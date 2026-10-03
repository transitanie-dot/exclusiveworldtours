# -*- coding: utf-8 -*-
"""O calendario do operador.

Esta e a pagina que mais vezes vai ser aberta, e quase sempre no
telemovel, muitas vezes tarde. Por isso nao passa por revisao nenhuma:
abrir e fechar dias e imediato. Um calendario que esperasse pela minha
aprovacao mostrava disponibilidade falsa durante horas, e disponibilidade
falsa nao e um atraso — e uma reserva que vai ter de ser cancelada.

Fechar um dia e tocar nele. Sem formulario, sem gravar, sem confirmar:
um toque, fica fechado, e a mudanca esta na base antes de o dedo sair do
ecra. O "undo" e tocar outra vez.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pagina
import portal_base
from portal import NAV

CORES = pagina.CORES

CSS = """
.cal-topo {
  display: flex; flex-wrap: wrap; gap: .8rem; align-items: center;
  margin-bottom: 1.2rem;
}
.cal-topo select { max-width: 22rem; }
.cal-nav { display: flex; align-items: center; gap: .5rem; margin-left: auto; }
.cal-mes {
  font: 700 1.05rem/1 'Archivo', system-ui, sans-serif; color: %(tinta)s;
  min-width: 10.5rem; text-align: center;
}
.cal-b {
  width: 2.6rem; height: 2.6rem; border-radius: 4px; cursor: pointer;
  background: %(branco)s; border: 1px solid %(mudo)s; color: %(tinta)s;
  font: 600 1rem/1 'Inter', system-ui, sans-serif;
}
.cal-b:hover { border-color: %(tinta)s; background: %(papel)s; }
.cal-b[disabled] { opacity: .4; cursor: not-allowed; }

.grelha {
  display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px;
  background: %(risco)s; border: 1px solid %(risco)s; border-radius: 6px;
  padding: 3px; margin-bottom: 1rem;
}
.gd {
  background: %(branco)s; text-align: center;
  font: 600 .66rem/1 'Archivo', system-ui, sans-serif;
  letter-spacing: .08em; text-transform: uppercase; color: %(mudo)s;
  padding: .55rem 0;
}
.dia {
  position: relative; background: %(branco)s; border: 0; cursor: pointer;
  aspect-ratio: 1 / 1; min-height: 2.9rem; padding: .25rem;
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: .1rem;
  font: 500 .95rem/1 'Inter', system-ui, sans-serif; color: %(tinta)s;
  font-variant-numeric: tabular-nums;
}
.dia:hover:not([disabled]) { outline: 2px solid %(cor)s; outline-offset: -2px; }
.dia:focus-visible { outline: 3px solid %(cor)s; outline-offset: -3px; z-index: 2; }
.dia-v { visibility: hidden; cursor: default; }
.dia[disabled] { background: %(papel)s; color: %(mudo)s; cursor: not-allowed; }
.dia-fora { opacity: .45; }
.dia .p {
  font: 600 .6rem/1 'Inter', system-ui, sans-serif; color: %(cor_escura)s;
}
/* Fechado e vendido nao se distinguem so pela cor: um tem risco, o outro
   tem um ponto. Quem nao distingue cores tem de ver a diferenca. */
.dia-closed {
  background: #F2EFEC; color: %(mudo)s; text-decoration: line-through;
  text-decoration-thickness: 2px;
}
.dia-sold {
  background: #FBF2EB; color: #7A3E12;
}
.dia-sold::after {
  content: ''; position: absolute; bottom: .3rem; left: 50%%;
  transform: translateX(-50%%);
  width: 5px; height: 5px; border-radius: 50%%; background: #7A3E12;
}
.dia-hoje { box-shadow: inset 0 0 0 2px %(tinta)s; }

.leg {
  display: flex; flex-wrap: wrap; gap: .4rem 1.1rem; margin: 0 0 1.4rem;
  font: 400 .84rem/1.5 'Inter', system-ui, sans-serif; color: %(mudo)s;
}
.leg span { display: flex; align-items: center; gap: .4rem; }
.leg i {
  width: 1.1rem; height: 1.1rem; border-radius: 3px; border: 1px solid %(risco)s;
  display: inline-block;
}
.leg .i-open { background: %(branco)s; }
.leg .i-closed { background: #F2EFEC; }
.leg .i-sold { background: #FBF2EB; }

.cal-ajuda {
  font: 400 .88rem/1.55 'Inter', system-ui, sans-serif; color: %(texto)s;
  background: %(branco)s; border-left: 4px solid %(cor)s;
  border-radius: 4px; padding: .9rem 1rem; margin-bottom: 1.3rem;
}
""" % CORES


JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  var DIAS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  var E = { anuncios: [], tour: null, mes: null, dados: {}, aEscrever: 0 };

  function iso(d) { return ewt.iso(d); }
  function primeiro(d) { return new Date(d.getFullYear(), d.getMonth(), 1); }
  function nomeMes(d) {
    return d.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
  }

  // ---------------------------------------------------------- desenhar
  function desenhar() {
    var g = document.getElementById('grelha');
    var mes = E.mes;
    document.getElementById('cal-mes').textContent = nomeMes(mes);

    var hoje = new Date(); hoje.setHours(0,0,0,0);
    var html = DIAS.map(function (d) {
      return '<div class="gd" aria-hidden="true">' + d + '</div>';
    }).join('');

    // A semana comeca na segunda: e assim que um operador europeu
    // pensa numa semana de trabalho.
    var inicio = primeiro(mes);
    var desvio = (inicio.getDay() + 6) % 7;
    for (var i = 0; i < desvio; i++) {
      html += '<span class="dia dia-v" aria-hidden="true"></span>';
    }

    var ultimo = new Date(mes.getFullYear(), mes.getMonth() + 1, 0).getDate();
    for (var n = 1; n <= ultimo; n++) {
      var d = new Date(mes.getFullYear(), mes.getMonth(), n);
      var k = iso(d);
      var r = E.dados[k] || { status: 'open' };
      var passado = d < hoje;
      var cls = 'dia';
      if (r.status === 'closed')   cls += ' dia-closed';
      if (r.status === 'sold_out') cls += ' dia-sold';
      if (iso(hoje) === k)         cls += ' dia-hoje';

      var legivel = d.toLocaleDateString(undefined,
        { weekday: 'long', day: 'numeric', month: 'long' });
      var estado = passado ? 'in the past'
        : r.status === 'closed' ? 'closed'
        : r.status === 'sold_out' ? 'sold out' : 'open';

      html += '<button type="button" class="' + cls + '" data-d="' + k + '"'
        + (passado ? ' disabled' : '')
        + ' aria-label="' + legivel + ', ' + estado + '">'
        + n
        + (r.price_override ? '<span class="p">€' + ewt.euros(r.price_override) + '</span>' : '')
        + '</button>';
    }
    g.innerHTML = html;

    var anterior = primeiro(new Date());
    document.getElementById('cal-ant').disabled = (mes <= anterior);
  }

  // ------------------------------------------------------------- dados
  async function carregar() {
    if (!E.tour) return;
    var de = iso(primeiro(E.mes));
    var ate = iso(new Date(E.mes.getFullYear(), E.mes.getMonth() + 1, 0));

    var r = await ewt.sb.from('availability')
      .select('day, status, price_override, seats_left')
      .eq('listing_id', E.tour).gte('day', de).lte('day', ate);

    if (r.error) {
      ewt.dizer('av-cal', ewt.legivel(r.error), 'mal');
      return;
    }
    E.dados = {};
    (r.data || []).forEach(function (x) { E.dados[x.day] = x; });
    desenhar();
  }

  // -------------------------------------------------------------- tocar
  //
  // Aberto -> fechado -> esgotado -> aberto. Tres estados num toque e
  // nao um menu: no telemovel, um menu por dia e vinte toques para
  // fechar uma semana.
  var SEGUINTE = { open: 'closed', closed: 'sold_out', sold_out: 'open' };

  async function tocar(dia) {
    var agora = (E.dados[dia] && E.dados[dia].status) || 'open';
    var novo = SEGUINTE[agora];

    // Mostra-se logo a mudanca e corrige-se depois se a base recusar.
    // Esperar pela rede antes de pintar o dia faz o calendario parecer
    // avariado numa ligacao lenta.
    E.dados[dia] = Object.assign({}, E.dados[dia] || {}, { day: dia, status: novo });
    desenhar();

    E.aEscrever++;
    sinal();
    var r = await ewt.sb.rpc('marcar_dias', {
      p_listing: E.tour, p_dias: [dia], p_status: novo
    });
    E.aEscrever--;
    sinal();

    if (r.error) {
      ewt.dizer('av-cal', ewt.legivel(r.error), 'mal');
      await carregar();   // volta-se ao que a base diz, nao ao que eu achava
    } else {
      ewt.dizer('av-cal', '', '');
    }
  }

  function sinal() {
    var s = document.getElementById('sinal-cal');
    if (!s) return;
    s.textContent = E.aEscrever > 0 ? 'Saving…' : 'Saved.';
    s.hidden = false;
  }

  // ----------------------------------------------------------- arranque
  (async function () {
    var pp = await ewt.exigir_entrada();
    if (!pp) return;

    var r = await ewt.sb.from('listings')
      .select('id, slug, status, city, country').order('created_at');
    var anuncios = r.data || [];

    document.getElementById('carrega').hidden = true;

    if (!anuncios.length) {
      document.getElementById('conteudo').innerHTML =
        '<div class="vazio"><h3>No tours to put on a calendar</h3>'
        + '<p>Add a tour first; the calendar belongs to a tour, not to '
        + 'your account as a whole.</p>'
        + '<a class="bt bt-p" href="/portal/listing/">Add a tour</a></div>';
      return;
    }

    document.getElementById('cal').hidden = false;

    // Os titulos vem das versoes; a tabela `listings` so tem o slug.
    var vv = await ewt.sb.from('listing_versions')
      .select('listing_id, version, payload')
      .in('listing_id', anuncios.map(function (a) { return a.id; }))
      .order('version', { ascending: false });
    var titulo = {};
    (vv.data || []).forEach(function (x) {
      if (!titulo[x.listing_id] && x.payload && x.payload.title) {
        titulo[x.listing_id] = x.payload.title;
      }
    });

    var sel = document.getElementById('qual');
    sel.innerHTML = anuncios.map(function (a) {
      return '<option value="' + a.id + '">'
        + ewt.escapar(titulo[a.id] || a.slug)
        + ' — ' + ewt.escapar(a.city) + '</option>';
    }).join('');

    var pedido = new URLSearchParams(location.search).get('tour');
    E.tour = (pedido && anuncios.some(function (a) { return a.id === pedido; }))
      ? pedido : anuncios[0].id;
    sel.value = E.tour;

    E.mes = primeiro(new Date());

    sel.addEventListener('change', function () {
      E.tour = sel.value;
      history.replaceState({}, '', '/portal/calendar/?tour=' + E.tour);
      carregar();
    });
    document.getElementById('cal-ant').addEventListener('click', function () {
      E.mes = new Date(E.mes.getFullYear(), E.mes.getMonth() - 1, 1);
      carregar();
    });
    document.getElementById('cal-seg').addEventListener('click', function () {
      E.mes = new Date(E.mes.getFullYear(), E.mes.getMonth() + 1, 1);
      carregar();
    });
    document.getElementById('grelha').addEventListener('click', function (ev) {
      var b = ev.target.closest('.dia[data-d]');
      if (b && !b.disabled) tocar(b.getAttribute('data-d'));
    });

    await carregar();
  })();
})();
"""


def corpo():
    return '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">
    <p class="carrega" id="carrega">Loading your calendar&hellip;</p>

    <div id="cal" hidden>
      <div class="pt-cab">
        <h1>Calendar</h1>
        <p>Open and closed days go live immediately &mdash; no review, no
          waiting. This is the one part of the portal that changes the
          site the moment you touch it.</p>
      </div>

      <p class="cal-ajuda">Tap a day to change it:
        <b>open</b> &rarr; <b>closed</b> &rarr; <b>sold out</b> &rarr;
        back to open. Tapping again undoes it.</p>

      <div class="cal-topo">
        <div class="campo" style="margin:0;flex:1 1 16rem">
          <label for="qual">Tour</label>
          <select id="qual"></select>
        </div>
        <div class="cal-nav">
          <button type="button" class="cal-b" id="cal-ant"
                  aria-label="Previous month">&larr;</button>
          <span class="cal-mes" id="cal-mes" role="status"></span>
          <button type="button" class="cal-b" id="cal-seg"
                  aria-label="Next month">&rarr;</button>
        </div>
      </div>

      <div class="grelha" id="grelha"></div>

      <p class="leg">
        <span><i class="i-open"></i> Open</span>
        <span><i class="i-closed"></i> Closed &mdash; struck through</span>
        <span><i class="i-sold"></i> Sold out &mdash; with a dot</span>
      </p>

      <p class="aviso" id="av-cal" role="status" hidden></p>
      <p class="lado-nota" id="sinal-cal" role="status" hidden></p>
    </div>
  </div>
</main>'''


def gerar():
    pagina.verificar_contraste()
    html = portal_base.envolver(
        titulo='Calendar — Exclusive World Tours',
        corpo=corpo(), js=JS, etiqueta='Operator portal',
        nav=NAV, atual='/portal/calendar/', css_extra=CSS)
    pagina.escrever(html, 'portal/calendar/index.html')


if __name__ == '__main__':
    gerar()
