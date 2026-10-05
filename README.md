# exclusiveworldtours.com

Marketplace de tours privados de um dia. Site estatico servido no Render,
com uma base de dados Supabase por tras para o portal dos operadores e a
area de administracao.

## Como esta construido

O site e gerado por scripts Python a partir de dados, e nao escrito a
mao. O Render **nao** corre nada: os scripts correm localmente e o HTML
gerado vai para o Git como qualquer outro ficheiro.

```
tools/gerar.py        gera o site todo, pela ordem certa, e verifica-o
tools/puxar.py        puxa da base os tours dos operadores aprovados
tools/tours.json      o catalogo escrito a mao: 36 tours, 6 paises
tools/tours-operadores.json   o que veio da base. GERADO, nao editar
tools/artigos.json    os artigos do /journal/
tools/politica.py     a politica de cancelamento (24h), num sitio so
tools/ligacao.py      o endereco da base e a chave publica
assets/atlas.json     coordenadas das 19 cidades e geometria dos paises
sql/                  o modelo de dados, por ordem de aplicacao
```

### Gerar

```bash
python3 tools/puxar.py --ver    # o que mudaria, sem escrever nada
python3 tools/puxar.py          # puxa os tours dos operadores
python3 tools/gerar.py          # gera tudo, e verifica no fim
python3 tools/gerar.py -v       # com a lista de ficheiros
```

O `puxar.py` e um passo a parte e nao entra no `gerar.py` de proposito:
precisa de rede, e gerar o site tem de funcionar sem ela. Correr so o
`gerar.py` reaproveita o que o ultimo `puxar.py` escreveu.

Depois, o que so corre no browser:

```bash
node tools/testar_portal.mjs    # 31 testes ao portal, com a base simulada
node tools/acessibilidade.mjs   # axe em 1440, 768 e 390 px
```

O `atlas.json` so precisa de ser regenerado se mudarem as cidades de
partida:

```bash
npm install world-atlas
pip install geonamescache
WORLD_ATLAS=./node_modules/world-atlas/countries-50m.json python3 tools/atlas.py
```

A biblioteca do Supabase esta alojada no proprio site, em
`assets/lib/supabase.js`, para o portal nao depender de um CDN. Para a
actualizar:

```bash
npm install @supabase/supabase-js
cp node_modules/@supabase/supabase-js/dist/umd/supabase.js assets/lib/supabase.js
```

## As paginas

| Morada | O que e | Gerada por |
|---|---|---|
| `/` | homepage | `home.py` |
| `/tours/`, `/search/` | resultados e catalogo | `resultados.py` |
| `/tours/<slug>/` | as 36 paginas de tour | `tour.py` |
| `/journal/` | o blog | `blog.py` |
| `/cancellation/` | a politica | `paginas_simples.py` |
| `/suppliers/` | angariacao de operadores | `fornecedores.py` |
| `/suppliers/apply/`, `/contact/` | os formularios | `formularios.py` |
| `/portal/` | entrada e painel do operador | `portal.py` |
| `/portal/listing/` | o editor de anuncios | `portal_anuncio.py` |
| `/portal/calendar/` | o calendario dos tours | `portal_calendario.py` |
| `/portal/fleet/` | a frota e o calendario de cada veiculo | `portal_frota.py` |
| `/portal/account/` | a conta do operador | `portal_conta.py` |
| `/admin/` | a fila de revisao | `admin.py` |
| `/admin/operators/`, `/admin/searches/` | as listas | `admin_listas.py` |

`tools/home3.py` e a homepage **anterior**, com a marca indigo de antes
de o A5 ser escolhido. Escreve para o mesmo `index.html`, por isso
corre-la publica a marca velha. Fica no repositorio como historico; quem
gera o site usa o `gerar.py`.

## A base de dados

Projeto Supabase `lmrvoakknsrypoeqmjbr`, regiao eu-west-1 (Irlanda).

Os ficheiros em `sql/` correm por ordem e podem voltar a correr sem
estragar nada. O `002_teste_regras.sql` nao e uma migracao: sao dez
cenarios de controlo de acesso que se correm contra um Postgres local
(ver `sql/CORRER.md`).

A ideia que manda no modelo: os dados tem dois ritmos. O **conteudo** e
lento, passa por revisao e e publicado em paginas estaticas; a
**disponibilidade** e rapida, nao passa por revisao nenhuma e e lida ao
vivo. Um calendario que esperasse por aprovacao mostrava disponibilidade
falsa durante horas, e isso nao e um atraso — e uma reserva que vai ter
de ser cancelada.

### A frota: capacidade partilhada de verdade

E aqui que este marketplace faz uma coisa que a GetYourGuide **avisa
expressamente para nao se tentar**. Vale a pena perceber porque.

A disponibilidade da GYG e lida de cache e sondada por intervalos (uma
vez por dia nos proximos 30 dias). Por isso a documentacao deles diz que
partilhar capacidade entre produtos "can lead to inconsistencies" e que
"cached availability won't reflect bookings made for other options". Um
operador deles com uma carrinha e tres tours tem de fingir que tem tres
carrinhas, ou fechar os outros dois a mao sempre que vende um.

Aqui a disponibilidade e lida **ao vivo**, no momento em que o cliente
escolhe a data. Por isso o recurso pode ser partilhado a serio:

```
vehicles          a frota do operador: nome, lugares, matricula
listing_vehicles  que veiculos servem que anuncio (muitos para muitos)
vehicle_days      o veiculo esta livre, ocupado ou indisponivel nesse dia
```

Fecha-se a carrinha no dia 12 e ela sai dos tres tours ao mesmo tempo,
sozinha. Se so sobrar o sedan, o tour continua a vender mas **ate tres
pessoas em vez de seis** — e e isso que a pagina do tour diz ao cliente.

Sao duas perguntas diferentes e por isso duas tabelas:

| Tabela | Pergunta | Afeta |
|---|---|---|
| `vehicle_days` | o veiculo esta ocupado? | todos os anuncios que o usam |
| `availability` | este tour corre neste dia? | so esse anuncio |

Um operador que ainda nao registou frota nenhuma continua a vender pelo
calendario do anuncio: uma funcionalidade nova nao pode tirar vendas a
quem ainda nao a usa.

### As horas de partida, e o lead time exacto

`listing_times` guarda as horas a que cada tour parte, e `listings.timezone`
diz em que fuso essas horas sao lidas. Sem o fuso, "parte as 8h" nao quer
dizer nada: o servidor corre em UTC e o cliente pode estar no Brasil.

Com horas registadas, o aviso minimo deixa de arredondar: compara-se o
INSTANTE da partida com o instante do pedido, partida a partida. O mesmo
dia pode ter a das 8h fechada e a das 17h aberta — e e assim que um tour
que parte ao fim da tarde deixa de perder um dia de calendario por causa
de uma conta grosseira.

Sem horas registadas, mantem-se a regra antiga do dia inteiro. Um
operador que ainda nao as registou nao fica pior do que estava.

**As horas sao disponibilidade, nao conteudo.** Vivem no calendario e nao
no editor de anuncios, e nao passam por revisao. Um cliente ve a hora, por
isso a tentacao e trata-la como conteudo — seria o mesmo erro que fazer o
calendario passar pela revisao. Um operador que muda a partida de amanha
das 8h para as 9h, porque o motorista adoeceu, nao pode esperar por
ninguem. A GetYourGuide chega a mesma conclusao: os time slots deles
vivem em Manage > Availability.

Tirar uma hora desativa-a, nao a apaga: um pedido antigo pode apontar
para ela, e a linha tem de continuar a fazer sentido daqui a um mes.

### O lead time nao tem tecto

`listings.lead_time_hours`, por omissao 24. A GYG impoe que o cut-off
**nao pode exceder 10 horas**, porque vive de reservas de ultima hora.
Um motorista nao se arranja em 10 horas. Aqui o operador poe 24, 48 ou
168 e ninguem lhe diz que nao pode.

A conta arredonda para cima, ao dia inteiro, e isso e deliberado: um
anuncio ainda nao guarda a hora de partida. Aceitar amanha as 13h de
hoje com 24 horas de aviso seria aceitar uma partida que pode ser as 8h
— 19 horas, nao 24. Entre prometer a mais e prometer a menos, prometer a
mais custa um cancelamento.

A regra esta nos dois sitios onde tem de estar: `dias_abertos()` esconde
o dia, e `registar_pedido()` recusa o pedido. Se so estivesse na pagina,
bastava abrir as ferramentas do browser para a saltar.

### Como um tour de um operador chega ao site

Este era o buraco mais grave do sistema: um operador submetia, era
aprovado, e o tour dele nao aparecia em lado nenhum, porque nenhum
gerador lia da base. O portal e a fila de revisao eram teatro.

```
  operador submete  ->  listing_versions (pending)
  Ricardo aprova    ->  listing_versions (approved)  [/admin/]
  python3 tools/puxar.py   ->  tools/tours-operadores.json
  python3 tools/gerar.py   ->  tours/<slug>/index.html
  git push                 ->  no ar
```

`catalogo_publico()` e a unica porta por onde o conteudo sai da base. E
uma funcao e nao uma vista aberta pela razao de sempre: por baixo de
`public_listings` esta `operators`, que tem email, telefone e a taxa de
comissao. Ha um teste que verifica que nenhuma dessas coisas sai
(`sql/011_teste_catalogo.sql`).

**O gerador nao precisa de chave de servico.** Tudo o que ele le vai
acabar numa pagina publica, por isso corre com a chave publicavel, como
o resto do site.

Dois ficheiros e nao um: `tours.json` e escrito a mao e nunca e tocado
por um guiao; `tours-operadores.json` e substituido inteiro em cada
corrida. Se fossem um so, um erro de rede podia apagar conteudo escrito
a mao, e isso descobria-se tarde.

O que vem da base passa por `limpar()` antes de ser escrito: cortes de
tamanho, escaloes de preco absurdos descartados um a um, fotografias so
por https. O conteudo foi escrito por um operador, e um gerador que
confia em texto de fora e um gerador que publica o que lhe mandarem.
`tools/testar_puxar.py` poe isso a prova, incluindo um titulo de quatro
mil caracteres e uma etiqueta `<script>` no meio da descricao.

### O caminho publico

Com RLS ligado, o visitante nao le nenhuma tabela. O que ele pode fazer
sao quatro funcoes, e nada mais:

| Funcao | Para que serve |
|---|---|
| `dias_abertos` | que dias posso ir — a consulta do calendario |
| `frota_no_dia` | o que ha neste dia: veiculos livres, maior lotacao, preco |
| `partidas_no_dia` | que partidas desse dia ainda estao dentro do prazo |
| `catalogo_publico` | os tours no ar, para o gerador do site |
| `catalogo_mudou_em` | quando foi a ultima aprovacao, para saber se vale a pena gerar |
| `registar_procura` | regista o que foi procurado (escreve, nao le) |
| `registar_pedido` | o formulario de contacto |
| `candidatar_operador` | a candidatura de um operador |

A comissao e **20%** (decidida a 2 de outubro de 2026). Vive em
`operators.commission_rate`, por operador, e a conta faz-se chamando
`repartir(operador, total)` — num sitio so, para o portal, a faturacao e
os relatorios nunca darem numeros diferentes.

### O primeiro administrador

`admin_emails` tem a lista de enderecos que sao administradores. Quem
entrar com um deles e promovido automaticamente, por um trigger. Sem
isto nao havia maneira de nomear o primeiro: `admins` aponta para
`auth.users`, e `auth.users` so tem alguem depois de essa pessoa entrar.

## Regras

1. **Nada de segredos no repositorio.** O site e servido com
   `publishPath: "."` — todo o ficheiro aqui dentro e publico pelo URL.
   A chave que esta no `ligacao.py` e a **publicavel**, que e desenhada
   para ir no browser e sozinha nao da acesso a nada; o que protege os
   dados e o RLS. A chave de **servico** ignora o RLS e nunca entra aqui
   — vive nas Environment Variables do Render. O `verificar.py` recusa
   qualquer pagina onde apareca.
2. **Nao editar a mao as paginas geradas.** Edita-se o `tours.json`, o
   `artigos.json` ou o gerador, e corre-se o `gerar.py`.
3. **Nao inventar factos.** Precos, horarios, capacidades, avaliacoes,
   numeros de registo: se faltar, pergunta-se e deixa-se por fazer.
4. **Sem avaliacoes.** A marca e nova e nao tem nenhuma. Nao se
   inventam, nem como exemplo.
5. **Acessibilidade AA.** Qualquer alteracao passa pelo axe antes de ir
   para o `main`: 0 violacoes WCAG 2.1 A/AA a 1440, 768 e 390 px.
6. **Nao fundir para `main` sem o Ricardo.** O `main` publica.

## Fotografia

As fotografias sao do Unsplash e sao **provisorias**, ate haver
fotografia propria dos operadores. Os creditos aos fotografos no fim da
pagina sao gerados da mesma tabela que as imagens.

No container onde isto e desenvolvido o dominio do Unsplash esta
bloqueado, por isso as fotografias **nao aparecem** nas capturas de ecra
feitas aqui. Aparecem no browser do Ricardo. Por baixo de cada
fotografia ha sempre uma cor cheia, para a pagina nunca parecer avariada
quando uma imagem nao carrega.

## Dados de exemplo na base

Ha um operador, um anuncio com duas versoes, uma candidatura e um pedido
de exemplo, para a fila de revisao poder ser vista a funcionar antes de
haver operadores reais. Estao todos marcados com `EXAMPLE`. Apagam-se
com:

```sql
delete from enquiries where name like 'EXAMPLE %';
delete from operator_applications where company like 'EXAMPLE %';
delete from operators where name like 'EXAMPLE %';   -- leva os anuncios atras
```
