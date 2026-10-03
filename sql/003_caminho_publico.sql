-- =====================================================================
-- O caminho publico
--
-- Com RLS ligado, o visitante do site nao le `availability` — e esta
-- certo que nao leia: a tabela tem precos especiais e lugares vendidos.
-- Mas a pagina do tour TEM de mostrar os dias certos, senao o cliente
-- escolhe um dia que o operador ja fechou e a reserva vai ter de ser
-- cancelada.
--
-- Por isso o publico nao recebe tabelas: recebe funcoes que devolvem
-- exatamente o que a pagina precisa, e nada mais. A superficie exposta
-- e a lista de `grant execute` la em baixo — e so essa.
-- =====================================================================

-- As vistas correm com as permissoes de quem consulta, e nao de quem as
-- criou. Sem isto, uma chave publica que chegasse a uma vista veria tudo
-- o que esta por tras dela.
alter view listing_live    set (security_invoker = true);
alter view public_listings set (security_invoker = true);

-- is_admin() e meus_operadores() leem apenas o utilizador autenticado,
-- por isso nao revelam nada a quem nao assinou; mesmo assim ficam fora
-- do alcance de quem nao esta autenticado.
revoke execute on function is_admin()        from anon, public;
revoke execute on function meus_operadores() from anon, public;
grant  execute on function is_admin()        to authenticated;
grant  execute on function meus_operadores() to authenticated;

-- repartir() mostra a comissao. Nunca para o publico.
revoke execute on function repartir(uuid, numeric) from anon, public;
grant  execute on function repartir(uuid, numeric) to authenticated;

-- Os dias abertos de um anuncio, num intervalo. Devolve o dia e, se
-- houver, o preco desse dia. Nao devolve lugares vendidos nem notas.
--
-- NOTA: a 006 reescreve o CORPO desta funcao — passa a respeitar o lead
-- time do anuncio e a frota do operador. A assinatura e o tipo de
-- retorno ficam exatamente como estao, de proposito: mudar o tipo de
-- retorno obrigava a um `drop`, e um `drop` numa base de producao e uma
-- janela em que a pagina do tour fica sem resposta. O detalhe da frota
-- vive numa funcao propria, `frota_no_dia`.
create or replace function dias_abertos(p_slug text, p_de date, p_ate date)
returns table (day date, price numeric)
language sql stable security definer set search_path = public as $$
  with anuncio as (
    select l.id, l.operator_id
    from   listings l
    join   operators o on o.id = l.operator_id
    where  l.slug = p_slug and l.status = 'live' and o.status = 'approved'
  )
  select d::date,
         (select a.price_override from availability a
           where a.listing_id = anuncio.id and a.day = d::date)
  from   anuncio, generate_series(greatest(p_de, current_date), p_ate, interval '1 day') as d
  where  not exists (
           select 1 from availability a
           where a.listing_id = anuncio.id and a.day = d::date
             and a.status in ('closed', 'sold_out'))
    and  not exists (
           select 1 from blackouts b
           where b.operator_id = anuncio.operator_id
             and d::date between b.starts_on and b.ends_on);
$$;

-- O limite de 400 dias vive dentro da propria consulta desde a 006. Havia
-- aqui uma segunda versao da funcao, com um argumento de limite; foi
-- retirada porque duas versoes da mesma pergunta e como se perde a
-- resposta certa.
revoke execute on function dias_abertos(text, date, date) from public;
grant  execute on function dias_abertos(text, date, date) to anon, authenticated;

-- O visitante escreve e nao encontra nada. Essa linha e a lista de
-- compras do marketplace: diz em que cidade falta um operador. Mas o
-- publico so pode ESCREVER; ler as procuras e so do administrador.
create or replace function registar_procura(p_q text, p_resultados integer,
                                            p_cidade text default null,
                                            p_pais text default null)
returns void
language plpgsql security definer set search_path = public as $$
begin
  -- Uma procura vazia nao e informacao, e um texto de 500 caracteres e
  -- quase sempre alguem a testar o formulario.
  if p_q is null or length(btrim(p_q)) = 0 or length(p_q) > 120 then
    return;
  end if;

  insert into search_queries (q, results, city_match, country)
  values (btrim(p_q), greatest(coalesce(p_resultados, 0), 0),
          left(p_cidade, 120), left(p_pais, 120));
end;
$$;

revoke execute on function registar_procura(text, integer, text, text) from public;
grant  execute on function registar_procura(text, integer, text, text) to anon, authenticated;
