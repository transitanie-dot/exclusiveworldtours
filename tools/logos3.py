#!/usr/bin/env python3
"""
Terceira ronda de logotipos: a letra e a marca.

As duas primeiras rondas foram as duas a mesma coisa por baixo — um
simbolo desenhado com o nome ao lado. Uma era geometria de mais, a outra
ilustracao de mais, mas o esqueleto era o mesmo e nenhuma convenceu.

Esta ronda muda de eixo. As marcas de viagem caras que funcionam a serio
— Aman, Belmond, Black Tomato, Mr & Mrs Smith — quase nao tem simbolo: o
que se ve e o nome, composto com cuidado. O premio nao esta no desenho,
esta no espacejamento, no peso e no que se corta.

Por isso aqui nao ha icones. Ha seis logotipos, cada um com:

  - a marca composta, grande, em claro e em escuro;
  - um monograma ou marca curta para o quadrado do avatar e do favicon,
    que sai do mesmo desenho e nao de um desenho novo;
  - o cabecalho do site ao tamanho real, que e onde isto vai viver
    todos os dias.

As fontes vao dentro do ficheiro em base64. Nao dependem do Google nem
de ligacao nenhuma: a pagina abre igual no Render, no browser dele a
partir do ficheiro, e aqui nas minhas capturas. Sem isso eu estaria a
desenhar as cegas outra vez.

    python3 tools/logos3.py        # escreve logos3/index.html e logos3.html
"""

import base64
import json
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FONTES = os.path.join(RAIZ, 'assets', 'fontes')


# ----------------------------------------------------------------- fontes

# (ficheiro, familia, peso). So entram as que sao mesmo usadas.
USADAS = [
    ('archivo-latin-400-normal.woff2',             'Archivo', 400),
    ('archivo-latin-500-normal.woff2',             'Archivo', 500),
    ('archivo-latin-600-normal.woff2',             'Archivo', 600),
    ('archivo-latin-700-normal.woff2',             'Archivo', 700),
    ('inter-latin-400-normal.woff2',               'Inter', 400),
    ('inter-latin-500-normal.woff2',               'Inter', 500),
    ('inter-latin-600-normal.woff2',               'Inter', 600),
    ('fraunces-latin-400-normal.woff2',            'Fraunces', 400),
    ('fraunces-latin-600-normal.woff2',            'Fraunces', 600),
    ('instrument-serif-latin-400-normal.woff2',    'Instrument Serif', 400),
    ('bricolage-grotesque-latin-700-normal.woff2', 'Bricolage Grotesque', 700),
    ('space-grotesk-latin-500-normal.woff2',       'Space Grotesk', 500),
    ('space-grotesk-latin-700-normal.woff2',       'Space Grotesk', 700),
    ('syne-latin-700-normal.woff2',                'Syne', 700),
]


def faces():
    """As @font-face com o woff2 embebido. Falha se faltar um ficheiro —
    uma pagina de escolha de tipografia com a fonte errada nao serve para
    escolher nada, e ja me aconteceu uma vez."""
    regras = []
    for ficheiro, familia, peso in USADAS:
        caminho = os.path.join(FONTES, ficheiro)
        if not os.path.exists(caminho):
            raise SystemExit('Falta a fonte %s. Corre primeiro a copia '
                             'para assets/fontes.' % caminho)
        with open(caminho, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        regras.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:%d;"
            "font-display:block;src:url(data:font/woff2;base64,%s) "
            "format('woff2')}" % (familia, peso, b64))
    return '\n'.join(regras)


# ------------------------------------------------------------- coordenada

def coordenada_dublin():
    """A coordenada que entra na proposta R sai do atlas, que sai do
    GeoNames. Nao se escreve a mao um numero que o site ja sabe."""
    caminho = os.path.join(RAIZ, 'assets', 'atlas.json')
    d = json.load(open(caminho))['cidades']['Dublin']
    lat, lon = d['lat'], d['lon']
    return '%.4f&deg; %s &nbsp;%.4f&deg; %s' % (
        abs(lat), 'N' if lat >= 0 else 'S',
        abs(lon), 'E' if lon >= 0 else 'W')


# ----------------------------------------------------------- as propostas
#
# Cada marca e HTML, nao imagem: assim ve-se a tipografia verdadeira, com
# o espacejamento verdadeiro, e eu posso afinar decimas de em sem
# redesenhar nada. A `escala` e o unico numero que muda entre o tamanho
# grande, o cabecalho e o quadrado — tudo o resto e proporcional.

def _m(classe, dentro, t, k):
    """A raiz de uma marca. `t` e o tamanho em px e `k` o fator de
    encolhimento (ver o CSS). Quem desenha a marca nunca precisa de saber
    mais nada: tudo o resto esta em em, por dentro."""
    return ('<span class="marca %s" style="--t:%gpx;--k:%g">%s</span>'
            % (classe, t, k, dentro))


def M(t, k):
    return _m('m-M', '<span class="m-M-regua"></span>'
                     '<span class="m-M-nome">Exclusive World Tours</span>'
                     '<span class="m-M-regua"></span>', t, k)


def M_curta(t, k):
    return _m('m-M-curta', 'EWT', t, k)


def N(t, k):
    return _m('m-N', '<span class="m-N-um">Exclusive</span>'
                     '<span class="m-N-dois">World Tours</span>', t, k)


def N_curta(t, k):
    return _m('m-N-curta', 'E', t, k)


def O(t, k):
    return _m('m-O', '<span class="m-O-um">exclusive</span>'
                     '<span class="m-O-dois">world tours</span>', t, k)


def O_curta(t, k):
    return _m('m-O-curta', 'e', t, k)


def P(t, k):
    return _m('m-P', '<span class="m-P-l1">Exclusive</span>'
                     '<span class="m-P-l2">World</span>'
                     '<span class="m-P-l3">Tours</span>', t, k)


def P_curta(t, k):
    return _m('m-P-curta', 'EWT', t, k)


# A proposta Q e a unica desenhada: um monograma onde o W serve de
# montanha e de onda ao mesmo tempo. Vai em SVG porque nenhuma fonte faz
# isto — e feito a mao, traco a traco.
Q_SVG = '''
<svg viewBox="0 0 170 68" class="q-svg" role="img"
     aria-label="Monograma E W T da Exclusive World Tours">
  <g fill="none" stroke="currentColor" stroke-width="8"
     stroke-linecap="square" stroke-linejoin="miter">
    <!-- E -->
    <path d="M30 10 H8 V58 H30"/>
    <path d="M8 34 H26"/>
    <!-- W: vales fundos e pico alto, para ler como serra e nao como uma
         letra sem intencao. A linha de agua fica so na marca curta: aqui,
         entre o E e o T, cortava as tres letras e lia-se como um risco
         por cima do nome. -->
    <path d="M48 10 L68 58 L85 20 L102 58 L122 10"/>
    <!-- T -->
    <path d="M132 12 H166 M149 12 V58"/>
  </g>
</svg>'''

Q_SVG_CURTO = '''
<svg viewBox="0 0 84 68" class="q-svg" role="img"
     aria-label="Marca curta da Exclusive World Tours">
  <g fill="none" stroke="currentColor" stroke-width="10"
     stroke-linecap="square" stroke-linejoin="miter">
    <path d="M10 10 L30 58 L42 35 L54 58 L74 10"/>
    <path d="M17 46 H67" stroke-width="7" opacity=".55"/>
  </g>
</svg>'''


def Q(t, k):
    return _m('m-Q', Q_SVG, t, k)


def Q_curta(t, k):
    return _m('m-Q', Q_SVG_CURTO, t, k)


def R(t, k):
    return _m('m-R', '<span class="m-R-coord">%s</span>'
                     '<span class="m-R-nome">Exclusive World Tours</span>'
                     % coordenada_dublin(), t, k)


def R_curta(t, k):
    return _m('m-R-curta', '<span class="m-R-curta-ponto"></span>'
                           '<span class="m-R-curta-letras">EWT</span>', t, k)


PROPOSTAS = [
    {
        'letra': 'M', 'nome': 'A linha estendida', 'largo': True,
        'marca': M, 'curta': M_curta,
        'tamanhos': (30, 9, 15.6), 'k': 0.0492,
        'ideia': 'O nome inteiro numa so linha, em maiusculas largas entre '
                 'dois filetes. Nao ha nada para interpretar: ve-se o nome '
                 'e ve-se que foi composto por alguem. E o movimento mais '
                 'antigo do luxo e continua a funcionar porque o espaco '
                 'custa dinheiro — uma marca que se da ao luxo de ocupar '
                 'uma linha inteira esta a dizer alguma coisa.',
        'contra': 'Vinte e um caracteres com este espacejamento nao cabem '
                  'num cabecalho de telemovel. Obriga a uma versao '
                  'empilhada a serio, nao a um encolhimento.',
    },
    {
        'letra': 'N', 'nome': 'A masthead',
        'marca': N, 'curta': N_curta,
        'tamanhos': (62, 18.6, 34.7), 'k': 0.2348,
        'ideia': '"Exclusive" grande numa serifa de revista, "World Tours" '
                 'pequeno em maiusculas por baixo. E a linguagem das '
                 'revistas de viagem e dos hoteis que cobram caro, e diz '
                 'editorial antes de dizer loja — que e exatamente a '
                 'distancia que separa isto da Viator.',
        'contra': 'Serifa grande com sans pequena por baixo e a combinacao '
                  'editorial que toda a gente faz. Fica bem a primeira e '
                  'nao se distingue a decima.',
    },
    {
        'letra': 'O', 'nome': 'O grotesco apertado',
        'marca': O, 'curta': O_curta,
        'tamanhos': (56, 15.7, 31.4), 'k': 0.1489,
        'ideia': 'Minusculas pesadas e apertadas, com "world tours" ao lado '
                 'na linha de base. Isto nao se le como agencia, le-se como '
                 'produto — tecnologico e direto, que e o que pediste. E a '
                 'unica da lista que podia estar num separador do browser '
                 'ao lado da Booking sem parecer mais pequena.',
        'contra': 'Minusculas pesadas sao a assinatura das startups. Com a '
                  'cor errada passa de moderno a barato num segundo.',
    },
    {
        'letra': 'P', 'nome': 'O bloco',
        'marca': P, 'curta': P_curta,
        'tamanhos': (46, 12, 17.6), 'k': 0.2347,
        'ideia': 'Tres linhas alinhadas a esquerda e encostadas umas as '
                 'outras, com as tres a acabar na mesma vertical. O bloco '
                 'e que e a marca. Nao ha nada desenhado para partir ao '
                 'pequeno e cabe num canto sem pedir licenca.',
        'contra': 'Tres linhas comem altura, e um cabecalho tem pouca. '
                  'Obriga a uma versao de uma linha so para o topo.',
    },
    {
        'letra': 'Q', 'nome': 'O monograma',
        'marca': Q, 'curta': Q_curta,
        'tamanhos': (60, 15.6, 36), 'k': 0.4,
        'ideia': 'E, W e T desenhados a mao com uma so espessura de traco. '
                 'O W tem os vales fundos e o pico alto, e na marca curta, '
                 'onde fica sozinho, leva uma linha de agua a cortar os '
                 'vales: por cima leem-se picos, por baixo le-se mar. No '
                 'conjunto das tres letras essa linha sai, porque ali '
                 'atravessava o E e o T e lia-se como um risco por cima do '
                 'nome. E a unica proposta que e letra e paisagem no mesmo '
                 'desenho, e o meio sozinho ja e a marca curta sem se '
                 'desenhar nada de novo.',
        'contra': 'Monogramas vivem de reconhecimento, e esta marca ainda '
                  'nao tem nenhum. Ate la o cliente ve tres letras que nao '
                  'lhe dizem nada — e o nome por extenso tem de andar '
                  'sempre ao lado.',
    },
    {
        'letra': 'R', 'nome': 'A coordenada', 'largo': True,
        'marca': R, 'curta': R_curta,
        'tamanhos': (29, 8.7, 15.1), 'k': 0.0579,
        'ideia': 'O nome com a coordenada real por cima, em numeros de '
                 'largura fixa. A de cima e a de Dublin, tirada do mesmo '
                 'ficheiro que o mapa do site usa — nao e um numero '
                 'escrito a mao. E o elemento de assinatura que ja '
                 'decidiste transformado na propria marca, e nenhum '
                 'concorrente tem nada parecido.',
        'contra': 'E um sistema, nao uma marca fixa: a coordenada muda de '
                  'pagina para pagina e isso exige disciplina. E ha sitios '
                  '— a fatura, o autocolante — onde nenhuma coordenada faz '
                  'sentido e so fica o nome.',
    },
]


# ------------------------------------------------------------------- css

CSS = '''
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:#fff;color:#14161A;
  font-family:'Inter',system-ui,sans-serif;font-size:16px;line-height:1.6;
  -webkit-font-smoothing:antialiased}
.folha{max-width:1040px;margin:0 auto;padding:64px 24px 96px}
h1{font-family:'Archivo',sans-serif;font-weight:700;letter-spacing:-.025em;
  font-size:clamp(2rem, 1.2rem + 2.6vw, 3.1rem);line-height:1.08;margin:0 0 20px}
.intro{max-width:62ch;color:#3C4149;margin:0 0 14px}
.intro strong{color:#14161A;font-weight:600}
.risco{height:1px;background:#E4E6EA;margin:56px 0;border:0}

.cabeca{display:flex;align-items:center;gap:14px;margin:0 0 28px}
.selo{width:34px;height:34px;flex:none;border:1.5px solid #14161A;
  border-radius:50%;display:grid;place-items:center;
  font-family:'Archivo',sans-serif;font-weight:600;font-size:13px}
.cabeca h2{font-family:'Archivo',sans-serif;font-weight:700;font-size:1.3rem;
  letter-spacing:-.02em;margin:0}

.par{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));
  gap:16px}
/* As marcas de uma linha longa nao cabem a meia largura sem partir, e uma
   proposta que se chama "a linha estendida" partida em duas nao e a
   proposta. Estas levam a largura toda, claro em cima e escuro em baixo. */
.par.largo{grid-template-columns:1fr}
.palco{border-radius:14px;padding:52px 28px;display:grid;place-items:center;
  min-height:190px}
.palco.claro{background:#F4F5F7;color:#14161A}
.palco.escuro{background:#14161A;color:#fff}

.rotulo{font-size:12px;color:#6B7280;letter-spacing:.04em;margin:30px 0 8px}
.caixa{border:1px solid #E4E6EA;border-radius:12px;padding:18px 20px}

.barra{display:flex;align-items:center;justify-content:space-between;gap:20px;
  flex-wrap:wrap}
.menu{display:flex;gap:22px;font-size:14px;color:#3C4149;font-weight:500}

.quadrados{display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.quad{background:#F4F5F7;border-radius:9px;display:grid;place-items:center;
  color:#14161A}
.quad.g{width:52px;height:52px}
.quad.p{width:26px;height:26px;border-radius:6px}
.favicon{display:inline-flex;align-items:center;gap:8px;border:1px solid #E4E6EA;
  border-radius:8px;padding:6px 12px 6px 7px;font-size:13px;color:#3C4149}
.favicon .quad{width:20px;height:20px;border-radius:5px;background:transparent}

.nota{max-width:62ch;margin:26px 0 0;color:#3C4149}
.nota b{color:#14161A;font-weight:600}
.nota + .nota{margin-top:10px}

.fim{color:#3C4149;max-width:62ch}

/* ------------------------------------------------------------ as marcas
   A raiz de cada marca leva --t (o tamanho) e tudo la dentro esta em em.
   Muda-se um numero e a marca inteira escala, espacejamento incluido.

   No palco grande o tamanho e min(tamanho cheio, o que o palco deixa).
   O segundo termo usa cqw — a largura do proprio palco — e nao vw: os
   palcos sao dois a dois, por isso a largura do ecra nao diz nada sobre
   o espaco que cada um tem, e a 768 px a marca O ainda rebentava com a
   conta feita em vw. Com cqw a conta e sobre o sitio onde a marca esta
   mesmo, a qualquer largura.

   --k e o tamanho cheio a dividir pela largura natural da marca, medido
   no browser por tools/medir-logos3.mjs — nao e um palpite. O 0.97 e a
   folga para a marca nao encostar a parede. */
.marca{font-size:var(--t);line-height:1;display:inline-flex}
.palco{container-type:inline-size}
.palco .marca{font-size:min(var(--t), calc(97cqw * var(--k)))}

/* -------------------------------------------------- M. a linha estendida */
.m-M{flex-direction:column;align-items:stretch;gap:.43em}
.m-M-regua{height:1px;background:currentColor;opacity:.42}
.m-M-nome{font-family:'Archivo',sans-serif;font-weight:500;white-space:nowrap;
  letter-spacing:.34em;text-transform:uppercase;line-height:1;
  /* o espacejamento poe espaco a direita da ultima letra tambem; sem isto
     o bloco fica torto e o filete sobra de um lado so */
  text-indent:.34em;margin-right:-.34em;text-align:center}
.m-M-curta{font-family:'Archivo',sans-serif;font-weight:500;
  letter-spacing:.167em;text-indent:.167em;margin-right:-.167em;line-height:1}

/* ------------------------------------------------------- N. a masthead */
.m-N{flex-direction:column;align-items:flex-start;gap:.145em}
.m-N-um{font-family:'Fraunces','Instrument Serif',serif;font-weight:400;
  line-height:.92;letter-spacing:-.018em}
.m-N-dois{font-family:'Archivo',sans-serif;font-weight:600;font-size:.242em;
  letter-spacing:.36em;text-indent:.36em;margin-right:-.36em;
  text-transform:uppercase;line-height:1;opacity:.82;white-space:nowrap}
.m-N-curta{font-family:'Fraunces',serif;font-weight:400;line-height:1}

/* ----------------------------------------------- O. o grotesco apertado */
.m-O{align-items:baseline;gap:.214em}
.m-O-um{font-family:'Bricolage Grotesque','Archivo',sans-serif;font-weight:700;
  letter-spacing:-.045em;line-height:1}
.m-O-dois{font-family:'Inter',sans-serif;font-weight:600;font-size:.25em;
  letter-spacing:.186em;text-indent:.186em;margin-right:-.186em;
  text-transform:uppercase;line-height:1;opacity:.72;white-space:nowrap}
.m-O-curta{font-family:'Bricolage Grotesque',sans-serif;font-weight:700;
  line-height:1;letter-spacing:-.04em}

/* ------------------------------------------------------------ P. o bloco */
/* As tres linhas acabam na mesma vertical. Os numeros nao sao de olho:
   medi a Archivo 600 em maiusculas a 100 px — EXCLUSIVE 561.5, WORLD
   373.6, TOURS 348.4 — e resolvi tamanho x largura/100 + (n-1) x ls para
   a mesma largura final nas tres. */
.m-P{flex-direction:column;align-items:flex-start;line-height:.94;
  font-family:'Archivo',sans-serif;font-weight:600;text-transform:uppercase}
.m-P-l1{font-size:.713em;letter-spacing:.0457em;margin-right:-.0457em}
.m-P-l2{font-size:1em;letter-spacing:.1304em;margin-right:-.1304em}
.m-P-l3{font-size:1em;letter-spacing:.1935em;margin-right:-.1935em}
/* A marca curta de P nao pode ser o bloco encolhido: tres linhas a 16 px
   sao tres borroes. E as mesmas letras, mesma fonte e mesmo peso, mas
   numa linha — que e o que se le ao pequeno. */
.m-P-curta{font-family:'Archivo',sans-serif;font-weight:600;line-height:1;
  letter-spacing:.0714em;text-indent:.0714em;
  margin-right:-.0714em;white-space:nowrap}

/* -------------------------------------------------------- Q. o monograma */
.m-Q .q-svg{height:1em;width:auto;display:block}

/* ------------------------------------------------------- R. a coordenada */
.m-R{flex-direction:column;align-items:center;gap:.379em}
.m-R-coord{font-family:'Space Grotesk','Inter',monospace;font-weight:500;
  font-variant-numeric:tabular-nums;font-size:.448em;letter-spacing:.123em;
  opacity:.72;white-space:nowrap}
.m-R-nome{font-family:'Archivo',sans-serif;font-weight:600;white-space:nowrap;
  letter-spacing:.193em;text-indent:.193em;margin-right:-.193em;
  text-transform:uppercase;line-height:1}
.m-R-curta{flex-direction:column;align-items:center;gap:.241em}
.m-R-curta-ponto{width:.31em;height:.31em;border-radius:50%;
  background:currentColor}
.m-R-curta-letras{font-family:'Archivo',sans-serif;font-weight:600;
  font-size:.897em;letter-spacing:.115em;text-indent:.115em;
  margin-right:-.115em;line-height:1}

@media (max-width:620px){
  .folha{padding:40px 16px 72px}
  .palco{padding:36px 16px;min-height:150px}
}
'''


# ----------------------------------------------------------------- blocos

def bloco(p):
    grande, cabecalho, quadrado = p['tamanhos']
    k = p['k']
    marca, curta = p['marca'], p['curta']
    return '''
<section>
  <div class="cabeca"><span class="selo">%(letra)s</span><h2>%(nome)s</h2></div>

  <div class="par %(largo)s">
    <div class="palco claro">%(grande)s</div>
    <div class="palco escuro">%(grande)s</div>
  </div>

  <p class="rotulo">No cabecalho do site, ao tamanho real</p>
  <div class="caixa barra">
    %(cabecalho)s
    <nav class="menu"><span>All tours</span><span>Operators</span><span>Help</span></nav>
  </div>

  <p class="rotulo">Marca curta: avatar, favicon e aplicacao</p>
  <div class="caixa quadrados">
    <span class="quad g">%(q_g)s</span>
    <span class="quad p">%(q_p)s</span>
    <span class="favicon"><span class="quad">%(q_f)s</span>Exclusive World Tours</span>
  </div>

  <p class="nota"><b>A ideia.</b> %(ideia)s</p>
  <p class="nota"><b>Contra.</b> %(contra)s</p>
</section>
<hr class="risco">''' % {
        'letra': p['letra'], 'nome': p['nome'],
        'largo': 'largo' if p.get('largo') else '',
        'grande': marca(grande, k),
        'cabecalho': marca(cabecalho, k),
        'q_g': curta(quadrado, k),
        'q_p': curta(quadrado * 0.46, k),
        'q_f': curta(quadrado * 0.36, k),
        'ideia': p['ideia'], 'contra': p['contra'],
    }


def main():
    html = '''<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exclusive World Tours — terceira ronda: a letra e a marca</title>
<style>
%(faces)s
%(css)s
</style>
</head>
<body>
<main class="folha">

<h1>Terceira ronda: a letra e a marca</h1>
<p class="intro">As duas primeiras rondas eram a mesma coisa por baixo — um
simbolo desenhado com o nome ao lado. Uma tinha geometria de mais, a outra
ilustracao de mais, e o esqueleto era o mesmo nas duas.</p>
<p class="intro">Esta muda de eixo. As marcas de viagem caras que funcionam
mesmo — <strong>Aman, Belmond, Black Tomato</strong> — quase nao tem simbolo:
o que se ve e o nome, composto com cuidado. O caro nao esta no desenho, esta
no espacejamento, no peso e no que se decide cortar.</p>
<p class="intro">Por isso aqui nao ha icones. Ha <strong>seis logotipos</strong>,
cada um com a marca composta em claro e em escuro, uma marca curta para o
quadrado do avatar e do favicon tirada do mesmo desenho, e o cabecalho do site
ao tamanho real — que e onde isto vai viver todos os dias.</p>

<hr class="risco">

%(blocos)s

<p class="fim">Continuam todos a uma so cor. A paleta sai da marca depois de
escolhida, e nao ao contrario.<br>
Diz-me uma ou duas e afino a mao — espacejamento optico letra a letra, versao
empilhada para telemovel, area de respiro — e entrego em SVG, PNG e favicon.</p>

</main>
</body>
</html>
''' % {'faces': faces(), 'css': CSS,
       'blocos': '\n'.join(bloco(p) for p in PROPOSTAS)}

    # Escreve-se nos dois sitios de proposito. O Render nem sempre serve
    # uma pasta a partir do index.html quando o endereco leva barra no
    # fim — ja apanhei um 404 em /logos/ com o /logos/index.html a
    # funcionar. Um ficheiro na raiz nao depende disso e abre sempre.
    for destino in (os.path.join(RAIZ, 'logos3', 'index.html'),
                    os.path.join(RAIZ, 'logos3.html')):
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, 'w') as f:
            f.write(html)
        print('escrito: %s (%d KB)' % (destino, os.path.getsize(destino) / 1024))
    print('%d propostas, %d fontes embebidas' % (len(PROPOSTAS), len(USADAS)))


if __name__ == '__main__':
    main()
