-- =====================================================================
-- ESTE FICHEIRO CORRE SEMPRE EM ULTIMO, E E DE PROPOSITO
--
-- Chamou-se 016, depois 019, e agora 022. O 017 trouxe a cotar(), que e
-- publica, e o varrimento do anon passou a acusar uma funcao que ainda
-- nao existia — a dizer que estava partida quando o que estava errado
-- era a ordem.
--
-- A numeracao e a ordem de execucao. Este e o ficheiro que verifica
-- TODAS as funcoes publicas de uma vez, por isso tem de vir depois de
-- todas elas: sempre que se acrescentar uma migracao com funcoes
-- publicas novas, este ficheiro muda de numero para continuar a ser o
-- ultimo, e acrescenta-se aqui a funcao nova.
-- =====================================================================
-- =====================================================================
-- Todas as funcoes publicas, corridas como `anon`
--
-- Existe por causa de um bug que quase passou: catalogo_publico() devolvia
-- ZERO LINHAS a quem nao tinha assinado. Nao dava erro — devolvia nada.
-- Um gerador a correr com a chave publicavel teria publicado um site sem
-- um unico tour de operador, e so se descobria quando um operador
-- perguntasse porque e que o tour dele tinha desaparecido.
--
-- A causa: uma funcao `security definer` que le atraves de uma vista
-- `security_invoker` perde os privilegios na fronteira da vista.
--
-- Isto nao se apanha a ler codigo. Apanha-se correndo como anon, que e o
-- que este ficheiro faz — e passa a fazer sempre que alguem acrescentar
-- uma funcao publica.
-- =====================================================================
\set ON_ERROR_STOP on
\pset pager off
begin;

insert into auth.users (id, email) values ('11111111-1111-1111-1111-111111111111','ana@x.invalid')
on conflict do nothing;
insert into operators (id,name,country,city,email,status,approved_at) values
 ('aaaaaaaa-0000-0000-0000-0000000000a1','Ana Tours','Ireland','Galway','ana@x.invalid','approved',now())
on conflict do nothing;
insert into listings (id,operator_id,slug,status,city,country,lead_time_hours) values
 ('bbbbbbbb-0000-0000-0000-0000000000b1','aaaaaaaa-0000-0000-0000-0000000000a1','um-tour','live','Galway','Ireland',24)
on conflict do nothing;
insert into listing_versions (listing_id,version,payload,status,reviewed_at) values
 ('bbbbbbbb-0000-0000-0000-0000000000b1',1,'{"title":"Um tour","slug":"um-tour"}'::jsonb,'approved',now())
on conflict do nothing;
insert into vehicles (id,operator_id,name,max_pax) values
 ('cccccccc-0000-0000-0000-0000000000c1','aaaaaaaa-0000-0000-0000-0000000000a1','V-Class',6)
on conflict do nothing;
insert into listing_vehicles values ('bbbbbbbb-0000-0000-0000-0000000000b1','cccccccc-0000-0000-0000-0000000000c1')
on conflict do nothing;
insert into meeting_points (id,operator_id,name) values
 ('dddddddd-0000-0000-0000-0000000000d1','aaaaaaaa-0000-0000-0000-0000000000a1','A praca')
on conflict do nothing;
update listings set meeting_point_id='dddddddd-0000-0000-0000-0000000000d1'
 where id='bbbbbbbb-0000-0000-0000-0000000000b1';
select definir_partidas('bbbbbbbb-0000-0000-0000-0000000000b1', array['09:00']::time[]);

\echo ''
\echo '=== Como anon, cada funcao publica tem de devolver o que deve ==='
set local role anon;

do $$
declare
  n integer;
  maus text[] := array[]::text[];
begin
  -- Cada linha: o nome, e quantas linhas tem de voltar no minimo.
  select count(*) into n from catalogo_publico();
  if n < 1 then maus := maus || 'catalogo_publico devolveu 0'; end if;

  select count(*) into n from pontos_de_encontro();
  if n < 1 then maus := maus || 'pontos_de_encontro devolveu 0'; end if;

  select count(*) into n from ponto_de_encontro('um-tour');
  if n < 1 then maus := maus || 'ponto_de_encontro devolveu 0'; end if;

  select count(*) into n from dias_abertos('um-tour', current_date, current_date + 30);
  if n < 1 then maus := maus || 'dias_abertos devolveu 0'; end if;

  select count(*) into n from partidas_no_dia('um-tour', current_date + 10);
  if n < 1 then maus := maus || 'partidas_no_dia devolveu 0'; end if;

  select count(*) into n from frota_no_dia('um-tour', current_date + 10);
  if n < 1 then maus := maus || 'frota_no_dia devolveu 0'; end if;

  select count(*) into n from notas_publicas();
  if n < 1 then maus := maus || 'notas_publicas devolveu 0'; end if;

  -- Estas devolvem zero com razao quando nao ha dados, por isso o que se
  -- testa e que nao REBENTAM.
  perform count(*) from avaliacoes_publicas();
  perform catalogo_mudou_em();
  perform registar_procura('dublin', 3, 'Dublin', 'Ireland');

  -- As publicas que a 020 trouxe.
  begin
    perform count(*) from janela_no_dia('x-que-nao-existe', current_date);
  exception when others then maus := maus || ('janela_no_dia: ' || sqlerrm); end;
  begin
    perform count(*) from promocao_para(gen_random_uuid(), current_date);
  exception when others then maus := maus || ('promocao_para: ' || sqlerrm); end;

  -- A cotar() tambem e publica: e a pagina do tour que a chama para
  -- mostrar o preco do grupo escolhido. Se devolvesse zero linhas ao
  -- anon — o erro da 010 — a pagina mostrava "sem preco" a todos os
  -- visitantes e so funcionava para quem tivesse sessao aberta.
  begin
    if not (cotar('{"slug":"x-que-nao-existe","date":"2030-01-01","pax":2}'::jsonb)
             ? 'ok') then
      maus := maus || 'cotar nao devolve ok';
    end if;
  exception when others then maus := maus || ('cotar: ' || sqlerrm); end;

  if array_length(maus, 1) > 0 then
    raise exception 'FUNCOES PUBLICAS PARTIDAS PARA O ANON: %',
      array_to_string(maus, '; ');
  end if;
  raise notice 'ok: as 13 funcoes publicas respondem ao anon';
end $$;

\echo ''
\echo '--- E o que o anon NAO pode fazer continua fechado'
do $$
declare mal text[] := array[]::text[];
begin
  begin perform count(*) from operators;
        mal := mal || 'le operators'; exception when others then null; end;
  begin perform count(*) from reviews;
        mal := mal || 'le reviews'; exception when others then null; end;
  begin perform count(*) from review_invites;
        mal := mal || 'le review_invites'; exception when others then null; end;
  begin perform count(*) from vehicles;
        mal := mal || 'le vehicles'; exception when others then null; end;
  begin perform count(*) from bookings;
        mal := mal || 'le bookings'; exception when others then null; end;
  begin perform count(*) from payment_rules;
        mal := mal || 'le payment_rules'; exception when others then null; end;
  begin perform count(*) from charge_attempts;
        mal := mal || 'le charge_attempts'; exception when others then null; end;

  -- E as funcoes do dinheiro, nenhuma delas publica.
  begin perform reservar('{}'::jsonb);
        mal := mal || 'chama reservar'; exception when others then null; end;
  begin perform confirmar_reserva('{}'::jsonb);
        mal := mal || 'chama confirmar_reserva'; exception when others then null; end;
  begin perform count(*) from reservas_a_cobrar();
        mal := mal || 'chama reservas_a_cobrar'; exception when others then null; end;
  begin perform registar_cobranca('{}'::jsonb);
        mal := mal || 'chama registar_cobranca'; exception when others then null; end;
  begin perform limpar_marcas();
        mal := mal || 'chama limpar_marcas'; exception when others then null; end;

  -- E as da 020. A epoca_do_dia() devolve o id da epoca, a
  -- marcar_falta() escreve na reserva, e nenhuma das duas e assunto de
  -- quem nao assinou.
  begin perform count(*) from epoca_do_dia(gen_random_uuid(), current_date);
        mal := mal || 'chama epoca_do_dia'; exception when others then null; end;
  begin perform marcar_falta(gen_random_uuid(), 10, 'texto suficientemente longo');
        mal := mal || 'chama marcar_falta'; exception when others then null; end;
  begin perform count(*) from listing_seasons;
        mal := mal || 'le listing_seasons'; exception when others then null; end;
  begin perform count(*) from promotions;
        mal := mal || 'le promotions'; exception when others then null; end;

  if array_length(mal, 1) > 0 then
    raise exception 'O ANON VE DEMAIS: %', array_to_string(mal, '; ');
  end if;
  raise notice 'ok: as tabelas continuam fechadas ao anon';
end $$;

reset role;
rollback;
