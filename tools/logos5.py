#!/usr/bin/env python3
"""
Quinta ronda: o passaporte.

Decidido pelo Ricardo. O sistema de desenho e o da ronda anterior, que
ele aceitou — duas cores, sem degrade, volume por planos sobrepostos —
e vem todo de tools/marca_base.py. Aqui so estao os desenhos.

Seis maneiras de fazer um passaporte ser uma marca, porque "passaporte"
sozinho ainda nao e um desenho: um retangulo com cantos redondos e a
coisa mais generica que ha, e a diferenca entre as seis esta toda em
*como* se resolve esse problema.

    python3 tools/logos5.py        # escreve logos5/index.html e logos5.html
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from marca_base import (PALETA, escrever, pagina, svg)  # noqa: E402


# ====================================================================
# A capa e sempre a mesma: 60 x 84, centrada, cantos a 6. Ter a mesma
# forma de base nas seis nao e preguica — e o que permite compara-las
# de verdade, porque a unica coisa que muda e a ideia.
# ====================================================================

CAPA = 'M26 8 h48 a6 6 0 0 1 6 6 v72 a6 6 0 0 1 -6 6 h-48 a6 6 0 0 1 -6 -6 v-72 a6 6 0 0 1 6 -6 Z'
# a lombada: a faixa estreita a esquerda que faz a capa ter espessura
LOMBADA = 'M26 8 h7 v84 h-7 a6 6 0 0 1 -6 -6 v-72 a6 6 0 0 1 6 -6 Z'


# O brasao da capa: o sol a nascer sobre a agua.
#
# A primeira versao era um circulo inteiro com duas barras grossas por
# baixo e lia-se hamburguer — a serio, nao e piada. O que faltava era o
# sol estar *meio enterrado* no horizonte em vez de pousado em cima dele:
# meio disco, a linha de agua a passar-lhe por baixo e mais larga do que
# ele, e as ondas finas. E a mesma correcao que torna a forma legivel ao
# pequeno, porque passa a haver uma silhueta so.

def brasao(cx, cy, r, w, cor_sol='c', cor_linhas='papel'):
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
        'sol': cor_sol, 'lin': cor_linhas,
        'x1': cx - w / 2, 'w': w, 'h': meia, 'hr': meia / 2,
        'x2': cx - w / 2 + w * .10, 'y2': cy + meia * 2.6,
        'w2': w * .56, 'h2': meia * .8, 'hr2': meia * .4,
        'x3': cx - w / 2 + w * .34, 'y3': cy + meia * 4.6, 'w3': w * .40,
    }


# ------------------------------------------------------------ A. a capa
#
# O passaporte como objeto: capa, lombada e o brasao ao meio. O brasao e
# o sol a nascer sobre a agua — a unica coisa que aqui e nossa, porque a
# capa e de toda a gente.

A_CHEIO = svg(
    '<path d="%s" class="p"/>' % CAPA +
    '<path d="%s" class="pf"/>' % LOMBADA +
    # o brasao: o sol a nascer sobre a agua
    brasao(56.5, 48, 14, 38) +
    # as duas linhas de texto da capa
    '<g class="c">'
    '<rect x="43" y="68" width="27" height="3.4" rx="1.7"/>'
    '<rect x="47" y="76" width="19" height="3.4" rx="1.7"/>'
    '</g>',
    rotulo='Capa de passaporte com brasao de sol sobre a agua')

A_UMA = svg(
    '<path d="%s" class="u"/>' % CAPA +
    '<path d="%s" class="u-f"/>' % LOMBADA +
    brasao(56.5, 48, 14, 38, cor_sol='u-f', cor_linhas='papel') +
    '<g class="u-f">'
    '<rect x="43" y="68" width="27" height="3.4" rx="1.7"/>'
    '<rect x="47" y="76" width="19" height="3.4" rx="1.7"/>'
    '</g>',
    rotulo='Capa de passaporte, a uma cor')

A_MINI = svg(
    '<path d="M22 8 h56 a7 7 0 0 1 7 7 v70 a7 7 0 0 1 -7 7 h-56 a7 7 0 0 1 -7 -7'
    ' v-70 a7 7 0 0 1 7 -7 Z" class="p"/>'
    # ao pequeno fica so o meio sol e a linha de agua: dois elementos
    '<path d="M31 56 A19 19 0 0 1 69 56 Z" class="c"/>'
    '<rect x="26" y="56" width="48" height="6" rx="3" class="papel"/>',
    rotulo='Capa de passaporte, versao reduzida')


# ---------------------------------------------------------- B. o carimbo
#
# Nao o passaporte: a marca que ele leva. O carimbo de entrada e a prova
# de que se foi la — e a unica parte do passaporte que e um troféu.

# A primeira versao tinha uma coroa de riscos a toda a volta e saiu uma
# roda dentada, nao um carimbo. Um carimbo de entrada le-se por outra
# coisa: dois aneis concentricos de espessuras diferentes e um campo
# claro no meio com as linhas da data.

B_CHEIO = svg(
    '<circle cx="50" cy="50" r="46" fill="none" stroke-width="3" class="tracos"/>'
    '<circle cx="50" cy="50" r="38" class="c"/>'
    '<circle cx="50" cy="50" r="29" class="papel"/>'
    # duas barras alinhadas a esquerda e de larguras diferentes: assim
    # leem-se como linhas de texto do carimbo. Centradas e iguais liam-se
    # como um sinal de igual, que foi o que me saiu a primeira vez.
    '<g class="p">'
    '<rect x="29" y="40" width="42" height="6" rx="3"/>'
    '<rect x="29" y="53" width="26" height="5" rx="2.5"/>'
    '<circle cx="64" cy="55.5" r="2.5"/>'
    '</g>',
    rotulo='Carimbo de entrada: dois aneis e as linhas da data')

B_UMA = svg(
    '<circle cx="50" cy="50" r="46" fill="none" stroke-width="3" class="tracos"/>'
    '<circle cx="50" cy="50" r="38" class="u-f"/>'
    '<circle cx="50" cy="50" r="29" class="papel"/>'
    '<g class="u">'
    '<rect x="29" y="40" width="42" height="6" rx="3"/>'
    '<rect x="29" y="53" width="26" height="5" rx="2.5"/>'
    '<circle cx="64" cy="55.5" r="2.5"/>'
    '</g>',
    rotulo='Carimbo, a uma cor')

B_MINI = svg(
    '<circle cx="50" cy="50" r="46" class="c"/>'
    '<circle cx="50" cy="50" r="33" class="papel"/>'
    '<rect x="26" y="42" width="48" height="16" rx="8" class="p"/>',
    rotulo='Carimbo, versao reduzida')


# -------------------------------------------------------- C. o carimbado
#
# Os dois juntos, e e a sobreposicao que faz tudo: o carimbo entra pelo
# canto da capa e sai fora dela. E o unico da lista com movimento.

C_CHEIO = svg(
    '<path d="M18 14 h46 a6 6 0 0 1 6 6 v66 a6 6 0 0 1 -6 6 h-46'
    ' a6 6 0 0 1 -6 -6 v-66 a6 6 0 0 1 6 -6 Z" class="p"/>'
    '<path d="M18 14 h7 v78 h-7 a6 6 0 0 1 -6 -6 v-66 a6 6 0 0 1 6 -6 Z" class="pf"/>'
    '<g class="papel">'
    '<rect x="30" y="68" width="28" height="3.4" rx="1.7"/>'
    '<rect x="34" y="76" width="20" height="3.4" rx="1.7"/>'
    '</g>'
    # o carimbo, a cavalo da aresta
    '<circle cx="68" cy="36" r="24" class="c"/>'
    '<circle cx="68" cy="36" r="16" class="papel"/>'
    '<g class="c">'
    '<rect x="56" y="30" width="24" height="5" rx="2.5"/>'
    '<rect x="56" y="39" width="14" height="4" rx="2"/>'
    '</g>',
    rotulo='Passaporte com o carimbo a cavalo da aresta da capa')

C_UMA = svg(
    '<path d="M18 14 h46 a6 6 0 0 1 6 6 v66 a6 6 0 0 1 -6 6 h-46'
    ' a6 6 0 0 1 -6 -6 v-66 a6 6 0 0 1 6 -6 Z" class="u"/>'
    '<g class="papel">'
    '<rect x="30" y="68" width="28" height="3.4" rx="1.7"/>'
    '<rect x="34" y="76" width="20" height="3.4" rx="1.7"/>'
    '</g>'
    '<circle cx="68" cy="36" r="24" class="u"/>'
    '<circle cx="68" cy="36" r="16" class="papel"/>'
    '<g class="u">'
    '<rect x="56" y="30" width="24" height="5" rx="2.5"/>'
    '<rect x="56" y="39" width="14" height="4" rx="2"/>'
    '</g>',
    rotulo='Passaporte carimbado, a uma cor')

C_MINI = svg(
    '<path d="M14 16 h44 a7 7 0 0 1 7 7 v62 a7 7 0 0 1 -7 7 h-44'
    ' a7 7 0 0 1 -7 -7 v-62 a7 7 0 0 1 7 -7 Z" class="p"/>'
    '<circle cx="72" cy="34" r="25" class="c"/>',
    rotulo='Passaporte carimbado, versao reduzida')


# --------------------------------------------------------- D. o aberto
#
# Aberto ao meio, com a pagina da direita ja carimbada. E o passaporte em
# uso, nao o passaporte na gaveta.

D_CHEIO = svg(
    # as duas paginas
    '<path d="M50 20 C38 14, 24 13, 10 16 L10 80 C24 77, 38 78, 50 84 Z" class="pf"/>'
    '<path d="M50 20 C62 14, 76 13, 90 16 L90 80 C76 77, 62 78, 50 84 Z" class="p"/>'
    # a lombada
    '<rect x="47" y="19" width="6" height="66" rx="3" class="p"/>'
    # as linhas na pagina da esquerda
    '<g class="papel">'
    '<rect x="17" y="30" width="24" height="3" rx="1.5"/>'
    '<rect x="17" y="39" width="20" height="3" rx="1.5"/>'
    '<rect x="17" y="48" width="23" height="3" rx="1.5"/>'
    '</g>'
    # o carimbo na pagina da direita
    '<circle cx="70" cy="46" r="16" class="c"/>'
    '<circle cx="70" cy="46" r="9" class="papel"/>',
    rotulo='Passaporte aberto, com carimbo na pagina da direita')

D_UMA = svg(
    '<path d="M50 20 C38 14, 24 13, 10 16 L10 80 C24 77, 38 78, 50 84 Z" class="u-f"/>'
    '<path d="M50 20 C62 14, 76 13, 90 16 L90 80 C76 77, 62 78, 50 84 Z" class="u"/>'
    '<rect x="47" y="19" width="6" height="66" rx="3" class="u"/>'
    '<circle cx="70" cy="46" r="16" class="papel"/>'
    '<circle cx="70" cy="46" r="9" class="u"/>',
    rotulo='Passaporte aberto, a uma cor')

D_MINI = svg(
    '<path d="M50 22 C36 14, 20 13, 6 16 L6 82 C20 79, 36 80, 50 88 Z" class="p"/>'
    '<path d="M50 22 C64 14, 80 13, 94 16 L94 82 C80 79, 64 80, 50 88 Z" class="c"/>',
    rotulo='Passaporte aberto, versao reduzida')


# ----------------------------------------------------------- E. a janela
#
# A capa com uma janela aberta e a paisagem la dentro. O passaporte
# deixa de ser um documento e passa a ser a moldura por onde se ve o sitio
# — que e literalmente o que a empresa vende.

E_CHEIO = svg(
    '<path d="%s" class="p"/>' % CAPA +
    '<path d="%s" class="pf"/>' % LOMBADA +
    # a janela
    '<path d="M39 26 h31 a4 4 0 0 1 4 4 v30 a4 4 0 0 1 -4 4 h-31 Z" class="cf"/>'
    # o sol e a serra, dentro da janela
    '<circle cx="63" cy="38" r="8" class="c"/>'
    '<path d="M39 64 L50 48 L58 57 L68 44 L74 52 L74 60 a4 4 0 0 1 -4 4 Z" class="p"/>'
    # as linhas de texto por baixo
    '<g class="c">'
    '<rect x="39" y="72" width="26" height="3.4" rx="1.7"/>'
    '<rect x="39" y="80" width="16" height="3.4" rx="1.7"/>'
    '</g>',
    rotulo='Capa de passaporte com uma janela aberta para a paisagem')

E_UMA = svg(
    '<path d="%s" class="u"/>' % CAPA +
    '<path d="%s" class="u-f"/>' % LOMBADA +
    '<path d="M39 26 h31 a4 4 0 0 1 4 4 v30 a4 4 0 0 1 -4 4 h-31 Z" class="papel"/>'
    '<circle cx="63" cy="38" r="8" class="u-f"/>'
    '<path d="M39 64 L50 48 L58 57 L68 44 L74 52 L74 60 a4 4 0 0 1 -4 4 Z" class="u"/>'
    '<g class="u-f">'
    '<rect x="39" y="72" width="26" height="3.4" rx="1.7"/>'
    '<rect x="39" y="80" width="16" height="3.4" rx="1.7"/>'
    '</g>',
    rotulo='Capa com janela, a uma cor')

E_MINI = svg(
    '<path d="M22 8 h56 a7 7 0 0 1 7 7 v70 a7 7 0 0 1 -7 7 h-56 a7 7 0 0 1 -7 -7'
    ' v-70 a7 7 0 0 1 7 -7 Z" class="p"/>'
    '<path d="M32 28 h36 a4 4 0 0 1 4 4 v28 h-40 Z" class="c"/>'
    '<path d="M32 60 L46 40 L58 54 L72 36 L72 60 Z" class="p"/>',
    rotulo='Capa com janela, versao reduzida')


# ------------------------------------------------------------- F. o maco
#
# Dois passaportes, um atras do outro. Diz "ja fomos muitas vezes" sem
# dizer nada, e a sobreposicao da a profundidade de borla.

F_CHEIO = svg(
    '<g transform="rotate(-9 50 50)">'
    '<path d="M30 10 h46 a6 6 0 0 1 6 6 v68 a6 6 0 0 1 -6 6 h-46'
    ' a6 6 0 0 1 -6 -6 v-68 a6 6 0 0 1 6 -6 Z" class="c"/>'
    '</g>'
    '<g transform="rotate(5 50 50)">'
    '<path d="M24 12 h46 a6 6 0 0 1 6 6 v68 a6 6 0 0 1 -6 6 h-46'
    ' a6 6 0 0 1 -6 -6 v-68 a6 6 0 0 1 6 -6 Z" class="p"/>'
    '<path d="M24 12 h7 v80 h-7 a6 6 0 0 1 -6 -6 v-68 a6 6 0 0 1 6 -6 Z" class="pf"/>' +
    brasao(53.5, 48, 12, 32) +
    '<g class="c">'
    '<rect x="41" y="68" width="25" height="3.4" rx="1.7"/>'
    '<rect x="45" y="76" width="17" height="3.4" rx="1.7"/>'
    '</g>'
    '</g>',
    rotulo='Dois passaportes, um atras do outro')

F_UMA = svg(
    '<g transform="rotate(-9 50 50)">'
    '<path d="M30 10 h46 a6 6 0 0 1 6 6 v68 a6 6 0 0 1 -6 6 h-46'
    ' a6 6 0 0 1 -6 -6 v-68 a6 6 0 0 1 6 -6 Z" class="u-f"/>'
    '</g>'
    '<g transform="rotate(5 50 50)">'
    '<path d="M24 12 h46 a6 6 0 0 1 6 6 v68 a6 6 0 0 1 -6 6 h-46'
    ' a6 6 0 0 1 -6 -6 v-68 a6 6 0 0 1 6 -6 Z" class="u"/>' +
    brasao(53.5, 48, 12, 32, cor_sol='papel', cor_linhas='u-f') +
    '</g>',
    rotulo='Dois passaportes, a uma cor')

F_MINI = svg(
    '<g transform="rotate(-10 50 50)">'
    '<path d="M28 10 h50 a7 7 0 0 1 7 7 v66 a7 7 0 0 1 -7 7 h-50'
    ' a7 7 0 0 1 -7 -7 v-66 a7 7 0 0 1 7 -7 Z" class="c"/>'
    '</g>'
    '<g transform="rotate(6 50 50)">'
    '<path d="M20 12 h48 a7 7 0 0 1 7 7 v64 a7 7 0 0 1 -7 7 h-48'
    ' a7 7 0 0 1 -7 -7 v-64 a7 7 0 0 1 7 -7 Z" class="p"/>'
    '</g>',
    rotulo='Dois passaportes, versao reduzida')


PROPOSTAS = [
    {'letra': 'A', 'nome': 'A capa',
     'cheio': A_CHEIO, 'uma': A_UMA, 'mini': A_MINI,
     'ideia': 'O passaporte como objeto, com a lombada a dar-lhe espessura e '
              'o brasao ao meio. O brasao e o sol a nascer sobre a agua, '
              'aberto a papel — e a unica parte que e nossa, porque a capa e '
              'de toda a gente. E a mais sobria das seis e a que melhor '
              'aguenta ser gravada em relevo num cartao.',
     'contra': 'E tambem a mais previsivel. Um passaporte desenhado de frente '
               'e o que qualquer pessoa desenharia primeiro, e isso tanto '
               'quer dizer "le-se logo" como "ja vi isto".'},

    {'letra': 'B', 'nome': 'O carimbo',
     'cheio': B_CHEIO, 'uma': B_UMA, 'mini': B_MINI,
     'ideia': 'Nao o passaporte: a marca que ele leva. O carimbo de entrada e '
              'a unica parte do passaporte que e um trofeu — ninguem '
              'fotografa a capa, toda a gente fotografa o carimbo. E redondo, '
              'o que resolve o avatar e o favicon de borla, e os dois aneis '
              'de espessuras diferentes dao-lhe a textura de um carimbo a '
              'serio em vez de um circulo qualquer.',
     'contra': 'Um carimbo redondo com dois aneis tambem e selo de garantia e '
               'de denominacao de origem. Pode ler-se "certificado" em vez de '
               '"viagem", e ai perde a graca toda.'},

    {'letra': 'C', 'nome': 'O carimbado',
     'cheio': C_CHEIO, 'uma': C_UMA, 'mini': C_MINI,
     'ideia': 'Os dois juntos, e e a sobreposicao que faz tudo: o carimbo '
              'entra pelo canto da capa e sai fora dela. E o unico da lista '
              'com movimento — ha uma coisa a acontecer, nao um objeto '
              'pousado. E o circulo a sair do retangulo da-lhe uma silhueta '
              'que se reconhece de longe.',
     'contra': 'Sao duas formas a disputar o mesmo espaco. Ao pequeno uma '
               'delas tem de ceder, e quando o carimbo ganha deixa de se '
               'perceber que ha um passaporte por baixo.'},

    {'letra': 'D', 'nome': 'O aberto',
     'cheio': D_CHEIO, 'uma': D_UMA, 'mini': D_MINI,
     'ideia': 'Aberto ao meio, com as paginas a curvar e a da direita ja '
              'carimbada. E o passaporte em uso e nao o passaporte na gaveta, '
              'e a curva das paginas e a unica linha organica de toda a '
              'ronda — num conjunto de retangulos e circulos, isso faz '
              'diferenca.',
     'contra': 'Aberto, e largo e baixo, e isso e mau para um avatar '
               'quadrado. E a 16 px as duas paginas colam-se e fica um '
               'losango.'},

    {'letra': 'E', 'nome': 'A janela',
     'cheio': E_CHEIO, 'uma': E_UMA, 'mini': E_MINI,
     'ideia': 'A capa com uma janela aberta e a paisagem la dentro. O '
              'passaporte deixa de ser um documento e passa a ser a moldura '
              'por onde se ve o sitio — que e literalmente o que a empresa '
              'vende. E a unica das seis que diz passaporte E diz destino no '
              'mesmo desenho, e e a que liga a serra que ja estavas a ver na '
              'ronda passada.',
     'contra': 'Tem duas ideias dentro de uma. Funciona grande; ao pequeno ha '
               'que decidir qual das duas sobrevive, e a resposta nao e '
               'obvia.'},

    {'letra': 'F', 'nome': 'O maco',
     'cheio': F_CHEIO, 'uma': F_UMA, 'mini': F_MINI,
     'ideia': 'Dois passaportes, um atras do outro, ligeiramente rodados. Diz '
              '"ja fomos muitas vezes" sem escrever nada, e a sobreposicao da '
              'a profundidade de borla. Para um marketplace tem uma leitura '
              'extra que nenhum dos outros tem: nao e um passaporte, sao '
              'varios — varios operadores, varios destinos.',
     'contra': 'Formas rodadas nunca assentam bem numa grelha, e um cabecalho '
               'e uma grelha. E ao pequeno os dois retangulos tornam-se uma '
               'mancha unica.'},
]


ABERTURA = '''
<p class="intro">Decidido: <strong>passaporte</strong>. O sistema de desenho e
o da ronda anterior — duas cores, sem degrade, volume por planos sobrepostos.</p>
<p class="intro">"Passaporte" sozinho ainda nao e um desenho: um retangulo com
cantos redondos e a coisa mais generica que ha. A diferenca entre estas seis
esta toda em <strong>como</strong> se resolve esse problema — o objeto, a marca
que ele leva, os dois juntos, o uso, a moldura, e o numero.</p>
<p class="intro">Cinco das seis partilham a mesma capa de base, com as mesmas
medidas. Isso nao e preguica: e o que permite compara-las de verdade, porque a
unica coisa que muda de uma para a outra e a ideia.</p>
'''

FECHO = '''
<p class="fim">Cada uma aparece a duas cores, a uma cor so — para carimbo,
fatura e preto e branco — e reduzida com menos planos, a 48, 32 e 16 px.<br>
Diz-me uma e afino a mao: proporcoes da capa, peso do brasao, area de respiro,
e a cor certa a serio. Entrego depois em SVG, PNG e favicon, nas tres versoes.</p>
'''


def main():
    html = pagina('Quinta ronda: o passaporte', ABERTURA, PROPOSTAS, FECHO)
    escrever(html, 'logos5')
    print('%d propostas' % len(PROPOSTAS))


if __name__ == '__main__':
    main()
