#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""O limpar() do puxar.py, posto a prova.

O conteudo que passa por aqui foi escrito por um operador. O que esta em
teste nao e o caminho feliz — e o que acontece quando alguem escreve um
titulo de quatro mil caracteres, um preco negativo, uma fotografia por
http, ou uma etiqueta <script> no meio da descricao.

    python3 tools/testar_puxar.py
"""

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pagina  # noqa: E402
import puxar  # noqa: E402

falhas = []


def igual(nome, obtido, esperado):
    if obtido != esperado:
        falhas.append('%s\n    esperava: %r\n    obteve:   %r'
                      % (nome, esperado, obtido))
    else:
        print('  ok      %s' % nome)


def verdade(nome, condicao, porque=''):
    if not condicao:
        falhas.append('%s%s' % (nome, ('\n    ' + porque) if porque else ''))
    else:
        print('  ok      %s' % nome)


def linha(**campos):
    """Uma linha como catalogo_publico() a devolve."""
    base = {
        'slug': 'um-tour', 'city': 'Dublin', 'country': 'Ireland',
        'operator_id': 'aaaa', 'operator_name': 'Ana Tours',
        'version': 3, 'reviewed_at': '2026-10-01T10:00:00Z',
        'lead_time_hours': 48, 'timezone': 'Europe/Dublin',
        'start_times': ['08:00:00', '14:30:00'],
        'max_pax': 6, 'vehicles': 2,
        'payload': {
            'slug': 'um-tour', 'title': 'Private Day in Wicklow',
            'lede': 'Um dia.', 'city': 'Dublin', 'countryName': 'Ireland',
            'durations': [{'h': '8h', 'tiers': [
                {'max': 3, 'vehicle': 'Sedan', 'price': 390},
                {'max': 6, 'vehicle': 'Minivan', 'price': 490}]}],
            'included': ['Vehicle', 'Driver'],
            'stops': [{'when': '08:00', 'h': 'Hotel', 'p': 'Collection.'}],
            'faq': [['Group size?', 'By vehicle.']],
            'photos': [{'url': 'https://exemplo.invalid/a.jpg',
                        'alt': 'A paisagem', 'by': 'Alguem'}],
        },
    }
    base.update(campos)
    return base


print('\nO QUE SAI DA BASE, LIMPO\n')

# ------------------------------------------------------------ o caminho feliz
t = puxar.limpar(linha())
verdade('um tour completo passa', t is not None)
igual('o preco e o mais baixo dos escaloes', t['durations'][0]['price'], 390)
igual('os escaloes vem por tamanho',
      [x['max'] for x in t['durations'][0]['tiers']], [3, 6])
igual('as horas vem da tabela e nao do payload',
      t['durations'][0]['startTimes'], ['08:00', '14:30'])
igual('o operador viaja com o tour', t['_operador'], 'Ana Tours')
igual('o pais fica em minusculas, para o filtro', t['country'], 'ireland')
igual('sem metaDesc, usa-se a lede', t['metaDesc'], 'Um dia.')

# --------------------------------------------------------- o que tem de cair
verdade('um tour sem titulo cai',
        puxar.limpar(linha(payload={'slug': 'x'})) is None)
verdade('um tour sem endereco cai',
        puxar.limpar(linha(payload={'title': 'Sem slug'})) is None)

sem_preco = linha()
sem_preco['payload']['durations'] = [{'h': '8h', 'tiers': []}]
verdade('um tour sem um unico escalao de preco cai',
        puxar.limpar(sem_preco) is None,
        'meio tour numa pagina de precos e pior do que tour nenhum')

mau = linha()
mau['payload']['durations'] = [{'h': '8h', 'tiers': [
    {'max': 4, 'price': -100},          # preco negativo
    {'max': 0, 'price': 50},            # zero pessoas
    {'max': 500, 'price': 50},          # um autocarro inteiro
    {'max': 'seis', 'price': 'muito'},  # texto onde devia haver numeros
    {'max': 4, 'price': 390},           # este e o unico bom
]}]
t = puxar.limpar(mau)
igual('escaloes absurdos sao descartados um a um',
      [x['max'] for x in t['durations'][0]['tiers']], [4])
igual('e o preco sai do que sobrou', t['durations'][0]['price'], 390)

# ------------------------------------------------------------- o tamanho
grande = linha()
grande['payload']['title'] = 'A' * 4000
grande['payload']['lede'] = 'B' * 5000
t = puxar.limpar(grande)
igual('um titulo gigante e cortado', len(t['title']), 140)
igual('e a lede tambem', len(t['lede']), 700)
verdade('e as listas tambem tem limite',
        len(puxar.limpar(linha(payload=dict(
            linha()['payload'], included=['x'] * 500)))['included']) == 20)

# ---------------------------------------------------------- as fotografias
fotos = linha()
fotos['payload']['photos'] = [
    {'url': 'http://exemplo.invalid/insegura.jpg', 'alt': 'a'},
    {'url': 'https://exemplo.invalid/boa.jpg', 'alt': 'b'},
    {'url': 'javascript:alert(1)', 'alt': 'c'},
]
t = puxar.limpar(fotos)
igual('so passam fotografias por https', len(t['photos']), 1)
igual('e e a certa', t['photos'][0]['url'], 'https://exemplo.invalid/boa.jpg')

# ------------------------------------------------------------- o escape
#
# O limpar() nao escapa HTML, de proposito: quem escapa e o e() dos
# geradores, no momento de escrever a pagina. Escapar aqui dava texto
# escapado duas vezes. O que se verifica e que o texto chega inteiro e
# que a pagina o escapa.
hostil = linha()
hostil['payload']['title'] = 'Tour <script>alert("x")</script> privado'
t = puxar.limpar(hostil)
verdade('o texto hostil chega intacto ao gerador', '<script>' in t['title'])
verdade('e e o gerador que o neutraliza',
        '&lt;script&gt;' in pagina.e(t['title']),
        'se isto falhar, uma etiqueta de um operador entra numa pagina')

# --------------------------------------------------------- o zero byte
nulo = linha()
nulo['payload']['title'] = 'Antes\x00Depois'
igual('um byte nulo e retirado', puxar.limpar(nulo)['title'], 'AntesDepois')

# ------------------------------------------------------ a forma final
t = puxar.limpar(linha())
preciso = ['slug', 'title', 'country', 'countryName', 'city', 'durations',
           'stops', 'included', 'faq', 'photos', 'metaDesc']
faltam = [c for c in preciso if c not in t]
verdade('tem a forma que os geradores esperam', not faltam,
        'faltam: %s' % faltam)
verdade('e os campos operacionais vem marcados com _',
        all(k.startswith('_') for k in t
            if k in ('_operador', '_versao', '_aviso_horas', '_fuso')))

# O teste que conta: os geradores conseguem mesmo usar isto?
d = t['durations'][0]
t['_h'] = d['h']
t['_tiers'] = d['tiers']
t['_preco'] = min(x['price'] for x in d['tiers'])
t['_max'] = max(x['max'] for x in d['tiers'])
t['_menor'] = min(d['tiers'], key=lambda x: x['price'])
t['_partida'] = (d.get('startTimes') or [None])[0]
t['_foto'] = (t.get('photos') or [None])[0]
try:
    cartao = pagina.cartao_tour(t)
    verdade('o cartao do tour desenha-se com estes dados',
            'Wicklow' in cartao and '390' in cartao)
except Exception as e:
    falhas.append('o cartao do tour rebentou: %s' % e)

print()
if falhas:
    print('FALHOU:')
    for f in falhas:
        print('  ' + f)
    sys.exit(1)
print('tudo passou\n')
