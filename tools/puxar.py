#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Puxa da base os tours dos operadores e escreve tools/tours-operadores.json.

E a peca que faltava para o circuito fechar. Ate aqui um operador
submetia, era aprovado, e o tour dele nao aparecia em lado nenhum:
nenhum gerador lia da base. O portal e a fila de revisao eram teatro.

    python3 tools/puxar.py          # puxa e escreve
    python3 tools/puxar.py --ver    # so diz o que mudaria

DOIS FICHEIROS, E NAO UM
---------------------------------------------------------------------
tools/tours.json              o catalogo escrito a mao. Nao se toca.
tools/tours-operadores.json   o que veio da base. Gerado, substituido
                              inteiro em cada corrida.

Sao dois de proposito. Se fossem um, uma corrida deste guiao podia
apagar conteudo escrito a mao por causa de um erro de rede ou de uma
linha mal formada — e isso descobria-se tarde. Assim o pior que uma
corrida pode fazer e esvaziar o ficheiro que ela propria escreve, e o
`git diff` mostra exatamente o que os operadores mudaram.

SEM CHAVE DE SERVICO
---------------------------------------------------------------------
Tudo o que isto le vai acabar numa pagina publica, por isso corre com a
chave PUBLICAVEL, como o resto do site. A chave de servico — a que
ignora o RLS — continua a nao existir em lado nenhum deste repositorio.

O que a base devolve passa por `limpar()` antes de ser escrito: o
conteudo foi escrito por um operador, e um gerador que confia em texto
de fora e um gerador que publica o que lhe mandarem.
"""

import json
import os
import sys
import urllib.error
import urllib.request

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import ligacao  # noqa: E402

DESTINO = os.path.join(AQUI, 'tours-operadores.json')

# O maximo que aceitamos de cada campo. Nao e paranoia: um titulo de
# 4.000 caracteres nao da erro nenhum, faz uma pagina feia e um <title>
# que o Google corta a meio.
LIMITES = {
    'title': 140, 'slug': 70, 'kicker': 90, 'lede': 700,
    'city': 80, 'countryName': 80, 'country': 80,
    'ticketTo': 120, 'metaDesc': 170,
    'stopsIntro': 500, 'includedIntro': 200,
    'notIncluded': 900, 'practical': 1200,
}


def pedir(funcao):
    """Chama uma funcao da base pela API REST."""
    url = '%s/rest/v1/rpc/%s' % (ligacao.URL, funcao)
    pedido = urllib.request.Request(
        url, data=b'{}', method='POST',
        headers={'apikey': ligacao.CHAVE_PUBLICA,
                 'Authorization': 'Bearer ' + ligacao.CHAVE_PUBLICA,
                 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(pedido, timeout=30) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        sys.exit('A base respondeu %s a %s:\n%s'
                 % (e.code, funcao, e.read().decode('utf-8', 'replace')[:400]))
    except urllib.error.URLError as e:
        sys.exit('Nao consegui falar com a base (%s).\n'
                 'Se estas num container sem saida para a internet, isto '
                 'so corre na maquina do Ricardo.' % e.reason)


def texto(v, limite):
    if v is None:
        return ''
    return str(v).replace('\x00', '').strip()[:limite]


def limpar(linha):
    """Da linha da base para a forma que os geradores leem.

    O conteudo foi escrito por um operador. Aqui corta-se ao tamanho,
    descartam-se os campos que nao reconhecemos, e garante-se que o que
    sai tem exatamente a forma de uma entrada do tours.json — porque e
    isso que os geradores esperam e nao sabem verificar.
    """
    p = linha.get('payload') or {}
    if not isinstance(p, dict):
        return None

    slug = texto(p.get('slug') or linha.get('slug'), LIMITES['slug'])
    titulo = texto(p.get('title'), LIMITES['title'])
    if not slug or not titulo:
        return None

    d = (p.get('durations') or [{}])[0]
    if not isinstance(d, dict):
        d = {}

    escaloes = []
    for x in (d.get('tiers') or []):
        if not isinstance(x, dict):
            continue
        try:
            maximo = int(x.get('max'))
            preco = float(x.get('price'))
        except (TypeError, ValueError):
            continue
        if maximo < 1 or maximo > 199 or preco < 0:
            continue
        e = {'max': maximo, 'price': preco}
        if x.get('vehicle'):
            e['vehicle'] = texto(x['vehicle'], 80)
        try:
            minimo = int(x.get('min'))
            if 1 < minimo <= maximo:
                e['min'] = minimo
        except (TypeError, ValueError):
            pass
        escaloes.append(e)
    escaloes.sort(key=lambda x: x['max'])

    if not escaloes:
        # Um tour sem um unico escalao de preco nao tem nada para mostrar
        # numa pagina de precos. Nao se publica meio tour.
        return None

    # As horas vem da tabela `listing_times` e nao do payload: sao
    # disponibilidade, nao conteudo, e por isso nao passam pela revisao.
    horas = [str(h)[:5] for h in (linha.get('start_times') or [])]

    def lista(chave, limite, maximo_itens):
        return [texto(x, limite) for x in (p.get(chave) or [])
                if texto(x, limite)][:maximo_itens]

    paragens = []
    for x in (p.get('stops') or [])[:40]:
        if not isinstance(x, dict) or not texto(x.get('h'), 140):
            continue
        paragens.append({'when': texto(x.get('when'), 12),
                         'h': texto(x.get('h'), 140),
                         'p': texto(x.get('p'), 900)})

    faq = []
    for x in (p.get('faq') or [])[:30]:
        if isinstance(x, (list, tuple)) and len(x) == 2 and texto(x[0], 220):
            faq.append([texto(x[0], 220), texto(x[1], 1200)])

    # `practical` sao pares rotulo/texto e nao um paragrafo: o gerador
    # desenha-os numa tabela. Uma string vinda de uma versao antiga do
    # editor nao se descarta — embrulha-se, que e o que um leitor
    # esperaria de qualquer maneira.
    pratico = []
    bruto = p.get('practical')
    if isinstance(bruto, str) and bruto.strip():
        pratico = [['Good to know', texto(bruto, LIMITES['practical'])]]
    else:
        for x in (bruto or [])[:12]:
            if isinstance(x, (list, tuple)) and len(x) == 2 and texto(x[0], 60):
                pratico.append([texto(x[0], 60), texto(x[1], 600)])

    fotos = []
    for x in (p.get('photos') or [])[:12]:
        if not isinstance(x, dict):
            continue
        url = texto(x.get('url') or x.get('id'), 500)
        # So https. Uma fotografia por http numa pagina https nao
        # aparece, e o browser diz porque numa consola que ninguem le.
        if x.get('url') and not url.startswith('https://'):
            continue
        if url:
            fotos.append({'id' if x.get('id') and not x.get('url') else 'url': url,
                          'alt': texto(x.get('alt'), 200),
                          'by': texto(x.get('by'), 120)})

    # O ponto de encontro. Sem ele, a recolha e no hotel — que e o normal
    # num dia privado e nao uma falta.
    encontro = None
    mp = linha.get('meeting_point')
    if isinstance(mp, dict) and texto(mp.get('name'), 120):
        foto = texto(mp.get('photo_url'), 500)
        encontro = {
            'name': texto(mp.get('name'), 120),
            'address': texto(mp.get('address'), 250),
            'instructions': texto(mp.get('instructions'), 600),
            'photo': foto if foto.startswith('https://') else '',
        }
        try:
            lat, lng = float(mp['lat']), float(mp['lng'])
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                encontro['lat'], encontro['lng'] = lat, lng
        except (TypeError, ValueError, KeyError):
            pass

    return {
        'slug': slug,
        'title': titulo,
        'country': texto(p.get('country') or linha.get('country'), 80).lower().replace(' ', '-'),
        'countryName': texto(p.get('countryName') or linha.get('country'), LIMITES['countryName']),
        'city': texto(p.get('city') or linha.get('city'), LIMITES['city']),
        'kicker': texto(p.get('kicker'), LIMITES['kicker']),
        'lede': texto(p.get('lede'), LIMITES['lede']),
        'metaDesc': texto(p.get('metaDesc'), LIMITES['metaDesc']) or texto(p.get('lede'), 160),
        'ticketTo': texto(p.get('ticketTo'), LIMITES['ticketTo']),
        'durations': [{
            'h': texto(d.get('h'), 30),
            'price': min(x['price'] for x in escaloes),
            'tiers': escaloes,
            'startTimes': horas or [texto(h, 12) for h in (d.get('startTimes') or [])][:12],
        }],
        'stopsIntro': texto(p.get('stopsIntro'), LIMITES['stopsIntro']),
        'stops': paragens,
        'includedIntro': texto(p.get('includedIntro'), LIMITES['includedIntro']),
        'included': lista('included', 220, 20),
        'notIncluded': texto(p.get('notIncluded'), LIMITES['notIncluded']),
        'practical': pratico,
        'faq': faq,
        'photos': fotos,
        # O que nao e conteudo, e vem das colunas da base.
        '_operador': texto(linha.get('operator_name'), 200),
        '_versao': linha.get('version'),
        '_aviso_horas': linha.get('lead_time_hours'),
        '_fuso': texto(linha.get('timezone'), 60),
        '_max_pax': linha.get('max_pax'),
        '_veiculos': linha.get('vehicles'),
        '_encontro': encontro,
    }


def main():
    so_ver = '--ver' in sys.argv

    linhas = pedir('catalogo_publico')

    # Os pontos de encontro vem a parte porque o catalogo_publico() nao
    # pode ganhar colunas sem um `drop` — ver a nota em
    # sql/012_pontos_de_encontro.sql. Uma chamada, nao uma por tour.
    pontos = {}
    for x in (pedir('pontos_de_encontro') or []):
        if isinstance(x, dict) and x.get('slug'):
            pontos[x['slug']] = x
    if not isinstance(linhas, list):
        sys.exit('A base devolveu uma coisa que nao e uma lista: %r'
                 % (str(linhas)[:200],))

    tours, descartados = [], []
    for linha in linhas:
        linha['meeting_point'] = pontos.get(linha.get('slug'))
        limpo = limpar(linha)
        (tours if limpo else descartados).append(limpo or linha.get('slug'))

    # Dois operadores nao podem ter o mesmo endereco web. A base ja impede
    # (o slug e unico em `listings`), mas um slug do payload pode colidir
    # com um dos tours escritos a mao — e esses a base nao conhece.
    mao = set()
    caminho_mao = os.path.join(AQUI, 'tours.json')
    if os.path.exists(caminho_mao):
        mao = {t['slug'] for t in json.load(open(caminho_mao))['tours']}

    chocam = [t['slug'] for t in tours if t['slug'] in mao]
    if chocam:
        tours = [t for t in tours if t['slug'] not in mao]

    saida = {
        '_nota': ('Gerado por tools/puxar.py a partir de catalogo_publico(). '
                  'Nao editar a mao: a proxima corrida substitui o ficheiro '
                  'inteiro. O catalogo escrito a mao vive em tours.json.'),
        'tours': sorted(tours, key=lambda t: t['slug']),
    }

    print('%d tours no catalogo da base' % len(linhas))
    if descartados:
        print('  %d descartados por nao terem titulo, endereco ou preco: %s'
              % (len(descartados), ', '.join(str(x) for x in descartados[:5])))
    if chocam:
        print('  %d com o endereco ja usado por um tour escrito a mao, NAO '
              'publicados: %s' % (len(chocam), ', '.join(chocam)))
        print('  (resolve-se mudando o slug no portal do operador)')

    if so_ver:
        antigo = (json.load(open(DESTINO))['tours']
                  if os.path.exists(DESTINO) else [])
        a = {t['slug'] for t in antigo}
        b = {t['slug'] for t in saida['tours']}
        print('\nentram: %s' % (', '.join(sorted(b - a)) or '—'))
        print('saem:   %s' % (', '.join(sorted(a - b)) or '—'))
        print('ficam:  %d' % len(a & b))
        return

    with open(DESTINO, 'w') as f:
        json.dump(saida, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('escrito: tools/tours-operadores.json (%d tours)' % len(saida['tours']))
    if saida['tours']:
        print('\nAgora gera o site:  python3 tools/gerar.py')


if __name__ == '__main__':
    main()
