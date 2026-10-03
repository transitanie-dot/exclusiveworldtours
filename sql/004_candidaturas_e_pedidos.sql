-- =====================================================================
-- Como alguem de fora entra no sistema
--
-- Ha duas portas, e as duas tinham de existir sem abrir uma tabela ao
-- publico:
--
--   CANDIDATURA   um operador quer vender aqui. Escreve, nao le. Fica
--                 em `new` e nao consegue por nada no site.
--   PEDIDO        um cliente quer uma data. Escreve, nao le.
--
-- Em ambos os casos o insert e feito por uma funcao `security definer`
-- com a validacao dentro. Se a validacao estivesse no formulario,
-- bastava abrir as ferramentas do browser para a saltar.
-- =====================================================================

do $$ begin
  create type application_status as enum ('new', 'contacted', 'approved', 'declined');
exception when duplicate_object then null;
end $$;

-- A candidatura fica numa tabela propria e nao em `operators`: uma
-- candidatura nao e um operador, e um pedido para ser um. Assim a tabela
-- que manda no site continua a ter so empresas a serio.
create table if not exists operator_applications (
  id            uuid primary key default gen_random_uuid(),
  company       text not null,
  contact_name  text not null,
  email         text not null,
  phone         text,
  website       text,
  country       text not null,
  city          text not null,
  fleet         text,            -- que veiculos tem, nas palavras deles
  tours_text    text,            -- que tours fazem hoje
  years         integer,         -- quantos anos de actividade
  licence_ref   text,
  status        application_status not null default 'new',
  notes         text,            -- notas do Ricardo
  operator_id   uuid references operators(id) on delete set null,
  created_at    timestamptz not null default now(),
  constraint cand_email_valido check (position('@' in email) > 1)
);

create index if not exists cand_novas_idx
  on operator_applications(created_at desc) where status = 'new';

alter table operator_applications enable row level security;

-- Ninguem le isto sem ser o administrador. Nem o proprio candidato: nao
-- ha nada aqui que ele precise de voltar a ler, e cada leitura possivel
-- e uma fuga possivel.
drop policy if exists cand_admin on operator_applications;
create policy cand_admin on operator_applications for select using (is_admin());

drop policy if exists cand_admin_muda on operator_applications;
create policy cand_admin_muda on operator_applications for update
  using (is_admin()) with check (is_admin());

create or replace function candidatar_operador(p jsonb)
returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_id    uuid;
  v_email text := btrim(coalesce(p->>'email', ''));
begin
  if length(btrim(coalesce(p->>'company', ''))) < 2 then
    raise exception 'Company name is required';
  end if;
  if length(btrim(coalesce(p->>'contact_name', ''))) < 2 then
    raise exception 'Contact name is required';
  end if;
  if position('@' in v_email) < 2 or length(v_email) > 200 then
    raise exception 'A valid email address is required';
  end if;
  if length(btrim(coalesce(p->>'country', ''))) < 2
     or length(btrim(coalesce(p->>'city', ''))) < 2 then
    raise exception 'Country and city are required';
  end if;

  -- A mesma empresa a submeter duas vezes na mesma hora e um duplo
  -- clique, nao duas candidaturas.
  if exists (select 1 from operator_applications
             where lower(email) = lower(v_email)
               and created_at > now() - interval '1 hour') then
    return null;
  end if;

  insert into operator_applications
    (company, contact_name, email, phone, website, country, city,
     fleet, tours_text, years, licence_ref)
  values (
    left(btrim(p->>'company'), 200),
    left(btrim(p->>'contact_name'), 200),
    v_email,
    left(btrim(p->>'phone'), 60),
    left(btrim(p->>'website'), 300),
    left(btrim(p->>'country'), 120),
    left(btrim(p->>'city'), 120),
    left(btrim(p->>'fleet'), 2000),
    left(btrim(p->>'tours_text'), 4000),
    nullif(btrim(coalesce(p->>'years', '')), '')::integer,
    left(btrim(p->>'licence_ref'), 120))
  returning id into v_id;

  return v_id;
end;
$$;

revoke execute on function candidatar_operador(jsonb) from public;
grant  execute on function candidatar_operador(jsonb) to anon, authenticated;

-- ---------------------------------------------------------------------
-- PEDIDOS DE CLIENTE
--
-- O "Check this date" e a pagina de contacto caem aqui. Fica guardado na
-- base ANTES de se tentar enviar email: se o email falhar, o pedido nao
-- se perde — e um pedido perdido e uma venda perdida.
-- ---------------------------------------------------------------------
do $$ begin
  create type enquiry_status as enum ('new', 'answered', 'booked', 'closed');
exception when duplicate_object then null;
end $$;

create table if not exists enquiries (
  id           uuid primary key default gen_random_uuid(),
  kind         text not null default 'general'
               check (kind in ('general', 'date', 'operator')),
  listing_slug text,            -- de que tour veio, se veio de um
  wanted_on    date,            -- a data que a pessoa quer
  party        integer check (party is null or (party > 0 and party < 200)),
  name         text not null,
  email        text not null,
  phone        text,
  message      text,
  status       enquiry_status not null default 'new',
  notes        text,
  source       text,            -- a pagina onde o formulario estava
  created_at   timestamptz not null default now(),
  constraint ped_email_valido check (position('@' in email) > 1)
);

create index if not exists pedidos_novos_idx
  on enquiries(created_at desc) where status = 'new';

alter table enquiries enable row level security;

drop policy if exists ped_admin on enquiries;
create policy ped_admin on enquiries for select using (is_admin());

drop policy if exists ped_admin_muda on enquiries;
create policy ped_admin_muda on enquiries for update
  using (is_admin()) with check (is_admin());

create or replace function registar_pedido(p jsonb)
returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_id    uuid;
  v_email text := btrim(coalesce(p->>'email', ''));
  v_data  date  := nullif(btrim(coalesce(p->>'wanted_on', '')), '')::date;
begin
  if length(btrim(coalesce(p->>'name', ''))) < 2 then
    raise exception 'Your name is required';
  end if;
  if position('@' in v_email) < 2 or length(v_email) > 200 then
    raise exception 'A valid email address is required';
  end if;
  -- Uma data no passado nao e um pedido, e um erro de escrita.
  if v_data is not null and v_data < current_date then
    raise exception 'That date has already passed';
  end if;
  if exists (select 1 from enquiries
             where lower(email) = lower(v_email)
               and created_at > now() - interval '2 minutes') then
    return null;
  end if;

  insert into enquiries
    (kind, listing_slug, wanted_on, party, name, email, phone, message, source)
  values (
    coalesce(nullif(btrim(p->>'kind'), ''), 'general'),
    left(btrim(p->>'listing_slug'), 200),
    v_data,
    nullif(btrim(coalesce(p->>'party', '')), '')::integer,
    left(btrim(p->>'name'), 200),
    v_email,
    left(btrim(p->>'phone'), 60),
    left(btrim(p->>'message'), 4000),
    left(btrim(p->>'source'), 300))
  returning id into v_id;

  return v_id;
end;
$$;

revoke execute on function registar_pedido(jsonb) from public;
grant  execute on function registar_pedido(jsonb) to anon, authenticated;

-- ---------------------------------------------------------------------
-- APROVAR UM CANDIDATO
--
-- Cria o operador, liga-o a candidatura e marca a candidatura. Numa
-- transacao so: ou acontece tudo, ou nao acontece nada. Metade disto
-- feito e um operador sem candidatura, ou o contrario.
-- ---------------------------------------------------------------------
create or replace function aprovar_candidatura(p_cand uuid)
returns uuid
language plpgsql security invoker set search_path = public as $$
declare
  c    operator_applications;
  v_op uuid;
begin
  if not is_admin() then
    raise exception 'So um administrador pode aprovar candidaturas';
  end if;

  select * into c from operator_applications where id = p_cand;
  if not found then
    raise exception 'Candidatura inexistente';
  end if;
  if c.operator_id is not null then
    return c.operator_id;   -- ja aprovada; chamar duas vezes nao faz mal
  end if;

  insert into operators (name, country, city, email, phone, website,
                         licence_ref, status, approved_at)
  values (c.company, c.country, c.city, c.email, c.phone, c.website,
          c.licence_ref, 'approved', now())
  returning id into v_op;

  update operator_applications
     set status = 'approved', operator_id = v_op
   where id = p_cand;

  return v_op;
end;
$$;

revoke execute on function aprovar_candidatura(uuid) from public, anon;
grant  execute on function aprovar_candidatura(uuid) to authenticated;
