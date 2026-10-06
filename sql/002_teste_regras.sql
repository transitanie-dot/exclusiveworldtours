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
--
-- O ON_ERROR_ROLLBACK NAO E DECORACAO
-- -----------------------------------
-- Metade dos cenarios aqui PROVOCA um erro de proposito (um operador a
-- aprovar-se a si mesmo, a mexer no calendario de outro). Fora de uma
-- transacao isso nao tinha consequencia nenhuma. Dentro de uma, o
-- primeiro erro aborta a transacao e TUDO o que vem depois falha com
-- "current transaction is aborted" — e com ON_ERROR_STOP 0 o psql sai
-- com codigo 0, por isso quem corre o ficheiro num ciclo ve sucesso.
--
-- Foi exatamente o que aconteceu quando se poe aqui a transacao: 32
-- instrucoes abortadas e nenhum sinal de que algo estava mal.
--
-- O ON_ERROR_ROLLBACK poe um savepoint implicito antes de cada
-- instrucao: um erro desfaz a instrucao e a transacao segue. E a
-- verificacao no fim do ficheiro e o que impede isto de voltar a passar
-- em silencio.
-- =====================================================================
\set ON_ERROR_ROLLBACK on
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

-- as politicas so se aplicam a quem nao e dono da tabela.
--
-- O `create role` vai num bloco que engole o duplicado porque os roles
-- sao do CLUSTER e nao da base: o rollback do fim deste ficheiro apaga
-- as linhas mas nao apaga o role. Correr a sequencia duas vezes seguidas
-- — que e o que se faz para provar que ela e idempotente — chegava aqui
-- com o role ja feito e enchia a saida de um erro que nao e erro.
do $$ begin
  create role app nologin;
exception
  when duplicate_object then null;
end $$;
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

-- =====================================================================
-- ESTE FICHEIRO CORREU DE VERDADE?
--
-- Com ON_ERROR_STOP 0, um ficheiro que aborte a meio sai com codigo 0 e
-- parece ter passado. Esta verificacao e o que torna isso impossivel: se
-- os dados do cenario nao estiverem todos de pe no fim, o ficheiro falha
-- com codigo diferente de 0 e quem o corre num ciclo para.
-- =====================================================================
\set ON_ERROR_STOP 1
do $$
begin
  if (select count(*) from operators
      where id in ('aaaaaaaa-0000-0000-0000-000000000001',
                   'bbbbbbbb-0000-0000-0000-000000000002')) <> 2
     or not exists (select 1 from admins
                    where user_id = '00021111-1111-1111-1111-111111111111')
     or not exists (select 1 from listing_versions
                    where listing_id = 'cccccccc-0000-0000-0000-000000000003') then
    raise exception 'O 002 nao correu inteiro: os dados do cenario nao estao '
      'todos de pe. Procura "current transaction is aborted" no que saiu.';
  end if;
  raise notice 'ok: o 002 correu inteiro';
end $$;

rollback;
