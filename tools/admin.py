# -*- coding: utf-8 -*-
"""A fila de revisao: a area do Ricardo.

Tres filas numa pagina so, porque sao a mesma tarefa com formas
diferentes — decidir o que entra no marketplace:

  TOURS         versoes submetidas por operadores, a espera de leitura
  OPERADORES    empresas que se candidataram a vender aqui
  PEDIDOS       clientes que escreveram e ainda nao tiveram resposta

Uma versao mostra-se SEMPRE ao lado da que esta no ar. Aprovar sem ver o
que mudou e assinar um texto que nao se leu; e o que muda, numa quinta
submissao do mesmo tour, costuma ser uma linha no meio de trinta.

Nada aqui apaga nada. Recusar uma versao nao a destroi: fica recusada,
com a razao escrita, e o operador le a razao no portal dele.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pagina
import portal_base

CORES = pagina.CORES

NAV = [('Review queue', '/admin/'),
       ('Bookings', '/admin/bookings/'),
       ('Operators', '/admin/operators/'),
       ('Searches', '/admin/searches/')]

CSS = """
.abas {
  display: flex; gap: .4rem; flex-wrap: wrap; margin-bottom: 1.3rem;
  border-bottom: 2px solid %(risco)s;
}
.aba {
  font: 600 .9rem/1 'Inter', system-ui, sans-serif;
  background: none; border: 0; border-bottom: 3px solid transparent;
  color: %(mudo)s; padding: .8rem .9rem; cursor: pointer; margin-bottom: -2px;
  display: flex; align-items: center; gap: .45rem;
}
.aba:hover { color: %(tinta)s; }
.aba[aria-selected="true"] { color: %(tinta)s; border-bottom-color: %(cor)s; }
.aba .n {
  font: 700 .72rem/1 'Archivo', system-ui, sans-serif;
  background: %(cor)s; color: #FFF; border-radius: 10px;
  padding: .22rem .42rem; min-width: 1.1rem; text-align: center;
}
.aba .n-0 { background: %(risco)s; color: %(mudo)s; }

/* ------------------------------------------------------------- revisao */
.rv {
  background: %(branco)s; border: 1px solid %(risco)s; border-radius: 6px;
  margin-bottom: 1.2rem; overflow: hidden;
}
.rv-t {
  padding: 1rem 1.1rem; border-bottom: 1px solid %(risco)s;
  display: grid; gap: .5rem;
}
@media (min-width: 820px) {
  .rv-t { grid-template-columns: 1fr auto; align-items: center; }
}
.rv-n {
  font: 700 1.1rem/1.25 'Archivo', system-ui, sans-serif;
  color: %(tinta)s; margin: 0 0 .25rem;
}
.rv-m {
  font: 400 .84rem/1.5 'Inter', system-ui, sans-serif; color: %(mudo)s;
  margin: 0; display: flex; flex-wrap: wrap; gap: .4rem .9rem;
}
.rv-c { padding: 1.1rem; }

/* O que mudou. Verde entra, vermelho sai — e com sinal, nao so cor. */
.dif { display: grid; gap: .6rem; }
.dif-l {
  border-left: 4px solid %(risco)s; padding: .5rem .8rem;
  background: %(papel)s; border-radius: 0 4px 4px 0;
}
.dif-campo {
  font: 600 .7rem/1 'Archivo', system-ui, sans-serif;
  letter-spacing: .1em; text-transform: uppercase; color: %(mudo)s;
  margin: 0 0 .4rem;
}
.dif-v {
  font: 400 .88rem/1.55 'Inter', system-ui, sans-serif;
  margin: 0; white-space: pre-wrap; word-break: break-word;
}
.dif-fora { color: #5F1512; background: #FCEEEC; }
.dif-dentro { color: #14401A; background: #EDF5EE; }
.dif-fora::before  { content: '\\2212  '; font-weight: 700; }
.dif-dentro::before { content: '+  '; font-weight: 700; }
.dif-novo { border-left-color: #1B5E20; }
.dif-ido  { border-left-color: #B3261E; }
.dif-mud  { border-left-color: %(cor)s; }
.dif-igual { color: %(mudo)s; font-style: italic; }

.rv-acoes {
  padding: 1rem 1.1rem; border-top: 1px solid %(risco)s; background: %(papel)s;
  display: grid; gap: .8rem;
}
.rv-acoes .campo { margin: 0; }

.dobra {
  font: 500 .86rem/1 'Inter', system-ui, sans-serif; color: %(cor_escura)s;
  background: none; border: 0; padding: .5rem 0; cursor: pointer;
  text-decoration: underline;
}
.todo {
  margin-top: .8rem; padding: .8rem; border: 1px solid %(risco)s;
  border-radius: 4px; background: %(papel)s;
  font: 400 .82rem/1.5 'Inter', ui-monospace, monospace;
  white-space: pre-wrap; word-break: break-word; max-height: 24rem;
  overflow: auto; color: %(texto)s;
}
""" % CORES


JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  var E = { aba: 'tours' };

  // ----------------------------------------------------------- o que mudou
  //
  // Comparam-se os campos que interessam, e nao o jsonb inteiro: a
  // ordem das chaves num objecto nao e informacao, e um diff que a
  // conta diz que mudou tudo quando nao mudou nada.
  var CAMPOS = [
    ['title', 'Title'], ['slug', 'Web address'], ['kicker', 'Kicker'],
    ['lede', 'Opening paragraph'], ['city', 'City'],
    ['countryName', 'Country'], ['ticketTo', 'Main attraction'],
    ['metaDesc', 'Search description'],
    ['stopsIntro', 'Intro to the stops'],
    ['includedIntro', 'Intro to what is included'],
    ['notIncluded', 'Not included'], ['practical', 'Practical notes']
  ];

  function texto(x) {
    if (x === null || x === undefined) return '';
    return typeof x === 'string' ? x : JSON.stringify(x, null, 1);
  }

  function precos(p) {
    var d = (p.durations && p.durations[0]) || {};
    var t = (d.tiers || []).map(function (x) {
      return 'up to ' + x.max + (x.vehicle ? ' (' + x.vehicle + ')' : '')
        + ': €' + ewt.euros(x.price);
    });
    return (d.h ? d.h + '\n' : '') + t.join('\n')
      + ((d.startTimes || []).length ? '\ndeparts ' + d.startTimes.join(', ') : '');
  }

  function listas(p) {
    return {
      'Stops': (p.stops || []).map(function (s) {
        return (s.when ? s.when + ' — ' : '') + (s.h || '')
          + (s.p ? '\n    ' + s.p : '');
      }).join('\n'),
      'Included': (p.included || []).join('\n'),
      'Questions': (p.faq || []).map(function (f) {
        return f[0] + '\n    ' + f[1];
      }).join('\n'),
      'Photographs': (p.photos || []).map(function (f) {
        return (f.url || f.id || '') + (f.alt ? ' — ' + f.alt : '');
      }).join('\n')
    };
  }

  function diferenca(velho, novo) {
    var linhas = [];

    function par(rotulo, a, b) {
      a = texto(a); b = texto(b);
      if (a === b) return;
      var tipo = !a ? 'novo' : (!b ? 'ido' : 'mud');
      var h = '<div class="dif-l dif-' + tipo + '">'
        + '<p class="dif-campo">' + rotulo + '</p>';
      if (a) h += '<p class="dif-v dif-fora">' + ewt.escapar(a) + '</p>';
      if (b) h += '<p class="dif-v dif-dentro">' + ewt.escapar(b) + '</p>';
      linhas.push(h + '</div>');
    }

    if (!velho) {
      // Primeira versao: nao ha nada com que comparar, mostra-se tudo.
      CAMPOS.forEach(function (c) {
        if (novo[c[0]]) par(c[1], '', novo[c[0]]);
      });
      par('Prices', '', precos(novo));
      var l = listas(novo);
      Object.keys(l).forEach(function (k) { if (l[k]) par(k, '', l[k]); });
      return '<div class="dif">' + linhas.join('') + '</div>';
    }

    CAMPOS.forEach(function (c) { par(c[1], velho[c[0]], novo[c[0]]); });
    par('Prices', precos(velho), precos(novo));
    var lv = listas(velho), ln = listas(novo);
    Object.keys(ln).forEach(function (k) { par(k, lv[k], ln[k]); });

    if (!linhas.length) {
      return '<p class="dif-v dif-igual">Nothing changed from the version '
        + 'already on the site. Approving this only moves the version '
        + 'number forward.</p>';
    }
    return '<div class="dif">' + linhas.join('') + '</div>';
  }

  // ----------------------------------------------------------- as filas
  async function filaTours() {
    var r = await ewt.sb.from('listing_versions')
      .select('id, listing_id, version, payload, submitted_at, '
            + 'listings(id, slug, status, city, country, '
            + 'operators(id, name, status, commission_rate))')
      .eq('status', 'pending')
      .order('submitted_at', { ascending: true });

    if (r.error) return '<div class="aviso aviso-mal">'
      + ewt.escapar(ewt.legivel(r.error)) + '</div>';

    var vs = r.data || [];
    if (!vs.length) {
      return '<div class="vazio"><h3>Nothing waiting</h3>'
        + '<p>No operator has submitted anything since you last looked.</p></div>';
    }

    // A versao que esta no ar, para cada um dos anuncios desta fila.
    var noAr = {};
    var ids = vs.map(function (v) { return v.listing_id; });
    var a = await ewt.sb.from('listing_versions')
      .select('listing_id, version, payload')
      .in('listing_id', ids).eq('status', 'approved')
      .order('version', { ascending: false });
    (a.data || []).forEach(function (x) {
      if (!noAr[x.listing_id]) noAr[x.listing_id] = x;
    });

    return vs.map(function (v) {
      var l = v.listings || {};
      var o = l.operators || {};
      var velho = noAr[v.listing_id];
      var p = v.payload || {};
      var d = new Date(v.submitted_at);
      return '<article class="rv" data-v="' + v.id + '">'
        + '<div class="rv-t"><div>'
        + '<h3 class="rv-n">' + ewt.escapar(p.title || l.slug) + '</h3>'
        + '<p class="rv-m">'
        + '<span><b>' + ewt.escapar(o.name || 'unknown operator') + '</b></span>'
        + '<span class="est est-' + (o.status || 'pending') + '">'
        + (o.status || 'pending') + '</span>'
        + '<span>' + ewt.escapar(l.city || '') + ', '
        + ewt.escapar(l.country || '') + '</span>'
        + '<span>version ' + v.version
        + (velho ? ' — replacing v' + velho.version : ' — first version')
        + '</span>'
        + '<span>sent ' + d.toLocaleDateString(undefined,
            { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })
        + '</span></p></div>'
        + '<div class="acoes">'
        + '<a class="bt bt-s bt-pq" href="/tours/' + ewt.escapar(l.slug)
        + '/" target="_blank" rel="noopener">See it live</a>'
        + '</div></div>'
        + '<div class="rv-c">' + diferenca(velho ? velho.payload : null, p)
        + '<button type="button" class="dobra" data-todo="' + v.id
        + '">Show everything that was submitted</button>'
        + '<pre class="todo" id="todo-' + v.id + '" hidden>'
        + ewt.escapar(JSON.stringify(p, null, 2)) + '</pre>'
        + '</div>'
        + '<div class="rv-acoes">'
        + '<div class="campo"><label for="nota-' + v.id + '">Why, if you '
        + 'are sending it back</label>'
        + '<input type="text" id="nota-' + v.id + '" maxlength="300" '
        + 'placeholder="The operator reads this exactly as you write it."></div>'
        + '<div class="acoes">'
        + '<button type="button" class="bt bt-p" data-sim="' + v.id
        + '">Approve and publish</button>'
        + '<button type="button" class="bt bt-mal" data-nao="' + v.id
        + '">Send back</button>'
        + '</div>'
        + '<p class="aviso" id="av-' + v.id + '" role="status" hidden></p>'
        + '</div></article>';
    }).join('');
  }

  async function filaOperadores() {
    var r = await ewt.sb.from('operator_applications')
      .select('*').eq('status', 'new').order('created_at', { ascending: true });
    if (r.error) return '<div class="aviso aviso-mal">'
      + ewt.escapar(ewt.legivel(r.error)) + '</div>';
    var cs = r.data || [];
    if (!cs.length) {
      return '<div class="vazio"><h3>No new applications</h3>'
        + '<p>When an operator applies through <a href="/suppliers/">the '
        + 'operators page</a>, it lands here.</p></div>';
    }
    return cs.map(function (c) {
      var d = new Date(c.created_at);
      function l(r, v) {
        return v ? '<p class="rv-m"><span><b>' + r + ':</b> '
          + ewt.escapar(v) + '</span></p>' : '';
      }
      return '<article class="rv" data-c="' + c.id + '">'
        + '<div class="rv-t"><div>'
        + '<h3 class="rv-n">' + ewt.escapar(c.company) + '</h3>'
        + '<p class="rv-m"><span>' + ewt.escapar(c.city) + ', '
        + ewt.escapar(c.country) + '</span>'
        + '<span>applied ' + d.toLocaleDateString(undefined,
            { day: 'numeric', month: 'short' }) + '</span></p>'
        + '</div></div>'
        + '<div class="rv-c">'
        + l('Contact', c.contact_name) + l('Email', c.email)
        + l('Phone', c.phone) + l('Website', c.website)
        + l('Years operating', c.years) + l('Licence', c.licence_ref)
        + (c.fleet ? '<div class="dif-l dif-mud"><p class="dif-campo">Fleet'
            + '</p><p class="dif-v">' + ewt.escapar(c.fleet) + '</p></div>' : '')
        + (c.tours_text ? '<div class="dif-l dif-mud"><p class="dif-campo">'
            + 'Tours they run today</p><p class="dif-v">'
            + ewt.escapar(c.tours_text) + '</p></div>' : '')
        + '</div>'
        + '<div class="rv-acoes"><div class="acoes">'
        + '<button type="button" class="bt bt-p" data-cand="' + c.id
        + '">Approve as an operator</button>'
        + '<button type="button" class="bt bt-s" data-cont="' + c.id
        + '">Mark as contacted</button>'
        + '<button type="button" class="bt bt-mal" data-rec="' + c.id
        + '">Decline</button>'
        + '</div>'
        + '<p class="aviso" id="av-' + c.id + '" role="status" hidden></p>'
        + '<p class="lado-nota">Approving creates the company in the system '
        + 'with a 20% commission. It does not give anyone a login yet — '
        + 'you link their email to the company afterwards.</p>'
        + '</div></article>';
    }).join('');
  }

  async function filaPedidos() {
    // Dois grupos: os por responder, e os que ja viajaram e ainda nao
    // foram convidados a avaliar. O segundo e o que se esquece — e
    // esquece-se exatamente quando mais vale a pena pedir, logo a
    // seguir ao dia.
    var r = await ewt.sb.from('enquiries')
      .select('*').in('status', ['new', 'answered', 'booked'])
      .order('created_at', { ascending: false });
    if (r.error) return '<div class="aviso aviso-mal">'
      + ewt.escapar(ewt.legivel(r.error)) + '</div>';
    var ps = r.data || [];
    if (!ps.length) {
      return '<div class="vazio"><h3>No unanswered enquiries</h3>'
        + '<p>Everything anyone asked has been dealt with.</p></div>';
    }
    return '<div class="tab-rolo" tabindex="0" role="region" '
      + 'aria-label="Table, scrolls sideways"><table class="tab">'
      + '<thead><tr><th>When</th><th>Who</th><th>Wants</th><th>Message</th>'
      + '<th></th></tr></thead><tbody>'
      + ps.map(function (p) {
        var d = new Date(p.created_at);
        return '<tr><td>' + d.toLocaleDateString(undefined,
            { day: 'numeric', month: 'short' }) + '</td>'
          + '<td><b>' + ewt.escapar(p.name) + '</b><br>'
          + '<a href="mailto:' + ewt.escapar(p.email) + '">'
          + ewt.escapar(p.email) + '</a>'
          + (p.phone ? '<br>' + ewt.escapar(p.phone) : '') + '</td>'
          + '<td>' + (p.listing_slug
              ? '<a href="/tours/' + ewt.escapar(p.listing_slug) + '/">'
                + ewt.escapar(p.listing_slug) + '</a><br>' : '')
          + (p.wanted_on ? ewt.escapar(p.wanted_on) : '')
          + (p.party ? '<br>' + p.party + ' people' : '') + '</td>'
          + '<td>' + ewt.escapar(p.message || '') + '</td>'
          + '<td><button type="button" class="bt bt-s bt-pq" data-ped="'
          + p.id + '">Done</button></td></tr>';
      }).join('')
      + '</tbody></table></div>';
  }

  // ---------------------------------------------------------- as acoes
  async function decidir(id, aprovar) {
    var nota = document.getElementById('nota-' + id);
    var texto = nota ? nota.value.trim() : '';
    if (!aprovar && texto.length < 5) {
      ewt.dizer('av-' + id, 'Write why you are sending it back. The '
        + 'operator sees this sentence and nothing else — without it '
        + 'they do not know what to change.', 'mal');
      if (nota) nota.focus();
      return;
    }
    travar(id, true);
    var r = await ewt.sb.rpc('rever_versao', {
      p_version: id, p_aprovar: aprovar, p_nota: texto || null
    });
    travar(id, false);
    if (r.error) {
      ewt.dizer('av-' + id, ewt.legivel(r.error), 'mal');
      return;
    }
    var art = document.querySelector('[data-v="' + id + '"]');
    if (art) {
      art.innerHTML = '<div class="rv-c"><p class="dif-v">'
        + (aprovar ? '<b>Approved.</b> It is live in the database. The site '
            + 'picks it up the next time the pages are generated.'
          : '<b>Sent back.</b> The operator sees your note in their portal.')
        + '</p></div>';
    }
    contar();
  }

  function travar(id, sim) {
    var art = document.querySelector('[data-v="' + id + '"], [data-c="' + id + '"]');
    if (!art) return;
    [].slice.call(art.querySelectorAll('.bt')).forEach(function (b) {
      b.disabled = sim;
    });
  }

  async function candidatura(id, acao) {
    travar(id, true);
    var r;
    if (acao === 'aprovar') {
      r = await ewt.sb.rpc('aprovar_candidatura', { p_cand: id });
    } else {
      r = await ewt.sb.from('operator_applications')
        .update({ status: acao === 'contactar' ? 'contacted' : 'declined' })
        .eq('id', id);
    }
    travar(id, false);
    if (r.error) { ewt.dizer('av-' + id, ewt.legivel(r.error), 'mal'); return; }
    var art = document.querySelector('[data-c="' + id + '"]');
    if (art) {
      art.innerHTML = '<div class="rv-c"><p class="dif-v">'
        + (acao === 'aprovar'
            ? '<b>Approved.</b> The company exists in the system. Next: link '
              + 'their email to it so they can sign in to the portal.'
            : acao === 'contactar'
              ? '<b>Marked as contacted.</b> It leaves this queue.'
              : '<b>Declined.</b> Nothing was sent to them automatically.')
        + '</p></div>';
    }
    contar();
  }

  async function pedidoFeito(id) {
    var r = await ewt.sb.from('enquiries')
      .update({ status: 'answered' }).eq('id', id);
    if (r.error) { alert(ewt.legivel(r.error)); return; }
    var tr = document.querySelector('[data-ped="' + id + '"]');
    if (tr) {
      var l = tr.closest('tr');
      if (l) l.remove();
    }
    contar();
  }

  // --------------------------------------------------------- as contagens
  async function contar() {
    var a = await ewt.sb.from('listing_versions')
      .select('id', { count: 'exact', head: true }).eq('status', 'pending');
    var b = await ewt.sb.from('operator_applications')
      .select('id', { count: 'exact', head: true }).eq('status', 'new');
    var c = await ewt.sb.from('enquiries')
      .select('id', { count: 'exact', head: true })
      .in('status', ['new', 'answered', 'booked']);
    pintar('n-tours', a.count); pintar('n-ops', b.count); pintar('n-peds', c.count);
  }
  function pintar(id, n) {
    var e = document.getElementById(id);
    if (!e) return;
    n = n || 0;
    e.textContent = n;
    e.className = 'n' + (n ? '' : ' n-0');
  }

  // ------------------------------------------------------------- abas
  async function mostrar(qual) {
    E.aba = qual;
    ['tours','ops','peds'].forEach(function (k) {
      var b = document.getElementById('aba-' + k);
      if (b) b.setAttribute('aria-selected', k === qual ? 'true' : 'false');
    });
    var c = document.getElementById('fila');
    c.innerHTML = '<p class="carrega">Loading…</p>';
    c.innerHTML = qual === 'tours' ? await filaTours()
                : qual === 'ops'   ? await filaOperadores()
                :                    await filaPedidos();
  }

  // ----------------------------------------------------------- arranque
  (async function () {
    var p = await ewt.exigir_entrada();
    if (!p) return;

    document.getElementById('carrega').hidden = true;

    if (!p.admin) {
      // Nao e um erro tecnico: e alguem num sitio que nao e o dele.
      document.getElementById('conteudo').innerHTML =
        '<div class="vazio"><h3>This area is not yours</h3>'
        + '<p>You are signed in as ' + ewt.escapar(p.email)
        + ', which is not an administrator account.</p>'
        + '<a class="bt bt-p" href="/portal/">Go to the operator portal</a></div>';
      return;
    }

    document.getElementById('ad').hidden = false;

    document.getElementById('abas').addEventListener('click', function (ev) {
      var b = ev.target.closest('.aba');
      if (b) mostrar(b.getAttribute('data-aba'));
    });

    // A data da viagem grava-se ao sair do campo e nao a cada tecla.
    document.getElementById('fila').addEventListener('change', function (ev) {
      var i = ev.target.closest('[data-viajou]');
      if (i) marcarViagem(i.getAttribute('data-viajou'), i.value);
    });

    document.getElementById('fila').addEventListener('click', function (ev) {
      var t = ev.target;
      var b = t.closest('button');
      if (!b) return;
      if (b.hasAttribute('data-sim'))  return decidir(b.getAttribute('data-sim'), true);
      if (b.hasAttribute('data-nao'))  return decidir(b.getAttribute('data-nao'), false);
      if (b.hasAttribute('data-cand')) return candidatura(b.getAttribute('data-cand'), 'aprovar');
      if (b.hasAttribute('data-cont')) return candidatura(b.getAttribute('data-cont'), 'contactar');
      if (b.hasAttribute('data-rec'))  return candidatura(b.getAttribute('data-rec'), 'recusar');
      if (b.hasAttribute('data-ped'))  return pedidoFeito(b.getAttribute('data-ped'));
      if (b.hasAttribute('data-conv')) return convidar(b.getAttribute('data-conv'));
      if (b.hasAttribute('data-liga')) return copiarLigacao(b.getAttribute('data-liga'));
      if (b.hasAttribute('data-todo')) {
        var pre = document.getElementById('todo-' + b.getAttribute('data-todo'));
        if (pre) {
          pre.hidden = !pre.hidden;
          b.textContent = pre.hidden ? 'Show everything that was submitted'
                                     : 'Hide the full submission';
        }
      }
    });

    await contar();
    await mostrar('tours');
  })();
})();
"""


def corpo():
    return '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">
    <p class="carrega" id="carrega">Loading the queue&hellip;</p>

    <div id="ad" hidden>
      <div class="pt-cab">
        <h1>Review queue</h1>
        <p>Nothing an operator writes reaches the site until it passes
          through here. Every submission is shown against the version
          already online, so you read what changed and not the whole
          thing again.</p>
      </div>

      <div class="abas" id="abas" role="tablist">
        <button type="button" class="aba" id="aba-tours" data-aba="tours"
                role="tab" aria-selected="true">
          Tours <span class="n n-0" id="n-tours">0</span>
        </button>
        <button type="button" class="aba" id="aba-ops" data-aba="ops"
                role="tab" aria-selected="false">
          Operators <span class="n n-0" id="n-ops">0</span>
        </button>
        <button type="button" class="aba" id="aba-peds" data-aba="peds"
                role="tab" aria-selected="false">
          Enquiries <span class="n n-0" id="n-peds">0</span>
        </button>
      </div>

      <div id="fila"></div>
    </div>
  </div>
</main>'''


def gerar():
    pagina.verificar_contraste()
    html = portal_base.envolver(
        titulo='Review queue — Exclusive World Tours',
        corpo=corpo(), js=JS, etiqueta='Administration',
        nav=NAV, atual='/admin/', css_extra=CSS)
    pagina.escrever(html, 'admin/index.html')


if __name__ == '__main__':
    gerar()
