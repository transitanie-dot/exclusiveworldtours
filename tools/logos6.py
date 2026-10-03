#!/usr/bin/env python3
"""
Sexta ronda: variacoes do A (a capa) e do D (o aberto).

O Ricardo escolheu dois dos seis passaportes. Esta ronda nao introduz
ideias novas — leva esses dois a serio e tira-lhes cinco versoes a cada,
que e o trabalho que falta fazer depois de uma escolha e antes de uma
decisao.

As variacoes nao sao aleatorias. Em cada familia mexe-se numa coisa de
cada vez — a silhueta, o enquadramento do brasao, o corte, o
transbordo, a faixa — para se perceber qual e o movimento que faz a
diferenca. Mudar tudo ao mesmo tempo nao ensina nada.

Esta pagina NAO vai para o site. E so para decidir.

    python3 tools/logos6.py        # escreve logos6.html
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from marca_base import escrever, pagina, svg  # noqa: E402


# A capa de base, a mesma das outras rondas: 60 x 84, cantos a 6.
CAPA = ('M26 8 h48 a6 6 0 0 1 6 6 v72 a6 6 0 0 1 -6 6 h-48 '
        'a6 6 0 0 1 -6 -6 v-72 a6 6 0 0 1 6 -6 Z')
LOMBADA = ('M26 8 h7 v84 h-7 a6 6 0 0 1 -6 -6 v-72 a6 6 0 0 1 6 -6 Z')


def brasao(cx, cy, r, w, sol='c', linhas='papel'):
    """O sol meio enterrado no horizonte, com a linha de agua mais larga
    do que ele e duas ondas finas por baixo.

    O sol tem de estar enterrado e nao pousado: pousado em cima de duas
    barras, isto le-se hamburguer — aconteceu-me na ronda passada e so
    se ve depois de desenhado."""
    meia = max(2.4, r * 0.22)
    return (
        '<path d="M%(e).1f %(y).1f A%(r).1f %(r).1f 0 0 1 %(d).1f %(y).1f Z" '
        'class="%(sol)s"/>'
        '<g class="%(lin)s">'
        '<rect x="%(x1).1f" y="%(y).1f" width="%(w).1f" height="%(h).1f" rx="%(hr).1f"/>'
        '<rect x="%(x2).1f" y="%(y2).1f" width="%(w2).1f" height="%(h2).1f" rx="%(hr2).1f"/>'
        '<rect x="%(x3).1f" y="%(y3).1f" width="%(w3).1f" height="%(h2).1f" rx="%(hr2).1f"/>'
        '</g>') % {
        'e': cx - r, 'd': cx + r, 'y': cy, 'r': r,
        'sol': sol, 'lin': linhas,
        'x1': cx - w / 2, 'w': w, 'h': meia, 'hr': meia / 2,
        'x2': cx - w / 2 + w * .10, 'y2': cy + meia * 2.6,
        'w2': w * .56, 'h2': meia * .8, 'hr2': meia * .4,
        'x3': cx - w / 2 + w * .34, 'y3': cy + meia * 4.6, 'w3': w * .40,
    }


def linhas_capa(cx, y, cor='c'):
    """As duas linhas de texto por baixo do brasao, que e o que torna
    aquilo uma capa de documento e nao um quadro."""
    return ('<g class="%s">'
            '<rect x="%.1f" y="%.1f" width="27" height="3.4" rx="1.7"/>'
            '<rect x="%.1f" y="%.1f" width="19" height="3.4" rx="1.7"/>'
            '</g>' % (cor, cx - 13.5, y, cx - 9.5, y + 8))


# ====================================================================
# Familia A — a capa fechada
# ====================================================================

# ---- A1. a capa limpa: sem lombada, brasao a mandar -----------------
A1 = svg('<path d="%s" class="p"/>' % CAPA +
         brasao(50, 48, 19, 48) + linhas_capa(50, 72),
         rotulo='Capa sem lombada, com o brasao grande')
A1U = svg('<path d="%s" class="u"/>' % CAPA +
          brasao(50, 48, 19, 48, sol='u-f') + linhas_capa(50, 72, 'u-f'),
          rotulo='Capa limpa, a uma cor')
A1M = svg('<path d="M22 8 h56 a7 7 0 0 1 7 7 v70 a7 7 0 0 1 -7 7 h-56'
          ' a7 7 0 0 1 -7 -7 v-70 a7 7 0 0 1 7 -7 Z" class="p"/>'
          '<path d="M28 58 A22 22 0 0 1 72 58 Z" class="c"/>'
          '<rect x="23" y="58" width="54" height="7" rx="3.5" class="papel"/>',
          rotulo='Capa limpa, versao reduzida')

# ---- A2. o brasao dentro de um escudo -------------------------------
ESCUDO = ('M39 26 h31 a4 4 0 0 1 4 4 v22 c0 10 -8 16 -19.5 20 '
          'C43 68 35 62 35 52 v-22 a4 4 0 0 1 4 -4 Z')
A2 = svg('<path d="%s" class="p"/>' % CAPA +
         '<path d="%s" class="pf"/>' % LOMBADA +
         '<path d="%s" class="papel"/>' % ESCUDO +
         brasao(54.5, 48, 12, 30, sol='c', linhas='p') +
         linhas_capa(56.5, 76),
         rotulo='Capa com o brasao dentro de um escudo')
A2U = svg('<path d="%s" class="u"/>' % CAPA +
          '<path d="%s" class="u-f"/>' % LOMBADA +
          '<path d="%s" class="papel"/>' % ESCUDO +
          brasao(54.5, 48, 12, 30, sol='u-f', linhas='u') +
          linhas_capa(56.5, 76, 'u-f'),
          rotulo='Capa com escudo, a uma cor')
A2M = svg('<path d="M22 8 h56 a7 7 0 0 1 7 7 v70 a7 7 0 0 1 -7 7 h-56'
          ' a7 7 0 0 1 -7 -7 v-70 a7 7 0 0 1 7 -7 Z" class="p"/>'
          '<path d="M30 26 h40 a5 5 0 0 1 5 5 v26 c0 13 -11 20 -25 26 '
          'C36 77 25 70 25 57 v-26 a5 5 0 0 1 5 -5 Z" class="c"/>',
          rotulo='Capa com escudo, versao reduzida')

# ---- A3. o canto cortado --------------------------------------------
CAPA_CORTADA = ('M26 8 h38 L80 24 v62 a6 6 0 0 1 -6 6 h-48 '
                'a6 6 0 0 1 -6 -6 v-72 a6 6 0 0 1 6 -6 Z')
A3 = svg('<path d="%s" class="p"/>' % CAPA_CORTADA +
         '<path d="M64 8 L80 24 h-16 Z" class="c"/>' +
         '<path d="%s" class="pf"/>' % LOMBADA +
         brasao(56.5, 52, 14, 38) + linhas_capa(56.5, 74),
         rotulo='Capa com o canto superior cortado em diagonal')
A3U = svg('<path d="%s" class="u"/>' % CAPA_CORTADA +
          '<path d="M64 8 L80 24 h-16 Z" class="u-f"/>' +
          '<path d="%s" class="u-f"/>' % LOMBADA +
          brasao(56.5, 52, 14, 38, sol='u-f') + linhas_capa(56.5, 74, 'u-f'),
          rotulo='Capa com canto cortado, a uma cor')
A3M = svg('<path d="M22 8 h36 L85 35 v50 a7 7 0 0 1 -7 7 h-56'
          ' a7 7 0 0 1 -7 -7 v-70 a7 7 0 0 1 7 -7 Z" class="p"/>'
          '<path d="M58 8 L85 35 h-27 Z" class="c"/>',
          rotulo='Capa com canto cortado, versao reduzida')

# ---- A4. o sol que transborda ---------------------------------------
A4 = svg('<circle cx="56.5" cy="22" r="18" class="c"/>'
         '<path d="M26 22 h48 a6 6 0 0 1 6 6 v58 a6 6 0 0 1 -6 6 h-48 '
         'a6 6 0 0 1 -6 -6 v-58 a6 6 0 0 1 6 -6 Z" class="p"/>'
         '<path d="M26 22 h7 v70 h-7 a6 6 0 0 1 -6 -6 v-58 a6 6 0 0 1 6 -6 Z"'
         ' class="pf"/>' +
         linhas_capa(56.5, 46) +
         '<g class="c">'
         '<rect x="43" y="68" width="27" height="3.4" rx="1.7"/>'
         '<rect x="47" y="76" width="19" height="3.4" rx="1.7"/>'
         '</g>',
         rotulo='Capa com o sol a nascer por tras da aresta de cima')
A4U = svg('<circle cx="56.5" cy="22" r="18" class="u-f"/>'
          '<path d="M26 22 h48 a6 6 0 0 1 6 6 v58 a6 6 0 0 1 -6 6 h-48 '
          'a6 6 0 0 1 -6 -6 v-58 a6 6 0 0 1 6 -6 Z" class="u"/>'
          '<path d="M26 22 h7 v70 h-7 a6 6 0 0 1 -6 -6 v-58 a6 6 0 0 1 6 -6 Z"'
          ' class="u-f"/>' +
          linhas_capa(56.5, 46, 'u-f') +
          '<g class="u-f">'
          '<rect x="43" y="68" width="27" height="3.4" rx="1.7"/>'
          '</g>',
          rotulo='Capa com o sol a nascer, a uma cor')
A4M = svg('<circle cx="50" cy="26" r="24" class="c"/>'
          '<path d="M22 26 h56 a7 7 0 0 1 7 7 v52 a7 7 0 0 1 -7 7 h-56'
          ' a7 7 0 0 1 -7 -7 v-52 a7 7 0 0 1 7 -7 Z" class="p"/>',
          rotulo='Capa com o sol a nascer, versao reduzida')

# ---- A5. a faixa -----------------------------------------------------
A5 = svg('<path d="%s" class="p"/>' % CAPA +
         '<path d="%s" class="pf"/>' % LOMBADA +
         '<rect x="20" y="36" width="60" height="30" class="c"/>' +
         brasao(56.5, 54, 12, 32, sol='papel', linhas='p') +
         '<g class="c">'
         '<rect x="43" y="74" width="27" height="3.4" rx="1.7"/>'
         '<rect x="47" y="82" width="19" height="3.4" rx="1.7"/>'
         '</g>',
         rotulo='Capa com uma faixa larga e o brasao recortado nela')
A5U = svg('<path d="%s" class="u"/>' % CAPA +
          '<path d="%s" class="u-f"/>' % LOMBADA +
          '<rect x="20" y="36" width="60" height="30" class="u-f"/>' +
          brasao(56.5, 54, 12, 32, sol='papel', linhas='u') +
          '<g class="u-f">'
          '<rect x="43" y="74" width="27" height="3.4" rx="1.7"/>'
          '<rect x="47" y="82" width="19" height="3.4" rx="1.7"/>'
          '</g>',
          rotulo='Capa com faixa, a uma cor')
A5M = svg('<path d="M22 8 h56 a7 7 0 0 1 7 7 v70 a7 7 0 0 1 -7 7 h-56'
          ' a7 7 0 0 1 -7 -7 v-70 a7 7 0 0 1 7 -7 Z" class="p"/>'
          '<rect x="15" y="34" width="70" height="32" class="c"/>'
          '<path d="M30 60 A20 20 0 0 1 70 60 Z" class="papel"/>',
          rotulo='Capa com faixa, versao reduzida')


# ====================================================================
# Familia D — o passaporte aberto
# ====================================================================

ESQ = 'M50 20 C38 14, 24 13, 10 16 L10 80 C24 77, 38 78, 50 84 Z'
DIR = 'M50 20 C62 14, 76 13, 90 16 L90 80 C76 77, 62 78, 50 84 Z'
VINCO = '<rect x="47" y="19" width="6" height="66" rx="3" class="p"/>'


def linhas_pagina(x, y, larguras=(24, 20, 23), cor='papel'):
    out = ['<g class="%s">' % cor]
    for i, w in enumerate(larguras):
        out.append('<rect x="%d" y="%d" width="%d" height="3" rx="1.5"/>'
                   % (x, y + i * 9, w))
    out.append('</g>')
    return ''.join(out)


# ---- D1. o aberto, com o carimbo maior ------------------------------
D1 = svg('<path d="%s" class="pf"/>' % ESQ + '<path d="%s" class="p"/>' % DIR +
         VINCO + linhas_pagina(17, 30) +
         '<circle cx="70" cy="46" r="19" class="c"/>'
         '<circle cx="70" cy="46" r="11" class="papel"/>',
         rotulo='Passaporte aberto, com o carimbo grande na pagina direita')
D1U = svg('<path d="%s" class="u-f"/>' % ESQ + '<path d="%s" class="u"/>' % DIR +
          '<rect x="47" y="19" width="6" height="66" rx="3" class="u"/>' +
          linhas_pagina(17, 30) +
          '<circle cx="70" cy="46" r="19" class="papel"/>'
          '<circle cx="70" cy="46" r="11" class="u"/>',
          rotulo='Aberto com carimbo grande, a uma cor')
D1M = svg('<path d="M50 22 C36 14, 20 13, 6 16 L6 82 C20 79, 36 80, 50 88 Z" class="p"/>'
          '<path d="M50 22 C64 14, 80 13, 94 16 L94 82 C80 79, 64 80, 50 88 Z" class="c"/>',
          rotulo='Aberto, versao reduzida')

# ---- D2. o sol a nascer do vinco ------------------------------------
# Tentei primeiro o sol a sair da propria dobra. Nao funciona: o vinco
# corta-o ao meio e o que se le e meio disco encostado a uma barra, nao
# um sol a nascer. O brasao inteiro, centrado na pagina da direita, diz a
# mesma coisa e le-se a primeira.
D2 = svg('<path d="%s" class="pf"/>' % ESQ + '<path d="%s" class="p"/>' % DIR +
         linhas_pagina(17, 32, (22, 18), 'papel') + VINCO +
         brasao(70, 44, 15, 36, sol='c', linhas='papel'),
         rotulo='Passaporte aberto com o brasao na pagina da direita')
D2U = svg('<path d="%s" class="u-f"/>' % ESQ + '<path d="%s" class="u"/>' % DIR +
          linhas_pagina(17, 32, (22, 18), 'papel') +
          '<rect x="47" y="19" width="6" height="66" rx="3" class="u"/>' +
          brasao(70, 44, 15, 36, sol='papel', linhas='papel'),
          rotulo='Aberto com o brasao na pagina, a uma cor')
D2M = svg('<path d="M50 22 C36 14, 20 13, 6 16 L6 82 C20 79, 36 80, 50 88 Z" class="p"/>'
          '<path d="M50 22 C64 14, 80 13, 94 16 L94 82 C80 79, 64 80, 50 88 Z" class="p"/>'
          '<path d="M52 62 A22 22 0 0 1 96 62 Z" class="c"/>'
          '<rect x="48" y="62" width="52" height="7" rx="3.5" class="papel"/>',
          rotulo='Aberto com o brasao, versao reduzida')

# ---- D3. visto de cima ----------------------------------------------
D3 = svg('<path d="M50 30 C36 24, 20 23, 8 28 L8 70 C20 65, 36 66, 50 72 Z" class="pf"/>'
         '<path d="M50 30 C64 24, 80 23, 92 28 L92 70 C80 65, 64 66, 50 72 Z" class="p"/>'
         '<rect x="47" y="29" width="6" height="43" rx="3" class="p"/>' +
         linhas_pagina(15, 38, (22, 18), 'papel') +
         '<circle cx="71" cy="48" r="13" class="c"/>'
         '<circle cx="71" cy="48" r="7" class="papel"/>',
         rotulo='Passaporte aberto visto de cima, mais baixo e mais largo')
D3U = svg('<path d="M50 30 C36 24, 20 23, 8 28 L8 70 C20 65, 36 66, 50 72 Z" class="u-f"/>'
          '<path d="M50 30 C64 24, 80 23, 92 28 L92 70 C80 65, 64 66, 50 72 Z" class="u"/>'
          '<rect x="47" y="29" width="6" height="43" rx="3" class="u"/>' +
          linhas_pagina(15, 38, (22, 18), 'papel') +
          '<circle cx="71" cy="48" r="13" class="papel"/>'
          '<circle cx="71" cy="48" r="7" class="u"/>',
          rotulo='Aberto visto de cima, a uma cor')
D3M = svg('<path d="M50 32 C34 24, 16 23, 4 28 L4 72 C16 67, 34 68, 50 76 Z" class="p"/>'
          '<path d="M50 32 C66 24, 84 23, 96 28 L96 72 C84 67, 66 68, 50 76 Z" class="c"/>',
          rotulo='Aberto de cima, versao reduzida')

# ---- D4. dois carimbos ----------------------------------------------
D4 = svg('<path d="%s" class="pf"/>' % ESQ + '<path d="%s" class="p"/>' % DIR +
         VINCO +
         '<circle cx="27" cy="40" r="12" class="c"/>'
         '<circle cx="27" cy="40" r="7.5" class="papel"/>'
         '<rect x="21" y="38.5" width="12" height="3" rx="1.5" class="p"/>'
         '<rect x="16" y="62" width="22" height="3" rx="1.5" class="papel"/>'
         '<circle cx="71" cy="54" r="16" class="c"/>'
         '<circle cx="71" cy="54" r="10" class="papel"/>'
         '<rect x="63" y="52" width="16" height="4" rx="2" class="p"/>'
         '<rect x="60" y="28" width="22" height="3" rx="1.5" class="papel"/>',
         rotulo='Passaporte aberto com um carimbo em cada pagina')
D4U = svg('<path d="%s" class="u-f"/>' % ESQ + '<path d="%s" class="u"/>' % DIR +
          '<rect x="47" y="19" width="6" height="66" rx="3" class="u"/>'
          '<circle cx="27" cy="40" r="12" class="u"/>'
          '<circle cx="27" cy="40" r="7.5" class="papel"/>'
          '<rect x="21" y="38.5" width="12" height="3" rx="1.5" class="u"/>'
          '<circle cx="71" cy="54" r="16" class="papel"/>'
          '<circle cx="71" cy="54" r="10" class="u"/>'
          '<rect x="63" y="52" width="16" height="4" rx="2" class="papel"/>',
          rotulo='Aberto com dois carimbos, a uma cor')
D4M = svg('<path d="M50 22 C36 14, 20 13, 6 16 L6 82 C20 79, 36 80, 50 88 Z" class="p"/>'
          '<path d="M50 22 C64 14, 80 13, 94 16 L94 82 C80 79, 64 80, 50 88 Z" class="p"/>'
          '<circle cx="72" cy="52" r="17" class="c"/>',
          rotulo='Aberto com carimbo, versao reduzida')

# ---- D5. a paisagem na pagina ---------------------------------------
D5 = svg('<path d="%s" class="pf"/>' % ESQ + '<path d="%s" class="p"/>' % DIR +
         VINCO + linhas_pagina(17, 32, (24, 20), 'papel') +
         # a paisagem, dentro da pagina da direita
         '<circle cx="76" cy="40" r="9" class="c"/>'
         '<path d="M57 60 L66 48 L72 55 L80 44 L88 57 L88 62 '
         'C76 59, 66 60, 57 63 Z" class="papel"/>'
         '<rect x="57" y="70" width="20" height="3" rx="1.5" class="papel"/>',
         rotulo='Passaporte aberto com a paisagem na pagina da direita')
D5U = svg('<path d="%s" class="u-f"/>' % ESQ + '<path d="%s" class="u"/>' % DIR +
          '<rect x="47" y="19" width="6" height="66" rx="3" class="u"/>' +
          linhas_pagina(17, 32, (24, 20), 'papel') +
          '<circle cx="76" cy="40" r="9" class="papel"/>'
          '<path d="M57 60 L66 48 L72 55 L80 44 L88 57 L88 62 '
          'C76 59, 66 60, 57 63 Z" class="papel"/>',
          rotulo='Aberto com paisagem, a uma cor')
D5M = svg('<path d="M50 22 C36 14, 20 13, 6 16 L6 82 C20 79, 36 80, 50 88 Z" class="p"/>'
          '<path d="M50 22 C64 14, 80 13, 94 16 L94 82 C80 79, 64 80, 50 88 Z" class="p"/>'
          '<circle cx="76" cy="38" r="12" class="c"/>'
          '<path d="M54 66 L66 48 L75 59 L86 44 L94 58 L94 66 Z" class="c"/>',
          rotulo='Aberto com paisagem, versao reduzida')


PROPOSTAS = [
    {'letra': 'A1', 'nome': 'A capa limpa',
     'seccao': 'Familia A — a capa fechada',
     'seccao_nota': 'Cinco versoes do que escolheste. Em cada uma mexe-se '
                    '<strong>numa coisa de cada vez</strong> — a silhueta, o '
                    'enquadramento do brasao, o corte, o transbordo, a faixa '
                    '— para se ver qual e o movimento que faz a diferenca. '
                    'Mudar tudo ao mesmo tempo nao ensina nada.',
     'cheio': A1, 'uma': A1U, 'mini': A1M,
     'ideia': 'Fora a lombada, e o brasao cresce ate quase tocar nas margens. '
              'Sem a faixa da esquerda a silhueta fica um retangulo limpo, e e '
              'o sol que passa a mandar — o passaporte vira suporte em vez de '
              'ser o assunto. E a que melhor aguenta ficar pequena.',
     'contra': 'Sem lombada perde-se a espessura, e com ela a leitura de '
               'objeto: fica mais perto de um cartao do que de um '
               'passaporte.'},

    {'letra': 'A2', 'nome': 'O escudo',
     'cheio': A2, 'uma': A2U, 'mini': A2M,
     'ideia': 'O mesmo brasao, mas dentro de um escudo. E o gesto que separa '
              'um documento oficial de uma capa qualquer, e da ao sol um '
              'sitio onde morar em vez de ele flutuar no meio da capa. Para '
              'uma marca que quer dizer "exclusive", a forma do escudo '
              'trabalha a favor.',
     'contra': 'Escudos tambem sao brasoes de colegio e de equipa de futebol. '
               'E a mais formal das cinco, e formal e vizinho de antiquado.'},

    {'letra': 'A3', 'nome': 'O canto cortado',
     'cheio': A3, 'uma': A3U, 'mini': A3M,
     'ideia': 'O canto cortado em diagonal, como nos passaportes ja usados — '
              'um pormenor verdadeiro, que quem viaja reconhece e quem nao '
              'viaja le so como uma forma invulgar. E a unica das cinco com '
              'uma silhueta que nao e um retangulo, e isso e o que a torna '
              'reconhecivel de longe e ao pequeno.',
     'contra': 'Duas leituras mas: no mundo real o canto cortado significa '
               'documento cancelado, e quem souber isso le o contrario do que '
               'queremos dizer. E um canto dobrado com um triangulo de outra '
               'cor e tambem o icone generico de ficheiro, que esta em todos '
               'os sistemas operativos.'},

    {'letra': 'A4', 'nome': 'O sol que transborda',
     'cheio': A4, 'uma': A4U, 'mini': A4M,
     'ideia': 'O sol esta atras da capa, centrado na propria aresta de cima: '
              've-se so a metade que nasce, e e a aresta do passaporte que '
              'faz de horizonte. E a mais economica das cinco — uma peca a '
              'menos do que as outras e a ideia continua inteira — e a unica '
              'em que o documento e a paisagem sao a mesma linha.',
     'contra': 'Um simbolo que sai fora da sua propria caixa obriga a uma '
               'area de respiro maior e a regras de uso mais apertadas. Numa '
               'linha de cabecalho baixa, o sol e a primeira coisa a ser '
               'cortada.'},

    {'letra': 'A5', 'nome': 'A faixa',
     'cheio': A5, 'uma': A5U, 'mini': A5M,
     'ideia': 'Uma faixa larga de cor atravessa a capa, e o sol esta recortado '
              'nela a papel em vez de desenhado por cima. E a que tem mais cor '
              'das cinco e a unica que se le a distancia como um bloco, nao '
              'como um detalhe — num separador de browser cheio, isso conta '
              'mais do que qualquer subtileza.',
     'contra': 'A faixa e tanta cor que a marca passa a ser a faixa. Se um dia '
               'mudares de cor, mudas de marca.'},

    {'letra': 'D1', 'nome': 'O carimbo grande',
     'seccao': 'Familia D — o passaporte aberto',
     'seccao_nota': 'A mesma logica: cinco versoes do aberto, cada uma a '
                    'mudar uma coisa — o tamanho do carimbo, o que esta no '
                    'vinco, o angulo, o numero de carimbos, o que esta na '
                    'pagina.',
     'cheio': D1, 'uma': D1U, 'mini': D1M,
     'ideia': 'O que escolheste, com o carimbo a crescer ate dominar a pagina '
              'da direita. Ao crescer, o carimbo passa a ser a parte que se '
              'reconhece primeiro, e o passaporte passa a ser o contexto — o '
              'que resolve o problema de o aberto ser largo e baixo, porque '
              'passa a haver um centro.',
     'contra': 'Continua a ser largo e baixo, e isso continua a ser mau para '
               'um avatar quadrado.'},

    {'letra': 'D2', 'nome': 'O brasao na pagina',
     'cheio': D2, 'uma': D2U, 'mini': D2M,
     'ideia': 'O brasao da capa, inteiro, impresso na pagina da direita. '
              'E a unica que junta as duas familias: e o aberto do D com o '
              'brasao do A, e isso faz as duas poderem conviver como marca '
              'principal e marca curta da mesma casa, em vez de serem duas '
              'marcas diferentes — o aberto grande, a capa em pequeno, e o sol '
              'a ligar os dois. Tentei primeiro o sol a sair da propria '
              'dobra: o vinco corta-o ao meio e le-se meio disco encostado a '
              'uma barra, nao um sol.',
     'contra': 'Dois desenhos encaixados um no outro: o passaporte da o '
               'contorno, o brasao da o conteudo, e nenhum dos dois manda. Ao '
               'pequeno ha que escolher, e quem escolher o brasao fica com a '
               'capa — ou seja, com o A.'},

    {'letra': 'D3', 'nome': 'Visto de cima',
     'cheio': D3, 'uma': D3U, 'mini': D3M,
     'ideia': 'O mesmo aberto, mas mais baixo e mais largo, como se estivesse '
              'pousado na mesa e visto um pouco de cima. Perde altura e ganha '
              'calma — e a versao que melhor assenta ao lado do nome numa '
              'linha de cabecalho, porque tem a mesma altura que as letras.',
     'contra': 'Achatado, as curvas das paginas quase desaparecem e o desenho '
               'aproxima-se de dois trapezios. E a menos expressiva das '
               'cinco.'},

    {'letra': 'D4', 'nome': 'Dois carimbos',
     'cheio': D4, 'uma': D4U, 'mini': D4M,
     'ideia': 'Um carimbo em cada pagina, de tamanhos diferentes e fora de '
              'eixo. Diz "ja ca estive mais do que uma vez" e da ao desenho '
              'um ritmo que o original nao tinha — e para um marketplace, dois '
              'carimbos leem-se tambem como dois operadores, duas origens.',
     'contra': 'Duas formas iguais em sitios diferentes e o tipo de desenho '
               'que fica desarrumado se nao for afinado ao milimetro. E ao '
               'pequeno so sobra um deles.'},

    {'letra': 'D5', 'nome': 'A paisagem na pagina',
     'cheio': D5, 'uma': D5U, 'mini': D5M,
     'ideia': 'Em vez do carimbo, a pagina da direita traz a paisagem: sol e '
              'serra recortados a papel. E o passaporte aberto a mostrar o '
              'sitio em vez de mostrar a burocracia — a mesma ideia da janela '
              'que te mostrei antes, mas aqui sem o conflito de duas formas, '
              'porque a pagina ja e uma moldura.',
     'contra': 'E a que tem mais pecas pequenas das dez, e a serra recortada a '
               'papel e a primeira a fechar quando o desenho encolhe.'},
]


ABERTURA = '''
<p class="intro">Escolheste <strong>o A, a capa</strong>, e <strong>o D, o
aberto</strong>. Esta ronda nao traz ideias novas: pega nesses dois e tira
cinco versoes a cada um — que e o trabalho que falta fazer depois de uma
escolha e antes de uma decisao.</p>
<p class="intro">Em cada familia muda-se <strong>uma coisa de cada vez</strong>.
Assim da para ver qual e o movimento responsavel pela diferenca, em vez de se
gostar de uma sem se saber porque.</p>
<p class="intro">Esta pagina nao esta no site: e so para decidires.</p>
'''

FECHO = '''
<p class="fim">Como sempre, as tres versoes de cada: a duas cores, a uma cor so
— carimbo, fatura, preto e branco — e reduzida com menos planos, a 48, 32 e
16 px.<br>
Diz-me uma e passo ao trabalho fino: espacejamento optico, area de respiro,
grelha de construcao, e a cor definitiva. Entrego em SVG, PNG e favicon.</p>
'''


def main():
    html = pagina('Sexta ronda: variacoes da capa e do aberto',
                  ABERTURA, PROPOSTAS, FECHO)
    escrever(html, 'logos6')
    print('%d propostas' % len(PROPOSTAS))


if __name__ == '__main__':
    main()
