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
         017_reservas.sql 018_teste_reservas.sql \
         020_epocas.sql 021_teste_epocas.sql 022_teste_anon.sql; do
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

**O varrimento do `anon` é o último ficheiro.** O `022_teste_anon.sql`
corre *todas* as funções públicas como `anon`, por isso tem de vir depois
de todas elas. Chamou-se `016`, depois `019`, e agora `022` — muda de número sempre que
uma migração nova traz funções públicas. Quando acrescentares uma migração
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

## Épocas, promoções e faltas (020 / 021)

O `020_epocas.sql` troca o modelo do calendário: deixa de ser uma linha
por dia e passa a ser **aberto por regra, fechado por excepção** — o
modelo da Viator, que está certo. Uma época é um intervalo de datas ×
dias da semana × horas de partida, e "segunda a sexta, Junho a Setembro,
às 09:00 e às 14:00" passa a ser uma linha em vez de noventa cliques.

Três coisas que não se mudam sem bom motivo:

**Uma época sem data de fim rola para a frente, 400 dias.** É a única
defesa contra o modo de falha mais comum de um marketplace: o anúncio
cuja disponibilidade se esgota em silêncio e ninguém dá por isso até as
vendas pararem.

**A migração não parte quem ainda não tem épocas.** Um anúncio só com
`listing_times` continua a responder exactamente como antes, e a `020`
cria-lhe uma época aberta a partir das horas que já tinha. A
`listing_times` **não se apaga** — fica sem ninguém a ler até se
confirmar que as épocas correm bem. Apagar a fonte no mesmo dia em que se
muda o leitor é cortar o ramo onde se está sentado.

**O modo do horário muda-se a qualquer momento.** A Viator torna a
escolha irreversível, e isso é uma decisão tomada no dia 1 com a menor
informação que a pessoa vai ter na vida.

| | O que o `021` prova | Porque interessa |
|---|---|---|
| 1-2 | Uma frase produz o calendário certo, e as horas são da época | Ninguém faz a mesma hora em Janeiro e em Agosto |
| 3 | Uma época sem fim abre até ao fim do calendário | O anúncio não se esgota em silêncio |
| 4 | Um dia fechado é uma excepção e não mexe na regra | |
| 5 | Um bebé ao colo não ocupa lugar nem muda o preço | O preço é do veículo — é o argumento central do site |
| 6 | A promoção precisa das **duas** janelas (reserva e viagem) | "Reserva até sexta, viaja no Verão" |
| 7 | Quem paga o desconto muda a repartição | Uma campanha nossa não corta a margem do operador |
| 8 | Motorista à disposição devolve uma janela, não uma hora inventada | |
| 9-10 | Uma falta exige minutos e texto, e não se regista antes do tour | É o registo feito no dia que ganha uma disputa de cartão |
| 11 | Um operador não vê nem mexe nas épocas de outro | |
| 12 | Quem ainda não migrou continua a vender | |
