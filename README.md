# exclusiveworldtours.com

Marketplace de tours privados de um dia. Site estatico, servido no Render.

## Como esta construido

O site e gerado por scripts Python a partir de dados, e nao escrito a mao.
O Render **nao** corre nada: os scripts correm localmente e o HTML gerado
vai para o Git como qualquer outro ficheiro.

```
tools/tours.json     o catalogo: 36 tours, 6 paises, precos, itinerarios
assets/atlas.json    as coordenadas das 19 cidades e a geometria dos paises
tools/atlas.py       gera o atlas.json (GeoNames + Natural Earth)
tools/home3.py       gera a index.html
tools/logos.py       gera a /logos/, as propostas de logotipo
index.html           a homepage, gerada — nao editar a mao
logos/index.html     propostas de logotipo, gerada — noindex
```

## Gerar o site

```bash
python3 tools/home3.py              # escreve index.html (producao)
python3 tools/home3.py --revisao    # escreve index-marketplace.html, com a
                                    # barra de paletas e o diagnostico de
                                    # fotografias, para rever
python3 tools/logos.py              # escreve logos/index.html
```

O `atlas.json` so precisa de ser regenerado se mudarem as cidades de
partida:

```bash
npm install world-atlas
pip install geonamescache
WORLD_ATLAS=./node_modules/world-atlas/countries-50m.json python3 tools/atlas.py
```

## Regras

1. **Nada de segredos no repositorio.** O site e servido com
   `publishPath: "."` — todo o ficheiro aqui dentro e publico pelo URL.
   Chaves de API vivem nas Environment Variables do Render.
2. **Nao editar a `index.html` a mao.** E gerada. Edita-se o `tours.json`
   ou o `home3.py` e corre-se o gerador.
3. **Nao inventar factos.** Precos, horarios, capacidades, avaliacoes,
   numeros de registo: se faltar, pergunta-se e deixa-se por fazer.
4. **Sem avaliacoes.** A marca e nova e nao tem nenhuma. Nao se inventam,
   nem como exemplo.
5. **Acessibilidade AA.** Qualquer alteracao passa pelo axe antes de ir
   para o `main`: 0 violacoes WCAG 2.1 A/AA a 1440, 768 e 390 px.

## Fotografia

As fotografias sao do Unsplash e sao **provisorias**, ate haver fotografia
propria dos operadores. Estao todas numa tabela so, a `FOTOS` no
`tools/home3.py`: troca-se o identificador e mais nada. Os creditos aos
fotografos no fim da pagina sao gerados dessa mesma tabela.

## Por decidir

- O logotipo: seis propostas em /logos/, por escolher. A paleta sai da
  marca depois de escolhida, e nao antes.
- A paleta: as tres do gerador (indigo, petroleo, magenta) foram todas
  rejeitadas. A de producao e a indigo, provisoria.
- Os precos de 22 dos 36 tours sao de teste e esperam confirmacao.
- Os operadores de cada tour ainda nao estao nomeados.
- O numero de WhatsApp e o email da marca.
