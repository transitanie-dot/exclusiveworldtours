#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""/review/ — a pagina onde o cliente deixa a avaliacao.

So se chega aqui com um token, e o token so existe se a viagem
aconteceu. Nao ha formulario aberto, e nao vai haver: a unica coisa que
uma marca nova tem para vender e ser acreditada, e a primeira avaliacao
que alguem possa ter escrito sem viajar estraga todas as outras.

A pagina tem de funcionar para quem acabou de chegar a casa, cansado,
no telemovel. Por isso: uma pergunta obrigatoria (a nota), tudo o resto
opcional, e o nome nao se escreve — vem do pedido.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ligacao  # noqa: E402
import pagina  # noqa: E402
from pagina import cabecalho, carregar, envolver, escrever, por_pais, rodape  # noqa: E402

CSS = '''
.av-capa{background:var(--tinta);color:rgba(255,255,255,.86);
  padding:var(--e5) 0}
.av-capa h1{color:var(--branco);margin:0 0 var(--e2);max-width:20ch;
  font-size:clamp(1.8rem,1.3rem + 2.2vw,2.7rem)}
.av-capa .lede{max-width:52ch;margin:0;color:rgba(255,255,255,.8);
  font-size:clamp(1rem,1rem + .3vw,1.14rem)}

.av-corpo{padding:var(--e5) 0 var(--e6)}
.av-cx{max-width:40rem;background:var(--branco);border:1px solid var(--risco);
  border-radius:var(--raio);padding:var(--e4)}
.av-cx h2{margin:0 0 var(--e2);font-size:1.3rem}
.av-cx p{font-size:.96rem;line-height:1.65;color:var(--texto)}

/* ---------------------------------------------------------- estrelas
   Botoes de radio a serio por baixo: um leitor de ecra ouve "4 de 5",
   o teclado percorre-os com as setas, e o rato ve estrelas. */
.estrelas{display:flex;gap:4px;margin:0;padding:0;border:0}
.estrelas legend{padding:0;margin:0 0 8px;font-weight:600;font-size:.92rem;
  color:var(--tinta)}
.estrela{position:relative}
.estrela input{position:absolute;opacity:0;width:100%;height:100%;
  margin:0;cursor:pointer}
.estrela span{display:block;width:2.6rem;height:2.6rem;border-radius:6px;
  border:1px solid var(--risco);background:var(--branco);
  display:flex;align-items:center;justify-content:center;
  font-size:1.3rem;line-height:1;color:var(--risco)}
.estrela input:checked ~ span,
.estrela.acesa span{background:#FBF2EB;border-color:var(--cor);
  color:var(--cor-escura)}
.estrela input:focus-visible ~ span{outline:3px solid var(--cor);
  outline-offset:2px}
.estrelas-mini .estrela span{width:2.1rem;height:2.1rem;font-size:1.05rem}

.av-campo{margin-bottom:var(--e3)}
.av-campo label{display:block;margin-bottom:6px;font-weight:600;
  font-size:.9rem;color:var(--tinta)}
.av-campo input,.av-campo textarea{width:100%;box-sizing:border-box;
  font:400 .96rem/1.5 var(--tipo);color:var(--tinta);background:var(--branco);
  border:1px solid var(--mudo);border-radius:4px;padding:11px 12px}
.av-campo input:focus-visible,.av-campo textarea:focus-visible{
  outline:3px solid var(--cor);outline-offset:1px;border-color:var(--tinta)}
.av-campo textarea{min-height:7rem;resize:vertical}
.av-campo .ajuda{display:block;margin-top:5px;font-size:.82rem;
  color:var(--mudo);line-height:1.45}

.av-temas{display:grid;gap:var(--e3);margin:var(--e3) 0}
@media(min-width:620px){.av-temas{grid-template-columns:1fr 1fr}}

.av-aviso{margin:var(--e3) 0 0;padding:12px 14px;border-radius:4px;
  font-size:.92rem;line-height:1.55;border-left:4px solid var(--mudo);
  background:var(--papel);color:var(--texto)}
.av-aviso-mal{border-left-color:#8C1D18;background:#FCEEEC;color:#5F1512}
.av-aviso-bem{border-left-color:#1B5E20;background:#EDF5EE;color:#14401A}

.av-bt{font:600 1rem/1 var(--tipo);background:var(--tinta);color:var(--papel);
  border:1px solid transparent;border-radius:4px;padding:15px 22px;
  cursor:pointer;width:100%}
.av-bt:hover{background:var(--texto)}
.av-bt[disabled]{opacity:.55;cursor:not-allowed}
'''


def estrelas(nome, rotulo, ajuda='', mini=False):
    """Cinco botoes de radio com cara de estrelas."""
    opcoes = []
    for n in range(1, 6):
        opcoes.append(
            '<span class="estrela"><input type="radio" name="%(n)s" '
            'id="%(n)s-%(i)d" value="%(i)d"><label class="pc-oculto" '
            'for="%(n)s-%(i)d">%(i)d out of 5</label>'
            '<span aria-hidden="true">&#9733;</span></span>'
            % {'n': nome, 'i': n})
    return ('<fieldset class="estrelas-cx"><legend>%(rotulo)s</legend>'
            '<div class="estrelas%(mini)s" data-estrelas="%(n)s">%(o)s</div>'
            '%(ajuda)s</fieldset>'
            % {'rotulo': rotulo, 'n': nome, 'o': '\n'.join(opcoes),
               'mini': ' estrelas-mini' if mini else '',
               'ajuda': ('<span class="ajuda">%s</span>' % ajuda) if ajuda else ''})


JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  var TOKEN = new URLSearchParams(location.search).get('t') || '';

  // As estrelas acendem-se ate a que esta escolhida. O estado verdadeiro
  // esta nos radios por baixo — isto e so pintura, e e por isso que
  // funciona sem rato e sem JavaScript nenhum a ler o valor.
  function pintar(caixa) {
    var rs = [].slice.call(caixa.querySelectorAll('input[type=radio]'));
    var escolhida = -1;
    rs.forEach(function (r, i) { if (r.checked) escolhida = i; });
    rs.forEach(function (r, i) {
      r.closest('.estrela').classList.toggle('acesa', i <= escolhida);
    });
  }
  [].slice.call(document.querySelectorAll('[data-estrelas]')).forEach(function (c) {
    c.addEventListener('change', function () { pintar(c); });
    pintar(c);
  });

  function nota(nome) {
    var r = document.querySelector('input[name="' + nome + '"]:checked');
    return r ? r.value : null;
  }

  function mostrar(qual) {
    ['carrega', 'form', 'erro', 'feito'].forEach(function (id) {
      var e = document.getElementById(id);
      if (e) e.hidden = (id !== qual);
    });
  }

  function recusar(titulo, texto) {
    document.getElementById('erro-t').textContent = titulo;
    document.getElementById('erro-p').innerHTML = texto;
    mostrar('erro');
  }

  (async function () {
    if (!TOKEN) {
      recusar('This link is incomplete',
        'A review link comes from us by email, after your day. If you '
        + 'have one, open it again from the email — copying part of '
        + 'it does not work.');
      return;
    }

    var r = await ewt.sb.rpc('convite', { p_token: TOKEN });
    if (r.error) {
      recusar('We could not check that link',
        'Try again in a minute. If it keeps happening, '
        + '<a href="/contact/">write to us</a> and we will sort it out.');
      return;
    }
    var c = (r.data && r.data.length) ? r.data[0] : null;

    if (!c) {
      recusar('That link is not one of ours',
        'Review links are sent by email after a day out. If yours was '
        + 'forwarded or retyped, ask the person who travelled to open '
        + 'theirs.');
      return;
    }
    if (!c.valido) {
      if (c.motivo === 'used') {
        recusar('That review is already in',
          'Thank you — it is already on the site. A link works once, '
          + 'so nobody can leave two.');
      } else {
        recusar('That link has expired',
          'Review links last 90 days. If you still want to say something '
          + 'about your day, <a href="/contact/">write to us</a> — we '
          + 'read everything.');
      }
      return;
    }

    document.getElementById('ola').textContent =
      (c.first_name ? c.first_name + ', how' : 'How') + ' was the day?';
    document.getElementById('qual').innerHTML =
      '<b>' + ewt.escapar(c.tour) + '</b>'
      + (c.travelled_on ? ', on ' + ewt.escapar(c.travelled_on) : '');
    mostrar('form');
  })();

  document.getElementById('f-av').addEventListener('submit', async function (ev) {
    ev.preventDefault();
    ewt.dizer('av-erro', '', '');

    var geral = nota('rating');
    if (!geral) {
      ewt.dizer('av-erro', 'Give the day a rating — it is the one thing '
        + 'we need.', 'mal');
      document.querySelector('[data-estrelas="rating"] input').focus();
      return;
    }

    var bt = document.getElementById('bt-av');
    bt.disabled = true; bt.textContent = 'Sending…';

    var res = await ewt.sb.rpc('deixar_avaliacao', {
      p_token: TOKEN,
      p: {
        rating: geral,
        r_driver: nota('r_driver'), r_vehicle: nota('r_vehicle'),
        r_value: nota('r_value'), r_organising: nota('r_organising'),
        title: document.getElementById('titulo').value.trim(),
        body: document.getElementById('texto').value.trim(),
        author_country: document.getElementById('pais').value.trim()
      }
    });

    bt.disabled = false; bt.textContent = 'Send my review';

    if (res.error) { ewt.dizer('av-erro', ewt.legivel(res.error), 'mal'); return; }
    mostrar('feito');
    document.getElementById('feito').focus();
  });
})();
"""


def corpo():
    return '''%(cabecalho)s
<main id="principal">

<section class="av-capa">
  <div class="folha">
    <h1 id="ola">How was the day?</h1>
    <p class="lede" id="qual">Loading&hellip;</p>
  </div>
</section>

<section class="av-corpo">
  <div class="folha">

    <p class="carrega" id="carrega">Checking your link&hellip;</p>

    <div class="av-cx" id="erro" hidden>
      <h2 id="erro-t"></h2>
      <p id="erro-p"></p>
      <p><a href="/tours/">See the tours</a></p>
    </div>

    <div class="av-cx" id="form" hidden>
      <form id="f-av" novalidate>
        %(geral)s

        <p class="ajuda" style="margin:var(--e2) 0 var(--e3)">Everything
          below is optional. One star and nothing else is a complete
          review, and we would rather have that than nothing.</p>

        <div class="av-temas">
          %(driver)s
          %(vehicle)s
          %(value)s
          %(organising)s
        </div>

        <div class="av-campo">
          <label for="titulo">One line, if you have one</label>
          <input type="text" id="titulo" maxlength="140"
                 placeholder="The stop at Cabo da Roca made the day">
        </div>

        <div class="av-campo">
          <label for="texto">What should the next person know?</label>
          <textarea id="texto" maxlength="4000" rows="6"
            placeholder="What the driver did well, what you would do differently, whether the timings worked."></textarea>
          <span class="ajuda">Write it for someone deciding whether to
            book, not for us. The operator reads it and can reply in
            public.</span>
        </div>

        <div class="av-campo">
          <label for="pais">Where you travelled from</label>
          <input type="text" id="pais" maxlength="80" placeholder="Brazil">
          <span class="ajuda">Optional. It helps other travellers place
            your review.</span>
        </div>

        <button type="submit" class="av-bt" id="bt-av">Send my review</button>
        <p class="av-aviso" id="av-erro" role="status" hidden></p>

        <p class="ajuda" style="margin-top:var(--e3)">Your review goes on
          the site with your first name only. We do not edit it, and we
          do not remove it because it is critical &mdash; only if it
          breaks the narrow rules on
          <a href="/reviews-policy/">how reviews work here</a>.</p>
      </form>
    </div>

    <div class="av-cx" id="feito" hidden tabindex="-1">
      <h2>Thank you &mdash; that is in</h2>
      <p>It appears on the tour page the next time the site is built,
        usually within a day. The operator can reply in public, and
        cannot contact you about it privately.</p>
      <p><a href="/tours/">See the other tours</a></p>
    </div>

  </div>
</section>

</main>
%(rodape)s''' % {
        'cabecalho': cabecalho(),
        'rodape': rodape(por_pais(carregar())),
        'geral': estrelas('rating', 'The day overall',
                          'The only answer we actually need.'),
        'driver': estrelas('r_driver', 'Your driver-guide', mini=True),
        'vehicle': estrelas('r_vehicle', 'The vehicle', mini=True),
        'value': estrelas('r_value', 'Worth the money', mini=True),
        'organising': estrelas('r_organising', 'How it was organised', mini=True),
    }


def gerar():
    pagina.verificar_contraste()
    html = envolver(
        'Leave a review — Exclusive World Tours',
        'Tell us how your private day went.',
        CSS, corpo(), js=JS, noindex=True)
    html = html.replace('</head>', ligacao.SCRIPTS + '\n</head>')
    escrever(html, 'review/index.html')


if __name__ == '__main__':
    gerar()
