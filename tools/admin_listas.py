# -*- coding: utf-8 -*-
"""Duas listas da administracao: os operadores e as procuras.

/admin/operators/   quem vende aqui, em que estado, e com que comissao.
                    E tambem onde se muda a comissao de um caso especial
                    sem publicar codigo.

/admin/searches/    o que as pessoas escreveram na barra de procura e nao
                    encontraram. Esta e a lista de compras do
                    marketplace: diz em que cidade falta um operador, por
                    ordem de quantas pessoas o pediram. Nao e uma
                    estatistica para olhar — e a ordem de trabalhos de
                    quem anda a angariar.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pagina
import portal_base
from admin import NAV

CORES = pagina.CORES

CSS = """
.ops-f { display: flex; flex-wrap: wrap; gap: .6rem; margin-bottom: 1.1rem; }
.ops-f button {
  font: 500 .85rem/1 'Inter', system-ui, sans-serif;
  background: %(branco)s; border: 1px solid %(mudo)s; border-radius: 20px;
  color: %(texto)s; padding: .5rem .9rem; cursor: pointer;
}
.ops-f button[aria-pressed="true"] {
  background: %(tinta)s; color: %(papel)s; border-color: %(tinta)s;
}
.com-in { width: 5.5rem; }
.barra {
  height: .5rem; border-radius: 3px; background: %(cor)s; min-width: 3px;
}
.barra-f { background: %(risco)s; border-radius: 3px; }
.proc-q { font-weight: 600; color: %(tinta)s; }
.nada { font-style: italic; color: %(mudo)s; }
""" % CORES


JS_OPERADORES = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;
  var FILTRO = 'all';

  async function desenhar() {
    var c = document.getElementById('lista');
    c.innerHTML = '<p class="carrega">Loading…</p>';

    var q = ewt.sb.from('operators')
      .select('*, listings(id, status)').order('created_at', { ascending: false });
    if (FILTRO !== 'all') q = q.eq('status', FILTRO);
    var r = await q;

    if (r.error) {
      c.innerHTML = '<div class="aviso aviso-mal">'
        + ewt.escapar(ewt.legivel(r.error)) + '</div>';
      return;
    }
    var os = r.data || [];
    if (!os.length) {
      c.innerHTML = '<div class="vazio"><h3>Nothing here</h3>'
        + '<p>No operator matches that filter.</p></div>';
      return;
    }

    c.innerHTML = '<div class="tab-rolo" tabindex="0" role="region" '
      + 'aria-label="Table, scrolls sideways"><table class="tab">'
      + '<thead><tr><th>Operator</th><th>Where</th><th>Status</th>'
      + '<th>Tours</th><th>Commission</th><th></th></tr></thead><tbody>'
      + os.map(function (o) {
          var vivos = (o.listings || []).filter(function (l) {
            return l.status === 'live'; }).length;
          return '<tr data-o="' + o.id + '">'
            + '<td><b>' + ewt.escapar(o.name) + '</b><br>'
            + '<a href="mailto:' + ewt.escapar(o.email) + '">'
            + ewt.escapar(o.email) + '</a></td>'
            + '<td>' + ewt.escapar(o.city) + '<br>'
            + ewt.escapar(o.country) + '</td>'
            + '<td><span class="est est-' + o.status + '">' + o.status
            + '</span></td>'
            + '<td>' + vivos + ' live<br>' + (o.listings || []).length
            + ' total</td>'
            + '<td><input type="number" class="com-in" min="0" max="50" '
            + 'step="0.5" value="' + (Number(o.commission_rate) * 100)
            + '" data-com="' + o.id + '" aria-label="Commission percent for '
            + ewt.escapar(o.name) + '">%</td>'
            + '<td><div class="acoes">'
            + (o.status !== 'approved'
                ? '<button type="button" class="bt bt-s bt-pq" data-est="approved" '
                  + 'data-id="' + o.id + '">Approve</button>' : '')
            + (o.status !== 'suspended'
                ? '<button type="button" class="bt bt-mal bt-pq" data-est="suspended" '
                  + 'data-id="' + o.id + '">Suspend</button>' : '')
            + '</div></td></tr>';
        }).join('')
      + '</tbody></table></div>'
      + '<p class="aviso" id="av-ops" role="status" hidden></p>'
      + '<p class="lado-nota" style="margin-top:1rem">Suspending an '
      + 'operator takes their tours off the site immediately &mdash; the '
      + 'public view requires the operator to be approved. It does not '
      + 'delete anything.</p>';
  }

  async function mudarEstado(id, estado) {
    var campos = { status: estado };
    if (estado === 'approved') campos.approved_at = new Date().toISOString();
    var r = await ewt.sb.from('operators').update(campos).eq('id', id);
    if (r.error) { ewt.dizer('av-ops', ewt.legivel(r.error), 'mal'); return; }
    ewt.dizer('av-ops', 'Status changed.', 'bem');
    desenhar();
  }

  async function mudarComissao(id, pct) {
    var v = Number(pct);
    // A base recusa fora de 0–50%, mas dizer antes poupa uma mensagem
    // tecnica a quem se enganou a escrever.
    if (!isFinite(v) || v < 0 || v > 50) {
      ewt.dizer('av-ops', 'Commission has to be between 0 and 50 per cent.',
        'mal');
      return;
    }
    var r = await ewt.sb.from('operators')
      .update({ commission_rate: v / 100 }).eq('id', id);
    if (r.error) { ewt.dizer('av-ops', ewt.legivel(r.error), 'mal'); return; }
    ewt.dizer('av-ops', 'Commission for that operator is now ' + v + '%. '
      + 'It applies to what they are paid, from now on.', 'bem');
  }

  (async function () {
    var p = await ewt.exigir_entrada();
    if (!p) return;
    document.getElementById('carrega').hidden = true;
    if (!p.admin) {
      document.getElementById('conteudo').innerHTML =
        '<div class="vazio"><h3>This area is not yours</h3>'
        + '<a class="bt bt-p" href="/portal/">Go to the operator portal</a></div>';
      return;
    }
    document.getElementById('ad').hidden = false;

    document.getElementById('filtros').addEventListener('click', function (ev) {
      var b = ev.target.closest('button[data-f]');
      if (!b) return;
      FILTRO = b.getAttribute('data-f');
      [].slice.call(ev.currentTarget.querySelectorAll('button'))
        .forEach(function (x) {
          x.setAttribute('aria-pressed',
            x.getAttribute('data-f') === FILTRO ? 'true' : 'false');
        });
      desenhar();
    });

    var lista = document.getElementById('lista');
    lista.addEventListener('click', function (ev) {
      var b = ev.target.closest('button[data-est]');
      if (b) mudarEstado(b.getAttribute('data-id'), b.getAttribute('data-est'));
    });
    // A comissao grava-se ao sair do campo e nao a cada tecla: gravar a
    // cada tecla escrevia "2", "20", "205" na base pelo caminho.
    lista.addEventListener('change', function (ev) {
      var i = ev.target.closest('[data-com]');
      if (i) mudarComissao(i.getAttribute('data-com'), i.value);
    });

    await desenhar();
  })();
})();
"""


JS_PROCURAS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  (async function () {
    var p = await ewt.exigir_entrada();
    if (!p) return;
    document.getElementById('carrega').hidden = true;
    if (!p.admin) {
      document.getElementById('conteudo').innerHTML =
        '<div class="vazio"><h3>This area is not yours</h3>'
        + '<a class="bt bt-p" href="/portal/">Go to the operator portal</a></div>';
      return;
    }
    document.getElementById('ad').hidden = false;

    var r = await ewt.sb.from('search_queries')
      .select('q, results, city_match, country, created_at')
      .order('created_at', { ascending: false }).limit(2000);

    var c = document.getElementById('lista');
    if (r.error) {
      c.innerHTML = '<div class="aviso aviso-mal">'
        + ewt.escapar(ewt.legivel(r.error)) + '</div>';
      return;
    }
    var todas = r.data || [];
    if (!todas.length) {
      c.innerHTML = '<div class="vazio"><h3>Nobody has searched yet</h3>'
        + '<p>Once the site is live, every search that comes back empty '
        + 'lands here. That list is where the next operator should be.</p>'
        + '</div>';
      return;
    }

    // Agrupa-se pelo texto em minusculas: "dublin" e "Dublin" sao a
    // mesma procura e contar as duas em separado esconde a verdadeira.
    var g = {};
    todas.forEach(function (x) {
      var k = (x.q || '').toLowerCase();
      var o = g[k] || (g[k] = { q: x.q, n: 0, vazias: 0, ultima: x.created_at,
                                cidade: x.city_match, pais: x.country });
      o.n++;
      if (!x.results) o.vazias++;
      if (x.created_at > o.ultima) o.ultima = x.created_at;
    });

    var lista = Object.keys(g).map(function (k) { return g[k]; });
    var semNada = lista.filter(function (x) { return x.vazias === x.n; })
      .sort(function (a, b) { return b.n - a.n; });
    var maior = semNada.length ? semNada[0].n : 1;

    var comAlgo = lista.filter(function (x) { return x.vazias < x.n; })
      .sort(function (a, b) { return b.n - a.n; }).slice(0, 40);

    function tabela(xs, vazio) {
      if (!xs.length) return '<p class="nada">' + vazio + '</p>';
      return '<div class="tab-rolo" tabindex="0" role="region" '
      + 'aria-label="Table, scrolls sideways"><table class="tab">'
        + '<thead><tr><th>What they typed</th><th>Times</th>'
        + '<th>Matched</th><th>Last</th></tr></thead><tbody>'
        + xs.map(function (x) {
            var d = new Date(x.ultima);
            return '<tr><td class="proc-q">' + ewt.escapar(x.q) + '</td>'
              + '<td><div class="barra-f" style="width:7rem">'
              + '<div class="barra" style="width:'
              + Math.max(3, Math.round(x.n / maior * 100)) + '%"></div></div>'
              + x.n + '</td>'
              + '<td>' + (x.cidade ? ewt.escapar(x.cidade) : '<span class="nada">nothing</span>')
              + (x.pais ? '<br>' + ewt.escapar(x.pais) : '') + '</td>'
              + '<td>' + d.toLocaleDateString(undefined,
                  { day: 'numeric', month: 'short' }) + '</td></tr>';
          }).join('')
        + '</tbody></table></div>';
    }

    c.innerHTML =
      '<div class="resumo">'
      + '<div class="rs"><b>' + todas.length + '</b><span>searches recorded</span></div>'
      + '<div class="rs"><b>' + semNada.length + '</b><span>that never found anything</span></div>'
      + '<div class="rs"><b>' + lista.length + '</b><span>different things asked for</span></div>'
      + '</div>'
      + '<div class="cx"><p class="cx-t">Asked for and not here</p>'
      + '<p class="lado-nota" style="margin:0 0 1rem">In order of how '
      + 'many people asked. This is the list an operator should be '
      + 'recruited against, top first.</p>'
      + tabela(semNada, 'Everything people searched for was found.')
      + '</div>'
      + '<div class="cx"><p class="cx-t">Found something</p>'
      + tabela(comAlgo, 'No search has matched a tour yet.')
      + '</div>';
  })();
})();
"""


def corpo(titulo, intro, filtros=''):
    return '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">
    <p class="carrega" id="carrega">Loading&hellip;</p>
    <div id="ad" hidden>
      <div class="pt-cab">
        <h1>%(titulo)s</h1>
        <p>%(intro)s</p>
      </div>
      %(filtros)s
      <div id="lista"></div>
    </div>
  </div>
</main>''' % {'titulo': titulo, 'intro': intro, 'filtros': filtros}


FILTROS = '''<div class="ops-f" id="filtros" role="group"
     aria-label="Filter by status">
  <button type="button" data-f="all" aria-pressed="true">All</button>
  <button type="button" data-f="pending" aria-pressed="false">Pending</button>
  <button type="button" data-f="approved" aria-pressed="false">Approved</button>
  <button type="button" data-f="suspended" aria-pressed="false">Suspended</button>
</div>'''


def gerar():
    pagina.verificar_contraste()

    pagina.escrever(portal_base.envolver(
        titulo='Operators — Exclusive World Tours',
        corpo=corpo('Operators',
                    'Who sells here, and exactly what each of them pays. '
                    'Changing a commission here changes what that operator '
                    'receives from the next booking on &mdash; it does not '
                    'touch anything already paid.',
                    FILTROS),
        js=JS_OPERADORES, etiqueta='Administration',
        nav=NAV, atual='/admin/operators/', css_extra=CSS),
        'admin/operators/index.html')

    pagina.escrever(portal_base.envolver(
        titulo='Searches — Exclusive World Tours',
        corpo=corpo('Searches',
                    'What people typed into the search box. The ones that '
                    'found nothing are the useful ones: each is somebody '
                    'who wanted a private day in a city where we have '
                    'nobody.'),
        js=JS_PROCURAS, etiqueta='Administration',
        nav=NAV, atual='/admin/searches/', css_extra=CSS),
        'admin/searches/index.html')


if __name__ == '__main__':
    gerar()
