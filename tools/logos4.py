#!/usr/bin/env python3
"""
Quarta ronda: ilustracao com volume, a duas cores.

As tres rondas anteriores falharam todas pela mesma razao, e a decisao
foi minha: impus que a marca fosse a uma so cor e a traco fino, e deixei
a paleta para depois. Isso tira a partida tudo o que faz um desenho
parecer rico. O Ricardo escolheu duas cores sem degrade e ilustracao com
volume — e isto e exatamente isso.

Volume sem degrade faz-se com **planos sobrepostos**. Nao ha nenhuma
transicao de cor em lado nenhum: ha formas cheias, umas a frente das
outras, e a profundidade nasce de quem tapa quem. As unicas variacoes
sao tintas planas das mesmas duas cores — uma tinta nao e um degrade,
imprime-se com a mesma chapa a menos percentagem.

Duas cores e so duas:

    tinta   #0B2B2A   verde-atlantico muito escuro, quase preto
    cor     #CE7030   ambar quente — sol, areia, sul

A escolha das cores e trocavel num sitio so (PALETA, aqui em baixo).
Nesta ronda o que se julga e o desenho; se o desenho servir, a cor afina-se
depois sem mexer em mais nada.

Cada proposta vem em tres estados, porque uma marca tem de aguentar os
tres ou nao serve:

  - a cores, sobre claro e sobre escuro;
  - a uma cor so, para carimbo, fatura e fax do operador;
  - reduzida a 16 px, redesenhada com menos planos.

    python3 tools/logos4.py      # escreve logos4/index.html e logos4.html
"""

import base64
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
FONTES = os.path.join(RAIZ, 'assets', 'fontes')

# O ambar nao e so uma escolha de gosto: tem de passar os 3:1 que a WCAG
# pede aos elementos graficos, nos DOIS papeis. O #E4873F que eu tinha
# dava 2.44:1 sobre o creme — reprovava. Este da 3.2:1 sobre o creme e
# 5.21:1 sobre o escuro, e mantem o calor.
PALETA = {'tinta': '#0B2B2A', 'cor': '#CE7030'}

PAPEL_CLARO = '#F6F4F1'
PAPEL_ESCURO = '#0B1715'
TINTA_ESCURO = '#F3F1EE'          # sobre escuro a "tinta" e o claro


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


# As tres tintas de cada palco. As percentagens sao as mesmas nos dois,
# o resultado e que muda — e e suposto mudar.
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

USADAS = [
    ('archivo-latin-500-normal.woff2', 'Archivo', 500),
    ('archivo-latin-600-normal.woff2', 'Archivo', 600),
    ('archivo-latin-700-normal.woff2', 'Archivo', 700),
    ('inter-latin-400-normal.woff2',   'Inter', 400),
    ('inter-latin-500-normal.woff2',   'Inter', 500),
    ('inter-latin-600-normal.woff2',   'Inter', 600),
]


def faces():
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


# ====================================================================
# Os simbolos.
#
# Todos no mesmo quadrado de 100x100 e com a mesma gramatica:
#
#   .p   plano de tinta        (a cor escura, o primeiro plano)
#   .pf  plano de tinta fraca  (tinta a 20% — o plano do meio)
#   .c   plano de cor          (o ambar, o que salta)
#   .cf  plano de cor fraca    (ambar a 48% — o plano de tras)
#
# Nenhum degrade. A profundidade vem de quem tapa quem, e a ordem no
# ficheiro e a ordem dos planos: de tras para a frente, sempre.
#
# A versao a uma cor nao e a mesma com as cores apagadas — isso daria
# uma mancha. E um desenho com menos planos, feito a mao, que mantem a
# silhueta reconhecivel.
# ====================================================================

_CONTA = [0]


def disco(dentro, raio=50):
    """O recorte circular que todos partilham. O circulo de fundo e o
    papel do sitio onde a marca esta, por isso em escuro o 'ceu' fica
    escuro sem se tocar no desenho.

    O id do clipPath vem de um contador e nao de um hash do conteudo: o
    hash de texto em Python muda a cada arranque, e isso dava um ficheiro
    diferente a cada geracao sem nada ter mudado. Um gerador tem de dar
    sempre o mesmo resultado para a mesma entrada, senao nao se consegue
    ver no git o que mudou de verdade."""
    _CONTA[0] += 1
    return ('<defs><clipPath id="%(id)s"><circle cx="50" cy="50" r="%(r)s"/>'
            '</clipPath></defs>'
            '<circle cx="50" cy="50" r="%(r)s" class="papel"/>'
            '<g clip-path="url(#%(id)s)">%(d)s</g>') % {
        'id': 'rec%d' % _CONTA[0], 'r': raio, 'd': dentro}


def svg(dentro, w=100, h=100, rotulo=''):
    return ('<svg viewBox="0 0 %d %d" class="sim" role="img" aria-label="%s">'
            '%s</svg>' % (w, h, rotulo, dentro))


# ---------------------------------------------------------------- S. o vale
S_CHEIO = svg(disco(
    # o sol, atras de tudo
    '<circle cx="66" cy="34" r="15" class="c"/>'
    # a serra de tras
    '<path d="M-5 62 L18 38 L38 58 L58 32 L80 56 L105 36 L105 105 L-5 105Z" class="cf"/>'
    # a serra do meio
    '<path d="M-5 74 L22 50 L46 70 L72 46 L105 72 L105 105 L-5 105Z" class="pf"/>'
    # a colina da frente
    '<path d="M-5 86 L26 66 L52 84 L78 64 L105 84 L105 105 L-5 105Z" class="p"/>'),
    rotulo='Serra em planos, com o sol atras')

S_UMA = svg(disco(
    '<circle cx="66" cy="34" r="15" class="u-f"/>'
    '<path d="M-5 74 L22 50 L46 70 L72 46 L105 72 L105 105 L-5 105Z" class="u-f"/>'
    '<path d="M-5 86 L26 66 L52 84 L78 64 L105 84 L105 105 L-5 105Z" class="u"/>'),
    rotulo='Serra em planos, a uma cor')

S_MINI = svg(disco(
    '<circle cx="64" cy="34" r="16" class="c"/>'
    '<path d="M-5 84 L30 54 L58 82 L84 58 L105 80 L105 105 L-5 105Z" class="p"/>'),
    rotulo='Serra, versao reduzida')


# ---------------------------------------------------------------- T. a baia
T_CHEIO = svg(disco(
    '<circle cx="34" cy="32" r="13" class="c"/>'
    # o promontorio de tras
    '<path d="M105 50 L78 30 L58 46 L48 40 L34 52 L105 52Z" class="cf"/>'
    # o mar
    '<path d="M-5 62 L105 62 L105 105 L-5 105Z" class="pf"/>'
    # o promontorio da frente, a entrar no mar
    '<path d="M-5 44 L16 30 L34 48 L48 42 L62 62 L-5 62Z" class="p"/>'
    # a onda da frente
    '<path d="M-5 80 C18 70, 34 90, 56 80 C74 72, 88 86, 105 78 L105 105 L-5 105Z"'
    ' class="p"/>'),
    rotulo='Baia com promontorio, mar e sol')

T_UMA = svg(disco(
    '<circle cx="34" cy="32" r="13" class="u-f"/>'
    '<path d="M-5 62 L105 62 L105 105 L-5 105Z" class="u-f"/>'
    '<path d="M-5 44 L16 30 L34 48 L48 42 L62 62 L-5 62Z" class="u"/>'
    '<path d="M-5 80 C18 70, 34 90, 56 80 C74 72, 88 86, 105 78 L105 105 L-5 105Z"'
    ' class="u"/>'),
    rotulo='Baia, a uma cor')

T_MINI = svg(disco(
    '<circle cx="32" cy="32" r="15" class="c"/>'
    '<path d="M-5 66 L105 66 L105 105 L-5 105Z" class="p"/>'
    '<path d="M-5 44 L18 26 L40 52 L54 44 L70 66 L-5 66Z" class="p"/>'),
    rotulo='Baia, versao reduzida')


# ---------------------------------------------------------------- U. a vela
U_CHEIO = svg(disco(
    '<circle cx="70" cy="30" r="13" class="cf"/>'
    # a vela de tras
    '<path d="M50 20 L50 64 L78 64 Z" class="c"/>'
    # a vela da frente
    '<path d="M46 16 L46 64 L20 64 Z" class="p"/>'
    # o mar
    '<path d="M-5 68 L105 68 L105 105 L-5 105Z" class="pf"/>'
    # o casco
    '<path d="M12 68 L86 68 L72 82 L26 82 Z" class="p"/>'),
    rotulo='Veleiro de duas velas sobre o mar')

U_UMA = svg(disco(
    '<circle cx="70" cy="30" r="13" class="u-f"/>'
    '<path d="M50 20 L50 64 L78 64 Z" class="u-f"/>'
    '<path d="M46 16 L46 64 L20 64 Z" class="u"/>'
    '<path d="M12 68 L86 68 L72 82 L26 82 Z" class="u"/>'),
    rotulo='Veleiro, a uma cor')

U_MINI = svg(disco(
    '<path d="M52 18 L52 66 L82 66 Z" class="c"/>'
    '<path d="M46 14 L46 66 L16 66 Z" class="p"/>'
    '<path d="M10 72 L90 72 L74 88 L26 88 Z" class="p"/>'),
    rotulo='Veleiro, versao reduzida')


# -------------------------------------------------------------- V. a cidade
#
# A primeira versao tinha o recorte redondo e o chao a tapar a base da
# cupula: ficava uma mancha com uma torre espetada. Esta fica solta sobre
# uma linha de chao, que e o que deixa a silhueta respirar, e a cupula
# assenta mesmo no chao em vez de desaparecer dentro dele.

V_CHEIO = svg(
    '<circle cx="84" cy="26" r="12" class="cf"/>'
    # a torre de tras, com o remate
    '<path d="M61 24 L73 24 L73 78 L61 78 Z" class="c"/>'
    '<path d="M60 24 L67 10 L74 24 Z" class="c"/>'
    # os telhados baixos, atras
    '<path d="M3 78 L3 64 L11 54 L19 64 L19 78 Z" class="pf"/>'
    '<path d="M79 78 L79 62 L87 53 L95 62 L95 78 Z" class="pf"/>'
    # a cupula, assente no chao
    '<path d="M20 78 L20 54 A17 17 0 0 1 54 54 L54 78 Z" class="p"/>'
    '<rect x="35" y="30" width="4" height="8" class="p"/>'
    # o chao
    '<rect x="2" y="78" width="96" height="7" rx="3.5" class="p"/>'
    # as janelas, abertas a papel na massa escura
    '<g class="papel">'
    '<rect x="29" y="60" width="6" height="18" rx="3"/>'
    '<rect x="39" y="60" width="6" height="18" rx="3"/>'
    '<rect x="64" y="38" width="6" height="9" rx="3"/>'
    '<rect x="64" y="54" width="6" height="9" rx="3"/>'
    '</g>',
    rotulo='Cidade europeia: cupula, torre e telhados')

V_UMA = svg(
    '<circle cx="84" cy="26" r="12" class="u-f"/>'
    '<path d="M61 24 L73 24 L73 78 L61 78 Z" class="u"/>'
    '<path d="M60 24 L67 10 L74 24 Z" class="u"/>'
    '<path d="M3 78 L3 64 L11 54 L19 64 L19 78 Z" class="u-f"/>'
    '<path d="M79 78 L79 62 L87 53 L95 62 L95 78 Z" class="u-f"/>'
    '<path d="M20 78 L20 54 A17 17 0 0 1 54 54 L54 78 Z" class="u"/>'
    '<rect x="35" y="30" width="4" height="8" class="u"/>'
    '<rect x="2" y="78" width="96" height="7" rx="3.5" class="u"/>',
    rotulo='Cidade, a uma cor')

V_MINI = svg(
    # tres pecas e nada mais: torre, cupula, chao
    '<path d="M60 18 L76 18 L76 76 L60 76 Z" class="c"/>'
    '<path d="M18 76 L18 50 A20 20 0 0 1 58 50 L58 76 Z" class="p"/>'
    '<rect x="2" y="78" width="96" height="10" rx="5" class="p"/>',
    rotulo='Cidade, versao reduzida')


# ------------------------------------------------------------- W. a estrada
#
# A primeira tinha o recorte redondo a cortar as colinas: sobrava um cone
# com uma bola em cima e lia-se vulcao. Agora as colinas atravessam o
# quadrado todo e a estrada ocupa so o meio — e a largura das colinas que
# faz a estrada parecer estrada.

W_CHEIO = svg(
    '<circle cx="50" cy="28" r="13" class="c"/>'
    '<path d="M0 50 L18 34 L36 50 L52 32 L70 48 L86 36 L100 50 L100 60 L0 60 Z"'
    ' class="cf"/>'
    '<path d="M0 60 L22 46 L44 62 L64 46 L84 60 L100 52 L100 70 L0 70 Z"'
    ' class="pf"/>'
    '<path d="M41 66 L59 66 L88 94 L12 94 Z" class="p"/>'
    '<rect x="2" y="94" width="96" height="7" rx="3.5" class="p"/>'
    '<g class="papel">'
    '<rect x="48.2" y="70" width="3.6" height="6" rx="1.8"/>'
    '<rect x="47.4" y="80" width="5.2" height="7" rx="2.6"/>'
    '</g>',
    rotulo='Estrada a fugir para o horizonte entre colinas')

W_UMA = svg(
    '<circle cx="50" cy="28" r="13" class="u-f"/>'
    '<path d="M0 60 L22 46 L44 62 L64 46 L84 60 L100 52 L100 70 L0 70 Z"'
    ' class="u-f"/>'
    '<path d="M41 66 L59 66 L88 94 L12 94 Z" class="u"/>'
    '<rect x="2" y="94" width="96" height="7" rx="3.5" class="u"/>',
    rotulo='Estrada, a uma cor')

W_MINI = svg(
    '<circle cx="50" cy="26" r="16" class="c"/>'
    '<path d="M0 58 L24 42 L50 64 L74 42 L100 58 L100 72 L0 72 Z" class="p"/>'
    '<path d="M40 64 L60 64 L92 96 L8 96 Z" class="p"/>',
    rotulo='Estrada, versao reduzida')


# --------------------------------------------------------------- X. a ilha
#
# A primeira tinha um anel de agua claro por fora e a praia em baixo como
# uma taca, com uma serra la dentro: lia-se copo, nao ilha. Esta e mesmo
# vista de cima — a agua enche o disco todo, a praia e a orla em ambar e a
# terra e a mesma forma mais pequena por cima.

# A costa tem de ser irregular ou nao e uma ilha. A minha primeira forma
# era quase um circulo e, com a orla por fora, lia-se alvo. Esta tem um
# lobo a poente, um cabo a nascente, um istmo e uma enseada a sul — e um
# ilheu ao largo, que e o que diz "arquipelago" sem se desenhar mais nada.
_ILHA_TERRA = ('M30 24 C40 18, 52 20, 58 28 C62 34, 72 30, 78 36 '
               'C84 42, 82 50, 74 54 C68 57, 66 62, 70 68 '
               'C73 73, 68 80, 60 78 C54 76.5, 50 70, 44 72 '
               'C37 74, 28 70, 26 62 C24 55, 28 50, 24 44 '
               'C20 38, 23 28, 30 24 Z')

# A orla de praia e a mesma costa afastada para fora. Afastar com uma
# escala a volta do centro da a mesma folga em toda a volta sem se
# redesenhar o contorno — e assim a praia nunca pode discordar da terra.
_ORLA = 'translate(50 50) scale(1.13) translate(-50 -50)'
_ORLA_ILHEU = 'translate(84 72) scale(1.45) translate(-84 -72)'

X_CHEIO = svg(disco(
    '<rect x="-5" y="-5" width="110" height="110" class="pf"/>'
    '<g class="c"><path d="%(t)s" transform="%(o)s"/>'
    '<circle cx="84" cy="72" r="5" transform="%(oi)s"/></g>'
    '<g class="p"><path d="%(t)s"/><circle cx="84" cy="72" r="5"/></g>'
    % {'t': _ILHA_TERRA, 'o': _ORLA, 'oi': _ORLA_ILHEU}),
    rotulo='Ilha vista de cima, com orla de praia, enseada e ilheu ao largo')

X_UMA = svg(disco(
    '<rect x="-5" y="-5" width="110" height="110" class="u-f"/>'
    '<g class="u"><path d="%(t)s"/><circle cx="84" cy="72" r="5"/></g>'
    % {'t': _ILHA_TERRA}),
    rotulo='Ilha, a uma cor')

X_MINI = svg(disco(
    '<rect x="-5" y="-5" width="110" height="110" class="cf"/>'
    '<path d="%(t)s" transform="%(o)s" class="p"/>'
    % {'t': _ILHA_TERRA, 'o': _ORLA}),
    rotulo='Ilha, versao reduzida')


# ==================================================== o nome ao lado
NOME = ('<span class="nome">'
        '<span class="nome-l1">Exclusive</span>'
        '<span class="nome-l2">World Tours</span></span>')


PROPOSTAS = [
    {'letra': 'S', 'nome': 'O vale',
     'cheio': S_CHEIO, 'uma': S_UMA, 'mini': S_MINI,
     'ideia': 'Tres cristas de serra umas a frente das outras e o sol por '
              'tras. Nao ha um unico degrade: a profundidade e so quem tapa '
              'quem, e e por isso que isto imprime igual num autocolante, '
              'num carimbo e numa fatura a preto. E a mais paisagem das '
              'seis, e a que diz "dia inteiro fora" sem pedir legenda.',
     'contra': 'Serra com sol e o desenho mais feito do turismo. Esta '
               'distingue-se pelo recorte e pelo numero de planos, nao pelo '
               'assunto — e isso e uma vantagem fina, que se perde se a cor '
               'for a errada.'},

    {'letra': 'T', 'nome': 'A baia',
     'cheio': T_CHEIO, 'uma': T_UMA, 'mini': T_MINI,
     'ideia': 'Um promontorio a entrar no mar, com a ponta de tras mais '
              'clara a dar a distancia. E a costa — que e o que a Irlanda, '
              'Portugal, Espanha e a Italia tem em comum e o que os seis '
              'paises vendem de facto. A onda da frente da-lhe movimento '
              'sem nenhuma linha solta.',
     'contra': 'Com o recorte redondo pode ler-se como vigia de barco e '
               'puxar a marca para cruzeiros, que nao e o negocio.'},

    {'letra': 'U', 'nome': 'A vela',
     'cheio': U_CHEIO, 'uma': U_UMA, 'mini': U_MINI,
     'ideia': 'Duas velas, uma a tapar a outra, e o casco por baixo. E o '
              'simbolo de viagem com mais silhueta de todos — reconhece-se '
              'a 16 px sem perder nada, que e o teste que as rondas '
              'anteriores falhavam. E diz Mediterraneo e Atlantico ao '
              'mesmo tempo.',
     'contra': 'Um veleiro promete barco, e a maioria dos tours e de '
               'carrinha. E a mais bonita e a menos verdadeira da lista, e '
               'isso conta.'},

    {'letra': 'V', 'nome': 'A cidade',
     'cheio': V_CHEIO, 'uma': V_UMA, 'mini': V_MINI,
     'ideia': 'Uma cupula, uma torre e dois telhados, com as janelas '
              'abertas a papel na massa escura. E a Europa sem ser nenhuma '
              'cidade em particular — nao copia Roma nem Lisboa, mas '
              'qualquer pessoa ve as duas. Das seis, e a unica que fala de '
              'cidade, que e de onde todos os tours partem.',
     'contra': 'Tem o maior numero de pecas pequenas, e as janelas sao as '
               'primeiras a fechar quando o simbolo encolhe. Obriga mesmo '
               'a versao reduzida, nao e um luxo.'},

    {'letra': 'W', 'nome': 'A estrada',
     'cheio': W_CHEIO, 'uma': W_UMA, 'mini': W_MINI,
     'ideia': 'A estrada a abrir em direcao a quem olha, entre duas linhas '
              'de colinas, com o sol a nascer no meio. E literalmente o '
              'produto: sair de manha de carrinha e ver o pais a passar. '
              'Os tracos brancos a aumentar dao a perspetiva sem desenhar '
              'nenhuma fuga.',
     'contra': 'Estrada em perspetiva e linguagem de empresa de aluguer de '
               'carros. A diferenca esta no sol e nas colinas, e isso a '
               '16 px desaparece.'},

    {'letra': 'X', 'nome': 'A ilha',
     'cheio': X_CHEIO, 'uma': X_UMA, 'mini': X_MINI,
     'ideia': 'Uma ilha vista de cima: a terra escura, a orla de praia em '
              'ambar a toda a volta e um ilheu ao largo. A costa tem um '
              'cabo, um istmo e uma enseada — e a irregularidade que faz '
              'isto ler-se como um sitio real e nao como um circulo. E a '
              'mais abstrata das seis e a unica que nao se parece com nada '
              'que a Viator ou a GetYourGuide usem.',
     'contra': 'Precisa de um segundo para se perceber. Marcas que precisam '
               'de um segundo ou sao as melhores ou sao as piores, e isso '
               'so se sabe depois de a ver em cem sitios.'},
]


CSS = '''
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%%}
/* As cores claras sao as de omissao e ficam no body, nao na marca. Uma
   variavel declarada no proprio elemento ganha a que vem de um
   antepassado, por isso declara-las na .marca fazia o palco escuro nao
   ter efeito nenhum e o nome ficava escuro sobre escuro. No body sao
   herdadas por toda a gente — cabecalho e caixas incluidos, que era o
   que faltava — e o palco escuro, por estar mais perto, troca-as. */
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

.tintas{display:flex;gap:10px;flex-wrap:wrap;margin:22px 0 0}
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

/* ---------------------------------------------------------- as marcas
   A raiz leva --t e tudo por dentro esta em em: um numero escala a marca
   inteira. No palco o tamanho e min(--t, 97cqw x --k), com cqw — a
   largura do proprio palco — porque os palcos sao dois a dois e a conta
   em vw nao sabe nada sobre o espaco que cada um tem. */
.marca{font-size:var(--t);line-height:1;display:inline-flex;align-items:center;
  gap:.62em}
.palco .marca{font-size:min(var(--t), calc(97cqw * var(--k)))}
.marca .sim{width:1em;height:1em;flex:none;display:block}
.nome{display:inline-flex;flex-direction:column;align-items:flex-start;
  font-family:'Archivo',sans-serif;font-weight:600;text-transform:uppercase;
  color:var(--tinta);line-height:1;white-space:nowrap}
.nome-l1{font-size:.268em;letter-spacing:.075em;margin-right:-.075em}
.nome-l2{font-size:.268em;letter-spacing:.2165em;margin-right:-.2165em;
  margin-top:.19em}

/* ------------------------------------------------------------ os planos
   Quatro classes para toda a ronda. Nenhum gradiente em lado nenhum: as
   tintas fracas sao percentagens planas das mesmas duas cores, que e o
   que uma grafica faz com a mesma chapa. */
.sim .papel, .sim .papel-f{fill:var(--papel)}
.sim .p{fill:var(--tinta)}
.sim .pf{fill:var(--tinta-f)}
.sim .c{fill:var(--cor)}
.sim .cf{fill:var(--cor-f)}
/* a uma cor so: tudo tinta, e o plano de tras na tinta fraca */
.sim .u{fill:var(--tinta)}
.sim .u-f{fill:var(--uma-f)}

@media (max-width:620px){
  .folha{padding:40px 16px 72px}
  .palco{padding:34px 16px;min-height:160px}
}
'''


def marca(simbolo, t, k):
    return ('<span class="marca" style="--t:%gpx;--k:%g">%s%s</span>'
            % (t, k, simbolo, NOME))


def so_simbolo(simbolo, t):
    return ('<span class="marca" style="--t:%gpx;--k:1">%s</span>'
            % (t, simbolo))


def bloco(p):
    return '''
<section>
  <div class="cabeca"><span class="selo">%(letra)s</span><h2>%(nome)s</h2></div>

  <div class="par">
    <div class="palco claro">%(grande)s</div>
    <div class="palco escuro">%(escuro)s</div>
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
        'escuro': marca(p['cheio'], 104, 0.235),
        'cabecalho': marca(p['cheio'], 34, 0.235),
        's64': so_simbolo(p['cheio'], 64),
        'u64': so_simbolo(p['uma'], 64),
        'm48': so_simbolo(p['mini'], 48),
        'm32': so_simbolo(p['mini'], 32),
        'm16': so_simbolo(p['mini'], 16),
        'ideia': p['ideia'], 'contra': p['contra'],
    }


def main():
    html = '''<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exclusive World Tours — quarta ronda: ilustracao com volume</title>
<style>
%(faces)s
%(css)s
</style>
</head>
<body>
<main class="folha">

<h1>Quarta ronda: ilustracao com volume, a duas cores</h1>
<p class="intro">As tres rondas anteriores falharam todas pela mesma razao, e
a decisao foi minha: impus que a marca fosse a <strong>uma so cor e a traco
fino</strong>, e deixei a paleta para depois. Isso tira a partida tudo o que
faz um desenho parecer rico. Isto corrige isso.</p>
<p class="intro">Volume sem degrade faz-se com <strong>planos sobrepostos</strong>.
Nao ha uma unica transicao de cor em lado nenhum: ha formas cheias, umas a
frente das outras, e a profundidade nasce de quem tapa quem. As variacoes mais
claras sao tintas planas das mesmas duas cores — o que uma grafica faz com a
mesma chapa a menos percentagem.</p>
<div class="tintas">
  <span class="tinta"><span class="amostra" style="background:%(tinta)s"></span>%(tinta)s &nbsp;tinta</span>
  <span class="tinta"><span class="amostra" style="background:%(cor)s"></span>%(cor)s &nbsp;cor</span>
</div>
<p class="intro" style="margin-top:18px">As cores em si trocam-se num sitio so.
Nesta ronda o que se julga e <strong>o desenho</strong>; se o desenho servir,
a cor afina-se depois sem mexer em mais nada. Cada proposta aparece tambem a
uma cor — para carimbo, fatura e preto e branco — e reduzida a 16 px com menos
planos, porque uma marca que so funciona grande nao e uma marca.</p>

<hr class="risco">

%(blocos)s

<p class="fim">Diz-me uma ou duas e afino a mao: proporcoes, recorte, numero de
planos, e a cor certa a serio.<br>
Entrego depois em SVG, PNG e favicon, nas tres versoes.</p>

</main>
</body>
</html>
''' % {'faces': faces(), 'css': CSS % {
           'papel_claro': PAPEL_CLARO, 'papel_escuro': PAPEL_ESCURO,
           'vars_claro': vars_css('claro'), 'vars_escuro': vars_css('escuro'),
       },
       'tinta': PALETA['tinta'], 'cor': PALETA['cor'],
       'blocos': '\n'.join(bloco(p) for p in PROPOSTAS)}

    for destino in (os.path.join(RAIZ, 'logos4', 'index.html'),
                    os.path.join(RAIZ, 'logos4.html')):
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, 'w') as f:
            f.write(html)
        print('escrito: %s (%d KB)' % (destino, os.path.getsize(destino) / 1024))
    print('%d propostas' % len(PROPOSTAS))


if __name__ == '__main__':
    main()
