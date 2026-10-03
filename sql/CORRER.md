# Como correr isto

## No Supabase (a sério)

O ficheiro `001_marketplace.sql` corre do princípio ao fim numa base
vazia, e pode voltar a correr sem estragar nada. No Supabase, cola-se no
editor de SQL ou aplica-se como migração.

Depois, para te tornares administrador — sem isto não consegues rever
nada:

```sql
insert into admins (user_id) values ('<o teu id em auth.users>');
```

## Em local, para testar

O Supabase traz o esquema `auth` e a função `auth.uid()`. Numa base
vazia não existem, por isso `000_supabase_simulado.sql` cria o mínimo
para o resto correr. **Não é para correr no Supabase** — lá já existe.

```bash
initdb -D data -U postgres --auth=trust
pg_ctl -D data -o "-k . -p 5433" start
psql -h . -p 5433 -U postgres -v ON_ERROR_STOP=1 \
     -f 000_supabase_simulado.sql -f 001_marketplace.sql -f 002_teste_regras.sql
```

## O que o teste prova

As regras de acesso não se verificam a olho. `002_teste_regras.sql` monta
um administrador e dois operadores e passa por dez cenários. Os que
interessam:

| | Cenário | Tem de acontecer |
|---|---|---|
| 2 | Conteúdo submetido e por rever | **Não** aparece no site |
| 3 | Operador aprova a própria versão | Erro |
| 4 | Operador lista anúncios | Vê só os dele |
| 5 | Operador mexe no calendário de outro | Erro |
| 9 | Dia fechado, dia livre, dia passado | `f`, `t`, `f` |
| 10 | Submissão nova por rever | A versão no ar **não** muda |

Se algum destes deixar de passar, há um buraco de segurança — não é um
teste cosmético.
