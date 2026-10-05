\set ON_ERROR_STOP 0
-- =====================================================================
-- DENTRO DE UMA TRANSACAO, E DESFEITA NO FIM
--
-- Isto nao estava aqui e custou caro: este ficheiro gravava os seus
-- dados e tornava o utilizador 1111... administrador PARA SEMPRE. O
-- 015, que usa esse mesmo id como OPERADOR, tinha um teste a provar que
-- um operador nao consegue mudar a nota de uma avaliacao — e esse teste
-- passava sozinho e falhava depois do 002, porque depois do 002 aquele
-- utilizador era administrador.
--
-- Um teste cujo resultado depende da ordem em que corre nao e um teste.
-- Por isso: tudo dentro de begin/rollback, e cada ficheiro de teste com
-- os seus proprios ids (ver o prefixo 0002 em baixo).
-- =====================================================================
begin;

-- ---- cenario: um administrador, dois operadores
insert into auth.users (id, email) values
  ('00021111-1111-1111-1111-111111111111','ricardo@exemplo.pt'),
  ('00022222-2222-2222-2222-222222222222','ana@operadora.pt'),
  ('00023333-3333-3333-3333-333333333333','joao@outra.pt');
insert into admins (user_id) values ('00021111-1111-1111-1111-111111111111');

insert into operators (id, name, country, city, email, status) values
  ('aaaaaaaa-0000-0000-0000-000000000001','Ana Tours','Portugal','Lisbon','ana@operadora.pt','approved'),
  ('bbbbbbbb-0000-0000-0000-000000000002','Outra Lda','Spain','Madrid','joao@outra.pt','approved');
insert into operator_users (operator_id, user_id) values
  ('aaaaaaaa-0000-0000-0000-000000000001','00022222-2222-2222-2222-222222222222'),
  ('bbbbbbbb-0000-0000-0000-000000000002','00023333-3333-3333-3333-333333333333');
insert into listings (id, operator_id, slug, city, country) values
  ('cccccccc-0000-0000-0000-000000000003','aaaaaaaa-0000-0000-0000-000000000001','sintra-dia','Lisbon','portugal'),
  ('dddddddd-0000-0000-0000-000000000004','bbbbbbbb-0000-0000-0000-000000000002','toledo-dia','Madrid','spain');

-- as politicas so se aplicam a quem nao e dono da tabela
create role app nologin;
grant usage on schema public, auth to app;
grant select, insert, update, delete on all tables in schema public to app;
grant execute on all functions in schema public, auth to app;
grant usage, select on all sequences in schema public to app;

\echo '--- 1. A Ana submete conteudo para o anuncio dela'
set role app; set teste.uid = '00022222-2222-2222-2222-222222222222';
select submeter_versao('cccccccc-0000-0000-0000-000000000003',
  '{"title":"Sintra em privado","price":480}'::jsonb) is not null as submeteu;

\echo '--- 2. Esta no site? Nao deve estar: ainda nao foi revisto'
reset role; select count(*) as anuncios_publicos from public_listings;

\echo '--- 3. A Ana tenta aprovar a propria versao (tem de falhar)'
set role app; set teste.uid = '00022222-2222-2222-2222-222222222222';
select rever_versao((select id from listing_versions limit 1), true);

\echo '--- 4. A Ana tenta ver o anuncio do Joao (tem de vir vazio)'
select count(*) as anuncios_que_a_ana_ve from listings;

\echo '--- 5. A Ana tenta mexer no calendario do Joao (tem de falhar)'
insert into availability (listing_id, day, status)
values ('dddddddd-0000-0000-0000-000000000004', current_date + 5, 'closed');

\echo '--- 6. O Ricardo aprova'
reset role; set role app; set teste.uid = '00021111-1111-1111-1111-111111111111';
select rever_versao((select id from listing_versions order by submitted_at limit 1), true, 'ok');

\echo '--- 7. Agora esta no site'
reset role; select slug, payload->>'title' as titulo, version from public_listings;

\echo '--- 8. A Ana fecha dois dias (nao precisa de revisao)'
set role app; set teste.uid = '00022222-2222-2222-2222-222222222222';
select marcar_dias('cccccccc-0000-0000-0000-000000000003',
  array[current_date + 10, current_date + 11]::date[], 'closed') as dias_marcados;

\echo '--- 9. A disponibilidade responde certo'
reset role;
select to_char(current_date + 10,'YYYY-MM-DD') as dia_fechado,
       dia_disponivel('cccccccc-0000-0000-0000-000000000003', current_date + 10) as disponivel;
select to_char(current_date + 12,'YYYY-MM-DD') as dia_livre,
       dia_disponivel('cccccccc-0000-0000-0000-000000000003', current_date + 12) as disponivel;
select to_char(current_date - 1,'YYYY-MM-DD') as ontem,
       dia_disponivel('cccccccc-0000-0000-0000-000000000003', current_date - 1) as disponivel;

\echo '--- 10. Uma submissao nova nao derruba a que esta no ar'
set role app; set teste.uid = '00022222-2222-2222-2222-222222222222';
select submeter_versao('cccccccc-0000-0000-0000-000000000003',
  '{"title":"TITULO POR REVER","price":9999}'::jsonb) is not null as submeteu_v2;
reset role; select slug, payload->>'title' as titulo_no_site, version from public_listings;

rollback;
