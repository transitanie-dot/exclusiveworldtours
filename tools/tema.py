# -*- coding: utf-8 -*-
"""As cores, os raios e o modo claro/escuro — num sitio so.

Porque e que isto e um modulo e nao CSS copiado nas duas cascas:

  o portal e o site tem de usar o MESMO verde. Enquanto as duas paletas
  viviam em ficheiros diferentes, comecavam iguais e acabavam diferentes
  — e a diferenca descobre-se tarde, numa pagina que ninguem estava a
  olhar. Agora ha um conjunto de fichas, nasce aqui, e quem quiser outro
  tom muda-o num lado.

O que esta aqui dentro:

  * TEMAS — as fichas, claro e escuro, com o mesmo nome nos dois. Uma
    regra que use `var(--sup)` funciona nos dois temas sem saber em qual
    esta. E isso que faz o modo escuro ser gratis em cada pagina nova.
  * CSS — o `:root`, o bloco do sistema, a sobreposicao do botao, e as
    regras de base (raios, reset dos botoes, o foco, os numeros a
    alinhar).
  * BOTAO / JS — o interruptor de tres estados.
  * verificar() — a porta: nenhuma pagina sai daqui com um par de cores
    que nao se le.

O modo escuro NAO e o claro com os cinzentos invertidos. O fundo escuro e
o proprio verde da marca levado ao quase-preto; um preto neutro nao teria
relacao nenhuma com o site, e um quase-preto tingido ao acaso le-se como
descuido.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from marca_base import contraste  # noqa: E402


# --------------------------------------------------------------- fichas
#
# O laranja aparece pouco de proposito. Na primeira tentativa pintava os
# dias reservados, os dias da semana escolhidos e os botoes todos ao
# mesmo tempo — e uma cor que esta em todo o lado deixa de apontar para
# nada.

CLARO = {
    'papel':     '#FAFAF9',   # o fundo da pagina
    'sup':       '#FFFFFF',   # uma superficie por cima do papel
    'sup_2':     '#F2F3F2',   # a seguinte, mais afundada
    'sup_3':     '#E9EBEA',   # filetes e separadores, quando fazem falta
    'tinta':     '#10312E',   # o texto
    'tinta_2':   '#3D524F',   # o texto secundario
    # 4.37:1 sobre o --sup-3 com o #5E706D, que reprovava. Uma ficha
    # tem de se ler sobre QUALQUER superficie do tema, senao e uma
    # armadilha para quem a usar no sitio errado daqui a um mes.
    'mudo':      '#586966',   # as dicas e os rotulos
    'acento':    '#A4501E',   # o ambar, para o que aponta
    'acento_f':  '#FBEFE7',   # o ambar como fundo
    'fechado':   '#98422C',   # o que esta fechado ou recusado
    'fechado_f': '#FBECE8',
    'bom':       '#1F6B4F',   # confirmado, pago, aprovado
    'bom_f':     '#E8F3ED',
    'sel':       '#10312E',   # superficie cheia (um dia escolhido)
    'sel_t':     '#FAFAF9',   # o texto que vai por cima dela
    'sombra':    '0 1px 2px rgba(16,49,46,.04), '
                 '0 8px 24px -12px rgba(16,49,46,.10)',
}

ESCURO = {
    'papel':     '#0C1413',
    'sup':       '#14201E',
    'sup_2':     '#1B2927',
    'sup_3':     '#243331',
    'tinta':     '#EAF1EF',
    'tinta_2':   '#B8C8C5',
    'mudo':      '#8C9F9C',   # ver a nota do claro
    'acento':    '#E88B4F',
    'acento_f':  '#2B1D14',
    'fechado':   '#E8907A',
    'fechado_f': '#2C1A17',
    'bom':       '#6FC79B',
    'bom_f':     '#12241C',
    # No escuro um "dia escolhido" nao pode ser pintado com a tinta: a
    # tinta aqui e o texto claro. E um verde a meio caminho, com o mesmo
    # texto claro por cima — foi isto que resolveu os dias que sairam
    # brancos na primeira versao escura.
    'sel':       '#2A4741',
    'sel_t':     '#EAF1EF',
    # Sombras sobre fundo escuro nao se veem e sujam as bordas. A
    # separacao no escuro faz-se com os tons de superficie.
    'sombra':    'none',
}

TEMAS = {'claro': CLARO, 'escuro': ESCURO}

# Os raios. Grandes de proposito — e a parte "redonda" do pedido.
RAIOS = {
    'r_xg': '28px',   # as superficies grandes
    'r_g':  '22px',   # os cartoes
    'r_m':  '14px',   # os dias do calendario, os campos
    'r_p':  '10px',   # as coisas pequenas
    'r_c':  '999px',  # as pastilhas e os botoes redondos
}


def _fichas(t):
    linhas = ['  --%s: %s;' % (k.replace('_', '-'), v)
              for k, v in t.items()]
    return '\n'.join(linhas)


def _raios():
    return '\n'.join('  --%s: %s;' % (k.replace('_', '-'), v)
                     for k, v in RAIOS.items())


# ------------------------------------------------------------------ CSS
#
# A ordem das tres regras nao e arbitraria:
#
#   1. `:root` — o claro, por omissao. Um navegador sem
#      prefers-color-scheme ve isto e esta bem servido.
#   2. `@media (prefers-color-scheme: dark)` com `:not([data-tema=claro])`
#      — o sistema decide, EXCEPTO se a pessoa forcou o claro.
#   3. `[data-tema=escuro]` — a pessoa forcou o escuro, e isto ganha
#      mesmo num sistema em modo claro.
#
# Sem o `:not()` do passo 2, forcar o claro num sistema escuro nao fazia
# nada: a regra do media query vinha depois e voltava a pintar tudo.

CSS = ('''
/* =================================================================
   AS FICHAS

   Ver tools/tema.py. Nao se escreve uma cor a mao numa folha de
   estilo deste projecto: escreve-se o nome de uma ficha. Uma cor
   escrita a mao e uma cor que nao muda quando o tema muda.
   ================================================================= */
:root {
''' + _fichas(CLARO) + '\n' + _raios() + '''
  color-scheme: light dark;
}

@media (prefers-color-scheme: dark) {
  :root:not([data-tema="claro"]) {
''' + _fichas(ESCURO) + '''
  }
}

:root[data-tema="escuro"] {
''' + _fichas(ESCURO) + '''
}

/* ------------------------------------------------------------ base */
*, *::before, *::after { box-sizing: border-box; }

html { -webkit-text-size-adjust: 100%; }

body {
  margin: 0;
  background: var(--papel);
  color: var(--tinta);
  /* Os numeros das tabelas e do calendario tem de alinhar em coluna.
     Era para isso que a primeira versao usava monoespacada — mas isso
     traz o aspecto de terminal com ele. `tnum` faz o trabalho e deixa
     o texto normal. */
  font-variant-numeric: tabular-nums;
  -webkit-font-smoothing: antialiased;
}

button, input, select, textarea { font: inherit; }

button {
  color: inherit; border: 0; background: none; cursor: pointer;
}

/* O foco e visivel em TODO o projecto, e e a mesma forma em todo o
   projecto. Quem navega por teclado nao devia ter de aprender duas
   linguagens entre o site e o portal. */
:focus-visible {
  outline: 2px solid var(--acento);
  outline-offset: 3px;
  border-radius: 6px;
}

/* Quem pediu menos movimento recebe menos movimento. Nao e uma
   gentileza: para algumas pessoas a animacao causa mal-estar fisico. */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .001ms !important;
    transition-duration: .001ms !important;
  }
}
''')


# --------------------------------------------------------------- botao
#
# Tres estados e nao dois: "como o sistema", "claro", "escuro". Um
# interruptor de dois estados obriga a pessoa a escolher uma vez para
# sempre, e depois o telefone muda para escuro a noite e a pagina fica a
# unica coisa branca no ecra.

BOTAO = '''
<button class="tm" type="button" aria-live="polite"
        aria-label="Theme: follow system">
  <span class="tm-i" aria-hidden="true"></span>
  <span class="tm-t">Auto</span>
</button>'''

CSS_BOTAO = '''
/* ----------------------------------------------------- o interruptor */
.tm {
  display: inline-flex; align-items: center; gap: .45rem;
  padding: .4rem .85rem .4rem .7rem;
  border-radius: var(--r-c);
  background: var(--sup-2); color: var(--tinta-2);
  font-size: .8rem; font-weight: 600; letter-spacing: .01em;
  transition: background .15s, color .15s;
}
.tm:hover { background: var(--sup-3); color: var(--tinta); }
.tm-i {
  width: 14px; height: 14px; border-radius: var(--r-c);
  background: var(--tinta-2);
  /* O icone e um circulo com uma mordida: cheio = escuro, vazio =
     claro, meio = automatico. Nao e um sol nem uma lua porque um sol
     e uma lua lado a lado perguntam "qual e o estado actual?" e esta
     forma responde. */
  box-shadow: inset -4px 0 0 0 var(--sup-2);
}
:root[data-tema="claro"] .tm-i { box-shadow: inset -9px 0 0 0 var(--sup-2); }
:root[data-tema="escuro"] .tm-i { box-shadow: none; }
'''

# O script e pequeno de proposito e nao depende de nada. Vai no <head>
# para o tema estar decidido antes da primeira pintura: posto no fim do
# <body>, uma pessoa com o escuro guardado via a pagina clara por um
# instante a cada visita.
JS_CABECA = '''
<script>
(function () {
  try {
    var g = localStorage.getItem('ewt-tema');
    if (g === 'claro' || g === 'escuro') {
      document.documentElement.setAttribute('data-tema', g);
    }
  } catch (e) {
    /* Em navegacao privada o localStorage estoura ao ser LIDO, nao so ao
       ser escrito. Sem este catch a pagina ficava sem tema nenhum — e o
       preco de falhar aqui e um botao que nao se lembra, nao uma pagina
       avariada. */
  }
})();
</script>'''

JS_BOTAO = '''
<script>
(function () {
  var ciclo = ['auto', 'claro', 'escuro'];
  var nomes = {auto: 'Auto', claro: 'Light', escuro: 'Dark'};
  var raiz = document.documentElement;

  function actual() {
    var a = raiz.getAttribute('data-tema');
    return (a === 'claro' || a === 'escuro') ? a : 'auto';
  }

  function por(v) {
    if (v === 'auto') {
      raiz.removeAttribute('data-tema');
      try { localStorage.removeItem('ewt-tema'); } catch (e) {}
    } else {
      raiz.setAttribute('data-tema', v);
      try { localStorage.setItem('ewt-tema', v); } catch (e) {}
    }
    Array.prototype.forEach.call(document.querySelectorAll('.tm'), function (b) {
      var t = b.querySelector('.tm-t');
      if (t) { t.textContent = nomes[v]; }
      b.setAttribute('aria-label', v === 'auto'
        ? 'Theme: follow system' : 'Theme: ' + nomes[v].toLowerCase());
    });
  }

  por(actual());

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest && ev.target.closest('.tm');
    if (!b) { return; }
    por(ciclo[(ciclo.indexOf(actual()) + 1) % ciclo.length]);
  });
})();
</script>'''


# ------------------------------------------------------------- a porta
#
# Os pares que tem de se ler, nos DOIS temas. Isto nao e uma lista de
# boas intencoes: a verificar() corre em cada geracao e mata o programa.
# Ja apanhou tres cores abaixo do minimo que eu tinha dado por boas a
# olho.

MINIMOS = [
    ('tinta sobre papel',     'tinta',   'papel',     4.5),
    ('tinta sobre superficie', 'tinta',  'sup',       4.5),
    ('tinta-2 sobre papel',   'tinta_2', 'papel',     4.5),
    ('mudo sobre papel',      'mudo',    'papel',     4.5),
    ('mudo sobre superficie', 'mudo',    'sup',       4.5),
    ('mudo sobre sup-2',      'mudo',    'sup_2',     4.5),
    ('mudo sobre sup-3',      'mudo',    'sup_3',     4.5),
    ('tinta-2 sobre sup-2',   'tinta_2', 'sup_2',     4.5),
    ('acento sobre papel',    'acento',  'papel',     4.5),
    ('acento sobre sup',      'acento',  'sup',       4.5),
    ('acento sobre o seu fundo', 'acento', 'acento_f', 4.5),
    ('fechado sobre papel',   'fechado', 'papel',     4.5),
    ('fechado sobre o seu fundo', 'fechado', 'fechado_f', 4.5),
    ('bom sobre papel',       'bom',     'papel',     4.5),
    ('bom sobre o seu fundo', 'bom',     'bom_f',     4.5),
    ('sel-t sobre sel',       'sel_t',   'sel',       4.5),
]


def verificar():
    maus = []
    for nome_tema, t in sorted(TEMAS.items()):
        for rotulo, frente, fundo, minimo in MINIMOS:
            r = contraste(t[frente], t[fundo])
            if r < minimo:
                maus.append('%s / %s: %.2f:1 (minimo %.1f)'
                            % (nome_tema, rotulo, r, minimo))
    if maus:
        sys.exit('Contraste insuficiente — nao gero paginas assim:\n  '
                 + '\n  '.join(maus))
    return True


if __name__ == '__main__':
    verificar()
    print('ok: %d pares verificados nos %d temas'
          % (len(MINIMOS), len(TEMAS)))
    for nome_tema, t in sorted(TEMAS.items()):
        print('\n--- %s ---' % nome_tema)
        for rotulo, frente, fundo, _m in MINIMOS:
            print('  %-28s %5.2f:1' % (rotulo, contraste(t[frente], t[fundo])))
