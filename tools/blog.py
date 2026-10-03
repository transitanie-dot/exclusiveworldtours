#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""/journal/ — o blog, gerado como tudo o resto.

Nao e um blog de turismo. Nao ha aqui "10 coisas a fazer em Lisboa", nem
horarios de monumentos, nem epocas do ano, porque nada disso foi
verificado por ninguem e um site novo que erra um horario perde a unica
coisa que tem.

O que ha sao artigos sobre o que esta no sistema: como se forma o preco,
o que a palavra "privado" quer dizer aqui, as horas de partida que estao
nos dados, e como um anuncio chega ao site. Todos os numeros que
aparecem sao CALCULADOS a partir do tours.json no momento de gerar — e
nao escritos a mao no texto. Se o catalogo mudar, o artigo muda com ele
e nunca fica a dizer um numero que deixou de ser verdade.

    python3 tools/blog.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import politica  # noqa: E402
import procura  # noqa: E402
from pagina import (CORES, cabecalho, carregar, e, envolver,  # noqa: E402
                    escrever, euros, img, por_pais, rodape)

AQUI = os.path.dirname(os.path.abspath(__file__))


CSS = '''
/* As migalhas do /journal/ ficam sobre fundo claro. A regra que existe
   no tour.py e branca, para o heroi escuro — aqui seria texto branco
   sobre creme, ou seja, invisivel. */
.jtopo .migalhas{font-size:12.5px;color:var(--mudo);margin:0 0 var(--e2)}
.jtopo .migalhas a{color:var(--cor-escura);text-decoration:underline;
  text-decoration-thickness:1px;text-underline-offset:2px}
.jtopo .migalhas a:hover{color:var(--tinta)}

/* O botao secundario: a mesma forma, sem a cor cheia. Nao existia em
   lado nenhum e eu usei-o — ficava com o estilo por omissao do browser. */
.botao-s{background:var(--branco);color:var(--tinta);
  border:1px solid var(--mudo)}
.botao-s:hover{background:var(--papel);border-color:var(--tinta);
  color:var(--tinta)}

.jcapa{background:var(--tinta);color:rgba(255,255,255,.86);
  padding:var(--e5) 0}
.jcapa h1{color:var(--branco);margin:0 0 var(--e2);max-width:22ch;
  font-size:clamp(1.9rem,1.3rem + 2.4vw,3rem)}
.jcapa .lede{max-width:56ch;margin:0;color:rgba(255,255,255,.8);
  font-size:clamp(1.02rem,1rem + .3vw,1.16rem)}

/* ------------------------------------------------------------- o indice */
.jlista{padding:var(--e5) 0 var(--e6)}
.jgrelha{display:grid;gap:1px;background:var(--risco);
  border:1px solid var(--risco);border-radius:var(--raio);overflow:hidden}
@media (min-width:860px){.jgrelha{grid-template-columns:1fr 1fr}}
.jart{background:var(--branco);padding:var(--e4);display:block;
  text-decoration:none;color:inherit}
.jart:hover{background:var(--papel)}
.jart:focus-visible{outline:3px solid var(--cor);outline-offset:-3px}
.jart .rot{display:flex;gap:10px;align-items:center;margin:0 0 10px;
  font-family:var(--mono);font-size:12px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--cor-escura);font-weight:600}
.jart .rot time{color:var(--mudo);font-weight:400;letter-spacing:.04em}
.jart h2{margin:0 0 10px;font-size:clamp(1.15rem,1.05rem + .4vw,1.4rem);
  line-height:1.2}
.jart p{margin:0;font-size:.94rem;line-height:1.65;color:var(--texto)}
.jart .mais{display:inline-block;margin-top:14px;font-weight:600;
  font-size:.9rem;color:var(--cor-escura)}

/* ------------------------------------------------------------- o artigo */
.jtopo{padding:var(--e5) 0 var(--e4);border-bottom:1px solid var(--risco)}
.jtopo .rot{display:flex;gap:12px;align-items:center;margin:0 0 var(--e2);
  font-family:var(--mono);font-size:12px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--cor-escura);font-weight:600}
.jtopo .rot time{color:var(--mudo);font-weight:400}
.jtopo h1{margin:0 0 var(--e2);max-width:26ch;
  font-size:clamp(1.8rem,1.2rem + 2.4vw,2.8rem)}
.jtopo .lede{margin:0;max-width:58ch;color:var(--texto);
  font-size:clamp(1.05rem,1rem + .35vw,1.22rem);line-height:1.6}

.jcorpo{padding:var(--e5) 0 var(--e6)}
.jcorpo .dentro{max-width:40rem}
.jcorpo h2{margin:var(--e5) 0 var(--e2);
  font-size:clamp(1.25rem,1.1rem + .5vw,1.6rem);line-height:1.22}
.jcorpo h2:first-child{margin-top:0}
.jcorpo p{margin:0 0 var(--e3);font-size:1.02rem;line-height:1.72;
  color:var(--texto)}
.jcorpo p b{color:var(--tinta)}

/* Os numeros que saem dos dados. Ficam marcados a olho para nao se
   confundirem com o texto: sao a parte que muda sozinha. */
.jdados{margin:var(--e3) 0 var(--e4);border:1px solid var(--risco);
  border-left:4px solid var(--cor);border-radius:var(--raio);
  background:var(--branco);overflow:hidden}
.jdados-t{margin:0;padding:12px var(--e3);border-bottom:1px solid var(--risco);
  font-family:var(--mono);font-size:11.5px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--mudo);font-weight:600}
.jdados table{width:100%;border-collapse:collapse}
.jdados th,.jdados td{text-align:left;padding:10px var(--e3);
  border-bottom:1px solid var(--risco);font-size:.92rem;color:var(--texto)}
.jdados th{font-family:var(--mono);font-size:11.5px;letter-spacing:.08em;
  text-transform:uppercase;color:var(--mudo);font-weight:600}
.jdados tr:last-child td{border-bottom:0}
.jdados .num{font-variant-numeric:tabular-nums;white-space:nowrap}
.jdados td a{color:var(--cor-escura);font-weight:500}
.jdados-n{margin:0;padding:10px var(--e3);background:var(--papel);
  border-top:1px solid var(--risco);font-size:.84rem;line-height:1.5;
  color:var(--mudo)}

.jfim{margin-top:var(--e5);padding-top:var(--e4);
  border-top:1px solid var(--risco)}
.jfim h3{margin:0 0 var(--e2);font-size:1.1rem}
.jfim .acoes{display:flex;flex-wrap:wrap;gap:12px}

.joutros{background:var(--branco);border-top:1px solid var(--risco);
  padding:var(--e5) 0}
.joutros h2{margin:0 0 var(--e3);font-size:1.3rem}
.joutros-g{display:grid;gap:var(--e3)}
@media (min-width:760px){.joutros-g{grid-template-columns:repeat(3,1fr)}}
.joutro{display:block;text-decoration:none;color:inherit;
  border:1px solid var(--risco);border-radius:var(--raio);padding:var(--e3)}
.joutro:hover{background:var(--papel)}
.joutro b{display:block;font-family:var(--tipo-titulo);font-size:1.02rem;
  line-height:1.25;margin-bottom:6px;color:var(--tinta)}
.joutro span{font-size:.88rem;line-height:1.55;color:var(--mudo)}
'''


def data_legivel(iso):
    """3 October 2026. Sem dependencias e sem locale: o locale do
    container nao e o do leitor e nao vale a pena finge-lo."""
    meses = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
             'August', 'September', 'October', 'November', 'December']
    a, m, d = iso.split('-')
    return '%d %s %s' % (int(d), meses[int(m) - 1], a)


# --------------------------------------------------------------- os dados
#
# Cada bloco de dados e uma funcao que recebe o catalogo e devolve uma
# tabela. O texto do artigo so diz o NOME do bloco; os numeros nunca
# passam pelo JSON. Assim um artigo nao pode ficar a mentir por o
# catalogo ter mudado.

def exemplos_preco(tours):
    """O mesmo dia a quatro tamanhos de grupo. Escolhem-se os tours com
    mais escaloes, porque sao esses que mostram a ideia."""
    com_escaloes = sorted(tours, key=lambda t: -len(t['durations'][0]['tiers']))
    linhas = []
    for t in com_escaloes[:3]:
        d = t['durations'][0]
        cheio = max(d['tiers'], key=lambda x: x['max'])
        menor = min(d['tiers'], key=lambda x: x['price'])
        linhas.append(
            '<tr><td><a href="/tours/%s/">%s</a></td>'
            '<td class="num">&euro;%s</td>'
            '<td class="num">&euro;%s</td>'
            '<td class="num">&euro;%s</td></tr>'
            % (e(t['slug']), e(t['title'].replace('Private Tour: ', '')),
               euros(menor['price']),
               euros(cheio['price']),
               euros(round(cheio['price'] / cheio['max']))))
    return ('<div class="jdados">'
            '<p class="jdados-t">From the catalogue, %s</p>'
            '<table><thead><tr><th>Tour</th><th>Smallest vehicle</th>'
            '<th>Largest vehicle</th><th>Per person, full</th></tr></thead>'
            '<tbody>%s</tbody></table>'
            '<p class="jdados-n">The last column is the largest vehicle '
            'price divided by the people it carries. It is arithmetic on '
            'the two columns before it, not a separate offer.</p></div>'
            % (data_legivel(HOJE), '\n'.join(linhas)))


def partidas(tours):
    """As partidas mais cedo do catalogo. Sai dos dados, por isso nao
    ha como escrever aqui uma hora que nao exista."""
    com_hora = [t for t in tours if t['_partida']]
    cedo = sorted(com_hora, key=lambda t: t['_partida'])[:6]
    linhas = []
    for t in cedo:
        linhas.append(
            '<tr><td class="num">%s</td>'
            '<td><a href="/tours/%s/">%s</a></td>'
            '<td>%s</td><td class="num">%s</td></tr>'
            % (e(t['_partida']), e(t['slug']),
               e(t['title'].replace('Private Tour: ', '')),
               e(t['city']), e(t['_h'])))
    antes8 = len([t for t in com_hora if t['_partida'] < '08:00'])
    return ('<div class="jdados">'
            '<p class="jdados-t">The earliest departures we list</p>'
            '<table><thead><tr><th>Leaves</th><th>Tour</th><th>From</th>'
            '<th>Lasts</th></tr></thead><tbody>%s</tbody></table>'
            '<p class="jdados-n">%d of the %d tours that publish a '
            'departure time leave before eight in the morning. Every one '
            'of them has a stop that fills up by mid-morning.</p></div>'
            % ('\n'.join(linhas), antes8, len(com_hora)))


BLOCOS = {'exemplos_preco': exemplos_preco, 'partidas': partidas}

HOJE = '2026-10-03'


# -------------------------------------------------------------- as paginas

def cartao(a):
    return ('<a class="jart" href="/journal/%s/">'
            '<p class="rot"><span>%s</span>'
            '<time datetime="%s">%s</time></p>'
            '<h2>%s</h2><p>%s</p>'
            '<span class="mais">Read it &rarr;</span></a>'
            % (e(a['slug']), e(a['kicker']), e(a['data']),
               data_legivel(a['data']), a['titulo'], a['lede']))


def indice(artigos, paises):
    corpo = '''%(cabecalho)s
<main id="principal">

<section class="jcapa">
  <div class="folha">
    <h1>The journal</h1>
    <p class="lede">Not a list of ten things to do. How a private day is
      priced, what the word means, and how a tour gets onto this
      site &mdash; with the numbers taken from the catalogue rather than
      written into the sentence.</p>
  </div>
</section>

<section class="jlista">
  <div class="folha">
    <div class="jgrelha">%(cartoes)s</div>
  </div>
</section>

</main>
%(rodape)s''' % {'cabecalho': cabecalho(paises=paises),
                 'rodape': rodape(paises),
                 'cartoes': '\n'.join(cartao(a) for a in artigos)}

    escrever(envolver(
        'The journal — Exclusive World Tours',
        'How private day tours are priced, what private actually means, '
        'and how a tour gets onto this site.',
        CSS, corpo, js=procura.JS), 'journal/index.html')


def artigo(a, artigos, tours, paises):
    secoes = []
    for s in a['secoes']:
        secoes.append('<h2>%s</h2>' % s['h'])
        for par in s['p']:
            secoes.append('<p>%s</p>' % par)
        if s.get('dados'):
            bloco = BLOCOS.get(s['dados'])
            if bloco is None:
                sys.exit('O artigo %s pede o bloco de dados "%s" e esse '
                         'bloco nao existe em BLOCOS.' % (a['slug'], s['dados']))
            secoes.append(bloco(tours))

    outros = [x for x in artigos if x['slug'] != a['slug']][:3]

    corpo = '''%(cabecalho)s
<main id="principal">

<header class="jtopo">
  <div class="folha">
    <nav class="migalhas" aria-label="Breadcrumb">
      <a href="/">Home</a> &rsaquo;
      <a href="/journal/">Journal</a> &rsaquo;
      <span>%(kicker)s</span>
    </nav>
    <p class="rot"><span>%(kicker)s</span>
      <time datetime="%(data)s">%(data_l)s</time></p>
    <h1>%(titulo)s</h1>
    <p class="lede">%(lede)s</p>
  </div>
</header>

<article class="jcorpo">
  <div class="folha">
    <div class="dentro">
      %(secoes)s

      <div class="jfim">
        <h3>%(fim_h)s</h3>
        <p>%(fim_p)s</p>
        <div class="acoes">%(fim_acoes)s</div>
      </div>
    </div>
  </div>
</article>

<section class="joutros">
  <div class="folha">
    <h2>Also here</h2>
    <div class="joutros-g">%(outros)s</div>
  </div>
</section>

</main>
%(rodape)s''' % {
        'cabecalho': cabecalho(paises=paises),
        'rodape': rodape(paises),
        'kicker': e(a['kicker']), 'data': e(a['data']),
        'data_l': data_legivel(a['data']),
        'titulo': a['titulo'], 'lede': a['lede'],
        'secoes': '\n      '.join(secoes),
        'fim_h': ('Want to list your tours?'
                  if a['kicker'] == 'For operators'
                  else 'Looking at a particular day?'),
        'fim_p': (('Commission is 20%% of what the guest pays, you set the '
                   'price, and we answer every application.')
                  if a['kicker'] == 'For operators'
                  else ('%s Tell us the date and we come back with a yes or '
                        'a no, and the exact price for your group size.'
                        % politica.CURTA + '.')),
        'fim_acoes': (('<a class="botao" href="/suppliers/apply/">Apply to '
                       'sell here</a>'
                       '<a class="botao botao-s" href="/suppliers/">How it '
                       'works</a>')
                      if a['kicker'] == 'For operators'
                      else ('<a class="botao" href="/tours/">See all '
                            'tours</a>'
                            '<a class="botao botao-s" href="/contact/">Ask '
                            'about a date</a>')),
        'outros': '\n'.join(
            '<a class="joutro" href="/journal/%s/"><b>%s</b><span>%s</span></a>'
            % (e(x['slug']), x['titulo'], x['lede'][:110] + '&hellip;')
            for x in outros),
    }

    escrever(envolver(
        '%s — Exclusive World Tours' % a['titulo'].replace('&quot;', '"'),
        a['lede'][:160],
        CSS, corpo, js=procura.JS), 'journal/%s/index.html' % a['slug'])


def main():
    tours = carregar()
    paises = por_pais(tours)
    artigos = json.load(open(os.path.join(AQUI, 'artigos.json')))['artigos']

    indice(artigos, paises)
    for a in artigos:
        artigo(a, artigos, tours, paises)
    print('%d artigos' % len(artigos))


if __name__ == '__main__':
    main()
