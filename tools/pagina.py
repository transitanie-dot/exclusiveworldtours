#!/usr/bin/env python3
"""
O que todas as paginas do site partilham.

Saiu do home.py quando apareceu a segunda pagina. A razao e simples: dois
ficheiros com o seu proprio CSS comecam iguais e acabam diferentes, e a
diferenca descobre-se sempre tarde, numa pagina que ninguem estava a
olhar. As cores, o cabecalho, o rodape, o cartao de um tour e os
carregadores de dados vivem aqui, num sitio so.

Cada pagina traz o seu proprio CSS por cima deste, so para o que e dela.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from marca import CSS as CSS_MARCA, lockup  # noqa: E402
from marca_base import PALETA, contraste, misturar  # noqa: E402
import procura  # noqa: E402

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



def cartao_tour(t, destaque=False):
    """O cartao de um tour.

    Leva o preco do grupo e, ao lado, o preco por pessoa no escalao mais
    cheio — que e a conta que o cliente faz de cabeca quando compara com
    um concorrente que vende por lugar. E uma divisao, nao uma promessa:
    sai dos mesmos numeros que ja estao na tabela.
    """
    foto = t['_foto']
    media = (img(foto['id'], foto['alt'], (420, 760),
                 '(min-width:1100px) 25vw, (min-width:700px) 50vw, 100vw',
                 eager=destaque)
             if foto else '')
    credito = ('<span class="credito">%s</span>' % e(foto['by'])) if foto else ''
    tier = t['_menor']
    cheio = max(t['durations'][0]['tiers'], key=lambda x: x['max'])
    por_pessoa = cheio['price'] / cheio['max']
    return '''<a class="tour" href="/tours/%(slug)s/">
  <span class="tour-foto">%(media)s%(credito)s
    <span class="tour-sel">%(h)s</span></span>
  <span class="tour-corpo">
    <span class="tour-onde">%(cidade)s <span class="pt">&middot;</span> %(pais)s</span>
    <span class="tour-nome">%(titulo)s</span>
    <span class="tour-linha">
      <span class="etiq">up to %(max)d</span>
      %(partida)s
      %(paragens)s
    </span>
    <span class="tour-preco">
      <b class="num">&euro;%(preco)s</b>
      <span class="tour-preco-nota">group total<br>
        <span class="num">&euro;%(pp)s</span> pp at %(cheiomax)d</span>
    </span>
  </span>
</a>''' % {
        'slug': e(t['slug']), 'media': media, 'credito': credito,
        'cidade': e(t['city']), 'pais': e(t['countryName']),
        'titulo': e(t['title'].replace('Private Tour: ', '')),
        'h': e(t['_h']), 'max': t['_max'],
        'partida': ('<span class="etiq">dep. %s</span>' % e(t['_partida'])
                    if t['_partida'] else ''),
        'paragens': ('<span class="etiq">%d stops</span>' % len(t['stops'])
                     if t.get('stops') else ''),
        'preco': euros(tier['price']),
        'pp': euros(round(por_pessoa)), 'cheiomax': cheio['max'],
    }


def css_base():
    """O CSS de qualquer pagina. O que e so de uma pagina fica nela."""
    return ('''

:root{
  --tinta:%(tinta)s; --cor:%(cor)s; --cor-escura:%(cor_escura)s;
  --papel:%(papel)s; --branco:%(branco)s;
  --tinta-f:%(tinta_f)s; --cor-f:%(cor_f)s; --uma-f:%(uma_f)s;
  --texto:%(texto)s; --mudo:%(mudo)s; --risco:%(risco)s;
  --tipo:'Inter',system-ui,-apple-system,sans-serif;
  --tipo-titulo:'Archivo','Inter',system-ui,sans-serif;
  --mono:ui-monospace,'SFMono-Regular','Menlo','Consolas',monospace;
  --raio:10px;
  /* a escala de intervalos: tudo no site sai daqui */
  --e1:6px; --e2:12px; --e3:20px; --e4:32px; --e5:52px;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%%;scroll-behavior:smooth}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}
  *,*::before,*::after{animation-duration:.01ms !important;
    transition-duration:.01ms !important}}
body{margin:0;background:var(--papel);color:var(--texto);
  font-family:var(--tipo);font-size:15.5px;line-height:1.55;
  -webkit-font-smoothing:antialiased}
img{max-width:100%%;display:block}
a{color:inherit}
h1,h2,h3{font-family:var(--tipo-titulo);color:var(--tinta);
  letter-spacing:-.025em;line-height:1.08;margin:0}
.folha{max-width:1320px;margin:0 auto;padding:0 clamp(16px,2.4vw,32px)}
/* o botao e o foco visivel sao de todas as paginas. Estiveram no CSS da
   homepage e a pagina de resultados ficou com um botao cinzento do
   browser — duas paginas, dois CSS, e a diferenca so se ve a olho. */
.botao{display:inline-flex;align-items:center;justify-content:center;
  background:var(--tinta);color:var(--branco);border:0;border-radius:10px;
  padding:0 26px;min-height:54px;font:inherit;font-weight:600;font-size:16px;
  cursor:pointer;text-decoration:none;white-space:nowrap}
.botao:hover{background:var(--cor-escura)}
a:focus-visible,button:focus-visible,input:focus-visible,
select:focus-visible{outline:3px solid var(--cor);outline-offset:3px;
  border-radius:4px}
/* So aparece a quem navega por teclado — mas aparece mesmo, que e o
   ponto. Escondido com left:-9999px e sem regra de foco, este atalho
   existe no HTML e nao serve a ninguem. */
.saltar{position:absolute;left:16px;top:-60px;z-index:60;background:var(--tinta);
  color:var(--branco);padding:12px 18px;border-radius:0 0 10px 10px;
  text-decoration:none;font-weight:600;transition:top .15s ease}
.saltar:focus{top:0}

/* ------------------------------------------------------------ cabecalho */
.topo{position:sticky;top:0;z-index:40;background:rgba(246,244,241,.94);
  backdrop-filter:saturate(180%%) blur(12px);
  border-bottom:1px solid var(--risco)}
.topo-i{display:flex;align-items:center;gap:28px;height:62px}
.nav{display:flex;gap:26px;margin-left:auto;font-size:15px;font-weight:500}
.nav a{text-decoration:none;color:var(--texto);padding:6px 0;
  border-bottom:2px solid transparent}
.nav a:hover{color:var(--tinta);border-bottom-color:var(--cor)}
.topo .marca{color:var(--tinta)}
@media (max-width:760px){.nav{display:none}}
/* ---------------------------------------------------------- as bandas
   O site deixa de ser uma folha branca com coisas em cima. Alterna
   bandas de cor a toda a largura, e e isso que da ritmo a pagina quando
   se percorre. */
.banda{background:var(--papel)}
.banda-b{background:var(--branco);border-top:1px solid var(--risco);
  border-bottom:1px solid var(--risco)}
.banda-e{background:var(--tinta);color:rgba(255,255,255,.86)}
.banda-e h1,.banda-e h2,.banda-e h3{color:var(--branco)}
.banda-e .rot{color:rgba(255,255,255,.6)}
.banda-e .rot b{color:var(--cor)}
.banda-e .rot::after{background:rgba(255,255,255,.18)}

/* ------------------------------------------------------- o detalhe fino
   O Ricardo pediu mais detalhe decorativo. Nao e enfeite solto: e um
   sistema pequeno que se repete em todas as paginas e faz o site parecer
   um instrumento em vez de uma brochura — rotulos numerados, filetes,
   cantos marcados, numeros de largura fixa. */

/* o rotulo numerado de uma seccao: "01 / THE DAY" */
.rot{display:flex;align-items:center;gap:10px;margin:0 0 var(--e2);
  font-size:11px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--mudo);font-weight:600}
.rot b{font-family:var(--mono);font-weight:600;color:var(--cor-escura);
  font-size:11px;letter-spacing:.06em}
.rot::after{content:'';flex:1;height:1px;background:var(--risco)}

/* numeros sempre de largura fixa: precos, horas, coordenadas */
.num,.preco,time,[data-num]{font-variant-numeric:tabular-nums}

/* a moldura com os cantos marcados, para blocos que tem de pesar */
.moldura{position:relative;border:1px solid var(--risco);
  border-radius:var(--raio);background:var(--branco)}
.moldura::before,.moldura::after{content:'';position:absolute;width:9px;
  height:9px;border:2px solid var(--cor);pointer-events:none}
.moldura::before{top:-1px;left:-1px;border-right:0;border-bottom:0;
  border-radius:var(--raio) 0 0 0}
.moldura::after{bottom:-1px;right:-1px;border-left:0;border-top:0;
  border-radius:0 0 var(--raio) 0}

/* um codigo: IATA, coordenada, referencia */
.cod{font-family:var(--mono);font-size:11.5px;letter-spacing:.04em;
  color:var(--mudo);background:var(--papel);border:1px solid var(--risco);
  border-radius:4px;padding:2px 6px}

/* a revelacao ao percorrer. Quem pediu para nao haver movimento nao tem
   movimento nenhum — e a regra esta primeiro, para nunca ser esquecida. */
@media (prefers-reduced-motion:no-preference){
  [data-rev]{opacity:0;transform:translateY(14px);
    transition:opacity .5s cubic-bezier(.2,.6,.2,1),
               transform .5s cubic-bezier(.2,.6,.2,1)}
  [data-rev].vis{opacity:1;transform:none}
}

/* os cartoes de tour: o cartao e desenhado em pagina.cartao_tour(), por
   isso o CSS dele tem de estar aqui tambem. Esteve so na homepage e na
   pagina de resultados os cartoes sairam como texto corrido. */
/* tours */
/* mais cartoes por ecra: a 1440 cabem quatro, nao tres */
.tours{display:grid;gap:14px;
  grid-template-columns:repeat(auto-fill,minmax(min(100%%,268px),1fr))}
.tour{display:flex;flex-direction:column;text-decoration:none;
  border:1px solid var(--risco);border-radius:var(--raio);overflow:hidden;
  background:var(--branco);transition:border-color .18s, transform .18s}
.tour:hover{border-color:var(--tinta-f);transform:translateY(-2px)}
.tour-foto{position:relative;aspect-ratio:16/10;background:var(--uma-f);
  display:block;overflow:hidden}
.tour-foto img{width:100%%;height:100%%;object-fit:cover;
  transition:transform .5s ease}
.tour:hover .tour-foto img{transform:scale(1.045)}
.credito{position:absolute;right:7px;bottom:6px;z-index:2;font-size:10px;
  color:#fff;background:rgba(11,43,42,.62);padding:2px 6px;border-radius:4px}
/* a duracao em cima da fotografia: le-se antes do titulo, que e a ordem
   por que as pessoas decidem */
.tour-sel{position:absolute;left:7px;top:7px;z-index:2;font-family:var(--mono);
  font-size:11px;letter-spacing:.03em;color:var(--tinta);background:var(--branco);
  padding:3px 8px;border-radius:4px;font-variant-numeric:tabular-nums}
.tour-corpo{display:flex;flex-direction:column;gap:7px;padding:14px 15px 15px;
  flex:1}
.tour-onde{font-size:11.5px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--cor-escura);font-weight:600}
.tour-onde .pt{color:var(--risco)}
.tour-nome{font-family:var(--tipo-titulo);font-weight:600;font-size:1.02rem;
  color:var(--tinta);line-height:1.2}
.tour-linha{display:flex;flex-wrap:wrap;gap:5px;margin-top:1px}
.etiq{font-size:11.5px;color:var(--texto);background:var(--papel);
  border:1px solid var(--risco);border-radius:4px;padding:2px 7px}
.tour-preco{margin-top:auto;padding-top:11px;border-top:1px solid var(--risco);
  display:flex;align-items:flex-end;gap:9px;justify-content:space-between}
.tour-preco b{font-family:var(--tipo-titulo);font-size:1.22rem;
  color:var(--tinta);line-height:1}
.tour-preco-nota{font-size:11.5px;color:var(--mudo);text-align:right;
  line-height:1.35}

/* rodape */
.rodape{background:var(--papel);border-top:1px solid var(--risco);
  padding:var(--e5) 0 var(--e4);margin-top:0}
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
''' % CORES) + CSS_MARCA + (procura.CSS % CORES)


# ---------------------------------------------------------- o invólucro

FONTES = """<link rel="preload" as="font" type="font/woff2" crossorigin href="/assets/fontes/archivo-latin-600-normal.woff2">
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
  src:url(/assets/fontes/archivo-latin-700-normal.woff2) format('woff2')}"""


def cabecalho(marca_titulo=False):
    """O topo. A marca so e <h1> na homepage; nas outras paginas o <h1> e
    o titulo da propria pagina, senao todas as paginas do site teriam o
    mesmo cabecalho de primeiro nivel e nenhuma diria do que trata."""
    return '''<header class="topo">
  <div class="folha topo-i">
    %s
    <nav class="nav" aria-label="Main">
      <a href="/tours/">All tours</a>
      <a href="/#destinations">Destinations</a>
      <a href="/#how">How it works</a>
      <a href="/contact/">Help</a>
    </nav>
  </div>
</header>''' % lockup(44, titulo=marca_titulo)


def rodape(paises):
    return '''<footer class="rodape">
  <div class="folha">
    <div class="rodape-i">
      <div>
        %(marca)s
        <p class="rodape-nota">Private day tours, priced for the whole group.</p>
      </div>
      <div class="rodape-cols">
        <div class="rodape-col">
          <h3>Tours</h3>
          %(links)s
        </div>
        <div class="rodape-col">
          <h3>Company</h3>
          <a href="/tours/">All tours</a>
          <a href="/contact/">Contact</a>
        </div>
      </div>
    </div>
    <div class="rodape-fim">
      <span>&copy; 2026 Exclusive World Tours</span>
      <span>Photographs by their authors on Unsplash</span>
    </div>
  </div>
</footer>''' % {
        'marca': lockup(40),
        'links': '\n'.join('<a href="/tours/?country=%s">%s</a>'
                           % (e(p['cod']), e(p['nome'])) for p in paises),
    }


def envolver(titulo, descricao, css_pagina, corpo, js='', noindex=True):
    """A pagina inteira. O noindex fica ligado ate o Ricardo confirmar os
    precos: uma pagina de precos indexada com numeros por confirmar e
    dificil de desfazer."""
    return '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(titulo)s</title>
<meta name="description" content="%(descricao)s">
%(robots)s
%(fontes)s
%(css)s
%(css_pagina)s
</style>
</head>
<body>
<a class="saltar" href="#principal">Skip to content</a>
%(corpo)s
%(js)s
</body>
</html>
''' % {
        'titulo': e(titulo), 'descricao': e(descricao),
        'robots': '<meta name="robots" content="noindex, nofollow">' if noindex else '',
        'fontes': FONTES, 'css': css_base(), 'css_pagina': css_pagina,
        'corpo': corpo,
        'js': '<script>%s</script>' % (js + REVELAR),
    }


REVELAR = """
(function () {
  // A revelacao ao percorrer. Quem tem 'reduzir movimento' ligado no
  // sistema nao ve nada disto: o conteudo aparece logo, inteiro.
  var q = window.matchMedia('(prefers-reduced-motion: reduce)');
  var alvos = [].slice.call(document.querySelectorAll('[data-rev]'));
  if (!alvos.length) return;
  if (q.matches || !('IntersectionObserver' in window)) {
    alvos.forEach(function (x) { x.classList.add('vis'); });
    return;
  }
  var obs = new IntersectionObserver(function (es) {
    es.forEach(function (en) {
      if (!en.isIntersecting) return;
      en.target.classList.add('vis');
      obs.unobserve(en.target);
    });
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.04 });
  alvos.forEach(function (x) { obs.observe(x); });
})();
"""


def escrever(html, caminho):
    destino = os.path.join(RAIZ, caminho)
    os.makedirs(os.path.dirname(destino), exist_ok=True) if os.path.dirname(destino) else None
    with open(destino, 'w') as f:
        f.write(html)
    print('escrito: %s (%.0f KB)' % (caminho, os.path.getsize(destino) / 1024))
