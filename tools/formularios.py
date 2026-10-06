#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Os dois formularios publicos: /contact/ e /suppliers/apply/.

Nao sao paginas do portal: quem as le ainda nao tem conta nenhuma, por
isso levam o cabecalho e o rodape do site, como qualquer outra pagina.

O que estes dois formularios tem de diferente da maioria:

1. Gravam na base ANTES de tentarem enviar email. Um pedido que se perde
   porque o servico de email estava em baixo e uma venda perdida, e nem
   se sabe que existiu.
2. A validacao verdadeira esta na base, dentro de uma funcao. O que esta
   aqui no browser e para a pessoa nao ter de esperar pela rede para
   saber que se esqueceu do email — nao e a defesa.
3. Dizem o que acontece a seguir, com um prazo. "We'll be in touch" nao
   e informacao.

    python3 tools/formularios.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ligacao  # noqa: E402
import pagina  # noqa: E402
import politica  # noqa: E402
from pagina import cabecalho, carregar, e, envolver, escrever, por_pais, rodape  # noqa: E402

CORES = pagina.CORES

# A politica de cancelamento vive em tools/politica.py — um sitio so para
# a regra, para a pagina do tour e esta nunca prometerem coisas
# diferentes.
CANCELAMENTO = politica.FRASE


CSS = '''
.fcapa{background:var(--tinta);color:rgba(255,255,255,.86);
  padding:var(--e5) 0 var(--e5)}
.fcapa h1{color:var(--branco);max-width:20ch;margin:0 0 var(--e2);
  font-size:clamp(1.9rem,1.3rem + 2.4vw,3rem)}
.fcapa .lede{font-size:clamp(1.02rem,1rem + .3vw,1.16rem);max-width:54ch;
  margin:0;color:rgba(255,255,255,.8)}

.fcorpo{padding:var(--e5) 0 var(--e6)}
.fgrelha{display:grid;gap:var(--e5)}
@media (min-width:980px){
  .fgrelha{grid-template-columns:minmax(0,1.15fr) minmax(0,.85fr);
    align-items:start}
}

.fcx{background:var(--branco);box-shadow:0 1px 2px rgba(11,43,42,.05),
    0 10px 30px -18px rgba(11,43,42,.22);
  border-radius:var(--raio);padding:var(--e4)}
.fcx h2{margin:0 0 var(--e2);font-size:1.3rem}

.fcampo{margin-bottom:var(--e3)}
.fcampo label{display:block;margin-bottom:6px;font-weight:600;
  font-size:.88rem;color:var(--tinta)}
.fcampo .ajuda{display:block;margin-top:5px;font-size:.82rem;
  color:var(--mudo);line-height:1.45}
.fcampo input,.fcampo select,.fcampo textarea{width:100%%;
  box-sizing:border-box;font:400 .96rem/1.4 var(--tipo);color:var(--tinta);
  background:var(--branco);border:1px solid var(--mudo);border-radius:var(--r-p);
  padding:11px 12px}
.fcampo input:focus-visible,.fcampo select:focus-visible,
.fcampo textarea:focus-visible{outline:3px solid var(--cor);
  outline-offset:1px;border-color:var(--tinta)}
.fcampo input[aria-invalid="true"],.fcampo textarea[aria-invalid="true"]{
  border-color:#B3261E;border-width:2px}
.fcampo textarea{min-height:7rem;resize:vertical}
.f2{display:grid;gap:var(--e3)}
@media (min-width:600px){.f2{grid-template-columns:1fr 1fr}}
.obg{color:#8C1D18}

.faviso{margin:var(--e3) 0 0;padding:12px 14px;border-radius:var(--r-p);
  font-size:.92rem;line-height:1.55;
  background:var(--papel);color:var(--texto)}
.faviso-mal{border-left-color:#8C1D18;background:#FCEEEC;color:#5F1512}
.faviso-bem{border-left-color:#1B5E20;background:#EDF5EE;color:#14401A}

.flado .quadro{background:var(--branco);border-radius:var(--r-g);
  box-shadow:0 1px 2px rgba(11,43,42,.05),
    0 10px 30px -18px rgba(11,43,42,.22);
  padding:var(--e3);margin-bottom:var(--e3)}
.flado h3{margin:0 0 8px;font-size:1.02rem}
.flado p{margin:0 0 10px;font-size:.92rem;line-height:1.6;color:var(--texto)}
.flado p:last-child{margin-bottom:0}
.flado ol{margin:0;padding-left:1.1rem;font-size:.92rem;line-height:1.65;
  color:var(--texto)}
.flado ol li{margin-bottom:7px}

.bgrande{font:600 1rem/1 var(--tipo);background:var(--tinta);
  color:var(--papel);border:1px solid transparent;border-radius:var(--r-p);
  padding:15px 22px;cursor:pointer;width:100%%}
.bgrande:hover{background:var(--texto)}
.bgrande[disabled]{opacity:.55;cursor:not-allowed}
'''


# ---------------------------------------------------------------- contacto

JS_CONTACTO = r"""
(function () {
  'use strict';
  var f = document.getElementById('f-ped');
  if (!f || !window.ewt || window.ewt.avariado) return;

  // De onde vem o pedido. O tour e a data chegam pelo endereco quando a
  // pessoa clicou "Check this date" numa pagina de tour — assim nao tem
  // de escrever outra vez o que ja escolheu.
  var q = new URLSearchParams(location.search);
  var tour = q.get('tour') || '';
  var data = q.get('date') || '';
  var hora = q.get('time') || '';
  var de = q.get('from') || '';
  if (tour) {
    document.getElementById('tour').value = tour;
    var r = document.getElementById('sobre');
    if (r) {
      r.hidden = false;
      r.innerHTML = 'About <b>' + ewt.escapar(tour.replace(/-/g, ' ')) + '</b>'
        + (data ? ', on <b>' + ewt.escapar(data) + '</b>' : '')
        + (hora ? ' at <b>' + ewt.escapar(hora) + '</b>' : '')
        + '. <a href="/tours/' + ewt.escapar(tour) + '/">Back to the tour</a>';
    }
  }
  if (data) document.getElementById('quando').value = data;
  if (hora) {
    var h = document.getElementById('a-que-horas');
    if (h) h.value = hora;
  }
  if (de === 'operator') {
    var o = document.getElementById('op-nota');
    if (o) o.hidden = false;
  }

  function mal(id, texto) {
    var e = document.getElementById(id);
    if (e) { e.setAttribute('aria-invalid', 'true'); e.focus(); }
    ewt.dizer('av-ped', texto, 'mal');
  }

  f.addEventListener('submit', async function (ev) {
    ev.preventDefault();
    ['nome','email','mensagem'].forEach(function (id) {
      var e = document.getElementById(id);
      if (e) e.removeAttribute('aria-invalid');
    });
    ewt.dizer('av-ped', '', '');

    var nome = document.getElementById('nome').value.trim();
    var email = document.getElementById('email').value.trim();
    if (nome.length < 2) return mal('nome', 'We need a name to write back to.');
    if (email.indexOf('@') < 1) return mal('email', 'That email address is not complete.');

    var bt = document.getElementById('bt-ped');
    bt.disabled = true; bt.textContent = 'Sending…';

    var r = await ewt.sb.rpc('registar_pedido', {
      p: {
        kind: tour ? 'date' : (de === 'operator' ? 'operator' : 'general'),
        listing_slug: tour || null,
        wanted_on: document.getElementById('quando').value || null,
        wanted_at: document.getElementById('a-que-horas').value || null,
        party: document.getElementById('quantos').value || null,
        name: nome, email: email,
        phone: document.getElementById('telefone').value.trim(),
        message: document.getElementById('mensagem').value.trim(),
        source: location.pathname + location.search
      }
    });

    bt.disabled = false; bt.textContent = 'Send';

    if (r.error) { ewt.dizer('av-ped', ewt.legivel(r.error), 'mal'); return; }

    // A funcao devolve null quando e a mesma pessoa a submeter duas
    // vezes em dois minutos. Para quem clicou duas vezes o resultado e
    // o mesmo: esta enviado.
    f.hidden = true;
    document.getElementById('feito').hidden = false;
    document.getElementById('feito').focus();
  });
})();
"""


def contacto(paises):
    cab = cabecalho(paises=paises)
    corpo = '''%(cabecalho)s
<main id="principal">

<section class="fcapa">
  <div class="folha">
    <h1>Ask us about a date</h1>
    <p class="lede">Every tour here is private and runs on the day you
      choose, so availability is a conversation and not a button. Tell us
      the day and we come back with a yes or a no &mdash; not a
      maybe.</p>
  </div>
</section>

<section class="fcorpo">
  <div class="folha fgrelha">

    <div>
      <p class="faviso" id="sobre" hidden></p>
      <p class="faviso" id="op-nota" hidden>You came from the operators
        page. If you want to <b>list your tours</b> with us, the
        application form is at <a href="/suppliers/apply/">/suppliers/apply/</a>
        &mdash; it asks the right questions. This form reaches the same
        inbox either way.</p>

      <form class="fcx" id="f-ped" novalidate>
        <h2>Your enquiry</h2>
        <input type="hidden" id="tour">

        <div class="f2">
          <div class="fcampo">
            <label for="quando">The day you want</label>
            <input type="date" id="quando">
            <span class="ajuda">If you are flexible, leave it empty and
              say so below.</span>
          </div>
          <div class="fcampo">
            <label for="a-que-horas">Departure</label>
            <input type="time" id="a-que-horas" step="300">
            <span class="ajuda">If the tour has set departure times, the
              one you picked is already here.</span>
          </div>
        </div>

        <div class="f2">
          <div class="fcampo">
            <label for="quantos">How many of you</label>
            <input type="number" id="quantos" min="1" max="199">
            <span class="ajuda">The price depends on the vehicle, not on
              the headcount.</span>
          </div>
          <div class="fcampo"></div>
        </div>

        <div class="f2">
          <div class="fcampo">
            <label for="nome">Your name <span class="obg">*</span></label>
            <input type="text" id="nome" maxlength="120" required
                   autocomplete="name">
          </div>
          <div class="fcampo">
            <label for="email">Your email <span class="obg">*</span></label>
            <input type="email" id="email" maxlength="200" required
                   autocomplete="email" inputmode="email">
          </div>
        </div>

        <div class="fcampo">
          <label for="telefone">Phone or WhatsApp</label>
          <input type="tel" id="telefone" maxlength="40" autocomplete="tel">
          <span class="ajuda">Only if you would rather we called.</span>
        </div>

        <div class="fcampo">
          <label for="mensagem">Anything we should know</label>
          <textarea id="mensagem" maxlength="2000" rows="5"
            placeholder="Where you are staying, who is travelling, a stop you really want, anything that would change the day."></textarea>
        </div>

        <button type="submit" class="bgrande" id="bt-ped">Send</button>
        <p class="faviso" id="av-ped" role="status" hidden></p>
      </form>

      <div class="fcx" id="feito" hidden tabindex="-1">
        <h2>That is with us</h2>
        <p>We read every enquiry ourselves and answer within one working
          day. If the day you asked for is not possible, we say so and
          offer the nearest one that is &mdash; we do not leave you
          guessing.</p>
        <p><a href="/tours/">Keep looking at tours</a></p>
      </div>
    </div>

    <aside class="flado">
      <div class="quadro">
        <h3>What happens next</h3>
        <ol>
          <li>We check the date with the operator who runs that day.</li>
          <li>You get a written answer with the price for your group
            size &mdash; the whole vehicle, not per person.</li>
          <li>If you want it, we confirm it. Nothing is charged before
            you say yes.</li>
        </ol>
      </div>
      <div class="quadro">
        <h3>Cancellation</h3>
        %(cancelamento)s
      </div>
      <div class="quadro">
        <h3>Are you an operator?</h3>
        <p>If you run private tours and want them here,
          <a href="/suppliers/">read how it works</a> and
          <a href="/suppliers/apply/">apply</a>. We answer every
          application.</p>
      </div>
    </aside>

  </div>
</section>

</main>
%(rodape)s''' % {'cabecalho': cab, 'rodape': rodape(paises),
                 'cancelamento': '\n        '.join(
                     '<p>%s</p>' % x for x in politica.PARAGRAFOS)}

    html = envolver(
        'Contact us — Exclusive World Tours',
        'Ask about a date for a private day tour. We answer within one '
        'working day with a yes or a no, and the price for your group size.',
        CSS, corpo, js=JS_CONTACTO, noindex=True)
    html = html.replace('</head>', ligacao.SCRIPTS + '\n</head>')
    escrever(html, 'contact/index.html')


# ------------------------------------------------------------- candidatura

JS_CANDIDATURA = r"""
(function () {
  'use strict';
  var f = document.getElementById('f-cand');
  if (!f || !window.ewt || window.ewt.avariado) return;

  function mal(id, texto) {
    var e = document.getElementById(id);
    if (e) { e.setAttribute('aria-invalid', 'true'); e.focus(); }
    ewt.dizer('av-cand', texto, 'mal');
  }

  f.addEventListener('submit', async function (ev) {
    ev.preventDefault();
    ['empresa','pessoa','email','pais','cidade','tours']
      .forEach(function (id) {
        var e = document.getElementById(id);
        if (e) e.removeAttribute('aria-invalid');
      });
    ewt.dizer('av-cand', '', '');

    function v(id) { return document.getElementById(id).value.trim(); }

    if (v('empresa').length < 2) return mal('empresa', 'What is the company called?');
    if (v('pessoa').length < 2) return mal('pessoa', 'Who are we talking to?');
    if (v('email').indexOf('@') < 1) return mal('email', 'That email address is not complete.');
    if (!v('pais')) return mal('pais', 'Which country do you operate in?');
    if (!v('cidade')) return mal('cidade', 'Which city do you depart from?');
    if (v('tours').length < 30) {
      return mal('tours', 'Describe one tour properly — this is the part '
        + 'we actually read.');
    }

    var bt = document.getElementById('bt-cand');
    bt.disabled = true; bt.textContent = 'Sending…';

    var r = await ewt.sb.rpc('candidatar_operador', {
      p: {
        company: v('empresa'), contact_name: v('pessoa'), email: v('email'),
        phone: v('telefone'), website: v('sitio'),
        country: v('pais'), city: v('cidade'),
        fleet: v('frota'), tours_text: v('tours'),
        years: v('anos'), licence_ref: v('licenca')
      }
    });

    bt.disabled = false; bt.textContent = 'Send the application';

    if (r.error) { ewt.dizer('av-cand', ewt.legivel(r.error), 'mal'); return; }

    f.hidden = true;
    document.getElementById('cand-feito').hidden = false;
    document.getElementById('cand-feito').focus();
  });
})();
"""


def candidatura(paises):
    cab = cabecalho(paises=paises)
    corpo = '''%(cabecalho)s
<main id="principal">

<section class="fcapa">
  <div class="folha">
    <h1>Apply to sell your tours</h1>
    <p class="lede">Six questions about your company and one about a tour
      you are proud of. A person reads it &mdash; not a form that scores
      you &mdash; and you get an answer either way.</p>
  </div>
</section>

<section class="fcorpo">
  <div class="folha fgrelha">

    <div>
      <form class="fcx" id="f-cand" novalidate>
        <h2>Your company</h2>

        <div class="f2">
          <div class="fcampo">
            <label for="empresa">Company name <span class="obg">*</span></label>
            <input type="text" id="empresa" maxlength="180" required>
          </div>
          <div class="fcampo">
            <label for="pessoa">Your name <span class="obg">*</span></label>
            <input type="text" id="pessoa" maxlength="180" required
                   autocomplete="name">
          </div>
        </div>

        <div class="f2">
          <div class="fcampo">
            <label for="email">Email <span class="obg">*</span></label>
            <input type="email" id="email" maxlength="200" required
                   autocomplete="email" inputmode="email">
            <span class="ajuda">This becomes your sign-in for the
              operator portal. Use one you will keep.</span>
          </div>
          <div class="fcampo">
            <label for="telefone">Phone or WhatsApp</label>
            <input type="tel" id="telefone" maxlength="40">
          </div>
        </div>

        <div class="f2">
          <div class="fcampo">
            <label for="pais">Country <span class="obg">*</span></label>
            <input type="text" id="pais" maxlength="100" required>
          </div>
          <div class="fcampo">
            <label for="cidade">City you depart from <span class="obg">*</span></label>
            <input type="text" id="cidade" maxlength="100" required>
          </div>
        </div>

        <div class="f2">
          <div class="fcampo">
            <label for="sitio">Website</label>
            <input type="url" id="sitio" maxlength="280"
                   placeholder="https://">
          </div>
          <div class="fcampo">
            <label for="anos">Years operating</label>
            <input type="number" id="anos" min="0" max="120">
          </div>
        </div>

        <div class="fcampo">
          <label for="licenca">Tour or transport licence</label>
          <input type="text" id="licenca" maxlength="100">
          <span class="ajuda">If your country issues one. We do not
            invent a requirement that does not exist where you
            are.</span>
        </div>

        <div class="fcampo">
          <label for="frota">Your vehicles</label>
          <textarea id="frota" maxlength="900" rows="3"
            placeholder="One Mercedes V-Class for up to 6, two sedans for up to 3."></textarea>
          <span class="ajuda">Because we price by vehicle, this is what
            decides your price tiers.</span>
        </div>

        <div class="fcampo">
          <label for="tours">One tour you are proud of
            <span class="obg">*</span></label>
          <textarea id="tours" maxlength="3000" rows="6"
            placeholder="Where it starts, where it goes, how long it lasts, and the one thing about it that a coach tour cannot do."></textarea>
          <span class="ajuda">This is the part that decides the
            application. Write it as you would tell a guest, not as a
            brochure.</span>
        </div>

        <button type="submit" class="bgrande" id="bt-cand">Send the
          application</button>
        <p class="faviso" id="av-cand" role="status" hidden></p>
      </form>

      <div class="fcx" id="cand-feito" hidden tabindex="-1">
        <h2>Got it</h2>
        <p>We read applications ourselves and answer every one, including
          the ones we turn down. Expect a reply within two working
          days.</p>
        <p>If we go ahead, we link your email to your company and you
          sign in at <a href="/portal/">the operator portal</a> &mdash; no
          password, just a link we email you.</p>
      </div>
    </div>

    <aside class="flado">
      <div class="quadro">
        <h3>The terms, in three lines</h3>
        <p><b>Commission is %(comissao)s</b> of the price the guest pays.
          You set the price; we do not change it and we do not discount
          your tour to win a sale.</p>
        <p>Your content is read by a person before it goes on the site,
          and read again on every change.</p>
        <p>Your calendar is not reviewed at all. You close a day, it is
          closed &mdash; immediately.</p>
      </div>
      <div class="quadro">
        <h3>What we ask</h3>
        <p>That you run the tour yourself, hold whatever licence your
          country requires, price the whole vehicle rather than the
          seat, own your photographs, and keep the calendar honest.</p>
      </div>
      <div class="quadro">
        <h3>What we are not pretending</h3>
        <p>We are new. We will not show you visitor numbers, because
          they would not impress you and a number invented to impress
          you is the first thing you would check.</p>
      </div>
    </aside>

  </div>
</section>

</main>
%(rodape)s''' % {'cabecalho': cab, 'rodape': rodape(paises),
                 'comissao': '20%'}

    html = envolver(
        'Apply to sell your tours — Exclusive World Tours',
        'Apply to list your private day tours. 20% commission, you set '
        'the price, and a person reads every application.',
        CSS, corpo, js=JS_CANDIDATURA, noindex=True)
    html = html.replace('</head>', ligacao.SCRIPTS + '\n</head>')
    escrever(html, 'suppliers/apply/index.html')


def gerar():
    pagina.verificar_contraste()
    paises = por_pais(carregar())
    contacto(paises)
    candidatura(paises)


if __name__ == '__main__':
    gerar()
