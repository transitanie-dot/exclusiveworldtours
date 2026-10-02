#!/usr/bin/env python3
"""
O atlas: gera o mapa e os pontos da homepage a partir de dados reais.

Duas fontes, nenhuma inventada:

- a geometria dos paises vem do Natural Earth, pelo pacote `world-atlas`
  (TopoJSON a 1:50m);
- as coordenadas das cidades vem do GeoNames, pelo pacote `geonamescache`.

Se uma cidade nao for encontrada na base, o script FALHA em vez de
adivinhar uma coordenada. Um mapa com um ponto errado e pior do que um
mapa que nao existe.

    python3 tools/atlas.py            # escreve assets/atlas.svg e atlas.json
"""

import json
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

# O TopoJSON vem do node_modules; o caminho e passado por variavel de
# ambiente para o script nao depender de onde foi instalado.
TOPO = os.environ.get('WORLD_ATLAS') or os.path.join(
    AQUI, 'node_modules', 'world-atlas', 'countries-50m.json')

# ----------------------------------------------------------- as cidades

# O nome que o Ricardo usa no tours.json, e o nome e o pais com que se
# procura no GeoNames. Onde o tour parte de uma regiao e nao de uma
# cidade, a cidade de referencia esta aqui explicita — e uma decisao, nao
# uma adivinhacao, e fica escrita.
CIDADES = {
    'Dublin':     ('Dublin',        'IE'),
    'London':     ('London',        'GB'),
    'Edinburgh':  ('Edinburgh',     'GB'),
    'Paris':      ('Paris',         'FR'),
    'Rome':       ('Rome',          'IT'),
    'Florence':   ('Florence',      'IT'),
    # O GeoNames so traz cidades acima dos 15 000 habitantes. Estas duas
    # ficam abaixo, por isso as coordenadas vem da Wikipedia, verificadas
    # a mao a 2 de outubro de 2026 — nao sao estimativas.
    'Sorrento':   (40.62611, 14.37611),   # en.wikipedia.org/wiki/Sorrento
    'Taormina':   (37.85222, 15.29194),   # en.wikipedia.org/wiki/Taormina
    'Palermo':    ('Palermo',       'IT'),
    'Olbia':      ('Olbia',         'IT'),
    'Cagliari':   ('Cagliari',      'IT'),
    'Lisbon':     ('Lisbon',        'PT'),
    'Porto':      ('Porto',         'PT'),
    'Algarve':    ('Faro',          'PT'),   # a regiao parte de Faro
    'Madeira':    ('Funchal',       'PT'),   # a ilha parte do Funchal
    'São Miguel': ('Ponta Delgada', 'PT'),   # a ilha parte de Ponta Delgada
    'Madrid':     ('Madrid',        'ES'),
    'Barcelona':  ('Barcelona',     'ES'),
    'Seville':    ('Seville',       'ES'),
}

# Os paises que o mapa desenha. Os seis onde ha tours, mais os vizinhos
# que dao contexto ao recorte — sem eles a Europa fica com buracos e
# deixa de se reconhecer.
COM_TOURS = {'IRL', 'GBR', 'FRA', 'ITA', 'ESP', 'PRT'}
CONTEXTO = {'BEL', 'NLD', 'DEU', 'CHE', 'AUT', 'LUX', 'MAR', 'DZA', 'TUN',
            'AND', 'MCO', 'SMR', 'VAT', 'SVN', 'HRV', 'CZE', 'DNK', 'MLT'}

# Natural Earth usa o codigo numerico ISO 3166-1; o world-atlas traz o
# nome em `properties.name`. Procura-se pelo nome, que e estavel.
NOMES = {
    'Ireland': 'IRL', 'United Kingdom': 'GBR', 'France': 'FRA',
    'Italy': 'ITA', 'Spain': 'ESP', 'Portugal': 'PRT',
    'Belgium': 'BEL', 'Netherlands': 'NLD', 'Germany': 'DEU',
    'Switzerland': 'CHE', 'Austria': 'AUT', 'Luxembourg': 'LUX',
    'Morocco': 'MAR', 'Algeria': 'DZA', 'Tunisia': 'TUN',
    'Andorra': 'AND', 'Monaco': 'MCO', 'San Marino': 'SMR',
    'Slovenia': 'SVN', 'Croatia': 'HRV', 'Czechia': 'CZE',
    'Denmark': 'DNK', 'Malta': 'MLT',
}

# A janela do mapa, em graus. Cobre dos Acores (-25.7 W) a Italia, e do
# norte de Africa a Escocia.
LON0, LON1 = -27.5, 19.0
LAT0, LAT1 = 31.6, 59.5

LARGURA = 1000.0     # unidades do viewBox


# ------------------------------------------------------------- TopoJSON

def descodificar(topo):
    """Os arcos do TopoJSON vem quantizados e em delta. Isto devolve-os
    em graus."""
    sx, sy = topo['transform']['scale']
    tx, ty = topo['transform']['translate']
    arcos = []
    for arco in topo['arcs']:
        x = y = 0
        pontos = []
        for dx, dy in arco:
            x += dx
            y += dy
            pontos.append((x * sx + tx, y * sy + ty))
        arcos.append(pontos)
    return arcos


def anel(arcos, indices):
    """Um anel e uma lista de indices de arcos; negativo quer dizer o
    arco ao contrario (~i, isto e, -i-1)."""
    pontos = []
    for i in indices:
        if i >= 0:
            trecho = arcos[i]
        else:
            trecho = arcos[~i][::-1]
        pontos.extend(trecho if not pontos else trecho[1:])
    return pontos


def poligonos(geom, arcos):
    """Devolve a lista de aneis exteriores e interiores da geometria."""
    t = geom['type']
    if t == 'Polygon':
        return [[anel(arcos, r) for r in geom['arcs']]]
    if t == 'MultiPolygon':
        return [[anel(arcos, r) for r in poli] for poli in geom['arcs']]
    return []


# ------------------------------------------------------------- projecao

LAT_MEDIA = math.radians((LAT0 + LAT1) / 2)
K = math.cos(LAT_MEDIA)

ESCALA = LARGURA / ((LON1 - LON0) * K)
ALTURA = (LAT1 - LAT0) * ESCALA


def projetar(lon, lat):
    """Equirretangular com correcao do cosseno da latitude media. Para
    uma janela deste tamanho a distorcao nao se ve, e o desenho fica
    fiel o suficiente para o mapa ser informacao e nao enfeite."""
    x = (lon - LON0) * K * ESCALA
    y = (LAT1 - lat) * ESCALA
    return x, y


def dentro(lon, lat, folga=6.0):
    return (LON0 - folga) <= lon <= (LON1 + folga) and \
           (LAT0 - folga) <= lat <= (LAT1 + folga)


def caminho(aneis, casas=1):
    """Os aneis para um atributo `d`, com os pontos arredondados: a uma
    decima de unidade o olho nao ve diferenca e o ficheiro fica muito
    mais pequeno."""
    partes = []
    for a in aneis:
        pts = [projetar(lon, lat) for lon, lat in a]
        # Fora da janela nao vale a pena desenhar.
        if not any(-60 <= x <= LARGURA + 60 and -60 <= y <= ALTURA + 60
                   for x, y in pts):
            continue
        d = 'M' + ' L'.join('%.*f %.*f' % (casas, x, casas, y) for x, y in pts) + 'Z'
        partes.append(d)
    return ' '.join(partes)


# --------------------------------------------------------------- correr

def main():
    if not os.path.exists(TOPO):
        sys.exit('Falta o world-atlas. Instala com: npm install world-atlas\n'
                 'ou aponta a variavel WORLD_ATLAS para o countries-50m.json')

    import geonamescache
    gc = geonamescache.GeonamesCache()
    todas = gc.get_cities()

    # ---- as cidades
    pontos = {}
    faltam = []
    for rotulo, valor in CIDADES.items():
        # Um par de numeros e uma coordenada verificada a mao; um par de
        # textos e uma procura no GeoNames.
        if isinstance(valor[0], float):
            pontos[rotulo] = {'nome': rotulo, 'geonome': rotulo + ' (Wikipedia)',
                              'pais': '', 'lat': valor[0], 'lon': valor[1]}
            continue
        nome, pais = valor
        achados = [c for c in todas.values()
                   if c['countrycode'] == pais and
                   (c['name'] == nome or nome in c.get('alternatenames', []))]
        if not achados:
            faltam.append('%s (%s, %s)' % (rotulo, nome, pais))
            continue
        # A maior, quando ha homonimos dentro do mesmo pais.
        c = max(achados, key=lambda c: c['population'])
        pontos[rotulo] = {
            'nome': rotulo, 'geonome': c['name'], 'pais': pais,
            'lat': round(c['latitude'], 4), 'lon': round(c['longitude'], 4),
        }

    if faltam:
        sys.exit('Cidades que o GeoNames nao resolveu — nao invento '
                 'coordenadas:\n  ' + '\n  '.join(faltam))

    # ---- o mapa
    topo = json.load(open(TOPO))
    arcos = descodificar(topo)
    geo = topo['objects']['countries']['geometries']

    com, sem = [], []
    for g in geo:
        nome = g.get('properties', {}).get('name')
        cod = NOMES.get(nome)
        if not cod:
            continue
        for aneis in poligonos(g, arcos):
            d = caminho(aneis)
            if not d:
                continue
            (com if cod in COM_TOURS else sem).append((cod, d))

    # ---- contar os tours por cidade
    tours = json.load(open(os.path.join(RAIZ, 'tools', 'tours.json')))['tours'] \
        if os.path.exists(os.path.join(RAIZ, 'tools', 'tours.json')) else []

    saida = {
        'janela': {'lon0': LON0, 'lon1': LON1, 'lat0': LAT0, 'lat1': LAT1},
        'viewBox': [0, 0, round(LARGURA, 1), round(ALTURA, 1)],
        'cidades': pontos,
        'paises_com_tours': [{'cod': c, 'd': d} for c, d in com],
        'paises_contexto': [{'cod': c, 'd': d} for c, d in sem],
    }
    for nome, p in pontos.items():
        x, y = projetar(p['lon'], p['lat'])
        p['x'], p['y'] = round(x, 1), round(y, 1)

    destino = os.path.join(RAIZ, 'assets', 'atlas.json')
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, 'w') as f:
        json.dump(saida, f, separators=(',', ':'))

    print('viewBox 0 0 %.0f %.0f' % (LARGURA, ALTURA))
    print('paises com tours: %d poligonos' % len(com))
    print('paises de contexto: %d poligonos' % len(sem))
    print('cidades resolvidas: %d' % len(pontos))
    print('escrito: %s (%.0f KB)' % (destino, os.path.getsize(destino) / 1024))
    for n, p in sorted(pontos.items()):
        print('  %-12s %-14s %8.4f %9.4f   -> %6.1f %6.1f'
              % (n, p['geonome'], p['lat'], p['lon'], p['x'], p['y']))


if __name__ == '__main__':
    main()
