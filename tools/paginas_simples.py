#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""As paginas de texto corrido: a politica de cancelamento, por agora.

Existe porque a homepage prometia /cancellation/ e essa pagina nao
existia — um 404 a partir do rodape da pagina mais vista do site.

O que esta aqui descreve o que acontece a um pedido confirmado por
email, que e como as reservas funcionam hoje. Nao descreve um mecanismo
de reembolso automatico, porque esse ainda nao foi construido, e
publicar uma politica que descreve um sistema que nao existe e a maneira
mais rapida de ter uma discussao que nao se pode ganhar.

    python3 tools/paginas_simples.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ligacao  # noqa: E402
import politica  # noqa: E402
import procura  # noqa: E402
from pagina import (cabecalho, carregar, envolver, escrever,  # noqa: E402
                    por_pais, rodape)

CSS = '''
.pcapa{background:var(--tinta);color:rgba(255,255,255,.86);
  padding:var(--e5) 0}
.pcapa h1{color:var(--branco);margin:0 0 var(--e2);max-width:20ch;
  font-size:clamp(1.9rem,1.3rem + 2.4vw,2.9rem)}
.pcapa .lede{max-width:54ch;margin:0;color:rgba(255,255,255,.8);
  font-size:clamp(1.02rem,1rem + .3vw,1.16rem)}

.ptexto{padding:var(--e5) 0 var(--e6)}
.ptexto .dentro{max-width:40rem}
.ptexto h2{margin:var(--e5) 0 var(--e2);font-size:1.4rem;line-height:1.22}
.ptexto h2:first-child{margin-top:0}
.ptexto p{margin:0 0 var(--e3);font-size:1.02rem;line-height:1.72;
  color:var(--texto)}
.ptexto ul{margin:0 0 var(--e3);padding-left:1.2rem}
.ptexto li{margin-bottom:10px;font-size:1.02rem;line-height:1.7;
  color:var(--texto)}

.pregra{background:var(--branco);border:1px solid var(--risco);
  border-left:4px solid var(--cor);border-radius:var(--raio);
  padding:var(--e4);margin:0 0 var(--e4)}
.pregra b{display:block;font-family:var(--tipo-titulo);font-size:1.3rem;
  color:var(--tinta);margin-bottom:8px}
.pregra span{font-size:1rem;line-height:1.65;color:var(--texto)}

.pnota{background:var(--papel);border:1px solid var(--risco);
  border-radius:var(--raio);padding:var(--e3);margin:var(--e4) 0 0;
  font-size:.92rem;line-height:1.65;color:var(--mudo)}

/* A pagina de confirmacao. A referencia e o que a pessoa le ao telefone,
   por isso e o maior elemento da pagina depois do titulo. */
.cref{font-family:var(--tipo-titulo);font-size:clamp(1.8rem,1.4rem + 2vw,2.6rem);
  letter-spacing:.06em;color:var(--tinta);margin:0 0 6px;
  -webkit-user-select:all;user-select:all}
.cref-r{font-size:11px;letter-spacing:.11em;text-transform:uppercase;
  color:var(--mudo);font-weight:600;margin:0 0 var(--e3)}
.clinhas{list-style:none;margin:0 0 var(--e4);padding:0;
  border-top:1px solid var(--risco)}
.clinhas li{display:flex;flex-wrap:wrap;gap:4px 14px;justify-content:space-between;
  padding:11px 0;border-bottom:1px solid var(--risco);font-size:1rem}
.clinhas dt,.clinhas b{color:var(--mudo);font-weight:500;font-size:.93rem}
.clinhas span{color:var(--tinta);font-weight:600;text-align:right}
.cestado{min-height:3rem}
.cerro{background:#fdf1f1;border:1px solid #e7c3c3;color:#8a2a2a;
  border-radius:var(--raio);padding:var(--e3);font-size:.98rem;line-height:1.6}
'''


def cancelamento(paises):
    corpo = '''%(cabecalho)s
<main id="principal">

<section class="pcapa">
  <div class="folha">
    <h1>Cancellation</h1>
    <p class="lede">One rule, the same on every tour, written where you
      can find it before you ask rather than after.</p>
  </div>
</section>

<section class="ptexto">
  <div class="folha">
    <div class="dentro">

      <div class="pregra">
        <b>Free up to %(horas)d hours before departure</b>
        <span>Cancel more than %(horas)d hours before your departure time
          and you pay nothing at all.</span>
      </div>

      <h2>Inside %(horas)d hours</h2>
      <p>Once you are inside %(horas)d hours, the vehicle and the driver
        are committed to your day. They are not taking another booking,
        so we cannot refund it. That is the trade for having a day that
        belongs to your group alone.</p>

      <h2>Weather is not a cancellation</h2>
      <p>These are private days, and that is exactly when it matters. If
        a stop is genuinely unsafe or a road is closed, your driver
        changes the route and tells you why &mdash; and you still get a
        full day out. A coach cannot do that, which is why a coach tour
        cancels and we usually do not.</p>
      <p>If you would rather not travel because of the forecast, that is
        a cancellation like any other and the %(horas)d hours apply.</p>

      <h2>If we cancel</h2>
      <p>You are refunded in full, whenever it happens and whatever the
        reason &mdash; conditions that make the roads unsafe, a vehicle
        that fails its check, a driver who cannot drive. We will also
        try to move you to another day first, if you want that.</p>

      <h2>Changing instead of cancelling</h2>
      <p>Moving your date is not a cancellation and costs nothing, as
        long as the operator has the new day free. Ask as early as you
        can: the day you want is somebody else's day until it is
        yours.</p>
      <p>Adding or removing people is free too, but it can change the
        price: if your group outgrows the vehicle it was booked for, the
        larger vehicle costs what the page says it costs.</p>

      <h2>How to cancel</h2>
      <p>Reply to the email that confirmed your day, or write to us
        through <a href="/contact/">the contact page</a>. The time that
        counts is the time your message reaches us, not the time we
        answer it.</p>

      <div class="pnota">
        <p style="margin:0">Bookings are confirmed by email today, and
          this page describes what happens to a booking confirmed that
          way. There is no automatic online refund, because there is no
          automatic online payment yet &mdash; we are not going to
          describe a system that does not exist.</p>
      </div>

    </div>
  </div>
</section>

</main>
%(rodape)s''' % {'cabecalho': cabecalho(paises=paises),
                 'rodape': rodape(paises),
                 'horas': politica.HORAS}

    escrever(envolver(
        'Cancellation — Exclusive World Tours',
        'Free cancellation up to %d hours before departure. What happens '
        'inside that window, what happens in bad weather, and what '
        'happens if we cancel.' % politica.HORAS,
        CSS, corpo, js=procura.JS), 'cancellation/index.html')


def avaliacoes(paises):
    """Como funcionam as avaliacoes aqui.

    Esta pagina e um compromisso publico e e por isso que existe. Um
    marketplace novo nao tem avaliacoes nenhumas; o que pode ter desde o
    primeiro dia e uma regra escrita sobre como as trata — e ser julgado
    por ela depois.
    """
    corpo = '''%(cabecalho)s
<main id="principal">

<section class="pcapa">
  <div class="folha">
    <h1>How reviews work here</h1>
    <p class="lede">We have very few, because we are new. What we will
      not do is make that look better than it is.</p>
  </div>
</section>

<section class="ptexto">
  <div class="folha">
    <div class="dentro">

      <div class="pregra">
        <b>Only people who travelled can leave one</b>
        <span>There is no open review form on this site, and there will
          not be one. A review link is sent by email after a day out, it
          works once, and it is tied to that booking.</span>
      </div>

      <h2>What that rules out</h2>
      <p>It rules out an operator reviewing himself, a competitor
        reviewing him, and us writing a few to fill the page. It also
        rules out a happy guest leaving five reviews, however much they
        enjoyed the day.</p>
      <p>The trade is that we will always have fewer reviews than a site
        that asks everyone who visits. We would rather have twenty you
        can trust than two hundred you cannot.</p>

      <h2>What the operator can and cannot do</h2>
      <ul>
        <li>They <b>can</b> reply in public, under the review, and we
          encourage it &mdash; a good reply to a bad review tells you
          more than ten good reviews.</li>
        <li>They <b>cannot</b> change the rating or the words.</li>
        <li>They <b>cannot</b> contact you privately about a review you
          left, or offer you anything to change it.</li>
      </ul>

      <h2>When we remove a review</h2>
      <p>Rarely, and only for these reasons:</p>
      <ul>
        <li>the day did not actually happen;</li>
        <li>it is abusive, or it identifies a person;</li>
        <li>the words and the rating contradict each other so plainly
          that one of them must be a mistake;</li>
        <li>it is advertising something;</li>
        <li>whoever wrote it has an interest in the outcome.</li>
      </ul>
      <p><b>"It is negative and it is true" is not on that list, and it
        is not going to be.</b> Every removal is recorded with the
        written reason, which is the thing that stops this from quietly
        becoming a button for deleting whatever stings.</p>

      <h2>How the score is worked out</h2>
      <p>A review from two years ago describes a vehicle that has since
        been sold and a driver who has since left. So recent reviews
        count for more: a review loses half its weight after about
        eighteen months, and half again after three years. We show the
        plain average as well, because a weighted average nobody can
        check is just a nicer number.</p>
      <p>A tour with fewer than three reviews of its own shows the
        <b>operator\u2019s</b> rating instead, and says so. The rating is
        real; it just is not that tour\u2019s yet.</p>
      <p>A tour with no reviews at all, and an operator with none,
        shows <b>nothing</b>. Not five empty stars, not "no reviews
        yet" in large type. An empty space is honest; empty stars read
        like a day that went badly.</p>

      <div class="pnota">
        <p style="margin:0">We do not pay for reviews, we do not offer
          anything in return for one, and we do not have a way to buy a
          better position on this site. If that ever changes, it will be
          written here before it happens.</p>
      </div>

    </div>
  </div>
</section>

</main>
%(rodape)s''' % {'cabecalho': cabecalho(paises=paises),
                 'rodape': rodape(paises)}

    escrever(envolver(
        'How reviews work — Exclusive World Tours',
        'Only people who travelled can leave a review here. What the '
        'operator can and cannot do, and the narrow reasons a review is '
        'ever removed.',
        CSS, corpo, js=procura.JS), 'reviews-policy/index.html')


def confirmada(paises):
    """/booking-confirmed/ — para onde o Stripe manda o cliente.

    A pagina nao sabe nada sozinha: le o `session_id` do endereco e
    pergunta a Edge Function `sessao`. Nada do que aparece aqui esta no
    HTML gerado, e e assim que tem de ser — esta pagina e a mesma para
    todas as reservas.

    DUAS FRASES DIFERENTES, E NAO UMA
    ---------------------------------
    Quem pagou agora leu "paid". Quem escolheu pagar depois NAO pagou
    nada, e dizer-lhe "paid" seria mentira que se descobre 72 horas antes
    do tour, quando o cartao e cobrado e a pessoa acha que ja tinha
    pagado. A pagina diz exatamente o que aconteceu e quando sai o
    dinheiro.
    """
    corpo = '''%(cabecalho)s
<main id="principal">

<section class="pcapa">
  <div class="dentro">
    <h1 data-titulo>Thank you &mdash; your day is booked</h1>
    <p class="lede" data-lede>We are just confirming it with the payment
      provider.</p>
  </div>
</section>

<section class="ptexto">
  <div class="dentro">
    <div class="cestado" data-estado>
      <p>One moment&hellip;</p>
    </div>

    <div data-detalhe hidden>
      <p class="cref" data-ref></p>
      <p class="cref-r">Your booking reference &mdash; keep it</p>

      <ul class="clinhas" data-linhas></ul>

      <div class="pregra">
        <b>What happens next</b>
        <span data-proximo></span>
      </div>

      <h2>Changing or cancelling</h2>
      <p>Free cancellation up to %(horas)d hours before departure. Reply to
        the confirmation email with your reference and we take care of it.
        The full rules are on the
        <a href="/cancellation/">cancellation page</a>.</p>

      <h2>On the day</h2>
      <p>The operator who runs your tour will be in touch to agree the exact
        pick-up point and time. Keep your phone reachable &mdash; it is how
        the driver finds you.</p>

      <p class="pnota">Nothing was saved on this page. Your booking lives in
        our system under the reference above, and the confirmation email is
        the copy you keep.</p>
    </div>
  </div>
</section>

</main>
%(rodape)s''' % {'cabecalho': cabecalho(paises=paises),
                 'rodape': rodape(paises),
                 'horas': politica.HORAS}

    html = envolver(
        'Booking confirmed — Exclusive World Tours',
        'Your private day is booked. Your reference, what happens next, '
        'and how to change or cancel it.',
        CSS, corpo, js=procura.JS + JS_CONFIRMADA)
    # Esta pagina nao sabe nada sozinha: tudo o que mostra vem da Edge
    # Function. A biblioteca TEM de estar carregada antes do script da
    # pagina, e o verificar.py confirma essa ordem — ao contrario, o
    # `window.ewt` ainda nao existe quando o script corre.
    html = html.replace('</head>', ligacao.SCRIPTS + '\n</head>')
    escrever(html, 'booking-confirmed/index.html')


JS_CONFIRMADA = r"""
(function () {
  'use strict';
  var est = document.querySelector('[data-estado]');
  var det = document.querySelector('[data-detalhe]');
  if (!est) return;

  function falhar(msg) {
    est.innerHTML = '<div class="cerro"></div>';
    est.firstChild.textContent = msg;
  }

  if (!window.ewt || window.ewt.avariado) {
    return falhar('We could not load your booking. Check the confirmation ' +
      'email, or send us a message with the reference from it.');
  }

  var id = new URLSearchParams(location.search).get('session_id');
  if (!id) {
    return falhar('This page needs the link from your payment. Check the ' +
      'confirmation email.');
  }

  function linha(rot, v) {
    if (!v) return '';
    var li = document.createElement('li');
    var b = document.createElement('b');
    b.textContent = rot;
    var s = document.createElement('span');
    s.textContent = v;
    li.appendChild(b); li.appendChild(s);
    return li;
  }

  window.ewt.resumo_sessao(id).then(function (d) {
    if (!d || !d.confirmed) {
      // O Stripe manda para ca assim que a sessao termina, e o webhook
      // pode ainda nao ter chegado. Nao se diz que falhou: diz-se o que
      // se sabe, que e que o pagamento esta a ser processado.
      return falhar('Your payment is still being processed. Give it a ' +
        'minute and reload this page. If it stays like this, send us a ' +
        'message and we will check it.');
    }

    var depois = d.payment_mode === 'later';

    document.querySelector('[data-titulo]').textContent = depois
      ? 'Your day is booked'
      : 'Paid \u2014 your day is booked';
    document.querySelector('[data-lede]').textContent = depois
      ? 'Nothing has been charged yet. We take the payment 72 hours before the tour.'
      : 'The payment went through and the day is held for you alone.';

    document.querySelector('[data-ref]').textContent = d.reference || '\u2014';

    var ul = document.querySelector('[data-linhas]');
    [
      linha('Tour', d.tour),
      linha('Operator', d.operator),
      linha('Date', d.date),
      linha('Start time', d.time),
      linha('Group', d.pax ? (d.pax + (d.pax === 1 ? ' person' : ' people')) : ''),
      linha(depois ? 'To be charged' : 'Paid',
            d.amount != null ? (d.currency + ' ' + Number(d.amount).toFixed(2)) : ''),
      linha('Confirmation sent to', d.email)
    ].forEach(function (li) { if (li) ul.appendChild(li); });

    document.querySelector('[data-proximo]').textContent = depois
      ? 'We hold your card and charge it 72 hours before the tour. You will ' +
        'get an email before that happens. Until then nothing has left your ' +
        'account, and you can cancel free of charge.'
      : 'You will get a confirmation email with everything on it. The ' +
        'operator will contact you to agree the pick-up point.';

    est.hidden = true;
    det.hidden = false;
  }).catch(function () {
    falhar('We could not find that booking. Check the confirmation email, ' +
      'or send us a message with the reference from it.');
  });
})();
"""


def main():
    paises = por_pais(carregar())
    cancelamento(paises)
    avaliacoes(paises)
    confirmada(paises)


if __name__ == '__main__':
    main()
