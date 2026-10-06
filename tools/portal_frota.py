# -*- coding: utf-8 -*-
"""A frota do operador, e o calendario de cada veiculo.

Esta e a pagina que a GetYourGuide nao tem, e a razao por que nao a tem
e arquitetural: a disponibilidade deles e lida de cache, por isso avisam
expressamente contra partilhar capacidade entre produtos. Um operador
deles com uma carrinha e tres tours tem de fingir que tem tres
carrinhas, ou fechar os outros dois a mao sempre que vende um.

Aqui a disponibilidade e lida ao vivo, por isso o recurso pode ser
partilhado a serio: fecha-se a carrinha no dia 12 e ela desaparece dos
tres tours ao mesmo tempo, sozinha.

O ecra tem duas metades e a ordem importa: primeiro a frota (o que
tenho), depois o calendario (quando esta livre). Um operador que chega
aqui pela primeira vez tem de registar um veiculo antes de o calendario
fazer sentido nenhum, e a pagina diz-lhe isso em vez de lhe mostrar uma
grelha vazia.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pagina
import portal_base
from portal import NAV

# As cores vem das fichas do tema, nao de hexadecimais fixos:
# ver a nota em portal_base.FICHAS. E isto que faz o modo
# escuro desta pagina funcionar sem lhe mexer no CSS.
CORES = portal_base.FICHAS

CSS = """
.fr { display: grid; gap: 1.2rem; }
@media (min-width: 1060px) {
  .fr { grid-template-columns: 21rem minmax(0, 1fr); align-items: start; }
}

/* ------------------------------------------------------------ a frota */
.v-lista { display: grid; gap: .6rem; }
.v {
  display: grid; grid-template-columns: 1fr auto; gap: .5rem 1rem;
  align-items: center; width: 100%%; text-align: left;
  background: %(branco)s; border-radius: var(--r-g);
  box-shadow: var(--sombra);
  border-left: 4px solid %(risco)s;
  padding: .8rem .9rem; cursor: pointer;
  font: 400 .92rem/1.4 'Inter', system-ui, sans-serif; color: %(texto)s;
}
.v:hover { border-color: %(mudo)s; }
.v[aria-pressed="true"] { border-left-color: %(cor)s; background: %(papel)s; }
.v:focus-visible { outline: 3px solid %(cor)s; outline-offset: 2px; }
.v b {
  display: block; font: 700 1rem/1.25 'Inter', system-ui, sans-serif;
  color: %(tinta)s; margin-bottom: .15rem;
}
.v span { color: %(mudo)s; font-size: .84rem; }
.v-pax {
  font: 700 1.1rem/1 'Inter', system-ui, sans-serif; color: %(tinta)s;
  text-align: right; white-space: nowrap;
}
.v-pax small {
  display: block; font: 400 .66rem/1.3 'Inter', system-ui, sans-serif;
  color: %(mudo)s;
}
.v-inativo { opacity: .55; }

.v-form { display: grid; gap: .8rem; }
@media (min-width: 420px) {
  .v-form .v-linha { display: grid; grid-template-columns: 1fr 7rem; gap: .8rem; }
}

/* Os tours ligados a um veiculo usam o .v-t do portal_base: tambem sao
   usados na pagina dos pontos de encontro. */

/* ------------------------------------------------------ o calendario */
.vc-topo {
  display: flex; flex-wrap: wrap; gap: .8rem; align-items: center;
  margin-bottom: 1rem;
}
.vc-quem {
  font: 700 1.05rem/1.2 'Inter', system-ui, sans-serif; color: %(tinta)s;
}
.vc-quem span {
  display: block; font: 400 .82rem/1.4 'Inter', system-ui, sans-serif;
  color: %(mudo)s;
}
.vc-nav { display: flex; align-items: center; gap: .5rem; margin-left: auto; }
.vc-mes {
  font: 700 1rem/1 'Inter', system-ui, sans-serif; color: %(tinta)s;
  min-width: 10rem; text-align: center;
}
.vc-b {
  width: 2.6rem; height: 2.6rem; border-radius: var(--r-p); cursor: pointer;
  background: %(branco)s; border: 1px solid %(mudo)s; color: %(tinta)s;
  font: 600 1rem/1 'Inter', system-ui, sans-serif;
}
.vc-b:hover { border-color: %(tinta)s; background: %(papel)s; }
.vc-b[disabled] { opacity: .4; cursor: not-allowed; }

.vgrelha {
  display: grid; grid-template-columns: repeat(7, 1fr); gap: 3px;
  background: var(--sup-2); border-radius: var(--r-g);
  padding: 3px; margin-bottom: 1rem;
}
.vgd {
  background: %(branco)s; text-align: center;
  font: 600 .66rem/1 'Inter', system-ui, sans-serif;
  letter-spacing: .08em; text-transform: uppercase; color: %(mudo)s;
  padding: .55rem 0;
}
.vd {
  position: relative; background: %(branco)s; border: 0; cursor: pointer;
  aspect-ratio: 1 / 1; min-height: 2.9rem; padding: .25rem;
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: .1rem;
  font: 500 .95rem/1 'Inter', system-ui, sans-serif; color: %(tinta)s;
  font-variant-numeric: tabular-nums;
}
@media (min-width: 720px) { .vd { aspect-ratio: auto; height: 4.4rem; } }
.vd:hover:not([disabled]) { outline: 2px solid %(cor)s; outline-offset: -2px; }
.vd:focus-visible { outline: 3px solid %(cor)s; outline-offset: -3px; z-index: 2; }
.vd-v { background: %(papel)s; cursor: default; }
.vd[disabled] { background: %(papel)s; color: %(mudo)s; cursor: not-allowed; }
.vd-hoje { box-shadow: inset 0 0 0 2px %(tinta)s; }
/* Ocupado e indisponivel nao se distinguem so pela cor. */
.vd-booked { background: #EDF5EE; color: #14401A; }
.vd-booked::after {
  content: ''; position: absolute; bottom: .3rem; left: 50%%;
  transform: translateX(-50%%);
  width: 5px; height: 5px; border-radius: 50%%; background: #14401A;
}
/* O fundo era um cinzento escrito a mao: no modo escuro ficava claro
   com o texto claro por cima. O par "fechado" diz a mesma coisa — este
   dia nao se vende — e e verificado nos dois temas. */
.vd-closed {
  background: var(--fechado-f); color: var(--fechado);
  text-decoration: line-through; text-decoration-thickness: 2px;
}

.vleg {
  display: flex; flex-wrap: wrap; gap: .4rem 1.1rem; margin: 0 0 1.2rem;
  font: 400 .84rem/1.5 'Inter', system-ui, sans-serif; color: %(mudo)s;
}
.vleg span { display: flex; align-items: center; gap: .4rem; }
.vleg i {
  width: 1.1rem; height: 1.1rem; border-radius: var(--r-p);
  border: 1px solid %(risco)s; display: inline-block;
}
.vleg .i-open { background: %(branco)s; }
.vleg .i-booked { background: #EDF5EE; }
.vleg .i-closed { background: #F2EFEC; }

.vc-ajuda {
  font: 400 .88rem/1.6 'Inter', system-ui, sans-serif; color: %(texto)s;
  background: %(branco)s; 
  border-radius: var(--r-p); padding: .9rem 1rem; margin-bottom: 1.2rem;
}
.vc-ajuda b { color: %(tinta)s; }
""" % CORES


JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  var DIAS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
  var E = { operador: null, frota: [], anuncios: [], escolhido: null,
            mes: null, dados: {}, aEscrever: 0 };

  function primeiro(d) { return new Date(d.getFullYear(), d.getMonth(), 1); }
  function nomeMes(d) {
    return d.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
  }

  // ------------------------------------------------------------- a frota
  function desenharFrota() {
    var c = document.getElementById('v-lista');
    if (!E.frota.length) {
      c.innerHTML = '<div class="vazio"><h3>No vehicles yet</h3>'
        + '<p>Add the vehicles you actually run. The calendar below belongs '
        + 'to the vehicle, not to a tour — so closing one closes it '
        + 'across every tour that uses it.</p></div>';
      document.getElementById('vc').hidden = true;
      return;
    }
    c.innerHTML = E.frota.map(function (v) {
      return '<button type="button" class="v' + (v.active ? '' : ' v-inativo')
        + '" data-v="' + v.id + '" aria-pressed="'
        + (E.escolhido === v.id ? 'true' : 'false') + '">'
        + '<span><b>' + ewt.escapar(v.name) + '</b>'
        + '<span>' + (v.plate ? ewt.escapar(v.plate) + ' · ' : '')
        + (v.tours || 0) + (v.tours === 1 ? ' tour' : ' tours')
        + (v.active ? '' : ' · retired') + '</span></span>'
        + '<span class="v-pax">' + v.max_pax + '<small>seats</small></span>'
        + '</button>';
    }).join('');
    document.getElementById('vc').hidden = false;
  }

  async function carregarFrota() {
    var r = await ewt.sb.from('vehicles')
      .select('id, name, max_pax, plate, notes, active, listing_vehicles(listing_id)')
      .order('max_pax');
    if (r.error) { ewt.dizer('av-fr', ewt.legivel(r.error), 'mal'); return; }
    E.frota = (r.data || []).map(function (v) {
      v.tours = (v.listing_vehicles || []).length;
      v.listings = (v.listing_vehicles || []).map(function (x) { return x.listing_id; });
      return v;
    });
    if (!E.escolhido || !E.frota.some(function (v) { return v.id === E.escolhido; })) {
      E.escolhido = E.frota.length ? E.frota[0].id : null;
    }
    desenharFrota();
    desenharLigacoes();
    await carregarDias();
  }

  // ------------------------------------------------- que tours o usam
  function desenharLigacoes() {
    var c = document.getElementById('v-tours');
    var v = E.frota.filter(function (x) { return x.id === E.escolhido; })[0];
    if (!v || !E.anuncios.length) {
      c.innerHTML = '<p class="lado-nota">'
        + (E.anuncios.length ? 'Pick a vehicle to see which tours it serves.'
                             : 'You have no tours yet.') + '</p>';
      return;
    }
    c.innerHTML = E.anuncios.map(function (a) {
      var ligado = v.listings.indexOf(a.id) > -1;
      return '<label class="v-t"><input type="checkbox" data-liga="' + a.id
        + '"' + (ligado ? ' checked' : '') + '>'
        + '<span>' + ewt.escapar(a.titulo) + '</span></label>';
    }).join('');
  }

  async function ligar(listingId, ligar_) {
    var v = E.frota.filter(function (x) { return x.id === E.escolhido; })[0];
    if (!v) return;
    var r = ligar_
      ? await ewt.sb.from('listing_vehicles')
          .insert({ listing_id: listingId, vehicle_id: v.id })
      : await ewt.sb.from('listing_vehicles').delete()
          .eq('listing_id', listingId).eq('vehicle_id', v.id);
    if (r.error) { ewt.dizer('av-fr', ewt.legivel(r.error), 'mal'); return; }
    ewt.dizer('av-fr', '', '');
    await carregarFrota();
  }

  // -------------------------------------------------------- o calendario
  function desenharCalendario() {
    var v = E.frota.filter(function (x) { return x.id === E.escolhido; })[0];
    if (!v) return;
    document.getElementById('vc-quem').innerHTML =
      ewt.escapar(v.name) + '<span>up to ' + v.max_pax + ' people · '
      + (v.tours || 0) + (v.tours === 1 ? ' tour uses it' : ' tours use it')
      + '</span>';

    var g = document.getElementById('vgrelha');
    var mes = E.mes;
    document.getElementById('vc-mes').textContent = nomeMes(mes);

    var hoje = new Date(); hoje.setHours(0, 0, 0, 0);
    var html = DIAS.map(function (d) {
      return '<div class="vgd" aria-hidden="true">' + d + '</div>';
    }).join('');

    var inicio = primeiro(mes);
    var desvio = (inicio.getDay() + 6) % 7;
    for (var i = 0; i < desvio; i++) {
      html += '<span class="vd vd-v" aria-hidden="true"></span>';
    }

    var ultimo = new Date(mes.getFullYear(), mes.getMonth() + 1, 0).getDate();
    for (var n = 1; n <= ultimo; n++) {
      var d = new Date(mes.getFullYear(), mes.getMonth(), n);
      var k = ewt.iso(d);
      var r = E.dados[k] || { status: 'open' };
      var passado = d < hoje;
      var cls = 'vd';
      if (r.status === 'booked') cls += ' vd-booked';
      if (r.status === 'closed') cls += ' vd-closed';
      if (ewt.iso(hoje) === k) cls += ' vd-hoje';

      var legivel = d.toLocaleDateString(undefined,
        { weekday: 'long', day: 'numeric', month: 'long' });
      var estado = passado ? 'in the past'
        : r.status === 'booked' ? 'out on a job'
        : r.status === 'closed' ? 'not available' : 'free';

      html += '<button type="button" class="' + cls + '" data-d="' + k + '"'
        + (passado ? ' disabled' : '')
        + ' aria-label="' + legivel + ', ' + ewt.escapar(v.name) + ' is '
        + estado + '">' + n + '</button>';
    }

    var ocupados = (desvio + ultimo) % 7;
    if (ocupados) {
      for (var f = ocupados; f < 7; f++) {
        html += '<span class="vd vd-v" aria-hidden="true"></span>';
      }
    }
    g.innerHTML = html;

    document.getElementById('vc-ant').disabled = (mes <= primeiro(new Date()));
  }

  async function carregarDias() {
    if (!E.escolhido) return;
    var de = ewt.iso(primeiro(E.mes));
    var ate = ewt.iso(new Date(E.mes.getFullYear(), E.mes.getMonth() + 1, 0));
    var r = await ewt.sb.from('vehicle_days')
      .select('day, status, note')
      .eq('vehicle_id', E.escolhido).gte('day', de).lte('day', ate);
    if (r.error) { ewt.dizer('av-fr', ewt.legivel(r.error), 'mal'); return; }
    E.dados = {};
    (r.data || []).forEach(function (x) { E.dados[x.day] = x; });
    desenharCalendario();
  }

  // Livre -> ocupado -> indisponivel -> livre. Tres estados num toque,
  // como no calendario dos tours: um menu por dia e vinte toques para
  // fechar uma semana no telemovel.
  var SEGUINTE = { open: 'booked', booked: 'closed', closed: 'open' };

  async function tocar(dia) {
    var agora = (E.dados[dia] && E.dados[dia].status) || 'open';
    var novo = SEGUINTE[agora];

    E.dados[dia] = Object.assign({}, E.dados[dia] || {},
                                 { day: dia, status: novo });
    desenharCalendario();

    E.aEscrever++; sinal();
    var r = await ewt.sb.rpc('marcar_veiculo', {
      p_vehicle: E.escolhido, p_dias: [dia], p_status: novo
    });
    E.aEscrever--; sinal();

    if (r.error) {
      ewt.dizer('av-fr', ewt.legivel(r.error), 'mal');
      await carregarDias();
    } else {
      ewt.dizer('av-fr', '', '');
    }
  }

  function sinal() {
    var s = document.getElementById('vc-sinal');
    if (!s) return;
    s.textContent = E.aEscrever > 0 ? 'Saving…' : 'Saved.';
    s.hidden = false;
  }

  // ------------------------------------------------------ novo veiculo
  async function acrescentar(ev) {
    ev.preventDefault();
    var nome = document.getElementById('v-nome').value.trim();
    var pax = parseInt(document.getElementById('v-pax').value, 10);
    var mat = document.getElementById('v-mat').value.trim();
    ewt.dizer('av-novo', '', '');

    if (nome.length < 2) {
      ewt.dizer('av-novo', 'Give the vehicle a name you will recognise — '
        + 'the model is usually enough.', 'mal');
      document.getElementById('v-nome').focus();
      return;
    }
    if (!(pax > 0 && pax < 100)) {
      ewt.dizer('av-novo', 'How many passengers does it seat?', 'mal');
      document.getElementById('v-pax').focus();
      return;
    }

    var bt = document.getElementById('bt-novo');
    bt.disabled = true; bt.textContent = 'Adding…';
    var r = await ewt.sb.from('vehicles').insert({
      operator_id: E.operador.id, name: nome, max_pax: pax,
      plate: mat || null
    }).select('id').single();
    bt.disabled = false; bt.textContent = 'Add vehicle';

    if (r.error) { ewt.dizer('av-novo', ewt.legivel(r.error), 'mal'); return; }
    document.getElementById('f-novo').reset();
    E.escolhido = r.data ? r.data.id : E.escolhido;
    await carregarFrota();
    ewt.dizer('av-novo', 'Added. Now tick the tours it can run, below.', 'bem');
  }

  // ----------------------------------------------------------- arranque
  (async function () {
    var p = await ewt.exigir_entrada();
    if (!p) return;
    document.getElementById('carrega').hidden = true;

    if (!p.operadores.length) {
      document.getElementById('conteudo').innerHTML =
        '<div class="vazio"><h3>Your account is not linked to a company</h3>'
        + '<a class="bt bt-s" href="/portal/">Back to the portal</a></div>';
      return;
    }
    E.operador = p.operadores[0];
    E.mes = primeiro(new Date());
    document.getElementById('fr').hidden = false;

    // Os titulos dos anuncios vem das versoes.
    var a = await ewt.sb.from('listings').select('id, slug').order('created_at');
    E.anuncios = (a.data || []).map(function (x) {
      return { id: x.id, titulo: x.slug };
    });
    if (E.anuncios.length) {
      var vv = await ewt.sb.from('listing_versions')
        .select('listing_id, version, payload')
        .in('listing_id', E.anuncios.map(function (x) { return x.id; }))
        .order('version', { ascending: false });
      var t = {};
      (vv.data || []).forEach(function (x) {
        if (!t[x.listing_id] && x.payload && x.payload.title) {
          t[x.listing_id] = x.payload.title;
        }
      });
      E.anuncios.forEach(function (x) { x.titulo = t[x.id] || x.titulo; });
    }

    document.getElementById('f-novo').addEventListener('submit', acrescentar);

    document.getElementById('v-lista').addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-v]');
      if (!b) return;
      E.escolhido = b.getAttribute('data-v');
      desenharFrota();
      desenharLigacoes();
      carregarDias();
    });

    document.getElementById('v-tours').addEventListener('change', function (ev) {
      var c = ev.target.closest('[data-liga]');
      if (c) ligar(c.getAttribute('data-liga'), c.checked);
    });

    document.getElementById('vc-ant').addEventListener('click', function () {
      E.mes = new Date(E.mes.getFullYear(), E.mes.getMonth() - 1, 1);
      carregarDias();
    });
    document.getElementById('vc-seg').addEventListener('click', function () {
      E.mes = new Date(E.mes.getFullYear(), E.mes.getMonth() + 1, 1);
      carregarDias();
    });
    document.getElementById('vgrelha').addEventListener('click', function (ev) {
      var b = ev.target.closest('.vd[data-d]');
      if (b && !b.disabled) tocar(b.getAttribute('data-d'));
    });

    await carregarFrota();
  })();
})();
"""


def corpo():
    return '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">
    <p class="carrega" id="carrega">Loading your fleet&hellip;</p>

    <div id="fr" hidden>
      <div class="pt-cab">
        <h1>Fleet</h1>
        <p>Your vehicles, and when each of them is free. A vehicle you
          close here disappears from <b>every tour that uses it</b>, at
          once &mdash; you do not close the same day three times.</p>
      </div>

      <p class="aviso" id="av-fr" role="status" hidden></p>

      <div class="fr">
        <div>
          <div class="cx">
            <p class="cx-t">Your vehicles</p>
            <div class="v-lista" id="v-lista"></div>
          </div>

          <div class="cx">
            <p class="cx-t">Add a vehicle</p>
            <form class="v-form" id="f-novo" novalidate>
              <div class="v-linha">
                <div class="campo">
                  <label for="v-nome">What is it</label>
                  <input type="text" id="v-nome" maxlength="80"
                         placeholder="Mercedes V-Class">
                </div>
                <div class="campo">
                  <label for="v-pax">Seats</label>
                  <input type="number" id="v-pax" min="1" max="99"
                         inputmode="numeric">
                </div>
              </div>
              <div class="campo">
                <label for="v-mat">Registration</label>
                <input type="text" id="v-mat" maxlength="20">
                <span class="ajuda">Only you and we see this. It is never
                  shown to a guest.</span>
              </div>
              <button type="submit" class="bt bt-p" id="bt-novo">Add
                vehicle</button>
              <p class="aviso" id="av-novo" role="status" hidden></p>
            </form>
          </div>

          <div class="cx">
            <p class="cx-t">Which tours it can run</p>
            <div class="v-tours" id="v-tours"></div>
            <p class="lado-nota">Tick every tour this vehicle can do. That
              is what lets one vehicle hold up a tour's calendar and drop
              out of it the moment it is busy.</p>
          </div>
        </div>

        <!-- ------------------------------------------ o calendario -->
        <div id="vc" hidden>
          <p class="vc-ajuda">Tap a day to change it:
            <b>free</b> &rarr; <b>out on a job</b> &rarr;
            <b>not available</b> &rarr; back to free. It applies
            immediately, with no review, to every tour this vehicle
            serves.</p>

          <div class="vc-topo">
            <p class="vc-quem" id="vc-quem" role="status"></p>
            <div class="vc-nav">
              <button type="button" class="vc-b" id="vc-ant"
                      aria-label="Previous month">&larr;</button>
              <span class="vc-mes" id="vc-mes" role="status"></span>
              <button type="button" class="vc-b" id="vc-seg"
                      aria-label="Next month">&rarr;</button>
            </div>
          </div>

          <div class="vgrelha" id="vgrelha"></div>

          <p class="vleg">
            <span><i class="i-open"></i> Free</span>
            <span><i class="i-booked"></i> Out on a job &mdash; with a dot</span>
            <span><i class="i-closed"></i> Not available &mdash; struck through</span>
          </p>
          <p class="lado-nota" id="vc-sinal" role="status" hidden></p>
        </div>
      </div>
    </div>
  </div>
</main>'''


def gerar():
    pagina.verificar_contraste()
    html = portal_base.envolver(
        titulo='Fleet — Exclusive World Tours',
        corpo=corpo(), js=JS, etiqueta='Operator portal',
        nav=NAV, atual='/portal/fleet/', css_extra=CSS)
    pagina.escrever(html, 'portal/fleet/index.html')


if __name__ == '__main__':
    gerar()
