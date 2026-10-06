#!/usr/bin/env python3
"""
/suppliers/ — a montra do canal de operadores.

E a pagina que angaria. Quem a le e um operador local que ja vende na
Viator ou na GetYourGuide e esta a decidir se vale a pena mais um canal.
Por isso diz tres coisas que esses dois nao dizem com clareza, e diz-as
primeiro: quanto fica para ele, quem manda no preco, e quando recebe.

O que esta pagina NAO diz, de proposito:
- numero de visitantes, de reservas ou de operadores. Ainda nao ha
  nenhum, e um numero inventado numa pagina de angariacao e a primeira
  coisa que um operador experiente vai verificar;
- prazos de pagamento concretos, enquanto o Ricardo nao decidir o fluxo
  do dinheiro.

A comissao ja esta decidida — 20%, a 2 de outubro de 2026 — e aparece na
pagina a partir da constante COMISSAO, num sitio so. O mesmo numero esta
em `commission_rate` na base, por operador, porque ha sempre um caso
especial e o caso especial nao deve obrigar a publicar codigo.

    python3 tools/fornecedores.py      # escreve suppliers/index.html
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import procura  # noqa: E402
from pagina import (cabecalho, carregar, e, envolver, escrever,  # noqa: E402
                    por_pais, rodape)

# Decidido pelo Ricardo a 2 de outubro de 2026. Troca-se aqui e so aqui;
# o valor por operador vive em `operators.commission_rate` na base.
COMISSAO = '20%'

CSS = '''
.capa-f{background:var(--tinta);color:rgba(255,255,255,.86);
  padding:var(--e5) 0 var(--e5)}
.capa-f h1{color:var(--branco);max-width:16ch;
  font-size:clamp(2.1rem,1.4rem + 2.8vw,3.5rem);margin:0 0 var(--e2)}
.capa-f .lede{font-size:clamp(1.05rem,1rem + .35vw,1.2rem);max-width:52ch;
  margin:0 0 var(--e4);color:rgba(255,255,255,.8)}
.capa-g{display:grid;grid-template-columns:1.1fr .9fr;gap:var(--e5);
  align-items:center}
@media (max-width:900px){.capa-g{grid-template-columns:1fr;gap:var(--e4)}}

/* Era uma caixa com molduras de 1px a dividir tres celulas — uma
   tabela disfarcada. Sao tres afirmacoes independentes, e passam a tres
   cartoes com espaco entre eles, que e o que sao. */
.tres{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
@media (max-width:760px){.tres{grid-template-columns:1fr}}
.tres div{background:rgba(255,255,255,.1);padding:var(--e3);
  border-radius:var(--r-m)}
.tres b{display:block;font-family:var(--tipo-titulo);color:var(--branco);
  font-size:1.05rem;margin:0 0 5px}
.tres p{margin:0;font-size:14px;color:rgba(255,255,255,.72)}

.passos-f{counter-reset:p}
.passo-f{display:grid;grid-template-columns:46px 1fr;gap:var(--e3);
  padding:0 0 var(--e4);position:relative}
.passo-f::before{counter-increment:p;content:counter(p,decimal-leading-zero);
  font-family:var(--mono);font-size:13px;color:var(--cor-escura);
  font-weight:600;padding-top:3px}
.passo-f::after{content:'';position:absolute;left:22px;top:26px;bottom:8px;
  width:1px;background:var(--risco)}
.passo-f:last-child::after{display:none}
.passo-f h3{font-size:1.1rem;margin:0 0 5px}
.passo-f p{margin:0;color:var(--mudo);max-width:56ch}
.passo-f .marca-rev{display:inline-block;margin-top:9px;font-size:12px;
  border-radius:var(--r-p);padding:3px 9px;border:1px solid var(--risco);
  background:var(--branco);color:var(--tinta)}

.duas-c{display:grid;grid-template-columns:1fr 1fr;gap:var(--e5)}
@media (max-width:860px){.duas-c{grid-template-columns:1fr;gap:var(--e4)}}
.lista-v{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.lista-v li{display:flex;gap:11px;align-items:flex-start;font-size:15px}
.lista-v svg{width:17px;height:17px;flex:none;margin-top:3px;fill:none;
  stroke:var(--cor-escura);stroke-width:2.6;stroke-linecap:round;
  stroke-linejoin:round}

.quadro{border-radius:var(--r-g);box-shadow:0 1px 2px rgba(11,43,42,.05),
    0 10px 30px -18px rgba(11,43,42,.22);
  background:var(--branco);padding:var(--e3)}
.quadro h3{font-size:1.05rem;margin:0 0 10px}
.quadro p{margin:0 0 10px;color:var(--mudo);font-size:14.5px}
.quadro p:last-child{margin:0}

.cand{background:var(--tinta);color:rgba(255,255,255,.84);
  padding:var(--e5) 0}
.cand h2{color:var(--branco);margin:0 0 var(--e2)}
.cand p{max-width:54ch;margin:0 0 var(--e3);color:rgba(255,255,255,.78)}
/* os rotulos pequenos nestas duas seccoes estao sobre fundo escuro e
   tem de usar as cores de fundo escuro, senao ficam a 2.8:1 */
/* o botao por omissao e tinta sobre claro; aqui o fundo e tinta e ele
   desaparecia */
.capa-f .botao{background:var(--branco);color:var(--tinta)}
.capa-f .botao:hover{background:var(--papel)}
.capa-f .rot,.cand .rot{color:rgba(255,255,255,.62)}
.capa-f .rot b,.cand .rot b{color:var(--cor-clara)}
.capa-f .rot::after,.cand .rot::after{background:rgba(255,255,255,.18)}
.cand .botao{background:var(--branco);color:var(--tinta)}
.cand .botao:hover{background:var(--papel)}
.aviso{margin-top:var(--e3);font-size:13.5px;color:rgba(255,255,255,.6);
  max-width:54ch}
'''

VISTO = ('<svg viewBox="0 0 24 24" aria-hidden="true">'
         '<path d="M4 12.5 L9.5 18 L20 6.5"/></svg>')


def main():
    tours = carregar()
    paises = por_pais(tours)

    corpo = '''%(cabecalho)s
<main id="principal">

<section class="capa-f">
  <div class="folha capa-g">
    <div>
      <p class="rot"><b>&mdash;</b> For operators</p>
      <h1>Your day, sold properly.</h1>
      <p class="lede">We list private day tours run by local operators.
        One vehicle, one group, a price for the whole group. If that is
        what you already do, we would like to carry it.</p>
      <a class="botao" href="#apply">Apply to list with us</a>
    </div>
    <div class="tres">
      <div><b>You set the price</b>
        <p>You give us the price for each vehicle size. We do not discount
          your work to win a booking.</p></div>
      <div><b>You own the day</b>
        <p>Your vehicle, your guide, your route. We send you the group and
          stay out of the way.</p></div>
      <div><b>No exclusivity</b>
        <p>Keep selling wherever you already sell. Nothing here asks you to
          stop.</p></div>
    </div>
  </div>
</section>

<section class="bloco folha" data-rev>
  <p class="rot"><b>01</b> How listing works</p>
  <h2>Everything you publish is read by a person first</h2>
  <p class="intro" style="color:var(--mudo);max-width:56ch;margin-bottom:var(--e4)">
    Not a filter, not a score &mdash; a person. It is slower than the big
    platforms and it is the reason a traveller can trust what the page
    says.</p>

  <div class="passos-f">
    <div class="passo-f">
      <div>
        <h3>You apply</h3>
        <p>Company, where you operate, what you run, and your licence if
          your country issues one. We answer every application.</p>
      </div>
    </div>
    <div class="passo-f">
      <div>
        <h3>You build the listing</h3>
        <p>Route, stops with times, what the price covers, what it does
          not, and a price for each vehicle size. Your own photographs.</p>
      </div>
    </div>
    <div class="passo-f">
      <div>
        <h3>We read it</h3>
        <p>We check the day is real, the times add up and the price is
          clear. If something is off we tell you exactly what, and you
          change it.</p>
        <span class="marca-rev">Reviewed before it goes live</span>
      </div>
    </div>
    <div class="passo-f">
      <div>
        <h3>It goes live</h3>
        <p>The page is built and published. Later edits to the text, the
          photographs or the price go through the same reading.</p>
        <span class="marca-rev">Reviewed again on every content change</span>
      </div>
    </div>
    <div class="passo-f">
      <div>
        <h3>Your calendar is yours</h3>
        <p>Closing a day, blocking a week, marking a date sold &mdash; that
          is instant and nobody reviews it. You can shut tomorrow at
          eleven at night and the site knows immediately.</p>
        <span class="marca-rev">No review, applies at once</span>
      </div>
    </div>
  </div>
</section>

<section class="banda-b">
  <div class="folha bloco duas-c" data-rev>
    <div>
      <p class="rot"><b>02</b> What we ask of you</p>
      <h2>Short list, no surprises</h2>
      <ul class="lista-v" style="margin-top:var(--e3)">
        <li>%(v)s<span>You run the tour yourself, with your own vehicle and
          driver or guide.</span></li>
        <li>%(v)s<span>You hold whatever licence and insurance your country
          requires.</span></li>
        <li>%(v)s<span>The price you give us is the price for the whole
          vehicle, by group size.</span></li>
        <li>%(v)s<span>Your photographs are yours to use.</span></li>
        <li>%(v)s<span>You keep the calendar honest. A day shown open is a
          day you can run.</span></li>
      </ul>
    </div>
    <div>
      <p class="rot"><b>03</b> What you get</p>
      <h2>And what we are not pretending</h2>
      <div class="quadro" style="margin-top:var(--e3)">
        <h3>Commission is %(com)s</h3>
        <p>Of the price the guest pays. You set that price and we do not
          touch it &mdash; we do not discount your tour to win a sale, and
          there is no fee to be listed, no fee per listing and no
          fee to be seen.</p>
        <p>On a &euro;790 day that is &euro;158 to us and &euro;632 to
          you, and the arithmetic is in the portal next to every price
          you type.</p>
      </div>
      <div class="quadro" style="margin-top:var(--e3)">
        <h3>Being straight with you</h3>
        <p>We are new. We are not going to show you visitor numbers or
          booking volumes, because they would not be impressive and a
          number invented to impress you is the first thing you would
          check.</p>
        <p>What we have is %(nt)d days in %(np)d countries, a page that
          explains a tour better than any marketplace we have seen, and
          room for operators who want to be listed properly rather than
          buried on page nine.</p>
      </div>
    </div>
  </div>
</section>

<section class="cand" id="apply">
  <div class="folha">
    <p class="rot"><b>04</b> Apply</p>
    <h2>Tell us what you run</h2>
    <p>Send us your company, the city you operate from, and one tour you
      are proud of. If it fits, we open your account and walk you through
      the first listing. Commission is %(com)s of what the guest pays, and
      you set the price.</p>
    <a class="botao" href="/suppliers/apply/">Start an application</a>
    <p class="aviso">The operator portal is open: you write your own
      listings, submit them for reading, and run your own calendar.
      <a href="/portal/">Sign in</a> if you already have an account.</p>
  </div>
</section>

</main>
%(rodape)s''' % {
        'cabecalho': cabecalho(paises=paises),
        'v': VISTO, 'com': COMISSAO,
        'nt': len(tours), 'np': len(paises),
        'rodape': rodape(paises),
    }

    html = envolver(
        'For operators — Exclusive World Tours',
        'List your private day tours with Exclusive World Tours. You set '
        'the price, you own the day, and every listing is read by a person '
        'before it goes live.',
        CSS, corpo, js=procura.JS)
    escrever(html, 'suppliers/index.html')


if __name__ == '__main__':
    main()
