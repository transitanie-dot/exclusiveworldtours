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

from marca import CSS as CSS_MARCA, lockup, marca_mini  # noqa: E402
from marca_base import PALETA, contraste, misturar  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

UNS = 'https://images.unsplash.com/photo-'

# ----------------------------------------------------------------- cores
#
# Tres cores e os seus tons calculados. As tintas sao cores cheias e nao
# transparencias, pela mesma razao de sempre: transparencia mistura-se
# com o que estiver por tras e muda de sitio para sitio.

TINTA = PALETA['tinta']          # #0B2B2A  verde-atlantico quase preto
COR = PALETA['cor']              # #CE7030  ambar
PAPEL = '#F6F4F1'                # o creme do fundo
BRANCO = '#FFFFFF'

CORES = {
    'tinta': TINTA, 'cor': COR, 'papel': PAPEL, 'branco': BRANCO,
    'tinta_f': misturar(TINTA, PAPEL, .30),
    'cor_f': misturar(COR, PAPEL, .52),
    'uma_f': misturar(TINTA, PAPEL, .26),
    'texto': misturar(TINTA, PAPEL, .82),     # o corpo de texto
    # .62 dava 4.31:1 sobre o creme e reprovava o minimo de 4.5 para
    # texto. A verificacao la em baixo apanhou-o antes de a pagina sair.
    'mudo': misturar(TINTA, PAPEL, .66),      # as legendas
    'risco': misturar(TINTA, PAPEL, .14),     # os filetes
    'cor_escura': '#A85426',                  # o ambar para texto pequeno
}

# Estes tem de passar a norma e nao e por acreditar em mim que passam:
# ver verificar_contraste(), que corre sempre que se gera a pagina.
MINIMOS = [
    ('texto sobre papel', 'texto', PAPEL, 4.5),
    ('mudo sobre papel', 'mudo', PAPEL, 4.5),
    ('tinta sobre papel', 'tinta', PAPEL, 4.5),
    ('papel sobre tinta', 'papel', TINTA, 4.5),
    ('ambar escuro sobre papel', 'cor_escura', PAPEL, 4.5),
    ('ambar sobre tinta', 'cor', TINTA, 3.0),
    ('papel sobre ambar', 'papel', COR, 3.0),
]


def verificar_contraste():
    maus = []
    for nome, chave, fundo, minimo in MINIMOS:
        r = contraste(CORES[chave], fundo)
        if r < minimo:
            maus.append('%s: %.2f:1 (minimo %.1f)' % (nome, r, minimo))
    if maus:
        sys.exit('Contraste insuficiente — nao gero a pagina assim:\n  '
                 + '\n  '.join(maus))


# ------------------------------------------------------------------ util

def e(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def img(fid, alt, larguras, sizes, classe='', eager=False):
    """Uma fotografia do Unsplash, com srcset e com rede de seguranca.

    Por baixo de cada fotografia ha sempre uma cor cheia. Se a imagem nao
    carregar — ligacao lenta, dominio bloqueado, o que for — o `onerror`
    esconde-a e fica a cor, que e legivel e nao parece avariado."""
    def u(w):
        return ('%s%s?auto=format&crop=entropy&cs=tinysrgb&fit=crop'
                '&fm=jpg&q=74&w=%d' % (UNS, fid, w))
    return ('<img class="%s" src="%s" srcset="%s" sizes="%s" alt="%s" '
            '%s decoding="async" '
            'onerror="this.style.display=&quot;none&quot;">'
            % (classe, u(larguras[-1]),
               ', '.join('%s %dw' % (u(w), w) for w in larguras),
               sizes, e(alt),
               'fetchpriority="high"' if eager else 'loading="lazy"'))


def euros(v):
    """Com separador de milhares fino e com os centimos quando existem.

    A primeira versao fazia int(v) e 159.90 saia "159" — menos noventa
    centimos do que o preco verdadeiro. Numa pagina de precos isso nao e
    um arredondamento, e um numero errado."""
    v = float(v)
    inteiro = '{:,}'.format(int(v)).replace(',', '\u202f')
    return inteiro if v.is_integer() else '%s.%02d' % (
        inteiro, round((v % 1) * 100))


# ------------------------------------------------------------------ dados

def carregar():
    tours = json.load(open(os.path.join(AQUI, 'tours.json')))['tours']
    for t in tours:
        d = t['durations'][0]
        t['_h'] = d['h']
        t['_tiers'] = d['tiers']
        t['_preco'] = min(x['price'] for x in d['tiers'])
        t['_max'] = max(x['max'] for x in d['tiers'])
        t['_menor'] = min(d['tiers'], key=lambda x: x['price'])
        t['_partida'] = (d.get('startTimes') or [None])[0]
        t['_foto'] = (t.get('photos') or [None])[0]
    return tours


def por_pais(tours):
    """Os paises por numero de tours. A ordem sai dos dados — nao e uma
    lista que eu escolhi."""
    paises = {}
    for t in tours:
        p = paises.setdefault(t['countryName'], {
            'nome': t['countryName'], 'cod': t['country'], 'tours': [],
            'cidades': set()})
        p['tours'].append(t)
        p['cidades'].add(t['city'])
    for p in paises.values():
        p['n'] = len(p['tours'])
        p['menor'] = min(x['_preco'] for x in p['tours'])
        p['foto'] = next((x['_foto'] for x in p['tours'] if x['_foto']), None)
    return sorted(paises.values(), key=lambda p: (-p['n'], p['nome']))


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
    return '''<a class="pais" href="/tours/#%(cod)s">
  <span class="pais-foto">%(media)s</span>
  <span class="pais-txt">
    <span class="pais-nome">%(nome)s</span>
    <span class="pais-meta">%(n)d %(dia)s &middot; from &euro;%(menor)s</span>
  </span>
</a>''' % {'cod': e(p['cod']), 'media': media, 'nome': e(p['nome']),
           'n': p['n'], 'dia': 'day tour' if p['n'] == 1 else 'day tours',
           'menor': euros(p['menor'])}


def cartao_tour(t, destaque=False):
    foto = t['_foto']
    media = (img(foto['id'], foto['alt'], (560, 900),
                 '(min-width:1100px) 33vw, (min-width:700px) 50vw, 100vw',
                 eager=destaque)
             if foto else '')
    credito = ('<span class="credito">Photo %s</span>'
               % e(foto['by'])) if foto else ''
    tier = t['_menor']
    return '''<a class="tour" href="/tours/%(slug)s/">
  <span class="tour-foto">%(media)s%(credito)s</span>
  <span class="tour-corpo">
    <span class="tour-onde">%(cidade)s, %(pais)s</span>
    <span class="tour-nome">%(titulo)s</span>
    <span class="tour-linha">
      <span class="etiq">%(h)s</span>
      <span class="etiq">up to %(max)d</span>
      %(partida)s
    </span>
    <span class="tour-preco">
      <b>&euro;%(preco)s</b>
      <span class="tour-preco-nota">total for up to %(tmax)d%(veic)s</span>
    </span>
  </span>
</a>''' % {
        'slug': e(t['slug']), 'media': media, 'credito': credito,
        'cidade': e(t['city']), 'pais': e(t['countryName']),
        'titulo': e(t['title'].replace('Private Tour: ', '')),
        'h': e(t['_h']), 'max': t['_max'],
        'partida': ('<span class="etiq">departs %s</span>' % e(t['_partida'])
                    if t['_partida'] else ''),
        'preco': euros(tier['price']), 'tmax': tier['max'],
        # dois dos tours sao caminhadas fotograficas e nao tem veiculo
        # nenhum. Em vez de inventar um, a linha fica sem ele.
        'veic': (' &middot; ' + e(tier['vehicle'])) if tier.get('vehicle') else '',
    }


# -------------------------------------------------------------------- css

def css():
    return ('''
:root{
  --tinta:%(tinta)s; --cor:%(cor)s; --cor-escura:%(cor_escura)s;
  --papel:%(papel)s; --branco:%(branco)s;
  --tinta-f:%(tinta_f)s; --cor-f:%(cor_f)s; --uma-f:%(uma_f)s;
  --texto:%(texto)s; --mudo:%(mudo)s; --risco:%(risco)s;
  --tipo:'Inter',system-ui,-apple-system,sans-serif;
  --tipo-titulo:'Archivo','Inter',system-ui,sans-serif;
  --raio:14px;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%%;scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}
  *,*::before,*::after{animation-duration:.01ms !important;
    transition-duration:.01ms !important}}
body{margin:0;background:var(--branco);color:var(--texto);
  font-family:var(--tipo);font-size:17px;line-height:1.6;
  -webkit-font-smoothing:antialiased}
img{max-width:100%%;display:block}
a{color:inherit}
h1,h2,h3{font-family:var(--tipo-titulo);color:var(--tinta);
  letter-spacing:-.025em;line-height:1.08;margin:0}
.folha{max-width:1240px;margin:0 auto;padding:0 24px}
/* So aparece a quem navega por teclado — mas aparece mesmo, que e o
   ponto. Escondido com left:-9999px e sem regra de foco, este atalho
   existe no HTML e nao serve a ninguem. */
.saltar{position:absolute;left:16px;top:-60px;z-index:60;background:var(--tinta);
  color:var(--branco);padding:12px 18px;border-radius:0 0 10px 10px;
  text-decoration:none;font-weight:600;transition:top .15s ease}
.saltar:focus{top:0}

/* ------------------------------------------------------------ cabecalho */
.topo{position:sticky;top:0;z-index:40;background:rgba(255,255,255,.92);
  backdrop-filter:saturate(180%%) blur(12px);
  border-bottom:1px solid var(--risco)}
.topo-i{display:flex;align-items:center;gap:28px;height:74px}
.nav{display:flex;gap:26px;margin-left:auto;font-size:15px;font-weight:500}
.nav a{text-decoration:none;color:var(--texto);padding:6px 0;
  border-bottom:2px solid transparent}
.nav a:hover{color:var(--tinta);border-bottom-color:var(--cor)}
.topo .marca{color:var(--tinta)}
@media (max-width:760px){.nav{display:none}}

/* ----------------------------------------------------------------- heroi */
.heroi{position:relative;background:var(--tinta);color:var(--branco);
  overflow:hidden}
.heroi-foto{position:absolute;inset:0}
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

/* a barra de procura */
.procura{display:grid;grid-template-columns:1.5fr 1fr 1fr auto;gap:0;
  background:var(--branco);border-radius:var(--raio);padding:7px;
  box-shadow:0 18px 46px -22px rgba(11,43,42,.55)}
.campo{display:flex;flex-direction:column;gap:2px;padding:10px 16px;
  border-right:1px solid var(--risco);min-width:0}
.campo:nth-child(3){border-right:0}
.campo label{font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--mudo);font-weight:600}
.campo select,.campo input{border:0;padding:0;font:inherit;font-size:15px;
  color:var(--tinta);background:transparent;width:100%%;min-width:0}
.campo select:focus-visible,.campo input:focus-visible,
a:focus-visible,button:focus-visible{outline:3px solid var(--cor);
  outline-offset:3px;border-radius:4px}
.procura .botao{margin:0 2px}
.botao{display:inline-flex;align-items:center;justify-content:center;
  background:var(--tinta);color:var(--branco);border:0;border-radius:10px;
  padding:0 26px;min-height:54px;font:inherit;font-weight:600;font-size:16px;
  cursor:pointer;text-decoration:none;white-space:nowrap}
.botao:hover{background:var(--cor-escura)}
@media (max-width:860px){
  .procura{grid-template-columns:1fr 1fr}
  .campo{border-right:0;border-bottom:1px solid var(--risco)}
  .campo:nth-child(1){grid-column:1/-1}
  .procura .botao{grid-column:1/-1;margin-top:6px}
}

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

/* tours */
.tours{display:grid;gap:22px;
  grid-template-columns:repeat(auto-fit,minmax(min(100%%,300px),1fr))}
.tour{display:flex;flex-direction:column;text-decoration:none;
  border:1px solid var(--risco);border-radius:var(--raio);overflow:hidden;
  background:var(--branco)}
.tour:hover{border-color:var(--tinta-f)}
.tour-foto{position:relative;aspect-ratio:3/2;background:var(--uma-f);
  display:block}
.tour-foto img{width:100%%;height:100%%;object-fit:cover}
.credito{position:absolute;right:8px;bottom:7px;z-index:2;font-size:10.5px;
  color:#fff;background:rgba(11,43,42,.68);padding:3px 7px;border-radius:5px}
.tour-corpo{display:flex;flex-direction:column;gap:9px;padding:18px 20px 20px;
  flex:1}
.tour-onde{font-size:12.5px;letter-spacing:.07em;text-transform:uppercase;
  color:var(--cor-escura);font-weight:600}
.tour-nome{font-family:var(--tipo-titulo);font-weight:600;font-size:1.13rem;
  color:var(--tinta);line-height:1.22}
.tour-linha{display:flex;flex-wrap:wrap;gap:7px;margin-top:2px}
.etiq{font-size:12.5px;color:var(--texto);background:var(--papel);
  border:1px solid var(--risco);border-radius:999px;padding:3px 10px}
.tour-preco{margin-top:auto;padding-top:13px;border-top:1px solid var(--risco);
  display:flex;align-items:baseline;gap:9px;flex-wrap:wrap}
.tour-preco b{font-family:var(--tipo-titulo);font-size:1.3rem;
  color:var(--tinta);font-variant-numeric:tabular-nums}
.tour-preco-nota{font-size:13px;color:var(--mudo)}

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

/* rodape */
.rodape{background:var(--papel);border-top:1px solid var(--risco);
  padding:56px 0 44px;margin-top:0}
.rodape-i{display:flex;gap:40px;flex-wrap:wrap;justify-content:space-between}
.rodape .marca{color:var(--tinta)}
.rodape-nota{color:var(--mudo);font-size:14px;max-width:40ch;margin:16px 0 0}
.rodape-cols{display:flex;gap:56px;flex-wrap:wrap}
.rodape-col h3{font-size:13px;letter-spacing:.07em;text-transform:uppercase;
  color:var(--mudo);font-family:var(--tipo);font-weight:600;margin:0 0 12px}
.rodape-col a{display:block;text-decoration:none;color:var(--texto);
  font-size:15px;padding:4px 0}
.rodape-col a:hover{color:var(--cor-escura)}
.rodape-fim{margin-top:40px;padding-top:22px;border-top:1px solid var(--risco);
  font-size:13.5px;color:var(--mudo);display:flex;gap:18px;flex-wrap:wrap;
  justify-content:space-between}
''' % CORES) + CSS_MARCA


# ------------------------------------------------------------------ pagina

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

    html = '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exclusive World Tours &mdash; private day tours, priced by the group</title>
<meta name="description" content="%(ndesc)d private day tours in %(np)d countries. One vehicle for your group, a price for the whole group instead of per person, and departure times set before the coaches arrive.">
<meta name="robots" content="noindex, nofollow">
<link rel="preload" as="font" type="font/woff2" crossorigin href="/assets/fontes/archivo-latin-600-normal.woff2">
<link rel="preload" as="font" type="font/woff2" crossorigin href="/assets/fontes/inter-latin-400-normal.woff2">
<style>
@font-face{font-family:'Inter';font-style:normal;font-weight:400;font-display:swap;
  src:url(/assets/fontes/inter-latin-400-normal.woff2) format('woff2')}
@font-face{font-family:'Inter';font-style:normal;font-weight:500;font-display:swap;
  src:url(/assets/fontes/inter-latin-500-normal.woff2) format('woff2')}
@font-face{font-family:'Inter';font-style:normal;font-weight:600;font-display:swap;
  src:url(/assets/fontes/inter-latin-600-normal.woff2) format('woff2')}
@font-face{font-family:'Archivo';font-style:normal;font-weight:600;font-display:swap;
  src:url(/assets/fontes/archivo-latin-600-normal.woff2) format('woff2')}
@font-face{font-family:'Archivo';font-style:normal;font-weight:700;font-display:swap;
  src:url(/assets/fontes/archivo-latin-700-normal.woff2) format('woff2')}
%(css)s
</style>
</head>
<body>

<a class="saltar" href="#principal">Skip to content</a>

<header class="topo">
  <div class="folha topo-i">
    %(marca)s
    <nav class="nav" aria-label="Main">
      <a href="/tours/">All tours</a>
      <a href="#destinations">Destinations</a>
      <a href="#how">How it works</a>
      <a href="/contact/">Help</a>
    </nav>
  </div>
</header>

<main id="principal">

<section class="heroi">
  <div class="heroi-foto">%(heroi_img)s</div>
  <div class="folha heroi-i">
    <h2>Someone else drives. The day is yours.</h2>
    <p>Private day tours in %(np)d countries. One vehicle for your group,
      a price for the whole group instead of per person, and a start time
      set early enough to reach the place before the coaches do.</p>

    <form class="procura" action="/tours/" method="get" role="search">
      <label class="campo">
        <span>Destination</span>
        <select name="city">
          <option value="">Anywhere</option>
          %(opcoes_cidade)s
        </select>
      </label>
      <label class="campo">
        <span>Date</span>
        <input type="date" name="date">
      </label>
      <label class="campo">
        <span>Group size</span>
        <select name="people">
          %(opcoes_grupo)s
        </select>
      </label>
      <button class="botao" type="submit">Search</button>
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

<footer class="rodape">
  <div class="folha">
    <div class="rodape-i">
      <div>
        %(marca_rodape)s
        <p class="rodape-nota">Private day tours, priced for the whole group.</p>
      </div>
      <div class="rodape-cols">
        <div class="rodape-col">
          <h3>Tours</h3>
          %(links_pais)s
        </div>
        <div class="rodape-col">
          <h3>Company</h3>
          <a href="/tours/">All tours</a>
          <a href="/contact/">Contact</a>
        </div>
      </div>
    </div>
    <div class="rodape-fim">
      <span>&copy; %(ano)s Exclusive World Tours</span>
      <span>Photographs by their authors on Unsplash</span>
    </div>
  </div>
</footer>

</body>
</html>
''' % {
        'css': css(),
        'ndesc': len(tours), 'nt': len(tours), 'np': len(paises),
        'nc': len(cidades), 'menor': euros(menor), 'ano': 2026,
        'marca': lockup(44, titulo=True),
        'marca_rodape': lockup(40),
        'heroi_img': (img(hf['id'], hf['alt'], (900, 1600, 2200),
                          '100vw', eager=True) if hf else ''),
        'opcoes_cidade': '\n'.join(
            '<option value="%s">%s</option>' % (e(c), e(c)) for c in cidades),
        'opcoes_grupo': '\n'.join(
            '<option value="%d">%d %s</option>' % (n, n,
                                                   'person' if n == 1 else 'people')
            for n in (2, 4, 6, 8, 12, 16)),
        'paises': '\n'.join(cartao_pais(p, i) for i, p in enumerate(paises)),
        'tours': '\n'.join(cartao_tour(t, i == 0)
                           for i, t in enumerate(destaques)),
        'mapa': mapa_svg(tours),
        'coords': '\n'.join('<span class="coord">%s &nbsp;%s</span>'
                            % (e(c['nome']), grau(c)) for c in tres),
        'links_pais': '\n'.join('<a href="/tours/#%s">%s</a>'
                                % (e(p['cod']), e(p['nome']))
                                for p in paises),
    }

    destino = os.path.join(RAIZ, 'index.html')
    with open(destino, 'w') as f:
        f.write(html)
    print('escrito: %s (%.0f KB)' % (destino, os.path.getsize(destino) / 1024))
    print('%d tours, %d paises, %d cidades, menor preco %s'
          % (len(tours), len(paises), len(cidades), menor))


if __name__ == '__main__':
    main()
