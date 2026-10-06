-- =====================================================================
-- 024 — Prova dos limites
-- =====================================================================
-- Transacional, como todos os ficheiros de teste: as linhas que cria
-- desaparecem no rollback do fim. Ver CORRER.md para o porque.
-- =====================================================================
\set ON_ERROR_ROLLBACK on
\set ON_ERROR_STOP 0

begin;

-- ---------------------------------------------------------------------
-- 1. A quota deixa passar ate ao limite e trava no seguinte
-- ---------------------------------------------------------------------
select 'cenario 1: contagem' as cenario;

select n,
       consumir_quota('t0024:conta', 'chave-a', 3, interval '1 hour') as cabe
from   generate_series(1, 5) as n;
-- Esperado: true, true, true, false, false

-- ---------------------------------------------------------------------
-- 2. Chaves diferentes nao se estorvam
-- ---------------------------------------------------------------------
select 'cenario 2: chaves independentes' as cenario;

select consumir_quota('t0024:conta', 'chave-b', 1, interval '1 hour') as b_primeira,
       consumir_quota('t0024:conta', 'chave-b', 1, interval '1 hour') as b_segunda,
       consumir_quota('t0024:conta', 'chave-c', 1, interval '1 hour') as c_primeira;
-- Esperado: true, false, true

-- ---------------------------------------------------------------------
-- 3. Baldes diferentes nao se estorvam
-- ---------------------------------------------------------------------
select 'cenario 3: baldes independentes' as cenario;

select consumir_quota('t0024:outro', 'chave-a', 1, interval '1 hour') as outro_balde;
-- Esperado: true — a chave-a ja estourou no balde t0024:conta

-- ---------------------------------------------------------------------
-- 4. Sem chave nao ha contagem, e isso nao e um erro
-- ---------------------------------------------------------------------
select 'cenario 4: chave vazia passa' as cenario;

select consumir_quota('t0024:conta', null,  1, interval '1 hour') as nula,
       consumir_quota('t0024:conta', '',    1, interval '1 hour') as vazia,
       consumir_quota('t0024:conta', '   ', 1, interval '1 hour') as espacos;
-- Esperado: true, true, true. Uma chamada sem chave nao pode ser
-- recusada: nao sabemos nada contra ela.

-- ---------------------------------------------------------------------
-- 5. A janela e fixa: tudo o que entra no mesmo minuto conta junto
-- ---------------------------------------------------------------------
select 'cenario 5: uma linha por janela' as cenario;

select count(*) as linhas_para_chave_a
from   rate_limits
where  bucket = 't0024:conta' and chave = 'chave-a';
-- Esperado: 1 — cinco chamadas, uma linha.

-- ---------------------------------------------------------------------
-- 6. O cliente_ip() nao estoura sem cabecalhos
-- ---------------------------------------------------------------------
-- Isto corre em psql, onde o GUC request.headers nao existe. E o caso
-- em que a funcao tem de devolver a constante e seguir em frente, nao
-- levantar excecao: uma candidatura nao pode falhar por causa disto.
select 'cenario 6: sem cabecalhos' as cenario;

select cliente_ip() as ip_fora_do_postgrest;
-- Esperado: sem-ip

-- ---------------------------------------------------------------------
-- 7. Um cabecalho com lixo tambem nao estoura
-- ---------------------------------------------------------------------
select 'cenario 7: cabecalho invalido' as cenario;

set local request.headers = 'isto nao e json';
select cliente_ip() as ip_com_lixo;
-- Esperado: sem-ip

-- ---------------------------------------------------------------------
-- 8. Com cabecalho a valer, le o IP — e so o primeiro da lista
-- ---------------------------------------------------------------------
select 'cenario 8: x-forwarded-for com cadeia' as cenario;

set local request.headers = '{"x-forwarded-for": "203.0.113.7, 10.0.0.1, 10.0.0.2"}';
select cliente_ip() as do_xff;
-- Esperado: 203.0.113.7 — o cliente, nao os proxies

set local request.headers = '{"cf-connecting-ip": "198.51.100.4", "x-forwarded-for": "203.0.113.7"}';
select cliente_ip() as prefere_o_especifico;
-- Esperado: 198.51.100.4

reset request.headers;

-- ---------------------------------------------------------------------
-- 9. O registar_pedido trava ao oitavo... quer dizer, ao decimo-primeiro
-- ---------------------------------------------------------------------
-- O limite por IP e 10/hora. Fora do PostgREST o IP e 'sem-ip', que e
-- uma chave como as outras: serve perfeitamente para provar a contagem.
select 'cenario 9: pedidos a mais do mesmo IP' as cenario;

do $$
declare
  i      integer;
  v_erro text := null;
  v_n    integer := 0;
begin
  for i in 1..12 loop
    begin
      perform registar_pedido(jsonb_build_object(
        'name',  'Teste 0024',
        'email', format('t0024-%s@exemplo.invalido', i),
        'message', 'prova de limite'));
      v_n := v_n + 1;
    exception when others then
      if v_erro is null then
        v_erro := format('travou a chamada %s: %s', i, sqlerrm);
      end if;
    end;
  end loop;
  raise notice 'passaram % de 12. %', v_n, coalesce(v_erro, 'nunca travou (ERRADO)');
  if v_n > 10 then
    raise exception 'FALHA: passaram % pedidos, o limite por IP e 10', v_n;
  end if;
end $$;
-- Esperado no notice: passaram 10 de 12, travou a chamada 11

-- ---------------------------------------------------------------------
-- 10. O limite por email e mais apertado que o por IP
-- ---------------------------------------------------------------------
-- 5/hora para o mesmo email. Como o balde do IP ja esta cheio do
-- cenario 9, este cenario mede-se noutro IP.
select 'cenario 10: o mesmo email a insistir' as cenario;

do $$
declare
  i   integer;
  v_n integer := 0;
begin
  set local request.headers = '{"x-forwarded-for": "203.0.113.99"}';
  for i in 1..7 loop
    begin
      perform registar_pedido(jsonb_build_object(
        'name',  'Teste 0024 email',
        'email', 't0024-insistente@exemplo.invalido',
        'message', format('tentativa %s', i)));
      v_n := v_n + 1;
    exception when others then
      null;
    end;
  end loop;
  -- Das que passam pela quota, so a primeira insere: as outras batem na
  -- regra dos 2 minutos e devolvem null. O que se mede aqui e a quota,
  -- nao as insercoes.
  raise notice 'chamadas aceites pela quota do email: %', v_n;
  if v_n > 5 then
    raise exception 'FALHA: a quota do email deixou passar %', v_n;
  end if;
end $$;
-- Esperado: 5

-- ---------------------------------------------------------------------
-- 11. A candidatura de operador tem o seu proprio balde
-- ---------------------------------------------------------------------
select 'cenario 11: candidaturas a mais' as cenario;

do $$
declare
  i   integer;
  v_n integer := 0;
begin
  set local request.headers = '{"x-forwarded-for": "203.0.113.55"}';
  for i in 1..5 loop
    begin
      perform candidatar_operador(jsonb_build_object(
        'company',      format('T0024 Lda %s', i),
        'contact_name', 'Teste 0024',
        'email',        format('t0024-cand-%s@exemplo.invalido', i),
        'country',      'Portugal',
        'city',         'Lisboa'));
      v_n := v_n + 1;
    exception when others then
      null;
    end;
  end loop;
  raise notice 'candidaturas aceites pela quota: % (limite 3/dia por IP)', v_n;
  if v_n > 3 then
    raise exception 'FALHA: a quota de candidaturas deixou passar %', v_n;
  end if;
end $$;
-- Esperado: 3

-- ---------------------------------------------------------------------
-- 12. A limpeza apaga o velho e poupa o novo
-- ---------------------------------------------------------------------
select 'cenario 12: limpeza' as cenario;

insert into rate_limits (bucket, chave, janela_inicio, contagem)
values ('t0024:velho', 'x', now() - interval '3 days', 9)
on conflict do nothing;

select limpar_quotas() as apagadas;
-- Esperado: >= 1

select count(*) as velhos_que_sobraram
from   rate_limits
where  janela_inicio < now() - interval '1 day';
-- Esperado: 0

select count(*) as novos_que_sobreviveram
from   rate_limits
where  bucket like 't0024:%' and janela_inicio >= now() - interval '1 day';
-- Esperado: > 0

-- ---------------------------------------------------------------------
-- 13. Nem anon nem authenticated chegam a nada disto
-- ---------------------------------------------------------------------
select 'cenario 13: portas fechadas' as cenario;

select p.proname,
       has_function_privilege('anon',          p.oid, 'execute') as anon,
       has_function_privilege('authenticated', p.oid, 'execute') as auth
from   pg_proc p
join   pg_namespace n on n.oid = p.pronamespace
where  n.nspname = 'public'
  and  p.proname in ('consumir_quota', 'cliente_ip', 'limpar_quotas')
order  by p.proname;
-- Esperado: false em todas

select has_table_privilege('anon',          'rate_limits', 'select') as anon_le,
       has_table_privilege('anon',          'rate_limits', 'insert') as anon_escreve,
       has_table_privilege('authenticated', 'rate_limits', 'select') as auth_le;
-- Esperado: false, false, false

-- ---------------------------------------------------------------------
-- A guarda final
-- ---------------------------------------------------------------------
-- Um ficheiro de teste que erra a meio e segue calado e pior que teste
-- nenhum: o psql sai com 0 e parece tudo bem. Esta assercao estoura se
-- os cenarios nao chegaram ao fim de pe.
\set ON_ERROR_STOP 1

do $$
declare
  v_baldes integer;
begin
  -- Os baldes que os cenarios 1 a 3 criam e que tem de estar de pe. O
  -- 't0024:velho' NAO entra nesta conta: o cenario 12 apaga-o de
  -- proposito, e e a ausencia dele que prova a limpeza.
  select count(distinct bucket) into v_baldes
  from   rate_limits
  where  bucket in ('t0024:conta', 't0024:outro');

  if v_baldes < 2 then
    raise exception 'FALHA: so % dos 2 baldes de teste existem; os cenarios 1 a 3 nao correram todos', v_baldes;
  end if;

  if exists (select 1 from rate_limits where bucket = 't0024:velho') then
    raise exception 'FALHA: a limpar_quotas() nao apagou a janela de 3 dias';
  end if;

  if (select count(*) from enquiries where email like 't0024-%') = 0 then
    raise exception 'FALHA: nenhum pedido de teste foi inserido';
  end if;

  if (select count(*) from operator_applications where email like 't0024-cand-%') = 0 then
    raise exception 'FALHA: nenhuma candidatura de teste foi inserida';
  end if;

  raise notice 'ok: % baldes, pedidos e candidaturas de teste de pe', v_baldes;
end $$;

rollback;
