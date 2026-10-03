# -*- coding: utf-8 -*-
"""A casca das paginas do portal e da administracao.

O portal nao e o site. O site e feito para ser bonito, lido uma vez e
indexado; o portal e feito para ser usado todos os dias por alguem que
tem pressa, muitas vezes no telemovel, a fechar um dia as onze da noite.
Por isso tem a mesma marca e as mesmas cores, mas outra densidade: menos
fotografia, mais tabela, botoes grandes e o estado sempre visivel.

Tudo aqui dentro leva `noindex`: um painel de operador no Google nao
traz clientes, traz confusao.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pagina
import ligacao
from marca import lockup

CORES = pagina.CORES


CSS = """
/* ------------------------------------------------------------ portal */
body.pt { background: %(papel)s; }

.pt-topo {
  background: %(tinta)s; color: %(papel)s;
  border-bottom: 3px solid %(cor)s;
  position: sticky; top: 0; z-index: 40;
}
.pt-topo-i {
  display: flex; align-items: center; gap: .6rem 1rem;
  min-height: 60px; padding: .5rem 0;
  /* Dobra. Sem isto, a marca mais a etiqueta mais o email mais o botao
     de sair somavam 525px num ecra de 390 e a pagina toda rolava para o
     lado — no sitio onde o operador a vai mesmo abrir. */
  flex-wrap: wrap;
}
.pt-topo .marca { flex: 0 0 auto; }
.pt-etiq {
  font: 600 .68rem/1 'Archivo', system-ui, sans-serif;
  letter-spacing: .14em; text-transform: uppercase;
  color: %(cor_clara)s; padding: .3rem .5rem;
  border: 1px solid %(cor_clara)s; border-radius: 3px;
  white-space: nowrap;
}
.pt-topo-fim {
  margin-left: auto; display: flex; align-items: center; gap: .9rem;
  min-width: 0;
}
.pt-quem {
  font: 400 .8rem/1.3 'Inter', system-ui, sans-serif;
  color: %(papel)s; opacity: .85; text-align: right;
  max-width: 14rem; overflow: hidden; text-overflow: ellipsis;
  white-space: nowrap; min-width: 0;
}
/* Em ecra estreito o email e a primeira coisa a sair: quem esta a usar o
   telemovel sabe de quem e o telemovel. O botao de sair fica. */
@media (max-width: 560px) {
  .pt-quem { display: none; }
  .pt-topo-i { min-height: 54px; }
  .pt-etiq { font-size: .62rem; padding: .26rem .4rem; }
}
.pt-sair {
  font: 500 .82rem/1 'Inter', system-ui, sans-serif;
  color: %(papel)s; background: none;
  border: 1px solid rgba(255,255,255,.4); border-radius: 4px;
  padding: .5rem .8rem; cursor: pointer;
}
.pt-sair:hover { border-color: %(papel)s; }

.pt-nav {
  background: %(branco)s; border-bottom: 1px solid %(risco)s;
  overflow-x: auto; -webkit-overflow-scrolling: touch;
}
.pt-nav-i { display: flex; gap: 0; }
.pt-nav a {
  font: 500 .88rem/1 'Inter', system-ui, sans-serif;
  color: %(mudo)s; text-decoration: none;
  padding: .95rem 1.1rem; border-bottom: 3px solid transparent;
  white-space: nowrap;
}
.pt-nav a:hover { color: %(tinta)s; background: %(papel)s; }
.pt-nav a[aria-current="page"] {
  color: %(tinta)s; border-bottom-color: %(cor)s; font-weight: 600;
}

.pt-corpo { padding: 1.6rem 0 4rem; }
.pt-cab { margin-bottom: 1.4rem; }
.pt-cab h1 {
  font: 700 clamp(1.4rem, 3vw, 1.9rem)/1.15 'Archivo', system-ui, sans-serif;
  color: %(tinta)s; margin: 0 0 .3rem;
}
.pt-cab p {
  font: 400 .95rem/1.5 'Inter', system-ui, sans-serif;
  color: %(mudo)s; margin: 0; max-width: 56ch;
}

/* ------------------------------------------------------------- cartoes */
.cx {
  background: %(branco)s; border: 1px solid %(risco)s; border-radius: 6px;
  padding: 1.2rem; margin-bottom: 1.1rem;
}
.cx-t {
  font: 600 .72rem/1 'Archivo', system-ui, sans-serif;
  letter-spacing: .12em; text-transform: uppercase;
  color: %(mudo)s; margin: 0 0 .9rem;
  padding-bottom: .6rem; border-bottom: 1px solid %(risco)s;
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

/* ------------------------------------------------------------ formulario */
.campo { margin-bottom: 1rem; }
.campo > label, .campo > .rot {
  display: block; margin-bottom: .35rem;
  font: 600 .82rem/1.3 'Inter', system-ui, sans-serif; color: %(tinta)s;
}
.campo .ajuda {
  display: block; margin-top: .3rem;
  font: 400 .78rem/1.45 'Inter', system-ui, sans-serif; color: %(mudo)s;
}
input[type=text], input[type=email], input[type=tel], input[type=url],
input[type=number], input[type=date], input[type=time], select, textarea {
  width: 100%%; box-sizing: border-box;
  font: 400 .95rem/1.4 'Inter', system-ui, sans-serif; color: %(tinta)s;
  background: %(branco)s; border: 1px solid %(mudo)s; border-radius: 4px;
  padding: .66rem .7rem;
}
input:focus-visible, select:focus-visible, textarea:focus-visible {
  outline: 3px solid %(cor)s; outline-offset: 1px; border-color: %(tinta)s;
}
input[aria-invalid="true"], textarea[aria-invalid="true"] {
  border-color: #B3261E; border-width: 2px;
}
textarea { min-height: 6.5rem; resize: vertical; }
.linha2 { display: grid; gap: 1rem; }
@media (min-width: 620px) { .linha2 { grid-template-columns: 1fr 1fr; } }
fieldset { border: 0; padding: 0; margin: 0 0 1rem; }
legend {
  padding: 0; margin-bottom: .6rem;
  font: 700 1.02rem/1.2 'Archivo', system-ui, sans-serif; color: %(tinta)s;
}
.obrig { color: #8C1D18; }

/* --------------------------------------------------------------- avisos */
.aviso {
  margin: .9rem 0; padding: .8rem .9rem; border-radius: 4px;
  font: 400 .9rem/1.5 'Inter', system-ui, sans-serif;
  border-left: 4px solid %(mudo)s; background: %(papel)s; color: %(texto)s;
}
.aviso-mal { border-left-color: #8C1D18; background: #FCEEEC; color: #5F1512; }
.aviso-bem { border-left-color: #1B5E20; background: #EDF5EE; color: #14401A; }
.aviso-nota { border-left-color: %(cor)s; background: #FBF2EB; color: %(texto)s; }

/* --------------------------------------------------------------- estados */
.est {
  display: inline-block; vertical-align: middle;
  font: 600 .68rem/1 'Archivo', system-ui, sans-serif;
  letter-spacing: .1em; text-transform: uppercase;
  padding: .32rem .5rem; border-radius: 3px; white-space: nowrap;
}
.est-pending  { background: #FBF2EB; color: #7A3E12; border: 1px solid #D9A77C; }
.est-approved { background: #EDF5EE; color: #14401A; border: 1px solid #8BB68F; }
.est-live     { background: #EDF5EE; color: #14401A; border: 1px solid #8BB68F; }
.est-rejected { background: #FCEEEC; color: #5F1512; border: 1px solid #D79C96; }
.est-draft    { background: %(papel)s; color: %(texto)s; border: 1px solid %(mudo)s; }
.est-paused   { background: %(papel)s; color: %(texto)s; border: 1px solid %(mudo)s; }
.est-new      { background: #FBF2EB; color: #7A3E12; border: 1px solid #D9A77C; }

/* --------------------------------------------------------------- tabelas */
.tab-rolo { overflow-x: auto; -webkit-overflow-scrolling: touch; }
.tab-rolo:focus-visible { outline: 3px solid %(cor)s; outline-offset: 2px; }
table.tab { width: 100%%; border-collapse: collapse; }
table.tab th, table.tab td {
  text-align: left; padding: .7rem .8rem;
  border-bottom: 1px solid %(risco)s; vertical-align: top;
  font: 400 .9rem/1.45 'Inter', system-ui, sans-serif; color: %(texto)s;
}
table.tab th {
  font: 600 .72rem/1 'Archivo', system-ui, sans-serif;
  letter-spacing: .1em; text-transform: uppercase; color: %(mudo)s;
  border-bottom: 2px solid %(risco)s; white-space: nowrap;
}
table.tab tr:last-child td { border-bottom: 0; }
table.tab a { color: %(cor_escura)s; font-weight: 500; }

/* ---------------------------------------------------------------- vazio */
.vazio {
  padding: 2.2rem 1.2rem; text-align: center;
  border: 2px dashed %(risco)s; border-radius: 6px; background: %(branco)s;
}
.vazio h3 {
  font: 700 1.05rem/1.25 'Archivo', system-ui, sans-serif;
  color: %(tinta)s; margin: 0 0 .4rem;
}
.vazio p {
  font: 400 .92rem/1.55 'Inter', system-ui, sans-serif;
  color: %(mudo)s; margin: 0 auto 1rem; max-width: 42ch;
}

/* --------------------------------------------------------------- acoes */
.acoes { display: flex; flex-wrap: wrap; gap: .6rem; align-items: center; }
.bt {
  font: 600 .92rem/1 'Inter', system-ui, sans-serif;
  padding: .75rem 1.15rem; border-radius: 4px; border: 1px solid transparent;
  cursor: pointer; text-decoration: none; display: inline-block;
}
.bt-p { background: %(tinta)s; color: %(papel)s; }
.bt-p:hover { background: %(texto)s; }
.bt-s { background: %(branco)s; color: %(tinta)s; border-color: %(mudo)s; }
.bt-s:hover { border-color: %(tinta)s; background: %(papel)s; }
.bt-mal { background: %(branco)s; color: #8C1D18; border-color: #B3261E; }
.bt-mal:hover { background: #FCEEEC; }
.bt[disabled] { opacity: .55; cursor: not-allowed; }
.bt-pq { font-size: .82rem; padding: .5rem .7rem; }

/* --------------------------------------------------------- a carregar */
.carrega {
  padding: 2rem 0; text-align: center;
  font: 400 .92rem/1.5 'Inter', system-ui, sans-serif; color: %(mudo)s;
}
"""


def css():
    return CSS % CORES


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
      <button type="button" class="pt-sair" id="sair" hidden>Sign out</button>
    </div>
  </div>
</header>%(nav)s''' % {'marca': lockup(34), 'etiq': pagina.e(etiqueta),
                       'nav': nav_html}


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
    html = html.replace('</head>', ligacao.SCRIPTS + '\n</head>')
    return html
