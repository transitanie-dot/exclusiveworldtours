-- =====================================================================
-- AS RESERVAS, POSTAS A PROVA
--
-- O que se testa aqui e o dinheiro e a concorrencia. Um preco que venha
-- do browser, um veiculo vendido duas vezes, um evento do Stripe
-- repetido, uma reparticao que nao fecha: sao os quatro erros que custam
-- dinheiro a serio e nenhum deles da uma mensagem de erro no browser.
-- =====================================================================
\set ON_ERROR_STOP on
\pset pager off
begin;

insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111','ana@x.invalid'),
  ('99999999-9999-9999-9999-999999999999','ricardo@x.invalid')
on conflict do nothing;
insert into admins (user_id) values ('99999999-9999-9999-9999-999999999999')
on conflict do nothing;

-- Um operador com 20% de comissao e UM carro de 4 lugares. Um carro so,
-- de proposito: e assim que se prova a trava.
insert into operators (id,name,country,city,email,status,approved_at,commission_rate) values
 ('aaaaaaaa-0000-0000-0000-00000000000a','Ana Tours','Ireland','Galway',
  'ana@x.invalid','approved',now(),0.2000)
on conflict (id) do update set commission_rate = 0.2000;
insert into operator_users values
 ('aaaaaaaa-0000-0000-0000-00000000000a','11111111-1111-1111-1111-111111111111')
on conflict do nothing;

insert into vehicles (id,operator_id,name,max_pax) values
 ('cccccccc-0000-0000-0000-00000000000c','aaaaaaaa-0000-0000-0000-00000000000a',
  'Skoda Superb',4)
on conflict do nothing;

insert into listings (id,operator_id,slug,status,city,country,lead_time_hours,timezone) values
 ('bbbbbbbb-0000-0000-0000-00000000000b','aaaaaaaa-0000-0000-0000-00000000000a',
  'connemara','live','Galway','Ireland',24,'Europe/Dublin')
on conflict (id) do update set lead_time_hours = 24, timezone = 'Europe/Dublin';
insert into listing_vehicles values
 ('bbbbbbbb-0000-0000-0000-00000000000b','cccccccc-0000-0000-0000-00000000000c')
on conflict do nothing;

-- Dois escaloes. O preco que conta e o do escalao, nunca o do pedido.
insert into listing_versions (listing_id,version,payload,status,reviewed_at) values
 ('bbbbbbbb-0000-0000-0000-00000000000b',1,
  '{"title":"Private Day in Connemara",
    "durations":[{"h":"8 hours","tiers":[
       {"max":3,"price":380,"vehicle":"Saloon car"},
       {"max":4,"price":420,"vehicle":"Saloon car"}]}],
    "photos":[{"url":"https://exemplo.invalid/a.jpg"}]}'::jsonb,
  'approved',now())
on conflict (listing_id,version) do update set payload = excluded.payload;

-- As datas: uma longe (da para pagar depois) e uma perto (nao da).
select (current_date + 30)::text as longe \gset
-- +2 dias: ja passou o lead time de 24 horas (que arredonda para cima,
-- ver a nota na 006) e ainda esta dentro das 72 horas do pagar depois.
-- E a janela estreita onde o dia se vende mas so a pronto.
select (current_date + 2)::text  as perto \gset

\echo ''
\echo '=== 1. O PRECO VEM DA BASE, NUNCA DO PEDIDO'
\echo '    (o pedido diz 1 euro e 3 pessoas; a base tem de dizer 380)'
select (cotar(jsonb_build_object(
          'slug','connemara','date',:'longe','pax',3,'price',1))->>'price')::numeric
       as preco_de_3_pessoas;
select (cotar(jsonb_build_object(
          'slug','connemara','date',:'longe','pax',4))->>'price')::numeric
       as preco_de_4_pessoas;
\echo '    e um grupo que nao cabe em escalao nenhum e recusado com o maximo'
select c->>'code' as codigo, c->>'maxPax' as maximo
from (select cotar(jsonb_build_object(
        'slug','connemara','date',:'longe','pax',9)) as c) z;

\echo ''
\echo '=== 2. PAGAR DEPOIS: a regra, e a RAZAO quando nao da'
\echo '    longe (30 dias): deve dar'
select (c->>'payLater')::boolean as pode, c->>'payLaterCode' as codigo
from (select cotar(jsonb_build_object('slug','connemara','date',:'longe','pax',3)) c) z;
\echo '    perto (1 dia): nao deve dar, e diz porque'
select (c->>'payLater')::boolean as pode, c->>'payLaterCode' as codigo,
       left(c->>'payLaterReason', 48) as razao
from (select cotar(jsonb_build_object('slug','connemara','date',:'perto','pax',3)) c) z;
\echo '    acima do limiar de valor: nao deve dar'
update payment_rules set max_value_for_later = 100 where id = 1;
select (c->>'payLater')::boolean as pode, c->>'payLaterCode' as codigo
from (select cotar(jsonb_build_object('slug','connemara','date',:'longe','pax',3)) c) z;
update payment_rules set max_value_for_later = 1200 where id = 1;

\echo ''
\echo '=== 3. A COMISSAO NAO E ASSUNTO DO PUBLICO'
set local role anon;
select not (cotar(jsonb_build_object('slug','connemara','date',:'longe','pax',3))
              ? 'split') as anon_nao_ve_a_chave_split;
\echo '    e o anon nao consegue reservar'
do $$
begin
  perform reservar(jsonb_build_object('slug','connemara','pax',3));
  raise exception 'FALHOU: o anon reservou';
exception when insufficient_privilege then raise notice 'ok: o anon nao reserva';
end $$;
reset role;

\echo ''
\echo '=== 4. "PAGAR DEPOIS" E UM PEDIDO, NAO UMA ORDEM'
\echo '    pede-se later numa data que nao permite; tem de sair now'
select r->>'payment_mode' as modo, r->>'reference' as ref
from (select reservar(jsonb_build_object(
        'slug','connemara','date',:'perto','pax',2,
        'payment_mode','later','name','Teste Perto',
        'email','perto@x.invalid')) r) z;
select payment_mode, charge_at is null as sem_data_de_cobranca
from bookings where customer_email = 'perto@x.invalid';

\echo ''
\echo '=== 5. A REPARTICAO FECHA, E E GRAVADA'
select price_total, commission_rate, platform_amount, operator_amount,
       round(platform_amount + operator_amount, 2) = price_total as fecha
from bookings where customer_email = 'perto@x.invalid';
\echo '    e a base recusa uma reparticao que nao feche'
do $$
begin
  update bookings set platform_amount = 1 where customer_email = 'perto@x.invalid';
  raise exception 'FALHOU: aceitou uma reparticao que nao fecha';
exception when check_violation then raise notice 'ok: a base recusou';
end $$;

\echo ''
\echo '=== 6. UM CARRO SO: a segunda reserva do mesmo dia e recusada'
\echo '    (a primeira, do teste 4, ja prendeu o carro nesse dia)'
-- O codigo que sai e `dayClosed` e nao `justTaken`, e esta certo: com o
-- unico carro preso, a dias_abertos() ja fecha o dia e a cotar() recusa
-- antes de a reservar() tentar prender nada. O `justTaken` e a corrida
-- verdadeira — duas transacoes ao mesmo tempo — que nao se encena numa
-- sessao so de psql. O que se prova aqui e que nao ha caminho nenhum que
-- venda o mesmo carro duas vezes.
select r->>'ok' as ok, r->>'code' as codigo
from (select reservar(jsonb_build_object(
        'slug','connemara','date',:'perto','pax',2,
        'name','Segundo','email','segundo@x.invalid')) r) z;
select count(*) as reservas_nesse_dia from bookings
 where booking_date = :'perto'::date and status <> 'cancelled';
-- E a linha do dia continua la, com a nota do operador intacta.
select status, note from vehicle_days where day = :'perto'::date;
select count(*) as carros_presos from vehicle_days
 where day = :'perto'::date and status <> 'open';
\echo '    e o dia deixou de aparecer livre'
select count(*) as dias_abertos_nesse_dia
from dias_abertos('connemara', :'perto'::date, :'perto'::date);

\echo ''
\echo '=== 7. UMA MARCA CADUCADA NAO PRENDE NADA'
\echo '    (a reserva do teste 4 ficou por pagar; faz-se de conta que passou)'
update vehicle_days set hold_expires_at = now() - interval '1 minute'
 where day = :'perto'::date;
select count(*) as dias_abertos_outra_vez
from dias_abertos('connemara', :'perto'::date, :'perto'::date);
\echo '    e outra pessoa consegue reservar o mesmo dia'
select r->>'ok' as ok, r->>'reference' as ref
from (select reservar(jsonb_build_object(
        'slug','connemara','date',:'perto','pax',2,
        'name','Terceiro','email','terceiro@x.invalid')) r) z;
select count(*) as continua_a_ser_um_carro_preso
from vehicle_days where day = :'perto'::date and status <> 'open';

\echo ''
\echo '=== 8. O STRIPE REPETE OS EVENTOS'
select id as bid from bookings where customer_email = 'terceiro@x.invalid' \gset
select confirmar_reserva(jsonb_build_object(
  'booking_id', :'bid', 'session_id','cs_test_1',
  'payment_intent','pi_1', 'email','terceiro@x.invalid'))->>'status' as primeira_vez;
select (confirmar_reserva(jsonb_build_object(
  'booking_id', :'bid', 'session_id','cs_test_1'))->>'repeated')::boolean
  as segunda_vez_e_repeticao;
select count(*) as reservas_pagas from bookings where status = 'paid';
\echo '    e a marca do carro deixou de ter validade'
select hold_expires_at is null as marca_definitiva
from vehicle_days where booking_id = :'bid'::uuid;

\echo ''
\echo '=== 9. PAGAR DEPOIS CONFIRMA, MAS NAO DIZ "PAGO"'
select r->>'payment_mode' as modo
from (select reservar(jsonb_build_object(
        'slug','connemara','date',:'longe','pax',3,
        'payment_mode','later','name','Maria Oliveira',
        'email','maria@x.invalid')) r) z;
select id as lid from bookings where customer_email = 'maria@x.invalid' \gset
select confirmar_reserva(jsonb_build_object(
  'booking_id', :'lid', 'session_id','cs_test_2',
  'setup_intent','seti_1','customer','cus_1','payment_method','pm_1'))->>'status'
  as estado;
select status, charged_at is null as nada_cobrado, charge_at is not null as tem_hora
from bookings where id = :'lid'::uuid;

\echo ''
\echo '=== 10. QUEM ESTA NA HORA DE COBRAR'
\echo '    hoje nao: a cobranca e 72h antes de uma partida a 30 dias'
select count(*) as a_cobrar_agora from reservas_a_cobrar();
\echo '    posta a hora, aparece'
update bookings set charge_at = now() - interval '1 hour' where id = :'lid'::uuid;
select reference, amount_cents, attempt from reservas_a_cobrar();
\echo '    uma tentativa falhada nao volta logo (intervalo de 8 horas)'
select registar_cobranca(jsonb_build_object(
  'booking_id', :'lid', 'ok', false, 'attempt', 1,
  'code','card_declined','message','Insufficient funds'));
select count(*) as a_cobrar_logo_depois from reservas_a_cobrar();
select charge_attempts, status from bookings where id = :'lid'::uuid;

\echo ''
\echo '=== 11. ESGOTADAS AS TENTATIVAS, O DIA VOLTA A VENDA'
-- Salta-se da tentativa 1 para a 3 em vez de esperar 16 horas pelos
-- intervalos. Sao por isso duas linhas em charge_attempts e nao tres.
select registar_cobranca(jsonb_build_object(
  'booking_id', :'lid', 'ok', false, 'attempt', 3, 'code','card_declined'));
select status, cancel_reason from bookings where id = :'lid'::uuid;
-- A linha fica, solta: o booking_id deixa de apontar para a reserva e o
-- dia volta a 'open'. Contar linhas aqui media a arrumacao e nao a venda.
select count(*) as carro_preso_nesse_dia
from vehicle_days where booking_id = :'lid'::uuid and status <> 'open';
select count(*) as tentativas_registadas
from charge_attempts where booking_id = :'lid'::uuid;

\echo ''
\echo '=== 12. O OPERADOR VE O QUE RECEBE, NAO O QUE A PLATAFORMA LEVA'
set local role authenticated;
set local "teste.uid" = '11111111-1111-1111-1111-111111111111';
select reference, pax, you_receive, status
from agenda_do_operador(current_date - 60, current_date + 60)
order by booking_date, reference;
\echo '    (380 x 0.8 = 304 e 320 x 0.8... o de 2 pessoas e 380: escalao de 3)'
\echo '    e a agenda nao tem coluna de comissao nenhuma'
select count(*) as colunas_com_comissao
from information_schema.columns
where table_name = 'agenda_do_operador';

\echo ''
\echo '=== 13. UM OPERADOR NAO VE AS RESERVAS DE OUTRO'
reset role;
insert into operators (id,name,country,city,email,status,approved_at) values
 ('aaaaaaaa-0000-0000-0000-00000000000e','Outro Tours','Spain','Madrid',
  'outro@x.invalid','approved',now())
on conflict do nothing;
insert into auth.users (id,email) values
 ('22222222-2222-2222-2222-222222222222','outro@x.invalid') on conflict do nothing;
insert into operator_users values
 ('aaaaaaaa-0000-0000-0000-00000000000e','22222222-2222-2222-2222-222222222222')
on conflict do nothing;
set local role authenticated;
set local "teste.uid" = '22222222-2222-2222-2222-222222222222';
select count(*) as reservas_que_o_outro_ve from bookings;
select count(*) as agenda_do_outro
from agenda_do_operador(current_date - 60, current_date + 60);
reset role;

\echo ''
\echo '=== 14. A AVALIACAO NASCE DA RESERVA PAGA'
\echo '    uma reserva paga de hoje ainda nao viajou'
select set_config('teste.bid', :'bid', false);
set local role authenticated;
set local "teste.uid" = '99999999-9999-9999-9999-999999999999';
do $$
begin
  perform convidar_por_reserva(current_setting('teste.bid')::uuid);
  raise exception 'FALHOU: convidou antes de o tour acontecer';
exception when others then
  if sqlerrm like '%ainda nao aconteceu%' then raise notice 'ok: recusou';
  else raise; end if;
end $$;

\echo '    posta no passado, aparece na fila e da convite'
reset role;
update bookings set booking_date = current_date - 3 where id = :'bid'::uuid;
set local role authenticated;
set local "teste.uid" = '99999999-9999-9999-9999-999999999999';
select count(*) as na_fila from reservas_a_convidar();
select convidar_por_reserva(:'bid'::uuid) as tk \gset
select set_config('teste.tk', :'tk', false);
select convidar_por_reserva(:'bid'::uuid) = :'tk'::uuid as duas_vezes_da_o_mesmo;
reset role;

\echo ''
\echo '=== 15. O NOME DA AVALIACAO VEM DA RESERVA, NAO DO FORMULARIO'
set local role anon;
select valido, tour, first_name from convite(:'tk'::uuid);
select deixar_avaliacao(:'tk'::uuid, jsonb_build_object(
  'rating','5','title','A long day and a good one',
  'body','The driver stopped where the light was best.',
  'author_name','QUEM EU QUISER')) is not null as deixou;
reset role;
select author_name, rating, booking_id is not null as veio_de_uma_reserva,
       enquiry_id is null as sem_pedido
from reviews where booking_id = :'bid'::uuid;

\echo ''
\echo '=== 16. UM CONVITE TEM UMA ORIGEM, NUNCA DUAS NEM NENHUMA'
do $$
begin
  insert into review_invites (listing_id, operator_id)
  values ('bbbbbbbb-0000-0000-0000-00000000000b',
          'aaaaaaaa-0000-0000-0000-00000000000a');
  raise exception 'FALHOU: aceitou um convite sem origem';
exception when check_violation then raise notice 'ok: recusou sem origem';
end $$;

\echo ''
\echo '=== 17. A NOTA PUBLICA CONTA A AVALIACAO QUE VEIO DA RESERVA'
select n, media from nota_anuncio('bbbbbbbb-0000-0000-0000-00000000000b');
select slug, mostrar, n from notas_publicas();

\echo ''
\echo '=== 18. A FILA DE PAGAMENTOS AO OPERADOR'
set local role authenticated;
set local "teste.uid" = '99999999-9999-9999-9999-999999999999';
select operator_name, reservas, total from a_pagar();
select marcar_pago('aaaaaaaa-0000-0000-0000-00000000000a',
                   'Transferencia SEPA 5 out') as marcadas;
select count(*) as ainda_a_pagar from a_pagar();
reset role;

\echo ''
\echo '=== 19. A NOTA DO OPERADOR SOBREVIVE A UMA RESERVA CANCELADA'
\echo '    (era isto que o delete from vehicle_days apagava)'
reset role;
select (current_date + 20)::text as nota_dia \gset
insert into vehicle_days (vehicle_id, day, status, note)
 values ('cccccccc-0000-0000-0000-00000000000c', :'nota_dia'::date,
         'open', 'So de manha: tenho o casamento da sobrinha a tarde')
on conflict (vehicle_id, day) do update set note = excluded.note;

select r->>'reference' as ref
from (select reservar(jsonb_build_object(
        'slug','connemara','date',:'nota_dia','pax',2,
        'name','Nota Teste','email','nota@x.invalid')) r) z;
select status, booking_id is not null as tem_reserva, note
from vehicle_days where day = :'nota_dia'::date;

select id as nid from bookings where customer_email = 'nota@x.invalid' \gset
select confirmar_reserva(jsonb_build_object(
  'booking_id', :'nid', 'session_id','cs_test_9'))->>'status' as pago;

set local role authenticated;
set local "teste.uid" = '99999999-9999-9999-9999-999999999999';
select cancelar_reserva(:'nid'::uuid,
  'O cliente mudou de planos e cancelou com uma semana de aviso.')->>'ok'
  as cancelou;
reset role;
\echo '    o dia volta a venda E a nota continua la'
select status, booking_id is null as sem_reserva, note
from vehicle_days where day = :'nota_dia'::date;
select count(*) as dia_aberto_outra_vez
from dias_abertos('connemara', :'nota_dia'::date, :'nota_dia'::date);

\echo ''
\echo '=== 20. UMA RESERVA CANCELADA NAO SE CONFIRMA'
\echo '    (o cliente paga no Stripe depois de a reserva ter caido)'
reset role;
select (current_date + 25)::text as tarde_dia \gset
select r->>'booking_id' as cid
from (select reservar(jsonb_build_object(
        'slug','connemara','date',:'tarde_dia','pax',2,
        'name','Perdeu A Corrida','email','perdeu@x.invalid')) r) z \gset
select id as cid from bookings where customer_email = 'perdeu@x.invalid' \gset
\echo '    faz-se de conta que a limpar_marcas() a fechou por nao ter sido paga'
update bookings set status = 'cancelled', cancelled_at = now(),
       cancel_reason = 'Nao foi paga: o cliente saiu do pagamento.'
 where id = :'cid'::uuid;

\echo '    e agora chega o webhook do Stripe a dizer que o pagamento entrou'
select c->>'ok' as aceitou, c->>'code' as codigo,
       (c->>'amount')::numeric as a_devolver
from (select confirmar_reserva(jsonb_build_object(
        'booking_id', :'cid', 'session_id','cs_test_10',
        'payment_intent','pi_a_devolver')) c) z;
\echo '    a reserva continua cancelada e nao ficou "paga"'
select status, charged_at is null as nada_marcado_como_cobrado
from bookings where id = :'cid'::uuid;

rollback;
