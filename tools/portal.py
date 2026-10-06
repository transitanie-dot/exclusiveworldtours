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

# As cores vem das fichas do tema, nao de hexadecimais fixos:
# ver a nota em portal_base.FICHAS. E isto que faz o modo
# escuro desta pagina funcionar sem lhe mexer no CSS.
CORES = portal_base.FICHAS

NAV = [('My tours', '/portal/'),
       ('Bookings', '/portal/bookings/'),
       # As epocas vem ANTES do calendario de proposito. A epoca e a
       # regra — "abro de segunda a sexta, de Junho a Setembro" — e o
       # calendario sao as excepcoes a ela. Quem chega primeiro ao
       # calendario acaba a pintar dia a dia o que uma frase resolvia,
       # que era a queixa de origem: "e super confuso mexer no
       # calendario".
       ('Seasons', '/portal/seasons/'),
       ('Calendar', '/portal/calendar/'),
       ('Fleet', '/portal/fleet/'),
       ('Meeting points', '/portal/places/'),
       ('Reviews', '/portal/reviews/'),
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
.ou {
  display: flex; align-items: center; gap: .8rem;
  margin: 1.2rem 0 1rem; color: %(mudo)s;
  font: 400 .8rem/1 'Inter', system-ui, sans-serif;
}
.ou::before, .ou::after {
  content: ''; flex: 1; height: 1px; background: %(risco)s;
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
/* O fundo era um creme escrito a mao e o texto vinha da ficha. No
   modo escuro isso dava texto claro sobre creme claro — o axe apanhou-o
   assim que passou a correr nos dois temas. Agora o fundo E o texto sao
   o par "acento", que a porta de contraste do tema.py garante nos
   dois. A barra de 3px sai: a cor do fundo ja diz o que isto e. */
.an-pend {
  margin-top: .6rem; padding: .6rem .8rem; border-radius: var(--r-p);
  background: var(--acento-f); color: var(--acento);
  font: 400 .84rem/1.45 'Inter', system-ui, sans-serif;
}

/* O QUE ESTA NO SITE, E O QUE ESTA SO APROVADO
   Duas coisas diferentes, duas cores diferentes. Um operador que ve
   "approved" e nao ve o tour no site liga a perguntar. */
.an-site {
  margin-top: .5rem; display: flex; flex-wrap: wrap; gap: .4rem .8rem;
  align-items: center;
  font: 400 .84rem/1.5 'Inter', system-ui, sans-serif; color: %(mudo)s;
}
.an-site a { color: %(cor_escura)s; font-weight: 600; }
.an-ar {
  display: inline-block; padding: .14rem .45rem; border-radius: 3px;
  font: 700 .7rem/1.5 'Inter', system-ui, sans-serif; letter-spacing: .05em;
  text-transform: uppercase;
}
.an-ar-no { background: #E6F2EA; color: #1D5C35; }
.an-ar-espera { background: #FFF4E0; color: #7A4C05; }
.an-ar-fora { background: %(risco)s; color: %(texto)s; }
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
  //
  // Duas maneiras de entrar, e as duas existem por razoes diferentes:
  //
  //   PALAVRA-PASSE  para quem entra aqui todos os dias. Nao depende de
  //                  email nenhum chegar, e e por isso que esta primeiro.
  //   LIGACAO        para o operador que entra tres vezes por mes e ia
  //                  esquecer a palavra-passe. Depende de o email sair.
  //
  // A ligacao so funciona quando o projeto tiver servidor de email
  // proprio; ate la o Supabase so entrega a membros da organizacao. Por
  // isso o erro dessa via tem de dizer isso por palavras, e nao deixar a
  // pessoa a olhar para um ecra que nao aconteceu nada.
  var f = document.getElementById('f-entrar');

  function volta() {
    return new URLSearchParams(location.search).get('volta') || '/portal/';
  }

  function travar(sim, botao, texto) {
    var bs = [document.getElementById('bt-entrar'),
              document.getElementById('bt-ligacao')];
    bs.forEach(function (b) { if (b) b.disabled = sim; });
    if (botao) botao.textContent = texto;
  }

  // --------------------------------------------------- palavra-passe
  f.addEventListener('submit', async function (ev) {
    ev.preventDefault();
    var email = document.getElementById('email').value.trim();
    var pw = document.getElementById('pw').value;
    var bt = document.getElementById('bt-entrar');
    ewt.dizer('av-entrada', '', '');

    if (!email) {
      ewt.dizer('av-entrada', 'Type the email you sign in with.', 'mal');
      document.getElementById('email').focus();
      return;
    }
    if (!pw) {
      // Sem palavra-passe nao se tenta entrar e falhar: oferece-se a
      // outra via, que e o que a pessoa provavelmente queria.
      ewt.dizer('av-entrada', 'Type your password, or use the sign-in '
        + 'link below if you do not have one.', 'mal');
      document.getElementById('pw').focus();
      return;
    }

    travar(true, bt, 'Signing in…');
    var r = await ewt.sb.auth.signInWithPassword({ email: email, password: pw });
    travar(false, bt, 'Sign in');

    if (r.error) {
      var m = (r.error.message || '').toLowerCase();
      ewt.dizer('av-entrada',
        m.indexOf('invalid') > -1
          ? 'That email and password do not match. Check both, or use the '
            + 'sign-in link below.'
          : ewt.legivel(r.error), 'mal');
      return;
    }
    location.href = volta();
  });

  // ---------------------------------------------------------- ligacao
  document.getElementById('bt-ligacao').addEventListener('click', async function () {
    var email = document.getElementById('email').value.trim();
    var bt = this;
    ewt.dizer('av-entrada', '', '');

    if (!email) {
      ewt.dizer('av-entrada', 'Type your email first and we send the link '
        + 'there.', 'mal');
      document.getElementById('email').focus();
      return;
    }

    travar(true, bt, 'Sending…');
    var r = await ewt.sb.auth.signInWithOtp({
      email: email,
      options: { emailRedirectTo: location.origin + volta() }
    });
    travar(false, bt, 'Email me a sign-in link instead');

    if (r.error) {
      var m = (r.error.message || '').toLowerCase();
      if (m.indexOf('not authorized') > -1 || m.indexOf('not allowed') > -1) {
        // O erro verdadeiro, dito por palavras: nao e um problema do
        // endereco da pessoa, e do servidor de email ainda nao estar
        // montado. Deixa-la a adivinhar isso seria indecente.
        ewt.dizer('av-entrada', 'We cannot email that address yet — our '
          + 'mail service is still being set up. Sign in with your '
          + 'password, or write to us and we will sort it out.', 'mal');
      } else {
        ewt.dizer('av-entrada', ewt.legivel(r.error), 'mal');
      }
      return;
    }
    // Nao se diz "if that address is registered": esta e uma area
    // fechada, e quem esta de fora nao ganha nada com a duvida.
    ewt.dizer('av-entrada',
      'Check ' + email + '. The link we sent is valid for one hour and '
      + 'opens the portal straight away.', 'bem');
  });

  // ============================================================
  // O QUE ESTA REALMENTE NO SITE
  //
  // A base diz que versao esta APROVADA. O site e estatico: a versao
  // aprovada so la chega quando alguem corre o gerador e faz push. Entre
  // uma coisa e outra podem passar dias, e durante esses dias este painel
  // dizia ao operador "live version 3" com a versao 2 no ar.
  //
  // O /assets/publicado.json e escrito pelo proprio gerador, na mesma
  // corrida que escreve as paginas. E a unica coisa que pode dizer "esta
  // no site" sem adivinhar.
  //
  // Se o ficheiro nao carregar, nao se inventa: o painel deixa de falar
  // do site e so diz o que a base sabe. Melhor calar-se do que mentir.
  // ============================================================
  var PUBLICADO = null;

  async function lerPublicado() {
    try {
      var r = await fetch('/assets/publicado.json', { cache: 'no-store' });
      if (!r.ok) return;
      PUBLICADO = await r.json();
    } catch (e) { /* fica a null, e o painel cala-se sobre o site */ }
  }

  /** O que dizer a este operador sobre este anuncio e o site. */
  function noSite(a) {
    if (!PUBLICADO || !PUBLICADO.tours) return '';

    var p = PUBLICADO.tours[a.slug];
    var quandoGerado = PUBLICADO.gerado_em
      ? quando(PUBLICADO.gerado_em) : null;

    // Nunca foi aprovado: nao ha nada a dizer sobre o site.
    if (a.versao === null) return '';

    if (!p) {
      return '<p class="an-site">'
        + '<span class="an-ar an-ar-espera">not on the site yet</span>'
        + '<span>Version ' + a.versao + ' is approved. It goes on the site '
        + 'at the next publish.</span></p>';
    }

    var ligacao = '<a href="/tours/' + encodeURIComponent(a.slug)
      + '/" target="_blank" rel="noopener">See it on the site</a>';

    if (p.versao === a.versao) {
      return '<p class="an-site">'
        + '<span class="an-ar an-ar-no">on the site</span>'
        + '<span>Version ' + a.versao
        + (quandoGerado ? ', published ' + quandoGerado : '') + '.</span>'
        + ligacao + '</p>';
    }

    // Esta no site, mas com uma versao antiga. E o caso que mais confunde
    // um operador: ele mudou o texto, foi aprovado, e o site continua a
    // mostrar o antigo.
    return '<p class="an-site">'
      + '<span class="an-ar an-ar-espera">older version on the site</span>'
      + '<span>The site shows version ' + (p.versao === null ? '—' : p.versao)
      + '; version ' + a.versao + ' is approved and goes up at the next '
      + 'publish.</span>' + ligacao + '</p>';
  }

  // -------------------------------------------------------------- painel
  function linhaAnuncio(a) {
    var pend = a.pendente
      ? '<p class="an-pend"><b>Waiting for review</b> — version '
        + a.pendente.version + ', sent ' + a.pendente.quando
        + '. The version on the site stays up until this one is approved '
        + 'and published.</p>'
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
      + (a.versao ? '<span>approved version ' + a.versao + '</span>'
                  : '<span>never approved</span>')
      + '</p>' + noSite(a) + pend + rec + '</div>'
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

    // O "on the site now" conta o que o MANIFESTO confirma, nao o que a
    // base aprovou. Antes contava `status === 'live'`, que e so uma
    // coluna da base e nao diz nada sobre o que esta publicado.
    var nPend = 0, nNoSite = 0;
    var lista = anuncios.map(function (a) {
      var o = porAnuncio[a.id] || {};
      if (o.pendente) nPend++;
      if (PUBLICADO && PUBLICADO.tours && PUBLICADO.tours[a.slug]
          && o.aprovada
          && PUBLICADO.tours[a.slug].versao === o.aprovada.version) nNoSite++;
      var titulo = (o.aprovada && o.aprovada.payload && o.aprovada.payload.title)
        || (o.pendente && o.pendente.payload && o.pendente.payload.title)
        || a.slug;
      return {
        id: a.id, slug: a.slug, titulo: titulo, status: a.status,
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
      + '<div class="rs"><b>' + nNoSite + '</b><span>on the site now</span></div>'
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
      // Antes de desenhar: sem isto, a primeira pintura dizia uma coisa e
      // a segunda outra.
      await lerPublicado();
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
        <p class="sub">Sign in with your password, or have us email you a
          link if you would rather not remember one.</p>

        <form id="f-entrar" novalidate>
          <div class="campo">
            <label for="email">Your work email</label>
            <input type="email" id="email" name="email" required
                   autocomplete="email" inputmode="email"
                   placeholder="you@yourcompany.com">
          </div>

          <div class="campo" id="campo-pw">
            <label for="pw">Password</label>
            <input type="password" id="pw" name="password"
                   autocomplete="current-password">
          </div>

          <button type="submit" class="bt bt-p" id="bt-entrar"
                  style="width:100%%">Sign in</button>
          <p class="aviso" id="av-entrada" role="status" hidden></p>
        </form>

        <div class="ou"><span>or</span></div>

        <button type="button" class="bt bt-s" id="bt-ligacao"
                style="width:100%%">Email me a sign-in link instead</button>
        <p class="ajuda" style="margin-top:.6rem">The link signs you in
          without a password. It works only if your address can receive
          our mail &mdash; if nothing arrives, use the password.</p>

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
