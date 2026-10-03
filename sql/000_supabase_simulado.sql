-- O Supabase traz o esquema `auth` e a funcao auth.uid(). Numa base
-- vazia nao existem, por isso para o teste criam-se os minimos.
create schema if not exists auth;
create table if not exists auth.users (id uuid primary key default gen_random_uuid(), email text);
create or replace function auth.uid() returns uuid language sql stable as $$
  select nullif(current_setting('teste.uid', true), '')::uuid $$;
