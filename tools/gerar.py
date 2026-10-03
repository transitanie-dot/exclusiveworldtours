#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o site todo e verifica-o.

Existe porque gerar o site eram onze comandos por ordem certa, e quem
se esquecesse de um publicava uma pagina velha ao lado de uma nova — que
e exatamente o tipo de erro que nao da erro.

    python3 tools/gerar.py

Nao corre no Render: o Render nao executa nada. Corre aqui, o HTML
gerado vai para o Git como qualquer outro ficheiro, e o push e que
publica.
"""

import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))

# Por ordem. A ligacao primeiro, porque as paginas do portal dependem do
# assets/ligacao.js existir; a verificacao no fim, porque verifica o que
# os outros escreveram.
PASSOS = [
    ('a ligacao a base de dados', 'ligacao.py'),
    ('as cidades da procura',     'cidades.py'),
    # home.py e nao home3.py: o home3 e a versao anterior, com a marca
    # indigo de antes de o A5 ser escolhido. Os dois escrevem para
    # index.html, e correr o errado publicava a marca antiga na pagina
    # mais vista do site. Aconteceu-me uma vez esta noite.
    ('a homepage',                'home.py'),
    ('a pagina de resultados',    'resultados.py'),
    ('as paginas de tour',        'tour.py'),
    ('a pagina de operadores',    'fornecedores.py'),
    ('os formularios',            'formularios.py'),
    ('o blog',                    'blog.py'),
    ('a politica',                'paginas_simples.py'),
    ('o portal',                  'portal.py'),
    ('o editor de anuncios',      'portal_anuncio.py'),
    ('o calendario',              'portal_calendario.py'),
    ('a frota',                   'portal_frota.py'),
    ('a conta do operador',       'portal_conta.py'),
    ('a fila de revisao',         'admin.py'),
    ('as listas da administracao', 'admin_listas.py'),
]


def correr(nome, guiao, silencioso=True):
    r = subprocess.run([sys.executable, os.path.join(AQUI, guiao)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print('\nPAROU em %s (%s):\n' % (nome, guiao))
        print(r.stdout)
        print(r.stderr)
        sys.exit(1)
    if not silencioso:
        print(r.stdout.rstrip())
    return r.stdout


def main():
    detalhe = '-v' in sys.argv or '--detalhe' in sys.argv
    print('A gerar o site.\n')
    for nome, guiao in PASSOS:
        saida = correr(nome, guiao, silencioso=not detalhe)
        n = len([x for x in saida.splitlines() if x.startswith('escrito:')])
        if not detalhe:
            print('  %-30s %d ficheiros' % (nome, n))

    print('\nA verificar.\n')
    r = subprocess.run([sys.executable, os.path.join(AQUI, 'verificar.py')],
                       capture_output=True, text=True)
    print(r.stdout.rstrip())
    if r.returncode != 0:
        print(r.stderr)
        sys.exit(1)

    print('\nFalta o que corre no browser (precisa de node):')
    print('  node tools/testar_portal.mjs      o portal, com a base simulada')
    print('  node tools/acessibilidade.mjs     o axe em 3 tamanhos')


if __name__ == '__main__':
    main()
