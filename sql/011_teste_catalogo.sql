-- =====================================================================
-- O catalogo publico, posto a prova
--
-- Prova que so sai da base o que deve sair: tours no ar, de operadores
-- aprovados, na versao aprovada. E que nao sai o email do operador, nem
-- a comissao, nem a matricula de um veiculo.
-- =====================================================================
\set ON_ERROR_STOP on
\pset pager off
begin;

insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'ana@exemplo.invalid')
on conflict do nothing;

insert into operators (id, name, country, city, email, phone, status,
                       approved_at, commission_rate)
values ('aaaaaaaa-0000-0000-0000-000000000001', 'Ana Tours', 'Ireland',
        'Dublin', 'segredo@exemplo.invalid', '+353000', 'approved', now(), 0.25),
       ('aaaaaaaa-0000-0000-0000-000000000002', 'Por Aprovar Lda', 'Ireland',
        'Cork', 'outro@exemplo.invalid', null, 'pending', null, 0.20)
on conflict (id) do nothing;

insert into listings (id, operator_id, slug, status, city, country, lead_time_hours)
values
  ('bbbbbbbb-0000-0000-0000-000000000001','aaaaaaaa-0000-0000-0000-000000000001','no-ar','live','Dublin','Ireland',48),
  ('bbbbbbbb-0000-0000-0000-000000000002','aaaaaaaa-0000-0000-0000-000000000001','rascunho','draft','Dublin','Ireland',24),
  ('bbbbbbbb-0000-0000-0000-000000000003','aaaaaaaa-0000-0000-0000-000000000002','de-nao-aprovado','live','Cork','Ireland',24)
on conflict (id) do nothing;

-- O "no-ar" tem a v1 aprovada e uma v2 por rever. Sai a v1.
insert into listing_versions (listing_id, version, payload, status, reviewed_at)
values ('bbbbbbbb-0000-0000-0000-000000000001', 1,
        '{"title":"A versao aprovada","slug":"no-ar","lede":"x"}'::jsonb,
        'approved', now())
on conflict do nothing;
insert into listing_versions (listing_id, version, payload, status)
values ('bbbbbbbb-0000-0000-0000-000000000001', 2,
        '{"title":"A versao por rever","slug":"no-ar"}'::jsonb, 'pending')
on conflict do nothing;
insert into listing_versions (listing_id, version, payload, status, reviewed_at)
values ('bbbbbbbb-0000-0000-0000-000000000002', 1, '{"title":"Rascunho"}'::jsonb,'approved', now()),
       ('bbbbbbbb-0000-0000-0000-000000000003', 1, '{"title":"De nao aprovado"}'::jsonb,'approved', now())
on conflict do nothing;

insert into vehicles (id, operator_id, name, max_pax, plate)
values ('cccccccc-0000-0000-0000-000000000001',
        'aaaaaaaa-0000-0000-0000-000000000001', 'V-Class', 6, '191-D-SEGREDO')
on conflict (id) do nothing;
insert into listing_vehicles values
  ('bbbbbbbb-0000-0000-0000-000000000001','cccccccc-0000-0000-0000-000000000001')
on conflict do nothing;
select definir_partidas('bbbbbbbb-0000-0000-0000-000000000001',
                        array['08:00','14:30']::time[]);

\echo ''
\echo '--- 1. So sai o que esta no ar, de operador aprovado'
select slug, operator_name, version, payload->>'title' as titulo
from catalogo_publico();

\echo ''
\echo '--- 2. Sai a versao APROVADA e nao a que esta por rever'
select (payload->>'title' = 'A versao aprovada') as sai_a_aprovada
from catalogo_publico() where slug = 'no-ar';

\echo ''
\echo '--- 3. Sai a frota em numeros, nao em matriculas'
select start_times, max_pax, vehicles, lead_time_hours, timezone
from catalogo_publico() where slug = 'no-ar';

\echo ''
\echo '--- 4. NAO sai nada que seja do operador e nao do publico'
select
  (select count(*) from catalogo_publico() c
    where c::text like '%segredo@exemplo.invalid%') as emails_expostos,
  (select count(*) from catalogo_publico() c
    where c::text like '%0.25%') as comissoes_expostas,
  (select count(*) from catalogo_publico() c
    where c::text like '%SEGREDO%') as matriculas_expostas;

\echo ''
\echo '--- 5. Quem nao assinou consegue ler o catalogo (e tem de conseguir)'
set local role anon;
select count(*) as tours_que_o_publico_ve from catalogo_publico();
\echo '    ...mas continua sem ver a tabela por tras'
do $$
begin
  perform count(*) from operators;
  raise notice 'ATENCAO: o anon consegue ler operators';
exception when others then
  raise notice 'ok: o anon nao le operators (%)', left(sqlerrm, 40);
end $$;
reset role;

\echo ''
\echo '--- 6. Suspender o operador tira os tours dele do catalogo'
update operators set status = 'suspended'
 where id = 'aaaaaaaa-0000-0000-0000-000000000001';
select count(*) as no_catalogo_depois_de_suspender from catalogo_publico();

rollback;
