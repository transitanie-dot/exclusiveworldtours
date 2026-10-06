-- =====================================================================
-- Exclusive World Tours — o modelo de dados do marketplace
--
-- Escrito para Postgres/Supabase. Corre do principio ao fim numa base
-- vazia e pode voltar a correr sem estragar nada (tudo e "if not
-- exists" ou "or replace").
--
-- A ideia que manda em tudo isto
-- ------------------------------
-- Os dados do marketplace tem dois ritmos completamente diferentes, e
-- tratá-los como se fossem um so e o erro que estraga estas plataformas:
--
--   LENTOS   titulo, itinerario, fotografias, escaloes de preco.
--            Mudam raramente, passam pela revisao do Ricardo, e sao
--            publicados como paginas estaticas — rapidas e indexaveis.
--
--   RAPIDOS  calendario, dias fechados, lugares vendidos.
--            Mudam varias vezes ao dia, NAO passam por revisao, e sao
--            lidos ao vivo no momento em que o cliente escolhe a data.
--            Uma pagina estatica que diga "disponivel" quando o
--            operador ja fechou o dia nao e um atraso: e uma reserva
--            que vai ter de ser cancelada.
--
-- Por isso: `listing_versions` (lento, com revisao) e `availability`
-- (rapido, sem revisao) sao tabelas diferentes, com regras diferentes.
--
-- A revisao
-- ---------
-- Cada alteracao ao conteudo cria uma VERSAO nova em estado `pending`.
-- A versao que esta no ar continua a ser a ultima aprovada, por isso o
-- operador nunca consegue por nada no site sem passar pelo Ricardo, e
-- uma submissao má nao derruba o anuncio que ja estava bom.
-- =====================================================================

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------
-- Quem e administrador. Fica numa tabela e nao numa lista no codigo,
-- para se poder acrescentar alguem sem publicar uma versao nova.
-- ---------------------------------------------------------------------
create table if not exists admins (
  user_id     uuid primary key references auth.users(id) on delete cascade,
  created_at  timestamptz not null default now()
);

create or replace function is_admin()
returns boolean
language sql
stable
security definer
set search_path = public
as $$
  select exists (select 1 from admins where user_id = auth.uid());
$$;

-- ---------------------------------------------------------------------
-- Quem VAI ser administrador quando a conta aparecer
-- ---------------------------------------------------------------------
-- A tabela `admins` aponta para uma linha da auth.users, logo so se pode
-- preencher depois de a conta existir. Mas a decisao de quem manda e
-- anterior a isso: e tomada por endereco de email, antes de haver conta
-- nenhuma. Por isso ha duas tabelas e nao uma.
--
-- Esta e a lista de enderecos. O trigger abaixo liga as duas: quando uma
-- conta nasce com um endereco que esta ca, e promovida na mesma
-- transacao. Isto e o que faz com que apagar a conta e registar outra
-- vez com o mesmo email devolva o acesso sozinho — sem isto, ficava-se
-- de fora do proprio administrador.
create table if not exists admin_emails (
  email       text primary key,
  nota        text,
  created_at  timestamptz not null default now()
);

alter table admin_emails enable row level security;

-- Ninguem le isto pelo caminho publico. Nem um administrador: saber
-- quem e administrador nao serve para nada a quem ja entrou, e a lista
-- de enderecos de quem manda e exatamente o que um atacante quer para
-- escolher em quem bater. A policy diz `false` e nao e um descuido.
drop policy if exists ae_ninguem on admin_emails;
create policy ae_ninguem on admin_emails for select using (false);

create or replace function promover_admin()
returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if exists (select 1 from admin_emails
             where lower(email) = lower(new.email)) then
    insert into admins (user_id) values (new.id)
    on conflict (user_id) do nothing;
  end if;
  return new;
end;
$$;

-- So em INSERT, de proposito: numa conta que ja existia a linha em
-- `admins` tem de ser posta a mao, e esta nota esta repetida na 005
-- porque e la que alguem vai tropecar nisso.
drop trigger if exists promover_admin_tg on auth.users;
create trigger promover_admin_tg
  after insert on auth.users
  for each row execute function promover_admin();

-- ---------------------------------------------------------------------
-- OPERADORES — as empresas que vendem no marketplace
-- ---------------------------------------------------------------------
do $$ begin
  create type operator_status as enum ('pending', 'approved', 'suspended');
exception
  when duplicate_object then null;  -- ja existia; o ficheiro volta a correr
end $$;

create table if not exists operators (
  id              uuid primary key default gen_random_uuid(),
  name            text not null,                 -- nome comercial
  legal_name      text,                          -- entidade legal
  country         text not null,
  city            text not null,
  email           text not null,
  phone           text,
  website         text,
  licence_ref     text,                           -- licenca de turismo, se houver
  status          operator_status not null default 'pending',
  -- Comissao: 20%, decidido pelo Ricardo a 2 de outubro de 2026.
  -- Fica por operador e nao numa constante, porque ha sempre um caso
  -- especial e o caso especial nao deve obrigar a publicar codigo.
  commission_rate numeric(5,4) not null default 0.2000
                  check (commission_rate >= 0 and commission_rate <= 0.5),
  notes           text,                           -- notas internas do Ricardo
  created_at      timestamptz not null default now(),
  approved_at     timestamptz,
  constraint operators_email_valido check (position('@' in email) > 1)
);

create index if not exists operators_status_idx on operators(status);

-- a ligacao entre uma conta e um operador. Uma empresa pode ter varias
-- pessoas; uma pessoa pode, em teoria, trabalhar para mais do que uma.
create table if not exists operator_users (
  operator_id uuid not null references operators(id) on delete cascade,
  user_id     uuid not null references auth.users(id) on delete cascade,
  role        text not null default 'owner' check (role in ('owner', 'staff')),
  created_at  timestamptz not null default now(),
  primary key (operator_id, user_id)
);

create or replace function meus_operadores()
returns setof uuid
language sql
stable
security definer
set search_path = public
as $$
  select operator_id from operator_users where user_id = auth.uid();
$$;

-- ---------------------------------------------------------------------
-- ANUNCIOS — o anuncio e a identidade; o conteudo vive nas versoes
-- ---------------------------------------------------------------------
do $$ begin
  create type listing_status as enum ('draft', 'live', 'paused', 'withdrawn');
exception
  when duplicate_object then null;  -- ja existia; o ficheiro volta a correr
end $$;

create table if not exists listings (
  id          uuid primary key default gen_random_uuid(),
  operator_id uuid not null references operators(id) on delete cascade,
  slug        text not null unique,
  status      listing_status not null default 'draft',
  city        text not null,
  country     text not null,
  created_at  timestamptz not null default now(),
  constraint slug_valido check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$')
);

create index if not exists listings_operator_idx on listings(operator_id);
create index if not exists listings_status_idx on listings(status);

-- ---------------------------------------------------------------------
-- VERSOES — e aqui que a revisao acontece
-- ---------------------------------------------------------------------
do $$ begin
  create type review_status as enum ('pending', 'approved', 'rejected');
exception
  when duplicate_object then null;  -- ja existia; o ficheiro volta a correr
end $$;

create table if not exists listing_versions (
  id            uuid primary key default gen_random_uuid(),
  listing_id    uuid not null references listings(id) on delete cascade,
  version       integer not null,
  -- o conteudo todo num so campo: titulo, lede, paragens, incluido,
  -- escaloes de preco, fotografias. Fica em jsonb para o formato poder
  -- crescer sem uma migracao por cada campo novo.
  payload       jsonb not null,
  status        review_status not null default 'pending',
  submitted_by  uuid references auth.users(id),
  submitted_at  timestamptz not null default now(),
  reviewed_by   uuid references auth.users(id),
  reviewed_at   timestamptz,
  review_note   text,                            -- porque e que foi recusado
  unique (listing_id, version)
);

create index if not exists versions_pendentes_idx
  on listing_versions(status, submitted_at)
  where status = 'pending';

-- A versao que esta no ar e sempre a ultima APROVADA. Nao e a ultima
-- submetida: assim uma submissao por rever nunca aparece no site, e uma
-- submissao recusada nao derruba o anuncio que ja la estava bom.
create or replace view listing_live as
select distinct on (v.listing_id)
       v.listing_id, v.id as version_id, v.version, v.payload, v.reviewed_at
from   listing_versions v
where  v.status = 'approved'
order  by v.listing_id, v.version desc;

-- O que o gerador do site le. So isto, e nada mais: se nao esta aqui,
-- nao vai para o site.
create or replace view public_listings as
select l.id, l.slug, l.city, l.country, l.status,
       o.id as operator_id, o.name as operator_name,
       lv.payload, lv.version, lv.reviewed_at
from   listings l
join   operators o on o.id = l.operator_id
join   listing_live lv on lv.listing_id = l.id
where  l.status = 'live' and o.status = 'approved';

-- ---------------------------------------------------------------------
-- CALENDARIO — dados rapidos, sem revisao
-- ---------------------------------------------------------------------
do $$ begin
  create type day_status as enum ('open', 'closed', 'sold_out');
exception
  when duplicate_object then null;  -- ja existia; o ficheiro volta a correr
end $$;

create table if not exists availability (
  listing_id     uuid not null references listings(id) on delete cascade,
  day            date not null,
  status         day_status not null default 'open',
  -- quando o operador quer cobrar diferente num dia especifico (feriado,
  -- epoca alta). Em branco, vale o preco do anuncio.
  price_override numeric(10,2) check (price_override is null or price_override >= 0),
  seats_left     integer check (seats_left is null or seats_left >= 0),
  updated_at     timestamptz not null default now(),
  primary key (listing_id, day)
);

create index if not exists availability_dia_idx on availability(day)
  where status = 'open';

-- dias fechados ao nivel do operador: ferias, um veiculo em oficina
create table if not exists blackouts (
  id          uuid primary key default gen_random_uuid(),
  operator_id uuid not null references operators(id) on delete cascade,
  starts_on   date not null,
  ends_on     date not null,
  reason      text,
  created_at  timestamptz not null default now(),
  constraint intervalo_valido check (ends_on >= starts_on)
);

-- A resposta a pergunta "posso ir neste dia?". E uma funcao e nao uma
-- consulta montada no cliente, porque a regra de quem fecha um dia tem
-- de estar num sitio so.
create or replace function dia_disponivel(p_listing uuid, p_day date)
returns boolean
language sql
stable
as $$
  select
    p_day >= current_date
    and not exists (
      select 1 from availability a
      where a.listing_id = p_listing and a.day = p_day
        and a.status in ('closed', 'sold_out'))
    and not exists (
      select 1 from blackouts b
      join listings l on l.id = p_listing
      where b.operator_id = l.operator_id
        and p_day between b.starts_on and b.ends_on);
$$;

-- Quanto fica para o operador num preco. A conta esta aqui e so aqui:
-- feita a mao no site, no painel e na fatura, mais tarde ou mais cedo
-- os tres numeros deixam de bater certo.
create or replace function repartir(p_operator uuid, p_total numeric)
returns table (total numeric, comissao numeric, para_o_operador numeric)
language sql
stable
as $$
  select p_total,
         round(p_total * o.commission_rate, 2),
         round(p_total - p_total * o.commission_rate, 2)
  from operators o where o.id = p_operator;
$$;

-- ---------------------------------------------------------------------
-- PROCURAS — o que as pessoas escrevem e nao encontram
-- ---------------------------------------------------------------------
create table if not exists search_queries (
  id          bigserial primary key,
  q           text not null,
  results     integer not null default 0,
  city_match  text,
  country     text,
  created_at  timestamptz not null default now()
);

create index if not exists procuras_sem_resultado_idx
  on search_queries(created_at desc) where results = 0;

-- ---------------------------------------------------------------------
-- QUEM VE O QUE
--
-- Tudo fechado por omissao. Um operador ve e mexe no que e dele; o
-- administrador ve tudo; o publico nao ve nada diretamente — o site e
-- gerado a partir da vista `public_listings` e nao fala com a base.
-- ---------------------------------------------------------------------
alter table operators        enable row level security;
alter table operator_users   enable row level security;
alter table listings         enable row level security;
alter table listing_versions enable row level security;
alter table availability     enable row level security;
alter table blackouts        enable row level security;
alter table search_queries   enable row level security;
alter table admins           enable row level security;

drop policy if exists op_leitura on operators;
create policy op_leitura on operators for select
  using (is_admin() or id in (select meus_operadores()));

drop policy if exists op_escrita on operators;
create policy op_escrita on operators for update
  using (is_admin() or id in (select meus_operadores()))
  with check (is_admin() or id in (select meus_operadores()));

-- So o administrador muda o estado e a comissao. Um operador que se
-- pudesse aprovar a si proprio nao e um marketplace revisto.
drop policy if exists op_admin_insere on operators;
create policy op_admin_insere on operators for insert
  with check (is_admin());

drop policy if exists ou_leitura on operator_users;
create policy ou_leitura on operator_users for select
  using (is_admin() or user_id = auth.uid());

drop policy if exists an_leitura on listings;
create policy an_leitura on listings for select
  using (is_admin() or operator_id in (select meus_operadores()));

drop policy if exists an_escrita on listings;
create policy an_escrita on listings for all
  using (is_admin() or operator_id in (select meus_operadores()))
  with check (is_admin() or operator_id in (select meus_operadores()));

drop policy if exists ver_leitura on listing_versions;
create policy ver_leitura on listing_versions for select
  using (is_admin() or listing_id in (
    select id from listings where operator_id in (select meus_operadores())));

-- O operador submete; quem decide e o administrador. Por isso o insert
-- obriga ao estado `pending` e o update do estado e so do admin.
drop policy if exists ver_submete on listing_versions;
create policy ver_submete on listing_versions for insert
  with check (
    status = 'pending'
    and listing_id in (
      select id from listings where operator_id in (select meus_operadores())));

drop policy if exists ver_revisao on listing_versions;
create policy ver_revisao on listing_versions for update
  using (is_admin()) with check (is_admin());

drop policy if exists dis_tudo on availability;
create policy dis_tudo on availability for all
  using (is_admin() or listing_id in (
    select id from listings where operator_id in (select meus_operadores())))
  with check (is_admin() or listing_id in (
    select id from listings where operator_id in (select meus_operadores())));

drop policy if exists bl_tudo on blackouts;
create policy bl_tudo on blackouts for all
  using (is_admin() or operator_id in (select meus_operadores()))
  with check (is_admin() or operator_id in (select meus_operadores()));

drop policy if exists pr_admin on search_queries;
create policy pr_admin on search_queries for select using (is_admin());

drop policy if exists ad_leitura on admins;
create policy ad_leitura on admins for select using (is_admin());

-- ---------------------------------------------------------------------
-- As operacoes, como funcoes. O cliente nao escreve SQL: chama isto.
-- ---------------------------------------------------------------------

-- Submeter conteudo novo. Cria sempre uma versao nova em `pending`;
-- nunca mexe na que esta no ar.
create or replace function submeter_versao(p_listing uuid, p_payload jsonb)
returns uuid
language plpgsql
security invoker
set search_path = public
as $$
declare
  v_nova integer;
  v_id   uuid;
begin
  select coalesce(max(version), 0) + 1 into v_nova
  from listing_versions where listing_id = p_listing;

  insert into listing_versions (listing_id, version, payload, status, submitted_by)
  values (p_listing, v_nova, p_payload, 'pending', auth.uid())
  returning id into v_id;

  return v_id;
end;
$$;

-- Decidir. So o administrador, e a verificacao esta aqui dentro para
-- nao depender de o cliente se portar bem.
create or replace function rever_versao(p_version uuid, p_aprovar boolean,
                                        p_nota text default null)
returns void
language plpgsql
security invoker
set search_path = public
as $$
begin
  if not is_admin() then
    raise exception 'So um administrador pode rever versoes';
  end if;

  update listing_versions
     set status      = case when p_aprovar then 'approved' else 'rejected' end::review_status,
         reviewed_by = auth.uid(),
         reviewed_at = now(),
         review_note = p_nota
   where id = p_version and status = 'pending';

  if not found then
    raise exception 'Versao inexistente ou ja revista';
  end if;

  -- a primeira aprovacao poe o anuncio no ar
  if p_aprovar then
    update listings set status = 'live'
     where id = (select listing_id from listing_versions where id = p_version)
       and status = 'draft';
  end if;
end;
$$;

-- Abrir ou fechar dias. Nao passa por revisao nenhuma de proposito: e
-- dado rapido, e o operador tem de poder fechar amanha as onze da noite.
create or replace function marcar_dias(p_listing uuid, p_dias date[],
                                       p_status day_status)
returns integer
language plpgsql
security invoker
set search_path = public
as $$
declare
  n integer;
begin
  insert into availability (listing_id, day, status, updated_at)
  select p_listing, d, p_status, now() from unnest(p_dias) as d
  on conflict (listing_id, day)
    do update set status = excluded.status, updated_at = now();
  get diagnostics n = row_count;
  return n;
end;
$$;
