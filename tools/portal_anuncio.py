# -*- coding: utf-8 -*-
"""O editor de anuncios do operador.

O que o operador escreve aqui tem exatamente a forma de uma entrada do
`tours.json` — e de proposito. O gerador do site le `payload` sem
traduzir nada: se houvesse uma traducao pelo meio, haveria dois formatos
a divergir, e o dia em que divergem e o dia em que o site mostra uma
coisa diferente do que o operador escreveu.

Nada do que se grava aqui vai para o site. Gravar cria um rascunho; so
"Submit for review" cria uma versao, e so a aprovacao a poe no ar.
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
.ed { display: grid; gap: 1.1rem; }
@media (min-width: 1040px) {
  .ed { grid-template-columns: minmax(0,1fr) 19rem; align-items: start; }
}

/* --------------------------------------------------- linhas repetiveis */
.rep { display: grid; gap: .7rem; }
.rep-l {
  display: grid; gap: .6rem; align-items: start;
  padding: .8rem; border: 1px solid %(risco)s; border-radius: 5px;
  background: %(papel)s;
}
.rep-l > .campo { margin: 0; }
.rep-x {
  justify-self: start;
  font: 500 .8rem/1 'Inter', system-ui, sans-serif;
  color: #8C1D18; background: none; border: 1px solid #B3261E;
  border-radius: 4px; padding: .45rem .6rem; cursor: pointer;
}
.rep-x:hover { background: #FCEEEC; }
.rep-mais {
  justify-self: start; margin-top: .3rem;
  font: 600 .85rem/1 'Inter', system-ui, sans-serif;
  color: %(tinta)s; background: %(branco)s;
  border: 1px dashed %(mudo)s; border-radius: 4px;
  padding: .6rem .85rem; cursor: pointer;
}
.rep-mais:hover { border-style: solid; border-color: %(tinta)s; }
@media (min-width: 700px) {
  .rep-escalao { grid-template-columns: 5.5rem 5.5rem 1fr 8rem auto;
                 align-items: end; }
  .rep-paragem { grid-template-columns: 7rem 1fr; }
  .rep-paragem .rep-p-t, .rep-paragem .rep-x { grid-column: 1 / -1; }
  .rep-faq { grid-template-columns: 1fr; }
}

/* ------------------------------------------------------------- barra */
.lado { position: sticky; top: 76px; }
.lado .cx { margin-bottom: .9rem; }
.lado .acoes { flex-direction: column; align-items: stretch; }
.lado .bt { width: 100%%; text-align: center; box-sizing: border-box; }
.lado-nota {
  font: 400 .82rem/1.5 'Inter', system-ui, sans-serif;
  color: %(mudo)s; margin: .7rem 0 0;
}
.hist { font: 400 .84rem/1.5 'Inter', system-ui, sans-serif; }
.hist div {
  padding: .45rem 0; border-bottom: 1px solid %(risco)s;
  display: flex; gap: .5rem; align-items: center; justify-content: space-between;
}
.hist div:last-child { border-bottom: 0; }
.conta {
  margin-top: .7rem; padding-top: .7rem; border-top: 1px solid %(risco)s;
  font: 400 .84rem/1.6 'Inter', system-ui, sans-serif; color: %(texto)s;
}
.conta b { font-variant-numeric: tabular-nums; }
""" % CORES


JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  var ID = new URLSearchParams(location.search).get('id');  // null = novo
  var ESTADO = { anuncio: null, operador: null, versoes: [], sujo: false };

  // ------------------------------------------------------------- campos
  var contaLinhas = 0;
  //
  // Uma linha repetivel. Os indices nos `name` nao servem para nada: o
  // que conta e a ordem no DOM, que e a ordem que o operador ve. Ler
  // por indice dava listas com buracos depois de apagar uma linha.
  function linha(tipo, v) {
    v = v || {};
    // Um numero que so cresce, para os ids dos campos. Apagar uma linha
    // nao devolve o numero ao saco: se devolvesse, dois campos acabavam
    // com o mesmo id e um label passava a apontar para o campo errado.
    var k = 'r' + (++contaLinhas);
    var d = document.createElement('div');
    d.className = 'rep-l rep-' + tipo;
    if (tipo === 'escalao') {
      d.innerHTML =
        '<div class="campo"><label for="' + k + '-0">From</label>'
        + '<input id="' + k + '-0" type="number" data-c="min" min="1" '
        + 'max="199" value="' + (v.min || 1) + '"></div>'
        + '<div class="campo"><label for="' + k + '-1">Up to</label>'
        + '<input id="' + k + '-1" type="number" data-c="max" min="1" max="199" value="'
        + (v.max || '') + '" required></div>'
        + '<div class="campo"><label for="' + k + '-2">Vehicle</label>'
        + '<input id="' + k + '-2" type="text" data-c="vehicle" maxlength="80" value="'
        + ewt.escapar(v.vehicle || '') + '" placeholder="Sedan, minivan…"></div>'
        + '<div class="campo"><label for="' + k + '-3">Group price &euro;</label>'
        + '<input id="' + k + '-3" type="number" data-c="price" min="0" step="0.01" value="'
        + (v.price === 0 || v.price ? v.price : '') + '" required></div>'
        + '<button type="button" class="rep-x">Remove</button>';
    } else if (tipo === 'paragem') {
      d.innerHTML =
        '<div class="campo"><label for="' + k + '-4">Time</label>'
        + '<input id="' + k + '-4" type="text" data-c="when" maxlength="12" value="'
        + ewt.escapar(v.when || '') + '" placeholder="09:10"></div>'
        + '<div class="campo"><label for="' + k + '-5">Stop</label>'
        + '<input id="' + k + '-5" type="text" data-c="h" maxlength="140" value="'
        + ewt.escapar(v.h || '') + '" placeholder="Bunratty Castle"></div>'
        + '<div class="campo rep-p-t"><label for="' + k + '-6">What happens there</label>'
        + '<textarea id="' + k + '-6" data-c="p" maxlength="900" rows="3">'
        + ewt.escapar(v.p || '') + '</textarea></div>'
        + '<button type="button" class="rep-x">Remove stop</button>';
    } else if (tipo === 'texto') {
      d.innerHTML =
        '<div class="campo">'
        + '<label class="so-leitor" for="' + k + '-7">Included item</label>'
        + '<input id="' + k + '-7" type="text" data-c="v" maxlength="220" value="'
        + ewt.escapar(v || '') + '"></div>'
        + '<button type="button" class="rep-x">Remove</button>';
    } else if (tipo === 'faq') {
      d.innerHTML =
        '<div class="campo"><label for="' + k + '-8">Question</label>'
        + '<input id="' + k + '-8" type="text" data-c="q" maxlength="220" value="'
        + ewt.escapar(v[0] || '') + '"></div>'
        + '<div class="campo"><label for="' + k + '-9">Answer</label>'
        + '<textarea id="' + k + '-9" data-c="a" maxlength="1200" rows="3">'
        + ewt.escapar(v[1] || '') + '</textarea></div>'
        + '<button type="button" class="rep-x">Remove</button>';
    } else if (tipo === 'foto') {
      d.innerHTML =
        '<div class="campo"><label for="' + k + '-10">Photo address (URL)</label>'
        + '<input id="' + k + '-10" type="url" data-c="url" maxlength="500" value="'
        + ewt.escapar(v.url || '') + '" placeholder="https://…"></div>'
        + '<div class="campo"><label for="' + k + '-11">What is in the photo</label>'
        + '<input id="' + k + '-11" type="text" data-c="alt" maxlength="200" value="'
        + ewt.escapar(v.alt || '') + '" placeholder="The cliffs above the Atlantic">'
        + '<span class="ajuda">Written for someone who cannot see it. '
        + 'Not a caption — a description.</span></div>'
        + '<button type="button" class="rep-x">Remove</button>';
    }
    var x = d.querySelector('.rep-x');
    // Cinco botoes a dizer "Remove" sao indistinguiveis num leitor de
    // ecra. O rotulo acessivel diz qual deles e.
    x.setAttribute('aria-label', x.textContent.trim() + ' (' + tipo + ' '
      + contaLinhas + ')');
    x.addEventListener('click', function () {
      d.remove(); marcar();
    });
    return d;
  }

  function ligarMais(botao, caixa, tipo) {
    botao.addEventListener('click', function () {
      caixa.appendChild(linha(tipo));
      var i = caixa.lastChild.querySelector('input, textarea');
      if (i) i.focus();
      marcar();
    });
  }

  function encher(caixa, tipo, valores) {
    caixa.innerHTML = '';
    (valores || []).forEach(function (v) { caixa.appendChild(linha(tipo, v)); });
  }

  function ler(caixa) {
    return [].slice.call(caixa.children).map(function (l) {
      var o = {};
      [].slice.call(l.querySelectorAll('[data-c]')).forEach(function (c) {
        o[c.getAttribute('data-c')] = c.value.trim();
      });
      return o;
    });
  }

  // O aviso minimo. E um numero inteiro de horas e nao faz parte do
  // conteudo: mudar de 24 para 48 horas nao e uma alteracao que alguem
  // precise de ler, e esperar por revisao para a aplicar seria o mesmo
  // erro que esperar por revisao para fechar um dia.
  function aviso() {
    var e = document.getElementById('aviso');
    var n = e ? parseInt(e.value, 10) : 24;
    return isFinite(n) ? n : 24;
  }

  function v(id) { var e = document.getElementById(id); return e ? e.value.trim() : ''; }
  function pv(id, x) { var e = document.getElementById(id); if (e) e.value = x == null ? '' : x; }

  // --------------------------------------------------------- o conteudo
  //
  // Exatamente a forma de uma entrada do tours.json. O gerador le isto
  // sem traduzir.
  function recolher() {
    var escaloes = ler(document.getElementById('escaloes'))
      .filter(function (x) { return x.max && x.price !== ''; })
      .map(function (x) {
        var o = { max: parseInt(x.max, 10), price: Number(x.price) };
        // O minimo so vai para o conteudo quando nao e 1: um escalao que
        // comeca em 1 e o caso normal, e escrever "min: 1" em todos os
        // escaloes de todos os tours e ruido no payload.
        var mn = parseInt(x.min, 10);
        if (mn > 1) o.min = mn;
        if (x.vehicle) o.vehicle = x.vehicle;
        return o;
      })
      .sort(function (a, b) { return a.max - b.max; });

    var horas = v('partidas').split(',').map(function (s) { return s.trim(); })
      .filter(Boolean);

    var p = {
      slug: v('slug'),
      title: v('titulo'),
      kicker: v('kicker'),
      lede: v('lede'),
      city: v('cidade'),
      country: v('pais_cod'),
      countryName: v('pais'),
      ticketTo: v('entrada_para'),
      metaDesc: v('meta'),
      durations: [{
        h: v('duracao'),
        price: escaloes.length ? Math.min.apply(null, escaloes.map(function (x) { return x.price; })) : 0,
        tiers: escaloes,
        startTimes: horas
      }],
      stopsIntro: v('paragens_intro'),
      stops: ler(document.getElementById('paragens'))
        .filter(function (x) { return x.h; }),
      includedIntro: v('inclui_intro'),
      included: ler(document.getElementById('inclui'))
        .map(function (x) { return x.v; }).filter(Boolean),
      notIncluded: v('nao_inclui'),
      practical: v('pratico'),
      faq: ler(document.getElementById('faq'))
        .filter(function (x) { return x.q && x.a; })
        .map(function (x) { return [x.q, x.a]; }),
      photos: ler(document.getElementById('fotos'))
        .filter(function (x) { return x.url; })
    };
    return p;
  }

  function espalhar(p) {
    p = p || {};
    pv('titulo', p.title); pv('slug', p.slug); pv('kicker', p.kicker);
    pv('lede', p.lede); pv('cidade', p.city); pv('pais', p.countryName);
    pv('pais_cod', p.country); pv('entrada_para', p.ticketTo);
    pv('meta', p.metaDesc);
    var d = (p.durations && p.durations[0]) || {};
    pv('duracao', d.h);
    pv('partidas', (d.startTimes || []).join(', '));
    encher(document.getElementById('escaloes'), 'escalao', d.tiers || [{}]);
    pv('paragens_intro', p.stopsIntro);
    encher(document.getElementById('paragens'), 'paragem', p.stops || []);
    pv('inclui_intro', p.includedIntro);
    encher(document.getElementById('inclui'), 'texto', p.included || []);
    pv('nao_inclui', p.notIncluded);
    pv('pratico', p.practical);
    encher(document.getElementById('faq'), 'faq', p.faq || []);
    encher(document.getElementById('fotos'), 'foto', p.photos || []);
    contar();
  }

  // -------------------------------------------------------- verificacao
  //
  // A base recusa o que esta mal, mas uma recusa da base e uma mensagem
  // tecnica. Vale a pena dizer antes, no campo, o que falta.
  function faltas() {
    var f = [];
    if (v('titulo').length < 6) f.push(['titulo', 'Give the tour a title.']);
    if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(v('slug'))) {
      f.push(['slug', 'Lowercase letters, numbers and hyphens only.']);
    }
    if (!v('cidade')) f.push(['cidade', 'Which city does it start from?']);
    if (!v('pais')) f.push(['pais', 'Which country?']);
    if (!v('duracao')) f.push(['duracao', 'How long does the day last?']);
    var esc = ler(document.getElementById('escaloes'))
      .filter(function (x) { return x.max && x.price !== ''; });
    if (!esc.length) f.push(['escaloes', 'Add at least one price tier.']);
    if (v('lede').length < 40) {
      f.push(['lede', 'Write a couple of sentences — this is what people read first.']);
    }
    return f;
  }

  function marcarFaltas(f) {
    ['titulo','slug','cidade','pais','duracao','lede'].forEach(function (id) {
      var e = document.getElementById(id);
      if (e) e.removeAttribute('aria-invalid');
    });
    f.forEach(function (x) {
      var e = document.getElementById(x[0]);
      if (e) e.setAttribute('aria-invalid', 'true');
    });
    if (f.length) {
      var e = document.getElementById(f[0][0]);
      if (e && e.focus) e.focus();
    }
  }

  // ----------------------------------------------------------- o estado
  function marcar() { ESTADO.sujo = true; sinal(); }
  function sinal() {
    var s = document.getElementById('sinal');
    if (s) {
      s.textContent = ESTADO.sujo
        ? 'Not saved yet.'
        : (ESTADO.anuncio ? 'Everything saved.' : '');
    }
  }
  window.addEventListener('beforeunload', function (ev) {
    if (!ESTADO.sujo) return;
    ev.preventDefault(); ev.returnValue = '';
  });

  function contar() {
    // Quanto fica para o operador. Nao e um numero que eu invento: e a
    // comissao que esta na ficha dele, aplicada ao escalao mais barato.
    var c = document.getElementById('conta');
    if (!c) return;
    var taxa = ESTADO.operador && ESTADO.operador.comissao != null
      ? Number(ESTADO.operador.comissao) : null;
    var esc = ler(document.getElementById('escaloes'))
      .filter(function (x) { return x.price !== ''; })
      .map(function (x) { return Number(x.price); });
    if (taxa === null || !esc.length) { c.innerHTML = ''; return; }
    var menor = Math.min.apply(null, esc);
    var com = Math.round(menor * taxa * 100) / 100;
    c.innerHTML = 'On your lowest tier of <b>&euro;' + ewt.euros(menor)
      + '</b>:<br>commission ' + (taxa * 100).toFixed(0) + '% = <b>&euro;'
      + ewt.euros(com) + '</b><br>you receive <b>&euro;'
      + ewt.euros(menor - com) + '</b>';
  }

  // ----------------------------------------------------------- gravar
  async function guardar(submeter) {
    var av = 'av-ed';
    ewt.dizer(av, '', '');

    var f = faltas();
    marcarFaltas(f);
    if (f.length) {
      ewt.dizer(av, f.length === 1 ? f[0][1]
        : 'There are ' + f.length + ' things to fix: ' + f[0][1], 'mal');
      return;
    }

    var p = recolher();
    var bts = [].slice.call(document.querySelectorAll('.lado .bt'));
    bts.forEach(function (b) { b.disabled = true; });

    try {
      if (!ESTADO.anuncio) {
        // O anuncio nasce agora. Fica em `draft`: existir no portal e
        // estar no site sao duas coisas diferentes.
        var r = await ewt.sb.from('listings').insert({
          operator_id: ESTADO.operador.id,
          slug: p.slug, city: p.city, country: p.countryName,
          status: 'draft', lead_time_hours: aviso()
        }).select('id, slug, status, city, country, lead_time_hours').single();
        if (r.error) throw r.error;
        ESTADO.anuncio = r.data;
        history.replaceState({}, '', '/portal/listing/?id=' + r.data.id);
      } else {
        var u = await ewt.sb.from('listings').update({
          slug: p.slug, city: p.city, country: p.countryName,
          lead_time_hours: aviso()
        }).eq('id', ESTADO.anuncio.id);
        if (u.error) throw u.error;
      }

      if (submeter) {
        var s = await ewt.sb.rpc('submeter_versao', {
          p_listing: ESTADO.anuncio.id, p_payload: p
        });
        if (s.error) throw s.error;
        ESTADO.sujo = false;
        ewt.dizer(av, 'Sent for review. Your live version — if you have '
          + 'one — stays on the site until this one is approved. We write '
          + 'to you either way.', 'bem');
        await historico();
      } else {
        // Um rascunho fica no browser e nao na base: a base guarda
        // versoes, e uma versao e uma coisa que alguem vai ler. Enchê-la
        // de rascunhos tornava a fila de revisao inutil.
        try {
          localStorage.setItem('ewt-rascunho-' + (ESTADO.anuncio.id || 'novo'),
            JSON.stringify(p));
        } catch (e) { /* modo privado; nao e grave */ }
        ESTADO.sujo = false;
        ewt.dizer(av, 'Saved as a draft on this device. Nothing was sent '
          + 'for review and nothing changed on the site.', 'bem');
      }
      sinal();
    } catch (err) {
      ewt.dizer(av, ewt.legivel(err), 'mal');
    } finally {
      bts.forEach(function (b) { b.disabled = false; });
    }
  }

  // ---------------------------------------------------------- historico
  async function historico() {
    var h = document.getElementById('hist');
    if (!h || !ESTADO.anuncio) return;
    var r = await ewt.sb.from('listing_versions')
      .select('version, status, submitted_at, review_note')
      .eq('listing_id', ESTADO.anuncio.id)
      .order('version', { ascending: false });
    var vs = r.data || [];
    ESTADO.versoes = vs;
    if (!vs.length) {
      h.innerHTML = '<p class="lado-nota">Never submitted.</p>';
      return;
    }
    h.innerHTML = vs.map(function (x) {
      var d = new Date(x.submitted_at);
      return '<div><span>v' + x.version + ' &middot; '
        + d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
        + '</span><span class="est est-' + x.status + '">' + x.status
        + '</span></div>'
        + (x.status === 'rejected' && x.review_note
            ? '<p class="lado-nota">' + ewt.escapar(x.review_note) + '</p>' : '');
    }).join('');
  }

  // ----------------------------------------------------------- arranque
  (async function () {
    var pp = await ewt.exigir_entrada();
    if (!pp) return;

    if (!pp.operadores.length) {
      document.getElementById('conteudo').innerHTML =
        '<div class="vazio"><h3>Your account is not linked to a company</h3>'
        + '<p>Only an approved operator can add tours.</p>'
        + '<a class="bt bt-s" href="/portal/">Back to the portal</a></div>';
      return;
    }
    ESTADO.operador = pp.operadores[0];

    document.getElementById('carrega').hidden = true;
    document.getElementById('ed').hidden = false;

    // Os botoes de acrescentar linha.
    [['mais-escalao','escaloes','escalao'], ['mais-paragem','paragens','paragem'],
     ['mais-inclui','inclui','texto'], ['mais-faq','faq','faq'],
     ['mais-foto','fotos','foto']].forEach(function (x) {
      ligarMais(document.getElementById(x[0]),
                document.getElementById(x[1]), x[2]);
    });

    document.getElementById('ed').addEventListener('input', function (ev) {
      marcar();
      if (ev.target.closest('#escaloes')) contar();
    });

    // O endereco web sugere-se a partir do titulo, mas so enquanto o
    // operador nao mexer nele: reescrever um endereco que ele escolheu
    // e mudar-lhe o URL do tour sem ele pedir.
    var slugTocado = false;
    document.getElementById('slug').addEventListener('input', function () {
      slugTocado = true;
    });
    document.getElementById('titulo').addEventListener('input', function (ev) {
      if (slugTocado || ESTADO.anuncio) return;
      pv('slug', ev.target.value.toLowerCase()
        .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 70));
    });

    document.getElementById('bt-guardar')
      .addEventListener('click', function () { guardar(false); });
    document.getElementById('bt-submeter')
      .addEventListener('click', function () { guardar(true); });

    if (ID) {
      var r = await ewt.sb.from('listings')
        .select('id, slug, status, city, country, lead_time_hours')
        .eq('id', ID).single();
      if (r.error || !r.data) {
        ewt.dizer('av-ed', 'That tour could not be opened. It may belong to '
          + 'another account.', 'mal');
        return;
      }
      ESTADO.anuncio = r.data;
      if (r.data.lead_time_hours != null) {
        var sel = document.getElementById('aviso');
        var tem = [].slice.call(sel.options).some(function (o) {
          return o.value === String(r.data.lead_time_hours);
        });
        // Um valor posto pela administracao que nao esteja na lista nao
        // se perde nem se arredonda em silencio: entra na lista.
        if (!tem) {
          var o = document.createElement('option');
          o.value = String(r.data.lead_time_hours);
          o.textContent = r.data.lead_time_hours + ' hours';
          sel.appendChild(o);
        }
        sel.value = String(r.data.lead_time_hours);
      }
      document.getElementById('t-ed').textContent = 'Edit tour';
      document.getElementById('est-ed').innerHTML =
        '<span class="est est-' + r.data.status + '">' + r.data.status + '</span>';

      // O que se abre e a ultima versao que existe — pendente ou
      // aprovada. Abrir a aprovada quando ha uma pendente fazia o
      // operador reescrever as alteracoes que acabou de enviar.
      var vv = await ewt.sb.from('listing_versions')
        .select('version, status, payload')
        .eq('listing_id', ID).order('version', { ascending: false }).limit(1);
      if (vv.data && vv.data.length) {
        espalhar(vv.data[0].payload);
      } else {
        espalhar({ city: r.data.city, countryName: r.data.country,
                   slug: r.data.slug });
      }
      await historico();
    } else {
      espalhar({});
    }
    ESTADO.sujo = false;
    sinal();
  })();
})();
"""


def corpo():
    return '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">
    <p class="carrega" id="carrega">Loading&hellip;</p>

    <div id="ed" hidden>
      <div class="pt-cab">
        <h1 id="t-ed">Add a tour</h1>
        <p>Write it as you would say it to a guest. We read every
          submission before it goes on the site &mdash; and we read what
          you wrote, not a shortened version of it. <span id="est-ed"></span></p>
      </div>

      <p class="aviso" id="av-ed" role="status" hidden></p>

      <div class="ed">
        <div>
          <div class="cx">
            <p class="cx-t">The tour</p>
            <div class="campo">
              <label for="titulo">Title <span class="obrig">*</span></label>
              <input type="text" id="titulo" maxlength="140"
                     placeholder="Private Tour: Cliffs of Moher &amp; Galway">
            </div>
            <div class="linha2">
              <div class="campo">
                <label for="slug">Web address <span class="obrig">*</span></label>
                <input type="text" id="slug" maxlength="70"
                       placeholder="cliffs-of-moher-galway">
                <span class="ajuda">Becomes
                  exclusiveworldtours.com/tours/&hellip;/ &mdash; changing it
                  later breaks links people already have.</span>
              </div>
              <div class="campo">
                <label for="kicker">One line above the title</label>
                <input type="text" id="kicker" maxlength="90"
                       placeholder="Private day tour from Dublin">
              </div>
            </div>
            <div class="campo">
              <label for="lede">The opening paragraph <span class="obrig">*</span></label>
              <textarea id="lede" maxlength="700" rows="4"
                placeholder="What the day is, in two or three sentences."></textarea>
              <span class="ajuda">This is what people read before anything
                else. Say what makes your day different, not that it is
                unforgettable.</span>
            </div>
            <div class="linha2">
              <div class="campo">
                <label for="cidade">Starts from (city) <span class="obrig">*</span></label>
                <input type="text" id="cidade" maxlength="80" placeholder="Dublin">
              </div>
              <div class="campo">
                <label for="pais">Country <span class="obrig">*</span></label>
                <input type="text" id="pais" maxlength="80" placeholder="Ireland">
              </div>
            </div>
            <div class="linha2">
              <div class="campo">
                <label for="duracao">How long <span class="obrig">*</span></label>
                <input type="text" id="duracao" maxlength="30" placeholder="12h 30m">
              </div>
              <div class="campo">
                <label for="partidas">Departure times</label>
                <input type="text" id="partidas" maxlength="120" placeholder="07:00, 09:00">
                <span class="ajuda">Separated by commas.</span>
              </div>
            </div>
            <div class="campo">
              <label for="aviso">How much notice you need</label>
              <select id="aviso">
                <option value="0">Same day is fine</option>
                <option value="12">12 hours</option>
                <option value="24" selected>24 hours</option>
                <option value="48">2 days</option>
                <option value="72">3 days</option>
                <option value="120">5 days</option>
                <option value="168">A week</option>
              </select>
              <span class="ajuda">Days inside this window stop being
                offered, and a request for one is refused before it
                reaches you. Put the real number: the big marketplaces cap
                this at ten hours, which is not enough time to find a
                driver, and we are not going to pretend otherwise.</span>
            </div>
            <div class="linha2">
              <div class="campo">
                <label for="entrada_para">Main attraction</label>
                <input type="text" id="entrada_para" maxlength="120"
                       placeholder="Cliffs of Moher">
                <span class="ajuda">If an entrance ticket is included, name
                  what it is for.</span>
              </div>
              <div class="campo">
                <label for="meta">Search-engine description</label>
                <input type="text" id="meta" maxlength="170">
                <span class="ajuda">About 160 characters. Left empty, we
                  use the opening paragraph.</span>
              </div>
            </div>
          </div>

          <div class="cx">
            <p class="cx-t">Price by group size</p>
            <p class="lado-nota" style="margin:0 0 .9rem">One line per
              vehicle. The price is for the <b>whole group</b>, not per
              person &mdash; that is the thing that makes this site
              different from the big ones, so the number has to be the
              number you would charge.</p>
            <div class="rep" id="escaloes"></div>
            <button type="button" class="rep-mais" id="mais-escalao">Add a
              group size</button>
          </div>

          <div class="cx">
            <p class="cx-t">The day, stop by stop</p>
            <div class="campo">
              <label for="paragens_intro">A line before the stops</label>
              <textarea id="paragens_intro" maxlength="500" rows="2"
                placeholder="A guide, not a timetable."></textarea>
            </div>
            <div class="rep" id="paragens"></div>
            <button type="button" class="rep-mais" id="mais-paragem">Add a
              stop</button>
          </div>

          <div class="cx">
            <p class="cx-t">What the price covers</p>
            <div class="campo">
              <label for="inclui_intro">A line before the list</label>
              <input type="text" id="inclui_intro" maxlength="200"
                     placeholder="The price covers the vehicle.">
            </div>
            <div class="rep" id="inclui"></div>
            <button type="button" class="rep-mais" id="mais-inclui">Add an
              item</button>
            <div class="campo" style="margin-top:1.1rem">
              <label for="nao_inclui">What is not included</label>
              <textarea id="nao_inclui" maxlength="900" rows="3"></textarea>
              <span class="ajuda">Say it plainly here and nobody argues
                about it on the day.</span>
            </div>
            <div class="campo">
              <label for="pratico">Practical notes</label>
              <textarea id="pratico" maxlength="1200" rows="3"
                placeholder="What to wear, how much walking, child seats…"></textarea>
            </div>
          </div>

          <div class="cx">
            <p class="cx-t">Questions guests ask</p>
            <div class="rep" id="faq"></div>
            <button type="button" class="rep-mais" id="mais-faq">Add a
              question</button>
          </div>

          <div class="cx">
            <p class="cx-t">Photographs</p>
            <p class="lado-nota" style="margin:0 0 .9rem">Your own
              photographs of your own tour. Not stock, not the tourist
              board's &mdash; guests notice, and so do we.</p>
            <div class="rep" id="fotos"></div>
            <button type="button" class="rep-mais" id="mais-foto">Add a
              photograph</button>
          </div>
        </div>

        <!-- --------------------------------------------------- barra -->
        <aside class="lado">
          <div class="cx">
            <p class="cx-t">Publish</p>
            <div class="acoes">
              <button type="button" class="bt bt-p" id="bt-submeter">Submit
                for review</button>
              <button type="button" class="bt bt-s" id="bt-guardar">Save a
                draft</button>
            </div>
            <p class="lado-nota" id="sinal" role="status"></p>
            <p class="lado-nota">A draft stays on this device. Submitting
              creates a new version; the one on the site stays up until
              yours is approved.</p>
          </div>

          <div class="cx">
            <p class="cx-t">What you receive</p>
            <div class="conta" id="conta"></div>
          </div>

          <div class="cx">
            <p class="cx-t">Versions</p>
            <div class="hist" id="hist">
              <p class="lado-nota">Never submitted.</p>
            </div>
          </div>
        </aside>
      </div>
    </div>
  </div>
</main>'''


def gerar():
    pagina.verificar_contraste()
    html = portal_base.envolver(
        titulo='Edit a tour — Exclusive World Tours',
        corpo=corpo(), js=JS, etiqueta='Operator portal',
        nav=NAV, atual='', css_extra=CSS)
    pagina.escrever(html, 'portal/listing/index.html')


if __name__ == '__main__':
    gerar()
