"""
O mapa de rota — o elemento de assinatura da Exclusive World Tours.

Nao e decoracao: recebe as coordenadas reais de cada parada e desenha-as
na posicao geografica correta, com uma linha fina a ligar as paradas na
ordem em que o dia as percorre.

Projecao: equirretangular com correcao do cosseno da latitude media
(longitude * cos(lat_media)). Numa area do tamanho de um pais a
distorcao e invisivel e a forma do percurso fica fiel — uma Mercator
aqui nao acrescentava nada e complicava a leitura.

A caixa de desenho e a caixa dos pontos, com uma margem para o rotulo
nao sair fora. O eixo Y inverte-se: no SVG cresce para baixo, na
latitude cresce para norte.

Uso:
    from mapa import rota_svg
    svg = rota_svg(paradas, largura=560, altura=420)

Cada parada e um dicionario:
    {"nome": "Cliffs of Moher", "lat": 52.9715, "lon": -9.4309,
     "hora": "10:30", "chave": True}

`chave` marca as paradas principais: ficam com o ponto maior e o nome
visivel. As outras ficam com o ponto pequeno.
"""

import math


def graus(lat, lon):
    """
    As coordenadas no formato que se le em voz alta: 52.9715 N, 9.4309 W.

    Quatro casas decimais chegam para identificar um local com cerca de
    onze metros de precisao, e e o formato que o Ricardo escreveu no
    briefing. Mais casas davam uma falsa ideia de rigor.
    """
    ns = 'N' if lat >= 0 else 'S'
    ew = 'E' if lon >= 0 else 'W'
    return '%.4f° %s, %.4f° %s' % (abs(lat), ns, abs(lon), ew)


def _projetar(paradas, largura, altura, margem):
    """Lat/lon reais para pontos do SVG, mantendo a proporcao do terreno."""
    lats = [p['lat'] for p in paradas]
    lons = [p['lon'] for p in paradas]
    lat_media = math.radians(sum(lats) / len(lats))
    k = math.cos(lat_media)

    xs = [lon * k for lon in lons]
    ys = lats

    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    dx = (x1 - x0) or 1e-9
    dy = (y1 - y0) or 1e-9

    # Uma so escala nos dois eixos: o percurso nao se deforma.
    util_l = largura - 2 * margem
    util_a = altura - 2 * margem
    escala = min(util_l / dx, util_a / dy)

    # Centrar o que sobra da caixa.
    sobra_x = (util_l - dx * escala) / 2
    sobra_y = (util_a - dy * escala) / 2

    pontos = []
    for p, x, y in zip(paradas, xs, ys):
        px = margem + sobra_x + (x - x0) * escala
        py = margem + sobra_y + (y1 - y) * escala    # norte para cima
        pontos.append((px, py))
    return pontos


def rota_svg(paradas, largura=560, altura=420, margem=46, id_prefixo='rota'):
    """
    O SVG do percurso.

    Devolve o elemento inteiro, pronto a inserir. Sem JavaScript: e uma
    imagem, e tem de continuar a ler-se com o JavaScript desligado.
    """
    pontos = _projetar(paradas, largura, altura, margem)

    linha = ' '.join('%.1f,%.1f' % pt for pt in pontos)

    # O caminho do percurso, por baixo de tudo o resto.
    partes = [
        '<svg class="rota" viewBox="0 0 %d %d" width="%d" height="%d" '
        'role="img" aria-labelledby="%s-t %s-d">'
        % (largura, altura, largura, altura, id_prefixo, id_prefixo),
        '<title id="%s-t">The route of the day</title>' % id_prefixo,
        '<desc id="%s-d">%s</desc>' % (
            id_prefixo,
            ' then '.join('%s at %s' % (p['nome'], p['hora']) for p in paradas)),
        '<polyline class="rota-linha" points="%s" />' % linha,
    ]

    # Os pontos e os rotulos, por cima.
    for p, (x, y) in zip(paradas, pontos):
        chave = p.get('chave')
        # O regresso ao ponto de partida fecha a linha mas nao leva ponto
        # novo: seria um circulo por cima do que ja esta ali.
        if p.get('ponto') is False:
            continue
        partes.append(
            '<circle class="rota-ponto%s" cx="%.1f" cy="%.1f" r="%s" />'
            % (' rota-ponto-chave' if chave else '', x, y, '4.5' if chave else '2.5'))
        if chave:
            # O rotulo salta para a esquerda quando o ponto esta na metade
            # direita, para nao sair fora da caixa.
            direita = x > largura * 0.62
            partes.append(
                '<text class="rota-nome" x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
                % (x + (-10 if direita else 10), y - 9,
                   'end' if direita else 'start', p['nome']))
            partes.append(
                '<text class="rota-hora" x="%.1f" y="%.1f" text-anchor="%s">%s</text>'
                % (x + (-10 if direita else 10), y + 6,
                   'end' if direita else 'start', p['hora']))

    partes.append('</svg>')
    return '\n'.join(partes)
