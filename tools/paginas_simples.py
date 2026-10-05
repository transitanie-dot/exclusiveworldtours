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


def main():
    paises = por_pais(carregar())
    cancelamento(paises)
    avaliacoes(paises)


if __name__ == '__main__':
    main()
