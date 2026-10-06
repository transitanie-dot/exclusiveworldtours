# -*- coding: utf-8 -*-
"""As avaliacoes, do lado do operador.

Ele le e responde. Nao muda a nota nem o texto, e nao ha botao nenhum
nesta pagina que o deixe tentar — a base tambem nao deixaria, mas uma
interface que oferece uma coisa impossivel e uma interface que ensina a
desconfiar dela.

A resposta e publica e aparece por baixo da avaliacao. E a melhor coisa
que um operador pode fazer com uma avaliacao ma: uma boa resposta a uma
ma avaliacao diz mais a quem esta a decidir do que dez boas.
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
.rv-resumo { display: grid; gap: .8rem; margin-bottom: 1.4rem; }
@media (min-width: 680px) { .rv-resumo { grid-template-columns: repeat(3, 1fr); } }

.rv-l { display: grid; gap: .9rem; }
.rv-c {
  background: %(branco)s; border-radius: var(--r-g);
  box-shadow: var(--sombra);
  padding: 1rem 1.1rem;
}
.rv-cab {
  display: flex; flex-wrap: wrap; align-items: center; gap: .6rem;
  margin-bottom: .6rem;
}
.rv-est {
  color: %(cor_escura)s; font-size: 1.05rem; letter-spacing: 2px;
  line-height: 1;
}
.rv-quem {
  font: 600 .95rem/1.3 'Inter', system-ui, sans-serif; color: %(tinta)s;
}
.rv-quando {
  margin-left: auto; font: 400 .82rem/1.3 'Inter', system-ui, sans-serif;
  color: %(mudo)s;
}
.rv-tour {
  font: 400 .8rem/1.3 'Inter', system-ui, sans-serif; color: %(mudo)s;
  width: 100%%;
}
.rv-c h3 {
  margin: 0 0 .35rem; font: 700 1rem/1.3 'Inter', system-ui, sans-serif;
  color: %(tinta)s;
}
.rv-c > p {
  margin: 0; font: 400 .93rem/1.65 'Inter', system-ui, sans-serif;
  color: %(texto)s;
}
.rv-resp {
  margin-top: .9rem; padding: .8rem .9rem; background: %(papel)s;
  border-left: 3px solid %(cor)s; border-radius: 0 4px 4px 0;
}
.rv-resp b {
  display: block; font: 600 .68rem/1 'Inter', system-ui, sans-serif; color: %(mudo)s;
  margin-bottom: .4rem;
}
.rv-resp p {
  margin: 0; font: 400 .9rem/1.6 'Inter', system-ui, sans-serif;
  color: %(texto)s;
}
.rv-form { margin-top: .9rem; display: grid; gap: .6rem; }
.rv-form textarea { min-height: 4.5rem; }
""" % CORES


JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  function estrelas(n) {
    var cheias = Math.round(n);
    var s = '';
    for (var i = 0; i < 5; i++) s += (i < cheias ? '★' : '☆');
    return '<span class="rv-est" role="img" aria-label="' + n
      + ' out of 5">' + s + '</span>';
  }

  function quando(d) {
    if (!d) return '';
    return new Date(d).toLocaleDateString(undefined,
      { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function cartao(a, titulos) {
    var resposta = a.reply
      ? '<div class="rv-resp"><b>Your reply</b><p>'
        + ewt.escapar(a.reply) + '</p></div>'
      : '<form class="rv-form" data-resp="' + a.id + '">'
        + '<label class="so-leitor" for="r-' + a.id + '">Your public reply</label>'
        + '<textarea id="r-' + a.id + '" maxlength="2000" rows="3" '
        + 'placeholder="Reply in public. A good reply to a hard review tells '
        + 'the next reader more than ten good ones."></textarea>'
        + '<button type="submit" class="bt bt-s bt-pq" '
        + 'style="justify-self:start">Reply in public</button></form>';

    return '<article class="rv-c">'
      + '<div class="rv-cab">' + estrelas(a.rating)
      + '<span class="rv-quem">' + ewt.escapar(a.author_name)
      + (a.author_country ? ' · ' + ewt.escapar(a.author_country) : '')
      + '</span>'
      + '<span class="rv-quando">travelled ' + quando(a.travelled_on) + '</span>'
      + '<span class="rv-tour">' + ewt.escapar(titulos[a.listing_id] || '')
      + '</span></div>'
      + (a.title ? '<h3>' + ewt.escapar(a.title) + '</h3>' : '')
      + (a.body ? '<p>' + ewt.escapar(a.body) + '</p>' : '')
      + resposta
      + '<p class="aviso" id="av-' + a.id + '" role="status" hidden></p>'
      + '</article>';
  }

  async function responder(id, texto) {
    var r = await ewt.sb.rpc('responder_avaliacao',
                             { p_review: id, p_texto: texto });
    if (r.error) { ewt.dizer('av-' + id, ewt.legivel(r.error), 'mal'); return; }
    await carregar();
  }

  async function carregar() {
    var r = await ewt.sb.from('reviews')
      .select('*').eq('state', 'published')
      .order('travelled_on', { ascending: false });
    if (r.error) { ewt.dizer('av-rv', ewt.legivel(r.error), 'mal'); return; }
    var av = r.data || [];

    var c = document.getElementById('rv-corpo');
    if (!av.length) {
      c.innerHTML = '<div class="vazio"><h3>No reviews yet</h3>'
        + '<p>A guest can only review a day that actually ran, and only '
        + 'from a link we send them afterwards. That is why there are '
        + 'none here yet — and why the ones that come will be worth '
        + 'something.</p>'
        + '<a class="bt bt-s" href="/reviews-policy/">How reviews work here</a>'
        + '</div>';
      return;
    }

    var titulos = {};
    var vv = await ewt.sb.from('listing_versions')
      .select('listing_id, version, payload')
      .in('listing_id', av.map(function (a) { return a.listing_id; }))
      .order('version', { ascending: false });
    (vv.data || []).forEach(function (x) {
      if (!titulos[x.listing_id] && x.payload && x.payload.title) {
        titulos[x.listing_id] = x.payload.title;
      }
    });

    var soma = av.reduce(function (s, a) { return s + a.rating; }, 0);
    var porResponder = av.filter(function (a) { return !a.reply; }).length;

    c.innerHTML =
      '<div class="rv-resumo">'
      + '<div class="rs"><b>' + (soma / av.length).toFixed(1)
      + '</b><span>average, across ' + av.length
      + (av.length === 1 ? ' review' : ' reviews') + '</span></div>'
      + '<div class="rs"><b>' + av.length + '</b><span>guests who reviewed</span></div>'
      + '<div class="rs"><b>' + porResponder + '</b><span>waiting for your reply</span></div>'
      + '</div>'
      + '<div class="rv-l">' + av.map(function (a) {
          return cartao(a, titulos);
        }).join('') + '</div>';
  }

  (async function () {
    var p = await ewt.exigir_entrada();
    if (!p) return;
    document.getElementById('carrega').hidden = true;
    if (!p.operadores.length && !p.admin) {
      document.getElementById('conteudo').innerHTML =
        '<div class="vazio"><h3>Your account is not linked to a company</h3>'
        + '<a class="bt bt-s" href="/portal/">Back to the portal</a></div>';
      return;
    }
    document.getElementById('rv').hidden = false;

    document.getElementById('rv-corpo').addEventListener('submit', function (ev) {
      var f = ev.target.closest('[data-resp]');
      if (!f) return;
      ev.preventDefault();
      var id = f.getAttribute('data-resp');
      var t = f.querySelector('textarea').value.trim();
      if (t.length < 10) {
        ewt.dizer('av-' + id, 'Write a real reply — the guest reads it '
          + 'exactly as you write it.', 'mal');
        return;
      }
      responder(id, t);
    });

    await carregar();
  })();
})();
"""


def corpo():
    return '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">
    <p class="carrega" id="carrega">Loading your reviews&hellip;</p>

    <div id="rv" hidden>
      <div class="pt-cab">
        <h1>Reviews</h1>
        <p>You can reply in public, and you should &mdash; a good reply to
          a hard review tells the next reader more than ten good ones.
          You cannot change a rating or a word of what a guest wrote, and
          you must not contact them privately about it.
          <a href="/reviews-policy/">The rules, in full</a>.</p>
      </div>

      <p class="aviso" id="av-rv" role="status" hidden></p>
      <div id="rv-corpo"></div>
    </div>
  </div>
</main>'''


def gerar():
    pagina.verificar_contraste()
    html = portal_base.envolver(
        titulo='Reviews — Exclusive World Tours',
        corpo=corpo(), js=JS, etiqueta='Operator portal',
        nav=NAV, atual='/portal/reviews/', css_extra=CSS)
    pagina.escrever(html, 'portal/reviews/index.html')


if __name__ == '__main__':
    gerar()
