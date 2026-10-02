#!/usr/bin/env python3
"""
Propostas de logotipo para a Exclusive World Tours.

Seis direcoes, todas desenhadas de raiz em SVG. A pagina mostra cada
uma como ela vai mesmo ser usada, e nao num palco bonito:

- em grande, a preto sobre branco e a branco sobre preto;
- dentro do cabecalho do site, ao tamanho real;
- como icone de 16 px e de 32 px, que e onde a maior parte dos
  logotipos deixa de se ler;
- a uma so cor, sempre.

A cor nao entra aqui de proposito. Um logotipo que so funciona porque
tem um gradiente nao e um logotipo. Decide-se a forma primeiro; a
paleta da marca escolhe-se depois, a partir dele.

    python3 tools/logos.py       # escreve logos/index.html
"""

import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)


# ---------------------------------------------------------------- simbolos
#
# Cada simbolo e uma funcao que devolve o SVG do desenho sozinho, numa
# caixa de 100x100, numa so cor (`currentColor`). Assim o mesmo desenho
# serve para o logotipo grande e para o icone de 16 px, sem redesenhar.

def sim_cruzamento(t=11):
    """Duas rotas que se cruzam, com o cruzamento aberto. Le-se como um
    X — de Exclusive — e como um cruzamento de caminhos. Fechado seria
    uma cruz; aberto e um encontro."""
    return '''<path d="M16 16 L40 40 M60 60 L84 84 M84 16 L60 40 M40 60 L16 84"
      fill="none" stroke="currentColor" stroke-width="%g" stroke-linecap="round"/>
    <circle cx="50" cy="50" r="7" fill="currentColor"/>''' % t


def sim_percurso(t=11):
    """De um ponto a outro: a origem pequena, o destino cheio, e o
    caminho curvo entre os dois. E o produto inteiro num simbolo."""
    return '''<path d="M18 80 C40 80, 44 50, 58 36 C66 28, 74 24, 82 22"
      fill="none" stroke="currentColor" stroke-width="%g" stroke-linecap="round"/>
    <circle cx="18" cy="80" r="%g" fill="var(--fundo, none)" stroke="currentColor"
      stroke-width="%g"/>
    <circle cx="82" cy="22" r="%g" fill="currentColor"/>''' % (t, t * .72, t * .82, t * .95)


def sim_horizonte(t=11):
    """O sol a nascer sobre a linha do horizonte. A forma mais simples
    que ainda diz viagem sem desenhar um aviao nem um globo."""
    return '''<circle cx="50" cy="46" r="24" fill="none" stroke="currentColor" stroke-width="%g"/>
    <path d="M10 78 H90" stroke="currentColor" stroke-width="%g" stroke-linecap="round"/>''' % (t, t)


def sim_camadas_caixa(t=10):
    """Tres barras de comprimento decrescente dentro de um quadrado de
    cantos macios: as camadas de uma paisagem vista de longe, e tambem
    paralelos num mapa. Nao ha forma que se leia melhor a 16 px do que
    linhas horizontais, e o quadrado da-lhe a silhueta que os sistemas
    esperam num icone de aplicacao."""
    return '''<rect x="6" y="6" width="88" height="88" rx="26"
      fill="none" stroke="currentColor" stroke-width="%g"/>
    <path d="M34 32 H62 M34 50 H56 M34 68 H62" stroke="currentColor"
      stroke-width="%g" stroke-linecap="round"/>''' % (t, t)


def sim_marco(t=11):
    """Um marco no mapa, desenhado so com a gota e o vazio la dentro.
    E o unico simbolo desta lista que qualquer pessoa reconhece sem
    explicacao — o que e uma vantagem e tambem o seu risco."""
    return '''<path d="M50 88 C50 88, 22 60, 22 42 a28 28 0 1 1 56 0 C78 60, 50 88, 50 88 Z"
      fill="none" stroke="currentColor" stroke-width="%g" stroke-linejoin="round"/>
    <circle cx="50" cy="42" r="10" fill="currentColor"/>''' % t


# ------------------------------------------------------------- as propostas

PROPOSTAS = [
    {
        'id': 'A', 'nome': 'Ponto final',
        'simbolo': None,
        'ideia': 'So o nome, sem simbolo nenhum. Inter no peso mais forte, '
                 'espacejamento muito apertado, e um ponto final na cor da '
                 'marca. E a convencao das marcas de tecnologia desta decada '
                 'e e a mais dificil de fazer mal.',
        'contra': 'Nao da icone. A 16 px fica so um "e", que nao distingue '
                  'nada. Precisa de uma das outras para lhe fazer companhia '
                  'no separador do browser e nas redes.',
    },
    {
        'id': 'B', 'nome': 'O cruzamento',
        'simbolo': sim_cruzamento,
        'ideia': 'Duas rotas que se cruzam, com o encontro aberto e um ponto '
                 'no meio. Le-se como o X de Exclusive e como um cruzamento '
                 'de caminhos — que e literalmente o que um marketplace faz: '
                 'junta quem viaja a quem conduz.',
        'contra': 'Um X e sempre um pouco severo, e ha quem lhe veja um sinal '
                  'de fechado ou de cancelar. Tem de ser visto em contexto '
                  'antes de se decidir.',
    },
    {
        'id': 'C', 'nome': 'O percurso',
        'simbolo': sim_percurso,
        'ideia': 'De um ponto ao outro: a origem em contorno, o destino '
                 'cheio, e o caminho curvo entre os dois. E o produto inteiro '
                 'num simbolo, e liga-se ao mapa e as coordenadas que ja '
                 'tinhas escolhido como assinatura.',
        'contra': 'E a mais fragil em tamanho pequeno: a curva fina tende a '
                  'desaparecer. Como icone precisa de uma versao com o traco '
                  'mais grosso, que ja esta nesta pagina a 16 px para veres.',
    },
    {
        'id': 'D', 'nome': 'O horizonte',
        'simbolo': sim_horizonte,
        'ideia': 'O sol sobre a linha do horizonte. E a forma mais simples '
                 'que ainda diz viagem sem recorrer a um aviao, a uma mala ou '
                 'a um globo com meridianos.',
        'contra': 'E tambem a mais usada: ha muitos soisinhos sobre linhas no '
                  'turismo. Ganha ou perde no desenho da letra ao lado, nao '
                  'no simbolo.',
    },
    {
        'id': 'E', 'nome': 'As camadas',
        'simbolo': sim_camadas_caixa,
        'ideia': 'Tres barras de comprimento decrescente — as camadas de uma '
                 'paisagem vista de longe, e tambem paralelos num mapa — '
                 'dentro de um quadrado de cantos macios. E a unica das seis '
                 'desenhada de raiz para ser icone: linhas horizontais sao a '
                 'forma que melhor sobrevive a 16 px, e o quadrado da-lhe a '
                 'silhueta que o telemovel espera.',
        'contra': 'Sozinha diz pouco: sem o nome ao lado tanto pode ser uma '
                  'paisagem como um menu de aplicacao. Depende da letra para '
                  'significar alguma coisa.',
    },
    {
        'id': 'F', 'nome': 'O marco',
        'simbolo': sim_marco,
        'ideia': 'Um marco no mapa. E o unico dos seis que toda a gente '
                 'reconhece sem explicacao nenhuma, e isso vale muito num '
                 'marketplace onde o cliente decide em segundos.',
        'contra': 'E tambem o mais banal: o marco e o simbolo por omissao de '
                  'tudo o que tem mapas. Distingue pouco.',
    },
]


# ------------------------------------------------------------------ montar

def marca(p, altura=52, cor='var(--tinta)', ponto='var(--tinta)'):
    """O logotipo completo: simbolo (quando ha) mais o nome."""
    sim = ''
    if p['simbolo']:
        sim = ('<svg class="s" viewBox="0 0 100 100" width="%g" height="%g" '
               'aria-hidden="true" style="color:%s">%s</svg>'
               % (altura, altura, cor, p['simbolo']()))
    return ('<span class="marca" style="--h:%gpx;color:%s">%s'
            '<span class="nome">Exclusive World Tours<span class="pt" '
            'style="color:%s">.</span></span></span>'
            % (altura, cor, sim, ponto))


def icone(p, tam):
    if p['simbolo']:
        return ('<svg viewBox="0 0 100 100" width="%d" height="%d" aria-hidden="true">%s</svg>'
                % (tam, tam, p['simbolo'](t=13 if tam <= 20 else 11)))
    # A proposta sem simbolo: o icone possivel e a inicial.
    return ('<svg viewBox="0 0 100 100" width="%d" height="%d" aria-hidden="true">'
            '<text x="50" y="74" text-anchor="middle" fill="currentColor" '
            'style="font:700 86px Inter,sans-serif;letter-spacing:-.05em">e</text></svg>'
            % (tam, tam))


def bloco(p):
    return '''<article class="prop" id="prop-%s">
  <header class="prop-cab">
    <span class="prop-id">%s</span>
    <h2>%s</h2>
  </header>

  <div class="palcos">
    <div class="palco claro">%s</div>
    <div class="palco escuro">%s</div>
  </div>

  <div class="usos">
    <div class="uso">
      <p class="rot">No cabeçalho do site, ao tamanho real</p>
      <div class="cabeca-demo">%s
        <nav><span>All tours</span><span>Operators</span><span>Help</span></nav>
      </div>
    </div>
    <div class="uso">
      <p class="rot">Ícone: 32 px e 16 px</p>
      <div class="icones">
        <span class="ic ic32">%s</span>
        <span class="ic ic16">%s</span>
        <span class="separador">%s<span>Exclusive World Tours</span></span>
      </div>
    </div>
  </div>

  <div class="notas">
    <p><strong>A ideia.</strong> %s</p>
    <p><strong>Contra.</strong> %s</p>
  </div>
</article>''' % (p['id'], p['id'], p['nome'],
                 marca(p, 54),
                 marca(p, 54, cor='var(--papel)', ponto='var(--papel)'),
                 marca(p, 30),
                 icone(p, 32), icone(p, 16), icone(p, 16),
                 p['ideia'], p['contra'])


PAGINA = '''<!DOCTYPE html>
<html lang="pt-PT">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Propostas de logótipo — Exclusive World Tours</title>
<meta name="robots" content="noindex, nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --papel:#FFFFFF; --tinta:#14161A; --mudo:#5C626B; --linha:#E5E7EA;
  --sup:#F6F7F8;
  --ui:'Inter',system-ui,-apple-system,sans-serif;
  --e3:12px; --e4:16px; --e5:20px; --e6:28px; --e7:40px; --e8:56px; --e9:80px;
}
*,*::before,*::after{box-sizing:border-box}
body{margin:0;background:var(--papel);color:var(--tinta);font-family:var(--ui);
     font-size:16px;line-height:1.55;-webkit-font-smoothing:antialiased}
svg{display:block}
h1,h2{margin:0;font-weight:700;letter-spacing:-0.035em;line-height:1.1}
h1{font-size:clamp(1.9rem, 1.3rem + 2.2vw, 2.9rem)}
h2{font-size:1.3rem}
p{margin:0 0 var(--e4);max-width:66ch}
p:last-child{margin-bottom:0}
.largura{width:100%;max-width:1120px;margin-inline:auto;padding-inline:var(--e5)}
@media(min-width:900px){.largura{padding-inline:var(--e7)}}

.topo{padding-block:var(--e9) var(--e7);border-bottom:1px solid var(--linha)}
.topo p{color:var(--mudo);margin-top:var(--e4);font-size:17px}

/* ---------------------------------------------------------- o logotipo */
.marca{display:inline-flex;align-items:center;gap:calc(var(--h) * .30)}
.marca .s{flex:0 0 auto}
.nome{font-weight:700;letter-spacing:-0.045em;line-height:1;
      font-size:calc(var(--h) * .50);white-space:nowrap}
.pt{font-weight:700}

.prop{padding-block:var(--e9);border-bottom:1px solid var(--linha)}
.prop-cab{display:flex;align-items:center;gap:var(--e4);margin-bottom:var(--e6)}
.prop-id{display:grid;place-items:center;width:34px;height:34px;flex:0 0 auto;
  border:1.5px solid var(--tinta);border-radius:50%;font-size:14px;font-weight:700}

.palcos{display:grid;gap:var(--e4)}
@media(min-width:760px){.palcos{grid-template-columns:1fr 1fr}}
.palco{display:grid;place-items:center;padding:var(--e8) var(--e5);
       border-radius:14px;overflow:hidden}
.claro{background:var(--sup)}
.escuro{background:var(--tinta)}

.usos{display:grid;gap:var(--e6);margin-top:var(--e6)}
@media(min-width:760px){.usos{grid-template-columns:1.25fr 1fr}}
.rot{font-size:12.5px;color:var(--mudo);margin:0 0 var(--e3)}
.cabeca-demo{display:flex;align-items:center;justify-content:space-between;
  gap:var(--e5);border:1px solid var(--linha);border-radius:12px;
  padding:var(--e4) var(--e5);min-height:76px}
.cabeca-demo nav{display:flex;gap:var(--e5);font-size:13.5px;color:var(--mudo)}
@media(max-width:620px){.cabeca-demo nav{display:none}}

.icones{display:flex;align-items:center;gap:var(--e5);flex-wrap:wrap;
  border:1px solid var(--linha);border-radius:12px;padding:var(--e4) var(--e5);
  min-height:76px}
.ic{display:grid;place-items:center;border-radius:8px;background:var(--sup);
    color:var(--tinta)}
.ic32{width:48px;height:48px}
.ic16{width:30px;height:30px}
.separador{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--linha);
  border-radius:8px 8px 0 0;padding:6px 12px;font-size:12.5px;color:var(--mudo);
  background:var(--papel)}

.notas{margin-top:var(--e6)}
.notas p{font-size:14.5px;margin-bottom:8px;max-width:78ch}
.notas strong{font-weight:600}

.fim{padding-block:var(--e8) var(--e9);color:var(--mudo);font-size:14.5px}
.fim p{max-width:72ch}
</style>
</head>
<body>

<header class="topo">
  <div class="largura">
    <h1>Seis logótipos, a uma só cor</h1>
    <p>A cor não entra aqui de propósito. Um logótipo decide-se a preto e
    branco: se só funciona porque tem um gradiente bonito, não é um
    logótipo. Escolhida a forma, a paleta da marca sai dela — e não ao
    contrário, que foi onde encalhámos.</p>
    <p>Cada proposta aparece em grande sobre claro e sobre escuro, depois
    dentro do cabeçalho do site ao tamanho real, e por fim reduzida a 32 e
    a 16 px, que é onde a maior parte dos logótipos deixa de se ler.</p>
  </div>
</header>

<main class="largura">
{{PROPOSTAS}}
</main>

<footer class="fim">
  <div class="largura">
    <p>Escolhida uma direção, afino-a à mão — proporções, espacejamento
    óptico, as versões horizontal e empilhada — e entrego em SVG, PNG e
    favicon, mais a versão a uma só cor para carimbo e bordado. Nenhuma
    destas é definitiva: servem para decidires o caminho.</p>
  </div>
</footer>

</body>
</html>'''


def main():
    html = PAGINA.replace('{{PROPOSTAS}}', '\n'.join(bloco(p) for p in PROPOSTAS))

    # Escreve-se nos dois sitios de proposito. O Render nem sempre serve
    # uma pasta a partir do index.html quando o endereco leva barra no
    # fim — ja apanhei um 404 em /logos/ com o /logos/index.html a
    # funcionar. Um ficheiro na raiz nao depende disso e abre sempre.
    destinos = [os.path.join(RAIZ, 'logos', 'index.html'),
                os.path.join(RAIZ, 'logos.html')]
    for caminho in destinos:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'w') as f:
            f.write(html)
        print('escrito: %s (%.0f KB)' % (caminho, os.path.getsize(caminho) / 1024))
    print('%d propostas' % len(PROPOSTAS))


if __name__ == '__main__':
    main()
