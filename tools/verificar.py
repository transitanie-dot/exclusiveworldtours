#!/usr/bin/env python3
"""
Verificacoes que correm sobre as paginas ja geradas.

Existe por uma razao concreta: tres vezes seguidas uma regra de CSS
ficou so na homepage e a pagina de resultados saiu partida — o botao sem
estilo, os cartoes como texto corrido. Sao erros que nao rebentam nada,
nao dao erro nenhum, e so se veem a olho. Por isso passam a ser
verificados por uma maquina.

    python3 tools/verificar.py
"""

import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

import glob

PAGINAS = (['index.html', 'tours/index.html', 'search/index.html']
           + sorted(os.path.relpath(x, RAIZ)
                    for x in glob.glob(os.path.join(RAIZ, 'tours', '*',
                                                    'index.html'))))

# Classes que aparecem no HTML e tem mesmo de ter regra no CSS da propria
# pagina. Nao e a lista toda: sao as que ja falharam ou que, se
# faltarem, estragam a pagina sem dar erro.
EXIGIDAS = ['botao', 'tour', 'tours', 'painel', 'paragem', 'galeria', 'tour-foto', 'tour-corpo', 'tour-preco',
            'etiq', 'marca', 'topo', 'rodape', 'folha', 'pc-caixa', 'pc-lista']


def classes_usadas(html):
    usadas = set()
    for m in re.finditer(r'class="([^"]+)"', html):
        usadas.update(m.group(1).split())
    return usadas


def main():
    falhas = []
    for nome in PAGINAS:
        caminho = os.path.join(RAIZ, nome)
        if not os.path.exists(caminho):
            falhas.append('%s: nao existe' % nome)
            continue
        html = open(caminho).read()
        css = '\n'.join(re.findall(r'<style>(.*?)</style>', html, re.S))
        usadas = classes_usadas(html)
        for c in EXIGIDAS:
            if c in usadas and ('.%s{' % c) not in css.replace(' ', '') \
                    and ('.%s ' % c) not in css and ('.%s,' % c) not in css \
                    and ('.%s:' % c) not in css and ('.%s[' % c) not in css:
                falhas.append('%s: usa .%s e nao tem regra para ela' % (nome, c))
        # o preco nunca pode sair com uma casa decimal so
        for m in re.finditer(r'&euro;([0-9 ,]+\.[0-9])(?![0-9])', html):
            falhas.append('%s: preco com uma casa decimal: %s' % (nome, m.group(0)))
        # noindex ligado ate os precos estarem confirmados
        if 'noindex' not in html:
            falhas.append('%s: sem noindex (os precos ainda nao foram '
                          'confirmados pelo Ricardo)' % nome)

    if falhas:
        print('FALHOU:')
        for f in falhas:
            print('  ' + f)
        sys.exit(1)
    print('ok: %d paginas verificadas' % len(PAGINAS))


if __name__ == '__main__':
    main()
