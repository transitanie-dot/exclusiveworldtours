-- =====================================================================
-- O catalogo publico: a unica porta por onde o conteudo sai da base
--
-- Faltava a peca que fecha o circuito. Um operador submetia, era
-- aprovado, e o tour dele nao aparecia em lado nenhum: nenhum gerador
-- lia da base. O portal e a fila de revisao eram teatro.
--
-- PORQUE E QUE E UMA FUNCAO E NAO UMA VISTA ABERTA
--
-- A tentacao e dar `select` ao publico sobre `public_listings`. Nao
-- serve: a vista corre com as permissoes de quem consulta
-- (security_invoker, posto na 003 precisamente para isso), e por baixo
-- dela esta `operators`, que tem email, telefone e a taxa de comissao.
-- Abrir a vista era abrir a tabela.
--
-- E a mesma razao de sempre, e e a razao por que todo o caminho publico
-- deste sistema sao funcoes: o publico nunca recebe uma tabela, recebe
-- exatamente as colunas de que precisa.
--
-- PORQUE E QUE O GERADOR NAO PRECISA DE CHAVE DE SERVICO
--
-- Tudo o que esta aqui vai acabar numa pagina publica. Nao ha nada a
-- proteger, por isso o gerador corre com a chave PUBLICAVEL, como o
-- resto do site. A chave de servico — a que ignora o RLS — continua a
-- nao existir em lado nenhum deste repositorio, e o verificar.py recusa
-- qualquer pagina onde ela apareca.
-- =====================================================================


-- ---------------------------------------------------------------------
-- NOTA IMPORTANTE, APRENDIDA A MAL
--
-- Esta funcao NAO pode ler atraves da vista `listing_live`.
--
-- A vista e `security_invoker` (posta assim na 003, e bem: por baixo
-- dela esta `operators`). Mas uma funcao `security definer` que le
-- atraves de uma vista invoker PERDE os privilegios na fronteira da
-- vista — e o resultado, para quem nao assinou, nao e um erro: sao ZERO
-- LINHAS.
--
-- Zero linhas aqui significa um gerador que puxa um catalogo vazio e
-- publica um site sem nenhum tour de operador, sem dar erro nenhum e sem
-- ninguem dar por isso ate um operador perguntar porque e que o tour
-- dele desapareceu.
--
-- Por isso a "ultima versao aprovada" e calculada aqui dentro, sobre a
-- tabela, e nao pedida a vista. O sql/022_teste_anon.sql corre todas as
-- funcoes publicas como `anon` justamente para isto nao voltar a passar.
-- ---------------------------------------------------------------------
create or replace function catalogo_publico()
returns table (
  slug          text,
  city          text,
  country       text,
  operator_id   uuid,
  operator_name text,
  payload       jsonb,
  version       integer,
  reviewed_at   timestamptz,
  lead_time_hours integer,
  timezone      text,
  start_times   time[],
  max_pax       integer,
  vehicles      integer
)
language sql stable security definer set search_path = public as $$
  select
    l.slug, l.city, l.country,
    o.id, o.name,
    lv.payload, lv.version, lv.reviewed_at,
    l.lead_time_hours, l.timezone,
    -- As horas configuradas, para a pagina as poder mostrar sem esperar
    -- pela rede. Quais delas ainda estao dentro do prazo e outra
    -- pergunta, respondida ao vivo por partidas_no_dia().
    (select array_agg(t.starts_at order by t.starts_at)
       from listing_times t
      where t.listing_id = l.id and t.active),
    -- A maior lotacao da frota ligada a este tour, e quantos veiculos
    -- sao. Nao sao matriculas nem notas: sao dois numeros que a pagina
    -- usa para dizer "ate 6 pessoas".
    (select max(v.max_pax) from listing_vehicles lx
       join vehicles v on v.id = lx.vehicle_id
      where lx.listing_id = l.id and v.active),
    (select count(*)::integer from listing_vehicles lx
       join vehicles v on v.id = lx.vehicle_id
      where lx.listing_id = l.id and v.active)
  from   listings l
  join   operators o on o.id = l.operator_id
  join   (select distinct on (v.listing_id)
                 v.listing_id, v.payload, v.version, v.reviewed_at
          from   listing_versions v
          where  v.status = 'approved'
          order  by v.listing_id, v.version desc) lv on lv.listing_id = l.id
  where  l.status = 'live' and o.status = 'approved'
  order  by o.name, l.slug;
$$;

revoke execute on function catalogo_publico() from public;
grant  execute on function catalogo_publico() to anon, authenticated;

-- ---------------------------------------------------------------------
-- QUANDO FOI A ULTIMA MUDANCA
--
-- O gerador corre a mao. Esta funcao e o que lhe permite saber se vale a
-- pena correr — e, mais importante, e o que permite a fila de revisao
-- dizer ao Ricardo "ha 3 tours aprovados que ainda nao estao no site".
-- Aprovar e publicar sao dois passos, e o segundo e facil de esquecer.
-- ---------------------------------------------------------------------
create or replace function catalogo_mudou_em()
returns timestamptz
language sql stable security definer set search_path = public as $$
  select greatest(
    (select max(lv.reviewed_at) from listing_versions lv
      join listings l on l.id = lv.listing_id
      join operators o on o.id = l.operator_id
     where lv.status = 'approved' and l.status = 'live'
       and o.status = 'approved'),
    (select max(t.created_at) from listing_times t
      join listings l on l.id = t.listing_id
     where l.status = 'live'));
$$;

revoke execute on function catalogo_mudou_em() from public;
grant  execute on function catalogo_mudou_em() to anon, authenticated;
