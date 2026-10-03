-- O Supabase traz o esquema `auth` e a funcao auth.uid(). Numa base
-- vazia nao existem, por isso para o teste criam-se os minimos.
create schema if not exists auth;
create table if not exists auth.users (id uuid primary key default gen_random_uuid(), email text);
create or replace function auth.uid() returns uuid language sql stable as $$
  select nullif(current_setting('teste.uid', true), '')::uuid $$;

-- O Supabase tambem traz os papeis `anon` (quem nao assinou) e
-- `authenticated` (quem assinou). Os `grant`/`revoke` das migracoes
-- falham sem eles, e e precisamente isso que se quer testar: se o
-- teste nao tem os papeis, nao esta a testar as permissoes a serio.
do $$ begin create role anon nologin;          exception when duplicate_object then null; end $$;
do $$ begin create role authenticated nologin; exception when duplicate_object then null; end $$;
grant usage on schema public to anon, authenticated;
