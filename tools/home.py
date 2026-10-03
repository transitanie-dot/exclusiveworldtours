#!/usr/bin/env python3
"""
A homepage da Exclusive World Tours.

Marketplace de dias privados, com a marca escolhida (A5, a faixa) e o
sistema de duas cores sem degrade.

Tudo o que esta na pagina sai de dados verdadeiros:

  tools/tours.json    os 36 tours — titulo, cidade, pais, duracao, os
                      escaloes de preco por veiculo, as horas de partida
                      e as fotografias com o credito do fotografo;
  assets/atlas.json   a geometria dos paises (Natural Earth) e as
                      coordenadas das 19 cidades de partida (GeoNames).

Nao ha aqui um numero escrito a mao. Os "36 tours", os "6 paises" e as
"19 cidades" sao contados no momento de gerar; se amanha o tours.json
mudar, a pagina muda com ele. Um numero escrito a mao numa homepage e
uma mentira a espera de acontecer.

O que NAO esta na pagina, e e de proposito: avaliacoes, testemunhos,
numero de clientes, "desde 2023", parceiros, e qualquer frase sobre
operadores locais. Isso e da The Epic Tours ou ainda nao e verdade
nesta marca, e inventa-se num segundo e desmente-se durante anos.

    python3 tools/home.py          # escreve index.html
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pagina  # noqa: E402
import procura  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

from pagina import (CORES, cabecalho, cartao_tour, carregar, e,  # noqa: E402
                    envolver, escrever, euros, img, por_pais, rodape,
                    verificar_contraste)

def mapa_svg(tours):
    """O mapa dos destinos, com as coordenadas reais.

    Era isto o elemento de assinatura que o Ricardo pediu no inicio: as
    coordenadas verdadeiras de cada destino, nao enfeite. Os paises vem
    do Natural Earth e os pontos do GeoNames; nenhum dos dois foi
    desenhado por mim."""
    caminho = os.path.join(RAIZ, 'assets', 'atlas.json')
    if not os.path.exists(caminho):
        return ''
    a = json.load(open(caminho))
    vb = a['viewBox']
    partidas = {t['city'] for t in tours}
    paises = ''.join('<path d="%s"/>' % p['d'] for p in a['paises_com_tours'])
    contexto = ''.join('<path d="%s"/>' % p['d'] for p in a['paises_contexto'])
    pontos = []
    for nome, c in sorted(a['cidades'].items()):
        if nome not in partidas:
            continue
        pontos.append('<circle cx="%.1f" cy="%.1f" r="7"/>' % (c['x'], c['y']))
    return (
        '<svg class="mapa" viewBox="0 0 %g %g" aria-hidden="true" '
        'preserveAspectRatio="xMidYMid meet">'
        '<g class="mapa-contexto">%s</g>'
        '<g class="mapa-paises">%s</g>'
        '<g class="mapa-pontos">%s</g>'
        '</svg>' % (vb[2], vb[3], contexto, paises, ''.join(pontos)))


# ------------------------------------------------------------------ pecas

def cartao_pais(p, i):
    foto = p['foto']
    media = (img(foto['id'], foto['alt'], (400, 800),
                 '(min-width:1100px) 25vw, (min-width:700px) 33vw, 50vw')
             if foto else '')
    return '''<a class="pais" href="/tours/?country=%(cod)s">
  <span class="pais-foto">%(media)s</span>
  <span class="pais-txt">
    <span class="pais-nome">%(nome)s</span>
    <span class="pais-meta">%(n)d %(dia)s &middot; from &euro;%(menor)s</span>
  </span>
</a>''' % {'cod': e(p['cod']), 'media': media, 'nome': e(p['nome']),
           'n': p['n'], 'dia': 'day tour' if p['n'] == 1 else 'day tours',
           'menor': euros(p['menor'])}


def css():
    """So o que e desta pagina. O resto vem de pagina.css_base()."""
    return ('''
/* ----------------------------------------------------------------- heroi */
.heroi{position:relative;background:var(--tinta);color:var(--branco)}
/* sem overflow:hidden aqui: era ele que cortava a lista de sugestoes da
   procura. Quem recorta a fotografia e a camada da fotografia. */
.heroi-foto{position:absolute;inset:0;overflow:hidden}
.heroi-foto img{width:100%%;height:100%%;object-fit:cover}
.heroi::after{content:'';position:absolute;inset:0;
  background:linear-gradient(100deg,
    rgba(11,43,42,.93) 0%%, rgba(11,43,42,.82) 46%%,
    rgba(11,43,42,.46) 76%%, rgba(11,43,42,.30) 100%%)}
.heroi-i{position:relative;z-index:2;padding:84px 0 92px;max-width:720px}
.heroi h2{color:var(--branco);
  font-size:clamp(2.3rem, 1.3rem + 3.4vw, 4rem);margin:0 0 18px}
.heroi p{font-size:clamp(1.05rem, .98rem + .4vw, 1.3rem);
  color:rgba(255,255,255,.88);margin:0 0 34px;max-width:33em}

/* a barra de procura: o CSS dela vive em tools/procura.py, junto com o
   comportamento, porque as duas coisas so fazem sentido juntas */
.procura{max-width:620px}
/* a linha de numeros, toda contada a partir dos dados */
.numeros{display:flex;flex-wrap:wrap;gap:14px 40px;margin-top:40px;
  padding-top:26px;border-top:1px solid rgba(255,255,255,.22)}
.numero b{display:block;font-family:var(--tipo-titulo);font-weight:700;
  font-size:1.6rem;color:var(--branco);line-height:1.1}
.numero span{font-size:14px;color:rgba(255,255,255,.78)}

/* ---------------------------------------------------------------- blocos */
.bloco{padding:84px 0}
.bloco-cab{display:flex;align-items:flex-end;justify-content:space-between;
  gap:24px;margin-bottom:34px;flex-wrap:wrap}
.bloco h2{font-size:clamp(1.7rem, 1.2rem + 1.6vw, 2.5rem)}
.bloco-cab p{margin:10px 0 0;color:var(--mudo);max-width:52ch}
.ligacao{color:var(--cor-escura);font-weight:600;text-decoration:none;
  white-space:nowrap}
.ligacao:hover{text-decoration:underline}

/* paises */
.paises{display:grid;gap:16px;grid-template-columns:repeat(3,1fr)}
@media (max-width:860px){.paises{grid-template-columns:repeat(2,1fr)}}
@media (max-width:460px){.paises{grid-template-columns:1fr}}
.pais{position:relative;display:block;border-radius:var(--raio);
  overflow:hidden;text-decoration:none;aspect-ratio:4/3;background:var(--tinta)}
.pais-foto{position:absolute;inset:0}
.pais-foto img{width:100%%;height:100%%;object-fit:cover}
.pais::after{content:'';position:absolute;inset:0;
  background:linear-gradient(to top, rgba(11,43,42,.92) 8%%,
    rgba(11,43,42,.22) 58%%, rgba(11,43,42,.08) 100%%)}
.pais-txt{position:absolute;left:18px;right:18px;bottom:16px;z-index:2;
  display:flex;flex-direction:column;gap:3px}
.pais-nome{font-family:var(--tipo-titulo);font-weight:600;font-size:1.15rem;
  color:var(--branco)}
.pais-meta{font-size:13.5px;color:rgba(255,255,255,.86)}
.pais:hover .pais-foto img{transform:scale(1.04)}
.pais-foto img{transition:transform .5s ease}

/* o mapa dos destinos */
.atlas{background:var(--tinta);color:var(--branco)}
.atlas h2{color:var(--branco)}
.atlas p{color:rgba(255,255,255,.82);max-width:46ch}
.atlas-i{display:grid;grid-template-columns:1fr 1fr;gap:56px;
  align-items:center}
@media (max-width:900px){.atlas-i{grid-template-columns:1fr;gap:34px}}
/* O mapa inteiro, nao um recorte. Estava em `slice` por tras da seccao e
   via-se so o meio da Europa — um mapa que corta os destinos que e
   suposto mostrar nao esta a mostrar nada. */
.mapa{width:100%%;height:auto;max-height:440px;display:block}
.mapa-contexto path{fill:none;stroke:rgba(255,255,255,.14);stroke-width:1.2}
.mapa-paises path{fill:rgba(255,255,255,.07);stroke:rgba(255,255,255,.3);
  stroke-width:1.4}
.mapa-pontos circle{fill:%(cor)s}
.coords{display:flex;flex-wrap:wrap;gap:8px 10px;margin-top:26px;
  font-variant-numeric:tabular-nums;font-size:13px}
.coord{border:1px solid rgba(255,255,255,.28);border-radius:999px;
  padding:4px 12px;color:rgba(255,255,255,.92)}

/* como funciona */
.passos{display:grid;gap:26px;
  grid-template-columns:repeat(auto-fit,minmax(min(100%%,240px),1fr))}
.passo{display:flex;flex-direction:column;gap:9px}
.passo-n{width:34px;height:34px;border-radius:50%%;background:var(--cor);
  color:var(--branco);display:grid;place-items:center;font-weight:700;
  font-family:var(--tipo-titulo);font-size:15px}
.passo h3{font-size:1.1rem}
.passo p{margin:0;color:var(--mudo);font-size:15.5px}
''' % CORES)


def main():
    verificar_contraste()
    tours = carregar()
    paises = por_pais(tours)
    cidades = sorted({t['city'] for t in tours})
    menor = min(t['_preco'] for t in tours)

    # o heroi usa a fotografia do tour mais barato do pais com mais tours,
    # para a imagem nunca ser uma escolha minha que ninguem consegue refazer
    heroi_t = max(tours, key=lambda t: (t['countryName'] == paises[0]['nome'],
                                        -t['_preco']))
    hf = heroi_t['_foto']

    destaques = []
    vistos = set()
    for p in paises:                       # um de cada pais, o mais barato
        t = min(p['tours'], key=lambda x: x['_preco'])
        destaques.append(t)
        vistos.add(t['slug'])
    for t in sorted(tours, key=lambda x: x['_preco']):
        if len(destaques) >= 9:
            break
        if t['slug'] not in vistos:
            destaques.append(t)
            vistos.add(t['slug'])

    coords = json.load(open(os.path.join(RAIZ, 'assets', 'atlas.json')))['cidades']
    def grau(c):
        return '%.4f&deg;&nbsp;%s&nbsp; %.4f&deg;&nbsp;%s' % (
            abs(c['lat']), 'N' if c['lat'] >= 0 else 'S',
            abs(c['lon']), 'E' if c['lon'] >= 0 else 'W')
    tres = [c for n, c in sorted(coords.items()) if n in {t['city'] for t in tours}][:4]

    corpo = '''%(cabecalho)s
<main id="principal">

<section class="heroi">
  <div class="heroi-foto">%(heroi_img)s</div>
  <div class="folha heroi-i">
    <h2>Someone else drives. The day is yours.</h2>
    <p>Private day tours in %(np)d countries. One vehicle for your group,
      a price for the whole group instead of per person, and a start time
      set early enough to reach the place before the coaches do.</p>

    <form class="procura" action="/search/" method="get" role="search">
      %(procura)s
    </form>

    <div class="numeros">
      <div class="numero"><b>%(nt)d</b><span>private day tours</span></div>
      <div class="numero"><b>%(np)d</b><span>countries</span></div>
      <div class="numero"><b>%(nc)d</b><span>departure cities</span></div>
      <div class="numero"><b>&euro;%(menor)s</b><span>lowest price for a whole group</span></div>
    </div>
  </div>
</section>

<section class="bloco folha" id="destinations">
  <div class="bloco-cab">
    <div>
      <h2>Where we go</h2>
      <p>Every tour below leaves from a real address in one of these countries,
        on a date you choose.</p>
    </div>
    <a class="ligacao" href="/tours/">See all %(nt)d tours &rarr;</a>
  </div>
  <div class="paises">%(paises)s</div>
</section>

<section class="atlas">
  <div class="folha bloco atlas-i">
    <div>
      <h2>Real places, real coordinates</h2>
      <p>The outlines come from Natural Earth and every dot is the actual
        coordinate of a city our days leave from, taken from GeoNames.
        Nothing on this map was drawn by hand.</p>
      <div class="coords">%(coords)s</div>
    </div>
    <div>%(mapa)s</div>
  </div>
</section>

<section class="bloco folha">
  <div class="bloco-cab">
    <div>
      <h2>Days worth getting up for</h2>
      <p>One from each country, starting with the lowest price. The price
        shown is for the whole group, not per person.</p>
    </div>
    <a class="ligacao" href="/tours/">Browse everything &rarr;</a>
  </div>
  <div class="tours">%(tours)s</div>
</section>

<section class="bloco folha" id="how">
  <div class="bloco-cab"><div><h2>How it works</h2></div></div>
  <div class="passos">
    <div class="passo">
      <span class="passo-n">1</span>
      <h3>Pick the day</h3>
      <p>Every tour has a fixed route, a fixed length and a start time.
        You can see all of it before you decide anything.</p>
    </div>
    <div class="passo">
      <span class="passo-n">2</span>
      <h3>Price by group, not per head</h3>
      <p>You book a vehicle, not a seat. Four people pay the same as one,
        and the price only changes when the group needs a bigger vehicle.</p>
    </div>
    <div class="passo">
      <span class="passo-n">3</span>
      <h3>Nobody else comes</h3>
      <p>The vehicle carries your group and nobody else. That is what makes
        an early start possible, and an early start is the whole point.</p>
    </div>
  </div>
</section>

</main>

%(rodape)s''' % {

                'cabecalho': cabecalho(marca_titulo=True),
        'rodape': rodape(paises),
        'ndesc': len(tours), 'nt': len(tours), 'np': len(paises),
        'nc': len(cidades), 'menor': euros(menor), 'ano': 2026,
        'heroi_img': (img(hf['id'], hf['alt'], (900, 1600, 2200),
                          '100vw', eager=True) if hf else ''),
        'procura': procura.HTML,
        'paises': '\n'.join(cartao_pais(p, i) for i, p in enumerate(paises)),
        'tours': '\n'.join(cartao_tour(t, i == 0)
                           for i, t in enumerate(destaques)),
        'mapa': mapa_svg(tours),
        'coords': '\n'.join('<span class="coord">%s &nbsp;%s</span>'
                            % (e(c['nome']), grau(c)) for c in tres),
    }


    html = envolver(
        'Exclusive World Tours \u2014 private day tours, priced by the group',
        '%d private day tours in %d countries. One vehicle for your group, '
        'a price for the whole group instead of per person.'
        % (len(tours), len(paises)),
        css(), corpo, js=procura.JS)

    escrever(html, 'index.html')
    print('%d tours, %d paises, %d cidades, menor preco %s'
          % (len(tours), len(paises), len(cidades), menor))


if __name__ == '__main__':
    main()
