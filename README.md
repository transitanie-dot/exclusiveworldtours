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
tools/tours.json      o catalogo: 36 tours, 6 paises, precos, itinerarios
tools/artigos.json    os artigos do /journal/
tools/politica.py     a politica de cancelamento (24h), num sitio so
tools/ligacao.py      o endereco da base e a chave publica
assets/atlas.json     coordenadas das 19 cidades e geometria dos paises
sql/                  o modelo de dados, por ordem de aplicacao
```

### Gerar

```bash
python3 tools/gerar.py          # tudo, e verifica no fim
python3 tools/gerar.py -v       # com a lista de ficheiros
```

Depois, o que so corre no browser:

```bash
node tools/testar_portal.mjs    # 15 testes ao portal, com a base simulada
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
| `/portal/calendar/` | o calendario | `portal_calendario.py` |
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

### O caminho publico

Com RLS ligado, o visitante nao le nenhuma tabela. O que ele pode fazer
sao quatro funcoes, e nada mais:

| Funcao | Para que serve |
|---|---|
| `dias_abertos` | os dias livres de um tour, para a pagina do tour |
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
