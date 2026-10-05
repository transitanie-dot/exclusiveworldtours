-- =====================================================================
-- As horas de partida, e o lead time que deixa de arredondar
--
-- Ate aqui o lead time arredondava para cima ao dia inteiro, porque o
-- sistema sabia o DIA mas nao a HORA. Com 24 horas de aviso, pedir
-- amanha as 13h de hoje podia significar uma partida as 8h — 19 horas de
-- aviso, nao 24 — por isso o dia inteiro era recusado. Correto, e caro:
-- um tour que parte as 17h perdia um dia de calendario sem razao.
--
-- Com as horas de partida a conta passa a ser exata: compara-se o
-- instante da partida com o instante do pedido, partida a partida. O
-- mesmo dia pode ter a partida das 8h fechada e a das 17h aberta.
--
-- PORQUE E QUE AS HORAS SAO DISPONIBILIDADE E NAO CONTEUDO
--
-- Um cliente ve a hora de partida, por isso a tentacao e trata-la como
-- conteudo e faze-la passar pela revisao. Seria o mesmo erro que fazer o
-- calendario passar pela revisao. Um operador que tem de mudar a partida
-- de amanha das 8h para as 9h — motorista doente, estrada cortada — nao
-- pode esperar por mim. A GetYourGuide chega a mesma conclusao: os time
-- slots deles vivem em Manage > Availability, nao na revisao de produto.
-- =====================================================================

create table if not exists listing_times (
  listing_id uuid not null references listings(id) on delete cascade,
  starts_at  time not null,
  active     boolean not null default true,
  created_at timestamptz not null default now(),
  primary key (listing_id, starts_at)
);

create index if not exists lt_anuncio_idx on listing_times(listing_id)
  where active;

alter table listing_times enable row level security;

drop policy if exists lt_tudo on listing_times;
create policy lt_tudo on listing_times for all
  using (is_admin() or listing_id in (
    select id from listings where operator_id in (select meus_operadores())))
  with check (is_admin() or listing_id in (
    select id from listings where operator_id in (select meus_operadores())));

-- ---------------------------------------------------------------------
-- O FUSO HORARIO
--
-- Um tour parte as 8h NA CIDADE DELE. O servidor corre em UTC e o
-- cliente pode estar no Brasil. Sem um fuso por anuncio, "8h" nao quer
-- dizer nada e o lead time engana-se por horas — exatamente o erro que
-- esta migracao existe para corrigir.
--
-- Fica no anuncio e nao no operador porque um operador pode vender em
-- Lisboa e no Porto hoje, e em Sevilha amanha.
-- ---------------------------------------------------------------------
alter table listings
  add column if not exists timezone text not null default 'Europe/Dublin';

do $$ begin
  alter table listings add constraint fuso_existe
    check (now() at time zone timezone is not null);
exception when duplicate_object then null;
end $$;

comment on column listings.timezone is
  'O fuso da cidade de partida. Sem ele, "parte as 8h" nao tem significado '
  'e o lead time engana-se por horas.';

-- ---------------------------------------------------------------------
-- As partidas de um dia que ainda e possivel servir.
--
-- Esta e a funcao que todas as outras usam. Devolve as horas, por ordem,
-- que estao a mais de `lead_time_hours` de distancia. Um dia sem
-- partidas registadas devolve nada, e quem chama decide o que isso quer
-- dizer — ver a nota em dias_abertos.
-- ---------------------------------------------------------------------
create or replace function partidas_possiveis(p_listing uuid, p_day date)
returns table (starts_at time)
language sql stable security definer set search_path = public as $$
  select t.starts_at
  from   listing_times t
  join   listings l on l.id = t.listing_id
  where  t.listing_id = p_listing
    and  t.active
    -- O instante da partida, no fuso da cidade, comparado com agora.
    and  ((p_day + t.starts_at) at time zone l.timezone)
         >= now() + make_interval(hours => l.lead_time_hours)
  order  by t.starts_at;
$$;

-- ---------------------------------------------------------------------
-- dias_abertos(), com a conta exata
--
-- A assinatura nao muda, outra vez de proposito: mudar o tipo de retorno
-- obriga a um drop, e um drop numa base de producao e uma janela em que
-- a pagina do tour fica sem resposta.
--
-- A regra do lead time passa a ter dois caminhos, e a diferenca entre
-- eles e o que esta migracao traz:
--
--   COM partidas registadas   o dia entra se ALGUMA partida ainda for
--                             possivel. Exato, hora a hora.
--   SEM partidas registadas   arredonda-se para cima ao dia inteiro,
--                             como antes. Um operador que ainda nao
--                             registou horas nao fica pior do que
--                             estava.
-- ---------------------------------------------------------------------
create or replace function dias_abertos(p_slug text, p_de date, p_ate date)
returns table (day date, price numeric)
language sql stable security definer set search_path = public as $$
  with anuncio as (
    select l.id, l.operator_id, l.lead_time_hours, l.timezone,
           exists (select 1 from listing_vehicles lv where lv.listing_id = l.id)
             as tem_frota,
           exists (select 1 from listing_times t
                   where t.listing_id = l.id and t.active) as tem_horas
    from   listings l
    join   operators o on o.id = l.operator_id
    where  l.slug = p_slug and l.status = 'live' and o.status = 'approved'
  ),
  -- Sem horas registadas, o primeiro dia inteiro dentro do prazo. Com
  -- horas, basta comecar em hoje: a filtragem exata faz-se por partida,
  -- la em baixo.
  limites as (
    select a.*,
           case when a.tem_horas then current_date
                else ((now() + make_interval(hours => a.lead_time_hours))::date
                       + case when (now() + make_interval(hours => a.lead_time_hours))::time
                                   <> '00:00:00' then 1 else 0 end)::date
           end as primeiro
    from anuncio a
  ),
  dias as (
    select d::date as dia, l.*
    from limites l,
         generate_series(greatest(p_de, l.primeiro),
                         least(p_ate, (current_date + 400)),
                         interval '1 day') as d
  )
  select dias.dia,
         (select a.price_override from availability a
           where a.listing_id = dias.id and a.day = dias.dia)
  from   dias
  where  not exists (
           select 1 from availability a
           where a.listing_id = dias.id and a.day = dias.dia
             and a.status in ('closed', 'sold_out'))
    and  not exists (
           select 1 from blackouts b
           where b.operator_id = dias.operator_id
             and dias.dia between b.starts_on and b.ends_on)
    and  (not dias.tem_frota
          or exists (select 1 from veiculos_livres(dias.id, dias.dia)))
    and  (not dias.tem_horas
          or exists (select 1 from partidas_possiveis(dias.id, dias.dia)));
$$;

-- ---------------------------------------------------------------------
-- frota_no_dia(), agora tambem com as partidas
--
-- Mesma razao de sempre para nao mudar o tipo de retorno. As horas vao
-- numa funcao propria, `partidas_no_dia`, que a pagina do tour chama ao
-- mesmo tempo — e que devolve so o que o publico pode ver.
-- ---------------------------------------------------------------------
create or replace function partidas_no_dia(p_slug text, p_day date)
returns table (starts_at time)
language sql stable security definer set search_path = public as $$
  select p.starts_at
  from   listings l
  join   operators o on o.id = l.operator_id,
         lateral partidas_possiveis(l.id, p_day) p
  where  l.slug = p_slug and l.status = 'live' and o.status = 'approved'
    -- Um dia fechado pelo anuncio nao tem partidas, mesmo que as horas
    -- por si so ainda dessem.
    and  not exists (
           select 1 from availability a
           where a.listing_id = l.id and a.day = p_day
             and a.status in ('closed', 'sold_out'))
    and  not exists (
           select 1 from blackouts b
           where b.operator_id = l.operator_id
             and p_day between b.starts_on and b.ends_on)
  order by p.starts_at;
$$;

revoke execute on function partidas_no_dia(text, date) from public;
grant  execute on function partidas_no_dia(text, date) to anon, authenticated;
revoke execute on function partidas_possiveis(uuid, date) from public, anon;
grant  execute on function partidas_possiveis(uuid, date) to authenticated;

-- ---------------------------------------------------------------------
-- O pedido guarda a hora, e a validacao usa-a
-- ---------------------------------------------------------------------
alter table enquiries
  add column if not exists wanted_at time;

create or replace function registar_pedido(p jsonb)
returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_id    uuid;
  v_email text := btrim(coalesce(p->>'email', ''));
  v_data  date  := nullif(btrim(coalesce(p->>'wanted_on', '')), '')::date;
  v_hora  time  := nullif(btrim(coalesce(p->>'wanted_at', '')), '')::time;
  v_slug  text  := left(btrim(coalesce(p->>'listing_slug', '')), 200);
  v_lead  integer;
  v_horas boolean;
  v_id_l  uuid;
begin
  if length(btrim(coalesce(p->>'name', ''))) < 2 then
    raise exception 'Your name is required';
  end if;
  if position('@' in v_email) < 2 or length(v_email) > 200 then
    raise exception 'A valid email address is required';
  end if;
  if v_data is not null and v_data < current_date then
    raise exception 'That date has already passed';
  end if;

  if v_data is not null and v_slug <> '' then
    select l.id, l.lead_time_hours,
           exists (select 1 from listing_times t
                   where t.listing_id = l.id and t.active)
      into v_id_l, v_lead, v_horas
    from listings l where l.slug = v_slug and l.status = 'live';

    if v_lead is not null then
      if v_horas then
        -- Com horas registadas a conta e exata: tem de sobrar pelo menos
        -- uma partida nesse dia. Se a pessoa escolheu uma hora, tem de
        -- ser essa.
        if v_hora is not null then
          if not exists (select 1 from partidas_possiveis(v_id_l, v_data) x
                         where x.starts_at = v_hora) then
            raise exception 'That departure is no longer possible. This tour needs % hours'' notice; pick another time or a later date.', v_lead;
          end if;
        elsif not exists (select 1 from partidas_possiveis(v_id_l, v_data)) then
          raise exception 'No departure that day is still possible. This tour needs % hours'' notice.', v_lead;
        end if;
      else
        -- Sem horas registadas, a regra antiga: o dia inteiro.
        if v_data < ((now() + make_interval(hours => v_lead))::date
                     + case when (now() + make_interval(hours => v_lead))::time
                                 <> '00:00:00' then 1 else 0 end) then
          raise exception 'That tour needs at least % hours notice. Pick a later date, or write to us without a date and we will see what we can do.', v_lead;
        end if;
      end if;
    end if;
  end if;

  if exists (select 1 from enquiries
             where lower(email) = lower(v_email)
               and created_at > now() - interval '2 minutes') then
    return null;
  end if;

  insert into enquiries
    (kind, listing_slug, wanted_on, wanted_at, party, name, email, phone,
     message, source)
  values (
    coalesce(nullif(btrim(p->>'kind'), ''), 'general'),
    nullif(v_slug, ''),
    v_data, v_hora,
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
-- Pôr e tirar horas, em bloco
-- ---------------------------------------------------------------------
create or replace function definir_partidas(p_listing uuid, p_horas time[])
returns integer
language plpgsql security invoker set search_path = public as $$
declare
  n integer;
begin
  -- Desativa as que sairam em vez de as apagar: um pedido antigo pode
  -- apontar para uma hora que ja nao se vende, e a linha tem de
  -- continuar a fazer sentido quando alguem a ler daqui a um mes.
  update listing_times set active = false
   where listing_id = p_listing
     and not (starts_at = any(coalesce(p_horas, array[]::time[])));

  insert into listing_times (listing_id, starts_at, active)
  select p_listing, h, true from unnest(coalesce(p_horas, array[]::time[])) as h
  on conflict (listing_id, starts_at) do update set active = true;

  select count(*) into n from listing_times
   where listing_id = p_listing and active;
  return n;
end;
$$;
