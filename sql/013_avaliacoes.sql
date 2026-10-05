-- =====================================================================
-- As avaliacoes
--
-- A REGRA QUE MANDA EM TUDO: NAO HA AVALIACAO SEM VIAGEM
--
-- Um marketplace novo nao tem avaliacoes nenhumas, e e exatamente por
-- isso que a tentacao de as facilitar e grande — um formulario aberto,
-- um convite por link que se pode reenviar, um "deixe a sua opiniao" no
-- fim da pagina. Qualquer uma dessas coisas transforma a primeira
-- avaliacao deste site numa avaliacao que ninguem acredita, e a unica
-- coisa que uma marca nova tem para vender e ser acreditada.
--
-- Por isso a cadeia e fechada e tem um so sentido:
--
--   pedido  ->  viajou  ->  convite (um token, uma utilizacao)  ->  avaliacao
--
-- Nao ha caminho para uma avaliacao que nao comece num pedido que o
-- Ricardo marcou como viajado. Nao ha formulario aberto. O token e de
-- uma utilizacao e expira. Um pedido so pode dar uma avaliacao.
--
-- O QUE SE PODE E NAO SE PODE FAZER A UMA AVALIACAO DEPOIS
--
--   o operador   responde em publico. Nunca muda a nota nem o texto.
--   o Ricardo    esconde, e so por razoes estreitas, que estao escritas
--                em `hidden_reason` e ficam no registo. Uma avaliacao
--                negativa e verdadeira NAO e uma dessas razoes.
--   o cliente    escreve uma vez.
--
-- Esconder nao apaga: a linha fica, com a razao. Uma plataforma que
-- apaga avaliacoes sem deixar rasto acaba por apagar as que lhe doem.
-- =====================================================================

-- ---------------------------------------------------------------------
-- O PEDIDO PASSA A SABER SE A VIAGEM ACONTECEU
-- ---------------------------------------------------------------------
alter table enquiries
  add column if not exists travelled_on date,
  add column if not exists listing_id uuid references listings(id) on delete set null;

comment on column enquiries.travelled_on is
  'A data em que a viagem aconteceu mesmo. Preenchida pelo Ricardo. '
  'E a unica porta para um convite de avaliacao.';

-- ---------------------------------------------------------------------
-- OS CONVITES
--
-- Um token por viagem. Opaco, de uma utilizacao, com prazo. Sem ele nao
-- ha avaliacao nenhuma.
-- ---------------------------------------------------------------------
create table if not exists review_invites (
  token       uuid primary key default gen_random_uuid(),
  enquiry_id  uuid not null unique references enquiries(id) on delete cascade,
  listing_id  uuid not null references listings(id) on delete cascade,
  operator_id uuid not null references operators(id) on delete cascade,
  sent_at     timestamptz,
  used_at     timestamptz,
  expires_at  timestamptz not null default now() + interval '90 days',
  created_at  timestamptz not null default now()
);

create index if not exists convites_por_usar_idx on review_invites(created_at)
  where used_at is null;

alter table review_invites enable row level security;

-- Ninguem le a tabela dos convites pela API. Nem o operador: um operador
-- que visse os tokens dos seus clientes podia escrever as avaliacoes
-- deles. O unico caminho para um token e a funcao de validacao, que
-- recebe o token e nao o devolve.
drop policy if exists ri_admin on review_invites;
create policy ri_admin on review_invites for select using (is_admin());

-- Criar convites e so do administrador, e e uma politica explicita em
-- vez de uma funcao `security definer`: assim a regra esta escrita na
-- tabela, onde se le, e nao escondida dentro de uma funcao que ignora o
-- RLS. A funcao continua a verificar is_admin() — duas fechaduras na
-- mesma porta e o que se quer num sitio destes.
drop policy if exists ri_admin_cria on review_invites;
create policy ri_admin_cria on review_invites for insert
  with check (is_admin());

-- Gastar o token e marcar `used_at`, e quem o faz e a funcao
-- `deixar_avaliacao`, que corre como `security definer` precisamente
-- para isto: o cliente que esta a avaliar nao assinou, e nao pode ter
-- permissao nenhuma sobre esta tabela.
drop policy if exists ri_admin_muda on review_invites;
create policy ri_admin_muda on review_invites for update
  using (is_admin()) with check (is_admin());

-- ---------------------------------------------------------------------
-- AS AVALIACOES
-- ---------------------------------------------------------------------
do $$ begin
  create type review_state as enum ('published', 'hidden');
exception when duplicate_object then null;
end $$;

create table if not exists reviews (
  id            uuid primary key default gen_random_uuid(),
  listing_id    uuid not null references listings(id) on delete cascade,
  operator_id   uuid not null references operators(id) on delete cascade,
  -- Uma viagem, uma avaliacao. A unicidade esta aqui e nao numa
  -- verificacao no codigo, porque uma verificacao no codigo perde-se
  -- numa corrida entre dois pedidos.
  enquiry_id    uuid not null unique references enquiries(id) on delete cascade,

  rating        smallint not null check (rating between 1 and 5),
  -- As quatro notas por tema. Opcionais: obrigar a cinco notas para
  -- deixar uma avaliacao e a maneira mais segura de nao receber
  -- nenhuma.
  r_driver      smallint check (r_driver      between 1 and 5),
  r_vehicle     smallint check (r_vehicle     between 1 and 5),
  r_value       smallint check (r_value       between 1 and 5),
  r_organising  smallint check (r_organising  between 1 and 5),

  title         text,
  body          text,
  author_name   text not null,
  author_country text,
  travelled_on  date not null,

  state         review_state not null default 'published',
  hidden_reason text,
  hidden_at     timestamptz,

  reply         text,
  replied_at    timestamptz,

  created_at    timestamptz not null default now(),

  -- Esconder sem dizer porque nao se faz. A base recusa.
  constraint esconder_tem_razao
    check (state = 'published'
           or (hidden_reason is not null and length(btrim(hidden_reason)) > 10))
);

create index if not exists av_anuncio_idx on reviews(listing_id, created_at desc)
  where state = 'published';
create index if not exists av_operador_idx on reviews(operator_id, created_at desc)
  where state = 'published';

alter table reviews enable row level security;

-- O operador le as suas. Nao as muda: a politica de update so existe
-- para a resposta, e passa por uma funcao que so deixa mexer nesse
-- campo.
drop policy if exists av_leitura on reviews;
create policy av_leitura on reviews for select
  using (is_admin() or operator_id in (select meus_operadores()));

drop policy if exists av_admin on reviews;
create policy av_admin on reviews for update
  using (is_admin()) with check (is_admin());

-- ---------------------------------------------------------------------
-- CRIAR O CONVITE
--
-- So o administrador, e so para um pedido que viajou. A data da viagem
-- e o que torna o convite legitimo, e por isso e ela que esta a ser
-- verificada e nao o estado do pedido — um estado pode ser mudado por
-- engano, uma data que ainda nao aconteceu nao.
-- ---------------------------------------------------------------------
create or replace function convidar_avaliacao(p_enquiry uuid)
returns uuid
language plpgsql security invoker set search_path = public as $$
declare
  e enquiries;
  l listings;
  v_token uuid;
begin
  if not is_admin() then
    raise exception 'So um administrador convida para avaliar';
  end if;

  select * into e from enquiries where id = p_enquiry;
  if not found then
    raise exception 'Pedido inexistente';
  end if;
  if e.travelled_on is null then
    raise exception 'Esse pedido ainda nao viajou. Marca a data da viagem primeiro.';
  end if;
  if e.travelled_on > current_date then
    raise exception 'A data da viagem esta no futuro.';
  end if;

  select * into l from listings
   where id = coalesce(e.listing_id,
                       (select id from listings where slug = e.listing_slug));
  if not found then
    raise exception 'Esse pedido nao esta ligado a nenhum tour.';
  end if;

  insert into review_invites (enquiry_id, listing_id, operator_id)
  values (p_enquiry, l.id, l.operator_id)
  on conflict (enquiry_id) do update set enquiry_id = excluded.enquiry_id
  returning token into v_token;

  return v_token;
end;
$$;

revoke execute on function convidar_avaliacao(uuid) from public, anon;
grant  execute on function convidar_avaliacao(uuid) to authenticated;

-- ---------------------------------------------------------------------
-- O QUE O CONVIDADO VE ANTES DE ESCREVER
--
-- Recebe o token e devolve o minimo para a pagina fazer sentido: que
-- tour foi, que dia, e o nome proprio de quem pediu. Nao devolve o
-- email, nem o telefone, nem a mensagem original — um token que caisse
-- nas maos erradas nao pode virar uma ficha de cliente.
-- ---------------------------------------------------------------------
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
    e.travelled_on,
    split_part(btrim(e.name), ' ', 1)
  from review_invites i
  join enquiries e on e.id = i.enquiry_id
  join listings l on l.id = i.listing_id
  -- Pela mesma razao da 010: uma funcao definer que le atraves de uma
  -- vista invoker devolve zero linhas a quem nao assinou, sem dar erro.
  left join (select distinct on (v.listing_id) v.listing_id, v.payload
             from listing_versions v where v.status = 'approved'
             order by v.listing_id, v.version desc) lv on lv.listing_id = l.id
  where i.token = p_token;
$$;

revoke execute on function convite(uuid) from public;
grant  execute on function convite(uuid) to anon, authenticated;

-- ---------------------------------------------------------------------
-- DEIXAR A AVALIACAO
--
-- Gasta o token na mesma transacao em que escreve a avaliacao. Se duas
-- submissoes chegarem ao mesmo tempo, uma delas encontra o token ja
-- gasto e perde — e e a base a decidir isso, nao o browser.
-- ---------------------------------------------------------------------
create or replace function deixar_avaliacao(p_token uuid, p jsonb)
returns uuid
language plpgsql security definer set search_path = public as $$
declare
  i review_invites;
  e enquiries;
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

  select * into e from enquiries where id = i.enquiry_id;

  insert into reviews (
    listing_id, operator_id, enquiry_id, rating,
    r_driver, r_vehicle, r_value, r_organising,
    title, body, author_name, author_country, travelled_on)
  values (
    i.listing_id, i.operator_id, i.enquiry_id, v_nota,
    nullif(btrim(coalesce(p->>'r_driver', '')), '')::smallint,
    nullif(btrim(coalesce(p->>'r_vehicle', '')), '')::smallint,
    nullif(btrim(coalesce(p->>'r_value', '')), '')::smallint,
    nullif(btrim(coalesce(p->>'r_organising', '')), '')::smallint,
    left(btrim(p->>'title'), 140),
    left(btrim(p->>'body'), 4000),
    -- O nome vem do pedido e nao do formulario: quem avalia e quem
    -- viajou, e deixar escolher o nome e deixar assinar como outra
    -- pessoa. Só o primeiro nome vai para a pagina.
    split_part(btrim(e.name), ' ', 1),
    left(btrim(p->>'author_country'), 80),
    e.travelled_on)
  returning id into v_id;

  update review_invites set used_at = now() where token = p_token;
  update enquiries set status = 'closed' where id = i.enquiry_id;

  return v_id;
end;
$$;

revoke execute on function deixar_avaliacao(uuid, jsonb) from public;
grant  execute on function deixar_avaliacao(uuid, jsonb) to anon, authenticated;

-- ---------------------------------------------------------------------
-- A RESPOSTA DO OPERADOR
--
-- So a resposta. Uma politica de update aberta deixava o operador mexer
-- na nota que recebeu, e nenhuma plataforma sobrevive a isso.
-- ---------------------------------------------------------------------
create or replace function responder_avaliacao(p_review uuid, p_texto text)
returns void
language plpgsql security definer set search_path = public as $$
declare
  v_op uuid;
begin
  select operator_id into v_op from reviews where id = p_review;
  if not found then
    raise exception 'Avaliacao inexistente';
  end if;
  if not (is_admin() or v_op in (select meus_operadores())) then
    raise exception 'Essa avaliacao nao e tua';
  end if;
  if length(btrim(coalesce(p_texto, ''))) < 10 then
    raise exception 'Write a real reply — the guest reads it exactly as you write it.';
  end if;

  update reviews
     set reply = left(btrim(p_texto), 2000), replied_at = now()
   where id = p_review;
end;
$$;

revoke execute on function responder_avaliacao(uuid, text) from public, anon;
grant  execute on function responder_avaliacao(uuid, text) to authenticated;

-- ---------------------------------------------------------------------
-- ESCONDER, COM RAZAO ESCRITA
--
-- As razoes estreitas, e so estas: a viagem nao aconteceu; o texto e
-- ofensivo ou identifica alguem; a nota contradiz o texto de forma
-- obvia; e publicidade; ou ha um conflito de interesses.
--
-- "E negativa e verdadeira" nao esta na lista e nunca vai estar.
-- ---------------------------------------------------------------------
create or replace function esconder_avaliacao(p_review uuid, p_razao text)
returns void
language plpgsql security invoker set search_path = public as $$
begin
  if not is_admin() then
    raise exception 'So um administrador esconde avaliacoes';
  end if;
  if length(btrim(coalesce(p_razao, ''))) < 11 then
    raise exception 'Escreve a razao. Fica no registo, e e o que impede isto de virar um botao de apagar o que doi.';
  end if;
  update reviews
     set state = 'hidden', hidden_reason = btrim(p_razao), hidden_at = now()
   where id = p_review;
end;
$$;

revoke execute on function esconder_avaliacao(uuid, text) from public, anon;
grant  execute on function esconder_avaliacao(uuid, text) to authenticated;
