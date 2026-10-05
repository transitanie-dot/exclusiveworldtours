-- =====================================================================
-- Os pontos de encontro, e um sitio para as fotografias viverem
--
-- Ate aqui uma fotografia era uma morada que o operador colava. Para um
-- operador de turismo isso quer dizer: ter um sitio onde alojar imagens,
-- saber o que e uma URL directa, e perceber porque e que a do Facebook
-- nao serve. Na pratica, quer dizer nao ter fotografias.
--
-- Agora ha um balde no Supabase Storage. O operador escolhe o ficheiro e
-- acabou.
-- =====================================================================

-- ---------------------------------------------------------------------
-- O BALDE
--
-- Publico para leitura: uma fotografia de um ponto de encontro vai estar
-- numa pagina publica de qualquer maneira, e uma URL assinada que expira
-- dentro de uma pagina estatica gerada ha tres dias e uma imagem
-- partida.
--
-- Escrita so para quem assinou, e so na pasta do seu operador. O caminho
-- e <operator_id>/<ficheiro>, e a politica verifica a primeira pasta:
-- sem isso, um operador escrevia por cima das fotografias de outro.
--
-- Isto corre no Supabase; num Postgres local nao ha esquema `storage`,
-- por isso esta parte so e aplicada se ele existir.
-- ---------------------------------------------------------------------
do $$
begin
  if exists (select 1 from information_schema.schemata
             where schema_name = 'storage') then

    insert into storage.buckets (id, name, public, file_size_limit,
                                 allowed_mime_types)
    values ('fotos', 'fotos', true, 5242880,
            array['image/jpeg','image/png','image/webp','image/avif'])
    on conflict (id) do update
      set public = true, file_size_limit = 5242880,
          allowed_mime_types = array['image/jpeg','image/png','image/webp','image/avif'];

    -- As politicas sao criadas uma a uma e so se faltarem: `create
    -- policy` nao tem `if not exists`, e um `drop` aqui apagava o acesso
    -- as fotografias durante o tempo que a migracao demorasse a correr.
    if not exists (select 1 from pg_policies
                   where schemaname = 'storage' and tablename = 'objects'
                     and policyname = 'fotos_le') then
      execute $p$create policy fotos_le on storage.objects for select
                 using (bucket_id = 'fotos')$p$;
    end if;
    if not exists (select 1 from pg_policies
                   where schemaname = 'storage' and tablename = 'objects'
                     and policyname = 'fotos_poe') then
      execute $p$create policy fotos_poe on storage.objects for insert
                 to authenticated with check (bucket_id = 'fotos'
                 and (storage.foldername(name))[1]::uuid in (select meus_operadores()))$p$;
    end if;
    if not exists (select 1 from pg_policies
                   where schemaname = 'storage' and tablename = 'objects'
                     and policyname = 'fotos_troca') then
      execute $p$create policy fotos_troca on storage.objects for update
                 to authenticated
                 using (bucket_id = 'fotos'
                 and (storage.foldername(name))[1]::uuid in (select meus_operadores()))
                 with check (bucket_id = 'fotos'
                 and (storage.foldername(name))[1]::uuid in (select meus_operadores()))$p$;
    end if;
    if not exists (select 1 from pg_policies
                   where schemaname = 'storage' and tablename = 'objects'
                     and policyname = 'fotos_apaga') then
      execute $p$create policy fotos_apaga on storage.objects for delete
                 to authenticated
                 using (bucket_id = 'fotos'
                 and (storage.foldername(name))[1]::uuid in (select meus_operadores()))$p$;
    end if;
  end if;
end $$;

-- ---------------------------------------------------------------------
-- OS PONTOS DE ENCONTRO
--
-- Pertencem ao OPERADOR e nao ao anuncio, pela mesma razao que os
-- veiculos: quem parte sempre da mesma praca nao deve escrever a mesma
-- morada em seis tours, nem corrigi-la em seis sitios quando uma obra
-- fechar a rua.
--
-- Sao dados RAPIDOS: nao passam por revisao. Um ponto de encontro errado
-- no dia e um cliente parado no sitio errado — fazer isso esperar pela
-- minha leitura seria o mesmo erro que fazer o calendario esperar.
-- ---------------------------------------------------------------------
create table if not exists meeting_points (
  id           uuid primary key default gen_random_uuid(),
  operator_id  uuid not null references operators(id) on delete cascade,
  name         text not null,
  address      text,
  lat          numeric(9,6) check (lat is null or (lat between -90 and 90)),
  lng          numeric(9,6) check (lng is null or (lng between -180 and 180)),
  instructions text,
  photo_url    text,
  created_at   timestamptz not null default now(),
  -- Meia coordenada nao serve para nada e desenha um pino no oceano.
  constraint mp_coordenadas_aos_pares check ((lat is null) = (lng is null))
);

create index if not exists mp_operador_idx on meeting_points(operator_id);

alter table meeting_points enable row level security;

drop policy if exists mp_tudo on meeting_points;
create policy mp_tudo on meeting_points for all
  using (is_admin() or operator_id in (select meus_operadores()))
  with check (is_admin() or operator_id in (select meus_operadores()));

alter table listings
  add column if not exists meeting_point_id uuid
    references meeting_points(id) on delete set null;

comment on column listings.meeting_point_id is
  'Nulo quer dizer recolha no hotel, que e o normal num dia privado. '
  'Preenchido quer dizer que o cliente vai ter a um sitio.';

-- ---------------------------------------------------------------------
-- O QUE O PUBLICO VE
--
-- Isto devia ser uma coluna do catalogo_publico(), e nao e: mudar o tipo
-- de retorno de uma funcao obriga a um drop, e um drop numa base de
-- producao e uma janela em que a pagina do tour fica sem resposta.
--
-- A licao, para a proxima vez que houver razao para mexer no catalogo
-- com o Ricardo a confirmar: ele devia devolver UMA coluna jsonb por
-- linha em vez de dezasseis colunas, e assim acrescentar um campo nunca
-- mais mudava a assinatura. Fica dito.
-- ---------------------------------------------------------------------
create or replace function pontos_de_encontro()
returns table (slug text, name text, address text,
               lat numeric, lng numeric,
               instructions text, photo_url text)
language sql stable security definer set search_path = public as $$
  select l.slug, m.name, m.address, m.lat, m.lng, m.instructions, m.photo_url
  from   listings l
  join   operators o on o.id = l.operator_id
  join   meeting_points m on m.id = l.meeting_point_id
  where  l.status = 'live' and o.status = 'approved'
  order  by l.slug;
$$;

revoke execute on function pontos_de_encontro() from public;
grant  execute on function pontos_de_encontro() to anon, authenticated;

create or replace function ponto_de_encontro(p_slug text)
returns table (name text, address text, lat numeric, lng numeric,
               instructions text, photo_url text)
language sql stable security definer set search_path = public as $$
  select m.name, m.address, m.lat, m.lng, m.instructions, m.photo_url
  from   listings l
  join   operators o on o.id = l.operator_id
  join   meeting_points m on m.id = l.meeting_point_id
  where  l.slug = p_slug and l.status = 'live' and o.status = 'approved';
$$;

revoke execute on function ponto_de_encontro(text) from public;
grant  execute on function ponto_de_encontro(text) to anon, authenticated;
