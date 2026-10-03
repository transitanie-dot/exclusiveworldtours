-- =====================================================================
-- A conta do Ricardo, e porque e que ela foi criada a mao
--
-- Normalmente uma conta nasce de um registo no browser, e esse registo
-- manda um email de confirmacao. O servidor de email que o Supabase da
-- por omissao so entrega a enderecos que sao membros da organizacao
-- Supabase — qualquer outro falha com "Email address not authorized".
-- O endereco do Ricardo e de fora, por isso nem o registo nem a ligacao
-- de entrada lhe chegavam.
--
-- Isto e um ARRANQUE e nao um padrao. Os operadores entram pela
-- candidatura, e quando o projeto tiver servidor de email proprio
-- (Resend, a espera dos registos DNS do dominio) tudo isto passa a
-- acontecer pelo caminho normal.
--
-- A palavra-passe nao esta aqui escrita, de proposito: foi definida uma
-- vez, entregue ao Ricardo, e ele muda-a em /portal/account/. Este
-- ficheiro fica como registo do que foi feito e porque.
-- =====================================================================

-- O endereco dele passa a estar na lista de administradores. A partir
-- daqui, se a conta for recriada um dia, e promovida sozinha.
insert into admin_emails (email, nota)
values ('ricardomachado_3160@hotmail.com', 'o endereco pessoal do Ricardo')
on conflict (email) do nothing;

-- O que foi corrido, com a palavra-passe substituida:
--
--   update auth.users
--      set encrypted_password = crypt('<a palavra-passe>', gen_salt('bf')),
--          email_confirmed_at = coalesce(email_confirmed_at, now()),
--          raw_app_meta_data  = '{"provider":"email","providers":["email"]}'::jsonb,
--          updated_at         = now()
--    where lower(email) = 'ricardomachado_3160@hotmail.com';
--
-- Notas de quem vier a repetir isto:
--
--   * `confirmed_at` e uma coluna GERADA a partir de email_confirmed_at.
--     Tentar escrever nela da "can only be updated to DEFAULT".
--   * sem uma linha em `auth.identities` com provider 'email', a entrada
--     por palavra-passe falha sem dizer porque.
--   * o trigger promover_admin so dispara em INSERT. Numa conta que ja
--     existia, a linha em `admins` tem de ser posta a mao.

insert into admins (user_id)
select u.id from auth.users u
join admin_emails a on lower(a.email) = lower(u.email)
on conflict (user_id) do nothing;
