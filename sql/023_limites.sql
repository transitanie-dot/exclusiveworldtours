-- =====================================================================
-- 023 — Limites de chamada nas escritas abertas ao publico
-- =====================================================================
-- Ha exatamente duas funcoes que um desconhecido pode usar para escrever
-- na base: `candidatar_operador` e `registar_pedido`. As duas ja tinham
-- uma defesa, mas a defesa errada: recusavam o mesmo email duas vezes
-- seguidas. Isso trava o duplo clique e nao trava mais nada — quem quer
-- enchir a tabela muda o email a cada chamada e nunca bate na regra.
--
-- O que trava e contar chamadas. E para contar chamadas e preciso saber
-- de quem vieram, e aqui ha uma subtileza que decide o desenho todo:
--
--   o corpo do pedido vem do navegador, logo e do atacante. Qualquer
--   campo lá dentro — incluindo um que se chamasse "ip" — e mentira
--   assim que convem ao atacante. Nao se pode contar por ele.
--
-- O unico sinal honesto e o cabecalho que o proxy da Supabase poe no
-- pedido antes de ele chegar ao Postgres, e que o PostgREST publica no
-- GUC `request.headers`. Esse o navegador nao escolhe.
--
-- Mas nao e garantido: numa chamada que nao venha pelo PostgREST (a API
-- de gestao, o psql, um trigger) o GUC nao existe. Por isso a contagem
-- tem tres baldes e nao um, e cada um e suficiente sozinho para o caso
-- em que os outros nao dizem nada:
--
--   1. por IP     — o limite verdadeiro, quando ha IP;
--   2. por email   — trava a insistencia de uma pessoa concreta;
--   3. global      — o tecto de toda a plataforma por minuto. E este que
--                    protege a tabela quando o IP nao esta disponivel e
--                    os emails vem todos diferentes.
--
-- Janelas fixas, nao deslizantes: a janela e o instante arredondado para
-- baixo ao tamanho dela. Isto deixa a chave primaria estavel (sem isso
-- cada chamada criava uma linha nova), torna o incremento um upsert de
-- uma linha, e faz a limpeza ser "apaga o que e mais antigo que X".
-- O preco e conhecido e aceitavel: na fronteira entre duas janelas cabem
-- ate 2x o limite. Para travar enchimento de tabelas isso e indiferente.
-- =====================================================================

create table if not exists rate_limits (
  bucket        text        not null,
  chave         text        not null,
  janela_inicio timestamptz not null,
  contagem      integer     not null default 0,
  primary key (bucket, chave, janela_inicio)
);

comment on table rate_limits is
  'Contagem de chamadas por balde e janela. So as funcoes security '
  'definer escrevem aqui; ninguem le isto de fora.';

create index if not exists rate_limits_velhos_idx
  on rate_limits(janela_inicio);

alter table rate_limits enable row level security;

-- Sem uma unica policy: nem anon nem authenticated tem nada que ver ou
-- mexer nisto. As funcoes abaixo sao security definer e passam ao lado.
revoke all on table rate_limits from public, anon, authenticated;

-- ---------------------------------------------------------------------
-- Quem esta a chamar
-- ---------------------------------------------------------------------
-- Devolve o IP do cliente quando o pedido veio pelo PostgREST, e a
-- constante 'sem-ip' quando nao veio. Nunca estoura: um GUC ausente ou
-- com lixo la dentro nao pode ser motivo para uma candidatura falhar.
create or replace function cliente_ip()
returns text
language plpgsql stable security definer set search_path = public as $$
declare
  h    json;
  v_ip text;
begin
  begin
    h := nullif(current_setting('request.headers', true), '')::json;
  exception when others then
    return 'sem-ip';
  end;

  if h is null then
    return 'sem-ip';
  end if;

  -- A ordem importa: o cabecalho mais especifico primeiro. Em
  -- x-forwarded-for pode vir uma lista "cliente, proxy1, proxy2" — o
  -- cliente e o primeiro.
  v_ip := coalesce(
    nullif(btrim(h->>'cf-connecting-ip'), ''),
    nullif(btrim(h->>'x-real-ip'), ''),
    nullif(btrim(split_part(coalesce(h->>'x-forwarded-for', ''), ',', 1)), ''));

  return left(coalesce(v_ip, 'sem-ip'), 60);
end;
$$;

comment on function cliente_ip() is
  'IP do cliente a partir dos cabecalhos que o proxy poe, ou sem-ip '
  'quando a chamada nao veio pelo PostgREST. O corpo do pedido nunca '
  'entra nesta conta: vem do navegador, logo vem do atacante.';

-- ---------------------------------------------------------------------
-- Consumir uma unidade de quota
-- ---------------------------------------------------------------------
-- Devolve true quando a chamada cabe no limite, false quando passa. Nao
-- levanta excecao: quem chama decide o que dizer a pessoa, e nem todos
-- os baldes merecem a mesma mensagem.
create or replace function consumir_quota(
  p_bucket text,
  p_chave  text,
  p_limite integer,
  p_janela interval)
returns boolean
language plpgsql security definer set search_path = public as $$
declare
  v_seg    numeric := extract(epoch from p_janela);
  v_inicio timestamptz;
  v_conta  integer;
begin
  if p_chave is null or btrim(p_chave) = '' or v_seg <= 0 then
    return true;   -- sem chave nao ha nada para contar
  end if;

  v_inicio := to_timestamp(floor(extract(epoch from now()) / v_seg) * v_seg);

  insert into rate_limits (bucket, chave, janela_inicio, contagem)
  values (p_bucket, left(p_chave, 120), v_inicio, 1)
  on conflict (bucket, chave, janela_inicio) do update
    set contagem = rate_limits.contagem + 1
  returning contagem into v_conta;

  return v_conta <= p_limite;
end;
$$;

comment on function consumir_quota(text, text, integer, interval) is
  'Soma 1 ao balde e diz se a chamada cabe no limite. A janela e fixa: '
  'o agora arredondado para baixo ao tamanho da janela.';

revoke execute on function consumir_quota(text, text, integer, interval)
  from public, anon, authenticated;
revoke execute on function cliente_ip() from public, anon, authenticated;

-- ---------------------------------------------------------------------
-- Limpeza
-- ---------------------------------------------------------------------
-- Vai no mesmo cron horario que a `limpar_marcas()`. Guarda um dia: as
-- janelas sao de minutos e de horas, nada mais antigo que isso serve
-- para decidir coisa alguma.
create or replace function limpar_quotas()
returns integer
language sql security definer set search_path = public as $$
  with fora as (
    delete from rate_limits
     where janela_inicio < now() - interval '1 day'
    returning 1)
  select count(*)::integer from fora;
$$;

revoke execute on function limpar_quotas() from public, anon, authenticated;

-- ---------------------------------------------------------------------
-- As duas escritas abertas, agora com limite
-- ---------------------------------------------------------------------
-- Os numeros: uma pessoa de boa fe submete um pedido, talvez dois se se
-- enganou. Dez por hora do mesmo IP e folgado para ela e apertado para
-- um script. O tecto global de 120 por minuto e deliberadamente alto:
-- nao e para moderar trafego normal, e para que um enchimento bata num
-- muro muito antes de a tabela crescer.
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
  v_ip    text  := cliente_ip();
begin
  -- O tecto global primeiro: e o que protege a tabela, e e o mais
  -- barato de avaliar.
  if not consumir_quota('pedido:global', 'todos', 120, interval '1 minute') then
    raise exception 'We are receiving a lot of requests right now. Please try again in a minute.';
  end if;
  if not consumir_quota('pedido:ip', v_ip, 10, interval '1 hour') then
    raise exception 'You have sent several requests already. We have them — give us a little time to reply.';
  end if;

  if length(btrim(coalesce(p->>'name', ''))) < 2 then
    raise exception 'Your name is required';
  end if;
  if position('@' in v_email) < 2 or length(v_email) > 200 then
    raise exception 'A valid email address is required';
  end if;
  if v_data is not null and v_data < current_date then
    raise exception 'That date has already passed';
  end if;

  if not consumir_quota('pedido:email', lower(v_email), 5, interval '1 hour') then
    raise exception 'You have sent several requests already. We have them — give us a little time to reply.';
  end if;

  if v_data is not null and v_slug <> '' then
    select l.id, l.lead_time_hours,
           exists (select 1 from epoca_do_dia(l.id, v_data))
      into v_id_l, v_lead, v_horas
    from listings l where l.slug = v_slug and l.status = 'live';

    if v_lead is not null then
      if v_horas then
        -- Com uma epoca a cobrir o dia a conta e exata: tem de sobrar pelo
        -- menos uma partida nesse dia. Se a pessoa escolheu uma hora,
        -- tem de ser essa.
        if v_hora is not null then
          if not exists (select 1 from partidas_possiveis(v_id_l, v_data) x
                         where x.starts_at = v_hora) then
            raise exception 'That departure is no longer possible. This tour needs % hours'' notice; pick another time or a later date.', v_lead;
          end if;
        elsif not exists (select 1 from partidas_possiveis(v_id_l, v_data)) then
          raise exception 'No departure that day is still possible. This tour needs % hours'' notice.', v_lead;
        end if;
      else
        -- Sem epoca a cobrir o dia, a regra antiga: o dia inteiro.
        -- (A `partidas_possiveis` ainda le a listing_times neste caso.)
        if v_data < ((now() + make_interval(hours => v_lead))::date
                     + case when (now() + make_interval(hours => v_lead))::time
                                 <> '00:00:00' then 1 else 0 end) then
          raise exception 'That tour needs at least % hours notice. Pick a later date, or write to us without a date and we will see what we can do.', v_lead;
        end if;
      end if;
    end if;
  end if;

  -- O duplo clique continua a ser duplo clique, e isto continua a
  -- devolver null em vez de estourar: a pessoa carregou duas vezes no
  -- botao, nao fez nada de errado.
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

-- Uma candidatura de operador e um acontecimento raro: tres por dia do
-- mesmo IP ja e muito, e o tecto global de 30 por hora cobre o dia em
-- que apareçamos numa newsletter do ramo.
create or replace function candidatar_operador(p jsonb)
returns uuid
language plpgsql security definer set search_path = public as $$
declare
  v_id    uuid;
  v_email text := btrim(coalesce(p->>'email', ''));
  v_ip    text := cliente_ip();
begin
  if not consumir_quota('cand:global', 'todos', 30, interval '1 hour') then
    raise exception 'We are receiving a lot of applications right now. Please try again later.';
  end if;
  if not consumir_quota('cand:ip', v_ip, 3, interval '1 day') then
    raise exception 'You have already applied. We will come back to you by email.';
  end if;

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

  if not consumir_quota('cand:email', lower(v_email), 2, interval '1 day') then
    raise exception 'You have already applied. We will come back to you by email.';
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
