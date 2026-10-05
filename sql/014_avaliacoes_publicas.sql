-- =====================================================================
-- As avaliacoes, do lado de quem as le
--
-- Tres decisoes, e as tres sao sobre honestidade e nao sobre codigo.
--
-- 1. PONDERADAS PELA RECENCIA, E DITO
--    Uma avaliacao de ha dois anos descreve um carro que ja foi
--    vendido e um motorista que ja saiu. Pesa metade ao fim de 18
--    meses, metade outra vez ao fim de 36. A media simples tambem e
--    devolvida, porque uma media ponderada que ninguem pode verificar
--    e so um numero bonito.
--
-- 2. ZERO AVALIACOES NAO E ZERO ESTRELAS
--    Um tour sem avaliacoes devolve `n = 0` e media nula. A pagina
--    mostra NADA — nem estrelas vazias, nem "sem avaliacoes ainda" em
--    letras grandes. Uma marca nova tem de conseguir viver com um
--    espaco em branco; o que nao pode e desenhar cinco estrelas
--    apagadas e parecer um tour que correu mal.
--
-- 3. O ARRANQUE A FRIO, SEM MENTIR
--    Um tour com menos de 3 avaliacoes proprias mostra a nota do
--    OPERADOR, e diz que e do operador. E o que a GetYourGuide faz, e
--    e defensavel: a nota e verdadeira, so nao e daquele tour. O que
--    nao se faz e mostrar a nota do operador como se fosse a do tour.
-- =====================================================================

-- A meia-vida, em meses. Num sitio so para ser discutivel: se amanha
-- parecer curta demais, muda-se aqui.
-- O `set search_path` aqui e pela mesma razao da nova_referencia na 017:
-- esta funcao nao e `security definer`, mas e chamada de dentro da
-- nota_anuncio() e da nota_operador(), que sao. Sem ele, o search_path e
-- de quem chama.
create or replace function peso_recencia(p_quando date)
returns numeric
language sql immutable
set search_path = public as $$
  select power(0.5, greatest(0, (current_date - p_quando)) / 547.0);  -- 18 meses
$$;

-- ---------------------------------------------------------------------
-- A nota de um anuncio, e a do operador
-- ---------------------------------------------------------------------
create or replace function nota_anuncio(p_listing uuid)
returns table (n integer, media numeric, ponderada numeric,
               driver numeric, vehicle numeric, value numeric,
               organising numeric)
language sql stable security definer set search_path = public as $$
  select count(*)::integer,
         round(avg(r.rating)::numeric, 2),
         round((sum(r.rating * peso_recencia(r.travelled_on))
                / nullif(sum(peso_recencia(r.travelled_on)), 0))::numeric, 2),
         round(avg(r.r_driver)::numeric, 2),
         round(avg(r.r_vehicle)::numeric, 2),
         round(avg(r.r_value)::numeric, 2),
         round(avg(r.r_organising)::numeric, 2)
  from reviews r
  where r.listing_id = p_listing and r.state = 'published';
$$;

create or replace function nota_operador(p_operator uuid)
returns table (n integer, media numeric, ponderada numeric)
language sql stable security definer set search_path = public as $$
  select count(*)::integer,
         round(avg(r.rating)::numeric, 2),
         round((sum(r.rating * peso_recencia(r.travelled_on))
                / nullif(sum(peso_recencia(r.travelled_on)), 0))::numeric, 2)
  from reviews r
  where r.operator_id = p_operator and r.state = 'published';
$$;

-- ---------------------------------------------------------------------
-- O que o gerador do site leva
--
-- Uma chamada so, com as notas de todos os tours no ar e as do
-- operador de cada um. `mostrar` diz a pagina o que fazer, para a
-- decisao do arranque a frio viver aqui e nao em tres sitios do
-- gerador:
--
--   'tour'      ha 3 ou mais avaliacoes proprias: mostra-se a do tour
--   'operador'  ha menos de 3, mas o operador tem alguma: mostra-se a
--               dele, DITO que e dele
--   'nada'      nao ha nenhuma. A pagina nao desenha estrelas.
-- ---------------------------------------------------------------------
create or replace function notas_publicas()
returns table (slug text, mostrar text,
               n integer, media numeric, ponderada numeric,
               op_n integer, op_media numeric, op_ponderada numeric,
               operator_name text,
               driver numeric, vehicle numeric, value numeric,
               organising numeric)
language sql stable security definer set search_path = public as $$
  select l.slug,
         case when a.n >= 3 then 'tour'
              when o.n > 0  then 'operador'
              else 'nada' end,
         a.n, a.media, a.ponderada,
         o.n, o.media, o.ponderada,
         op.name,
         a.driver, a.vehicle, a.value, a.organising
  from   listings l
  join   operators op on op.id = l.operator_id,
         lateral nota_anuncio(l.id) a,
         lateral nota_operador(l.operator_id) o
  where  l.status = 'live' and op.status = 'approved';
$$;

-- As avaliacoes em si, para o gerador as escrever nas paginas. So as
-- publicadas, e so o que vai aparecer: nem email, nem o pedido de onde
-- vieram, nem a razao por que outra foi escondida.
create or replace function avaliacoes_publicas(p_por_tour integer default 12)
returns table (slug text, rating smallint, title text, body text,
               author_name text, author_country text, travelled_on date,
               reply text, replied_at timestamptz, created_at timestamptz)
language sql stable security definer set search_path = public as $$
  select x.slug, x.rating, x.title, x.body, x.author_name, x.author_country,
         x.travelled_on, x.reply, x.replied_at, x.created_at
  from (
    select l.slug, r.rating, r.title, r.body, r.author_name,
           r.author_country, r.travelled_on, r.reply, r.replied_at,
           r.created_at,
           row_number() over (partition by l.slug
                              order by r.travelled_on desc, r.created_at desc) as ordem
    from   reviews r
    join   listings l on l.id = r.listing_id
    join   operators o on o.id = l.operator_id
    where  r.state = 'published' and l.status = 'live'
      and  o.status = 'approved'
  ) x
  where x.ordem <= greatest(1, least(coalesce(p_por_tour, 12), 50));
$$;

revoke execute on function nota_anuncio(uuid) from public, anon;
revoke execute on function nota_operador(uuid) from public, anon;
grant  execute on function nota_anuncio(uuid) to authenticated;
grant  execute on function nota_operador(uuid) to authenticated;

revoke execute on function notas_publicas() from public;
grant  execute on function notas_publicas() to anon, authenticated;
revoke execute on function avaliacoes_publicas(integer) from public;
grant  execute on function avaliacoes_publicas(integer) to anon, authenticated;
