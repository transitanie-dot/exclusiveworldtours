-- =====================================================================
-- A frota, posta a prova
--
-- O que se prova aqui e a afirmacao central: uma carrinha ocupada
-- desaparece de TODOS os tours que a usam, ao mesmo tempo, sem ninguem
-- ter de fechar nada a mao. E a GetYourGuide nao faz isto — avisa
-- expressamente contra tentar.
--
--   su postgres -c "psql -h /tmp/pgtest -p 5433 -d t31 -f sql/007_teste_frota.sql"
-- =====================================================================

\set ON_ERROR_STOP on
\pset pager off

begin;

-- --------------------------------------------------------------- cenario
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

-- Dois tours da mesma operadora. Um deles precisa de 48 horas de aviso.
insert into listings (id, operator_id, slug, status, city, country, lead_time_hours)
values
  ('bbbbbbbb-0000-0000-0000-000000000001',
   'aaaaaaaa-0000-0000-0000-000000000001', 'cliffs-dia', 'live',
   'Dublin', 'Ireland', 24),
  ('bbbbbbbb-0000-0000-0000-000000000002',
   'aaaaaaaa-0000-0000-0000-000000000001', 'wicklow-dia', 'live',
   'Dublin', 'Ireland', 48)
on conflict (id) do nothing;

insert into listing_versions (listing_id, version, payload, status, reviewed_at)
select id, 1, '{"title":"t"}'::jsonb, 'approved', now() from listings
on conflict do nothing;

-- UMA carrinha e UM sedan. A carrinha serve os dois tours.
insert into vehicles (id, operator_id, name, max_pax) values
  ('cccccccc-0000-0000-0000-000000000001',
   'aaaaaaaa-0000-0000-0000-000000000001', 'Mercedes V-Class', 6),
  ('cccccccc-0000-0000-0000-000000000002',
   'aaaaaaaa-0000-0000-0000-000000000001', 'Skoda Superb', 3)
on conflict (id) do nothing;

insert into listing_vehicles (listing_id, vehicle_id) values
  ('bbbbbbbb-0000-0000-0000-000000000001', 'cccccccc-0000-0000-0000-000000000001'),
  ('bbbbbbbb-0000-0000-0000-000000000001', 'cccccccc-0000-0000-0000-000000000002'),
  ('bbbbbbbb-0000-0000-0000-000000000002', 'cccccccc-0000-0000-0000-000000000001')
on conflict do nothing;

\echo ''
\echo '--- 1. Com a frota toda livre, os dois tours vendem'
select 'cliffs' as tour, disponivel, veiculos, max_pax
from frota_no_dia('cliffs-dia', current_date + 10);
select 'wicklow' as tour, disponivel, veiculos, max_pax
from frota_no_dia('wicklow-dia', current_date + 10);

\echo ''
\echo '--- 2. A carrinha fica ocupada nesse dia. UMA escritura, dois tours afetados.'
select marcar_veiculo('cccccccc-0000-0000-0000-000000000001',
                      array[(current_date + 10)::date], 'booked',
                      'reserva directa') as dias_marcados;

\echo ''
\echo '    o cliffs continua a vender, mas so ate 3 pessoas (fica o sedan)'
select disponivel, veiculos, max_pax
from frota_no_dia('cliffs-dia', current_date + 10);

\echo ''
\echo '    o wicklow desaparece do calendario sozinho — era a unica carrinha'
select count(*) as dias_disponiveis
from dias_abertos('wicklow-dia', current_date + 10, current_date + 10);
select disponivel, veiculos from frota_no_dia('wicklow-dia', current_date + 10);

\echo ''
\echo '--- 3. O lead time nao tem tecto, e cada tour tem o seu'
\echo '    o cliffs (24h) ja nao aceita amanha...'
select count(*) as amanha_no_cliffs
from dias_abertos('cliffs-dia', current_date + 1, current_date + 1);
\echo '    ...e o wicklow (48h) tambem nao aceita depois de amanha'
select count(*) as depois_de_amanha_no_wicklow
from dias_abertos('wicklow-dia', current_date + 2, current_date + 2);
\echo '    mas daqui a uma semana os dois aceitam'
select (select count(*) from dias_abertos('cliffs-dia', current_date + 7, current_date + 7)) as cliffs,
       (select count(*) from dias_abertos('wicklow-dia', current_date + 7, current_date + 7)) as wicklow;

\echo ''
\echo '--- 4. O pedido respeita o lead time, mesmo vindo de fora da pagina'
do $$
begin
  perform registar_pedido(jsonb_build_object(
    'name', 'Alguem', 'email', 'a@b.invalid',
    'listing_slug', 'wicklow-dia',
    'wanted_on', (current_date + 1)::text));
  raise exception 'FALHOU: aceitou um pedido dentro do lead time';
exception
  when others then
    if sqlerrm like '%48 hours notice%' then
      raise notice 'ok: recusou com "%"', left(sqlerrm, 60);
    else
      raise;
    end if;
end $$;

\echo ''
\echo '--- 5. Ferias do operador tapam a frota toda'
insert into blackouts (operator_id, starts_on, ends_on, reason)
values ('aaaaaaaa-0000-0000-0000-000000000001',
        current_date + 20, current_date + 25, 'ferias');
select (select count(*) from dias_abertos('cliffs-dia', current_date + 20, current_date + 25)) as cliffs_em_ferias,
       (select count(*) from dias_abertos('wicklow-dia', current_date + 20, current_date + 25)) as wicklow_em_ferias;

\echo ''
\echo '--- 6. Um operador sem frota registada continua a vender pelo calendario do anuncio'
insert into listings (id, operator_id, slug, status, city, country, lead_time_hours)
values ('bbbbbbbb-0000-0000-0000-000000000003',
        'aaaaaaaa-0000-0000-0000-000000000001', 'sem-frota', 'live',
        'Dublin', 'Ireland', 24)
on conflict (id) do nothing;
insert into listing_versions (listing_id, version, payload, status, reviewed_at)
values ('bbbbbbbb-0000-0000-0000-000000000003', 1, '{"title":"t"}'::jsonb,
        'approved', now())
on conflict do nothing;
select count(*) as dias_na_proxima_semana
from dias_abertos('sem-frota', current_date + 5, current_date + 11);

\echo ''
\echo '--- 7. Um operador nao ve a frota de outro'
insert into auth.users (id, email) values
  ('22222222-2222-2222-2222-222222222222', 'outro@exemplo.invalid')
on conflict do nothing;
set local role authenticated;
set local "teste.uid" = '22222222-2222-2222-2222-222222222222';
select count(*) as veiculos_que_o_outro_ve from vehicles;
reset role;

rollback;
