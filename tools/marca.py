#!/usr/bin/env python3
"""
A marca da Exclusive World Tours.

Escolhida pelo Ricardo a 2 de outubro de 2026: a proposta A5, "a faixa"
— a capa de um passaporte atravessada por uma faixa larga de cor, com o
sol recortado nela a papel.

Este ficheiro e a fonte unica do desenho. Quem precisar da marca —
homepage, paginas de tour, favicon, email, o que vier — importa daqui e
nao volta a desenhar nada. Um logotipo copiado para tres sitios e um
logotipo que daqui a um ano esta diferente em tres sitios.

Tres versoes, porque uma marca tem de aguentar as tres:

  marca()        a duas cores, para tudo o que e normal;
  marca_uma()    a uma cor so, para carimbo, fatura e preto e branco;
  marca_mini()   com menos planos, para 32 px e abaixo (favicon, avatar).

E dois encaixes:

  lockup()       o simbolo com o nome ao lado, que e o cabecalho;
  lockup_v()     o simbolo com o nome por baixo, para quadrados.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from marca_base import PALETA, misturar  # noqa: E402,F401

# A capa: 60 x 84 dentro de um quadrado de 100, cantos a 6.
CAPA = ('M26 8 h48 a6 6 0 0 1 6 6 v72 a6 6 0 0 1 -6 6 h-48 '
        'a6 6 0 0 1 -6 -6 v-72 a6 6 0 0 1 6 -6 Z')
LOMBADA = 'M26 8 h7 v84 h-7 a6 6 0 0 1 -6 -6 v-72 a6 6 0 0 1 6 -6 Z'


def _brasao(cx, cy, r, w, sol, linhas):
    """O sol meio enterrado no horizonte, com a linha de agua mais larga
    do que ele e duas ondas finas por baixo.

    O sol tem de estar enterrado e nao pousado em cima das barras:
    pousado, isto le-se hamburguer. Nao e piada — foi o que me saiu a
    primeira vez e so se ve depois de desenhado."""
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


def _svg(dentro, rotulo, classe='sim'):
    return ('<svg viewBox="0 0 100 100" class="%s" role="img" aria-label="%s">'
            '%s</svg>' % (classe, rotulo, dentro))


ROTULO = 'Exclusive World Tours'


def marca():
    """A duas cores."""
    return _svg(
        '<path d="%s" class="p"/>' % CAPA +
        '<path d="%s" class="pf"/>' % LOMBADA +
        '<rect x="20" y="36" width="60" height="30" class="c"/>' +
        _brasao(56.5, 54, 12, 32, sol='papel', linhas='p') +
        '<g class="c">'
        '<rect x="43" y="74" width="27" height="3.4" rx="1.7"/>'
        '<rect x="47" y="82" width="19" height="3.4" rx="1.7"/>'
        '</g>', ROTULO)


def marca_uma():
    """A uma cor so. Nao e a de duas com a cor apagada: a faixa passa a
    tinta fraca e o sol continua a ser o unico vazio, senao a marca
    fecha-se numa mancha."""
    return _svg(
        '<path d="%s" class="u"/>' % CAPA +
        '<path d="%s" class="u-f"/>' % LOMBADA +
        '<rect x="20" y="36" width="60" height="30" class="u-f"/>' +
        _brasao(56.5, 54, 12, 32, sol='papel', linhas='u') +
        '<g class="u-f">'
        '<rect x="43" y="74" width="27" height="3.4" rx="1.7"/>'
        '<rect x="47" y="82" width="19" height="3.4" rx="1.7"/>'
        '</g>', ROTULO)


def marca_mini():
    """Para 32 px e abaixo. A lombada, as ondas e as linhas de texto
    desaparecem — a essa escala sao sujidade. Fica a capa, a faixa e o
    sol, que e o que ainda se le."""
    return _svg(
        '<path d="M22 8 h56 a7 7 0 0 1 7 7 v70 a7 7 0 0 1 -7 7 h-56 '
        'a7 7 0 0 1 -7 -7 v-70 a7 7 0 0 1 7 -7 Z" class="p"/>'
        '<rect x="15" y="34" width="70" height="32" class="c"/>'
        '<path d="M30 60 A20 20 0 0 1 70 60 Z" class="papel"/>', ROTULO)


# ------------------------------------------------------------- encaixes

def lockup(tamanho, classe='marca', mini=False, titulo=False):
    """O simbolo com o nome ao lado. `tamanho` e a altura do simbolo em
    px; tudo o resto escala a partir dela, por isso ha um numero so a
    mudar entre o cabecalho e o rodape.

    `titulo=True` poe o nome num <h1>, para a homepage, onde a marca
    e mesmo o titulo da pagina. Em todo o lado o nome e texto a serio e
    nao um desenho: le-se, procura-se, copia-se, e um leitor de ecra
    anuncia-o."""
    nome = ('<span class="marca-nome">'
            '<span class="marca-l1">Exclusive</span>'
            '<span class="marca-l2">World Tours</span></span>')
    if titulo:
        nome = '<h1 class="marca-nome marca-nome-h1">%s</h1>' % (
            '<span class="marca-l1">Exclusive</span>'
            '<span class="marca-l2">World Tours</span>')
    return ('<span class="%s" style="--t:%gpx">%s%s</span>'
            % (classe, tamanho, marca_mini() if mini else marca(), nome))


# O CSS da marca. Vai junto com o desenho de proposito: as proporcoes
# fazem parte do logotipo tanto como as formas.
CSS = '''
.marca{font-size:var(--t);line-height:1;display:inline-flex;align-items:center;
  gap:.6em;text-decoration:none}
.marca .sim{width:1em;height:1em;flex:none;display:block}
.marca-nome{display:inline-flex;flex-direction:column;align-items:flex-start;
  font-family:var(--tipo-titulo);font-weight:600;text-transform:uppercase;
  color:var(--tinta);line-height:1;white-space:nowrap;margin:0}
.marca-nome-h1{font-size:inherit}
.marca-l1{font-size:.268em;letter-spacing:.075em;margin-right:-.075em}
.marca-l2{font-size:.268em;letter-spacing:.2165em;margin-right:-.2165em;
  margin-top:.19em}
/* os planos: nenhum gradiente, so cores cheias que tapam o que esta atras */
.sim .papel{fill:var(--papel)}
.sim .p{fill:var(--tinta)}
.sim .pf{fill:var(--tinta-f)}
.sim .c{fill:var(--cor)}
.sim .u{fill:var(--tinta)}
.sim .u-f{fill:var(--uma-f)}
'''
