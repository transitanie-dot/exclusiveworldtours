-- =====================================================================
-- A frota, a capacidade e o lead time
--
-- Isto e a parte onde a GetYourGuide e estruturalmente fraca e onde um
-- marketplace de veiculo inteiro pode ser melhor. Tres decisoes:
--
-- 1. A CAPACIDADE VIVE NO VEICULO, NAO NO ANUNCIO.
--    A GYG conta "maximum groups per time slot" por option, e avisa
--    explicitamente contra partilhar capacidade entre options porque a
--    disponibilidade deles e lida de cache. Resultado: um operador com
--    uma carrinha e tres tours tem de fingir que tem tres carrinhas, ou
--    fechar os outros dois a mao sempre que vende um.
--
--    Aqui a disponibilidade e lida ao vivo, por isso o recurso pode ser
--    partilhado de verdade: a carrinha ocupada no dia 12 desaparece dos
--    tres tours ao mesmo tempo, sozinha. E o que o operador ja faz de
--    cabeca; o sistema so passa a fazer por ele.
--
-- 2. O LEAD TIME NAO TEM TECTO.
--    A GYG impoe que o cut-off nao pode exceder 10 horas, porque vive de
--    reservas de ultima hora. Um motorista nao se arranja em 10 horas.
--    Aqui o operador poe 24, 48 ou 72 e ninguem lhe diz que nao pode.
--
-- 3. UM ESCALAO TEM MINIMO E MAXIMO.
--    A categoria GROUP da GYG nao consegue exprimir um minimo de
--    participantes — ou aceitas de 1 pessoa, ou deixas de poder vender
--    ao grupo. Aqui um escalao e um intervalo.
-- =====================================================================

-- ---------------------------------------------------------------------
-- OS VEICULOS — a frota do operador, nao do anuncio
-- ---------------------------------------------------------------------
create table if not exists vehicles (
  id          uuid primary key default gen_random_uuid(),
  operator_id uuid not null references operators(id) on delete cascade,
  name        text not null,              -- "Mercedes V-Class", "Skoda Superb"
  max_pax     integer not null check (max_pax > 0 and max_pax < 100),
  plate       text,                        -- so o operador e o admin veem
  notes       text,
  active      boolean not null default true,
  created_at  timestamptz not null default now()
);

create index if not exists vehicles_operador_idx on vehicles(operator_id)
  where active;

-- Que veiculos servem que anuncio. Um veiculo serve varios anuncios, e e
-- isso que torna a capacidade partilhada possivel.
create table if not exists listing_vehicles (
  listing_id uuid not null references listings(id) on delete cascade,
  vehicle_id uuid not null references vehicles(id) on delete cascade,
  primary key (listing_id, vehicle_id)
);

create index if not exists lv_veiculo_idx on listing_vehicles(vehicle_id);

-- ---------------------------------------------------------------------
-- O CALENDARIO, AGORA POR VEICULO
--
-- `availability` continua a existir e continua a ser por anuncio: serve
-- para o operador fechar UM tour num dia em que o veiculo esta livre
-- (feriado so daquele percurso, guia que nao fala a lingua). Sao duas
-- perguntas diferentes e por isso sao duas tabelas:
--
--   vehicle_days   o veiculo esta ocupado?   -> afeta todos os anuncios
--   availability   este tour corre hoje?     -> afeta so este anuncio
-- ---------------------------------------------------------------------
do $$ begin
  create type vehicle_day_status as enum ('open', 'closed', 'booked');
exception when duplicate_object then null;
end $$;

create table if not exists vehicle_days (
  vehicle_id uuid not null references vehicles(id) on delete cascade,
  day        date not null,
  status     vehicle_day_status not null default 'open',
  note       text,                          -- "oficina", "casamento"
  updated_at timestamptz not null default now(),
  primary key (vehicle_id, day)
);

create index if not exists vd_dia_idx on vehicle_days(day)
  where status <> 'open';

-- ---------------------------------------------------------------------
-- O LEAD TIME, SEM TECTO
-- ---------------------------------------------------------------------
alter table listings
  add column if not exists lead_time_hours integer not null default 24;

do $$ begin
  alter table listings add constraint lead_time_razoavel
    check (lead_time_hours >= 0 and lead_time_hours <= 2160);  -- 90 dias
exception when duplicate_object then null;
end $$;

comment on column listings.lead_time_hours is
  'Horas minimas entre o pedido e a partida. Sem tecto artificial: a '
  'GetYourGuide limita isto a 10 horas e um motorista nao se arranja em '
  '10 horas.';

-- ---------------------------------------------------------------------
-- QUEM VE O QUE
-- ---------------------------------------------------------------------
alter table vehicles         enable row level security;
alter table listing_vehicles enable row level security;
alter table vehicle_days     enable row level security;

drop policy if exists v_tudo on vehicles;
create policy v_tudo on vehicles for all
  using (is_admin() or operator_id in (select meus_operadores()))
  with check (is_admin() or operator_id in (select meus_operadores()));

drop policy if exists lv_tudo on listing_vehicles;
create policy lv_tudo on listing_vehicles for all
  using (is_admin() or listing_id in (
    select id from listings where operator_id in (select meus_operadores())))
  with check (is_admin() or listing_id in (
    select id from listings where operator_id in (select meus_operadores())));

drop policy if exists vd_tudo on vehicle_days;
create policy vd_tudo on vehicle_days for all
  using (is_admin() or vehicle_id in (
    select id from vehicles where operator_id in (select meus_operadores())))
  with check (is_admin() or vehicle_id in (
    select id from vehicles where operator_id in (select meus_operadores())));

-- ---------------------------------------------------------------------
-- MARCAR DIAS DE UM VEICULO
--
-- Como o marcar_dias dos anuncios: imediato, sem revisao. Um operador
-- que precisa de fechar a carrinha as onze da noite fecha-a.
-- ---------------------------------------------------------------------
create or replace function marcar_veiculo(p_vehicle uuid, p_dias date[],
                                          p_status vehicle_day_status,
                                          p_nota text default null)
returns integer
language plpgsql security invoker set search_path = public as $$
declare
  n integer;
begin
  insert into vehicle_days (vehicle_id, day, status, note, updated_at)
  select p_vehicle, d, p_status, p_nota, now() from unnest(p_dias) as d
  on conflict (vehicle_id, day)
    do update set status = excluded.status,
                  note = coalesce(excluded.note, vehicle_days.note),
                  updated_at = now();
  get diagnostics n = row_count;
  return n;
end;
$$;

-- ---------------------------------------------------------------------
-- A PERGUNTA QUE INTERESSA
--
-- "Que veiculos tenho livres neste tour, neste dia?" A resposta cruza as
-- tres coisas: a frota ligada ao anuncio, os dias fechados do veiculo, e
-- os dias fechados do operador (ferias). O dia do anuncio e o lead time
-- entram em dias_abertos(), que e quem o publico chama.
-- ---------------------------------------------------------------------
create or replace function veiculos_livres(p_listing uuid, p_day date)
returns table (vehicle_id uuid, name text, max_pax integer)
language sql stable security definer set search_path = public as $$
  select v.id, v.name, v.max_pax
  from   listing_vehicles lv
  join   vehicles v on v.id = lv.vehicle_id
  join   listings l on l.id = lv.listing_id
  where  lv.listing_id = p_listing
    and  v.active
    and  not exists (
           select 1 from vehicle_days d
           where d.vehicle_id = v.id and d.day = p_day
             and d.status <> 'open')
    and  not exists (
           select 1 from blackouts b
           where b.operator_id = l.operator_id
             and p_day between b.starts_on and b.ends_on)
  order by v.max_pax, v.name;
$$;

-- ---------------------------------------------------------------------
-- dias_abertos(), outra vez — agora com frota e lead time
--
-- A assinatura e o tipo de retorno NAO mudam. Mudar o tipo de retorno de
-- uma funcao em Postgres obriga a um `drop` + `create`, e entre os dois
-- a pagina do tour fica sem resposta. Numa base de producao isso e uma
-- janela de erro por uma conveniencia de desenho; nao vale a pena.
--
-- Por isso sao duas perguntas e duas funcoes, o que alias e a divisao
-- certa:
--
--   dias_abertos    QUE DIAS posso ir? — a consulta do calendario, uma
--                   linha por dia, leve, chamada com intervalos grandes.
--   frota_no_dia    O QUE HA neste dia? — chamada so quando a pessoa
--                   escolhe uma data, e devolve o detalhe que a pagina
--                   precisa para dizer "ate 6 pessoas".
--
-- Um dia so aparece em dias_abertos se:
--   * esta dentro do lead time do anuncio;
--   * o anuncio nao o fechou;
--   * o operador nao esta de ferias;
--   * HA PELO MENOS UM VEICULO LIVRE — ou, se o operador ainda nao
--     registou frota nenhuma, cai no comportamento antigo e confia no
--     calendario do anuncio. Um operador sem frota registada nao fica
--     sem vender por causa de uma funcionalidade nova.
-- ---------------------------------------------------------------------
create or replace function dias_abertos(p_slug text, p_de date, p_ate date)
returns table (day date, price numeric)
language sql stable security definer set search_path = public as $$
  with anuncio as (
    select l.id, l.operator_id, l.lead_time_hours,
           exists (select 1 from listing_vehicles lv where lv.listing_id = l.id)
             as tem_frota
    from   listings l
    join   operators o on o.id = l.operator_id
    where  l.slug = p_slug and l.status = 'live' and o.status = 'approved'
  ),
  -- O primeiro dia que ainda e possivel servir.
  --
  -- Arredonda-se para CIMA, ao dia inteiro, e isso e deliberado. Um
  -- anuncio nao guarda ainda a hora de partida, so o dia. Se as 13h de
  -- hoje, com 24 horas de lead time, aceitassemos amanha, estariamos a
  -- aceitar uma partida que pode ser as 8h — 19 horas de aviso, nao 24.
  --
  -- Entre prometer a mais e prometer a menos, prometer a mais custa um
  -- cancelamento e prometer a menos custa um dia de calendario.
  --
  -- Quando os anuncios tiverem horas de partida, isto deixa de precisar
  -- de arredondar: compara-se o instante da partida com o instante do
  -- pedido, e a conta fica exata.
  limites as (
    select a.*,
           ((now() + make_interval(hours => a.lead_time_hours))::date
             + case when (now() + make_interval(hours => a.lead_time_hours))::time
                         <> '00:00:00' then 1 else 0 end)::date as primeiro
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
          or exists (select 1 from veiculos_livres(dias.id, dias.dia)));
$$;

-- O detalhe de um dia so. Devolve quantos veiculos estao livres e qual o
-- maior — que e o que decide a frase "ate 6 pessoas neste dia". Nao
-- devolve matriculas, notas nem precos especiais de outro dia: o publico
-- recebe o que precisa de ver e nada mais.
--
-- `disponivel` responde a pergunta inteira numa so coluna, para a pagina
-- nao ter de a reconstruir: um dia pode ter veiculos livres e ainda
-- assim estar fechado pelo calendario do anuncio.
create or replace function frota_no_dia(p_slug text, p_day date)
returns table (disponivel boolean, veiculos integer, max_pax integer,
               price numeric, lead_time_hours integer)
language sql stable security definer set search_path = public as $$
  with anuncio as (
    select l.id, l.operator_id, l.lead_time_hours,
           exists (select 1 from listing_vehicles lv where lv.listing_id = l.id)
             as tem_frota
    from   listings l
    join   operators o on o.id = l.operator_id
    where  l.slug = p_slug and l.status = 'live' and o.status = 'approved'
  )
  select
    exists (select 1 from dias_abertos(p_slug, p_day, p_day)),
    (select count(*)::integer from veiculos_livres(a.id, p_day)),
    (select max(vl.max_pax) from veiculos_livres(a.id, p_day) vl),
    (select av.price_override from availability av
      where av.listing_id = a.id and av.day = p_day),
    a.lead_time_hours
  from anuncio a;
$$;

revoke execute on function dias_abertos(text, date, date) from public;
grant  execute on function dias_abertos(text, date, date) to anon, authenticated;
revoke execute on function frota_no_dia(text, date) from public;
grant  execute on function frota_no_dia(text, date) to anon, authenticated;

revoke execute on function veiculos_livres(uuid, date) from public, anon;
grant  execute on function veiculos_livres(uuid, date) to authenticated;

-- ---------------------------------------------------------------------
-- O LEAD TIME TAMBEM TEM DE VALER NO PEDIDO
--
-- Dizer na pagina que o dia nao esta disponivel e uma coisa; aceitar o
-- pedido na mesma e outra. A validacao tem de estar na base, senao basta
-- abrir as ferramentas do browser para a saltar.
-- ---------------------------------------------------------------------
create or replace function registar_pedido(p jsonb)
returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_id    uuid;
  v_email text := btrim(coalesce(p->>'email', ''));
  v_data  date  := nullif(btrim(coalesce(p->>'wanted_on', '')), '')::date;
  v_slug  text  := left(btrim(coalesce(p->>'listing_slug', '')), 200);
  v_lead  integer;
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

  -- Se o pedido e para um tour nosso e tem data, o lead time vale.
  if v_data is not null and v_slug <> '' then
    select l.lead_time_hours into v_lead
    from listings l where l.slug = v_slug and l.status = 'live';

    -- A mesma conta de dias_abertos(), arredondada para cima pela mesma
    -- razao. As duas tem de concordar: se a pagina esconde um dia e a
    -- base o aceita, o operador recebe um pedido que nao pode servir.
    if v_lead is not null
       and v_data < ((now() + make_interval(hours => v_lead))::date
                     + case when (now() + make_interval(hours => v_lead))::time
                                 <> '00:00:00' then 1 else 0 end) then
      raise exception 'That tour needs at least % hours notice. Pick a later date, or write to us without a date and we will see what we can do.', v_lead;
    end if;
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
    nullif(v_slug, ''),
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
