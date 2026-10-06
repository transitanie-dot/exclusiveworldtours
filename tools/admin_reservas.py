# -*- coding: utf-8 -*-
"""/admin/bookings/ — as reservas, e o dinheiro que elas movem.

Tres coisas numa pagina, porque sao tres coisas que se fazem na mesma
sessao e nao vale a pena tres paginas:

  Reservas      o que esta vendido, por ordem de data da viagem. A
                proxima primeiro, porque e a que importa hoje.
  A convidar    quem ja viajou e ainda nao foi convidado a avaliar. A
                `reservas_a_convidar()` ja filtra: so reservas PAGAS com
                data passada. Nao ha aqui nenhum botao de "marcar como
                viajado" — o pagamento e a prova.
  A pagar       quanto esta a pagar a cada operador, e o botao de marcar
                como pago. Soma so as viagens que JA aconteceram: pagar
                antes da viagem e emprestar dinheiro.

O QUE ESTA PAGINA NAO FAZ
-------------------------
Nao devolve dinheiro. O botao de cancelar grava o cancelamento, solta o
veiculo e MOSTRA o payment_intent e o valor para se fazer o reembolso no
painel do Stripe. Fazer as duas coisas num clique parece melhor e e
pior: se o Stripe recusar o reembolso depois de a base ter gravado o
cancelamento, fica uma reserva cancelada com o dinheiro do cliente ca
dentro e ninguem sabe.

Nao marca pagamentos automaticos ao operador. O `marcar_pago()` e um
registo do que o Ricardo transferiu, nao uma transferencia.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pagina
import portal_base

# As cores vem das fichas do tema, nao de hexadecimais fixos:
# ver a nota em portal_base.FICHAS. E isto que faz o modo
# escuro desta pagina funcionar sem lhe mexer no CSS.
CORES = portal_base.FICHAS

CSS = """
.rv-abas { display: flex; gap: .4rem; flex-wrap: wrap; margin-bottom: 1.3rem;
  border-bottom: 2px solid %(risco)s; }
.rv-aba { font: 600 .9rem/1 'Inter', system-ui, sans-serif; background: none;
  border: 0; border-bottom: 3px solid transparent; color: %(mudo)s;
  padding: .8rem .9rem; cursor: pointer; margin-bottom: -2px; }
.rv-aba[aria-selected="true"] { color: %(tinta)s; border-bottom-color: %(cor)s; }
.rv-aba .n { display: inline-block; margin-left: .4rem; padding: 0 .4rem;
  border-radius: 10px; background: %(risco)s; color: %(texto)s;
  font-size: .78rem; font-weight: 700; }

/* Uma reserva. A referencia e a data sao o que se procura com os olhos,
   por isso sao as duas unicas coisas em destaque. */
.rb { border: 1px solid %(risco)s; border-radius: 10px; background: %(branco)s;
  padding: 1rem 1.1rem; margin-bottom: .8rem; }
.rb-t { display: flex; flex-wrap: wrap; gap: .5rem 1rem; align-items: baseline;
  margin-bottom: .55rem; }
.rb-r { font: 700 1.05rem/1 'Inter', system-ui, sans-serif; color: %(tinta)s;
  letter-spacing: .05em; -webkit-user-select: all; user-select: all; }
.rb-d { font-weight: 650; color: %(tinta)s; }
.rb-tour { color: %(texto)s; }
.rb-l { display: flex; flex-wrap: wrap; gap: .35rem 1.3rem; margin: 0 0 .5rem;
  font-size: .88rem; color: %(mudo)s; }
.rb-l b { color: %(texto)s; font-weight: 600; }
.rb-acoes { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .7rem; }

/* O estado, numa palavra e numa cor. 'confirmed' nao e 'paid' e a
   diferenca e dinheiro: uma esta cobrada, a outra tem um cartao
   guardado e uma cobranca marcada. */
.et { display: inline-block; padding: .18rem .5rem; border-radius: 4px;
  font: 700 .72rem/1.4 'Inter', system-ui, sans-serif; letter-spacing: .06em;
  text-transform: uppercase; }
.et-paid { background: #e6f2ea; color: #1d5c35; }
.et-confirmed { background: #fff4e0; color: #7a4c05; }
.et-pending { background: %(risco)s; color: %(texto)s; }
.et-cancelled { background: #f6e9e9; color: #8a2a2a; }
.et-refunded { background: #ecebf5; color: #41407a; }
.et-later { background: %(papel)s; color: %(texto)s; border: 1px solid %(risco)s; }

.rb-cob { font-size: .85rem; color: %(mudo)s; margin: .4rem 0 0;
  padding-left: .7rem; border-left: 2px solid %(risco)s; }

.pg { border: 1px solid %(risco)s; border-radius: 10px; background: %(branco)s;
  padding: 1rem 1.1rem; margin-bottom: .8rem; display: flex;
  flex-wrap: wrap; gap: .7rem 1.2rem; align-items: center;
  justify-content: space-between; }
.pg-v { font: 700 1.3rem/1 'Inter', system-ui, sans-serif; color: %(tinta)s; }
.pg-n { font-weight: 650; color: %(tinta)s; }
.pg-m { font-size: .85rem; color: %(mudo)s; }

.lk { font-size: .85rem; word-break: break-all; }
.nada { font-style: italic; color: %(mudo)s; }
""" % CORES


JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  var ABA = 'bookings';
  var e = ewt.escapar;

  function et(s) {
    return '<span class="et et-' + e(s) + '">' + e(s) + '</span>';
  }

  function linha(rot, v) {
    if (v === null || v === undefined || v === '') return '';
    return '<span><b>' + e(rot) + '</b> ' + e(String(v)) + '</span>';
  }

  // ------------------------------------------------------------ reservas
  async function reservas() {
    // Por data da viagem e nao por data da reserva: o que interessa a
    // quem abre esta pagina e o que esta a chegar, nao o que entrou.
    var r = await ewt.sb.from('bookings')
      .select('*').neq('status', 'pending')
      .order('booking_date', { ascending: true })
      .limit(200);
    if (r.error) throw new Error(ewt.legivel(r.error));

    var hoje = ewt.hoje();
    var futuras = (r.data || []).filter(function (b) {
      return b.booking_date >= hoje && b.status !== 'cancelled';
    });
    var resto = (r.data || []).filter(function (b) {
      return !(b.booking_date >= hoje && b.status !== 'cancelled');
    }).reverse();

    if (!futuras.length && !resto.length) {
      return '<p class="nada">No bookings yet.</p>';
    }

    return (futuras.length
              ? '<h2 class="pt-h2">Coming up</h2>' + futuras.map(cartao).join('')
              : '<p class="nada">Nothing booked for the days ahead.</p>')
         + (resto.length
              ? '<h2 class="pt-h2">Past and cancelled</h2>'
                + resto.slice(0, 60).map(cartao).join('')
              : '');
  }

  function cartao(b) {
    var depois = b.payment_mode === 'later';
    var podeCancelar = b.status === 'confirmed' || b.status === 'paid';

    return '<article class="rb" data-b="' + e(b.id) + '">'
      + '<div class="rb-t">'
      +   '<span class="rb-r">' + e(b.reference) + '</span>'
      +   '<span class="rb-d">' + e(b.booking_date)
      +     (b.start_time ? ' &middot; ' + e(String(b.start_time).slice(0, 5)) : '')
      +   '</span>'
      +   '<span class="rb-tour">' + e(b.tour_title) + '</span>'
      +   et(b.status)
      +   (depois ? '<span class="et et-later">pay later</span>' : '')
      + '</div>'

      + '<p class="rb-l">'
      +   linha('Group', b.pax + (b.pax === 1 ? ' person' : ' people'))
      +   linha('Vehicle', b.vehicle_name)
      +   linha('Customer', b.customer_name)
      +   linha('Email', b.customer_email)
      +   linha('Phone', b.customer_phone)
      + '</p>'
      + '<p class="rb-l">'
      +   linha('Total', b.currency + ' ' + Number(b.price_total).toFixed(2))
      +   linha('Operator gets', b.currency + ' ' + Number(b.operator_amount).toFixed(2))
      +   linha('We keep', b.currency + ' ' + Number(b.platform_amount).toFixed(2))
      +   linha('Paid out', b.payout_at ? b.payout_at.slice(0, 10) : 'not yet')
      + '</p>'
      + (b.pickup ? '<p class="rb-l">' + linha('Pick-up', b.pickup) + '</p>' : '')
      + (b.notes ? '<p class="rb-l">' + linha('Notes', b.notes) + '</p>' : '')

      // A COBRANCA QUE AINDA NAO ACONTECEU
      //
      // Uma reserva 'confirmed' nao tem dinheiro nenhum ca dentro. Sem
      // esta linha, a pagina mostrava um valor e uma data e parecia tudo
      // tratado — e so no dia da viagem e que se descobria que nao.
      + (depois && b.status === 'confirmed'
          ? '<p class="rb-cob">Nothing charged yet. The card is charged on '
            + e(b.charge_at ? b.charge_at.slice(0, 16).replace('T', ' ') : '—')
            + (b.charge_attempts
                ? ' &middot; ' + b.charge_attempts + ' attempt(s) so far'
                : '')
            + (b.stripe_payment_method_id ? ''
                : ' &middot; <b>no card saved — this one cannot be charged</b>')
            + '</p>'
          : '')
      + (b.cancel_reason
          ? '<p class="rb-cob">' + e(b.cancel_reason) + '</p>' : '')

      + (podeCancelar
          ? '<div class="rb-acoes">'
            + '<button class="pt-b pt-b-f" data-cancelar>Cancel this booking</button>'
            + '</div>'
          : '')
      + '</article>';
  }

  // ---------------------------------------------------------- a convidar
  async function convidar() {
    var r = await ewt.sb.rpc('reservas_a_convidar');
    if (r.error) throw new Error(ewt.legivel(r.error));
    var l = r.data || [];
    if (!l.length) {
      return '<p class="nada">Nobody is waiting for a review invitation.</p>';
    }
    return l.map(function (b) {
      return '<article class="rb" data-b="' + e(b.booking_id) + '">'
        + '<div class="rb-t">'
        +   '<span class="rb-r">' + e(b.reference) + '</span>'
        +   '<span class="rb-d">' + e(b.booking_date) + '</span>'
        +   '<span class="rb-tour">' + e(b.tour_title) + '</span>'
        + '</div>'
        + '<p class="rb-l">' + linha('Customer', b.customer_name)
        +   linha('Email', b.customer_email) + '</p>'
        + '<div class="rb-acoes">'
        +   '<button class="pt-b" data-convidar>Create the review link</button>'
        + '</div>'
        + '<p class="lk" data-lk hidden></p>'
        + '</article>';
    }).join('');
  }

  // ------------------------------------------------------------- a pagar
  async function pagar() {
    var r = await ewt.sb.rpc('a_pagar');
    if (r.error) throw new Error(ewt.legivel(r.error));
    var l = r.data || [];
    if (!l.length) {
      return '<p class="nada">Nothing owed to any operator right now.</p>';
    }
    return '<p>These are tours that have already happened and been paid for '
      + 'by the customer. Marking an operator as paid records what you '
      + 'transferred &mdash; it does not transfer anything.</p>'
      + l.map(function (o) {
        return '<div class="pg" data-op="' + e(o.operator_id) + '">'
          + '<div>'
          +   '<p class="pg-n">' + e(o.operator_name) + '</p>'
          +   '<p class="pg-m">' + e(o.operator_email) + ' &middot; '
          +     o.reservas + ' booking(s) &middot; oldest '
          +     e(o.mais_antiga) + '</p>'
          + '</div>'
          + '<div>'
          +   '<span class="pg-v">&euro;' + Number(o.total).toFixed(2) + '</span>'
          + '</div>'
          + '<div><button class="pt-b" data-pago>Mark as paid</button></div>'
          + '</div>';
      }).join('');
  }

  // ------------------------------------------------------------ desenhar
  var FEITORES = { bookings: reservas, invites: convidar, payouts: pagar };

  async function desenhar() {
    var c = document.getElementById('lista');
    c.innerHTML = '<p class="carrega">Loading&hellip;</p>';
    try {
      c.innerHTML = await FEITORES[ABA]();
    } catch (err) {
      c.innerHTML = '';
      ewt.dizer(c, err.message, 'mal');
    }
    contar();
  }

  /** Os numeros nas abas. Correm em separado e depois do desenho: uma
   *  contagem lenta nao pode atrasar a lista que se foi ver. */
  async function contar() {
    try {
      var a = await ewt.sb.rpc('reservas_a_convidar');
      var b = await ewt.sb.rpc('a_pagar');
      poe('invites', (a.data || []).length);
      poe('payouts', (b.data || []).length);
    } catch (err) { /* os numeros sao um extra, nao a pagina */ }
  }

  function poe(aba, n) {
    var el = document.querySelector('[data-aba="' + aba + '"] .n');
    if (el) el.textContent = n;
  }

  document.getElementById('abas').addEventListener('click', function (ev) {
    var b = ev.target.closest('[data-aba]');
    if (!b) return;
    ABA = b.dataset.aba;
    [].forEach.call(document.querySelectorAll('[data-aba]'), function (x) {
      x.setAttribute('aria-selected', x === b ? 'true' : 'false');
    });
    desenhar();
  });

  document.getElementById('lista').addEventListener('click', async function (ev) {
    var art = ev.target.closest('[data-b], [data-op]');
    if (!art) return;

    // ---- cancelar
    if (ev.target.matches('[data-cancelar]')) {
      var razao = prompt('Why is this booking being cancelled?\n\n'
        + 'This is written into the record and the operator can see it. '
        + 'At least 10 characters.');
      if (!razao) return;
      ev.target.disabled = true;
      try {
        var r = await ewt.sb.rpc('cancelar_reserva',
          { p_booking: art.dataset.b, p_razao: razao });
        if (r.error) throw new Error(ewt.legivel(r.error));
        var d = r.data || {};
        // O REEMBOLSO FICA PARA O STRIPE
        //
        // A base ja gravou o cancelamento e soltou o veiculo. O dinheiro
        // devolve-se no painel do Stripe, com o payment_intent que
        // aparece aqui. Fazer as duas coisas num clique dava uma reserva
        // cancelada com o dinheiro do cliente ca dentro no dia em que o
        // Stripe recusasse o reembolso.
        alert('Cancelled. The vehicle is free again.\n\n'
          + (d.charged
              ? 'This one WAS charged: ' + Number(d.amount).toFixed(2)
                + '\nRefund it in Stripe using\n' + (d.payment_intent || '—')
              : 'Nothing had been charged, so there is nothing to refund.'));
        desenhar();
      } catch (err) {
        ewt.dizer(art, err.message, 'mal');
        ev.target.disabled = false;
      }
      return;
    }

    // ---- convidar a avaliar
    if (ev.target.matches('[data-convidar]')) {
      ev.target.disabled = true;
      try {
        var c = await ewt.sb.rpc('convidar_por_reserva',
          { p_booking: art.dataset.b });
        if (c.error) throw new Error(ewt.legivel(c.error));
        var p = art.querySelector('[data-lk]');
        // O link copia-se e mete-se num email a mao. Enquanto os
        // registos DNS do dominio nao estiverem na Resend, nao sai email
        // nenhum daqui — e um link que se ve vale mais do que um envio
        // que falha em silencio.
        p.textContent = location.origin + '/review/?t=' + c.data;
        p.hidden = false;
        ev.target.textContent = 'Link created — copy it';
      } catch (err) {
        ewt.dizer(art, err.message, 'mal');
        ev.target.disabled = false;
      }
      return;
    }

    // ---- marcar como pago
    if (ev.target.matches('[data-pago]')) {
      var nota = prompt('How did you pay them?\n\n'
        + 'A bank reference or a date — anything that lets you find it '
        + 'again in six months.');
      if (nota === null) return;
      ev.target.disabled = true;
      try {
        var m = await ewt.sb.rpc('marcar_pago',
          { p_operator: art.dataset.op, p_nota: nota });
        if (m.error) throw new Error(ewt.legivel(m.error));
        desenhar();
      } catch (err) {
        ewt.dizer(art, err.message, 'mal');
        ev.target.disabled = false;
      }
    }
  });

  (async function () {
    var p = await ewt.exigir_entrada();
    if (!p) return;
    if (!p.admin) {
      document.getElementById('carrega').textContent =
        'This page is for the administrator.';
      return;
    }
    document.getElementById('carrega').hidden = true;
    document.getElementById('ad').hidden = false;
    desenhar();
  })();
})();
"""


CORPO = '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">
    <p class="carrega" id="carrega">Loading&hellip;</p>
    <div id="ad" hidden>
      <div class="pt-cab">
        <h1>Bookings</h1>
        <p>What is sold, who still has to be invited to leave a review,
          and what is owed to each operator. Nothing on this page moves
          money &mdash; it records what happened and tells you what to do
          in Stripe.</p>
      </div>

      <div class="rv-abas" id="abas" role="tablist" aria-label="Bookings views">
        <button type="button" class="rv-aba" data-aba="bookings"
                role="tab" aria-selected="true">Bookings</button>
        <button type="button" class="rv-aba" data-aba="invites"
                role="tab" aria-selected="false">To invite<span class="n">0</span></button>
        <button type="button" class="rv-aba" data-aba="payouts"
                role="tab" aria-selected="false">To pay<span class="n">0</span></button>
      </div>

      <div id="lista"></div>
    </div>
  </div>
</main>'''


def gerar():
    pagina.verificar_contraste()
    from admin import NAV
    pagina.escrever(portal_base.envolver(
        titulo='Bookings — Exclusive World Tours',
        corpo=CORPO, js=JS, etiqueta='Administration',
        nav=NAV, atual='/admin/bookings/', css_extra=CSS),
        'admin/bookings/index.html')


if __name__ == '__main__':
    gerar()
