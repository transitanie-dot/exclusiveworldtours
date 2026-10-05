-- =====================================================================
-- EPOCAS: o calendario deixa de ser pintado a dia
--
-- O modelo ate aqui era uma linha por dia. A disponibilidade de um
-- operador nao e isso: e "segunda a sexta, de Junho a Setembro, as 09:00
-- e as 14:00" — uma frase. Fechar os domingos de uma epoca eram noventa
-- cliques e treze paginas de calendario.
--
-- O modelo novo e o da Viator, e esta certo: ABERTO POR REGRA, FECHADO
-- POR EXCECAO.
--
--   listing_seasons   um intervalo de datas x dias da semana
--   season_times      as horas de partida DESSA epoca
--   availability      as excecoes (ja existia): fechar um dia solto
--
-- O QUE ISTO MUDA NA PRATICA
-- --------------------------
-- 1. As horas de partida passam a pertencer a EPOCA e nao ao anuncio.
--    Ninguem faz a mesma hora em Janeiro e em Agosto, e o modelo antigo
--    obrigava a isso.
-- 2. Uma epoca sem data de fim ROLA PARA A FRENTE, 400 dias. E a unica
--    defesa contra o modo de falha mais comum de um marketplace: o
--    anuncio cuja disponibilidade se esgota em silencio e ninguem da por
--    isso ate as vendas pararem.
-- 3. Um anuncio sem epocas nenhumas continua a funcionar como antes.
--    Nao se parte o que esta no ar: a 020 migra as listing_times para
--    uma epoca aberta e o comportamento fica igual.
--
-- O QUE NAO MUDA
-- --------------
-- As assinaturas da dias_abertos(), partidas_no_dia() e cotar(). As
-- paginas do site chamam-nas na mesma e nao sabem que isto aconteceu.
-- =====================================================================

-- ---------------------------------------------------------------------
-- O MODO DO HORARIO
--
-- Nem todos os produtos tem hora de partida. Um "chauffeur for the day"
-- tem uma JANELA: das 8 as 18, e combina-se a hora com o cliente. O
-- modelo antigo obrigava a inventar uma hora de partida, e a inventada
-- aparecia na pagina como se fosse verdade.
--
-- Ao contrario da Viator, isto NAO e uma escolha irreversivel. Mudar de
-- modo e um update; o que estiver configurado no outro modo fica
-- guardado e volta a valer se se mudar de ideias. Uma decisao tomada no
-- dia 1, com a menor informacao que a pessoa vai ter, nao pode ser
-- definitiva.
-- ---------------------------------------------------------------------
do $$ begin
  create type schedule_mode as enum ('departures', 'opening_hours');
exception when duplicate_object then null;
end $$;

alter table listings
  add column if not exists schedule_mode schedule_mode not null default 'departures';

comment on column listings.schedule_mode is
  'departures: horas fixas (a maioria dos tours). opening_hours: uma '
  'janela, e a hora combina-se com o cliente (motorista a disposicao). '
  'Muda-se a qualquer momento, ao contrario da Viator.';

-- ---------------------------------------------------------------------
-- BEBES AO COLO
--
-- A Viator tem faixas etarias com PRECO. Aqui o preco e do veiculo e
-- quatro pessoas pagam o mesmo que uma — e esse e o argumento central do
-- site, nao um detalhe. Por isso fica so a parte util: um bebe ao colo
-- nao ocupa um lugar, e portanto nao conta para o escalao nem para a
-- lotacao do carro.
--
-- Fica a zero por omissao, que e o comportamento de hoje: toda a gente
-- conta. Um operador que leve bebes ao colo poe a idade maxima.
-- ---------------------------------------------------------------------
alter table listings
  add column if not exists lap_infant_max_age smallint
    check (lap_infant_max_age is null
           or (lap_infant_max_age >= 0 and lap_infant_max_age <= 4));

comment on column listings.lap_infant_max_age is
  'Idade ate a qual uma crianca viaja ao colo e NAO ocupa lugar. Nulo = '
  'toda a gente ocupa lugar. Nunca mexe no preco: o preco e do veiculo.';

-- ---------------------------------------------------------------------
-- AS EPOCAS
-- ---------------------------------------------------------------------
create table if not exists listing_seasons (
  id          uuid primary key default gen_random_uuid(),
  listing_id  uuid not null references listings(id) on delete cascade,

  starts_on   date not null,
  -- Nulo = rola para a frente. Ver a nota no topo: e isto que impede um
  -- anuncio de se esgotar em silencio.
  ends_on     date,

  -- Os dias da semana em ISO: 1 = segunda, 7 = domingo. Um array e nao
  -- sete colunas booleanas porque a pergunta que se faz e sempre
  -- "este dia esta ca dentro?", e `= any(weekdays)` responde-a.
  weekdays    smallint[] not null,

  -- So no modo opening_hours. A janela em que o motorista esta
  -- disponivel; a hora exata combina-se depois.
  opens_at    time,
  closes_at   time,

  note        text,
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now(),

  constraint epoca_ordem check (ends_on is null or ends_on >= starts_on),
  constraint epoca_tem_dias check (
    array_length(weekdays, 1) between 1 and 7
    and weekdays <@ array[1,2,3,4,5,6,7]::smallint[]),
  constraint janela_ordem check (
    opens_at is null or closes_at is null or closes_at > opens_at)
);

create index if not exists epocas_anuncio_idx
  on listing_seasons(listing_id, starts_on);

comment on table listing_seasons is
  'Uma linha por epoca. Fora de qualquer epoca, o tour NAO corre: aberto '
  'por regra, e a regra e esta.';

create table if not exists season_times (
  season_id  uuid not null references listing_seasons(id) on delete cascade,
  starts_at  time not null,
  primary key (season_id, starts_at)
);

-- ---------------------------------------------------------------------
-- QUEM MEXE
-- ---------------------------------------------------------------------
alter table listing_seasons enable row level security;
alter table season_times    enable row level security;

do $$ begin
  create policy epocas_le on listing_seasons for select to authenticated
    using (is_admin() or listing_id in (
             select l.id from listings l
             where l.operator_id in (select meus_operadores())));
exception when duplicate_object then null; end $$;

do $$ begin
  create policy epocas_mexe on listing_seasons for all to authenticated
    using (is_admin() or listing_id in (
             select l.id from listings l
             where l.operator_id in (select meus_operadores())))
    with check (is_admin() or listing_id in (
             select l.id from listings l
             where l.operator_id in (select meus_operadores())));
exception when duplicate_object then null; end $$;

do $$ begin
  create policy horas_le on season_times for select to authenticated
    using (is_admin() or season_id in (
             select s.id from listing_seasons s
             join listings l on l.id = s.listing_id
             where l.operator_id in (select meus_operadores())));
exception when duplicate_object then null; end $$;

do $$ begin
  create policy horas_mexe on season_times for all to authenticated
    using (is_admin() or season_id in (
             select s.id from listing_seasons s
             join listings l on l.id = s.listing_id
             where l.operator_id in (select meus_operadores())))
    with check (is_admin() or season_id in (
             select s.id from listing_seasons s
             join listings l on l.id = s.listing_id
             where l.operator_id in (select meus_operadores())));
exception when duplicate_object then null; end $$;

-- ---------------------------------------------------------------------
-- MIGRAR O QUE JA EXISTE
--
-- Um anuncio com horas registadas na listing_times ganha uma epoca
-- aberta, todos os dias da semana, com essas horas. O comportamento
-- fica EXATAMENTE igual ao de hoje — e e por isso que esta migracao
-- pode correr numa base com operadores a vender.
--
-- A listing_times nao se apaga. Fica como estava, sem ninguem a ler, ate
-- se confirmar que as epocas correm bem. Apagar a fonte no mesmo dia em
-- que se muda o leitor e como cortar o ramo onde se esta sentado.
-- ---------------------------------------------------------------------
do $$
declare a record; v_id uuid;
begin
  for a in
    select distinct l.id
    from   listings l
    join   listing_times t on t.listing_id = l.id and t.active
    where  not exists (select 1 from listing_seasons s where s.listing_id = l.id)
  loop
    insert into listing_seasons (listing_id, starts_on, ends_on, weekdays, note)
    values (a.id, current_date, null, array[1,2,3,4,5,6,7]::smallint[],
            'Criada automaticamente a partir das horas que o anuncio ja tinha.')
    returning id into v_id;

    insert into season_times (season_id, starts_at)
    select v_id, t.starts_at from listing_times t
    where  t.listing_id = a.id and t.active
    on conflict do nothing;
  end loop;
end $$;

-- ---------------------------------------------------------------------
-- RESOLVER AS REGRAS
--
-- A funcao que responde "este dia esta coberto por alguma epoca?". Tudo
-- o resto — dias_abertos(), partidas_no_dia(), cotar() — passa por aqui.
-- Uma copia so da regra.
-- ---------------------------------------------------------------------
create or replace function epoca_do_dia(p_listing uuid, p_day date)
returns table (season_id uuid, opens_at time, closes_at time)
language sql stable security definer set search_path = public as $$
  select s.id, s.opens_at, s.closes_at
  from   listing_seasons s
  where  s.listing_id = p_listing
    and  p_day >= s.starts_on
    -- Sem data de fim: vale ate 400 dias para a frente, que e o limite
    -- do calendario. Nao e "para sempre" porque um calendario infinito
    -- nao se mostra nem se verifica.
    and  (case when s.ends_on is null
                 then p_day <= current_date + 400
                 else p_day <= s.ends_on end)
    and  extract(isodow from p_day)::smallint = any(s.weekdays)
  -- Se duas epocas cobrirem o mesmo dia, ganha a que comeca mais tarde:
  -- e a que foi escrita a pensar nesse periodo. Nao se recusa a
  -- sobreposicao — recusa-la obrigava o operador a partir epocas a mao
  -- so para acrescentar uma semana de Natal.
  order  by s.starts_on desc, s.created_at desc
  limit  1;
$$;

revoke execute on function epoca_do_dia(uuid, date) from public, anon;
grant  execute on function epoca_do_dia(uuid, date) to authenticated;

-- ---------------------------------------------------------------------
-- AS PARTIDAS, AGORA DA EPOCA
--
-- Mesma assinatura de sempre. Um anuncio sem epocas cai na listing_times
-- como antes — o `union all` com a condicao `not exists` e isso: nao ha
-- dois caminhos a decidir, ha um caminho e uma alternativa para quem
-- ainda nao migrou.
-- ---------------------------------------------------------------------
create or replace function partidas_possiveis(p_listing uuid, p_day date)
returns table (starts_at time)
language sql stable security definer set search_path = public as $$
  -- Pelas epocas.
  select st.starts_at
  from   epoca_do_dia(p_listing, p_day) e
  join   season_times st on st.season_id = e.season_id
  join   listings l on l.id = p_listing
  where  ((p_day + st.starts_at) at time zone l.timezone)
         >= now() + make_interval(hours => l.lead_time_hours)

  union all

  -- Pelo modelo antigo, so para quem ainda nao tem epocas nenhumas.
  select t.starts_at
  from   listing_times t
  join   listings l on l.id = t.listing_id
  where  t.listing_id = p_listing
    and  t.active
    and  not exists (select 1 from listing_seasons s
                     where s.listing_id = p_listing)
    and  ((p_day + t.starts_at) at time zone l.timezone)
         >= now() + make_interval(hours => l.lead_time_hours)

  order  by 1;
$$;

revoke execute on function partidas_possiveis(uuid, date) from public, anon;
grant  execute on function partidas_possiveis(uuid, date) to authenticated;

-- ---------------------------------------------------------------------
-- A JANELA, para o modo opening_hours
--
-- Devolve a janela do dia em vez de uma lista de horas. A pagina mostra
-- "das 08:00 as 18:00, combinamos a hora consigo" em vez de inventar uma
-- partida que ninguem prometeu.
-- ---------------------------------------------------------------------
create or replace function janela_no_dia(p_slug text, p_day date)
returns table (opens_at time, closes_at time)
language sql stable security definer set search_path = public as $$
  select e.opens_at, e.closes_at
  from   listings l
  join   operators o on o.id = l.operator_id,
         lateral epoca_do_dia(l.id, p_day) e
  where  l.slug = p_slug and l.status = 'live' and o.status = 'approved'
    and  l.schedule_mode = 'opening_hours'
    and  e.opens_at is not null
    -- A janela so vale se ainda sobrar tempo depois do aviso minimo: uma
    -- janela que fecha antes de o lead time acabar nao e uma janela.
    and  ((p_day + e.closes_at) at time zone l.timezone)
         >= now() + make_interval(hours => l.lead_time_hours);
$$;

revoke execute on function janela_no_dia(text, date) from public;
grant  execute on function janela_no_dia(text, date) to anon, authenticated;

-- ---------------------------------------------------------------------
-- dias_abertos(), outra vez — agora resolvida das epocas
--
-- Mesma assinatura, mesmo tipo de retorno. Um dia aparece se:
--   * uma epoca o cobre (ou, sem epocas, o lead time o permite);
--   * no modo departures, ainda sobra uma partida possivel;
--   * o anuncio nao o fechou (a excecao);
--   * o operador nao esta de ferias;
--   * ha um veiculo livre, se houver frota registada.
-- ---------------------------------------------------------------------
create or replace function dias_abertos(p_slug text, p_de date, p_ate date)
returns table (day date, price numeric)
language sql stable security definer set search_path = public as $$
  with anuncio as (
    select l.id, l.operator_id, l.lead_time_hours, l.schedule_mode,
           exists (select 1 from listing_vehicles lv where lv.listing_id = l.id)
             as tem_frota,
           exists (select 1 from listing_seasons s where s.listing_id = l.id)
             as tem_epocas
    from   listings l
    join   operators o on o.id = l.operator_id
    where  l.slug = p_slug and l.status = 'live' and o.status = 'approved'
  ),
  -- Sem epocas, a regra antiga: o primeiro dia que o lead time permite,
  -- arredondado para cima ao dia inteiro.
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
         generate_series(p_de, least(p_ate, (current_date + 400)),
                         interval '1 day') as d
  )
  select dias.dia,
         (select a.price_override from availability a
           where a.listing_id = dias.id and a.day = dias.dia)
  from   dias
  where  (
           case when dias.tem_epocas
             then exists (select 1 from epoca_do_dia(dias.id, dias.dia))
                  and (dias.schedule_mode = 'opening_hours'
                       or exists (select 1 from partidas_possiveis(dias.id, dias.dia)))
             else dias.dia >= dias.primeiro
           end
         )
    and  not exists (
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

revoke execute on function dias_abertos(text, date, date) from public;
grant  execute on function dias_abertos(text, date, date) to anon, authenticated;

-- ---------------------------------------------------------------------
-- PROMOCOES, COM DUAS JANELAS
--
-- A ideia e da Viator e e a parte do modelo deles que mais falta faz:
-- um desconto tem DUAS janelas independentes.
--
--   book_from / book_until      quando a RESERVA tem de ser feita
--   travel_from / travel_until  quando a VIAGEM tem de acontecer
--
-- "Reserva ate sexta, viaja em qualquer altura do Verao" e uma frase
-- normal num negocio de turismo, e a maioria dos sistemas so sabe
-- exprimir uma das duas datas.
--
-- O desconto sai do que a PLATAFORMA leva, nao do operador, a nao ser
-- que o operador seja o dono da promocao. E por isso que a tabela tem
-- `quem_paga`: uma campanha nossa nao pode cortar a margem dele sem ele
-- saber.
-- ---------------------------------------------------------------------
do $$ begin
  create type promo_kind as enum ('percent', 'amount');
exception when duplicate_object then null; end $$;

do $$ begin
  create type promo_payer as enum ('platform', 'operator');
exception when duplicate_object then null; end $$;

create table if not exists promotions (
  id           uuid primary key default gen_random_uuid(),
  operator_id  uuid not null references operators(id) on delete cascade,
  -- Nulo = todos os anuncios desse operador.
  listing_id   uuid references listings(id) on delete cascade,

  label        text not null,
  kind         promo_kind not null,
  value        numeric(10,2) not null check (value > 0),
  quem_paga    promo_payer not null default 'operator',

  book_from    date,
  book_until   date,
  travel_from  date,
  travel_until date,

  active       boolean not null default true,
  created_at   timestamptz not null default now(),

  constraint promo_janela_reserva check (
    book_from is null or book_until is null or book_until >= book_from),
  constraint promo_janela_viagem check (
    travel_from is null or travel_until is null or travel_until >= travel_from),
  -- Uma percentagem acima de 90 nao e uma promocao, e um erro de dedo.
  constraint promo_valor_sensato check (
    kind <> 'percent' or value <= 90)
);

create index if not exists promo_operador_idx on promotions(operator_id)
  where active;

comment on column promotions.quem_paga is
  'operator: sai da margem do operador. platform: sai da nossa comissao. '
  'Uma campanha nossa nao corta a margem dele sem ele saber.';

alter table promotions enable row level security;

do $$ begin
  create policy promo_le on promotions for select to authenticated
    using (is_admin() or operator_id in (select meus_operadores()));
exception when duplicate_object then null; end $$;

do $$ begin
  create policy promo_mexe on promotions for all to authenticated
    using (is_admin() or operator_id in (select meus_operadores()))
    with check (is_admin() or operator_id in (select meus_operadores()));
exception when duplicate_object then null; end $$;

-- A promocao que se aplica a este anuncio, nesta data de viagem, hoje.
-- Devolve a melhor para o cliente; se duas servirem, ganha a que desconta
-- mais. Nao se somam: descontos que se empilham sao a forma mais rapida
-- de vender abaixo do custo.
create or replace function promocao_para(p_listing uuid, p_dia date)
returns table (id uuid, label text, kind promo_kind, value numeric,
               quem_paga promo_payer, desconto numeric)
language sql stable security definer set search_path = public as $$
  select p.id, p.label, p.kind, p.value, p.quem_paga,
         case when p.kind = 'percent' then p.value else null end
  from   promotions p
  join   listings l on l.id = p_listing
  where  p.active
    and  p.operator_id = l.operator_id
    and  (p.listing_id is null or p.listing_id = p_listing)
    and  (p.book_from    is null or current_date >= p.book_from)
    and  (p.book_until   is null or current_date <= p.book_until)
    and  (p.travel_from  is null or p_dia >= p.travel_from)
    and  (p.travel_until is null or p_dia <= p.travel_until)
  order  by p.kind, p.value desc
  limit  1;
$$;

revoke execute on function promocao_para(uuid, date) from public;
grant  execute on function promocao_para(uuid, date) to anon, authenticated;

-- ---------------------------------------------------------------------
-- O NAO-COMPARECIMENTO
--
-- A Viator tem uma ferramenta propria para isto e diz que ganha 73% das
-- disputas de cartao com ela. A razao e simples: o que ganha uma disputa
-- nao e a palavra do operador, e um registo FEITO NO DIA, com hora, com
-- quanto tempo se esperou e com o que se tentou.
--
-- Por isso esta funcao exige as tres coisas e nao aceita um registo
-- feito antes do tour. Um registo escrito duas semanas depois, de
-- memoria, nao vale nada num banco.
-- ---------------------------------------------------------------------
alter table bookings
  add column if not exists no_show_at    timestamptz,
  add column if not exists no_show_by    uuid references auth.users(id),
  add column if not exists no_show_wait  integer,
  add column if not exists no_show_note  text;

comment on column bookings.no_show_wait is
  'Minutos que o motorista esperou. E o numero que um banco pergunta.';

create or replace function marcar_falta(p_booking uuid, p_esperou integer,
                                        p_nota text)
returns jsonb
language plpgsql security definer set search_path = public as $$
declare b record;
begin
  select * into b from bookings where id = p_booking for update;
  if b.id is null then raise exception 'Reserva nao encontrada.'; end if;

  if not is_admin() and not exists (
       select 1 from operator_users ou
       where  ou.operator_id = b.operator_id and ou.user_id = auth.uid()) then
    raise exception 'Nao podes registar uma falta nesta reserva.';
  end if;

  if b.booking_date > current_date then
    raise exception 'O tour ainda nao aconteceu.';
  end if;
  if b.status not in ('paid', 'confirmed') then
    raise exception 'So uma reserva confirmada ou paga pode ter uma falta.';
  end if;
  if b.no_show_at is not null then
    raise exception 'Esta falta ja foi registada em %.',
      to_char(b.no_show_at, 'YYYY-MM-DD HH24:MI');
  end if;
  if coalesce(p_esperou, -1) < 0 or p_esperou > 480 then
    raise exception 'Quantos minutos esperaste? (0 a 480)';
  end if;
  -- O texto e a prova. Vinte letras nao e burocracia: "nao apareceu" nao
  -- ganha uma disputa, "esperei 40 minutos no lobby do hotel, liguei
  -- duas vezes para o numero da reserva" ganha.
  if coalesce(length(btrim(p_nota)), 0) < 20 then
    raise exception 'Escreve o que aconteceu: onde esperaste, o que '
      'tentaste, a que horas. E isto que ganha uma disputa de cartao.';
  end if;

  update bookings set no_show_at = now(), no_show_by = auth.uid(),
                      no_show_wait = p_esperou,
                      no_show_note = btrim(p_nota), updated_at = now()
  where  id = b.id;

  return jsonb_build_object('ok', true, 'reference', b.reference,
    'payment_intent', b.stripe_payment_intent, 'amount', b.price_total);
end $$;

revoke execute on function marcar_falta(uuid, integer, text) from public, anon;
grant  execute on function marcar_falta(uuid, integer, text) to authenticated;

-- =====================================================================
-- COTAR, OUTRA VEZ
--
-- Uma nota sobre ter esta funcao em dois ficheiros: a 017 criou-a, esta
-- substitui-a. A sequencia corre por ordem, por isso esta ganha. E assim
-- que uma cadeia de migracoes funciona — o ficheiro antigo fica como
-- historia e nunca se edita, senao perde-se o registo do que a base ja
-- foi. Quem quiser ler a versao em vigor le SEMPRE a ultima.
--
-- O que muda em relacao a 017:
--   * bebes ao colo nao contam para o escalao nem para a lotacao
--   * o modo opening_hours devolve a janela em vez de exigir uma hora
--   * aplica a promocao, e diz o preco ANTES e DEPOIS
-- =====================================================================
create or replace function cotar(p jsonb)
returns jsonb
language plpgsql stable security definer set search_path = public as $$
declare
  v_slug   text := nullif(trim(p->>'slug'), '');
  v_dia    date;
  v_hora   time;
  v_pessoas integer;   -- o que o cliente escreveu
  v_bebes  integer;    -- destes, os que vao ao colo
  v_pax    integer;    -- os que ocupam lugar: e este que conta
  a        record;
  r        record;
  pr       record;
  promo    record;
  -- Escalares e nao um `record`: um record que nao chega a ser atribuido
  -- rebenta mal se leia um campo dele ("record is not assigned yet"), e
  -- no modo departures ele NUNCA e atribuido — que e o caminho normal.
  v_abre   time;
  v_fecha  time;
  v_tier   jsonb;
  v_base   numeric;
  v_preco  numeric;
  v_max    integer;
  v_horas  numeric;
  v_mais_cedo timestamptz;
begin
  if v_slug is null then
    return jsonb_build_object('ok', false, 'code', 'noTour',
      'error', 'We could not find this tour.');
  end if;

  begin
    v_dia     := (p->>'date')::date;
    v_pessoas := (p->>'pax')::integer;
    v_bebes   := coalesce((p->>'infants')::integer, 0);
    v_hora    := nullif(p->>'time', '')::time;
  exception when others then
    return jsonb_build_object('ok', false, 'code', 'badInput',
      'error', 'Check the date, the time and the number of people.');
  end;

  select l.id, l.operator_id, l.lead_time_hours, l.timezone,
         l.schedule_mode, l.lap_infant_max_age,
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

  if v_pessoas is null or v_pessoas < 1 then
    return jsonb_build_object('ok', false, 'code', 'noPax',
      'error', 'Tell us how many people are travelling.');
  end if;

  -- BEBES AO COLO
  --
  -- So contam como "nao ocupa lugar" se o anuncio disser que leva bebes
  -- ao colo. Sem isso, toda a gente ocupa um lugar — que e o
  -- comportamento de sempre e o seguro.
  if a.lap_infant_max_age is null then
    v_bebes := 0;
  end if;
  v_bebes := least(greatest(v_bebes, 0), v_pessoas - 1);
  v_pax := v_pessoas - v_bebes;

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

  v_base := (v_tier->>'price')::numeric;
  if v_base is null or v_base <= 0 then
    return jsonb_build_object('ok', false, 'code', 'noPrice',
      'error', 'This tour has no online price yet. Send us a message and we will quote it.');
  end if;

  select coalesce(av.price_override, v_base) into v_base
  from   (select 1) z
  left   join availability av on av.listing_id = a.id and av.day = v_dia;
  v_base := coalesce(v_base, (v_tier->>'price')::numeric);
  v_preco := v_base;

  if v_dia is null then
    return jsonb_build_object('ok', false, 'code', 'noDate',
      'error', 'Pick the date of the tour.',
      'price', v_preco, 'currency', 'EUR',
      'vehicle', v_tier->>'vehicle', 'maxPax', v_max);
  end if;

  if not exists (select 1 from dias_abertos(v_slug, v_dia, v_dia)) then
    return jsonb_build_object('ok', false, 'code', 'dayClosed',
      'error', 'That day is not available. Pick another one.',
      'price', v_preco, 'currency', 'EUR', 'maxPax', v_max);
  end if;

  -- A HORA, ou a JANELA
  if a.schedule_mode = 'opening_hours' then
    select j.opens_at, j.closes_at into v_abre, v_fecha
    from janela_no_dia(v_slug, v_dia) j;
    -- Neste modo nao se exige hora nenhuma: combina-se depois. Guardar
    -- uma hora que o cliente escolheu de uma lista inventada era pior do
    -- que nao guardar nada.
    v_hora := null;
  elsif v_hora is not null
     and exists (select 1 from listing_seasons s where s.listing_id = a.id)
     and not exists (select 1 from partidas_no_dia(v_slug, v_dia) pd
                      where pd.starts_at = v_hora) then
    return jsonb_build_object('ok', false, 'code', 'timeClosed',
      'error', 'That start time is no longer available for this date.',
      'price', v_preco, 'currency', 'EUR', 'maxPax', v_max);
  end if;

  select count(*)::integer as n into r
  from   veiculos_livres(a.id, v_dia) vl
  where  vl.max_pax >= v_pax;

  if exists (select 1 from listing_vehicles lx where lx.listing_id = a.id)
     and coalesce(r.n, 0) = 0 then
    return jsonb_build_object('ok', false, 'code', 'noVehicle',
      'error', format('No vehicle for %s people on that date.', v_pax),
      'price', v_preco, 'currency', 'EUR', 'maxPax', v_max);
  end if;

  -- A PROMOCAO
  select * into promo from promocao_para(a.id, v_dia);
  if promo.id is not null then
    v_preco := case when promo.kind = 'percent'
                 then round(v_base * (1 - promo.value / 100.0), 2)
                 else greatest(round(v_base - promo.value, 2), 0) end;
  end if;

  v_mais_cedo := ((v_dia + coalesce(v_hora, v_abre, time '00:00'))
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
      'scheduleMode', a.schedule_mode,
      'pax', v_pax,
      'people', v_pessoas,
      'infants', v_bebes,
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
                    then v_mais_cedo - make_interval(hours => pr2.charge_lead_hours)
                  end)
    -- A janela, so no modo que a tem.
    || case when a.schedule_mode = 'opening_hours' and v_abre is not null
         then jsonb_build_object('window', jsonb_build_object(
                'from', v_abre, 'to', v_fecha))
       else '{}'::jsonb end
    -- A promocao, so quando ha uma. Ausente quer dizer ausente: ver a
    -- nota sobre o `split` na 017.
    || case when promo.id is not null
         then jsonb_build_object('promo', jsonb_build_object(
                'label', promo.label, 'before', v_base,
                'saving', round(v_base - v_preco, 2)))
       else '{}'::jsonb end
    || case when auth.uid() is not null then
         jsonb_build_object('split', jsonb_build_object(
           'rate', a.commission_rate,
           -- QUEM PAGA O DESCONTO
           --
           -- Se a promocao e nossa, o operador recebe o que receberia sem
           -- ela e o desconto sai da nossa comissao. Se e dele, sai da
           -- margem dele. Sem esta distincao, uma campanha nossa cortava
           -- a margem do operador sem ele saber.
           'platform', case when promo.quem_paga = 'platform'
                         then round(v_preco - (v_base - v_base * a.commission_rate), 2)
                         else round(v_preco * a.commission_rate, 2) end,
           'operator', case when promo.quem_paga = 'platform'
                         then round(v_base - v_base * a.commission_rate, 2)
                         else round(v_preco - v_preco * a.commission_rate, 2) end))
       else '{}'::jsonb end
    from payment_rules pr2,
    lateral (
      select
        case
          when v_horas < pr2.min_hours_for_later then false
          when v_preco > pr2.max_value_for_later then false
          else true
        end as permite,
        case
          when v_horas < pr2.min_hours_for_later then
            format('The tour starts in about %s hours. Paying later needs at least %s hours'' notice, so this one is paid at booking.',
                   round(v_horas)::integer, pr2.min_hours_for_later)
          when v_preco > pr2.max_value_for_later then
            'Tours above our higher-value threshold are paid at booking.'
        end as razao,
        case
          when v_horas < pr2.min_hours_for_later then 'tooSoon'
          when v_preco > pr2.max_value_for_later then 'tooExpensive'
        end as codigo
    ) x
    where pr2.id = 1);
end $$;

revoke execute on function cotar(jsonb) from public;
grant  execute on function cotar(jsonb) to anon, authenticated;

-- ---------------------------------------------------------------------
-- A reserva guarda os bebes, para o operador saber quantos lugares
-- precisa de ter e quantas pessoas vai levar. Sao dois numeros
-- diferentes e o operador precisa dos dois.
-- ---------------------------------------------------------------------
alter table bookings
  add column if not exists infants integer not null default 0
    check (infants >= 0 and infants < 10);

comment on column bookings.pax is
  'Lugares ocupados. Os bebes ao colo NAO contam aqui: contam na coluna '
  'infants. O escalao do preco usa esta.';
