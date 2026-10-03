#!/usr/bin/env python3
"""
A pagina de um tour. E a pagina que vende.

Tudo o que aparece sai do tours.json: o itinerario com as horas, os
escaloes de preco por veiculo, o que inclui, o que nao inclui, as notas
praticas e as perguntas. Nada e escrito aqui a mao.

Duas coisas ficam deliberadamente de fora:

1. **As perguntas que falam de politica** — reembolsos, cancelamentos,
   depositos, seguros. Esses textos sao da The Epic Tours e descrevem
   regras que a Exclusive World Tours ainda nao tem. Publicar uma
   politica de reembolso que nao existe e prometer uma coisa que depois
   nao se cumpre. O gerador apanha-as por assunto e diz quais tirou.

2. **O botao de reservar.** Nao ha ainda forma de receber uma reserva.
   Em vez de um botao que nao faz nada, ha um bloco que diz a verdade
   sobre como se reserva hoje. Assim que houver canal, troca-se num
   sitio so.

    python3 tools/tour.py            # escreve tours/<slug>/index.html
"""

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import procura  # noqa: E402
from pagina import (CORES, cabecalho, carregar, cartao_tour, e, envolver,  # noqa: E402
                    escrever, euros, img, por_pais, rodape)

# Assuntos que nao se publicam enquanto o Ricardo nao definir a politica.
# Nao e censura: e nao prometer o que ainda nao existe.
POLITICA = re.compile(
    r'\b(refund|refunded|cancel|cancelled|cancellation|deposit|insurance|'
    r'insured|reschedul)\w*\b', re.I)


CSS = '''<style>
.migalhas{font-size:13.5px;color:var(--mudo);padding:18px 0 0}
/* sublinhados de proposito: na migalha o link tem a mesma cor do texto
   a volta, e sem sublinhado a unica coisa que o distingue e a cor — que
   e exatamente o que a norma nao deixa. */
.migalhas a{color:var(--mudo);text-decoration:underline;
  text-underline-offset:2px;text-decoration-color:var(--risco)}
.migalhas a:hover{color:var(--cor-escura);
  text-decoration-color:var(--cor-escura)}

.t-topo{padding:14px 0 30px}
.t-kicker{font-size:13px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--cor-escura);font-weight:600;margin:0 0 10px}
.t-topo h1{font-size:clamp(1.9rem, 1.3rem + 2.2vw, 3rem);margin:0 0 14px}
.t-lede{font-size:clamp(1.05rem,1rem + .35vw,1.25rem);color:var(--texto);
  max-width:60ch;margin:0}

/* A grande manda na altura e as duas pequenas enchem as duas filas. Com
   proporcao propria em cada uma, as pequenas acabavam antes da grande e
   sobrava um buraco branco por baixo delas. */
.galeria{display:grid;gap:10px;grid-template-columns:2fr 1fr 1fr;
  grid-template-rows:repeat(2,1fr);margin:0 0 34px}
.galeria figure{position:relative;margin:0;border-radius:var(--raio);
  overflow:hidden;background:var(--uma-f);min-height:0}
.galeria figure:first-child{aspect-ratio:3/2;grid-row:1/3}
.galeria img{width:100%;height:100%;object-fit:cover}
.galeria figcaption{position:absolute;right:8px;bottom:7px;font-size:10.5px;
  color:#fff;background:rgba(11,43,42,.68);padding:3px 7px;border-radius:5px}
@media (max-width:860px){
  .galeria{grid-template-columns:1fr 1fr;grid-template-rows:auto}
  .galeria figure{aspect-ratio:4/3}
  .galeria figure:first-child{grid-column:1/-1;grid-row:auto;aspect-ratio:3/2}
}

.t-grelha{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:52px;
  align-items:start;padding-bottom:80px}
@media (max-width:980px){.t-grelha{grid-template-columns:1fr;gap:36px}}

.factos{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 36px}
.facto{border:1px solid var(--risco);border-radius:11px;padding:11px 15px}
.facto b{display:block;font-family:var(--tipo-titulo);color:var(--tinta);
  font-size:1rem;line-height:1.2}
.facto span{font-size:12.5px;color:var(--mudo)}

.sec{margin:0 0 44px}
.sec h2{font-size:1.45rem;margin:0 0 6px}
.sec .intro{color:var(--mudo);margin:0 0 20px;max-width:58ch}

/* a linha do dia: as posicoes sao as do tours.json, nao desenhadas a olho */
.fita{position:relative;height:66px;margin:0 0 26px}
.fita-linha{position:absolute;left:0;right:0;top:26px;height:3px;
  background:var(--risco);border-radius:2px}
.fita-ponto{position:absolute;top:19px;width:17px;height:17px;
  border-radius:50%;background:var(--branco);
  border:3px solid var(--tinta-f);transform:translateX(-50%)}
.fita-ponto.chave{background:var(--cor);border-color:var(--cor);
  width:21px;height:21px;top:17px}
.fita-rot{position:absolute;top:46px;transform:translateX(-50%);
  font-size:11.5px;color:var(--mudo);white-space:nowrap;
  font-variant-numeric:tabular-nums}
.fita-fim{position:absolute;top:0;font-size:12px;color:var(--tinta);
  font-weight:600;font-variant-numeric:tabular-nums}
.fita-fim.e{left:0}.fita-fim.d{right:0}
@media (max-width:760px){.fita{display:none}}

.paragens{list-style:none;margin:0;padding:0}
.paragem{display:grid;grid-template-columns:76px 1fr;gap:18px;
  padding:0 0 26px;position:relative}
.paragem::before{content:'';position:absolute;left:87px;top:20px;bottom:0;
  width:2px;background:var(--risco)}
.paragem:last-child::before{display:none}
.paragem-h{font-variant-numeric:tabular-nums;color:var(--mudo);
  font-size:14px;padding-top:1px;text-align:right}
.paragem-c{position:relative;padding-left:26px}
.paragem-c::before{content:'';position:absolute;left:-5px;top:7px;
  width:11px;height:11px;border-radius:50%;background:var(--tinta-f)}
.paragem.chave .paragem-c::before{background:var(--cor);
  box-shadow:0 0 0 4px var(--cor-f)}
.paragem h3{font-size:1.05rem;margin:0 0 5px}
.paragem p{margin:0;color:var(--texto);font-size:15.5px}
.paragem .nota{display:inline-block;margin-top:8px;font-size:12.5px;
  color:var(--texto);background:var(--papel);border:1px solid var(--risco);
  border-radius:999px;padding:3px 11px}

.inclui{list-style:none;margin:0;padding:0;display:grid;gap:9px}
.inclui li{display:flex;gap:11px;align-items:flex-start;font-size:15.5px}
.inclui svg{width:19px;height:19px;flex:none;margin-top:3px;fill:none;
  stroke:var(--cor-escura);stroke-width:2.4;stroke-linecap:round;
  stroke-linejoin:round}
.nao-inclui{margin:18px 0 0;color:var(--mudo);font-size:15.5px;
  max-width:58ch}

.pratico{border-collapse:collapse;width:100%;font-size:15.5px}
.pratico th{text-align:left;vertical-align:top;padding:13px 20px 13px 0;
  width:150px;color:var(--tinta);font-weight:600;
  border-top:1px solid var(--risco)}
.pratico td{padding:13px 0;border-top:1px solid var(--risco);
  color:var(--texto)}

.faq details{border-top:1px solid var(--risco)}
.faq details:last-of-type{border-bottom:1px solid var(--risco)}
.faq summary{cursor:pointer;padding:16px 0;font-weight:600;
  color:var(--tinta);list-style:none;display:flex;gap:14px;
  align-items:flex-start}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:'+';margin-left:auto;color:var(--cor-escura);
  font-size:20px;line-height:1}
.faq details[open] summary::after{content:'\\2013'}
.faq p{margin:0 0 18px;color:var(--texto);max-width:60ch}

/* o painel de preco */
.painel{position:sticky;top:94px;border:1px solid var(--risco);
  border-radius:var(--raio);padding:24px;background:var(--branco);
  box-shadow:0 18px 44px -28px rgba(11,43,42,.4)}
.painel .desde{font-size:13px;color:var(--mudo);margin:0}
.painel .preco{font-family:var(--tipo-titulo);font-size:2.3rem;
  color:var(--tinta);font-variant-numeric:tabular-nums;line-height:1.1;
  margin:2px 0 2px}
.painel .por{font-size:13.5px;color:var(--mudo);margin:0 0 20px}
.escaloes{width:100%;border-collapse:collapse;font-size:14.5px;
  margin:0 0 20px}
.escaloes th{text-align:left;font-weight:600;color:var(--mudo);
  font-size:12px;letter-spacing:.06em;text-transform:uppercase;
  padding:0 0 8px}
.escaloes th:last-child,.escaloes td:last-child{text-align:right}
.escaloes td{padding:8px 0;border-top:1px solid var(--risco);
  font-variant-numeric:tabular-nums}
.escaloes tr.activo td{color:var(--tinta);font-weight:600}
.escaloes .veic{color:var(--mudo);font-size:13px}
.painel .nota{font-size:13.5px;color:var(--mudo);margin:0}
.painel .nota b{color:var(--tinta)}
.reservar{display:block;width:100%;text-align:center;margin:0 0 14px}

.relacionados{background:var(--papel);border-top:1px solid var(--risco);
  padding:64px 0 76px}
.relacionados h2{font-size:1.5rem;margin:0 0 24px}
</style>'''


def facto(valor, rotulo):
    return '<span class="facto"><b>%s</b><span>%s</span></span>' % (
        e(valor), e(rotulo))


def fita(t):
    if not t.get('ribbon'):
        return ''
    pontos = []
    for r in t['ribbon']:
        chave = ' chave' if r.get('key') else ''
        pontos.append('<span class="fita-ponto%s" style="left:%s%%"></span>'
                      '<span class="fita-rot" style="left:%s%%">%s</span>'
                      % (chave, r['pos'], r['pos'], e(r['n'])))
    bordas = t.get('ribbonEdges') or []
    return ('<div class="fita" aria-hidden="true">'
            '<span class="fita-linha"></span>'
            '%s%s%s</div>'
            % ('<span class="fita-fim e">%s</span>' % e(bordas[0]) if bordas else '',
               '<span class="fita-fim d">%s</span>' % e(bordas[1]) if len(bordas) > 1 else '',
               ''.join(pontos)))


def paragens(t):
    out = []
    for s in t.get('stops', []):
        nota = ('<span class="nota">%s</span>' % e(s['note'])) if s.get('note') else ''
        out.append('''<li class="paragem%(chave)s">
  <span class="paragem-h">%(when)s</span>
  <div class="paragem-c">
    <h3>%(h)s</h3>
    <p>%(p)s</p>
    %(nota)s
  </div>
</li>''' % {'chave': ' chave' if s.get('key') else '',
             'when': e(s.get('when') or ''), 'h': e(s['h']),
             'p': e(s['p']), 'nota': nota})
    return '<ol class="paragens">%s</ol>' % '\n'.join(out)


VISTO = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
         '<path d="M4 12.5 L9.5 18 L20 6.5"/></svg>')


def faq(t, tirados):
    linhas = []
    for q, a in t.get('faq', []):
        if POLITICA.search(q) or POLITICA.search(a):
            tirados.append((t['slug'], q))
            continue
        linhas.append('<details><summary>%s</summary><p>%s</p></details>'
                      % (e(q), e(a)))
    if not linhas:
        return ''
    return ('<section class="sec faq"><h2>Questions</h2>%s</section>'
            % '\n'.join(linhas))


def painel(t):
    d = t['durations'][0]
    menor = min(d['tiers'], key=lambda x: x['price'])
    linhas = []
    for x in d['tiers']:
        activo = ' class="activo"' if x is menor else ''
        linhas.append('<tr%s><td>Up to %d<span class="veic">%s</span></td>'
                      '<td>&euro;%s</td></tr>'
                      % (activo, x['max'],
                         (' &middot; ' + e(x['vehicle'])) if x.get('vehicle') else '',
                         euros(x['price'])))
    return '''<aside class="painel">
  <p class="desde">From</p>
  <p class="preco">&euro;%(preco)s</p>
  <p class="por">for the whole group, up to %(max)d people</p>
  <table class="escaloes">
    <thead><tr><th>Group size</th><th>Total</th></tr></thead>
    <tbody>%(linhas)s</tbody>
  </table>
  <a class="botao reservar" href="#book">Check this date</a>
  <p class="nota">The price is for the <b>whole vehicle</b>, not per person.
    Four people pay the same as one.</p>
</aside>''' % {'preco': euros(menor['price']), 'max': t['_max'],
               'linhas': '\n'.join(linhas)}


def main():
    tours = carregar()
    paises = por_pais(tours)
    por_slug = {t['slug']: t for t in tours}
    tirados = []

    for t in tours:
        d = t['durations'][0]
        fotos = t.get('photos') or []
        galeria = ''
        if fotos:
            figs = []
            for i, f in enumerate(fotos[:3]):
                figs.append('<figure>%s<figcaption>Photo %s</figcaption></figure>'
                            % (img(f['id'], f['alt'], (600, 1200),
                                   '(min-width:860px) 50vw, 100vw',
                                   eager=(i == 0)), e(f['by'])))
            galeria = '<div class="galeria">%s</div>' % '\n'.join(figs)

        irmaos = [x for x in tours
                  if x['countryName'] == t['countryName'] and x['slug'] != t['slug']]
        irmaos = sorted(irmaos, key=lambda x: x['_preco'])[:3]

        corpo = '''%(cabecalho)s
<main id="principal">
<div class="folha">
  <nav class="migalhas" aria-label="Breadcrumb">
    <a href="/">Home</a> &rsaquo;
    <a href="/tours/?country=%(cod)s">%(pais)s</a> &rsaquo;
    <span>%(cidade)s</span>
  </nav>

  <header class="t-topo">
    <p class="t-kicker">%(kicker)s</p>
    <h1>%(titulo)s</h1>
    <p class="t-lede">%(lede)s</p>
  </header>

  %(galeria)s

  <div class="t-grelha">
    <div>
      <div class="factos">%(factos)s</div>

      <section class="sec">
        <h2>The day</h2>
        <p class="intro">%(stopsIntro)s</p>
        %(fita)s
        %(paragens)s
      </section>

      <section class="sec">
        <h2>What the price covers</h2>
        <p class="intro">%(includedIntro)s</p>
        <ul class="inclui">%(inclui)s</ul>
        <p class="nao-inclui">%(naoInclui)s</p>
      </section>

      <section class="sec">
        <h2>Practical</h2>
        <table class="pratico"><tbody>%(pratico)s</tbody></table>
      </section>

      %(faq)s

      <section class="sec" id="book">
        <h2>How to book</h2>
        <p class="intro">Online booking opens shortly. Until then, tell us the
          date and the size of your group and we will come back to you with the
          exact price and a hold on the day.</p>
      </section>
    </div>

    %(painel)s
  </div>
</div>

%(relacionados)s
</main>
%(rodape)s''' % {
            'cabecalho': cabecalho(),
            'cod': e(t['country']), 'pais': e(t['countryName']),
            'cidade': e(t['city']),
            'kicker': e(t.get('kicker') or ''), 'titulo': e(t['title']),
            'lede': e(t.get('lede') or ''), 'galeria': galeria,
            'factos': ''.join([
                facto(t['_h'], 'door to door'),
                facto('Up to %d' % t['_max'], 'in one group'),
                facto(t['_partida'] or '—', 'departure'),
                facto(t['city'], 'pick-up'),
                facto('Private', 'nobody else'),
            ]),
            'stopsIntro': e(t.get('stopsIntro') or ''),
            'fita': fita(t), 'paragens': paragens(t),
            'includedIntro': e(t.get('includedIntro') or ''),
            'inclui': '\n'.join('<li>%s<span>%s</span></li>' % (VISTO, e(x))
                                for x in t.get('included', [])),
            'naoInclui': e(t.get('notIncluded') or ''),
            'pratico': '\n'.join('<tr><th>%s</th><td>%s</td></tr>'
                                 % (e(a), e(b)) for a, b in t.get('practical', [])),
            'faq': faq(t, tirados),
            'painel': painel(t),
            'relacionados': ('''<section class="relacionados">
  <div class="folha">
    <h2>More days in %s</h2>
    <div class="tours">%s</div>
  </div>
</section>''' % (e(t['countryName']),
                 '\n'.join(cartao_tour(x) for x in irmaos))) if irmaos else '',
            'rodape': rodape(paises),
        }

        html = envolver(
            '%s — Exclusive World Tours' % t['title'],
            t.get('metaDesc') or '',
            CSS, corpo, js=procura.JS)
        escrever(html, 'tours/%s/index.html' % t['slug'])

    print('%d paginas de tour' % len(tours))
    if tirados:
        print('\nPerguntas retiradas por falarem de politica que a marca '
              'ainda nao tem (%d):' % len(tirados))
        vistos = set()
        for slug, q in tirados:
            if q in vistos:
                continue
            vistos.add(q)
            print('  %s' % q)


if __name__ == '__main__':
    main()
