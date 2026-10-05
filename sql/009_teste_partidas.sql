-- =====================================================================
-- As horas de partida, postas a prova
--
-- O que se prova: que o lead time deixou de arredondar. O mesmo dia pode
-- ter a partida da manha fechada e a da tarde aberta — e e isso que
-- devolve ao operador os dias que o arredondamento lhe tirava.
-- =====================================================================

\set ON_ERROR_STOP on
\pset pager off

begin;

insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'ana@exemplo.invalid')
on conflict do nothing;
insert into operators (id, name, country, city, email, status, approved_at)
values ('aaaaaaaa-0000-0000-0000-000000000001', 'Ana Tours', 'Ireland',
        'Dublin', 'ana@exemplo.invalid', 'approved', now())
on conflict (id) do nothing;
insert into operator_users (operator_id, user_id)
values ('aaaaaaaa-0000-0000-0000-000000000001',
        '11111111-1111-1111-1111-111111111111')
on conflict do nothing;

-- Um tour com 24 horas de aviso e duas partidas: 08:00 e 17:00.
insert into listings (id, operator_id, slug, status, city, country,
                      lead_time_hours, timezone)
values ('bbbbbbbb-0000-0000-0000-000000000001',
        'aaaaaaaa-0000-0000-0000-000000000001', 'duas-partidas', 'live',
        'Dublin', 'Ireland', 24, 'Europe/Dublin')
on conflict (id) do nothing;
insert into listing_versions (listing_id, version, payload, status, reviewed_at)
values ('bbbbbbbb-0000-0000-0000-000000000001', 1, '{"title":"t"}'::jsonb,
        'approved', now())
on conflict do nothing;

select definir_partidas('bbbbbbbb-0000-0000-0000-000000000001',
                        array['08:00','17:00']::time[]) as horas_activas;

\echo ''
\echo '--- 1. O dia de amanha: a conta e por partida e nao por dia'
\echo '    (depende da hora a que este teste corre, e e exatamente esse o ponto)'
select to_char(now(), 'HH24:MI') as agora_utc,
       (select count(*) from partidas_possiveis(
          'bbbbbbbb-0000-0000-0000-000000000001', current_date + 1))
         as partidas_possiveis_amanha,
       (select string_agg(starts_at::text, ', ' order by starts_at)
        from partidas_possiveis(
          'bbbbbbbb-0000-0000-0000-000000000001', current_date + 1))
         as quais;

\echo ''
\echo '--- 2. Daqui a uma semana as duas partidas servem'
select string_agg(starts_at::text, ', ' order by starts_at) as quais
from partidas_possiveis('bbbbbbbb-0000-0000-0000-000000000001',
                        current_date + 7);

\echo ''
\echo '--- 3. Com um aviso de 10 dias, uma semana ja nao chega'
update listings set lead_time_hours = 240
 where id = 'bbbbbbbb-0000-0000-0000-000000000001';
select count(*) as partidas_daqui_a_uma_semana
from partidas_possiveis('bbbbbbbb-0000-0000-0000-000000000001',
                        current_date + 7);
select count(*) as dias_na_proxima_semana
from dias_abertos('duas-partidas', current_date + 1, current_date + 7);
update listings set lead_time_hours = 24
 where id = 'bbbbbbbb-0000-0000-0000-000000000001';

\echo ''
\echo '--- 4. Fechar o dia no anuncio tira as partidas todas'
select marcar_dias('bbbbbbbb-0000-0000-0000-000000000001',
                   array[(current_date + 7)::date], 'closed');
select count(*) as partidas_no_dia_fechado
from partidas_no_dia('duas-partidas', current_date + 7);
select marcar_dias('bbbbbbbb-0000-0000-0000-000000000001',
                   array[(current_date + 7)::date], 'open');

\echo ''
\echo '--- 5. Tirar uma partida desativa-a, nao a apaga'
select definir_partidas('bbbbbbbb-0000-0000-0000-000000000001',
                        array['17:00']::time[]) as horas_activas;
select starts_at, active from listing_times
 where listing_id = 'bbbbbbbb-0000-0000-0000-000000000001'
 order by starts_at;
\echo '    e volta a entrar sem perder o historico'
select definir_partidas('bbbbbbbb-0000-0000-0000-000000000001',
                        array['08:00','17:00']::time[]) as horas_activas;

\echo ''
\echo '--- 6. O pedido recusa uma partida que ja nao e possivel'
do $$
begin
  perform registar_pedido(jsonb_build_object(
    'name', 'Alguem', 'email', 'a@b.invalid',
    'listing_slug', 'duas-partidas',
    'wanted_on', current_date::text, 'wanted_at', '08:00'));
  raise exception 'FALHOU: aceitou uma partida de hoje com 24h de aviso';
exception
  when others then
    if sqlerrm like '%no longer possible%' or sqlerrm like '%notice%' then
      raise notice 'ok: recusou com "%"', left(sqlerrm, 70);
    else raise;
    end if;
end $$;

\echo ''
\echo '    ...e aceita uma que e possivel, guardando a hora'
select registar_pedido(jsonb_build_object(
  'name', 'Alguem', 'email', 'c@d.invalid',
  'listing_slug', 'duas-partidas',
  'wanted_on', (current_date + 10)::text, 'wanted_at', '17:00')) is not null
  as aceitou;
select wanted_on, wanted_at from enquiries where email = 'c@d.invalid';

\echo ''
\echo '--- 7. Um tour sem horas registadas continua pela regra do dia inteiro'
insert into listings (id, operator_id, slug, status, city, country,
                      lead_time_hours)
values ('bbbbbbbb-0000-0000-0000-000000000002',
        'aaaaaaaa-0000-0000-0000-000000000001', 'sem-horas', 'live',
        'Dublin', 'Ireland', 24)
on conflict (id) do nothing;
insert into listing_versions (listing_id, version, payload, status, reviewed_at)
values ('bbbbbbbb-0000-0000-0000-000000000002', 1, '{"title":"t"}'::jsonb,
        'approved', now())
on conflict do nothing;
select (select count(*) from dias_abertos('sem-horas', current_date + 1, current_date + 1)) as amanha,
       (select count(*) from dias_abertos('sem-horas', current_date + 5, current_date + 5)) as daqui_a_cinco_dias;

\echo ''
\echo '--- 8. O fuso conta: o mesmo tour em Auckland nao tem as mesmas partidas'
update listings set timezone = 'Pacific/Auckland'
 where id = 'bbbbbbbb-0000-0000-0000-000000000001';
select count(*) as partidas_amanha_em_auckland
from partidas_possiveis('bbbbbbbb-0000-0000-0000-000000000001',
                        current_date + 1);
update listings set timezone = 'Europe/Dublin'
 where id = 'bbbbbbbb-0000-0000-0000-000000000001';

\echo ''
\echo '--- 9. Um fuso inventado e recusado pela base'
do $$
begin
  update listings set timezone = 'Europe/Narnia'
   where id = 'bbbbbbbb-0000-0000-0000-000000000001';
  raise exception 'FALHOU: aceitou um fuso que nao existe';
exception
  when others then
    if sqlerrm like '%Narnia%' or sqlerrm like '%fuso_existe%'
       or sqlerrm like '%time zone%' then
      raise notice 'ok: recusou o fuso inventado';
    else raise;
    end if;
end $$;

rollback;
