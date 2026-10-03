# -*- coding: utf-8 -*-
"""A conta do operador: o que o sistema sabe sobre ele.

Pagina curta de proposito. O que um operador vem aqui ver e sempre uma
de tres coisas: com que email entrou, qual e a comissao que lhe estao a
cobrar, e quem mais da empresa tem acesso. As tres estao a vista sem
clicar em nada.

A comissao mostra-se com a conta feita. Uma percentagem sozinha obriga
cada operador a ir buscar a calculadora, e um numero que cada um calcula
por si e um numero sobre o qual se vai discutir.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pagina
import portal_base
from portal import NAV

CORES = pagina.CORES

CSS = """
.ct { display: grid; gap: 1.1rem; }
@media (min-width: 900px) { .ct { grid-template-columns: 1fr 1fr; } }
.ct-l { display: flex; justify-content: space-between; gap: 1rem;
  padding: .7rem 0; border-bottom: 1px solid %(risco)s;
  font: 400 .92rem/1.5 'Inter', system-ui, sans-serif; color: %(texto)s; }
.ct-l:last-child { border-bottom: 0; }
.ct-l b { color: %(tinta)s; text-align: right; }
.conta-g {
  background: %(papel)s; border-left: 4px solid %(cor)s; border-radius: 4px;
  padding: .9rem 1rem; margin-top: .9rem;
  font: 400 .92rem/1.7 'Inter', system-ui, sans-serif; color: %(texto)s;
}
.conta-g b { font-variant-numeric: tabular-nums; color: %(tinta)s; }
""" % CORES

JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  function l(r, v) {
    return v ? '<div class="ct-l"><span>' + r + '</span><b>'
      + ewt.escapar(v) + '</b></div>' : '';
  }

  // A mudanca de palavra-passe. Nao pede a antiga porque a sessao ja
  // prova quem e: quem esta aqui dentro ja entrou. Pede duas vezes a
  // nova, que e o erro que realmente acontece.
  function ligarPalavraPasse() {
    var f = document.getElementById('f-pw');
    if (!f) return;
    f.addEventListener('submit', async function (ev) {
      ev.preventDefault();
      var a = document.getElementById('pw1').value;
      var b = document.getElementById('pw2').value;
      ewt.dizer('av-pw', '', '');

      if (a.length < 10) {
        ewt.dizer('av-pw', 'Make it at least 10 characters.', 'mal');
        document.getElementById('pw1').focus();
        return;
      }
      if (a !== b) {
        ewt.dizer('av-pw', 'The two do not match.', 'mal');
        document.getElementById('pw2').focus();
        return;
      }

      var bt = document.getElementById('bt-pw');
      bt.disabled = true; bt.textContent = 'Changing\u2026';
      var r = await ewt.sb.auth.updateUser({ password: a });
      bt.disabled = false; bt.textContent = 'Change my password';

      if (r.error) { ewt.dizer('av-pw', ewt.legivel(r.error), 'mal'); return; }
      f.reset();
      ewt.dizer('av-pw', 'Done. Use the new one next time you sign in \u2014 '
        + 'this session stays open.', 'bem');
    });
  }

  (async function () {
    var p = await ewt.exigir_entrada();
    if (!p) return;

    document.getElementById('carrega').hidden = true;
    var c = document.getElementById('ct');
    c.hidden = false;

    if (!p.operadores.length) {
      c.innerHTML = '<div class="vazio"><h3>No company linked to '
        + ewt.escapar(p.email) + '</h3><p>Your sign-in works, but it is not '
        + 'attached to an operator yet.</p>'
        + '<a class="bt bt-s" href="/suppliers/apply/">Apply to sell here</a>'
        + '</div>';
      return;
    }

    var emp = p.operadores[0];
    var r = await ewt.sb.from('operators')
      .select('*').eq('id', emp.id).single();
    var o = r.data || {};

    var taxa = o.commission_rate != null ? Number(o.commission_rate) : null;
    var conta = '';
    if (taxa !== null) {
      // Em tres precos redondos, para a conta ser obvia sem calculadora.
      conta = '<div class="conta-g">'
        + [200, 500, 1000].map(function (x) {
            var com = Math.round(x * taxa * 100) / 100;
            return 'On <b>€' + ewt.euros(x) + '</b> you receive <b>€'
              + ewt.euros(x - com) + '</b> (commission €'
              + ewt.euros(com) + ')';
          }).join('<br>')
        + '</div>';
    }

    var u = await ewt.sb.from('operator_users')
      .select('user_id, role, created_at').eq('operator_id', emp.id);
    var quantos = (u.data || []).length;

    c.innerHTML =
      '<div class="cx"><p class="cx-t">Your company</p>'
      + l('Trading name', o.name)
      + l('Legal entity', o.legal_name)
      + l('Where', [o.city, o.country].filter(Boolean).join(', '))
      + l('Contact email', o.email)
      + l('Phone', o.phone)
      + l('Website', o.website)
      + l('Licence reference', o.licence_ref)
      + '<div class="ct-l"><span>Status</span><b><span class="est est-'
      + (o.status || 'pending') + '">' + (o.status || 'pending')
      + '</span></b></div>'
      + '</div>'

      + '<div class="cx"><p class="cx-t">Commission</p>'
      + '<div class="ct-l"><span>On what the guest pays</span><b>'
      + (taxa === null ? 'not set' : (taxa * 100).toFixed(taxa * 100 % 1 ? 2 : 0) + '%')
      + '</b></div>'
      + conta
      + '<p class="lado-nota">You set your prices. We do not change them '
      + 'and we do not discount your tour to win a sale. There is no '
      + 'listing fee and no fee to be seen.</p>'
      + '</div>'

      + '<div class="cx"><p class="cx-t">Sign-in</p>'
      + l('You are signed in as', p.email)
      + l('People with access', String(quantos))
      + '<p class="lado-nota">To add someone from your team, write to us '
      + 'with their email. We do not let an account add its own members '
      + 'yet &mdash; it is the kind of thing that is easy to get wrong '
      + 'once and hard to notice.</p>'
      + '</div>'

      + '<div class="cx"><p class="cx-t">Password</p>'
      + '<form id="f-pw" novalidate>'
      + '<div class="campo"><label for="pw1">New password</label>'
      + '<input type="password" id="pw1" autocomplete="new-password" '
      + 'minlength="10">'
      + '<span class="ajuda">At least 10 characters. A short phrase you '
      + 'will remember beats a short word you will not.</span></div>'
      + '<div class="campo"><label for="pw2">Type it again</label>'
      + '<input type="password" id="pw2" autocomplete="new-password">'
      + '<span class="ajuda">Because a password you cannot retype is a '
      + 'password you have already lost.</span></div>'
      + '<button type="submit" class="bt bt-p" id="bt-pw">Change my '
      + 'password</button>'
      + '<p class="aviso" id="av-pw" role="status" hidden></p>'
      + '</form></div>';

    ligarPalavraPasse();
  })();
})();
"""


def corpo():
    return '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">
    <p class="carrega" id="carrega">Loading your account&hellip;</p>
    <div id="ct-cab" class="pt-cab">
      <h1>Account</h1>
      <p>What the system knows about your company, and exactly what we
        take.</p>
    </div>
    <div class="ct" id="ct" hidden></div>
  </div>
</main>'''


def gerar():
    pagina.verificar_contraste()
    html = portal_base.envolver(
        titulo='Account — Exclusive World Tours',
        corpo=corpo(), js=JS, etiqueta='Operator portal',
        nav=NAV, atual='/portal/account/', css_extra=CSS)
    pagina.escrever(html, 'portal/account/index.html')


if __name__ == '__main__':
    gerar()
