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

## A ordem importa, e porquê

A numeração é a ordem de execução. Corre tudo de uma vez, numa base
vazia, e corre **duas vezes** — a segunda volta é o que prova que
nenhuma migração estraga uma base que já existe:

```bash
cd sql
for f in 000_supabase_simulado.sql 001_marketplace.sql 002_teste_regras.sql \
         003_caminho_publico.sql 004_candidaturas_e_pedidos.sql \
         006_frota_e_capacidade.sql 007_teste_frota.sql \
         008_horas_de_partida.sql 009_teste_partidas.sql \
         010_catalogo_publico.sql 011_teste_catalogo.sql \
         012_pontos_de_encontro.sql 013_avaliacoes.sql \
         014_avaliacoes_publicas.sql 015_teste_avaliacoes.sql \
         017_reservas.sql 018_teste_reservas.sql 019_teste_anon.sql; do
  psql -h . -p 5433 -U postgres -v ON_ERROR_STOP=1 -f "$f" || break
done
```

Duas regras que saíram de um erro a sério, e que não se mudam sem bom
motivo:

**Um ficheiro de teste não grava nada.** Todos abrem com `begin;` e
fecham com `rollback;`. O `002` não fazia isso, e gravava o utilizador
`1111…` na tabela `admins`. O `015` usa esse mesmo id como *operador* e
tem um teste a provar que um operador não consegue mudar a nota de uma
avaliação — esse teste passava quando corria sozinho e falhava depois do
`002`, porque depois do `002` aquele utilizador era administrador. Um
teste cujo resultado depende da ordem em que corre não é um teste.

**O varrimento do `anon` é o último ficheiro.** O `019_teste_anon.sql`
corre *todas* as funções públicas como `anon`, por isso tem de vir depois
de todas elas. Chamava-se `016` e deu um falso alarme no dia em que o
`017` trouxe uma função pública nova. Quando acrescentares uma migração
com funções públicas, muda o número deste ficheiro para continuar a ser o
último, e acrescenta lá a função nova.

## As reservas e o dinheiro (017 / 018)

O `017_reservas.sql` é a parte do pagamento que tem de ser verdade mesmo
que a Edge Function que fala com o Stripe tenha um erro:

| | O que o `018` prova | Porque é que custa dinheiro |
|---|---|---|
| 1 | O preço vem da base, nunca do pedido | Um preço mudado no browser chegava ao Stripe |
| 2 | "Pagar depois" tem regra e diz a razão | "Não disponível" sem razão parece uma avaria |
| 4 | `later` pedido numa data que não permite sai `now` | Reservava-se um tour de amanhã sem pagar |
| 5 | A repartição fecha, e está gravada na linha | Renegociar a comissão reescrevia o passado |
| 6-7 | Um carro não se vende duas vezes, e uma marca caducada não prende nada | Dois clientes no mesmo carro, ou o dia preso por quem desistiu |
| 8 | Um evento repetido do Stripe não dá duas reservas | O Stripe repete sempre |
| 10-11 | Tentativas espaçadas, e esgotadas voltam o dia à venda | O cron queimava as três tentativas em três horas |
| 12-13 | O operador vê o que recebe, e só as reservas dele | A taxa de comissão de um operador não é assunto de outro |
