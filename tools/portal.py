# -*- coding: utf-8 -*-
"""A entrada do portal e o painel do operador.

Uma pagina so, dois estados: quem nao assinou ve a entrada, quem assinou
ve os seus anuncios. Sao a mesma pagina de proposito — o endereco que o
operador guarda nos favoritos e sempre /portal/, e nunca da de cara com
um redirecionamento.

A entrada e por ligacao no email e nao por palavra-passe. Nao e
preguica: um operador que entra aqui tres vezes por mes esquece a
palavra-passe, e o que vem a seguir e uma palavra-passe fraca escrita
num papel ao lado do volante.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pagina
import portal_base

CORES = pagina.CORES

NAV = [('My tours', '/portal/'),
       ('Calendar', '/portal/calendar/'),
       ('Account', '/portal/account/')]


CSS = """
.entrada { max-width: 27rem; margin: 2.5rem auto 4rem; }
.entrada .cx { padding: 1.6rem; }
.entrada h1 {
  font: 700 1.5rem/1.2 'Archivo', system-ui, sans-serif;
  color: %(tinta)s; margin: 0 0 .5rem;
}
.entrada .sub {
  font: 400 .93rem/1.55 'Inter', system-ui, sans-serif;
  color: %(mudo)s; margin: 0 0 1.3rem;
}
.entrada .rodape-l {
  margin-top: 1.4rem; padding-top: 1.1rem; border-top: 1px solid %(risco)s;
  font: 400 .86rem/1.55 'Inter', system-ui, sans-serif; color: %(mudo)s;
}
.entrada .rodape-l a { color: %(cor_escura)s; }

/* --------------------------------------------------- resumo do painel */
.resumo { display: grid; gap: .8rem; margin-bottom: 1.4rem; }
@media (min-width: 680px) { .resumo { grid-template-columns: repeat(3, 1fr); } }
.rs {
  background: %(branco)s; border: 1px solid %(risco)s; border-radius: 6px;
  border-left: 4px solid %(cor)s; padding: .9rem 1rem;
}
.rs b {
  display: block;
  font: 700 1.6rem/1 'Archivo', system-ui, sans-serif;
  color: %(tinta)s; font-variant-numeric: tabular-nums;
}
.rs span {
  font: 400 .8rem/1.4 'Inter', system-ui, sans-serif; color: %(mudo)s;
}

/* ------------------------------------------------------- lista de anuncios */
.an { display: grid; gap: .9rem; }
.an-l {
  background: %(branco)s; border: 1px solid %(risco)s; border-radius: 6px;
  padding: 1rem 1.1rem;
  display: grid; gap: .7rem;
}
@media (min-width: 760px) {
  .an-l { grid-template-columns: 1fr auto; align-items: center; }
}
.an-n {
  font: 700 1.08rem/1.25 'Archivo', system-ui, sans-serif;
  color: %(tinta)s; margin: 0 0 .3rem;
}
.an-m {
  font: 400 .84rem/1.5 'Inter', system-ui, sans-serif; color: %(mudo)s;
  margin: 0; display: flex; flex-wrap: wrap; gap: .5rem .9rem; align-items: center;
}
.an-pend {
  margin-top: .6rem; padding: .5rem .7rem; border-radius: 4px;
  background: #FBF2EB; border-left: 3px solid %(cor)s;
  font: 400 .84rem/1.45 'Inter', system-ui, sans-serif; color: %(texto)s;
}
""" % CORES


JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  var elEntrada = document.getElementById('entrada');
  var elPainel  = document.getElementById('painel');
  // O cabecalho do painel e fixo; so isto e que muda. Escrever no
  // painel inteiro apagava o titulo e a explicacao com ele.
  var elCorpo   = document.getElementById('corpo-painel');
  var elCarrega = document.getElementById('carrega');

  // ------------------------------------------------------------- entrada
  var f = document.getElementById('f-entrar');
  f.addEventListener('submit', async function (ev) {
    ev.preventDefault();
    var email = document.getElementById('email').value.trim();
    var bt = document.getElementById('bt-entrar');
    if (!email) { return; }

    bt.disabled = true;
    bt.textContent = 'Sending…';
    ewt.dizer('av-entrada', '', '');

    // Volta para onde a pessoa estava a tentar ir, nao para a raiz.
    var volta = new URLSearchParams(location.search).get('volta') || '/portal/';
    var r = await ewt.sb.auth.signInWithOtp({
      email: email,
      options: { emailRedirectTo: location.origin + volta }
    });

    bt.disabled = false;
    bt.textContent = 'Email me a sign-in link';

    if (r.error) {
      ewt.dizer('av-entrada', ewt.legivel(r.error), 'mal');
      return;
    }
    // Nao se diz "if that address is registered": o operador precisa de
    // saber se escreveu o email certo, e esta e uma area fechada onde
    // nao ha nada a esconder de quem ja esta de fora.
    ewt.dizer('av-entrada',
      'Check ' + email + '. The link we sent is valid for one hour and '
      + 'opens the portal straight away — no password needed.', 'bem');
    document.getElementById('f-entrar').reset();
  });

  // -------------------------------------------------------------- painel
  function linhaAnuncio(a) {
    var pend = a.pendente
      ? '<p class="an-pend"><b>Waiting for review</b> — version '
        + a.pendente.version + ', sent ' + a.pendente.quando
        + '. Your live version stays online until this one is approved.</p>'
      : '';
    var rec = a.recusada
      ? '<p class="an-pend"><b>Sent back</b> — '
        + ewt.escapar(a.recusada.review_note || 'no reason given')
        + '. Edit and submit again.</p>'
      : '';
    return '<div class="an-l"><div>'
      + '<h3 class="an-n">' + ewt.escapar(a.titulo) + '</h3>'
      + '<p class="an-m"><span class="est est-' + a.status + '">' + a.status
      + '</span>'
      + '<span>' + ewt.escapar(a.city) + ', ' + ewt.escapar(a.country) + '</span>'
      + (a.versao ? '<span>live version ' + a.versao + '</span>'
                  : '<span>never published</span>')
      + '</p>' + pend + rec + '</div>'
      + '<div class="acoes">'
      + '<a class="bt bt-s bt-pq" href="/portal/calendar/?tour=' + a.id + '">Calendar</a>'
      + '<a class="bt bt-p bt-pq" href="/portal/listing/?id=' + a.id + '">Edit</a>'
      + '</div></div>';
  }

  function quando(s) {
    if (!s) return '';
    var d = new Date(s);
    return d.toLocaleDateString(undefined,
      { day: 'numeric', month: 'short', year: 'numeric' });
  }

  async function painel(p) {
    if (!p.operadores.length && !p.admin) {
      // Entrou, mas nao esta ligado a nenhuma empresa. Acontece a quem
      // se candidatou e ainda nao foi aprovado — e tem de o perceber
      // sem ter de escrever a ninguem.
      elCorpo.innerHTML = '<div class="vazio"><h3>Your account is not '
        + 'linked to a company yet</h3><p>If you have applied to sell on '
        + 'Exclusive World Tours, we are still reviewing it. Once your '
        + 'company is approved, your tours appear here.</p>'
        + '<a class="bt bt-s" href="/suppliers/">How selling here works</a></div>';
      return;
    }

    if (p.admin) {
      elCorpo.innerHTML = '<div class="aviso aviso-nota">You are signed in '
        + 'as an administrator. <a href="/admin/">Open the review queue</a>.'
        + '</div><div id="meus"></div>';
    } else {
      elCorpo.innerHTML = '<div id="meus"></div>';
    }

    var emp = p.operadores[0];
    var meus = document.getElementById('meus');

    if (emp && emp.estado !== 'approved') {
      meus.innerHTML = '<div class="aviso aviso-nota"><b>'
        + ewt.escapar(emp.nome) + '</b> is marked as <b>' + emp.estado
        + '</b>. You can prepare tours, but nothing goes on the site until '
        + 'the company is approved.</div>';
    }

    var r = await ewt.sb.from('listings')
      .select('id, slug, status, city, country, created_at')
      .order('created_at', { ascending: false });

    if (r.error) {
      meus.innerHTML += '<div class="aviso aviso-mal">'
        + ewt.escapar(ewt.legivel(r.error)) + '</div>';
      return;
    }
    var anuncios = r.data || [];

    if (!anuncios.length) {
      meus.innerHTML += '<div class="vazio"><h3>No tours yet</h3>'
        + '<p>Add your first tour. You write it, we read it, and it goes '
        + 'on the site once it is approved. Nothing is published before '
        + 'that.</p><a class="bt bt-p" href="/portal/listing/">Add a tour</a>'
        + '</div>';
      return;
    }

    // As versoes de todos os anuncios de uma vez, e nao uma consulta por
    // anuncio: com vinte anuncios isso eram vinte viagens a base.
    var ids = anuncios.map(function (a) { return a.id; });
    var v = await ewt.sb.from('listing_versions')
      .select('listing_id, version, status, submitted_at, review_note, payload')
      .in('listing_id', ids)
      .order('version', { ascending: false });

    var porAnuncio = {};
    (v.data || []).forEach(function (x) {
      var o = porAnuncio[x.listing_id] || (porAnuncio[x.listing_id] = {});
      if (x.status === 'approved' && !o.aprovada) o.aprovada = x;
      if (x.status === 'pending'  && !o.pendente) o.pendente  = x;
      if (x.status === 'rejected' && !o.recusada) o.recusada  = x;
    });

    var nPend = 0, nVivos = 0;
    var lista = anuncios.map(function (a) {
      var o = porAnuncio[a.id] || {};
      if (o.pendente) nPend++;
      if (a.status === 'live') nVivos++;
      var titulo = (o.aprovada && o.aprovada.payload && o.aprovada.payload.title)
        || (o.pendente && o.pendente.payload && o.pendente.payload.title)
        || a.slug;
      return {
        id: a.id, titulo: titulo, status: a.status,
        city: a.city, country: a.country,
        versao: o.aprovada ? o.aprovada.version : null,
        pendente: o.pendente
          ? { version: o.pendente.version, quando: quando(o.pendente.submitted_at) }
          : null,
        // Uma recusa so interessa se for a ultima palavra: se depois
        // dela houve uma submissao nova, ja esta tratada.
        recusada: (o.recusada && (!o.pendente || o.pendente.version < o.recusada.version))
          ? o.recusada : null
      };
    });

    meus.innerHTML +=
      '<div class="resumo">'
      + '<div class="rs"><b>' + anuncios.length + '</b><span>tours in your account</span></div>'
      + '<div class="rs"><b>' + nVivos + '</b><span>live on the site</span></div>'
      + '<div class="rs"><b>' + nPend + '</b><span>waiting for review</span></div>'
      + '</div>'
      + '<div class="acoes" style="margin-bottom:1.1rem">'
      + '<a class="bt bt-p" href="/portal/listing/">Add a tour</a>'
      + '<a class="bt bt-s" href="/portal/calendar/">Open the calendar</a>'
      + '</div>'
      + '<div class="an">' + lista.map(linhaAnuncio).join('') + '</div>';
  }

  // ------------------------------------------------------------- arranque
  (async function () {
    var p = await ewt.papel();
    elCarrega.hidden = true;
    if (!p.entrou) {
      elEntrada.hidden = false;
      document.getElementById('email').focus();
      return;
    }
    elPainel.hidden = false;
    try {
      await painel(p);
    } catch (err) {
      elCorpo.innerHTML = '<div class="aviso aviso-mal">'
        + ewt.escapar(ewt.legivel(err)) + '</div>';
    }
  })();
})();
"""


def corpo():
    return '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">

    <p class="carrega" id="carrega">Loading your account&hellip;</p>

    <!-- ----------------------------------------------------- entrada -->
    <div class="entrada" id="entrada" hidden>
      <div class="cx">
        <h1>Operator sign-in</h1>
        <p class="sub">We email you a link. No password to remember, and
          nothing to reset when you have not been here for a month.</p>

        <form id="f-entrar" novalidate>
          <div class="campo">
            <label for="email">Your work email</label>
            <input type="email" id="email" name="email" required
                   autocomplete="email" inputmode="email"
                   placeholder="you@yourcompany.com">
            <span class="ajuda">Use the address you applied with. A link
              to a different address will not find your tours.</span>
          </div>
          <button type="submit" class="bt bt-p" id="bt-entrar"
                  style="width:100%%">Email me a sign-in link</button>
          <p class="aviso" id="av-entrada" role="status" hidden></p>
        </form>

        <p class="rodape-l">Not selling with us yet?
          <a href="/suppliers/">See how it works</a> and apply &mdash; it
          takes about five minutes.</p>
      </div>
    </div>

    <!-- ------------------------------------------------------ painel -->
    <div id="painel" hidden>
      <div class="pt-cab">
        <h1>My tours</h1>
        <p>Everything you change here is read before it goes on the site.
          The calendar is the exception: days you open or close are live
          immediately, because an availability that waits for review is
          an availability that is wrong.</p>
      </div>
      <div id="corpo-painel"></div>
    </div>

  </div>
</main>'''


def gerar():
    pagina.verificar_contraste()
    html = portal_base.envolver(
        titulo='Operator portal — Exclusive World Tours',
        corpo=corpo(), js=JS, etiqueta='Operator portal',
        nav=NAV, atual='/portal/', css_extra=CSS)
    pagina.escrever(html, 'portal/index.html')


if __name__ == '__main__':
    gerar()
