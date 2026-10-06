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

import datetime  # noqa: E402

import empresa  # noqa: E402
import ligacao  # noqa: E402
import politica  # noqa: E402
import procura  # noqa: E402
from pagina import (cabecalho, carregar, envolver, escrever,  # noqa: E402
                    por_pais, rodape)
from pagina import e  # noqa: E402

# A data que as paginas legais mostram. E a data de GERACAO e nao uma
# constante escrita a mao: uma politica que diz "actualizada em Janeiro"
# e foi mexida em Marco e pior do que nao ter data nenhuma.
DATA = datetime.date.today().strftime('%d %B %Y')

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


# =====================================================================
# AS PAGINAS LEGAIS
# =====================================================================
# A partir do momento em que o site aceita um cartao, estas duas deixam
# de ser boa pratica e passam a ser obrigacao. Mas o que as torna uteis
# nao e a obrigacao: e dizerem, antes de alguem pagar, as tres coisas
# que a pessoa vai querer saber quando houver um problema — com quem e
# que ela tem contrato, quem conduz o carro, e a quem se queixa.
#
# O ponto que estas paginas tem de deixar sem duvida e aquele em que um
# marketplace se engana sempre: **o contrato do dia e com o operador, e
# nao connosco.** Nos vendemos, cobramos e respondemos; quem conduz e
# ele. Escrever isto com clareza e o que evita a discussao de quem e
# responsavel pelo que, no dia em que ela aparecer.
#
# O bloco de identidade vem do tools/empresa.py, e se os dados nao
# estiverem la estas paginas NAO SE ESCREVEM. Ver a nota desse ficheiro.

CSS_LEGAL = '''
.lg .dentro{max-width:42rem}
.lg h2{margin:var(--e5) 0 var(--e2);font-size:1.35rem;line-height:1.25}
.lg h3{margin:var(--e4) 0 var(--e2);font-size:1.08rem;line-height:1.35;
  color:var(--tinta)}
.lg p,.lg li{font-size:1.01rem;line-height:1.72;color:var(--texto)}
.lg .data{font-size:.9rem;color:var(--mudo);margin:0 0 var(--e4)}

/* O bloco de identidade. Uma lista de definicoes e nao uma tabela: sao
   pares nome/valor, que e exactamente o que um <dl> e, e num telemovel
   uma tabela de duas colunas com moradas dentro parte-se. */
.ident{margin:var(--e4) 0 0;padding:var(--e4);border-radius:var(--raio);
  background:var(--papel)}
.ident dl{margin:0;display:grid;gap:10px}
.id-l{display:flex;flex-wrap:wrap;gap:4px 14px}
.id-l dt{min-width:12rem;color:var(--mudo);font-size:.93rem;font-weight:500}
.id-l dd{margin:0;color:var(--tinta);font-weight:600;font-size:.96rem}
'''


def _capa(titulo, lede):
    return '''<section class="pcapa">
  <div class="folha">
    <h1>%s</h1>
    <p class="lede">%s</p>
  </div>
</section>''' % (titulo, lede)


def _identidade():
    return '''<div class="ident">
  <h3 style="margin-top:0">Who you are dealing with</h3>
  <dl>
%s
  </dl>
</div>''' % empresa.identidade_html(e)


def termos(paises):
    corpo = '''%(cabecalho)s
<main id="principal" class="lg">

%(capa)s

<section class="ptexto">
  <div class="folha">
    <div class="dentro">

      <p class="data">Last updated %(data)s.</p>

      <h2>What we are</h2>
      <p>%(marca)s is a marketplace. We list private day tours run by
        independent local operators, we take the booking, and we take the
        payment. We do not own the vehicles and we do not employ the
        drivers.</p>
      <p>This matters more than it sounds, so it is worth being plain
        about it: <b>your contract for the day itself is with the
        operator</b> who runs the tour. Our contract with you is for
        finding it, booking it, holding the money and standing behind the
        booking. Where something goes wrong on the day, the operator is
        responsible for it &mdash; and we are the people you tell.</p>

      <h2>Prices</h2>
      <p>Prices on this site are for the <b>whole vehicle</b>, not per
        person. A price for up to four people is the same price whether
        two of you travel or four. Where a tour sets a maximum group
        size, that maximum is the number of seats in the vehicle.</p>
      <p>The price shown at the moment you book is the price you pay. It
        includes the vehicle, the driver and their fuel for the route
        described. It does not include entrance tickets, meals, or
        anything the listing says is not included.</p>
      <p>Where a tour lets infants travel on an adult&rsquo;s lap, those
        infants do not take a seat and do not count towards the price
        band. Everyone else does.</p>

      <h2>Booking and paying</h2>
      <p>You can pay when you book, or &mdash; on tours and dates where
        we offer it &mdash; book now and be charged before you travel. If
        you choose to pay later, we save your card at the time of booking
        and charge it shortly before departure. We tell you the date we
        will charge it.</p>
      <p>A booking is confirmed when the payment, or the saved card, is
        accepted. Until then the vehicle is held for you for a short
        window only.</p>
      <p>If a later charge fails, we will tell you and try again. A
        booking we cannot charge is cancelled, and we say so rather than
        letting you arrive at a pick-up that is not coming.</p>

      <h2>Cancelling</h2>
      <p>%(cancelamento)s</p>
      <p>If the operator cancels &mdash; a vehicle breaks down, a driver
        falls ill and no replacement is possible &mdash; you are refunded
        in full, whatever the notice. That is not a goodwill gesture; it
        is the rule.</p>

      <h2>If you do not turn up</h2>
      <p>If nobody is at the pick-up point and the driver cannot reach
        you, the day is not refunded. The driver records how long they
        waited and what they tried. We will always look at that record
        with you if you think it is wrong.</p>

      <h2>Changes to a booking</h2>
      <p>Ask us. Dates, times and pick-up points can often be moved if
        the operator still has the day free, and it costs nothing to
        ask. What we cannot do is promise a change before checking with
        the operator.</p>

      <h2>Reviews</h2>
      <p>Only someone who actually travelled can leave a review, because
        the invitation to write one is sent against a real booking. We do
        not remove a review for being unflattering. We remove it for
        being abusive, for naming a private individual, or for not being
        about the tour.</p>

      <h2>When things go wrong</h2>
      <p>Write to <a href="mailto:%(email)s">%(email)s</a> and tell us
        what happened. We would rather hear it from you than read it
        later. Nothing on this page takes away rights you have under
        consumer law where you live.</p>

      %(identidade)s

    </div>
  </div>
</section>

</main>
%(rodape)s''' % {'cabecalho': cabecalho(paises=paises),
                 'rodape': rodape(paises),
                 'capa': _capa('Terms',
                   'What you are buying, who you are buying it from, and '
                   'what happens when something does not go to plan.'),
                 'data': DATA,
                 'marca': e(empresa.NOME_COMERCIAL),
                 'email': e(empresa.EMAIL),
                 'cancelamento': politica.FRASE,
                 'identidade': _identidade()}

    escrever(envolver(
        'Terms — Exclusive World Tours',
        'The terms of booking a private day tour through Exclusive World '
        'Tours: prices, paying, cancelling, and who is responsible for '
        'what.',
        CSS + CSS_LEGAL, corpo, js=procura.JS), 'terms/index.html')


def privacidade(paises):
    corpo = '''%(cabecalho)s
<main id="principal" class="lg">

%(capa)s

<section class="ptexto">
  <div class="folha">
    <div class="dentro">

      <p class="data">Last updated %(data)s.</p>

      <h2>The short version</h2>
      <p>We ask for what a driver needs to collect you and what a bank
        needs to take a payment, and nothing else. We do not sell your
        details to anybody, for any price. Your card number never
        reaches us.</p>

      <h2>What we collect, and why</h2>
      <h3>When you book</h3>
      <p>Your name, email, phone number, the pick-up point and anything
        you tell us about the group &mdash; a child seat, a wheelchair, a
        flight number. We need it to make the booking exist and to let
        the driver find you.</p>
      <h3>When you pay</h3>
      <p>The card itself is handled by %(stripe)s. It goes from your
        browser to them; it does not pass through our servers and we
        never hold the number. What we keep is the fact that a payment
        succeeded, for how much, and a reference we can use to refund
        it.</p>
      <p>If you choose to pay later, %(stripe)s keeps the card for us
        against the booking, and we hold only a token &mdash; a reference
        that lets us charge that card once, for that booking, and lets us
        do nothing else with it.</p>
      <h3>When you ask us something</h3>
      <p>What you wrote and how to reply to it.</p>
      <h3>When you use the site</h3>
      <p>What was searched for, so we know which cities to add tours in.
        This is not tied to your name.</p>

      <h2>Who else sees it</h2>
      <p><b>The operator who runs your tour</b> sees your name, your
        phone number, your pick-up point and your notes. They cannot see
        what you paid us; they see what they are owed. A driver who
        cannot phone you is a driver who leaves without you, which is why
        the phone number goes across.</p>
      <p><b>%(stripe)s</b> processes the payment.</p>
      <p>Nobody else. We do not sell or rent your details, and we do not
        pass them to advertisers.</p>

      <h2>How long we keep it</h2>
      <p>A booking and its payment record are kept for as long as tax and
        accounting rules require &mdash; those rules, not our preference,
        set the clock. An enquiry that never became a booking is kept
        while it is useful to answer you, and then deleted.</p>

      <h2>What you can ask us to do</h2>
      <ul>
        <li>Tell you what we hold about you.</li>
        <li>Correct it when it is wrong.</li>
        <li>Delete it, where no law requires us to keep it &mdash; a paid
          booking is the usual exception, and we will say so rather than
          quietly refusing.</li>
        <li>Send you a copy in a form you can take elsewhere.</li>
        <li>Object to us using it, or ask us to stop while a complaint is
          looked at.</li>
      </ul>
      <p>Write to <a href="mailto:%(email)s">%(email)s</a>. We answer
        within a month, and usually much sooner. If you are not satisfied
        with the answer, you can complain to the data protection
        authority where you live.</p>

      <h2>What this site stores in your browser</h2>
      <p>What is needed for it to work: that you are signed in, if you
        are an operator, and which theme you chose. No advertising
        trackers and no third-party analytics that follow you to other
        sites.</p>

      %(identidade)s

    </div>
  </div>
</section>

</main>
%(rodape)s''' % {'cabecalho': cabecalho(paises=paises),
                 'rodape': rodape(paises),
                 'capa': _capa('Privacy',
                   'What we ask for, who sees it, how long we keep it, and '
                   'what you can tell us to do with it.'),
                 'data': DATA,
                 'stripe': e(empresa.PROCESSADOR),
                 'email': e(empresa.EMAIL),
                 'identidade': _identidade()}

    escrever(envolver(
        'Privacy — Exclusive World Tours',
        'What Exclusive World Tours collects when you book a private day '
        'tour, who it is shared with, and what you can ask us to do with '
        'it.',
        CSS + CSS_LEGAL, corpo, js=procura.JS), 'privacy/index.html')


def main():
    paises = por_pais(carregar())
    cancelamento(paises)
    avaliacoes(paises)
    confirmada(paises)

    # As paginas legais so saem com os dados da empresa confirmados. Ver
    # a nota no topo do tools/empresa.py: um numero de registo inventado
    # nao e um marcador de lugar, e uma declaracao falsa sobre quem
    # recebe o dinheiro.
    if empresa.completa():
        termos(paises)
        privacidade(paises)
    else:
        print('  FALTA  ' + empresa.porque_nao())


if __name__ == '__main__':
    main()
