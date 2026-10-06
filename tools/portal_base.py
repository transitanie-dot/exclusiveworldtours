# -*- coding: utf-8 -*-
"""A casca das paginas do portal e da administracao.

O portal nao e o site. O site e feito para ser bonito, lido uma vez e
indexado; o portal e feito para ser usado todos os dias por alguem que
tem pressa, muitas vezes no telemovel, a fechar um dia as onze da noite.
Por isso tem a mesma marca e as mesmas cores, mas outra densidade: menos
fotografia, mais tabela, botoes grandes e o estado sempre visivel.

Tudo aqui dentro leva `noindex`: um painel de operador no Google nao
traz clientes, traz confusao.

-----------------------------------------------------------------------
O QUE MUDOU, E PORQUE
-----------------------------------------------------------------------
A primeira versao desta folha tinha uma moldura de 1px em todos os
cartoes, todos os campos, todas as pastilhas e todas as celulas de
tabela; raios de 3 a 6px; etiquetas em maiusculas com espacamento de
letra por cima de cada seccao; duas familias tipograficas; e vinte e
tantas cores escritas a mao em hexadecimal.

Dois problemas, e o segundo e o grave:

  1. o aspecto. Molduras em tudo e maiusculas espacadas sao a linguagem
     de um painel de administracao de 2014. O pedido era moderno,
     redondo e minimalista, e isto era o contrario das tres coisas.

  2. as cores escritas a mao NAO PODEM seguir um tema. Enquanto o
     `#FCEEEC` estava aqui dentro, nenhum modo escuro era possivel sem
     reescrever a folha — e por isso o modo escuro ia sendo adiado.

Agora:

  * zero molduras. A separacao e por TOM DE FUNDO e por espaco. Um
     cartao e uma superficie mais clara (ou mais escura) que o papel, nao
     um retangulo com um risco em volta.
  * raios grandes, das fichas `--r-*`.
  * uma familia so — a Inter, que ja estava servida do nosso dominio —
     com `tabular-nums` para os numeros alinharem. A Archivo em
     maiusculas espacadas sai: era ela que datava a pagina.
  * nenhuma cor escrita a mao. Todas vem do `tools/tema.py`, que tem as
     duas paletas e uma porta de contraste que mata a geracao se um par
     nao se ler.

Os NOMES das classes sao todos os mesmos. Isto e de proposito: ha oito
paginas do portal a usa-las, e uma mudanca de aspecto que obrigue a
mexer em oito ficheiros e uma mudanca que se faz a meio e fica a meio.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pagina
import ligacao
import tema
from marca import lockup
from marca_base import TINTAS

CORES = pagina.CORES

# ---------------------------------------------------------------- FICHAS
#
# As paginas do portal escrevem a cor pelo NOME — `%(tinta)s`, `%(mudo)s`
# — e ate aqui esses nomes resolviam para um hexadecimal fixo. Era isso
# que impedia o modo escuro: um `#0B2B2A` escrito dentro da folha de uma
# pagina nao muda quando o tema muda, e o titulo "Operator sign-in"
# aparecia verde-escuro sobre fundo verde-escuro.
#
# A correccao e de um sitio so. Os nomes passam a resolver para a FICHA
# correspondente em vez do hexadecimal, e as dez paginas do portal ficam
# a seguir o tema sem uma linha de CSS mexida. Cada pagina troca
# `CORES = pagina.CORES` por `CORES = portal_base.FICHAS` e mais nada.
#
# Os nomes antigos ficam todos, mesmo os que apontam para a mesma ficha:
# tirar um obrigava a rever dez ficheiros a procura de onde ele era
# usado, e o que se ganhava era uma linha a menos neste dicionario.
FICHAS = dict(CORES)
FICHAS.update({
    'tinta':       'var(--tinta)',
    'texto':       'var(--tinta-2)',    # o corpo de texto
    'mudo':        'var(--mudo)',       # legendas e dicas
    'papel':       'var(--papel)',
    'branco':      'var(--sup)',        # ja nao e branco: e a superficie
    'risco':       'var(--sup-3)',      # os filetes, quando restam
    'cor':         'var(--acento)',
    'cor_escura':  'var(--acento)',     # a ficha ja passa o contraste
    'cor_clara':   'var(--acento)',     #   nos dois temas; ver tema.py
})

# O topo do portal e escuro nos dois temas, e a marca foi desenhada com a
# tinta a fazer de cor escura. Sobre fundo escuro isso da escuro sobre
# escuro: o nome desaparecia e a capa do passaporte ficava um quadrado
# quase invisivel.
#
# A solucao nao e pintar o logotipo a mao: e usar o conjunto de tintas
# que ja existe para fundo escuro, onde a "tinta" passa a ser o claro. As
# variaveis vao no proprio topo, e nao na .marca, porque as da .marca
# ganhariam as herdadas e o palco escuro nao teria efeito nenhum.
ESCURO = TINTAS['escuro']


CSS = """
/* ------------------------------------------------------------ portal */
body.pt {
  background: var(--papel);
  font: 400 15px/1.5 'Inter', system-ui, -apple-system, sans-serif;
  color: var(--tinta);
}

/* ---------------------------------------------------------- o topo
   Uma barra so, sem a segunda barra de navegacao por baixo. Eram duas
   faixas a roubar 110px de altura antes de comecar o conteudo, no
   ecra onde ha menos altura para dar. */
.pt-topo {
  background: var(--tinta-topo); color: var(--papel-topo);
  position: sticky; top: 0; z-index: 40;
  /* as tintas de fundo escuro, para a marca aqui dentro */
  --papel: %(m_papel)s; --tinta: %(m_tinta)s; --cor: %(m_cor)s;
  --tinta-f: %(m_tinta_f)s; --cor-f: %(m_cor_f)s; --uma-f: %(m_uma_f)s;
}
/* O fundo do topo e o verde da marca e nao o quase-preto do palco
   escuro, por isso a capa do passaporte leva a cor do papel claro: e
   assim que ela se destaca, como se destaca no papel. */
.pt-topo .sim .p { fill: var(--papel-topo); }
.pt-topo .sim .pf { fill: %(m_cor_f)s; }
.pt-topo .sim .papel { fill: var(--tinta-topo); }
.pt-topo .sim .u { fill: var(--papel-topo); }
.pt-topo .marca-nome { color: var(--papel-topo); }
.pt-topo-i {
  display: flex; align-items: center; gap: .6rem 1rem;
  min-height: 62px; padding: .55rem 0;
  /* Dobra. Sem isto, a marca mais a etiqueta mais o email mais o botao
     de sair somavam 525px num ecra de 390 e a pagina toda rolava para o
     lado — no sitio onde o operador a vai mesmo abrir. */
  flex-wrap: wrap;
}
.pt-topo .marca { flex: 0 0 auto; }

/* A etiqueta era maiuscula, espacada e com moldura. Agora e uma
   pastilha de fundo translucido: diz a mesma coisa e nao grita. */
.pt-etiq {
  font-size: .76rem; font-weight: 600;
  color: var(--papel-topo); background: rgba(255,255,255,.14);
  padding: .3rem .7rem; border-radius: var(--r-c);
  white-space: nowrap;
}
.pt-topo-fim {
  margin-left: auto; display: flex; align-items: center; gap: .6rem;
  min-width: 0;
}
.pt-quem {
  font-size: .82rem; color: var(--papel-topo); opacity: .8;
  text-align: right; max-width: 14rem;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  min-width: 0;
}
/* Em ecra estreito o email e a primeira coisa a sair: quem esta a usar o
   telemovel sabe de quem e o telemovel. O botao de sair fica. */
@media (max-width: 620px) {
  .pt-quem { display: none; }
  .pt-topo-i { min-height: 56px; }
  .pt-etiq { font-size: .7rem; padding: .26rem .55rem; }
}
.pt-sair {
  font-size: .84rem; font-weight: 500;
  color: var(--papel-topo); background: rgba(255,255,255,.14);
  border-radius: var(--r-c); padding: .48rem .9rem;
}
.pt-sair:hover { background: rgba(255,255,255,.26); }

/* O interruptor de tema, dentro do topo: o topo e escuro nos dois
   temas, por isso o botao aqui nao pode usar as fichas de superficie. */
.pt-topo .tm {
  background: rgba(255,255,255,.14); color: var(--papel-topo);
}
.pt-topo .tm:hover { background: rgba(255,255,255,.26); }
.pt-topo .tm-i {
  background: var(--papel-topo);
  box-shadow: inset -4px 0 0 0 %(m_tinta)s;
}
:root[data-tema="claro"] .pt-topo .tm-i {
  box-shadow: inset -9px 0 0 0 %(m_tinta)s;
}
:root[data-tema="escuro"] .pt-topo .tm-i { box-shadow: none; }

/* ------------------------------------------------- a navegacao
   Pastilhas numa fita que rola, e nao separadores com um risco por
   baixo. A pastilha activa e cheia: ve-se de relance qual e, que e a
   unica pergunta que uma navegacao tem de responder. */
.pt-nav {
  background: var(--papel);
  overflow-x: auto; -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
}
.pt-nav::-webkit-scrollbar { display: none; }
.pt-nav-i { display: flex; gap: .3rem; padding: .7rem 0 .2rem; }
.pt-nav a {
  font-size: .89rem; font-weight: 500;
  color: var(--tinta-2); text-decoration: none;
  padding: .55rem .95rem; border-radius: var(--r-c);
  white-space: nowrap; transition: background .15s, color .15s;
}
.pt-nav a:hover { background: var(--sup-2); color: var(--tinta); }
.pt-nav a[aria-current="page"] {
  background: var(--sel); color: var(--sel-t); font-weight: 600;
}

.pt-corpo { padding: 1.5rem 0 5rem; }
.pt-cab { margin-bottom: 1.5rem; }
.pt-cab h1 {
  font-size: clamp(1.5rem, 3.4vw, 2.05rem); font-weight: 700;
  line-height: 1.12; letter-spacing: -.02em;
  color: var(--tinta); margin: 0 0 .35rem;
}
.pt-cab p {
  font-size: .96rem; line-height: 1.55;
  color: var(--mudo); margin: 0; max-width: 58ch;
}

/* ------------------------------------------------------------ cartoes */
.cx {
  background: var(--sup); border-radius: var(--r-g);
  padding: 1.4rem; margin-bottom: 1rem;
  box-shadow: var(--sombra);
}
/* O titulo do cartao era maiusculo, espacado e com um risco por baixo.
   Agora e so uma linha mais forte com espaco a seguir — o espaco separa
   tao bem como o risco e nao acrescenta nada ao ecra. */
.cx-t {
  font-size: .95rem; font-weight: 600; letter-spacing: -.01em;
  color: var(--tinta); margin: 0 0 1rem;
}
.cx-v { display: grid; gap: 1.1rem; }
@media (min-width: 900px) { .cx-2 { grid-template-columns: 1fr 1fr; } }

/* Visivel para um leitor de ecra, invisivel para o olho. Serve as listas
   onde repetir o rotulo cinco vezes seria ruido, mas onde um campo sem
   rotulo nenhum e um campo que ninguem consegue usar as cegas. */
.so-leitor {
  position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); clip-path: inset(50%%); white-space: nowrap;
}

/* --------------------------------------------------------- formulario */
.campo { margin-bottom: 1.1rem; }
.campo > label, .campo > .rot {
  display: block; margin-bottom: .4rem;
  font-size: .85rem; font-weight: 600; color: var(--tinta);
}
.campo .ajuda {
  display: block; margin-top: .35rem;
  font-size: .8rem; line-height: 1.45; color: var(--mudo);
}
/* Os campos nao levam moldura: levam uma superficie afundada. E a
   mesma leitura — "aqui escreve-se" — com menos tracos no ecra. A
   moldura so aparece no foco e no erro, que e quando ela informa. */
input[type=text], input[type=email], input[type=tel], input[type=url],
input[type=number], input[type=date], input[type=time], input[type=password],
select, textarea {
  width: 100%%; box-sizing: border-box;
  font-size: .96rem; line-height: 1.4; color: var(--tinta);
  background: var(--sup-2); border: 0; border-radius: var(--r-m);
  padding: .78rem .85rem;
  transition: background .15s, box-shadow .15s;
}
input::placeholder, textarea::placeholder { color: var(--mudo); }
input:hover, select:hover, textarea:hover { background: var(--sup-3); }
input:focus-visible, select:focus-visible, textarea:focus-visible {
  outline: 0; background: var(--sup);
  box-shadow: 0 0 0 2px var(--acento);
}
input[aria-invalid="true"], textarea[aria-invalid="true"] {
  box-shadow: 0 0 0 2px var(--fechado); background: var(--fechado-f);
}
textarea { min-height: 7rem; resize: vertical; }
.linha2 { display: grid; gap: 1rem; }
@media (min-width: 620px) { .linha2 { grid-template-columns: 1fr 1fr; } }
fieldset { border: 0; padding: 0; margin: 0 0 1.2rem; }
legend {
  padding: 0; margin-bottom: .7rem;
  font-size: 1.05rem; font-weight: 700; letter-spacing: -.015em;
  color: var(--tinta);
}
.obrig { color: var(--fechado); }

/* --------------------------------------------------- linhas repetiveis
   Uma lista onde se acrescentam e apagam linhas: escaloes de preco,
   paragens, perguntas, fotografias. Vive aqui e nao no editor porque
   mais do que uma pagina do portal a usa. */
.rep { display: grid; gap: .7rem; }
.rep-l {
  display: grid; gap: .6rem; align-items: start;
  padding: 1rem; border-radius: var(--r-m);
  background: var(--sup-2);
}
.rep-l > .campo { margin: 0; }
.rep-l input, .rep-l select, .rep-l textarea { background: var(--sup); }
.rep-l input:hover, .rep-l select:hover { background: var(--sup-3); }
.rep-x {
  justify-self: start;
  font-size: .82rem; font-weight: 600;
  color: var(--fechado); background: var(--fechado-f);
  border-radius: var(--r-c); padding: .48rem .85rem;
}
.rep-x:hover { filter: brightness(.96); }
/* O "acrescentar" era um retangulo tracejado. O tracejado diz
   "provisorio", e acrescentar uma linha nao e provisorio. */
.rep-mais {
  justify-self: start; margin-top: .3rem;
  font-size: .87rem; font-weight: 600;
  color: var(--tinta); background: var(--sup-2);
  border-radius: var(--r-c); padding: .6rem 1rem;
}
.rep-mais:hover { background: var(--sup-3); }

/* Os tours ligados a um recurso (um veiculo, um ponto de encontro). */
.v-tours { display: grid; gap: .4rem; margin-top: .3rem; }
.v-t {
  display: flex; align-items: flex-start; gap: .6rem;
  font-size: .9rem; line-height: 1.45; color: var(--tinta-2);
  padding: .6rem .7rem; border-radius: var(--r-p); background: var(--sup-2);
  cursor: pointer;
}
.v-t:hover { background: var(--sup-3); }
.v-t input {
  margin: .15rem 0 0; width: 1.1rem; height: 1.1rem; flex: none;
  accent-color: var(--acento);
}
.v-t span span { color: var(--mudo); }

/* ------------------------------------------------------------- avisos
   Sem a barra de 4px a esquerda: a cor do fundo ja diz de que tipo e o
   aviso, e a barra era uma segunda vez a dizer o mesmo. */
.aviso {
  margin: 1rem 0; padding: .9rem 1.05rem; border-radius: var(--r-m);
  font-size: .91rem; line-height: 1.55;
  background: var(--sup-2); color: var(--tinta-2);
}
.aviso-mal  { background: var(--fechado-f); color: var(--fechado); }
.aviso-bem  { background: var(--bom-f);     color: var(--bom); }
.aviso-nota { background: var(--acento-f);  color: var(--acento); }
.aviso strong { color: inherit; }

/* ------------------------------------------------------------ estados */
.est {
  display: inline-block; vertical-align: middle;
  font-size: .76rem; font-weight: 600;
  padding: .26rem .65rem; border-radius: var(--r-c); white-space: nowrap;
}
.est-pending  { background: var(--acento-f);  color: var(--acento); }
.est-approved { background: var(--bom-f);     color: var(--bom); }
.est-live     { background: var(--bom-f);     color: var(--bom); }
.est-rejected { background: var(--fechado-f); color: var(--fechado); }
.est-draft    { background: var(--sup-2);     color: var(--mudo); }
.est-paused   { background: var(--sup-2);     color: var(--mudo); }
.est-new      { background: var(--acento-f);  color: var(--acento); }

/* ------------------------------------------------------------ tabelas */
.tab-rolo { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.tab-rolo:focus-visible { outline: 2px solid var(--acento); outline-offset: 2px; }
table.tab { width: 100%%; border-collapse: collapse; }
table.tab th, table.tab td {
  text-align: left; padding: .85rem .9rem; vertical-align: top;
  font-size: .91rem; line-height: 1.45; color: var(--tinta-2);
}
/* O cabecalho da tabela era maiusculo e espacado com um risco de 2px.
   Agora e texto normal mais claro, e a linha que separa e a propria
   mudanca de fundo das linhas abaixo. */
table.tab th {
  font-size: .8rem; font-weight: 600; color: var(--mudo);
  white-space: nowrap; padding-bottom: .5rem;
}
table.tab tbody tr { background: var(--sup); }
table.tab tbody tr:nth-child(even) { background: var(--sup-2); }
table.tab tbody tr:first-child td:first-child { border-top-left-radius: var(--r-m); }
table.tab tbody tr:first-child td:last-child { border-top-right-radius: var(--r-m); }
table.tab tbody tr:last-child td:first-child { border-bottom-left-radius: var(--r-m); }
table.tab tbody tr:last-child td:last-child { border-bottom-right-radius: var(--r-m); }
table.tab a { color: var(--acento); font-weight: 500; }

/* -------------------------------------------------------------- vazio
   O retangulo tracejado sai. Um ecra vazio nao e um erro nem um
   espaco por preencher: e um estado normal no primeiro dia de uso. */
.vazio {
  padding: 2.6rem 1.4rem; text-align: center;
  border-radius: var(--r-g); background: var(--sup-2);
}
.vazio h3 {
  font-size: 1.1rem; font-weight: 700; letter-spacing: -.015em;
  color: var(--tinta); margin: 0 0 .45rem;
}
.vazio p {
  font-size: .94rem; line-height: 1.55;
  color: var(--mudo); margin: 0 auto 1.2rem; max-width: 44ch;
}

/* -------------------------------------------------------------- acoes */
.acoes { display: flex; flex-wrap: wrap; gap: .6rem; align-items: center; }
.bt {
  font-size: .93rem; font-weight: 600;
  padding: .78rem 1.3rem; border-radius: var(--r-c); border: 0;
  cursor: pointer; text-decoration: none; display: inline-block;
  transition: background .15s, filter .15s;
}
.bt-p { background: var(--sel); color: var(--sel-t); }
.bt-p:hover { filter: brightness(1.12); }
.bt-s { background: var(--sup-2); color: var(--tinta); }
.bt-s:hover { background: var(--sup-3); }
.bt-mal { background: var(--fechado-f); color: var(--fechado); }
.bt-mal:hover { filter: brightness(.96); }
.bt[disabled] { opacity: .5; cursor: not-allowed; filter: none; }
.bt-pq { font-size: .84rem; padding: .52rem .9rem; }

/* --------------------------------------------------------- a carregar */
.carrega {
  padding: 2.5rem 0; text-align: center;
  font-size: .93rem; color: var(--mudo);
}
"""


def css():
    """A folha do portal: as fichas do tema, as regras de base, o
    interruptor, e o que e do portal.

    A ordem importa. As fichas tem de vir antes de qualquer regra que
    use `var(--...)`, e as regras do portal tem de vir depois das de
    base para poderem ganhar-lhes."""
    v = dict(CORES)
    v.update({'m_' + k: x for k, x in ESCURO.items()})
    # O topo e escuro nos DOIS temas. Por isso nao usa `--tinta` e
    # `--papel`, que trocam de valor quando o tema troca: tem fichas
    # proprias, fixas. Sem isto, no modo escuro o topo ficava claro e
    # a marca desaparecia outra vez — o problema que esta casca ja
    # tinha resolvido uma vez para fundo escuro.
    fixas = """
:root {
  --tinta-topo: %(tinta)s;
  --papel-topo: %(papel)s;
}
""" % {'tinta': CORES['tinta'], 'papel': CORES['papel']}
    return tema.CSS + fixas + tema.CSS_BOTAO + (CSS % v)


def topo(etiqueta, nav=None, atual=''):
    """O topo do portal: marca, para que serve esta area, e quem esta.

    O email de quem entrou fica sempre a vista. Num portal onde uma
    pessoa pode gerir mais do que uma empresa, nao saber em nome de quem
    se esta a mexer e como se perdem dias no calendario errado."""
    nav_html = ''
    if nav:
        nav_html = '''
  <nav class="pt-nav" aria-label="Portal">
    <div class="folha pt-nav-i">%s</div>
  </nav>''' % '\n'.join(
            '<a href="%s"%s>%s</a>'
            % (href, ' aria-current="page"' if href == atual else '',
               pagina.e(nome))
            for nome, href in nav)

    return '''<header class="pt-topo">
  <div class="folha pt-topo-i">
    %(marca)s
    <span class="pt-etiq">%(etiq)s</span>
    <div class="pt-topo-fim">
      <span class="pt-quem" id="quem"></span>
      %(tema)s
      <button type="button" class="pt-sair" id="sair" hidden>Sign out</button>
    </div>
  </div>
</header>%(nav)s''' % {'marca': lockup(34), 'etiq': pagina.e(etiqueta),
                       'tema': tema.BOTAO, 'nav': nav_html}


JS_CASCA = r"""
(function () {
  // O email e o botao de sair, iguais em todas as paginas do portal.
  if (!window.ewt || window.ewt.avariado) {
    var c = document.getElementById('conteudo');
    if (c) {
      c.innerHTML = '<div class="aviso aviso-mal">The portal could not '
        + 'load. Reload the page; if it keeps happening, write to us.</div>';
    }
    return;
  }
  var b = document.getElementById('sair');
  if (b) {
    b.addEventListener('click', function () { ewt.sair(); });
  }
  ewt.utilizador().then(function (u) {
    var q = document.getElementById('quem');
    if (u && q) { q.textContent = u.email; }
    if (u && b) { b.hidden = false; }
    // A navegacao do portal leva a paginas que exigem sessao. Mostra-la
    // a quem ainda nao entrou era oferecer quatro ligacoes que todas
    // devolvem a pessoa a esta mesma pagina.
    var nav = document.querySelector('.pt-nav');
    if (nav && !u) { nav.hidden = true; }
  });
})();
"""


def envolver(titulo, corpo, js='', etiqueta='Operator portal',
             nav=None, atual='', css_extra=''):
    """A pagina do portal, inteira.

    Reaproveita a `envolver` do site para nao haver dois sitios a
    decidir como e a cabeca de uma pagina — mas acrescenta a classe `pt`
    no body, que e o que liga o CSS do portal."""
    html = pagina.envolver(
        titulo=titulo,
        descricao='Operator area of Exclusive World Tours.',
        css_pagina=css() + css_extra,
        corpo=topo(etiqueta, nav, atual) + corpo,
        js=js + JS_CASCA,
        noindex=True)

    # O body do portal tem de levar a classe, e os scripts da base tem de
    # vir antes do nosso: a biblioteca primeiro, a ligacao depois.
    html = html.replace('<body>', '<body class="pt">')

    # O script do tema vai no <head>, antes de tudo, e nao no fim do
    # <body>: posto no fim, uma pessoa com o escuro guardado via a
    # pagina clara por um instante a cada visita. O do botao vai no fim,
    # porque precisa do botao ja existir.
    html = html.replace('</head>',
                        tema.JS_CABECA + ligacao.SCRIPTS + '\n</head>')
    html = html.replace('</body>', tema.JS_BOTAO + '\n</body>')
    return html
