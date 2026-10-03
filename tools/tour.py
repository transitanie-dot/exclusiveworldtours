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
/* ------------------------------------------------------------- o heroi
   A fotografia a sangrar com o titulo por cima. A Viator e a
   GetYourGuide poem uma grelha de miniaturas e o titulo em texto preto
   por baixo; isto poe o sitio primeiro, que e o que se esta a comprar. */
.heroi-t{position:relative;min-height:clamp(380px,48vw,560px);
  display:flex;align-items:flex-end;background:var(--tinta);overflow:hidden}
.heroi-t .foto{position:absolute;inset:0;overflow:hidden}
.heroi-t .foto img{width:100%;height:100%;object-fit:cover}
.heroi-t::after{content:'';position:absolute;inset:0;
  background:linear-gradient(to top, rgba(11,43,42,.94) 0%,
    rgba(11,43,42,.78) 32%, rgba(11,43,42,.34) 66%, rgba(11,43,42,.22) 100%)}
.heroi-t .folha{position:relative;z-index:2;padding-top:var(--e5);
  padding-bottom:var(--e4)}
.migalhas{font-size:12.5px;color:rgba(255,255,255,.72);margin:0 0 var(--e2)}
.migalhas a{color:rgba(255,255,255,.72);text-decoration:underline;
  text-underline-offset:2px;text-decoration-color:rgba(255,255,255,.3)}
.migalhas a:hover{color:#fff;text-decoration-color:#fff}
.t-kicker{font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--cor);font-weight:600;margin:0 0 10px}
.heroi-t h1{color:var(--branco);max-width:17ch;
  font-size:clamp(2rem, 1.3rem + 2.6vw, 3.4rem);margin:0 0 12px}
.t-lede{color:rgba(255,255,255,.85);max-width:54ch;margin:0 0 var(--e3);
  font-size:clamp(1rem,.95rem + .3vw,1.12rem)}
.factos{display:flex;flex-wrap:wrap;gap:0;border:1px solid rgba(255,255,255,.22);
  border-radius:var(--raio);overflow:hidden;width:fit-content;max-width:100%}
.facto{padding:10px 18px;border-right:1px solid rgba(255,255,255,.22)}
.facto:last-child{border-right:0}
.facto b{display:block;font-family:var(--tipo-titulo);color:var(--branco);
  font-size:.98rem;line-height:1.2;font-variant-numeric:tabular-nums}
.facto span{font-size:11.5px;color:rgba(255,255,255,.66)}
@media (max-width:620px){.factos{width:100%}.facto{flex:1 1 44%;
  border-bottom:1px solid rgba(255,255,255,.22)}}

/* a tira de fotografias, por baixo do heroi */
/* o numero de colunas segue o numero de fotografias: fixo em tres, com
   duas ficava um buraco do tamanho de uma fotografia */
.tira{display:grid;gap:8px;padding:8px 0 0;
  grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr))}
.tira figure{position:relative;margin:0;border-radius:var(--raio);
  overflow:hidden;background:var(--uma-f);aspect-ratio:3/2}
.tira img{width:100%;height:100%;object-fit:cover}
.tira figcaption{position:absolute;right:7px;bottom:6px;font-size:10px;
  color:#fff;background:rgba(11,43,42,.62);padding:2px 6px;border-radius:4px}
@media (max-width:700px){.tira{grid-template-columns:1fr 1fr}
  .tira figure:first-child{grid-column:1/-1}}

/* a barra que aparece ao percorrer, com o preco sempre a mao */
.fixa{position:fixed;left:0;right:0;top:62px;z-index:39;background:var(--tinta);
  color:#fff;transform:translateY(-100%);transition:transform .25s ease;
  border-bottom:1px solid rgba(255,255,255,.14)}
.fixa.vis{transform:none}
@media (max-width:620px){.fixa{top:62px}}
.fixa .folha{display:flex;align-items:center;gap:var(--e3);height:58px}
.fixa-t{font-family:var(--tipo-titulo);font-weight:600;color:#fff;
  font-size:.95rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.fixa-p{margin-left:auto;white-space:nowrap;font-size:13px;
  color:rgba(255,255,255,.75)}
.fixa-p b{font-family:var(--tipo-titulo);font-size:1.05rem;color:#fff;
  font-variant-numeric:tabular-nums}
/* O botao da barra e branco, nao ambar. Branco sobre ambar da 3.51:1 e
   tinta sobre ambar 4.3:1 — os dois reprovam os 4.5 que a norma pede a
   texto. Tinta sobre branco da 15:1, e numa barra escura o branco salta
   mais do que o ambar saltava. */
.fixa .botao{min-height:38px;padding:0 18px;background:var(--branco);
  color:var(--tinta);font-size:14px}
.fixa .botao:hover{background:var(--papel);color:var(--tinta)}
@media (max-width:700px){.fixa-t{display:none}.fixa-p{margin-left:0}}

/* ------------------------------------------------------------ o corpo */
.t-grelha{display:grid;grid-template-columns:minmax(0,1fr) 340px;
  gap:var(--e5);align-items:start}
@media (max-width:980px){.t-grelha{grid-template-columns:1fr;gap:var(--e4)}}

.sec{margin:0 0 var(--e5)}
.sec:last-child{margin-bottom:0}
.sec h2{font-size:1.35rem;margin:0 0 6px}
.sec .intro{color:var(--mudo);margin:0 0 var(--e3);max-width:56ch}
.banda-e .sec .intro{color:rgba(255,255,255,.7)}

/* a linha do dia */
.fita{position:relative;height:62px;margin:0 0 var(--e3)}
.fita-linha{position:absolute;left:0;right:0;top:24px;height:2px;
  background:rgba(255,255,255,.2);border-radius:2px}
.fita-ponto{position:absolute;top:18px;width:14px;height:14px;
  border-radius:50%;background:var(--tinta);
  border:2px solid rgba(255,255,255,.45);transform:translateX(-50%)}
.fita-ponto.chave{background:var(--cor);border-color:var(--cor);
  width:18px;height:18px;top:16px}
.fita-rot{position:absolute;top:42px;transform:translateX(-50%);
  font-size:11px;color:rgba(255,255,255,.66);white-space:nowrap}
.fita-fim{position:absolute;top:0;font-size:11.5px;color:#fff;
  font-weight:600;font-family:var(--mono)}
.fita-fim.e{left:0}.fita-fim.d{right:0}
@media (max-width:760px){.fita{display:none}}

.paragens{list-style:none;margin:0;padding:0;
  columns:2;column-gap:var(--e5)}
@media (max-width:860px){.paragens{columns:1}}
.paragem{display:grid;grid-template-columns:54px 1fr;gap:14px;
  padding:0 0 var(--e3);break-inside:avoid}
.paragem-h{font-family:var(--mono);font-size:12.5px;
  color:rgba(255,255,255,.6);padding-top:2px;text-align:right}
.paragem-c{position:relative;padding-left:20px;
  border-left:1px solid rgba(255,255,255,.16)}
.paragem-c::before{content:'';position:absolute;left:-5px;top:6px;
  width:9px;height:9px;border-radius:50%;background:rgba(255,255,255,.35)}
.paragem.chave .paragem-c::before{background:var(--cor);
  box-shadow:0 0 0 4px rgba(206,112,48,.25)}
.paragem h3{font-size:.98rem;margin:0 0 4px;color:#fff}
.paragem p{margin:0;color:rgba(255,255,255,.76);font-size:14px}
.paragem .nota{display:inline-block;margin-top:7px;font-size:11.5px;
  color:rgba(255,255,255,.82);border:1px solid rgba(255,255,255,.22);
  border-radius:4px;padding:2px 8px}

.inclui{list-style:none;margin:0;padding:0;display:grid;gap:8px;
  grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr))}
.inclui li{display:flex;gap:10px;align-items:flex-start;font-size:14.5px}
.inclui svg{width:17px;height:17px;flex:none;margin-top:3px;fill:none;
  stroke:var(--cor-escura);stroke-width:2.6;stroke-linecap:round;
  stroke-linejoin:round}
.nao-inclui{margin:var(--e3) 0 0;color:var(--mudo);font-size:14.5px;
  max-width:60ch;padding-left:14px;border-left:2px solid var(--risco)}

.pratico{border-collapse:collapse;width:100%;font-size:14.5px}
.pratico th{text-align:left;vertical-align:top;padding:12px 18px 12px 0;
  width:140px;color:var(--tinta);font-weight:600;
  border-top:1px solid var(--risco)}
.pratico td{padding:12px 0;border-top:1px solid var(--risco)}

.faq details{border-top:1px solid var(--risco);background:var(--branco)}
.faq details:last-of-type{border-bottom:1px solid var(--risco)}
.faq summary{cursor:pointer;padding:14px 16px;font-weight:600;
  color:var(--tinta);list-style:none;display:flex;gap:14px;
  align-items:flex-start;font-size:14.5px}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:'+';margin-left:auto;color:var(--cor-escura);
  font-size:18px;line-height:1}
.faq details[open] summary::after{content:'\2013'}
.faq p{margin:0 16px 16px;color:var(--texto);max-width:62ch;font-size:14.5px}

/* ----------------------------------------------------------- a coluna */
.lado{position:sticky;top:74px;display:grid;gap:12px}
.painel{border:1px solid var(--risco);border-radius:var(--raio);
  padding:18px;background:var(--branco);
  box-shadow:0 14px 36px -26px rgba(11,43,42,.45)}
.painel .desde{font-size:11.5px;color:var(--mudo);margin:0;
  letter-spacing:.1em;text-transform:uppercase;font-weight:600}
.painel .preco{font-family:var(--tipo-titulo);font-size:2rem;
  color:var(--tinta);font-variant-numeric:tabular-nums;line-height:1.1;
  margin:3px 0 1px}
.painel .por{font-size:12.5px;color:var(--mudo);margin:0 0 var(--e3)}
.escaloes{width:100%;border-collapse:collapse;font-size:13.5px;
  margin:0 0 var(--e3)}
.escaloes th{text-align:left;font-weight:600;color:var(--mudo);
  font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;
  padding:0 0 7px}
.escaloes th:not(:first-child),.escaloes td:not(:first-child){text-align:right}
.escaloes td{padding:7px 0;border-top:1px solid var(--risco);
  font-variant-numeric:tabular-nums}
.escaloes tr.activo td{color:var(--tinta);font-weight:600}
.escaloes .veic{color:var(--mudo);font-size:12px}
.escaloes .pp{color:var(--mudo);font-size:12.5px}
.painel .nota{font-size:12.5px;color:var(--mudo);margin:0}
.painel .nota b{color:var(--tinta)}
.reservar{display:block;width:100%;text-align:center;margin:0 0 12px;
  min-height:46px}

/* o que a concorrencia nao mostra: o resumo do que esta incluido, ali
   mesmo ao lado do preco, para nao ser preciso ir procurar */
.lado-bloco{border:1px solid var(--risco);border-radius:var(--raio);
  padding:14px 16px;background:var(--branco)}
.lado-bloco h3{font-size:11px;letter-spacing:.11em;text-transform:uppercase;
  color:var(--mudo);font-family:var(--tipo);font-weight:600;margin:0 0 10px}
.lado-lista{list-style:none;margin:0;padding:0;display:grid;gap:7px;
  font-size:13.5px}
.lado-lista li{display:flex;gap:9px;align-items:flex-start}
.lado-lista svg{width:15px;height:15px;flex:none;margin-top:2px;fill:none;
  stroke:var(--cor-escura);stroke-width:2.6;stroke-linecap:round;
  stroke-linejoin:round}

/* o mapa pequeno */
.mapinha{overflow:hidden;border:1px solid var(--risco);
  border-radius:var(--raio);background:var(--branco)}
.mapinha svg{width:100%;height:auto;display:block;background:var(--papel)}
.mapinha .m-ctx path{fill:none;stroke:var(--risco);stroke-width:1.4}
.mapinha .m-pais path{fill:var(--papel);stroke:var(--tinta-f);
  stroke-width:1.6}
.mapinha .m-eu{fill:var(--cor);stroke:var(--branco);stroke-width:2.5}
.mapinha-pe{display:flex;align-items:center;justify-content:space-between;
  gap:8px;margin:0;padding:9px 11px;border-top:1px solid var(--risco);
  font-size:12.5px;flex-wrap:wrap}
.mapinha-pe b{color:var(--tinta)}
.mapinha-pe .cod{white-space:nowrap;font-size:10.5px;padding:2px 5px}

/* o stepper do grupo e o campo da data */
.campo-g{margin:0 0 var(--e2)}
.campo-g label{display:block;font-size:11px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--mudo);font-weight:600;margin:0 0 6px}
.stepper{display:flex;align-items:center;border:1px solid var(--risco);
  border-radius:8px;overflow:hidden}
.stepper button{flex:none;width:44px;height:42px;border:0;background:var(--papel);
  color:var(--tinta);font-size:19px;line-height:1;cursor:pointer;
  font-family:var(--tipo)}
.stepper button:hover{background:var(--cor);color:#fff}
.stepper output{flex:1;text-align:center;font-family:var(--tipo-titulo);
  font-weight:600;font-size:1.05rem;color:var(--tinta);
  font-variant-numeric:tabular-nums}
.campo-g input[type=date]{width:100%;border:1px solid var(--risco);
  border-radius:8px;padding:11px 12px;font:inherit;font-size:14.5px;
  color:var(--tinta);background:var(--branco)}
.veiculo{margin:0 0 var(--e2);font-size:13px;color:var(--mudo);
  min-height:1.3em}
.tabela-d{margin:0 0 var(--e2)}
.tabela-d summary{cursor:pointer;font-size:12.5px;color:var(--cor-escura);
  font-weight:600;list-style:none;padding:4px 0}
.tabela-d summary::-webkit-details-marker{display:none}
/* o triangulo e desenhado, nao um caractere: o \25B8 saia como caixa
   vazia porque o tipo de letra nao tem esse glifo */
.tabela-d summary::before{content:'';display:inline-block;width:0;height:0;
  border-left:5px solid currentColor;border-top:4px solid transparent;
  border-bottom:4px solid transparent;margin-right:7px;
  transition:transform .15s;vertical-align:1px}
.tabela-d[open] summary::before{transform:rotate(90deg)}

/* a lupa no canto da fotografia */
.tira figure{cursor:zoom-in}
.tira figure:focus-visible{outline:3px solid var(--cor);outline-offset:2px}
.lupa{position:absolute;left:8px;top:8px;width:26px;height:26px;
  display:grid;place-items:center;border-radius:6px;font-size:14px;
  background:rgba(255,255,255,.9);color:var(--tinta);opacity:0;
  transition:opacity .18s}
.tira figure:hover .lupa,.tira figure:focus-visible .lupa{opacity:1}

/* a caixa de luz */
.luz{position:fixed;inset:0;z-index:90;background:rgba(7,22,21,.94);
  display:grid;grid-template-columns:auto 1fr auto;align-items:center;
  gap:var(--e2);padding:var(--e3)}
.luz[hidden]{display:none}
.luz figure{margin:0;display:grid;place-items:center;gap:10px;min-height:0}
.luz img{max-width:100%;max-height:80vh;width:auto;height:auto;
  border-radius:var(--raio)}
.luz figcaption{color:rgba(255,255,255,.72);font-size:12.5px}
.luz button{background:rgba(255,255,255,.1);color:#fff;border:0;
  width:46px;height:46px;border-radius:50%;font-size:24px;line-height:1;
  cursor:pointer}
.luz button:hover{background:rgba(255,255,255,.22)}
.luz-x{position:absolute;right:var(--e3);top:var(--e3);z-index:2}
@media (max-width:620px){
  .luz{grid-template-columns:1fr;grid-template-rows:1fr auto}
  .luz-a{position:absolute;left:10px;top:50%}
  .luz-p{position:absolute;right:10px;top:50%}
}

.reservar-bloco{padding:var(--e3)}
.reservar-bloco h2{margin-bottom:6px}
.relacionados{padding:var(--e5) 0}
.relacionados h2{font-size:1.35rem;margin:0 0 var(--e3)}
</style>'''


def grande_url(fid):
    return ('https://images.unsplash.com/photo-%s?auto=format&crop=entropy'
            '&cs=tinysrgb&fit=max&fm=jpg&q=82&w=1800' % fid)


def mapa_cidade(t):
    """Um mapa pequeno com a cidade de partida marcada.

    Os contornos vem do Natural Earth e o ponto da coordenada real do
    GeoNames — o mesmo atlas da homepage. Nao e um enfeite: e a resposta
    a pergunta "onde e isto ao certo", que e das primeiras que se faz
    quando se compara dois dias."""
    caminho = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'assets', 'atlas.json')
    if not os.path.exists(caminho):
        return ''
    a = json.load(open(caminho))
    c = a['cidades'].get(t['city'])
    if not c:
        return ''
    vb = a['viewBox']
    # janela apertada a volta da cidade, para se ver onde ela esta sem o
    # mapa inteiro da Europa
    lado = 300.0
    x0 = max(0, min(vb[2] - lado, c['x'] - lado / 2))
    y0 = max(0, min(vb[3] - lado * .72, c['y'] - lado * .36))
    paises = ''.join('<path d="%s"/>' % p['d'] for p in a['paises_com_tours'])
    ctx = ''.join('<path d="%s"/>' % p['d'] for p in a['paises_contexto'])
    graus = '%.4f&deg; %s &nbsp;%.4f&deg; %s' % (
        abs(c['lat']), 'N' if c['lat'] >= 0 else 'S',
        abs(c['lon']), 'E' if c['lon'] >= 0 else 'W')
    return '''<div class="mapinha moldura">
  <svg viewBox="%(x0).0f %(y0).0f %(l).0f %(a).0f" aria-hidden="true">
    <g class="m-ctx">%(ctx)s</g>
    <g class="m-pais">%(paises)s</g>
    <circle class="m-eu" cx="%(cx).1f" cy="%(cy).1f" r="7"/>
  </svg>
  <p class="mapinha-pe"><b>%(cidade)s</b><span class="cod num">%(graus)s</span></p>
</div>''' % {'x0': x0, 'y0': y0, 'l': lado, 'a': lado * .72,
               'ctx': ctx, 'paises': paises, 'cx': c['x'], 'cy': c['y'],
               'cidade': e(t['city']), 'graus': graus}


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
    return ('<section class="sec faq" data-rev>'
            '<p class="rot"><b>04</b> Questions</p>'
            '<h2>Before you ask</h2>%s</section>'
            % '\n'.join(linhas))


def painel(t):
    d = t['durations'][0]
    menor = min(d['tiers'], key=lambda x: x['price'])
    maior = max(d['tiers'], key=lambda x: x['max'])
    linhas = []
    for x in d['tiers']:
        linhas.append(
            '<tr data-tier="%d"><td>Up to %d<span class="veic">%s</span></td>'
            '<td class="num">&euro;%s</td>'
            '<td class="num pp">&euro;%s</td></tr>'
            % (x['max'], x['max'],
               (' &middot; ' + e(x['vehicle'])) if x.get('vehicle') else '',
               euros(x['price']), euros(round(x['price'] / x['max']))))

    tiers_json = json.dumps([{'max': x['max'], 'price': x['price'],
                             'vehicle': x.get('vehicle', '')}
                            for x in d['tiers']])
    horas = json.dumps(d.get('startTimes') or [])

    return '''<aside class="painel" data-painel
  data-tiers='%(tiers)s' data-horas='%(horas)s'>
  <p class="desde">Your price</p>
  <p class="preco"><span data-preco>&euro;%(preco)s</span></p>
  <p class="por"><span data-por>for the whole group, up to %(min)d people</span></p>

  <div class="campo-g">
    <label for="pessoas">How many of you?</label>
    <div class="stepper">
      <button type="button" data-menos aria-label="One fewer person">&minus;</button>
      <output id="pessoas" data-pessoas aria-live="polite">%(min)d</output>
      <button type="button" data-mais aria-label="One more person">+</button>
    </div>
  </div>

  <div class="campo-g">
    <label for="quando">Which day?</label>
    <input id="quando" type="date" data-data>
  </div>

  <p class="veiculo" data-veiculo></p>

  <a class="botao reservar" href="#book" data-ir>Check this date</a>

  <details class="tabela-d">
    <summary>All group sizes</summary>
    <table class="escaloes">
      <thead><tr><th>Group</th><th>Total</th><th>Per person</th></tr></thead>
      <tbody>%(linhas)s</tbody>
    </table>
  </details>

  <p class="nota">The price is for the <b>whole vehicle</b>, not per person.
    Four people pay the same as one.</p>
</aside>''' % {'preco': euros(menor['price']), 'min': menor['max'],
                 'maximo': maior['max'], 'linhas': '\n'.join(linhas),
                 'tiers': tiers_json, 'horas': horas}


JS_FIXA = r"""
(function () {
  // A barra com o preco so aparece depois de o heroi sair do ecra: antes
  // disso o preco ja esta a vista no painel, e duas barras ao mesmo
  // tempo e ruido.
  var barra = document.querySelector('[data-fixa]');
  var heroi = document.querySelector('.heroi-t');
  if (!barra || !heroi || !('IntersectionObserver' in window)) return;
  new IntersectionObserver(function (es) {
    barra.classList.toggle('vis', !es[0].isIntersecting);
  }, { rootMargin: '-60px 0px 0px 0px' }).observe(heroi);
})();
"""


JS_PAINEL = r"""
(function () {
  // O painel responde: escolhe-se o tamanho do grupo e o preco muda para
  // o escalao certo, com o veiculo que o leva. Nenhum dos dois grandes
  // faz isto, porque vendem lugares e nao veiculos.
  var p = document.querySelector('[data-painel]');
  if (!p) return;
  var tiers = JSON.parse(p.getAttribute('data-tiers'));
  var horas = JSON.parse(p.getAttribute('data-horas') || '[]');
  var saidaPreco = p.querySelector('[data-preco]');
  var saidaPor = p.querySelector('[data-por]');
  var saidaPes = p.querySelector('[data-pessoas]');
  var saidaVeic = p.querySelector('[data-veiculo]');
  var data = p.querySelector('[data-data]');
  var minimo = 1;
  var maximo = tiers[tiers.length - 1].max;
  var n = tiers[0].max;

  function dinheiro(v) {
    var s = (Math.round(v * 100) / 100).toFixed(2).replace('.00', '');
    var ps = s.split('.');
    ps[0] = ps[0].replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
    return ps.join('.');
  }

  function escalao(k) {
    for (var i = 0; i < tiers.length; i++) if (k <= tiers[i].max) return tiers[i];
    return tiers[tiers.length - 1];
  }

  function pintar() {
    var t = escalao(n);
    saidaPreco.textContent = '€' + dinheiro(t.price);
    saidaPes.textContent = n;
    saidaPor.textContent = 'for ' + n + (n === 1 ? ' person' : ' people')
      + ' · €' + dinheiro(Math.round(t.price / n)) + ' each';
    saidaVeic.textContent = t.vehicle
      ? t.vehicle + (horas.length ? ' · departs ' + horas[0] : '')
      : (horas.length ? 'Departs ' + horas[0] : '');
    var trs = p.querySelectorAll('tr[data-tier]');
    for (var j = 0; j < trs.length; j++) {
      trs[j].classList.toggle('activo',
        parseInt(trs[j].getAttribute('data-tier'), 10) === t.max);
    }
  }

  p.querySelector('[data-menos]').addEventListener('click', function () {
    if (n > minimo) { n--; pintar(); }
  });
  p.querySelector('[data-mais]').addEventListener('click', function () {
    if (n < maximo) { n++; pintar(); }
  });
  // nao se aceitam datas passadas: um campo que deixa escolher ontem e um
  // campo que ainda nao foi pensado
  if (data) { data.min = new Date().toISOString().slice(0, 10); }
  pintar();
})();
"""


JS_GALERIA = r"""
(function () {
  // As fotografias abrem em grande. Setas, Escape, foco preso dentro da
  // caixa e devolvido ao sitio de onde se saiu — senao quem navega por
  // teclado fica perdido atras da imagem.
  var figs = [].slice.call(document.querySelectorAll('[data-foto]'));
  if (!figs.length) return;
  var i = 0, antes = null;
  var cx = document.createElement('div');
  cx.className = 'luz';
  cx.setAttribute('role', 'dialog');
  cx.setAttribute('aria-modal', 'true');
  cx.setAttribute('aria-label', 'Photograph');
  cx.hidden = true;
  cx.innerHTML = '<button class="luz-x" aria-label="Close">&times;</button>'
    + '<button class="luz-a" aria-label="Previous">&#8249;</button>'
    + '<figure><img alt=""><figcaption></figcaption></figure>'
    + '<button class="luz-p" aria-label="Next">&#8250;</button>';
  document.body.appendChild(cx);
  var im = cx.querySelector('img');
  var cap = cx.querySelector('figcaption');

  function mostrar(k) {
    i = (k + figs.length) % figs.length;
    var f = figs[i];
    im.src = f.getAttribute('data-grande');
    im.alt = f.getAttribute('data-alt') || '';
    cap.textContent = f.getAttribute('data-credito') || '';
  }
  function abrir(k) {
    antes = document.activeElement;
    mostrar(k);
    cx.hidden = false;
    document.body.style.overflow = 'hidden';
    cx.querySelector('.luz-x').focus();
  }
  function fechar() {
    cx.hidden = true;
    document.body.style.overflow = '';
    if (antes) antes.focus();
  }
  figs.forEach(function (f, k) {
    f.addEventListener('click', function () { abrir(k); });
    f.addEventListener('keydown', function (ev) {
      if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); abrir(k); }
    });
  });
  cx.querySelector('.luz-x').addEventListener('click', fechar);
  cx.querySelector('.luz-a').addEventListener('click', function () { mostrar(i - 1); });
  cx.querySelector('.luz-p').addEventListener('click', function () { mostrar(i + 1); });
  cx.addEventListener('click', function (ev) { if (ev.target === cx) fechar(); });
  document.addEventListener('keydown', function (ev) {
    if (cx.hidden) return;
    if (ev.key === 'Escape') fechar();
    else if (ev.key === 'ArrowLeft') mostrar(i - 1);
    else if (ev.key === 'ArrowRight') mostrar(i + 1);
    else if (ev.key === 'Tab') {
      var fs = cx.querySelectorAll('button');
      var pri = fs[0], ult = fs[fs.length - 1];
      if (ev.shiftKey && document.activeElement === pri) { ev.preventDefault(); ult.focus(); }
      else if (!ev.shiftKey && document.activeElement === ult) { ev.preventDefault(); pri.focus(); }
    }
  });
})();
"""


def main():
    tours = carregar()
    paises = por_pais(tours)
    por_slug = {t['slug']: t for t in tours}
    tirados = []

    for t in tours:
        d = t['durations'][0]
        fotos = t.get('photos') or []
        # a primeira fotografia e o heroi, a sangrar; as outras ficam numa
        # tira por baixo. A Viator e a GetYourGuide poem uma grelha de
        # miniaturas; quem compra um dia quer ver o sitio grande primeiro.
        heroi_img = (img(fotos[0]['id'], fotos[0]['alt'], (900, 1600, 2200),
                         '100vw', eager=True) if fotos else '')
        tira = ''
        if len(fotos) > 1:
            figs = []
            for f in fotos[1:4]:
                figs.append(
                    '<figure data-foto tabindex="0" role="button" '
                    'aria-label="Open photograph" data-grande="%s" '
                    'data-alt="%s" data-credito="Photo %s">'
                    '%s<figcaption>Photo %s</figcaption>'
                    '<span class="lupa" aria-hidden="true">&#8599;</span>'
                    '</figure>'
                    % (e(grande_url(f['id'])), e(f['alt']), e(f['by']),
                       img(f['id'], f['alt'], (500, 900),
                           '(min-width:700px) 33vw, 50vw'), e(f['by'])))
            tira = ('<div class="folha"><div class="tira">%s</div></div>'
                    % '\n'.join(figs))

        # o resumo do que esta incluido, ao lado do preco. A concorrencia
        # obriga a ir procurar isto no fundo da pagina.
        lado_inclui = ''
        if t.get('included'):
            lado_inclui = ('<div class="lado-bloco"><h3>Included</h3>'
                           '<ul class="lado-lista">%s</ul></div>'
                           % '\n'.join('<li>%s<span>%s</span></li>' % (VISTO, e(x))
                                       for x in t['included'][:5]))

        irmaos = [x for x in tours
                  if x['countryName'] == t['countryName'] and x['slug'] != t['slug']]
        irmaos = sorted(irmaos, key=lambda x: x['_preco'])[:3]

        corpo = '''%(cabecalho)s

<div class="fixa" data-fixa>
  <div class="folha">
    <span class="fixa-t">%(titulo_curto)s</span>
    <span class="fixa-p">from <b>&euro;%(menor)s</b> &middot; whole group</span>
    <a class="botao" href="#book">Check this date</a>
  </div>
</div>

<main id="principal">

<header class="heroi-t">
  <div class="foto">%(heroi_img)s</div>
  <div class="folha">
    <nav class="migalhas" aria-label="Breadcrumb">
      <a href="/">Home</a> &rsaquo;
      <a href="/tours/?country=%(cod)s">%(pais)s</a> &rsaquo;
      <span>%(cidade)s</span>
    </nav>
    <p class="t-kicker">%(kicker)s</p>
    <h1>%(titulo)s</h1>
    <p class="t-lede">%(lede)s</p>
    <div class="factos">%(factos)s</div>
  </div>
</header>

%(tira)s

<section class="banda-e" data-rev>
  <div class="folha bloco">
    <p class="rot"><b>01</b> The day</p>
    <h2>From %(cidade)s, door to door</h2>
    <p class="intro">%(stopsIntro)s</p>
    %(fita)s
    %(paragens)s
  </div>
</section>

<div class="folha bloco">
  <div class="t-grelha">
    <div>
      <section class="sec" data-rev>
        <p class="rot"><b>02</b> What the price covers</p>
        <h2>The vehicle, not the seat</h2>
        <p class="intro">%(includedIntro)s</p>
        <ul class="inclui">%(inclui)s</ul>
        <p class="nao-inclui">%(naoInclui)s</p>
      </section>

      <section class="sec" data-rev>
        <p class="rot"><b>03</b> Practical</p>
        <h2>Before the day</h2>
        <table class="pratico"><tbody>%(pratico)s</tbody></table>
      </section>

      %(faq)s

      <section class="sec moldura reservar-bloco" id="book" data-rev>
        <p class="rot"><b>05</b> Booking</p>
        <h2>How to book</h2>
        <p class="intro">Online booking opens shortly. Until then, tell us the
          date and the size of your group and we will come back to you with the
          exact price and a hold on the day.</p>
      </section>
    </div>

    <div class="lado">
      %(painel)s
      %(lado_inclui)s
      %(mapa)s
    </div>
  </div>
</div>

%(relacionados)s
</main>
%(rodape)s''' % {
            'cabecalho': cabecalho(),
            'cod': e(t['country']), 'pais': e(t['countryName']),
            'cidade': e(t['city']),
            'kicker': e(t.get('kicker') or ''), 'titulo': e(t['title']),
            'titulo_curto': e(t['title'].replace('Private Tour: ', '')),
            'menor': euros(t['_preco']),
            'lede': e(t.get('lede') or ''),
            'heroi_img': heroi_img, 'tira': tira,
            'lado_inclui': lado_inclui,
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
            'faq': faq(t, tirados), 'mapa': mapa_cidade(t),
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
            CSS, corpo, js=procura.JS + JS_FIXA + JS_PAINEL + JS_GALERIA)
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
