#!/usr/bin/env python3
"""
A base partilhada das paginas de marca.

A quarta ronda estabeleceu o sistema e o Ricardo aceitou-o: duas cores,
sem degrade, volume por planos sobrepostos. A partir daqui esse sistema
vive aqui, num sitio so, em vez de ser copiado de ronda para ronda. A
pagina da quarta ronda fica como foi entregue; o que vier a seguir usa
este modulo.

O que esta aqui:

  - a paleta e as tintas calculadas;
  - o CSS dos palcos, do cabecalho e da fila de tamanhos;
  - o involucro da pagina.

O que NAO esta aqui, e e de proposito: os desenhos. Cada ronda traz os
seus, porque e isso que muda.
"""

import base64
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FONTES = os.path.join(RAIZ, 'assets', 'fontes')

# O ambar nao e so uma escolha de gosto: tem de passar os 3:1 que a WCAG
# pede aos elementos graficos, nos DOIS papeis. O #E4873F que eu tinha a
# principio dava 2.44:1 sobre o creme e reprovava. Este da 3.2:1 sobre o
# creme e 5.21:1 sobre o escuro, e mantem o calor.
PALETA = {'tinta': '#0B2B2A', 'cor': '#CE7030'}

PAPEL_CLARO = '#F6F4F1'
PAPEL_ESCURO = '#0B1715'
TINTA_ESCURO = '#F3F1EE'          # sobre escuro a "tinta" e o claro

USADAS = [
    ('archivo-latin-500-normal.woff2', 'Archivo', 500),
    ('archivo-latin-600-normal.woff2', 'Archivo', 600),
    ('archivo-latin-700-normal.woff2', 'Archivo', 700),
    ('inter-latin-400-normal.woff2',   'Inter', 400),
    ('inter-latin-500-normal.woff2',   'Inter', 500),
    ('inter-latin-600-normal.woff2',   'Inter', 600),
]


def faces():
    """As @font-face com o woff2 embebido.

    Vai dentro do ficheiro de proposito: a pagina abre igual no Render,
    no browser dele a partir do ficheiro guardado, e nas minhas capturas.
    Sem isto eu estaria a julgar tipografia as cegas, que ja custou uma
    ronda inteira neste projeto."""
    regras = []
    for ficheiro, familia, peso in USADAS:
        caminho = os.path.join(FONTES, ficheiro)
        if not os.path.exists(caminho):
            raise SystemExit('Falta a fonte %s.' % caminho)
        with open(caminho, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        regras.append(
            "@font-face{font-family:'%s';font-style:normal;font-weight:%d;"
            "font-display:block;src:url(data:font/woff2;base64,%s) "
            "format('woff2')}" % (familia, peso, b64))
    return '\n'.join(regras)


def misturar(frente, fundo, parte):
    """Uma tinta: a cor a `parte` por cento sobre o papel, calculada e
    gravada como cor cheia.

    Isto nao e o mesmo que por opacidade no SVG. A opacidade mistura com
    o que estiver por tras — e o que esta por tras muda de palco para
    palco e de plano para plano, por isso a mesma percentagem dava
    castanho num sitio e verde noutro, e os planos sobrepostos somavam-se
    uns aos outros. Com a cor calculada, cada plano e opaco: tapa o que
    esta atras, que e exatamente o que faz o volume."""
    def canais(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    f, g = canais(frente), canais(fundo)
    return '#%02X%02X%02X' % tuple(
        round(f[i] * parte + g[i] * (1 - parte)) for i in range(3))


TINTAS = {
    'claro': {
        'papel': PAPEL_CLARO, 'tinta': PALETA['tinta'], 'cor': PALETA['cor'],
        'tinta_f': misturar(PALETA['tinta'], PAPEL_CLARO, .30),
        'cor_f': misturar(PALETA['cor'], PAPEL_CLARO, .52),
        'uma_f': misturar(PALETA['tinta'], PAPEL_CLARO, .26),
    },
    'escuro': {
        'papel': PAPEL_ESCURO, 'tinta': TINTA_ESCURO, 'cor': PALETA['cor'],
        'tinta_f': misturar(TINTA_ESCURO, PAPEL_ESCURO, .30),
        'cor_f': misturar(PALETA['cor'], PAPEL_ESCURO, .52),
        'uma_f': misturar(TINTA_ESCURO, PAPEL_ESCURO, .26),
    },
}


def vars_css(qual):
    t = TINTAS[qual]
    return ('--papel:%(papel)s;--tinta:%(tinta)s;--cor:%(cor)s;'
            '--tinta-f:%(tinta_f)s;--cor-f:%(cor_f)s;--uma-f:%(uma_f)s' % t)


def contraste(a, b):
    """A razao de contraste entre duas cores, para eu nao ter de acreditar
    em mim proprio quando escolho uma tinta."""
    def rel(h):
        h = h.lstrip('#')
        c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        c = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4
             for x in c]
        return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]
    l1, l2 = sorted((rel(a), rel(b)), reverse=True)
    return (l1 + .05) / (l2 + .05)


# ------------------------------------------------------------------- svg

_CONTA = [0]


def recorte_id():
    """Os ids vem de um contador e nao de um hash do conteudo: o hash de
    texto em Python muda a cada arranque, e isso dava um ficheiro
    diferente a cada geracao sem nada ter mudado. Um gerador tem de dar
    sempre o mesmo resultado para a mesma entrada, senao nao se consegue
    ver no git o que mudou de verdade."""
    _CONTA[0] += 1
    return 'rec%d' % _CONTA[0]


def svg(dentro, rotulo=''):
    return ('<svg viewBox="0 0 100 100" class="sim" role="img" '
            'aria-label="%s">%s</svg>' % (rotulo, dentro))


# ------------------------------------------------------------------- css

CSS = '''
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%%}
/* As cores claras sao as de omissao e ficam no body, nao na marca. Uma
   variavel declarada no proprio elemento ganha a que vem de um
   antepassado, por isso declara-las na .marca fazia o palco escuro nao
   ter efeito nenhum e o nome ficava escuro sobre escuro. No body sao
   herdadas por toda a gente — cabecalho e caixas incluidos — e o palco
   escuro, por estar mais perto, troca-as. */
body{%(vars_claro)s;
  margin:0;background:#fff;color:#14161A;
  font-family:'Inter',system-ui,sans-serif;font-size:16px;line-height:1.6;
  -webkit-font-smoothing:antialiased}
.folha{max-width:1040px;margin:0 auto;padding:64px 24px 96px}
h1{font-family:'Archivo',sans-serif;font-weight:700;letter-spacing:-.025em;
  font-size:clamp(2rem, 1.2rem + 2.6vw, 3.1rem);line-height:1.08;margin:0 0 20px}
.intro{max-width:62ch;color:#3C4149;margin:0 0 14px}
.intro strong{color:#14161A;font-weight:600}
.risco{height:1px;background:#E4E6EA;margin:56px 0;border:0}

.tintas{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0}
.tinta{display:inline-flex;align-items:center;gap:9px;border:1px solid #E4E6EA;
  border-radius:9px;padding:7px 13px 7px 8px;font-size:13px;color:#3C4149;
  font-variant-numeric:tabular-nums}
.amostra{width:22px;height:22px;border-radius:5px}

.cabeca{display:flex;align-items:center;gap:14px;margin:0 0 28px}
.selo{width:34px;height:34px;flex:none;border:1.5px solid #14161A;
  border-radius:50%%;display:grid;place-items:center;
  font-family:'Archivo',sans-serif;font-weight:600;font-size:13px}
.cabeca h2{font-family:'Archivo',sans-serif;font-weight:700;font-size:1.3rem;
  letter-spacing:-.02em;margin:0}

.par{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%%,300px),1fr));
  gap:16px}
.palco{border-radius:14px;padding:46px 28px;display:grid;place-items:center;
  min-height:200px;container-type:inline-size}
.palco.claro{background:%(papel_claro)s}
.palco.escuro{background:%(papel_escuro)s;%(vars_escuro)s}

.rotulo{font-size:12px;color:#6B7280;letter-spacing:.04em;margin:30px 0 8px}
.caixa{border:1px solid #E4E6EA;border-radius:12px;padding:18px 20px}
.barra{display:flex;align-items:center;justify-content:space-between;gap:20px;
  flex-wrap:wrap}
.menu{display:flex;gap:22px;font-size:14px;color:#3C4149;font-weight:500}

.fila{display:flex;align-items:flex-end;gap:26px;flex-wrap:wrap}
.item{display:flex;flex-direction:column;align-items:center;gap:9px;
  font-size:11px;color:#6B7280}
.cx{display:grid;place-items:center;border-radius:9px;
  background:%(papel_claro)s}
.cx .sim{display:block}

.nota{max-width:62ch;margin:26px 0 0;color:#3C4149}
.nota b{color:#14161A;font-weight:600}
.nota + .nota{margin-top:10px}
.fim{color:#3C4149;max-width:62ch}
/* o titulo de uma familia de propostas, quando a pagina traz mais do que
   uma linha de trabalho */
.seccao{font-family:'Archivo',sans-serif;font-weight:700;letter-spacing:-.02em;
  font-size:1.75rem;margin:0 0 10px}
.seccao + .intro{margin-bottom:40px}

/* ---------------------------------------------------------- as marcas
   A raiz leva --t e tudo por dentro esta em em: um numero escala a marca
   inteira. No palco o tamanho e min(--t, 97cqw x --k), com cqw — a
   largura do proprio palco — porque os palcos sao dois a dois e a conta
   em vw nao sabe nada sobre o espaco que cada um tem. */
.marca{font-size:var(--t);line-height:1;display:inline-flex;align-items:center;
  gap:.6em}
.palco .marca{font-size:min(var(--t), calc(97cqw * var(--k)))}
.marca .sim{width:1em;height:1em;flex:none;display:block}
.nome{display:inline-flex;flex-direction:column;align-items:flex-start;
  font-family:'Archivo',sans-serif;font-weight:600;text-transform:uppercase;
  color:var(--tinta);line-height:1;white-space:nowrap}
.nome-l1{font-size:.268em;letter-spacing:.075em;margin-right:-.075em}
.nome-l2{font-size:.268em;letter-spacing:.2165em;margin-right:-.2165em;
  margin-top:.19em}

/* ------------------------------------------------------------ os planos
   Quatro classes para toda a ronda, e nenhum gradiente em lado nenhum. */
.sim .papel{fill:var(--papel)}
.sim .p{fill:var(--tinta)}
.sim .pf{fill:var(--tinta-f)}
.sim .c{fill:var(--cor)}
.sim .cf{fill:var(--cor-f)}
/* a uma cor so: tudo tinta, e o plano de tras na tinta fraca */
.sim .u{fill:var(--tinta)}
.sim .u-f{fill:var(--uma-f)}
/* os tracos sao linhas, nao formas: levam stroke. Sem esta regra ficavam
   com fill nenhum e stroke nenhum, ou seja invisiveis — foi o que
   aconteceu a coroa de riscos do carimbo na primeira versao. */
.sim .tracos{stroke:var(--tinta);fill:none;stroke-linecap:round}
.sim .tracos-c{stroke:var(--cor);fill:none;stroke-linecap:round}

@media (max-width:620px){
  .folha{padding:40px 16px 72px}
  .palco{padding:34px 16px;min-height:160px}
}
'''


def css():
    return CSS % {
        'papel_claro': PAPEL_CLARO, 'papel_escuro': PAPEL_ESCURO,
        'vars_claro': vars_css('claro'), 'vars_escuro': vars_css('escuro'),
    }


# ----------------------------------------------------------- os blocos

NOME = ('<span class="nome">'
        '<span class="nome-l1">Exclusive</span>'
        '<span class="nome-l2">World Tours</span></span>')


def marca(simbolo, t, k):
    return ('<span class="marca" style="--t:%gpx;--k:%g">%s%s</span>'
            % (t, k, simbolo, NOME))


def so_simbolo(simbolo, t):
    return ('<span class="marca" style="--t:%gpx;--k:1">%s</span>'
            % (t, simbolo))


def bloco(p):
    """Um bloco por proposta. `p` traz letra, nome, os tres desenhos
    (cheio, uma, mini) e os dois textos."""
    return '''
<section>
  <div class="cabeca"><span class="selo">%(letra)s</span><h2>%(nome)s</h2></div>

  <div class="par">
    <div class="palco claro">%(grande)s</div>
    <div class="palco escuro">%(grande)s</div>
  </div>

  <p class="rotulo">No cabecalho do site, ao tamanho real</p>
  <div class="caixa barra">
    %(cabecalho)s
    <nav class="menu"><span>All tours</span><span>Operators</span><span>Help</span></nav>
  </div>

  <p class="rotulo">A duas cores, a uma cor so, e reduzida — e o que acontece
    a cada uma a 48, 32 e 16 px</p>
  <div class="caixa fila">
    <span class="item"><span class="cx" style="width:84px;height:84px">%(s64)s</span>duas cores</span>
    <span class="item"><span class="cx" style="width:84px;height:84px">%(u64)s</span>uma cor</span>
    <span class="item"><span class="cx" style="width:68px;height:68px">%(m48)s</span>48 px</span>
    <span class="item"><span class="cx" style="width:48px;height:48px">%(m32)s</span>32 px</span>
    <span class="item"><span class="cx" style="width:30px;height:30px">%(m16)s</span>16 px</span>
  </div>

  <p class="nota"><b>A ideia.</b> %(ideia)s</p>
  <p class="nota"><b>Contra.</b> %(contra)s</p>
</section>
<hr class="risco">''' % {
        'letra': p['letra'], 'nome': p['nome'],
        'grande': marca(p['cheio'], 104, 0.235),
        'cabecalho': marca(p['cheio'], 34, 0.235),
        's64': so_simbolo(p['cheio'], 64),
        'u64': so_simbolo(p['uma'], 64),
        'm48': so_simbolo(p['mini'], 48),
        'm32': so_simbolo(p['mini'], 32),
        'm16': so_simbolo(p['mini'], 16),
        'ideia': p['ideia'], 'contra': p['contra'],
    }


def pagina(titulo, abertura, propostas, fecho):
    return '''<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exclusive World Tours — %(titulo)s</title>
<style>
%(faces)s
%(css)s
</style>
</head>
<body>
<main class="folha">
<h1>%(titulo)s</h1>
%(abertura)s
<div class="tintas">
  <span class="tinta"><span class="amostra" style="background:%(tinta)s"></span>%(tinta)s &nbsp;tinta</span>
  <span class="tinta"><span class="amostra" style="background:%(cor)s"></span>%(cor)s &nbsp;cor</span>
</div>
<hr class="risco">
%(blocos)s
%(fecho)s
</main>
</body>
</html>
''' % {'titulo': titulo, 'abertura': abertura, 'fecho': fecho,
       'faces': faces(), 'css': css(),
       'tinta': PALETA['tinta'], 'cor': PALETA['cor'],
       'blocos': '\n'.join(
           (('<h2 class="seccao">%s</h2><p class="intro">%s</p>'
             % (p['seccao'], p.get('seccao_nota', '')))
            if p.get('seccao') else '') + bloco(p)
           for p in propostas)}


def escrever(html, nome):
    """Escreve-se nos dois sitios de proposito. O Render nem sempre serve
    uma pasta a partir do index.html quando o endereco leva barra no fim
    — ja apanhei um 404 em /logos/ com o /logos/index.html a funcionar.
    Um ficheiro na raiz nao depende disso e abre sempre."""
    for destino in (os.path.join(RAIZ, nome, 'index.html'),
                    os.path.join(RAIZ, nome + '.html')):
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, 'w') as f:
            f.write(html)
        print('escrito: %s (%d KB)' % (destino, os.path.getsize(destino) / 1024))
