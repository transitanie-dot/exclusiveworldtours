#!/usr/bin/env python3
"""
Segunda ronda de logotipos — mais desenho, turismo explicito.

A primeira ronda era geometria minima e o Ricardo achou-a simples de mais
e sem leitura de turismo. Esta vai ao contrario: simbolos com mais traco,
com referencias de viagem que qualquer pessoa reconhece — rosa dos
ventos, globo com rota, emblema de paisagem, arco, janela, farol.

Cada proposta vem em duas versoes, e isso nao e um extra: e como se faz.

- A **marca completa**, com o detalhe todo, para o cabecalho, o rodape,
  o papel timbrado, o autocolante na carrinha.
- A **versao reduzida**, simplificada a mao, para 16 e 32 px. Um simbolo
  detalhado encolhido a 16 px vira uma nodoa; por isso desenha-se outro,
  com menos elementos e traco mais grosso, que se le a essa escala e
  continua a ser reconhecivel como o mesmo.

A cor continua fora: decide-se a forma primeiro.

    python3 tools/logos2.py       # escreve logos2.html e logos2/index.html
"""

import os

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)


# ============================================================== os simbolos
#
# Cada par de funcoes desenha o mesmo simbolo em dois niveis de detalhe,
# numa caixa de 100x100 e numa so cor (`currentColor`).

# ---------------------------------------------------------- 1. rosa dos ventos

def rosa_completa():
    return '''
    <circle cx="50" cy="50" r="46" fill="none" stroke="currentColor" stroke-width="2.4"/>
    <circle cx="50" cy="50" r="38" fill="none" stroke="currentColor" stroke-width="1.1"/>
    <g stroke="currentColor" stroke-width="1.1" fill="none">
      <path d="M50 12 v6 M50 82 v6 M12 50 h6 M82 50 h6"/>
      <path d="M23 23 l4.2 4.2 M77 23 l-4.2 4.2 M23 77 l4.2 -4.2 M77 77 l-4.2 -4.2"/>
    </g>
    <!-- as quatro pontas diagonais, mais curtas -->
    <path d="M50 50 L68 32 L59 41 Z M50 50 L68 68 L59 59 Z
             M50 50 L32 68 L41 59 Z M50 50 L32 32 L41 41 Z"
          fill="currentColor" opacity=".45"/>
    <!-- as quatro pontas principais -->
    <path d="M50 50 L50 16 L57 43 Z M50 50 L50 16 L43 43 Z" fill="currentColor"/>
    <path d="M50 50 L50 84 L57 57 Z M50 50 L50 84 L43 57 Z" fill="currentColor" opacity=".55"/>
    <path d="M50 50 L84 50 L57 57 Z M50 50 L84 50 L57 43 Z" fill="currentColor" opacity=".55"/>
    <path d="M50 50 L16 50 L43 57 Z M50 50 L16 50 L43 43 Z" fill="currentColor" opacity=".55"/>
    <circle cx="50" cy="50" r="4.5" fill="currentColor"/>'''


def rosa_reduzida():
    return '''
    <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" stroke-width="7"/>
    <path d="M50 14 L60 50 L50 86 L40 50 Z" fill="currentColor"/>
    <path d="M14 50 L50 40 L86 50 L50 60 Z" fill="currentColor" opacity=".55"/>'''


# ------------------------------------------------------------ 2. globo em rota

def globo_completo():
    return '''
    <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="2.6"/>
    <!-- paralelos -->
    <path d="M14 38 H86 M11 50 H89 M14 62 H86" stroke="currentColor"
          stroke-width="1.3" fill="none" opacity=".75"/>
    <!-- meridianos -->
    <ellipse cx="50" cy="50" rx="17" ry="40" fill="none" stroke="currentColor"
             stroke-width="1.3" opacity=".75"/>
    <path d="M50 10 V90" stroke="currentColor" stroke-width="1.3" opacity=".75"/>
    <!-- a rota, por cima, a sair e a entrar no globo -->
    <path d="M22 70 C34 34, 70 26, 86 20" fill="none" stroke="currentColor"
          stroke-width="4.2" stroke-linecap="round" stroke-dasharray="1 8"/>
    <circle cx="22" cy="70" r="6.5" fill="currentColor"/>
    <path d="M86 20 l-8 -2 l2 8 Z" fill="currentColor"/>'''


def globo_reduzido():
    return '''
    <circle cx="50" cy="50" r="38" fill="none" stroke="currentColor" stroke-width="8"/>
    <path d="M12 50 H88" stroke="currentColor" stroke-width="7"/>
    <ellipse cx="50" cy="50" rx="17" ry="38" fill="none" stroke="currentColor"
             stroke-width="7"/>'''


# -------------------------------------------------------------- 3. o emblema

def emblema_completo():
    return '''
    <circle cx="50" cy="50" r="46" fill="none" stroke="currentColor" stroke-width="2.6"/>
    <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="1"/>
    <!-- o sol, atras das montanhas -->
    <circle cx="50" cy="40" r="11" fill="none" stroke="currentColor" stroke-width="2.6"/>
    <g stroke="currentColor" stroke-width="2.4" stroke-linecap="round">
      <path d="M50 20 v6 M34.5 30.5 l4 4 M65.5 30.5 l-4 4 M26 44 h6 M68 44 h6"/>
    </g>
    <!-- as montanhas -->
    <path d="M18 66 L34 46 L45 60 L56 40 L74 66 Z" fill="currentColor" opacity=".18"/>
    <path d="M18 66 L34 46 L45 60 L56 40 L74 66" fill="none" stroke="currentColor"
          stroke-width="2.4" stroke-linejoin="round"/>
    <!-- a estrada a fugir para o horizonte -->
    <path d="M30 82 L45 66 M70 82 L55 66" fill="none" stroke="currentColor"
          stroke-width="2.4" stroke-linecap="round"/>
    <path d="M50 80 v-4 M50 72 v-4" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" opacity=".7"/>'''


def emblema_reduzido():
    return '''
    <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" stroke-width="7"/>
    <circle cx="50" cy="40" r="9" fill="currentColor"/>
    <path d="M20 70 L38 48 L52 64 L64 50 L80 70 Z" fill="currentColor"/>'''


# ------------------------------------------------------------------ 4. o arco

def arco_completo():
    return '''
    <!-- o arco: a viagem como passagem -->
    <path d="M22 86 V48 a28 28 0 0 1 56 0 V86" fill="none" stroke="currentColor"
          stroke-width="3"/>
    <path d="M30 86 V48 a20 20 0 0 1 40 0 V86" fill="none" stroke="currentColor"
          stroke-width="1.4" opacity=".7"/>
    <!-- as aduelas -->
    <g stroke="currentColor" stroke-width="1.2" opacity=".7">
      <path d="M26.5 40 l7.5 3 M34 29 l6 5.5 M50 22 v8 M66 29 l-6 5.5 M73.5 40 l-7.5 3"/>
    </g>
    <!-- a estrada a passar por baixo e a fugir -->
    <path d="M38 86 L47 60 M62 86 L53 60" fill="none" stroke="currentColor"
          stroke-width="2.4" stroke-linecap="round"/>
    <path d="M50 78 v-5 M50 69 v-5" stroke="currentColor" stroke-width="2"
          stroke-linecap="round" opacity=".7"/>
    <path d="M12 86 H88" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>'''


def arco_reduzido():
    return '''
    <path d="M26 80 V48 a24 24 0 0 1 48 0 V80" fill="none" stroke="currentColor"
          stroke-width="10"/>
    <path d="M14 88 H86" stroke="currentColor" stroke-width="10"
          stroke-linecap="round"/>'''


# ---------------------------------------------------------------- 5. a janela

def janela_completa():
    return '''
    <rect x="12" y="12" width="76" height="76" rx="22" fill="none"
          stroke="currentColor" stroke-width="3"/>
    <!-- o sol -->
    <circle cx="66" cy="36" r="9" fill="currentColor" opacity=".85"/>
    <!-- as colinas -->
    <path d="M12 64 C26 48, 36 68, 50 58 C62 50, 74 62, 88 54"
          fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
    <path d="M12 74 C28 60, 40 78, 54 68 C66 60, 76 70, 88 64"
          fill="none" stroke="currentColor" stroke-width="2" opacity=".55"
          stroke-linecap="round"/>
    <!-- a agua -->
    <g stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity=".7">
      <path d="M24 82 h14 M46 82 h12 M64 82 h12"/>
    </g>'''


def janela_reduzida():
    return '''
    <rect x="10" y="10" width="80" height="80" rx="24" fill="none"
          stroke="currentColor" stroke-width="8"/>
    <circle cx="66" cy="36" r="9" fill="currentColor"/>
    <path d="M18 70 C32 50, 44 74, 58 62 C68 54, 76 64, 86 58"
          fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>'''


# ----------------------------------------------------------------- 6. o farol

def farol_completo():
    return '''
    <!-- a luz -->
    <g stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity=".65">
      <path d="M30 24 L14 18 M30 32 L12 32 M70 24 L86 18 M70 32 L88 32"/>
    </g>
    <!-- a lanterna -->
    <path d="M40 20 H60 L57 34 H43 Z" fill="currentColor"/>
    <path d="M37 38 H63" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
    <!-- a torre -->
    <path d="M42 38 L38 76 H62 L58 38" fill="none" stroke="currentColor"
          stroke-width="3" stroke-linejoin="round"/>
    <g stroke="currentColor" stroke-width="2" opacity=".6">
      <path d="M41 50 H59 M40 62 H60"/>
    </g>
    <!-- a rocha e o mar -->
    <path d="M24 78 C32 74, 40 78, 50 78 C60 78, 68 74, 76 78" fill="none"
          stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
    <g stroke="currentColor" stroke-width="2" stroke-linecap="round" opacity=".7">
      <path d="M14 86 h16 M38 86 h24 M70 86 h16"/>
    </g>'''


def farol_reduzido():
    return '''
    <!-- a lanterna -->
    <path d="M41 14 H59 L56 27 H44 Z" fill="currentColor"/>
    <!-- a torre: alta e estreita, para nao ler como um laco ao pequeno -->
    <path d="M44 31 L39 80 H61 L56 31 Z" fill="currentColor"/>
    <!-- os raios: horizontais e a meia altura da lanterna, destacados.
         Em diagonal colavam aos cantos da lanterna e o conjunto lia-se
         como um laco em vez de um farol. -->
    <g stroke="currentColor" stroke-width="7" stroke-linecap="round">
      <path d="M27 21 H16 M73 21 H84"/>
    </g>
    <!-- a rocha -->
    <path d="M24 88 h52" stroke="currentColor" stroke-width="7"
          stroke-linecap="round"/>'''


# ============================================================== as propostas

PROPOSTAS = [
    {
        'id': 'G', 'nome': 'A rosa dos ventos',
        'completa': rosa_completa, 'reduzida': rosa_reduzida,
        'ideia': 'A rosa dos ventos e o simbolo mais antigo da viagem que '
                 'existe, e nao precisa de explicacao nenhuma em lado nenhum '
                 'do mundo. Esta tem dois aneis, as quatro pontas principais '
                 'cheias e as diagonais mais leves, com marcas de grau a toda '
                 'a volta — e um instrumento, nao um icone.',
        'contra': 'E tambem o simbolo mais usado em agencias de viagens. O que '
                  'a distingue tem de vir do desenho e da letra ao lado, nao '
                  'da ideia.',
    },
    {
        'id': 'H', 'nome': 'O globo em rota',
        'completa': globo_completo, 'reduzida': globo_reduzido,
        'ideia': 'Um globo com paralelos e meridianos, atravessado por uma '
                 'rota a tracejado que sai de um ponto e aponta para fora da '
                 'esfera. Diz "world" e diz "tours" no mesmo desenho, e liga-se '
                 'ao mapa real que ja esta na homepage.',
        'contra': 'Globo com rota tracejada e o desenho de viagem mais '
                  'repetido que ha. Funciona, mas nao surpreende ninguem.',
    },
    {
        'id': 'I', 'nome': 'O emblema',
        'completa': emblema_completo, 'reduzida': emblema_reduzido,
        'ideia': 'Dentro de um anel duplo: o sol com raios, uma linha de '
                 'montanhas e a estrada a fugir para o horizonte com a linha '
                 'branca do meio. E uma paisagem inteira num selo, e e o que '
                 'mais diretamente diz "um dia de carro pela estrada".',
        'contra': 'Emblemas circulares com montanhas sao a linguagem dos '
                  'parques naturais e das cervejas artesanais. Corre o risco '
                  'de parecer um clube de campo em vez de um marketplace.',
    },
    {
        'id': 'J', 'nome': 'O arco',
        'completa': arco_completo, 'reduzida': arco_reduzido,
        'ideia': 'Um arco de pedra com as aduelas marcadas e a estrada a passar '
                 'por baixo, a fugir para longe. A viagem como passagem — e uma '
                 'forma que existe em Roma, em Lisboa, em Paris e em Dublin, '
                 'por isso serve os seis paises sem pertencer a nenhum.',
        'contra': 'Lido em pequeno pode confundir-se com uma porta ou com um '
                  'tunel. E o menos imediato dos seis.',
    },
    {
        'id': 'K', 'nome': 'A janela',
        'completa': janela_completa, 'reduzida': janela_reduzida,
        'ideia': 'O que se ve da janela do carro: colinas, agua e o sol. '
                 'O quadrado de cantos macios ja e a forma de um icone de '
                 'aplicacao, por isso esta e a unica que nasce pronta para o '
                 'telemovel.',
        'contra': 'E a mais doce das seis, e doce nao e exatamente o que a '
                  'palavra "exclusive" promete.',
    },
    {
        'id': 'L', 'nome': 'O farol',
        'completa': farol_completo, 'reduzida': farol_reduzido,
        'ideia': 'Um farol com a luz a sair para os dois lados, sobre a rocha '
                 'e o mar. Guia, costa e Atlantico — tres coisas que a marca '
                 'tem de verdade, com tours na Irlanda, em Portugal e no '
                 'Mediterraneo. E dos seis, o unico que ninguem neste mercado '
                 'esta a usar.',
        'contra': 'Um farol fica parado e a marca vende movimento. E a aposta '
                  'mais arriscada da lista — que e tambem porque e a mais '
                  'interessante.',
    },
]


# ================================================================== montar

def marca(p, altura, cor):
    return ('<span class="marca" style="--h:%gpx;color:%s">'
            '<svg class="s" viewBox="0 0 100 100" width="%g" height="%g" '
            'aria-hidden="true">%s</svg>'
            '<span class="nome">Exclusive World Tours</span></span>'
            % (altura, cor, altura, altura, p['completa']()))


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
      <p class="rot">Versão reduzida: 32 px e 16 px</p>
      <div class="icones">
        <span class="ic ic32"><svg viewBox="0 0 100 100" width="32" height="32" aria-hidden="true">%s</svg></span>
        <span class="ic ic16"><svg viewBox="0 0 100 100" width="16" height="16" aria-hidden="true">%s</svg></span>
        <span class="separador"><svg viewBox="0 0 100 100" width="16" height="16" aria-hidden="true">%s</svg><span>Exclusive World Tours</span></span>
      </div>
    </div>
  </div>

  <div class="comparar">
    <p class="rot">O mesmo símbolo nos dois níveis de detalhe, lado a lado</p>
    <div class="par">
      <span><svg viewBox="0 0 100 100" width="76" height="76" aria-hidden="true">%s</svg><small>completa</small></span>
      <span><svg viewBox="0 0 100 100" width="76" height="76" aria-hidden="true">%s</svg><small>reduzida</small></span>
    </div>
  </div>

  <div class="notas">
    <p><strong>A ideia.</strong> %s</p>
    <p><strong>Contra.</strong> %s</p>
  </div>
</article>''' % (p['id'], p['id'], p['nome'],
                 marca(p, 60, 'var(--tinta)'),
                 marca(p, 60, 'var(--papel)'),
                 marca(p, 34, 'var(--tinta)'),
                 p['reduzida'](), p['reduzida'](), p['reduzida'](),
                 p['completa'](), p['reduzida'](),
                 p['ideia'], p['contra'])


PAGINA = '''<!DOCTYPE html>
<html lang="pt-PT">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Logótipos, segunda ronda — Exclusive World Tours</title>
<meta name="robots" content="noindex, nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{
  --papel:#FFFFFF; --tinta:#14161A; --mudo:#5C626B; --linha:#E5E7EA; --sup:#F6F7F8;
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

.marca{display:inline-flex;align-items:center;gap:calc(var(--h) * .26)}
.marca .s{flex:0 0 auto}
.nome{font-weight:700;letter-spacing:-0.045em;line-height:1;
      font-size:calc(var(--h) * .42);white-space:nowrap}

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
  padding:var(--e4) var(--e5);min-height:84px}
.cabeca-demo nav{display:flex;gap:var(--e5);font-size:13.5px;color:var(--mudo)}
@media(max-width:620px){.cabeca-demo nav{display:none}}
.icones{display:flex;align-items:center;gap:var(--e5);flex-wrap:wrap;
  border:1px solid var(--linha);border-radius:12px;padding:var(--e4) var(--e5);
  min-height:84px}
.ic{display:grid;place-items:center;border-radius:8px;background:var(--sup);
    color:var(--tinta)}
.ic32{width:48px;height:48px}
.ic16{width:30px;height:30px}
.separador{display:inline-flex;align-items:center;gap:7px;border:1px solid var(--linha);
  border-radius:8px 8px 0 0;padding:6px 12px;font-size:12.5px;color:var(--mudo)}

.comparar{margin-top:var(--e6)}
.par{display:flex;gap:var(--e7);align-items:flex-end;border:1px solid var(--linha);
     border-radius:12px;padding:var(--e5) var(--e6)}
.par span{display:grid;gap:8px;justify-items:center}
.par small{font-size:11.5px;color:var(--mudo)}

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
    <h1>Segunda ronda: mais desenho, turismo explícito</h1>
    <p>A primeira ronda era geometria mínima e ficou simples de mais, sem
    leitura de turismo. Esta vai ao contrário: símbolos com traço a sério e
    com referências de viagem que ninguém precisa que lhe expliquem.</p>
    <p>Cada uma vem em <strong>duas versões</strong>, e isso não é um extra —
    é como se faz. A <strong>completa</strong>, com o detalhe todo, para o
    cabeçalho, o papel timbrado e a carrinha. E a <strong>reduzida</strong>,
    redesenhada à mão com menos elementos e traço mais grosso, para 16 e
    32&nbsp;px: um símbolo detalhado encolhido a 16&nbsp;px vira uma nódoa,
    por isso desenha-se outro que se leia a essa escala e continue a ser
    reconhecível como o mesmo.</p>
  </div>
</header>

<main class="largura">
{{PROPOSTAS}}
</main>

<footer class="fim">
  <div class="largura">
    <p>Continuam todos a uma só cor. A paleta sai da marca depois de
    escolhida, e não ao contrário. Diz-me uma ou duas e afino-as à mão —
    proporções, espacejamento óptico, versão horizontal e empilhada — e
    entrego em SVG, PNG e favicon.</p>
  </div>
</footer>

</body>
</html>'''


def main():
    html = PAGINA.replace('{{PROPOSTAS}}', '\n'.join(bloco(p) for p in PROPOSTAS))
    for caminho in (os.path.join(RAIZ, 'logos2', 'index.html'),
                    os.path.join(RAIZ, 'logos2.html')):
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, 'w') as f:
            f.write(html)
        print('escrito: %s (%.0f KB)' % (caminho, os.path.getsize(caminho) / 1024))
    print('%d propostas' % len(PROPOSTAS))


if __name__ == '__main__':
    main()
