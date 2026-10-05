-- =====================================================================
-- AS EPOCAS, POSTAS A PROVA
--
-- O que se testa: que uma frase ("segunda a sexta, Junho a Setembro, as
-- 09:00") produz o calendario certo, que uma epoca sem fim nao se
-- esgota, que um bebe ao colo nao ocupa lugar, que uma promocao com duas
-- janelas so se aplica quando as duas batem, e que uma falta nao se
-- regista sem prova.
-- =====================================================================
\set ON_ERROR_STOP on
\set ON_ERROR_ROLLBACK on
\pset pager off
begin;

insert into auth.users (id, email) values
  ('00211111-1111-1111-1111-111111111111','ana@x.invalid'),
  ('00219999-9999-9999-9999-999999999999','ricardo@x.invalid')
on conflict do nothing;
insert into admins (user_id) values ('00219999-9999-9999-9999-999999999999')
on conflict do nothing;

insert into operators (id,name,country,city,email,status,approved_at,commission_rate)
 values ('0021aaaa-0000-0000-0000-00000000000a','Ana Tours','Ireland','Galway',
         'ana@x.invalid','approved',now(),0.2000)
on conflict (id) do update set commission_rate = 0.2000;
insert into operator_users values
 ('0021aaaa-0000-0000-0000-00000000000a','00211111-1111-1111-1111-111111111111')
on conflict do nothing;

insert into listings (id,operator_id,slug,status,city,country,lead_time_hours,timezone)
 values ('0021bbbb-0000-0000-0000-00000000000b','0021aaaa-0000-0000-0000-00000000000a',
         'connemara-epocas','live','Galway','Ireland',24,'Europe/Dublin')
on conflict (id) do update set lead_time_hours = 24;

insert into listing_versions (listing_id,version,payload,status,reviewed_at) values
 ('0021bbbb-0000-0000-0000-00000000000b',1,
  '{"title":"Private Day in Connemara",
    "durations":[{"h":"8 hours","tiers":[
       {"max":3,"price":400,"vehicle":"Saloon car"},
       {"max":6,"price":500,"vehicle":"Minivan"}]}],
    "photos":[{"url":"https://exemplo.invalid/a.jpg"}]}'::jsonb,
  'approved',now())
on conflict (listing_id,version) do update set payload = excluded.payload;

-- A epoca: segunda a sexta, dos dias +10 a +60, as 09:00 e as 14:00.
select (current_date + 10)::text as de \gset
select (current_date + 60)::text as ate \gset
insert into listing_seasons (id,listing_id,starts_on,ends_on,weekdays)
 values ('0021cccc-0000-0000-0000-00000000000c',
         '0021bbbb-0000-0000-0000-00000000000b',
         :'de'::date, :'ate'::date, array[1,2,3,4,5]::smallint[]);
insert into season_times values
 ('0021cccc-0000-0000-0000-00000000000c','09:00'),
 ('0021cccc-0000-0000-0000-00000000000c','14:00');

\echo ''
\echo '=== 1. UMA FRASE, E O CALENDARIO SAI DELA'
\echo '    (seg-sex entre +10 e +60; os fins de semana nao aparecem)'
select count(*) as dias_abertos,
       count(*) filter (where extract(isodow from day) > 5) as fins_de_semana
from dias_abertos('connemara-epocas', current_date, current_date + 90);

\echo '    e fora da epoca nao ha nada'
select count(*) as antes_da_epoca
from dias_abertos('connemara-epocas', current_date, current_date + 9);
select count(*) as depois_da_epoca
from dias_abertos('connemara-epocas', current_date + 61, current_date + 90);

\echo ''
\echo '=== 2. AS HORAS SAO DA EPOCA, NAO DO ANUNCIO'
select (current_date + 14)::text as d1 \gset
select count(*) as horas_nesse_dia from partidas_no_dia('connemara-epocas', :'d1'::date);
\echo '    uma segunda epoca com outra hora so vale no periodo dela'
insert into listing_seasons (id,listing_id,starts_on,ends_on,weekdays)
 values ('0021dddd-0000-0000-0000-00000000000d',
         '0021bbbb-0000-0000-0000-00000000000b',
         (current_date + 61), (current_date + 120), array[6]::smallint[]);
insert into season_times values ('0021dddd-0000-0000-0000-00000000000d','10:00');
select count(*) as sabados_novos
from dias_abertos('connemara-epocas', current_date + 61, current_date + 120);

\echo ''
\echo '=== 3. UMA EPOCA SEM FIM NAO SE ESGOTA'
\echo '    (e o modo de falha mais comum: a disponibilidade acaba em silencio)'
insert into listings (id,operator_id,slug,status,city,country,lead_time_hours,timezone)
 values ('0021eeee-0000-0000-0000-00000000000e','0021aaaa-0000-0000-0000-00000000000a',
         'sem-fim','live','Galway','Ireland',24,'Europe/Dublin');
insert into listing_versions (listing_id,version,payload,status,reviewed_at) values
 ('0021eeee-0000-0000-0000-00000000000e',1,
  '{"title":"Sem fim","durations":[{"h":"8h","tiers":[{"max":4,"price":300}]}]}'::jsonb,
  'approved',now());
insert into listing_seasons (id,listing_id,starts_on,ends_on,weekdays)
 values ('0021ffff-0000-0000-0000-00000000000f','0021eeee-0000-0000-0000-00000000000e',
         current_date, null, array[1,2,3,4,5,6,7]::smallint[]);
insert into season_times values ('0021ffff-0000-0000-0000-00000000000f','09:00');
select count(*) > 300 as abre_ate_ao_fim_do_calendario
from dias_abertos('sem-fim', current_date, current_date + 400);

\echo ''
\echo '=== 4. UM DIA FECHADO E UMA EXCECAO A REGRA'
insert into availability (listing_id, day, status)
 values ('0021bbbb-0000-0000-0000-00000000000b', :'d1'::date, 'closed');
select count(*) as esse_dia_continua_aberto
from dias_abertos('connemara-epocas', :'d1'::date, :'d1'::date);
\echo '    e a regra continua de pe para os outros'
select count(*) as os_outros_nao_mexeram
from dias_abertos('connemara-epocas', current_date, current_date + 90);

\echo ''
\echo '=== 5. UM BEBE AO COLO NAO OCUPA LUGAR'
\echo '    sem lap_infant_max_age, 4 pessoas = 4 lugares = escalao de 500'
select (c->>'pax')::integer as lugares, (c->>'price')::numeric as preco
from (select cotar(jsonb_build_object('slug','connemara-epocas',
        'date',(current_date+15)::text,'pax',4,'infants',1)) c) z;
\echo '    com bebes ao colo ate aos 2 anos, 4 pessoas com 1 bebe = 3 lugares = 400'
update listings set lap_infant_max_age = 2
 where id = '0021bbbb-0000-0000-0000-00000000000b';
select (c->>'pax')::integer as lugares, (c->>'people')::integer as pessoas,
       (c->>'infants')::integer as bebes, (c->>'price')::numeric as preco
from (select cotar(jsonb_build_object('slug','connemara-epocas',
        'date',(current_date+15)::text,'pax',4,'infants',1)) c) z;
\echo '    e nao se pode dizer que sao todos bebes'
select (c->>'pax')::integer as lugares, (c->>'infants')::integer as bebes
from (select cotar(jsonb_build_object('slug','connemara-epocas',
        'date',(current_date+15)::text,'pax',4,'infants',9)) c) z;

\echo ''
\echo '=== 6. A PROMOCAO TEM DUAS JANELAS, E PRECISA DAS DUAS'
insert into promotions (operator_id, listing_id, label, kind, value,
                        quem_paga, book_until, travel_from, travel_until)
 values ('0021aaaa-0000-0000-0000-00000000000a','0021bbbb-0000-0000-0000-00000000000b',
         'Book by Friday, travel all summer','percent',15,'operator',
         current_date + 5, current_date + 30, current_date + 60);
\echo '    dentro das duas janelas: desconta'
select (c->>'price')::numeric as preco, c->'promo'->>'label' as promocao,
       (c->'promo'->>'saving')::numeric as poupanca
from (select cotar(jsonb_build_object('slug','connemara-epocas',
        'date',(current_date+35)::text,'pax',2)) c) z;
\echo '    data de viagem fora da janela de viagem: nao desconta'
select (c->>'price')::numeric as preco, (c ? 'promo') as tem_promocao
from (select cotar(jsonb_build_object('slug','connemara-epocas',
        'date',(current_date+15)::text,'pax',2)) c) z;
\echo '    janela de reserva ja fechada: nao desconta, mesmo viajando na janela certa'
update promotions set book_until = current_date - 1;
select (c->>'price')::numeric as preco, (c ? 'promo') as tem_promocao
from (select cotar(jsonb_build_object('slug','connemara-epocas',
        'date',(current_date+35)::text,'pax',2)) c) z;
update promotions set book_until = current_date + 5;

\echo ''
\echo '=== 7. QUEM PAGA O DESCONTO MUDA A REPARTICAO'
set local role authenticated;
set local "teste.uid" = '00219999-9999-9999-9999-999999999999';
\echo '    desconto do operador: a plataforma leva 20% do preco JA descontado'
select (c->>'price')::numeric as preco,
       (c->'split'->>'operator')::numeric as operador,
       (c->'split'->>'platform')::numeric as plataforma
from (select cotar(jsonb_build_object('slug','connemara-epocas',
        'date',(current_date+35)::text,'pax',2)) c) z;
reset role;
update promotions set quem_paga = 'platform';
set local role authenticated;
set local "teste.uid" = '00219999-9999-9999-9999-999999999999';
\echo '    desconto nosso: o operador recebe o que receberia SEM promocao (320)'
select (c->>'price')::numeric as preco,
       (c->'split'->>'operator')::numeric as operador,
       (c->'split'->>'platform')::numeric as plataforma
from (select cotar(jsonb_build_object('slug','connemara-epocas',
        'date',(current_date+35)::text,'pax',2)) c) z;
reset role;

\echo ''
\echo '=== 8. MOTORISTA A DISPOSICAO: UMA JANELA, NAO UMA HORA'
insert into listings (id,operator_id,slug,status,city,country,lead_time_hours,
                      timezone,schedule_mode)
 values ('00210000-0000-0000-0000-000000000011','0021aaaa-0000-0000-0000-00000000000a',
         'chauffeur','live','Galway','Ireland',24,'Europe/Dublin','opening_hours');
insert into listing_versions (listing_id,version,payload,status,reviewed_at) values
 ('00210000-0000-0000-0000-000000000011',1,
  '{"title":"A driver for the day","durations":[{"h":"10h","tiers":[{"max":4,"price":600}]}]}'::jsonb,
  'approved',now());
insert into listing_seasons (listing_id,starts_on,ends_on,weekdays,opens_at,closes_at)
 values ('00210000-0000-0000-0000-000000000011', current_date, null,
         array[1,2,3,4,5,6,7]::smallint[], '08:00', '18:00');
\echo '    o dia abre sem haver uma unica hora de partida registada'
select count(*) as dias from dias_abertos('chauffeur', current_date + 5, current_date + 5);
select opens_at, closes_at from janela_no_dia('chauffeur', (current_date + 5));
\echo '    e a cotacao devolve a janela em vez de exigir uma hora'
select c->>'scheduleMode' as modo, c->'window'->>'from' as abre,
       c->'window'->>'to' as fecha, (c->>'time') is null as sem_hora
from (select cotar(jsonb_build_object('slug','chauffeur',
        'date',(current_date+5)::text,'pax',2)) c) z;

\echo ''
\echo '=== 9. UMA FALTA NAO SE REGISTA SEM PROVA'
insert into bookings (reference,listing_id,listing_slug,tour_title,operator_id,
  booking_date,pax,price_total,commission_rate,platform_amount,operator_amount,
  payment_mode,status,customer_name,customer_email)
 values ('EWFALTA1','0021bbbb-0000-0000-0000-00000000000b','connemara-epocas',
         'Private Day in Connemara','0021aaaa-0000-0000-0000-00000000000a',
         current_date - 1, 2, 400.00, 0.2000, 80.00, 320.00,
         'now','paid','Quem Nao Veio','nao@x.invalid');
select id as fid from bookings where reference = 'EWFALTA1' \gset
select set_config('teste.fid', :'fid', false);

set local role authenticated;
set local "teste.uid" = '00211111-1111-1111-1111-111111111111';
\echo '    sem texto a serio, recusa'
do $$
begin
  perform marcar_falta(current_setting('teste.fid')::uuid, 30, 'nao veio');
  raise exception 'FALHOU: aceitou sem prova';
exception when others then
  if sqlerrm like '%ganha uma disputa%' then raise notice 'ok: exigiu a prova';
  else raise; end if;
end $$;
\echo '    sem minutos, recusa'
do $$
begin
  perform marcar_falta(current_setting('teste.fid')::uuid, null,
    'Esperei no lobby do hotel e liguei duas vezes para o numero da reserva.');
  raise exception 'FALHOU: aceitou sem os minutos';
exception when others then
  if sqlerrm like '%minutos%' then raise notice 'ok: exigiu os minutos';
  else raise; end if;
end $$;
\echo '    com as duas coisas, aceita'
select marcar_falta(:'fid'::uuid, 40,
  'Esperei 40 minutos no lobby do Hotel Meyrick, liguei duas vezes para o '
  'numero da reserva e deixei mensagem.')->>'ok' as registou;
\echo '    e nao se regista duas vezes'
do $$
begin
  perform marcar_falta(current_setting('teste.fid')::uuid, 40,
    'Outra tentativa de registar a mesma falta, com texto suficiente.');
  raise exception 'FALHOU: registou duas vezes';
exception when others then
  if sqlerrm like '%ja foi registada%' then raise notice 'ok: recusou a segunda';
  else raise; end if;
end $$;
reset role;
select no_show_wait, length(no_show_note) > 20 as tem_prova,
       no_show_by is not null as sabe_quem
from bookings where reference = 'EWFALTA1';

\echo ''
\echo '=== 10. UM TOUR QUE AINDA NAO ACONTECEU NAO TEM FALTAS'
reset role;
update bookings set booking_date = current_date + 5, no_show_at = null,
       no_show_wait = null, no_show_note = null where reference = 'EWFALTA1';
set local role authenticated;
set local "teste.uid" = '00211111-1111-1111-1111-111111111111';
do $$
begin
  perform marcar_falta(current_setting('teste.fid')::uuid, 30,
    'Texto com tamanho suficiente para passar a verificacao da prova.');
  raise exception 'FALHOU: registou uma falta de um tour futuro';
exception when others then
  if sqlerrm like '%ainda nao aconteceu%' then raise notice 'ok: recusou';
  else raise; end if;
end $$;
reset role;

\echo ''
\echo '=== 11. O OPERADOR SO MEXE NAS EPOCAS DELE'
insert into auth.users (id,email) values
 ('00212222-2222-2222-2222-222222222222','outro@x.invalid') on conflict do nothing;
insert into operators (id,name,country,city,email,status,approved_at) values
 ('0021aaaa-0000-0000-0000-0000000000ff','Outro','Spain','Madrid',
  'outro@x.invalid','approved',now()) on conflict do nothing;
insert into operator_users values
 ('0021aaaa-0000-0000-0000-0000000000ff','00212222-2222-2222-2222-222222222222')
on conflict do nothing;
set local role authenticated;
set local "teste.uid" = '00212222-2222-2222-2222-222222222222';
select count(*) as epocas_que_o_outro_ve from listing_seasons;
do $$
declare n integer;
begin
  update listing_seasons set weekdays = array[1]::smallint[];
  get diagnostics n = row_count;
  if n > 0 then raise exception 'FALHOU: mexeu em % epocas', n; end if;
  raise notice 'ok: nao mexeu em nenhuma';
end $$;
reset role;

\echo ''
\echo '=== 12. A MIGRACAO NAO PARTIU QUEM AINDA NAO TEM EPOCAS'
\echo '    (um anuncio so com listing_times continua a responder)'
insert into listings (id,operator_id,slug,status,city,country,lead_time_hours,timezone)
 values ('00210000-0000-0000-0000-000000000022','0021aaaa-0000-0000-0000-00000000000a',
         'antigo','live','Galway','Ireland',24,'Europe/Dublin');
insert into listing_versions (listing_id,version,payload,status,reviewed_at) values
 ('00210000-0000-0000-0000-000000000022',1,
  '{"title":"Antigo","durations":[{"h":"8h","tiers":[{"max":4,"price":300}]}]}'::jsonb,
  'approved',now());
insert into listing_times values ('00210000-0000-0000-0000-000000000022','09:00',true);
select count(*) > 300 as continua_a_abrir
from dias_abertos('antigo', current_date, current_date + 400);
select count(*) as tem_partidas
from partidas_no_dia('antigo', (current_date + 5));

rollback;
