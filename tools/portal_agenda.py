# -*- coding: utf-8 -*-
"""/portal/bookings/ — a agenda do operador.

O que ele precisa de ver para trabalhar amanha: quem vem, a que horas,
quantos sao, em que carro, onde se apanham, e quanto RECEBE.

O QUE ELE NAO VE AQUI
---------------------
Nao ve o total que o cliente pagou nem a taxa de comissao. Isso nao e
pudor: e a `agenda_do_operador()` na base que nao devolve essas colunas,
e e por isso que esta pagina nao as pode mostrar mesmo que alguem edite
o HTML. A comissao dele e uma conversa que ele teve com o Ricardo, e nao
uma coluna que aparece ao lado de cada cliente — e a comissao de OUTRO
operador nao e assunto dele de maneira nenhuma.

Tambem nao ve as reservas por pagar ('pending'): uma reserva que esta a
meio do Stripe pode nunca chegar a existir, e por-lhe isso na agenda era
dar-lhe um cliente que ainda nao e dele.
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
.ag-f { display: flex; flex-wrap: wrap; gap: .6rem; margin-bottom: 1.2rem; }
.ag-f button { font: 500 .85rem/1 'Inter', system-ui, sans-serif;
  background: %(branco)s; border: 1px solid %(mudo)s; border-radius: 20px;
  color: %(texto)s; padding: .5rem .9rem; cursor: pointer; }
.ag-f button[aria-pressed="true"] { background: %(tinta)s; color: %(papel)s;
  border-color: %(tinta)s; }

.ag-soma { display: flex; flex-wrap: wrap; gap: 1.4rem; align-items: baseline;
  border: 1px solid %(risco)s; border-left: 4px solid %(cor)s;
  border-radius: 10px; background: %(branco)s; padding: .9rem 1.1rem;
  margin-bottom: 1.2rem; }
.ag-soma b { font: 700 1.4rem/1 'Inter', system-ui, sans-serif; color: %(tinta)s; }
.ag-soma span { font-size: .86rem; color: %(mudo)s; }

/* Um dia. A data e a hora sao o que se le primeiro quando se abre isto
   de manha, por isso sao o que esta em cima e em maior. */
.ag { border: 1px solid %(risco)s; border-radius: 10px; background: %(branco)s;
  padding: 1rem 1.1rem; margin-bottom: .8rem; }
.ag-t { display: flex; flex-wrap: wrap; gap: .4rem 1rem; align-items: baseline;
  margin-bottom: .5rem; }
.ag-dia { font: 700 1.05rem/1.2 'Inter', system-ui, sans-serif; color: %(tinta)s; }
.ag-h { font-weight: 650; color: %(cor_escura)s; }
.ag-tour { color: %(texto)s; }
.ag-l { display: flex; flex-wrap: wrap; gap: .35rem 1.3rem; margin: 0 0 .4rem;
  font-size: .88rem; color: %(mudo)s; }
.ag-l b { color: %(texto)s; font-weight: 600; }
.ag-r { font-weight: 700; color: %(tinta)s; }
.ag-n { font-size: .87rem; color: %(texto)s; margin: .5rem 0 0;
  padding-left: .7rem; border-left: 2px solid %(risco)s; line-height: 1.55; }
.nada { font-style: italic; color: %(mudo)s; }
""" % CORES


JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  var e = ewt.escapar;
  var QUANDO = 'next';

  function intervalo() {
    var h = ewt.hoje();
    var d = new Date();
    if (QUANDO === 'next') {
      // De hoje a 90 dias. "Hoje" e nao "amanha": um tour de hoje a
      // tarde ainda esta por fazer, e e o mais urgente de todos.
      var f = new Date(d.getTime() + 90 * 864e5);
      return [h, ewt.iso(f)];
    }
    // O que ja passou, um ano para tras. E aqui que ele confirma o que
    // lhe foi pago.
    var a = new Date(d.getTime() - 365 * 864e5);
    return [ewt.iso(a), h];
  }

  function linha(rot, v) {
    if (v === null || v === undefined || v === '') return '';
    return '<span><b>' + e(rot) + '</b> ' + e(String(v)) + '</span>';
  }

  function cartao(b) {
    return '<article class="ag">'
      + '<div class="ag-t">'
      +   '<span class="ag-dia">' + e(b.booking_date) + '</span>'
      +   (b.start_time
            ? '<span class="ag-h">' + e(String(b.start_time).slice(0, 5)) + '</span>'
            : '<span class="ag-h">time to agree</span>')
      +   '<span class="ag-tour">' + e(b.tour_title) + '</span>'
      +   '<span class="ag-r">&euro;' + Number(b.you_receive).toFixed(2) + '</span>'
      + '</div>'
      + '<p class="ag-l">'
      +   linha('Group', b.pax + (b.pax === 1 ? ' person' : ' people'))
      +   linha('Vehicle', b.vehicle_name)
      +   linha('Name', b.customer_name)
      +   linha('Phone', b.customer_phone)
      +   linha('Reference', b.reference)
      // A DIFERENCA ENTRE CONFIRMADA E PAGA, DITA
      //
      // Ao operador nao interessa o jargao do Stripe, interessa saber se
      // o dia e dele. Nos dois casos e: a reserva esta feita e o veiculo
      // esta preso. O que muda e quando o dinheiro chega.
      +   linha('Payment', b.status === 'paid'
            ? 'collected' + (b.paid_out ? ' and paid to you' : ', you have not been paid yet')
            : 'confirmed — the customer is charged before the tour')
      + '</p>'
      + (b.pickup ? '<p class="ag-l">' + linha('Pick-up', b.pickup) + '</p>' : '')
      + (b.notes ? '<p class="ag-n">' + e(b.notes) + '</p>' : '')
      + '</article>';
  }

  async function desenhar() {
    var c = document.getElementById('lista');
    c.innerHTML = '<p class="carrega">Loading&hellip;</p>';
    var i = intervalo();
    try {
      var r = await ewt.sb.rpc('agenda_do_operador',
        { p_de: i[0], p_ate: i[1] });
      if (r.error) throw new Error(ewt.legivel(r.error));
      var l = r.data || [];

      if (!l.length) {
        c.innerHTML = '<p class="nada">' + (QUANDO === 'next'
          ? 'Nothing booked yet. Your days show up here the moment somebody '
            + 'pays for one.'
          : 'No tours in the last year.') + '</p>';
        return;
      }

      if (QUANDO === 'past') l = l.slice().reverse();

      var soma = l.reduce(function (t, b) { return t + Number(b.you_receive); }, 0);
      var porPagar = l.filter(function (b) {
        return b.status === 'paid' && !b.paid_out;
      }).reduce(function (t, b) { return t + Number(b.you_receive); }, 0);

      c.innerHTML =
        '<div class="ag-soma">'
        + '<div><b>' + l.length + '</b> <span>'
        +   (QUANDO === 'next' ? 'days booked' : 'days done') + '</span></div>'
        + '<div><b>&euro;' + soma.toFixed(2) + '</b> <span>yours in total</span></div>'
        + (porPagar > 0
            ? '<div><b>&euro;' + porPagar.toFixed(2)
              + '</b> <span>collected, not yet paid to you</span></div>'
            : '')
        + '</div>'
        + l.map(cartao).join('');
    } catch (err) {
      c.innerHTML = '';
      ewt.dizer(c, err.message, 'mal');
    }
  }

  document.getElementById('quando').addEventListener('click', function (ev) {
    var b = ev.target.closest('button[data-q]');
    if (!b) return;
    QUANDO = b.dataset.q;
    [].forEach.call(document.querySelectorAll('#quando button'), function (x) {
      x.setAttribute('aria-pressed', x === b ? 'true' : 'false');
    });
    desenhar();
  });

  (async function () {
    var p = await ewt.exigir_entrada();
    if (!p) return;
    if (!p.operadores.length) {
      document.getElementById('carrega').textContent =
        'This page is for operators. If you have applied and are waiting, '
        + 'we will be in touch.';
      return;
    }
    document.getElementById('carrega').hidden = true;
    document.getElementById('ag').hidden = false;
    desenhar();
  })();
})();
"""


CORPO = '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">
    <p class="carrega" id="carrega">Loading&hellip;</p>
    <div id="ag" hidden>
      <div class="pt-cab">
        <h1>Bookings</h1>
        <p>Everything that is booked with you, and what you receive for
          each day. The amount shown is yours &mdash; our commission is
          already taken off.</p>
      </div>

      <div class="ag-f" id="quando" role="group" aria-label="Which bookings">
        <button type="button" data-q="next" aria-pressed="true">Coming up</button>
        <button type="button" data-q="past" aria-pressed="false">Already done</button>
      </div>

      <div id="lista"></div>
    </div>
  </div>
</main>'''


def gerar():
    pagina.verificar_contraste()
    pagina.escrever(portal_base.envolver(
        titulo='Bookings — Exclusive World Tours',
        corpo=CORPO, js=JS, etiqueta='Operator portal',
        nav=NAV, atual='/portal/bookings/', css_extra=CSS),
        'portal/bookings/index.html')


if __name__ == '__main__':
    gerar()
