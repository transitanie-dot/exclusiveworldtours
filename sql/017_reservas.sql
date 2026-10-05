-- =====================================================================
-- RESERVAS E PAGAMENTO
--
-- O dinheiro entra todo na EWT e o operador e pago depois (decisao do
-- Ricardo, 5 out 2026). Duas formas de pagar, como no Airportlink:
--
--   agora    o Stripe cobra no momento da reserva
--   depois   o Stripe GUARDA o cartao e cobra-se N horas antes
--
-- Porque e que "pagar depois" existe: o Stripe nao devolve a comissao
-- num reembolso. Se o cliente cancela — e com cancelamento gratis ate
-- 24 horas antes vai cancelar — uma cobranca ja feita custa-nos a
-- comissao do Stripe nos dois sentidos. Guardar o cartao e cobrar perto
-- da partida faz com que a maior parte dos cancelamentos aconteca antes
-- de haver cobranca nenhuma.
--
-- O QUE ESTE FICHEIRO NAO FAZ
-- ---------------------------
-- Nao fala com o Stripe. O site e estatico e nao tem onde guardar uma
-- chave; quem fala com o Stripe e uma Edge Function do Supabase, que tem
-- a chave nos segredos do projeto. Este ficheiro e a parte que tem de
-- ser verdade mesmo que a Edge Function tenha um erro:
--
--   cotar()            o preco, calculado na base e nunca no browser
--   reservar()         cria a reserva E prende o veiculo, de forma atomica
--   confirmar_reserva() o pagamento entrou
--   cancelar_reserva()  solta o veiculo
--   reservas_a_cobrar() quais e que estao na hora de cobrar
--
-- O PRECO NUNCA VEM DO BROWSER
-- ----------------------------
-- O browser manda o slug, o dia, a hora e quantas pessoas. O preco sai
-- da versao APROVADA do anuncio, aqui dentro. Um preco mudado nas
-- ferramentas do browser nao chega ao Stripe. E a cotar() e a MESMA
-- funcao que a pagina usa para mostrar o preco, por isso nao ha duas
-- copias da regra para divergirem.
-- =====================================================================

-- ---------------------------------------------------------------------
-- AS REGRAS DO PAGAR DEPOIS, NUMA TABELA
--
-- Os limiares vao mudar com o ticket medio. Numa tabela mudam-se com um
-- update; no codigo da Edge Function obrigavam a um deploy.
-- ---------------------------------------------------------------------
create table if not exists payment_rules (
  id                     integer primary key default 1 check (id = 1),
  min_hours_for_later    integer not null default 72,
  charge_lead_hours      integer not null default 72,
  max_value_for_later    numeric(10,2) not null default 1200.00,
  max_charge_attempts    integer not null default 3,
  retry_interval_hours   integer not null default 8,
  hold_minutes           integer not null default 30,
  updated_at             timestamptz not null default now(),
  check (charge_lead_hours <= min_hours_for_later),
  check (hold_minutes between 5 and 240)
);

comment on table payment_rules is
  'Uma linha so. O charge_lead_hours nunca pode ser maior que o '
  'min_hours_for_later: cobrar-se-ia antes de a reserva poder existir.';

comment on column payment_rules.min_hours_for_later is
  'Minimo de aviso para pagar depois. 72 horas e nao 48 como nos '
  'transfers: um tour privado de dia inteiro obriga o operador a '
  'recusar outro trabalho, e um cancelamento a 48 horas deixa-lhe o '
  'dia vazio.';

comment on column payment_rules.hold_minutes is
  'Quanto tempo uma reserva por pagar prende o veiculo. Passado isto o '
  'veiculo volta a aparecer livre, mesmo que a reserva fique por ai.';

insert into payment_rules (id) values (1) on conflict (id) do nothing;

-- ---------------------------------------------------------------------
-- AS RESERVAS
--
-- O preco e a reparticao ficam GRAVADOS na linha, nao calculados depois.
-- Se o operador renegociar a comissao em janeiro, as reservas de
-- dezembro continuam a dizer o que foi acordado em dezembro. Uma
-- reparticao calculada ao vivo reescreve o passado.
-- ---------------------------------------------------------------------
do $$ begin
  create type booking_status as enum
    ('pending', 'confirmed', 'paid', 'cancelled', 'refunded');
exception when duplicate_object then null;
end $$;

do $$ begin
  create type payment_mode as enum ('now', 'later');
exception when duplicate_object then null;
end $$;

create table if not exists bookings (
  id              uuid primary key default gen_random_uuid(),
  reference       text not null unique,

  -- O anuncio no momento da reserva. O listing_id para ligar, e o
  -- titulo e o slug COPIADOS: o operador pode mudar o titulo amanha e
  -- a reserva tem de continuar a dizer o que a pessoa comprou.
  listing_id      uuid not null references listings(id),
  listing_slug    text not null,
  tour_title      text not null,
  operator_id     uuid not null references operators(id),
  listing_version integer,

  booking_date    date not null,
  start_time      time,
  pax             integer not null check (pax > 0 and pax < 100),
  vehicle_id      uuid references vehicles(id),
  vehicle_name    text,

  price_total     numeric(10,2) not null check (price_total >= 0),
  currency        text not null default 'EUR',
  commission_rate numeric(5,4) not null,
  platform_amount numeric(10,2) not null,
  operator_amount numeric(10,2) not null,

  payment_mode    payment_mode not null,
  status          booking_status not null default 'pending',

  charge_at       timestamptz,
  charged_at      timestamptz,
  charge_attempts integer not null default 0,

  stripe_session_id        text unique,
  stripe_payment_intent    text,
  stripe_customer_id       text,
  stripe_payment_method_id text,
  stripe_setup_intent_id   text,

  customer_name   text,
  customer_email  text,
  customer_phone  text,
  pickup          text,
  notes           text,

  -- Quando o operador foi pago. Nulo = a pagar.
  payout_at       timestamptz,
  payout_note     text,

  cancelled_at    timestamptz,
  cancel_reason   text,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),

  -- A soma tem de fechar. Uma reparticao que nao da o total e um erro
  -- de contabilidade a espera de acontecer.
  constraint reparticao_fecha
    check (round(platform_amount + operator_amount, 2) = round(price_total, 2))
);

create index if not exists bookings_operador_idx
  on bookings(operator_id, booking_date desc);
create index if not exists bookings_dia_idx
  on bookings(booking_date) where status in ('confirmed', 'paid');
create index if not exists bookings_a_cobrar_idx
  on bookings(charge_at) where payment_mode = 'later' and charged_at is null;
create index if not exists bookings_a_pagar_idx
  on bookings(operator_id) where status = 'paid' and payout_at is null;

-- A referencia que o cliente le ao telefone. Curta, sem vogais (nao se
-- forma uma palavra por acidente) e sem I, O, 0 e 1 (confundem-se).
-- O `set search_path` NAO e cosmetico aqui.
--
-- Esta funcao nao e `security definer`, mas e CHAMADA de dentro da
-- reservar(), que e. Com o search_path a mudar com quem chama, bastava
-- criar um esquema proprio com uma tabela `bookings` a frente do public
-- para esta funcao passar a ler outra coisa — e o que ela devolve e a
-- referencia que vai para a reserva. O linter do Supabase apanhou isto.
create or replace function nova_referencia()
returns text language plpgsql
set search_path = public as $$
declare
  alfabeto text := 'ACDEFGHJKLMNPQRSTUVWXYZ23456789';
  r text;
  i integer;
begin
  loop
    r := 'EW';
    for i in 1..6 loop
      r := r || substr(alfabeto, 1 + floor(random() * length(alfabeto))::integer, 1);
    end loop;
    exit when not exists (select 1 from bookings b where b.reference = r);
  end loop;
  return r;
end $$;

-- ---------------------------------------------------------------------
-- O VEICULO PRESO
--
-- Um veiculo nao pode ser vendido duas vezes no mesmo dia. Entre o
-- momento em que o cliente abre o Stripe e o momento em que paga passam
-- minutos, e nesses minutos outra pessoa pode estar a comprar o mesmo.
--
-- A trava e a CHAVE PRIMARIA da vehicle_days: um `insert ... on conflict
-- do nothing` que nao insere nada quer dizer que alguem chegou primeiro.
-- Nao e um lock que se possa esquecer de largar nem uma leitura seguida
-- de uma escrita com uma janela pelo meio: e uma operacao so.
--
-- Uma reserva por pagar nao pode prender o veiculo para sempre, por isso
-- a marca leva uma validade. Passada a validade o dia volta a aparecer
-- livre — e isso tem de valer tambem para a veiculos_livres(), que e
-- reescrita aqui em baixo.
-- ---------------------------------------------------------------------
alter table vehicle_days
  add column if not exists booking_id uuid references bookings(id) on delete set null,
  add column if not exists hold_expires_at timestamptz;

-- A `note` NAO e escrita pela reserva, e isso e deliberado. A nota do
-- dia e do operador ("oficina", "casamento", "so de manha"), e a reserva
-- ja se identifica pelo booking_id. Escrever 'Reserva EWxxxx' na nota
-- apagava o que o operador tinha escrito, e libertar o dia a seguir
-- apagava-o de vez.
comment on column vehicle_days.hold_expires_at is
  'So existe numa marca provisoria (reserva por pagar). Passada a hora, '
  'a veiculos_livres() ignora a linha. Quando o pagamento entra, a '
  'confirmar_reserva() poe isto a nulo e a marca passa a definitiva.';

-- A mesma assinatura e o mesmo tipo de retorno de sempre: um
-- `create or replace` nao deixa a pagina do tour sem resposta.
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
             and d.status <> 'open'
             -- Uma marca provisoria que ja passou da validade nao
             -- prende nada. E a unica diferenca em relacao a versao da
             -- 006, e e o que impede uma reserva abandonada no Stripe
             -- de fechar o dia de um operador.
             and (d.hold_expires_at is null or d.hold_expires_at > now()))
    and  not exists (
           select 1 from blackouts b
           where b.operator_id = l.operator_id
             and p_day between b.starts_on and b.ends_on)
  order by v.max_pax, v.name;
$$;

revoke execute on function veiculos_livres(uuid, date) from public, anon;
grant  execute on function veiculos_livres(uuid, date) to authenticated;

-- ---------------------------------------------------------------------
-- COTAR
--
-- Responde a pergunta inteira: quanto custa, pode-se pagar depois, e se
-- nao se pode, PORQUE. Um "nao disponivel" sem razao parece uma avaria;
-- "a partida e dentro de 40 horas, e pagar depois precisa de 72" e uma
-- regra que a pessoa percebe e pode contornar escolhendo outra data.
--
-- Devolve jsonb e nao uma tabela, de proposito: a forma vai crescer
-- (extras, moedas, descontos) e um jsonb cresce sem `drop function`.
--
-- Pode ser chamada por quem nao assinou: nao devolve nada que nao esteja
-- ja na pagina. E e essa a razao de ser — a pagina e o checkout usam a
-- mesma funcao, por isso nao ha duas copias do preco.
-- ---------------------------------------------------------------------
create or replace function cotar(p jsonb)
returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare
  v_slug  text := nullif(trim(p->>'slug'), '');
  v_dia   date;
  v_hora  time;
  v_pax   integer;
  a       record;
  r       record;
  v_tier  jsonb;
  v_preco numeric;
  v_max   integer;
  v_horas numeric;
  v_mais_cedo timestamptz;
begin
  if v_slug is null then
    return jsonb_build_object('ok', false, 'code', 'noTour',
      'error', 'We could not find this tour.');
  end if;

  begin
    v_dia  := (p->>'date')::date;
    v_pax  := (p->>'pax')::integer;
    v_hora := nullif(p->>'time', '')::time;
  exception when others then
    return jsonb_build_object('ok', false, 'code', 'badInput',
      'error', 'Check the date, the time and the number of people.');
  end;

  -- O anuncio, na versao aprovada. Lido sobre as tabelas e nunca
  -- atraves da listing_live: ver a nota na 010.
  select l.id, l.operator_id, l.lead_time_hours, l.timezone,
         o.commission_rate, o.name as operador,
         lv.payload, lv.version
    into a
  from   listings l
  join   operators o on o.id = l.operator_id
  join   (select distinct on (v.listing_id)
                 v.listing_id, v.payload, v.version
          from   listing_versions v
          where  v.status = 'approved'
          order  by v.listing_id, v.version desc) lv on lv.listing_id = l.id
  where  l.slug = v_slug and l.status = 'live' and o.status = 'approved';

  if a.id is null then
    return jsonb_build_object('ok', false, 'code', 'noTour',
      'error', 'We could not find this tour.');
  end if;

  if v_pax is null or v_pax < 1 then
    return jsonb_build_object('ok', false, 'code', 'noPax',
      'error', 'Tell us how many people are travelling.');
  end if;

  -- O escalao: o primeiro cujo maximo chega para o grupo. Os escaloes
  -- vivem no payload da versao aprovada, que e o mesmo texto que a
  -- pagina mostra.
  select t into v_tier
  from   jsonb_array_elements(
           coalesce(a.payload->'durations'->0->'tiers', '[]'::jsonb)) as t
  where  (t->>'max')::integer >= v_pax
  order  by (t->>'max')::integer
  limit  1;

  select max((t->>'max')::integer) into v_max
  from   jsonb_array_elements(
           coalesce(a.payload->'durations'->0->'tiers', '[]'::jsonb)) as t;

  if v_tier is null then
    return jsonb_build_object('ok', false, 'code', 'tooMany',
      'maxPax', v_max,
      'error', case when v_max is null
                 then 'This tour has no online price yet.'
                 else format('This tour takes up to %s people.', v_max) end);
  end if;

  v_preco := (v_tier->>'price')::numeric;
  if v_preco is null or v_preco <= 0 then
    return jsonb_build_object('ok', false, 'code', 'noPrice',
      'error', 'This tour has no online price yet. Send us a message and we will quote it.');
  end if;

  -- Um preco especial para aquele dia, se o operador o definiu.
  select coalesce(av.price_override, v_preco) into v_preco
  from   (select 1) z
  left   join availability av on av.listing_id = a.id and av.day = v_dia;
  v_preco := coalesce(v_preco, (v_tier->>'price')::numeric);

  if v_dia is null then
    return jsonb_build_object('ok', false, 'code', 'noDate',
      'error', 'Pick the date of the tour.',
      'price', v_preco, 'currency', 'EUR',
      'vehicle', v_tier->>'vehicle', 'maxPax', v_max);
  end if;

  -- O dia esta aberto? A dias_abertos() ja soma o lead time, o
  -- calendario do anuncio, as ferias do operador e a frota livre.
  if not exists (select 1 from dias_abertos(v_slug, v_dia, v_dia)) then
    return jsonb_build_object('ok', false, 'code', 'dayClosed',
      'error', 'That day is not available. Pick another one.',
      'price', v_preco, 'currency', 'EUR', 'maxPax', v_max);
  end if;

  -- A hora, se a disseram, tem de ser uma das partidas que ainda estao
  -- dentro do prazo. A partidas_no_dia() compara o instante exato no
  -- fuso do anuncio — e por isso que a listings.timezone existe.
  if v_hora is not null
     and exists (select 1 from listing_times t
                  where t.listing_id = a.id and t.active)
     and not exists (select 1 from partidas_no_dia(v_slug, v_dia) pd
                      where pd.starts_at = v_hora) then
    return jsonb_build_object('ok', false, 'code', 'timeClosed',
      'error', 'That start time is no longer available for this date.',
      'price', v_preco, 'currency', 'EUR', 'maxPax', v_max);
  end if;

  -- Ha veiculo que leve o grupo?
  select count(*)::integer as n, max(vl.max_pax) as maior into r
  from   veiculos_livres(a.id, v_dia) vl
  where  vl.max_pax >= v_pax;

  if exists (select 1 from listing_vehicles lx where lx.listing_id = a.id)
     and coalesce(r.n, 0) = 0 then
    return jsonb_build_object('ok', false, 'code', 'noVehicle',
      'error', format('No vehicle for %s people on that date.', v_pax),
      'price', v_preco, 'currency', 'EUR', 'maxPax', v_max);
  end if;

  -- Quantas horas faltam para a partida, no fuso do anuncio. Sem hora
  -- marcada assume-se o inicio do dia: entre prometer a mais e prometer
  -- a menos, prometer a menos custa um dia de calendario e prometer a
  -- mais custa um cancelamento.
  v_mais_cedo := ((v_dia + coalesce(v_hora, time '00:00'))
                    at time zone coalesce(a.timezone, 'UTC'));
  v_horas := extract(epoch from (v_mais_cedo - now())) / 3600.0;

  return (
    select jsonb_build_object(
      'ok', true,
      'slug', v_slug,
      'title', a.payload->>'title',
      'operator', a.operador,
      'version', a.version,
      'date', v_dia,
      'time', v_hora,
      'pax', v_pax,
      'vehicle', v_tier->>'vehicle',
      'maxPax', v_max,
      'price', v_preco,
      'currency', 'EUR',
      'hoursToStart', round(v_horas, 1),
      'photo', a.payload->'photos'->0->>'url',
      'payLater', permite,
      'payLaterReason', razao,
      'payLaterCode', codigo,
      'chargeAt', case when permite
                    then v_mais_cedo - make_interval(hours => pr.charge_lead_hours)
                  end,
      'photoAlt', a.payload->'photos'->0->>'alt')
    -- A REPARTICAO, SO PARA QUEM ASSINOU
    --
    -- Concatenada e nao posta num `case` dentro do jsonb_build_object,
    -- e a diferenca importa: um `case` que da null deixa a CHAVE no
    -- objeto com o valor null, e `->'split' is null` passa a ser falso.
    -- Quem le do outro lado ve uma chave "split" e conclui que ha
    -- reparticao para ler. Concatenar um objeto vazio nao deixa chave
    -- nenhuma, e ausente quer dizer ausente.
    --
    -- A taxa de comissao de um operador nao e assunto do publico.
    || case when auth.uid() is not null then
         jsonb_build_object('split', jsonb_build_object(
           'rate', a.commission_rate,
           'platform', round(v_preco * a.commission_rate, 2),
           'operator', round(v_preco - v_preco * a.commission_rate, 2)))
       else '{}'::jsonb end
    from payment_rules pr,
    lateral (
      select
        case
          when v_horas < pr.min_hours_for_later then false
          when v_preco > pr.max_value_for_later then false
          else true
        end as permite,
        case
          when v_horas < pr.min_hours_for_later then
            format('The tour starts in about %s hours. Paying later needs at least %s hours'' notice, so this one is paid at booking.',
                   round(v_horas)::integer, pr.min_hours_for_later)
          when v_preco > pr.max_value_for_later then
            'Tours above our higher-value threshold are paid at booking.'
        end as razao,
        case
          when v_horas < pr.min_hours_for_later then 'tooSoon'
          when v_preco > pr.max_value_for_later then 'tooExpensive'
        end as codigo
    ) x
    where pr.id = 1);
end $$;

revoke execute on function cotar(jsonb) from public;
grant  execute on function cotar(jsonb) to anon, authenticated;

-- ---------------------------------------------------------------------
-- RESERVAR
--
-- Cria a reserva e prende o veiculo na MESMA transacao. Devolve o que a
-- Edge Function precisa de mandar ao Stripe: a referencia, o valor em
-- centimos, o titulo e a fotografia.
--
-- Nao esta aberta a quem nao assinou. Quem a chama e a Edge Function,
-- com a chave de servico — porque se a reserva se pudesse criar do
-- browser, criavam-se mil reservas e prendia-se a frota toda de um
-- operador sem pagar nada.
-- ---------------------------------------------------------------------
create or replace function reservar(p jsonb)
returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  c        jsonb;
  v_id     uuid;
  v_ref    text;
  v_modo   payment_mode;
  v_veic   record;
  a        record;
  pr       record;
  v_preso  integer;
  v_dia    date;
  v_hora   time;
begin
  -- O preco e a disponibilidade saem da MESMA funcao que a pagina usou.
  c := cotar(p);
  if not (c->>'ok')::boolean then
    return c;
  end if;

  v_dia  := (c->>'date')::date;
  v_hora := nullif(c->>'time', '')::time;

  -- "Pagar depois" e um pedido, nao uma ordem: so vale se a cotar()
  -- disse que sim. Vindo do browser, qualquer pessoa reservava um tour
  -- de amanha sem pagar nada.
  v_modo := case
    when coalesce(p->>'payment_mode', 'now') = 'later'
         and (c->>'payLater')::boolean then 'later'
    else 'now' end::payment_mode;

  select l.id, l.operator_id, o.commission_rate
    into a
  from   listings l join operators o on o.id = l.operator_id
  where  l.slug = c->>'slug';

  select * into pr from payment_rules where id = 1;

  v_ref := nova_referencia();

  insert into bookings (
    reference, listing_id, listing_slug, tour_title, operator_id,
    listing_version, booking_date, start_time, pax,
    price_total, currency, commission_rate, platform_amount, operator_amount,
    payment_mode, status, charge_at,
    customer_name, customer_email, customer_phone, pickup, notes)
  values (
    v_ref, a.id, c->>'slug', c->>'title', a.operator_id,
    (c->>'version')::integer, v_dia, v_hora, (c->>'pax')::integer,
    (c->>'price')::numeric, 'EUR', a.commission_rate,
    round((c->>'price')::numeric * a.commission_rate, 2),
    round((c->>'price')::numeric - (c->>'price')::numeric * a.commission_rate, 2),
    v_modo, 'pending',
    case when v_modo = 'later' then (c->>'chargeAt')::timestamptz end,
    nullif(trim(p->>'name'), ''), nullif(trim(lower(p->>'email')), ''),
    nullif(trim(p->>'phone'), ''), nullif(trim(p->>'pickup'), ''),
    nullif(trim(p->>'notes'), ''))
  returning id into v_id;

  -- PRENDER O VEICULO
  --
  -- O menor veiculo que leve o grupo, para nao gastar o de 8 lugares num
  -- casal. O `on conflict do nothing` e a trava: se ninguem inseriu,
  -- alguem chegou primeiro e tenta-se o seguinte.
  for v_veic in
    select vl.vehicle_id, vl.name, vl.max_pax
    from   veiculos_livres(a.id, v_dia) vl
    where  vl.max_pax >= (c->>'pax')::integer
    order  by vl.max_pax
  loop
    insert into vehicle_days (vehicle_id, day, status, booking_id,
                              hold_expires_at)
    values (v_veic.vehicle_id, v_dia, 'booked', v_id,
            now() + make_interval(mins => pr.hold_minutes))
    on conflict (vehicle_id, day) do update
      set status = 'booked', booking_id = v_id,
          hold_expires_at = now() + make_interval(mins => pr.hold_minutes),
          updated_at = now()
      -- QUEM E QUE SE PODE PISAR
      --
      -- Uma linha 'open' (o operador escreveu uma nota num dia que
      -- continua a venda) ou uma marca provisoria que ja caducou. Uma
      -- marca definitiva, ou uma provisoria ainda valida, nao.
      --
      -- A primeira metade desta condicao faltava, e o resultado era que
      -- um operador que escrevesse uma nota num dia aberto tornava esse
      -- dia IMPOSSIVEL de vender: a linha existia, o update nao a
      -- tocava, nenhum veiculo ficava preso, e o cliente lia "someone
      -- booked the last vehicle" num dia em que nao havia reserva
      -- nenhuma. A veiculos_livres() dizia que o dia estava livre, e
      -- dizia bem — era a reserva que nao o conseguia prender.
      where vehicle_days.status = 'open'
         or (vehicle_days.hold_expires_at is not null
             and vehicle_days.hold_expires_at <= now());

    get diagnostics v_preso = row_count;
    if v_preso > 0 then
      update bookings set vehicle_id = v_veic.vehicle_id,
                          vehicle_name = v_veic.name
      where  id = v_id;
      exit;
    end if;
  end loop;

  -- Frota registada e nenhum veiculo preso: alguem comprou o ultimo nos
  -- segundos em que esta pessoa escrevia o email. Desfaz-se tudo.
  if v_preso is null or v_preso = 0 then
    if exists (select 1 from listing_vehicles lx where lx.listing_id = a.id) then
      -- Nao se apaga: marca-se. Uma reserva perdida numa corrida e
      -- informacao — diz que houve procura para um dia que estava
      -- esgotado, e e isso que justifica dizer ao operador que precisa
      -- de mais um carro.
      update bookings set status = 'cancelled', cancelled_at = now(),
             cancel_reason = 'O ultimo veiculo foi vendido enquanto o '
                             'cliente preenchia o formulario.',
             updated_at = now()
       where id = v_id;
      return jsonb_build_object('ok', false, 'code', 'justTaken',
        'error', 'Someone booked the last vehicle for that date while you '
                 'were filling this in. Pick another date.');
    end if;
  end if;

  return c || jsonb_build_object(
    'booking_id', v_id,
    'reference', v_ref,
    'payment_mode', v_modo,
    'amount_cents', round((c->>'price')::numeric * 100)::bigint,
    'vehicle_name', (select vehicle_name from bookings where id = v_id),
    'hold_minutes', pr.hold_minutes);
end $$;

revoke execute on function reservar(jsonb) from public, anon, authenticated;

-- ---------------------------------------------------------------------
-- O PAGAMENTO ENTROU
--
-- Chamada pelo webhook. Tem de ser IDEMPOTENTE: o Stripe repete os
-- eventos, e um evento repetido nao pode dar duas reservas, dois emails
-- nem dois veiculos presos. A deteccao e o stripe_session_id, que e
-- unico na tabela.
--
-- No modo 'later' nao entrou dinheiro nenhum: guardou-se o cartao. O
-- estado passa a 'confirmed' e nao a 'paid', e e a verdade — quem for
-- ao painel do Stripe ve uma reserva confirmada sem pagamento, nao uma
-- reserva paga que nao esta.
-- ---------------------------------------------------------------------
create or replace function confirmar_reserva(p jsonb)
returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  b      record;
  v_novo booking_status;
begin
  select * into b from bookings
  where  id = (p->>'booking_id')::uuid
  for    update;

  if b.id is null then
    return jsonb_build_object('ok', false, 'code', 'notFound');
  end if;

  -- Ja tratado. Responde ok para o Stripe parar de repetir.
  if b.status in ('confirmed', 'paid') then
    return jsonb_build_object('ok', true, 'repeated', true,
      'reference', b.reference, 'status', b.status);
  end if;

  -- UMA RESERVA CANCELADA NAO SE CONFIRMA
  --
  -- Isto faltava e era o pior buraco do ficheiro. Uma reserva pode ser
  -- cancelada ENTRE abrir o Stripe e o pagamento entrar: perdeu a
  -- corrida pelo ultimo veiculo, ou passou das duas horas e a
  -- limpar_marcas() fechou-a. O webhook chegava a seguir e punha-a a
  -- 'paid' — e ficava um cliente cobrado por um dia que nao esta preso
  -- para ele, sem nada no ecra a dizer que algo correu mal.
  --
  -- Agora recusa, e devolve o payment_intent: e com ele que se devolve o
  -- dinheiro. Quem trata disso e a Edge Function, que grita no registo.
  if b.status in ('cancelled', 'refunded') then
    return jsonb_build_object('ok', false, 'code', 'cancelled',
      'reference', b.reference, 'status', b.status,
      'cancel_reason', b.cancel_reason,
      'payment_intent', coalesce(nullif(p->>'payment_intent',''),
                                 b.stripe_payment_intent),
      'amount', b.price_total);
  end if;

  v_novo := case when b.payment_mode = 'later'
              then 'confirmed' else 'paid' end::booking_status;

  update bookings set
    status                   = v_novo,
    stripe_session_id        = coalesce(nullif(p->>'session_id',''), stripe_session_id),
    stripe_payment_intent    = coalesce(nullif(p->>'payment_intent',''), stripe_payment_intent),
    stripe_customer_id       = coalesce(nullif(p->>'customer',''), stripe_customer_id),
    stripe_payment_method_id = coalesce(nullif(p->>'payment_method',''), stripe_payment_method_id),
    stripe_setup_intent_id   = coalesce(nullif(p->>'setup_intent',''), stripe_setup_intent_id),
    customer_name            = coalesce(nullif(trim(p->>'name'),''), customer_name),
    customer_email           = coalesce(nullif(trim(lower(p->>'email')),''), customer_email),
    customer_phone           = coalesce(nullif(trim(p->>'phone'),''), customer_phone),
    charged_at               = case when v_novo = 'paid' then now() else charged_at end,
    updated_at               = now()
  where id = b.id;

  -- A marca do veiculo deixa de ter validade: passa a definitiva.
  update vehicle_days set hold_expires_at = null, updated_at = now()
  where  booking_id = b.id;

  return jsonb_build_object('ok', true, 'reference', b.reference,
    'status', v_novo, 'operator_id', b.operator_id,
    'operator_amount', b.operator_amount);
end $$;

revoke execute on function confirmar_reserva(jsonb) from public, anon, authenticated;

-- ---------------------------------------------------------------------
-- CANCELAR
--
-- Solta o veiculo e guarda a razao. Nao apaga a reserva: uma reserva
-- cancelada e informacao (quantas se cancelam, de quem, quando) e
-- apagar historico comercial para poupar uma linha e mau negocio.
--
-- Nao decide reembolsos. Quem cobra e o Stripe e quem devolve e o
-- Stripe; esta funcao guarda o estado e a Edge Function trata do
-- dinheiro. Se fizesse as duas coisas, um erro no Stripe deixava a base
-- a dizer uma coisa e o dinheiro a dizer outra.
-- ---------------------------------------------------------------------
create or replace function cancelar_reserva(p_booking uuid, p_razao text)
returns jsonb
language plpgsql security definer set search_path = public as $$
declare
  b record;
  v_admin boolean := exists (select 1 from admins a where a.user_id = auth.uid());
begin
  select * into b from bookings where id = p_booking for update;
  if b.id is null then
    raise exception 'Reserva nao encontrada.';
  end if;

  -- O admin, ou o operador do tour. Mais ninguem.
  if not v_admin and not exists (
       select 1 from operator_users ou
       where  ou.operator_id = b.operator_id and ou.user_id = auth.uid()) then
    raise exception 'Nao podes cancelar esta reserva.';
  end if;

  if coalesce(length(trim(p_razao)), 0) < 10 then
    raise exception 'Escreve a razao do cancelamento (pelo menos 10 letras).';
  end if;

  update bookings set status = 'cancelled', cancelled_at = now(),
                      cancel_reason = trim(p_razao), updated_at = now()
  where  id = b.id;

  -- LIBERTAR, E NAO APAGAR
  --
  -- A linha de vehicle_days nao e da reserva: e do dia. O operador pode
  -- ter escrito ali uma nota, e apagar a linha apagava-lhe a nota. Por
  -- isso solta-se a marca — o dia volta a 'open' e deixa de ter reserva —
  -- e a linha fica.
  --
  -- Para a veiculos_livres() isto e exatamente o mesmo: ela so olha para
  -- quem tem `status <> 'open'`.
  update vehicle_days
     set status = 'open', booking_id = null, hold_expires_at = null,
         updated_at = now()
   where booking_id = b.id;

  return jsonb_build_object('ok', true, 'reference', b.reference,
    'was', b.status, 'charged', b.charged_at is not null,
    'payment_intent', b.stripe_payment_intent,
    'amount', b.price_total);
end $$;

revoke execute on function cancelar_reserva(uuid, text) from public, anon;
grant  execute on function cancelar_reserva(uuid, text) to authenticated;

-- ---------------------------------------------------------------------
-- QUEM ESTA NA HORA DE COBRAR
--
-- A Edge Function do cron chama isto e cobra uma a uma. A regra de
-- esperar entre tentativas esta aqui e nao no codigo: um cron de hora a
-- hora queimava as tres tentativas em tres horas, e o cliente que teve
-- o cartao recusado por falta de saldo ao meio-dia pode ter saldo a
-- noite.
-- ---------------------------------------------------------------------
create or replace function reservas_a_cobrar()
returns table (
  booking_id uuid, reference text, amount_cents bigint, currency text,
  stripe_customer_id text, stripe_payment_method_id text,
  tour_title text, booking_date date, customer_email text, attempt integer)
language sql stable security definer set search_path = public as $$
  select b.id, b.reference, round(b.price_total * 100)::bigint, b.currency,
         b.stripe_customer_id, b.stripe_payment_method_id,
         b.tour_title, b.booking_date, b.customer_email,
         b.charge_attempts + 1
  from   bookings b, payment_rules pr
  where  pr.id = 1
    and  b.payment_mode = 'later'
    and  b.status = 'confirmed'
    and  b.charged_at is null
    and  b.charge_at <= now()
    and  b.charge_attempts < pr.max_charge_attempts
    and  b.stripe_customer_id is not null
    and  b.stripe_payment_method_id is not null
    and  (b.charge_attempts = 0
          or b.updated_at <= now() - make_interval(hours => pr.retry_interval_hours))
  order  by b.charge_at
  limit  50;
$$;

revoke execute on function reservas_a_cobrar() from public, anon, authenticated;

-- O registo de cada tentativa. Sem isto, "o cartao foi recusado" e uma
-- frase sem data nem motivo, e nao se sabe se se tentou uma vez ou tres.
create table if not exists charge_attempts (
  id         bigserial primary key,
  booking_id uuid not null references bookings(id) on delete cascade,
  attempt    integer not null,
  ok         boolean not null,
  code       text,
  message    text,
  created_at timestamptz not null default now()
);

create index if not exists ca_reserva_idx on charge_attempts(booking_id, created_at desc);

create or replace function registar_cobranca(p jsonb)
returns void
language plpgsql security definer set search_path = public as $$
declare
  v_id      uuid := (p->>'booking_id')::uuid;
  v_ok      boolean := coalesce((p->>'ok')::boolean, false);
  v_tent    integer := coalesce((p->>'attempt')::integer, 1);
  v_max     integer;
begin
  select max_charge_attempts into v_max from payment_rules where id = 1;

  insert into charge_attempts (booking_id, attempt, ok, code, message)
  values (v_id, v_tent, v_ok, nullif(p->>'code',''), nullif(p->>'message',''));

  if v_ok then
    update bookings set status = 'paid', charged_at = now(),
                        charge_attempts = v_tent,
                        stripe_payment_intent =
                          coalesce(nullif(p->>'payment_intent',''), stripe_payment_intent),
                        updated_at = now()
    where id = v_id;
  else
    -- Esgotadas as tentativas, a reserva cai e o dia volta a ficar a
    -- venda. Guardar uma reserva confirmada que nunca foi paga era pior:
    -- o operador ficava com o dia preso por um cartao que nao paga.
    update bookings set charge_attempts = v_tent, updated_at = now(),
      status = case when v_tent >= v_max then 'cancelled' else status end,
      cancelled_at = case when v_tent >= v_max then now() end,
      cancel_reason = case when v_tent >= v_max
        then 'O cartao foi recusado em ' || v_tent || ' tentativas.' end
    where id = v_id;

    -- Esgotadas as tentativas, o dia volta a ficar a venda. Solta-se a
    -- marca em vez de apagar a linha: ver a nota na cancelar_reserva().
    if v_tent >= v_max then
      update vehicle_days
         set status = 'open', booking_id = null, hold_expires_at = null,
             updated_at = now()
       where booking_id = v_id;
    end if;
  end if;
end $$;

revoke execute on function registar_cobranca(jsonb) from public, anon, authenticated;

-- ---------------------------------------------------------------------
-- SOLTAR AS MARCAS CADUCADAS
--
-- A veiculos_livres() ja ignora uma marca caducada, por isso o dia
-- aparece livre sem isto. Esta funcao e a limpeza: apaga as linhas que
-- nao servem e cancela as reservas que ficaram por pagar, para a fila do
-- admin nao enche de reservas mortas.
-- ---------------------------------------------------------------------
create or replace function limpar_marcas()
returns integer
language plpgsql security definer set search_path = public as $$
declare n integer;
begin
  update bookings set status = 'cancelled', cancelled_at = now(),
         cancel_reason = 'Nao foi paga: o cliente saiu do pagamento.',
         updated_at = now()
  where  status = 'pending'
    and  created_at < now() - interval '2 hours';

  -- As marcas caducadas soltam-se, nao se apagam: a linha pode ter uma
  -- nota do operador. A veiculos_livres() ja ignorava uma marca caducada,
  -- por isso o dia ja aparecia livre; isto e a arrumacao.
  update vehicle_days
     set status = 'open', booking_id = null, hold_expires_at = null,
         updated_at = now()
   where hold_expires_at is not null and hold_expires_at <= now();
  get diagnostics n = row_count;
  return n;
end $$;

revoke execute on function limpar_marcas() from public, anon, authenticated;

-- ---------------------------------------------------------------------
-- QUEM VE AS RESERVAS
--
-- O publico nao ve nenhuma. O operador ve as DELE, e nao ve a comissao
-- nem o que a plataforma leva — isso vai numa funcao propria, para se
-- poder mostrar o que ele recebe sem lhe abrir a tabela toda.
-- ---------------------------------------------------------------------
alter table bookings        enable row level security;
alter table charge_attempts enable row level security;
alter table payment_rules   enable row level security;

do $$ begin
  create policy admin_ve_reservas on bookings for select to authenticated
    using (exists (select 1 from admins a where a.user_id = auth.uid()));
exception when duplicate_object then null; end $$;

do $$ begin
  create policy admin_muda_reservas on bookings for update to authenticated
    using (exists (select 1 from admins a where a.user_id = auth.uid()));
exception when duplicate_object then null; end $$;

do $$ begin
  create policy operador_ve_as_suas on bookings for select to authenticated
    using (exists (select 1 from operator_users ou
                   where ou.operator_id = bookings.operator_id
                     and ou.user_id = auth.uid()));
exception when duplicate_object then null; end $$;

do $$ begin
  create policy admin_ve_cobrancas on charge_attempts for select to authenticated
    using (exists (select 1 from admins a where a.user_id = auth.uid()));
exception when duplicate_object then null; end $$;

do $$ begin
  create policy admin_ve_regras on payment_rules for select to authenticated
    using (exists (select 1 from admins a where a.user_id = auth.uid()));
exception when duplicate_object then null; end $$;

do $$ begin
  create policy admin_muda_regras on payment_rules for update to authenticated
    using (exists (select 1 from admins a where a.user_id = auth.uid()));
exception when duplicate_object then null; end $$;

-- ---------------------------------------------------------------------
-- A AGENDA DO OPERADOR
--
-- O que ele precisa de ver para trabalhar: quem vem, quando, quantos, em
-- que carro, e quanto e que RECEBE. Nao o total que o cliente pagou nem
-- a taxa de comissao — isso e uma conversa, nao uma coluna.
-- ---------------------------------------------------------------------
create or replace function agenda_do_operador(p_de date, p_ate date)
returns table (
  reference text, tour_title text, booking_date date, start_time time,
  pax integer, vehicle_name text, customer_name text, customer_phone text,
  pickup text, notes text, you_receive numeric, status booking_status,
  paid_out boolean)
language sql stable security definer set search_path = public as $$
  select b.reference, b.tour_title, b.booking_date, b.start_time,
         b.pax, b.vehicle_name, b.customer_name, b.customer_phone,
         b.pickup, b.notes, b.operator_amount, b.status,
         b.payout_at is not null
  from   bookings b
  where  b.status in ('confirmed', 'paid')
    and  b.booking_date between p_de and p_ate
    and  exists (select 1 from operator_users ou
                 where ou.operator_id = b.operator_id
                   and ou.user_id = auth.uid())
  order  by b.booking_date, b.start_time nulls last;
$$;

revoke execute on function agenda_do_operador(date, date) from public, anon;
grant  execute on function agenda_do_operador(date, date) to authenticated;

-- O que esta a pagar a cada operador. A fila de pagamentos do Ricardo.
create or replace function a_pagar()
returns table (
  operator_id uuid, operator_name text, operator_email text,
  reservas integer, total numeric, mais_antiga date)
language sql stable security definer set search_path = public as $$
  select o.id, o.name, o.email, count(*)::integer,
         round(sum(b.operator_amount), 2), min(b.booking_date)
  from   bookings b
  join   operators o on o.id = b.operator_id
  where  b.status = 'paid' and b.payout_at is null
    and  b.booking_date <= current_date
    and  exists (select 1 from admins a where a.user_id = auth.uid())
  group  by o.id, o.name, o.email
  order  by min(b.booking_date);
$$;

revoke execute on function a_pagar() from public, anon;
grant  execute on function a_pagar() to authenticated;

create or replace function marcar_pago(p_operator uuid, p_nota text)
returns integer
language plpgsql security definer set search_path = public as $$
declare n integer;
begin
  if not exists (select 1 from admins a where a.user_id = auth.uid()) then
    raise exception 'So o administrador marca pagamentos.';
  end if;
  update bookings set payout_at = now(), payout_note = nullif(trim(p_nota),''),
                      updated_at = now()
  where  operator_id = p_operator and status = 'paid' and payout_at is null
    and  booking_date <= current_date;
  get diagnostics n = row_count;
  return n;
end $$;

revoke execute on function marcar_pago(uuid, text) from public, anon;
grant  execute on function marcar_pago(uuid, text) to authenticated;

-- =====================================================================
-- A CADEIA DA AVALIACAO, GENERALIZADA
--
-- A 013 construiu a cadeia toda em volta da enquiries, porque em
-- outubro um pedido era a unica maneira de alguem viajar. Com reservas
-- pagas ha duas, e a cadeia tem de aceitar as duas sem perder o que a
-- torna solida: uma avaliacao continua a precisar de prova de viagem e
-- de um token de uso unico.
--
-- Nao se prega uma coluna a mais: generaliza-se a ORIGEM do convite.
-- Um convite nasce de um pedido OU de uma reserva, nunca dos dois e
-- nunca de nenhum, e isso e uma restricao da base e nao uma convencao.
--
-- As assinaturas de convite() e deixar_avaliacao() nao mudam. O
-- /review/?t=... que ja esta no site continua a funcionar sem saber
-- que isto mudou por baixo.
-- =====================================================================
alter table review_invites alter column enquiry_id drop not null;
alter table review_invites
  add column if not exists booking_id uuid references bookings(id) on delete cascade;

alter table reviews alter column enquiry_id drop not null;
alter table reviews
  add column if not exists booking_id uuid references bookings(id) on delete cascade;

do $$ begin
  create unique index review_invites_reserva_idx
    on review_invites(booking_id) where booking_id is not null;
exception when duplicate_table then null; end $$;

do $$ begin
  create unique index reviews_reserva_idx
    on reviews(booking_id) where booking_id is not null;
exception when duplicate_table then null; end $$;

do $$ begin
  alter table review_invites add constraint convite_tem_uma_origem
    check ((enquiry_id is null) <> (booking_id is null));
exception when duplicate_object then null; end $$;

do $$ begin
  alter table reviews add constraint avaliacao_tem_uma_origem
    check ((enquiry_id is null) <> (booking_id is null));
exception when duplicate_object then null; end $$;

-- ---------------------------------------------------------------------
-- A ORIGEM DE UM CONVITE, NUMA SO FUNCAO
--
-- Quem viajou, quando, e com que email — venha de um pedido ou de uma
-- reserva. Existe para a convite() e a deixar_avaliacao() nao terem
-- cada uma a sua copia do `coalesce`: a regra do nome ("vem da viagem,
-- nunca do formulario") e o coracao da integridade das avaliacoes e nao
-- pode estar escrita em dois sitios.
-- ---------------------------------------------------------------------
create or replace function quem_viajou(p_token uuid)
returns table (first_name text, email text, travelled_on date)
language sql stable security definer set search_path = public as $$
  select
    split_part(btrim(coalesce(e.name, b.customer_name, '')), ' ', 1),
    coalesce(e.email, b.customer_email),
    coalesce(e.travelled_on, b.booking_date)
  from   review_invites i
  left   join enquiries e on e.id = i.enquiry_id
  left   join bookings  b on b.id = i.booking_id
  where  i.token = p_token;
$$;

revoke execute on function quem_viajou(uuid) from public, anon, authenticated;

create or replace function convite(p_token uuid)
returns table (valido boolean, motivo text, tour text, slug text,
               travelled_on date, first_name text)
language sql stable security definer set search_path = public as $$
  select
    (i.used_at is null and i.expires_at > now()),
    case when i.used_at is not null then 'used'
         when i.expires_at <= now() then 'expired'
         else null end,
    coalesce(lv.payload->>'title', l.slug),
    l.slug,
    q.travelled_on,
    q.first_name
  from review_invites i
  join listings l on l.id = i.listing_id
  cross join lateral quem_viajou(i.token) q
  -- Pela mesma razao da 010: uma funcao definer que le atraves de uma
  -- vista invoker devolve zero linhas a quem nao assinou, sem dar erro.
  left join (select distinct on (v.listing_id) v.listing_id, v.payload
             from listing_versions v where v.status = 'approved'
             order by v.listing_id, v.version desc) lv on lv.listing_id = l.id
  where i.token = p_token;
$$;

revoke execute on function convite(uuid) from public;
grant  execute on function convite(uuid) to anon, authenticated;

create or replace function deixar_avaliacao(p_token uuid, p jsonb)
returns uuid
language plpgsql security definer set search_path = public as $$
declare
  i review_invites;
  q record;
  v_id uuid;
  v_nota smallint := nullif(btrim(coalesce(p->>'rating', '')), '')::smallint;
begin
  -- `for update` segura a linha: e isto que faz duas submissoes
  -- simultaneas darem uma avaliacao e nao duas.
  select * into i from review_invites where token = p_token for update;
  if not found then
    raise exception 'That review link is not valid.';
  end if;
  if i.used_at is not null then
    raise exception 'That review has already been left. Thank you.';
  end if;
  if i.expires_at <= now() then
    raise exception 'That review link has expired.';
  end if;

  if v_nota is null or v_nota < 1 or v_nota > 5 then
    raise exception 'Give the day a rating from 1 to 5.';
  end if;

  select * into q from quem_viajou(p_token);

  insert into reviews (
    listing_id, operator_id, enquiry_id, booking_id, rating,
    r_driver, r_vehicle, r_value, r_organising,
    title, body, author_name, author_country, travelled_on)
  values (
    i.listing_id, i.operator_id, i.enquiry_id, i.booking_id, v_nota,
    nullif(btrim(coalesce(p->>'r_driver', '')), '')::smallint,
    nullif(btrim(coalesce(p->>'r_vehicle', '')), '')::smallint,
    nullif(btrim(coalesce(p->>'r_value', '')), '')::smallint,
    nullif(btrim(coalesce(p->>'r_organising', '')), '')::smallint,
    left(btrim(p->>'title'), 140),
    left(btrim(p->>'body'), 4000),
    -- O nome vem da viagem e nao do formulario: quem avalia e quem
    -- viajou, e deixar escolher o nome e deixar assinar como outra
    -- pessoa. So o primeiro nome vai para a pagina.
    q.first_name,
    left(btrim(p->>'author_country'), 80),
    q.travelled_on)
  returning id into v_id;

  update review_invites set used_at = now() where token = p_token;
  if i.enquiry_id is not null then
    update enquiries set status = 'closed' where id = i.enquiry_id;
  end if;

  return v_id;
end;
$$;

revoke execute on function deixar_avaliacao(uuid, jsonb) from public;
grant  execute on function deixar_avaliacao(uuid, jsonb) to anon, authenticated;

-- ---------------------------------------------------------------------
-- O CONVITE QUE NASCE DE UMA RESERVA
--
-- A 013 obriga alguem a marcar o pedido como "viajou" a mao, e isso fazia
-- sentido quando um pedido era so uma mensagem: ninguem sabia se a
-- viagem tinha acontecido. Uma reserva PAGA com data passada ja viajou —
-- a prova e o pagamento.
--
-- Continua a nao haver formulario aberto: o convite tem token, o token
-- gasta-se, e o nome vem da reserva.
-- ---------------------------------------------------------------------
create or replace function convidar_por_reserva(p_booking uuid)
returns uuid
language plpgsql security definer set search_path = public as $$
declare
  b  record;
  tk uuid;
begin
  if not exists (select 1 from admins a where a.user_id = auth.uid()) then
    raise exception 'So o administrador convida.';
  end if;

  select * into b from bookings where id = p_booking;
  if b.id is null then raise exception 'Reserva nao encontrada.'; end if;
  if b.status <> 'paid' then
    raise exception 'A reserva ainda nao esta paga.';
  end if;
  if b.booking_date > current_date then
    raise exception 'O tour ainda nao aconteceu.';
  end if;
  if b.customer_email is null then
    raise exception 'A reserva nao tem email do cliente.';
  end if;

  select i.token into tk from review_invites i where i.booking_id = b.id;
  if tk is not null then return tk; end if;

  insert into review_invites (booking_id, listing_id, operator_id)
  values (b.id, b.listing_id, b.operator_id)
  returning token into tk;

  return tk;
end $$;

revoke execute on function convidar_por_reserva(uuid) from public, anon;
grant  execute on function convidar_por_reserva(uuid) to authenticated;

-- As reservas que ja viajaram e ainda nao foram convidadas. A fila do
-- Ricardo deixa de ser "marca que viajou e depois convida": passa a ser
-- uma lista que ele percorre, ou que um cron percorre por ele.
create or replace function reservas_a_convidar()
returns table (booking_id uuid, reference text, tour_title text,
               booking_date date, customer_name text, customer_email text)
language sql stable security definer set search_path = public as $$
  select b.id, b.reference, b.tour_title, b.booking_date,
         b.customer_name, b.customer_email
  from   bookings b
  where  b.status = 'paid'
    and  b.booking_date < current_date
    and  b.customer_email is not null
    and  not exists (select 1 from review_invites i where i.booking_id = b.id)
    and  exists (select 1 from admins a where a.user_id = auth.uid())
  order  by b.booking_date;
$$;

revoke execute on function reservas_a_convidar() from public, anon;
grant  execute on function reservas_a_convidar() to authenticated;

-- ---------------------------------------------------------------------
-- A promover_admin() NAO E PARA SER CHAMADA
--
-- E uma funcao de gatilho: devolve `trigger`. Estava executavel pelo
-- anon e pelo authenticated — o que nao da acesso a nada (o Postgres
-- recusa chamar uma funcao de gatilho diretamente) mas aparece na API
-- exposta e no linter de seguranca do Supabase. Fecha-se, para a lista
-- de avisos so ter o que e deliberado e um aviso novo se notar.
--
-- O `if exists` e porque a funcao nasceu numa migracao anterior e este
-- ficheiro tem de poder correr numa base onde ela ainda nao exista.
-- ---------------------------------------------------------------------
do $$ begin
  if exists (select 1 from pg_proc p join pg_namespace n on n.oid = p.pronamespace
             where n.nspname = 'public' and p.proname = 'promover_admin') then
    revoke execute on function promover_admin() from public, anon, authenticated;
  end if;
end $$;
