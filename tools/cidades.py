#!/usr/bin/env python3
"""
O indice da barra de procura: as cidades onde o Airportlink esta, mais
os tours que ja existem.

Porque nao uma API
------------------
Este site e servido estaticamente com a raiz toda publica. Uma chave de
API de autocompletar (Google Places, Mapbox, Algolia) teria de ir no
HTML ou num ficheiro ao lado, e qualquer pessoa a ve com Ctrl+U. Alem
disso custa por pedido, falha quando o servico falha, e cada letra
escrita por um visitante e uma viagem a rede. Com 408 cidades e 36
tours, o indice inteiro e mais pequeno do que uma fotografia.

O que entra
-----------
1. As cidades dos 408 aeroportos onde o Airportlink opera
   (tools/aeroportos.csv, dado pelo Ricardo). Cidades com mais do que um
   aeroporto — Londres tem quatro, Roma dois — ficam numa linha so, com
   os codigos todos.
2. As cidades de onde parte um tour, mesmo que nao tenham aeroporto
   nenhum na lista: Sorrento, Taormina, Algarve.
3. Os 36 tours, para a procura encontrar "cliffs" e nao so "Dublin".

Cada cidade leva **apelidos** para procura: os codigos IATA e os nomes
dos aeroportos. Quem escreve "LHR" ou "Heathrow" chega a Londres, e quem
escreve "Fiumicino" chega a Roma. E o mesmo que a GetYourGuide faz ao
indexar aliases num campo procuravel.

O `tier` do CSV serve de popularidade: e o desempate entre resultados
igualmente bons, nunca o criterio principal.

    python3 tools/cidades.py        # escreve assets/procura.json
"""

import csv
import io
import json
import os
import sys
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)


def sem_acentos(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn').lower()


def main():
    # ---- os 408 aeroportos
    raw = open(os.path.join(AQUI, 'aeroportos.csv'), 'rb').read()
    linhas = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    linhas = [x for x in linhas if (x.get('IATA') or '').strip()]
    if not linhas:
        sys.exit('aeroportos.csv vazio ou com cabecalho diferente.')

    cidades = {}
    for a in linhas:
        chave = (a['Cidade'].strip(), a['País'].strip())
        c = cidades.setdefault(chave, {
            'nome': chave[0], 'pais': chave[1],
            'continente': a['Continente'].strip(),
            'iata': [], 'aeroportos': [], 'tier': 9, 'tours': 0,
        })
        c['iata'].append(a['IATA'].strip())
        c['aeroportos'].append(a['Aeroporto'].strip())
        try:
            c['tier'] = min(c['tier'], int(a['Tier']))
        except (TypeError, ValueError):
            pass

    # ---- os tours
    tours = json.load(open(os.path.join(AQUI, 'tours.json')))['tours']
    atlas = json.load(open(os.path.join(RAIZ, 'assets',
                                        'atlas.json')))['cidades']

    por_nome = {}
    for (nome, pais), c in cidades.items():
        por_nome.setdefault(nome, []).append(c)

    lista_tours = []
    for t in tours:
        d = t['durations'][0]
        preco = min(x['price'] for x in d['tiers'])
        lista_tours.append({
            'slug': t['slug'], 'titulo': t['title'].replace('Private Tour: ', ''),
            'cidade': t['city'], 'pais': t['countryName'],
            'h': d['h'],
            # ja formatado: 159.9 tem de aparecer como 159.90, e quem
            # formata e quem sabe o que o numero e — nao o browser
            'preco': ('%d' % preco) if float(preco).is_integer()
                     else ('%.2f' % preco),
        })
        # a cidade de partida conta um tour; se nao estiver nos 408,
        # entra na mesma, porque e um sitio onde vendemos mesmo
        achadas = por_nome.get(t['city'])
        if achadas:
            achadas[0]['tours'] += 1
        else:
            chave = (t['city'], t['countryName'])
            c = cidades.setdefault(chave, {
                'nome': t['city'], 'pais': t['countryName'],
                'continente': 'Europe', 'iata': [], 'aeroportos': [],
                'tier': 2, 'tours': 0,
            })
            c['tours'] += 1
            por_nome.setdefault(t['city'], []).append(c)

    # ---- coordenadas, onde as houver. Servem o mapa, nao a procura.
    try:
        import geonamescache
        gc = geonamescache.GeonamesCache()
        todas = list(gc.get_cities().values())
        iso = {p['name']: p['iso'] for p in gc.get_countries().values()}
    except Exception:
        todas, iso = [], {}

    def coords(c):
        a = atlas.get(c['nome'])
        if a:
            return round(a['lat'], 4), round(a['lon'], 4)
        cod = iso.get(c['pais'])
        if not cod:
            return None
        achadas = [x for x in todas if x['countrycode'] == cod and
                   (x['name'] == c['nome'] or
                    c['nome'] in (x.get('alternatenames') or []))]
        if not achadas:
            return None
        x = max(achadas, key=lambda y: y['population'])
        return round(x['latitude'], 4), round(x['longitude'], 4)

    saida_cidades = []
    sem_coord = 0
    for c in sorted(cidades.values(), key=lambda x: (x['tier'], x['nome'])):
        xy = coords(c)
        if xy is None:
            sem_coord += 1
        # apelidos: os codigos e os nomes dos aeroportos, sem repetir o
        # nome da cidade (que ja e procurado por si)
        apelidos = list(dict.fromkeys(
            c['iata'] + [a.replace(' Airport', '').replace(' International', '')
                         for a in c['aeroportos']]))
        apelidos = [a for a in apelidos
                    if sem_acentos(a) != sem_acentos(c['nome'])]
        saida_cidades.append({
            'n': c['nome'], 'p': c['pais'], 'c': c['continente'],
            't': c['tier'], 'x': c['tours'],
            'a': apelidos,
            'g': list(xy) if xy else None,
        })

    saida = {
        'fonte': 'tools/aeroportos.csv (408 aeroportos) + tools/tours.json',
        'cidades': saida_cidades,
        'tours': lista_tours,
    }
    destino = os.path.join(RAIZ, 'assets', 'procura.json')
    with open(destino, 'w') as f:
        json.dump(saida, f, separators=(',', ':'), ensure_ascii=False)

    antigo = os.path.join(RAIZ, 'assets', 'cidades.json')
    if os.path.exists(antigo):
        os.remove(antigo)
        print('removido o indice antigo do GeoNames: assets/cidades.json')

    print('escrito: %s (%.0f KB)' % (destino,
                                     os.path.getsize(destino) / 1024))
    print('%d aeroportos -> %d cidades, %d paises, %d tours'
          % (len(linhas), len(saida_cidades),
             len({c['p'] for c in saida_cidades}), len(lista_tours)))
    print('com tours: %d cidades' % sum(1 for c in saida_cidades if c['x']))
    print('sem coordenada conhecida: %d (so afeta o mapa, nao a procura)'
          % sem_coord)


if __name__ == '__main__':
    main()
