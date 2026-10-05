-- =====================================================================
-- As avaliacoes, postas a prova
--
-- O que se testa aqui nao e o caminho feliz. E a cadeia que impede uma
-- avaliacao falsa, e os limites do que cada um pode fazer depois.
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

insert into operators (id,name,country,city,email,status,approved_at) values
 ('aaaaaaaa-0000-0000-0000-00000000000a','Ana Tours','Ireland','Galway','ana@x.invalid','approved',now())
on conflict do nothing;
insert into operator_users values ('aaaaaaaa-0000-0000-0000-00000000000a','11111111-1111-1111-1111-111111111111')
on conflict do nothing;
insert into listings (id,operator_id,slug,status,city,country) values
 ('bbbbbbbb-0000-0000-0000-00000000000b','aaaaaaaa-0000-0000-0000-00000000000a','connemara','live','Galway','Ireland')
on conflict do nothing;
insert into listing_versions (listing_id,version,payload,status,reviewed_at) values
 ('bbbbbbbb-0000-0000-0000-00000000000b',1,'{"title":"Private Day in Connemara"}'::jsonb,'approved',now())
on conflict do nothing;

-- Dois pedidos: um que viajou, outro que nunca viajou.
insert into enquiries (id,kind,listing_slug,listing_id,name,email,travelled_on) values
 ('eeeeeeee-0000-0000-0000-00000000000e','date','connemara','bbbbbbbb-0000-0000-0000-00000000000b','Maria Oliveira','m@x.invalid',current_date - 10),
 ('eeeeeeee-0000-0000-0000-00000000000f','date','connemara','bbbbbbbb-0000-0000-0000-00000000000b','Nunca Viajou','n@x.invalid',null)
on conflict do nothing;

set local role authenticated;
set local "teste.uid" = '99999999-9999-9999-9999-999999999999';

\echo ''
\echo '--- 1. Um pedido que nao viajou nao da convite nenhum'
do $$
begin
  perform convidar_avaliacao('eeeeeeee-0000-0000-0000-00000000000f');
  raise exception 'FALHOU: convidou alguem que nunca viajou';
exception when others then
  if sqlerrm like '%ainda nao viajou%' then raise notice 'ok: recusou';
  else raise; end if;
end $$;

\echo ''
\echo '--- 2. Um pedido que viajou da um convite, e so um'
select convidar_avaliacao('eeeeeeee-0000-0000-0000-00000000000e') as tk \gset
select set_config('teste.tk', :'tk', false);
select :'tk' is not null as deu_token;
select convidar_avaliacao('eeeeeeee-0000-0000-0000-00000000000e') = :'tk'::uuid
       as convidar_duas_vezes_da_o_mesmo;
select count(*) as convites from review_invites;
reset role;

\echo ''
\echo '--- 3. Quem nao assinou nao consegue convidar ninguem'
set local role anon;
do $$
begin
  perform convidar_avaliacao('eeeeeeee-0000-0000-0000-00000000000e');
  raise exception 'FALHOU: o anon convidou';
exception when others then raise notice 'ok: o anon nao convida';
end $$;

\echo ''
\echo '--- 4. O convite diz o que a pagina precisa, e nada do cliente'
select valido, tour, first_name, travelled_on from convite(:'tk'::uuid);
select (select count(*) from convite(:'tk'::uuid) c
         where c::text like '%m@x.invalid%') as email_exposto;
\echo '    e o anon nao consegue ler a tabela dos convites'
do $$
begin
  perform count(*) from review_invites;
  raise exception 'FALHOU: o anon leu os convites';
exception when others then raise notice 'ok: a tabela dos convites esta fechada';
end $$;

\echo ''
\echo '--- 5. Um token inventado nao devolve nada'
select count(*) as linhas from convite('00000000-0000-0000-0000-000000000000');

\echo ''
\echo '--- 6. Deixar a avaliacao gasta o token'
select deixar_avaliacao(:'tk'::uuid,
  jsonb_build_object('rating','4','r_driver','5','r_value','4',
                     'title','A day we will not forget',
                     'body','The driver knew where the light would be good.',
                     'author_name','QUEM EU QUISER')) is not null as deixou;
\echo '    e o nome vem do pedido, nao do formulario'
reset role;
select author_name from reviews;
set local role anon;
\echo '    o token fica gasto'
reset role;
select used_at is not null as gasto from review_invites;
set local role anon;

\echo ''
\echo '--- 7. O mesmo token nao serve duas vezes'
do $$
begin
  perform deixar_avaliacao(current_setting('teste.tk')::uuid,
                           jsonb_build_object('rating','1'));
  raise exception 'FALHOU: aceitou o token duas vezes';
exception when others then
  if sqlerrm like '%already been left%' then raise notice 'ok: recusou';
  else raise; end if;
end $$;

\echo ''
\echo '--- 8. Uma nota fora de 1 a 5 nao entra'
reset role;
insert into enquiries (id,listing_id,listing_slug,name,email,travelled_on)
 values ('eeeeeeee-0000-0000-0000-00000000001e','bbbbbbbb-0000-0000-0000-00000000000b','connemara','Outro Cliente','o@x.invalid',current_date-5);
set local role authenticated;
set local "teste.uid" = '99999999-9999-9999-9999-999999999999';
select convidar_avaliacao('eeeeeeee-0000-0000-0000-00000000001e') as t2 \gset
select set_config('teste.t2', :'t2', false);
reset role;
reset role;
do $$
begin
  perform deixar_avaliacao(current_setting('teste.t2')::uuid,
                           jsonb_build_object('rating','7'));
  raise exception 'FALHOU: aceitou uma nota de 7';
exception when others then
  if sqlerrm like '%1 to 5%' then raise notice 'ok: recusou';
  else raise; end if;
end $$;

\echo ''
\echo '--- 9. O operador responde, mas nao muda a nota'
set local role authenticated;
set local "teste.uid" = '11111111-1111-1111-1111-111111111111';
select id as rid from reviews limit 1 \gset
select set_config('teste.rid', :'rid', false);
select responder_avaliacao(:'rid'::uuid,
  'Thank you Maria — it was a good day to be out there.') is null as respondeu;
select rating, reply is not null as tem_resposta from reviews;
\echo '    e nao consegue mexer na nota (estava 4; tenta por 5)'
do $$
declare n integer;
begin
  update reviews set rating = 5;
  get diagnostics n = row_count;
  if n > 0 then
    raise exception 'FALHOU: o operador mudou a nota em % linhas', n;
  end if;
  raise notice 'ok: o update nao afetou nenhuma linha';
exception when insufficient_privilege then
  raise notice 'ok: a base recusou o update';
end $$;
reset role;
select rating as nota_depois_da_tentativa from reviews;

\echo ''
\echo '--- 10. Esconder exige razao escrita, e nao apaga'
set local role authenticated;
set local "teste.uid" = '99999999-9999-9999-9999-999999999999';
do $$
begin
  perform esconder_avaliacao(current_setting('teste.rid')::uuid, 'nao gostei');
  raise exception 'FALHOU: escondeu sem razao a serio';
exception when others then
  if sqlerrm like '%Escreve a razao%' then raise notice 'ok: exigiu a razao';
  else raise; end if;
end $$;
select esconder_avaliacao(:'rid'::uuid,
  'A viagem nao aconteceu: o cliente cancelou e o pedido foi marcado como viajado por engano.') is null as escondeu;
select state, hidden_reason is not null as tem_razao, rating from reviews;
reset role;

\echo ''
\echo '--- 11. Escondida, sai das contas publicas'
select n, media from nota_anuncio('bbbbbbbb-0000-0000-0000-00000000000b');
select count(*) as nas_paginas from avaliacoes_publicas();

\echo ''
\echo '--- 12. Zero avaliacoes devolve zero e nulo, nunca zero estrelas'
select n, media, ponderada from nota_anuncio('bbbbbbbb-0000-0000-0000-00000000000b');
select slug, mostrar, n, op_n from notas_publicas();

rollback;
