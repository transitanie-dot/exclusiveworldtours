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
  background: %(branco)s; border: 1px solid %(mudo)s; border-radius: var(--r-c);
  color: %(texto)s; padding: .5rem .9rem; cursor: pointer; }
.ag-f button[aria-pressed="true"] { background: %(tinta)s; color: %(papel)s;
  border-color: %(tinta)s; }

.ag-soma { display: flex; flex-wrap: wrap; gap: 1.4rem; align-items: baseline;
  border-radius: var(--r-g); background: var(--sup-2); padding: 1.1rem 1.2rem;
  margin-bottom: 1.2rem; }
.ag-soma b { font: 700 1.4rem/1 'Inter', system-ui, sans-serif; color: %(tinta)s; }
.ag-soma span { font-size: .86rem; color: %(mudo)s; }

/* Um dia. A data e a hora sao o que se le primeiro quando se abre isto
   de manha, por isso sao o que esta em cima e em maior. */
.ag { border-radius: var(--r-g); background: %(branco)s;
  box-shadow: var(--sombra);
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

/* ------------------------------------------------------- a falta
   O botao so aparece num dia que ja passou, e desaparece assim que a
   falta esta registada. Um botao que esta la mas responde com um erro
   e pior que botao nenhum: a pessoa so descobre depois de carregar. */
.ag-falta { margin-top: .8rem; }
.ag-falta summary {
  display: inline-flex; align-items: center; gap: .4rem;
  font-size: .86rem; font-weight: 600; color: var(--fechado);
  background: var(--fechado-f); border-radius: var(--r-c);
  padding: .5rem .95rem; cursor: pointer; list-style: none;
}
.ag-falta summary::-webkit-details-marker { display: none; }
.ag-falta summary:hover { filter: brightness(.96); }
.ag-falta[open] summary { margin-bottom: .9rem; }
.ag-falta .campo { margin-bottom: .8rem; }
.ag-falta .campo input, .ag-falta .campo textarea { background: var(--sup-2); }
.fx-feito {
  margin: .8rem 0 0; padding: .7rem .9rem; border-radius: var(--r-m);
  background: var(--fechado-f); color: var(--fechado);
  font-size: .87rem; line-height: 1.55;
}
.fx-porque {
  margin: 0 0 .9rem; font-size: .85rem; line-height: 1.55;
  color: var(--mudo);
}
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
      + falta(b)
      + '</article>';
  }

  // ------------------------------------------------------------ a falta
  //
  // O cliente que nao aparece e dinheiro que o operador ja nao recupera
  // — a menos que haja um registo. A Viator tem uma ferramenta propria
  // para isto e diz que ganha 73% das disputas de cartao com ela. O que
  // ganha uma disputa nao e a palavra do operador: e um registo FEITO NO
  // DIA, com hora, com quanto tempo se esperou e com o que se tentou.
  //
  // Por isso o painel pede as duas coisas que um banco pergunta, e a
  // funcao na base recusa um texto com menos de vinte letras. "Nao
  // apareceu" nao ganha nada.
  function falta(b) {
    var passou = b.booking_date <= ewt.iso(new Date());
    if (!passou) return '';

    if (b.no_show_at) {
      return '<p class="fx-feito"><b>No-show recorded</b> on '
        + e(String(b.no_show_at).slice(0, 10))
        + (b.no_show_wait != null
            ? ' \u2014 you waited ' + e(b.no_show_wait) + ' minutes.' : '.')
        + ' If the card is disputed, we send this with the evidence.</p>';
    }
    // Sem o id nao ha nada para registar. Acontece quando a reserva veio
    // de uma leitura que nao o trouxe — e melhor nao mostrar botao
    // nenhum do que mostrar um que falha.
    if (!b.id) return '';

    var r = e(b.reference);
    return '<details class="ag-falta" data-falta="' + r + '">'
      + '<summary>The customer did not show up</summary>'
      + '<p class="fx-porque">Record it today, not next week. A bank asks '
      + 'how long you waited and what you tried, and an account written '
      + 'from memory a fortnight later carries no weight.</p>'
      + '<div class="campo">'
      +   '<label for="fx-m-' + r + '">Minutes you waited</label>'
      +   '<input type="number" id="fx-m-' + r + '" min="0" max="480" '
      +     'step="5" style="max-width:9rem" inputmode="numeric">'
      + '</div>'
      + '<div class="campo">'
      +   '<label for="fx-t-' + r + '">What happened</label>'
      +   '<textarea id="fx-t-' + r + '" rows="3" '
      +     'placeholder="Waited 40 minutes at the hotel lobby, called the '
      +     'number on the booking twice, left a message at reception."'
      +     '></textarea>'
      +   '<span class="ajuda">Where you waited, what you tried, at what '
      +     'time. This is the part that wins a chargeback.</span>'
      + '</div>'
      + '<p class="aviso" id="fx-av-' + r + '" role="status" hidden></p>'
      + '<div class="acoes">'
      +   '<button type="button" class="bt bt-mal bt-pq" data-marca="'
      +     e(b.id) + '" data-ref="' + r + '">Record the no-show</button>'
      + '</div>'
      + '</details>';
  }

  async function marcar(id, ref, botao) {
    var m = document.getElementById('fx-m-' + ref);
    var t = document.getElementById('fx-t-' + ref);
    var av = 'fx-av-' + ref;

    var min = parseInt(m.value, 10);
    if (isNaN(min) || min < 0 || min > 480) {
      ewt.dizer(av, 'How many minutes did you wait? (0 to 480)', 'mal');
      m.focus();
      return;
    }
    // A base recusa menos de vinte letras. Dizer isso AQUI poupa uma ida
    // ao servidor e, mais importante, diz-se com as palavras certas:
    // nao e um limite tecnico, e o que faz a diferenca numa disputa.
    if (t.value.trim().length < 20) {
      ewt.dizer(av, 'Write what happened \u2014 where you waited, what you '
        + 'tried, at what time. A line or two is enough, but "did not '
        + 'show" on its own will not win a dispute.', 'mal');
      t.focus();
      return;
    }

    botao.disabled = true;
    var r = await ewt.sb.rpc('marcar_falta',
      { p_booking: id, p_esperou: min, p_nota: t.value.trim() });
    if (r.error) {
      botao.disabled = false;
      ewt.dizer(av, ewt.legivel(r.error), 'mal');
      return;
    }
    await desenhar();
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

      // A agenda vem de uma funcao que devolve o que o operador precisa
      // de VER, e so isso: nao traz o id da reserva nem o estado da
      // falta. Em vez de alargar o contrato dessa funcao — que outras
      // paginas tambem leem — pede-se o que falta a propria tabela, que
      // o operador ja pode ler pelas regras de seguranca que ja existem.
      //
      // So nos dias que ja passaram: e o unico separador onde o botao da
      // falta aparece, e uma leitura a mais no separador dos dias que
      // ainda vem seria trabalho para nada.
      if (QUANDO === 'past' && l.length) {
        var extra = await ewt.sb.from('bookings')
          .select('id, reference, no_show_at, no_show_wait')
          .gte('booking_date', i[0]).lte('booking_date', i[1]);
        if (!extra.error) {
          var porRef = {};
          (extra.data || []).forEach(function (x) { porRef[x.reference] = x; });
          l.forEach(function (b) {
            var x = porRef[b.reference];
            if (x) {
              b.id = x.id;
              b.no_show_at = x.no_show_at;
              b.no_show_wait = x.no_show_wait;
            }
          });
        }
        // Se esta leitura falhar, a agenda aparece na mesma — sem o
        // botao da falta. Uma lista de reservas que nao abre por causa
        // de um botao e uma troca muito ma.
      }

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

  document.getElementById('lista').addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-marca]');
    if (b) marcar(b.getAttribute('data-marca'), b.getAttribute('data-ref'), b);
  });

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
