# -*- coding: utf-8 -*-
"""As promocoes do operador.

A ideia, em duas frases
-----------------------
Uma promocao tem DUAS janelas independentes, e e isso que a distingue de
um desconto qualquer: a janela em que se pode RESERVAR e a janela em que
se VIAJA. "Reserve ate ao fim do mes para viajar em Setembro" precisa das
duas, e com uma so nao se escreve.

A outra metade e quem paga. Uma promocao do operador sai da margem dele;
uma campanha nossa sai da nossa comissao e NAO lhe corta a margem. A
coluna existe na base desde a 020 e nunca teve ecra — o que significa que
na pratica so existia a primeira.

O que esta pagina esconde de proposito
--------------------------------------
O `quem_paga` nao aparece aqui. Um operador so pode criar promocoes que
ele proprio paga, e dar-lhe um interruptor com "a plataforma paga" seria
dar-lhe um botao para gastar o meu dinheiro. A coluna fica no valor por
omissao — `operator` — e as campanhas da plataforma criam-se do lado da
administracao, quando houver uma.

Por isso a pagina diz, por palavras, o que o desconto lhe custa. Um
operador que carrega em "20%" sem perceber de onde sai vai descobri-lo
no fim do mes, e essa e a pior altura.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pagina
import portal_base
from portal import NAV

CORES = portal_base.FICHAS

CSS = """
.pr { display: grid; gap: .7rem; margin-bottom: 1.6rem; }
.pm {
  background: var(--sup); border-radius: var(--r-g);
  padding: 1.1rem 1.2rem; box-shadow: var(--sombra);
  display: flex; flex-wrap: wrap; gap: .7rem 1rem; align-items: baseline;
}
/* Como nas epocas: uma promocao e uma FRASE, nao uma linha de tabela com
   seis colunas e um cabecalho que e preciso ler para saber o que e
   cada uma. */
.pm-f {
  flex: 1 1 22rem; margin: 0;
  font-size: 1rem; line-height: 1.6; color: var(--tinta-2);
}
.pm-f b { color: var(--tinta); font-weight: 600; }
.pm-v {
  font-size: 1.15rem; font-weight: 700; color: var(--acento);
  background: var(--acento-f); border-radius: var(--r-c);
  padding: .3rem .85rem; flex: 0 0 auto;
}
.pm-nota {
  flex-basis: 100%; margin: 0;
  font-size: .85rem; line-height: 1.5; color: var(--mudo);
}
.pm-acoes { display: flex; gap: .5rem; margin-left: auto; }
/* Uma promocao desligada ou fora de prazo nao se apaga: fica, recuada.
   Repetir a campanha do ano passado e uma coisa que se faz. */
.pm-off .pm-f, .pm-off .pm-f b { color: var(--mudo); }
.pm-off .pm-v { color: var(--mudo); background: var(--sup-2); }

/* O tipo: percentagem ou valor. Dois botoes e nao um <select>, pela
   mesma razao do modo nas epocas — a escolha muda o campo seguinte. */
.tipos { display: flex; gap: .5rem; margin-bottom: 1rem; }
.tipo {
  flex: 1 1 0; padding: .8rem 1rem; border-radius: var(--r-m);
  background: var(--sup); text-align: center;
  font-size: .93rem; font-weight: 600; color: var(--tinta);
}
.tipo:hover { background: var(--sup-3); }
.tipo-on { background: var(--sel); color: var(--sel-t); }
.tipo-on:hover { background: var(--sel); filter: brightness(1.12); }


/* O que o desconto custa, em euros, antes de se carregar em gravar. */
.custa {
  margin: 0 0 1rem; padding: .9rem 1.05rem; border-radius: var(--r-m);
  background: var(--acento-f); color: var(--acento);
  font-size: .9rem; line-height: 1.6;
}
.custa b { color: inherit; font-weight: 700; }

.janelas { display: grid; gap: 1.2rem; margin-bottom: .6rem; }
@media (min-width: 760px) { .janelas { grid-template-columns: 1fr 1fr; } }
.janela {
  background: var(--sup); border-radius: var(--r-m); padding: 1.1rem;
}
.janela h3 {
  margin: 0 0 .2rem; font-size: .95rem; font-weight: 600; color: var(--tinta);
}
.janela p {
  margin: 0 0 .9rem; font-size: .83rem; line-height: 1.5; color: var(--mudo);
}
"""


JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  var E = { operador: null, anuncios: [], promos: [], tipo: 'percent',
            comissao: 0.20 };

  function esc(s) { return ewt.escapar(String(s == null ? '' : s)); }

  function legivel(iso) {
    if (!iso) return '';
    var p = String(iso).split('-');
    var d = new Date(+p[0], +p[1] - 1, +p[2]);
    return d.toLocaleDateString(undefined,
      { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function janela(de, ate, verbo) {
    if (!de && !ate) return 'any time';
    if (de && ate) {
      return verbo + ' between <b>' + legivel(de) + '</b> and <b>'
           + legivel(ate) + '</b>';
    }
    if (de) return verbo + ' from <b>' + legivel(de) + '</b> onwards';
    return verbo + ' until <b>' + legivel(ate) + '</b>';
  }

  function valor(p) {
    return p.kind === 'percent'
      ? Number(p.value).toFixed(0) + '% off'
      : '€' + Number(p.value).toFixed(2) + ' off';
  }

  // Uma promocao esta a valer hoje? Nao basta `active`: pode estar
  // ligada e com a janela de reserva ja fechada, e dizer "live" a uma
  // promocao que nao desconta nada e exactamente o tipo de ecra que faz
  // alguem passar uma tarde a perceber porque e que o preco nao muda.
  function aValer(p) {
    if (!p.active) return false;
    var h = ewt.iso(new Date());
    if (p.book_from && h < p.book_from) return false;
    if (p.book_until && h > p.book_until) return false;
    return true;
  }

  function desenhar() {
    var c = document.getElementById('pr');
    if (!E.promos.length) {
      c.innerHTML = '<div class="vazio"><h3>No offer yet</h3>'
        + '<p>An offer lowers the price the customer sees, for the dates '
        + 'you choose. Nothing is discounted until you add one.</p></div>';
      return;
    }
    c.innerHTML = E.promos.map(function (p) {
      var vive = aValer(p);
      var qual = p.listing_id
        ? (E.anuncios.filter(function (a) { return a.id === p.listing_id; })[0]
           || {}).titulo
        : null;
      return '<div class="pm' + (vive ? '' : ' pm-off') + '">'
        + '<span class="pm-v">' + valor(p) + '</span>'
        + '<p class="pm-f"><b>' + esc(p.label) + '</b> — on '
        + (qual ? '<b>' + esc(qual) + '</b>' : '<b>every tour</b>')
        + ', ' + janela(p.book_from, p.book_until, 'booked')
        + ', ' + janela(p.travel_from, p.travel_until, 'travelling') + '.'
        + (vive ? '' : ' <span class="est est-draft">'
            + (p.active ? 'outside its booking window' : 'off') + '</span>')
        + '</p>'
        + '<div class="pm-acoes">'
        + '<button type="button" class="bt bt-s bt-pq" data-liga="' + esc(p.id)
        +   '" data-para="' + (p.active ? 'off' : 'on') + '">'
        +   (p.active ? 'Turn off' : 'Turn on') + '</button>'
        + '<button type="button" class="bt bt-mal bt-pq" data-apaga="'
        +   esc(p.id) + '">Remove</button>'
        + '</div>'
        + '</div>';
    }).join('');
  }

  // ------------------------------------------------- o que isto custa
  //
  // O numero, antes de gravar. Um operador que carrega em "20%" sem
  // perceber de onde sai descobre-o no fim do mes, e essa e a pior
  // altura para descobrir.
  function custa() {
    var c = document.getElementById('custa');
    var v = parseFloat(document.getElementById('valor').value);
    if (!(v > 0)) { c.hidden = true; return; }

    // Um tour de exemplo a 500 euros chega para a conta ser concreta. O
    // que importa nao e o numero exacto: e que a comissao continua a
    // ser calculada sobre o preco JA DESCONTADO, e que a diferenca sai
    // toda do lado do operador.
    var base = 500;
    var desc = E.tipo === 'percent' ? base * v / 100 : v;
    if (desc > base) { desc = base; }
    var novo = base - desc;
    var antes = base - base * E.comissao;
    var depois = novo - novo * E.comissao;

    c.innerHTML = 'On a €500 tour this takes the price to <b>€'
      + novo.toFixed(2) + '</b>. Your share goes from €'
      + antes.toFixed(2) + ' to <b>€' + depois.toFixed(2)
      + '</b> — the discount comes out of your margin, not our '
      + 'commission.';
    c.hidden = false;
  }

  // ------------------------------------------------------------ gravar
  async function criar() {
    var nome = document.getElementById('nome').value.trim();
    var v = parseFloat(document.getElementById('valor').value);
    var qual = document.getElementById('qual').value;

    if (nome.length < 3) {
      ewt.dizer('av-novo', 'Give the offer a name you will recognise in '
        + 'six months.', 'mal');
      return;
    }
    if (!(v > 0)) {
      ewt.dizer('av-novo', 'How much is the discount?', 'mal'); return;
    }
    if (E.tipo === 'percent' && v > 90) {
      // A base tem a mesma regra. Dizer-se aqui poupa a ida e explica
      // porque: noventa por cento nao e uma promocao, e um dedo no
      // teclado.
      ewt.dizer('av-novo', 'A discount above 90% is almost certainly a '
        + 'typo. If you really mean it, use a fixed amount.', 'mal');
      return;
    }

    var l = {
      operator_id: E.operador,
      listing_id: qual || null,
      label: nome,
      kind: E.tipo,
      value: v,
      book_from: document.getElementById('bd').value || null,
      book_until: document.getElementById('ba').value || null,
      travel_from: document.getElementById('vd').value || null,
      travel_until: document.getElementById('va').value || null
      // `quem_paga` fica no valor por omissao: ver a nota no topo deste
      // ficheiro. Um operador nao tem um interruptor para gastar a
      // comissao da plataforma.
    };

    if (l.book_from && l.book_until && l.book_until < l.book_from) {
      ewt.dizer('av-novo', 'The booking window ends before it starts.', 'mal');
      return;
    }
    if (l.travel_from && l.travel_until && l.travel_until < l.travel_from) {
      ewt.dizer('av-novo', 'The travel window ends before it starts.', 'mal');
      return;
    }

    var b = document.getElementById('bt-criar');
    b.disabled = true;
    var r = await ewt.sb.from('promotions').insert(l);
    b.disabled = false;
    if (r.error) { ewt.dizer('av-novo', ewt.legivel(r.error), 'mal'); return; }

    document.getElementById('nome').value = '';
    document.getElementById('valor').value = '';
    document.getElementById('custa').hidden = true;
    ewt.dizer('av-novo', '', '');
    ewt.dizer('av', 'Offer added. The price on the site changes now.', 'bem');
    await carregar();
  }

  async function ligar(id, para) {
    var r = await ewt.sb.from('promotions')
      .update({ active: para === 'on' }).eq('id', id);
    if (r.error) { ewt.dizer('av', ewt.legivel(r.error), 'mal'); return; }
    await carregar();
  }

  async function apagar(id) {
    if (!window.confirm('Remove this offer? Prices go back to normal '
        + 'straight away.')) return;
    var r = await ewt.sb.from('promotions').delete().eq('id', id);
    if (r.error) { ewt.dizer('av', ewt.legivel(r.error), 'mal'); return; }
    ewt.dizer('av', 'Offer removed.', 'bem');
    await carregar();
  }

  async function carregar() {
    var r = await ewt.sb.from('promotions')
      .select('id, listing_id, label, kind, value, active, '
            + 'book_from, book_until, travel_from, travel_until')
      .order('created_at', { ascending: false });
    if (r.error) { ewt.dizer('av', ewt.legivel(r.error), 'mal'); return; }
    E.promos = r.data || [];
    desenhar();
  }

  function desenharTipo() {
    ['percent', 'amount'].forEach(function (k) {
      var b = document.getElementById('tipo-' + k);
      var on = E.tipo === k;
      b.className = 'tipo' + (on ? ' tipo-on' : '');
      b.setAttribute('aria-pressed', on);
    });
    var i = document.getElementById('valor');
    i.setAttribute('max', E.tipo === 'percent' ? '90' : '100000');
    document.getElementById('valor-u').textContent =
      E.tipo === 'percent' ? '% off the price' : 'euros off the price';
    custa();
  }

  (async function () {
    var u = await ewt.exigir_entrada();
    if (!u) return;

    var o = await ewt.sb.from('operators').select('id, name, commission_rate');
    if (o.error || !(o.data || []).length) {
      document.getElementById('carrega').hidden = true;
      document.getElementById('conteudo').innerHTML =
        '<div class="vazio"><h3>No operator account</h3>'
        + '<p>Offers belong to an operator, and this sign-in is not linked '
        + 'to one yet.</p></div>';
      return;
    }
    E.operador = o.data[0].id;
    if (o.data[0].commission_rate != null) {
      E.comissao = Number(o.data[0].commission_rate);
    }

    var r = await ewt.sb.from('listings')
      .select('id, slug, city, listing_versions(payload)').order('created_at');
    E.anuncios = (r.data || []).map(function (l) {
      var v = (l.listing_versions || [])[0];
      l.titulo = (v && v.payload && v.payload.title) || l.slug;
      return l;
    });

    document.getElementById('carrega').hidden = true;
    document.getElementById('pg').hidden = false;

    document.getElementById('qual').innerHTML =
      '<option value="">Every tour</option>'
      + E.anuncios.map(function (a) {
          return '<option value="' + esc(a.id) + '">' + esc(a.titulo)
            + '</option>';
        }).join('');

    ['percent', 'amount'].forEach(function (k) {
      document.getElementById('tipo-' + k).addEventListener('click', function () {
        E.tipo = k; desenharTipo();
      });
    });
    document.getElementById('valor').addEventListener('input', custa);
    document.getElementById('bt-criar').addEventListener('click', criar);
    document.getElementById('pr').addEventListener('click', function (ev) {
      var a = ev.target.closest('[data-apaga]');
      if (a) { apagar(a.getAttribute('data-apaga')); return; }
      var l = ev.target.closest('[data-liga]');
      if (l) { ligar(l.getAttribute('data-liga'), l.getAttribute('data-para')); }
    });

    desenharTipo();
    await carregar();
  })();
})();
"""


def corpo():
    return '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">
    <p class="carrega" id="carrega">Loading your offers&hellip;</p>

    <div id="pg" hidden>
      <div class="pt-cab">
        <h1>Offers</h1>
        <p>An offer lowers the price on the site for the dates you pick.
          It has two windows, and they are not the same thing: when the
          customer can <b>book</b>, and when they <b>travel</b>.</p>
      </div>

      <p class="aviso" id="av" role="status" hidden></p>

      <div class="pr" id="pr"></div>

      <div class="cx cx-fundo">
        <h2 class="cx-t">Add an offer</h2>

        <div class="campo">
          <label for="nome">Name it</label>
          <input type="text" id="nome" placeholder="Early booking, summer">
          <span class="ajuda">Only you see this. It is here for the day
            you have three offers running and need to tell them
            apart.</span>
        </div>

        <div class="campo">
          <span class="rotc" id="rotc-tipo">Discount</span>
          <div class="tipos" role="group" aria-labelledby="rotc-tipo">
            <button type="button" class="tipo" id="tipo-percent"
                    aria-pressed="true">A percentage</button>
            <button type="button" class="tipo" id="tipo-amount"
                    aria-pressed="false">A fixed amount</button>
          </div>
        </div>

        <div class="campo" style="max-width:20rem">
          <label for="valor">How much</label>
          <input type="number" id="valor" min="1" step="1" inputmode="decimal">
          <span class="ajuda" id="valor-u">% off the price</span>
        </div>

        <p class="custa" id="custa" hidden></p>

        <div class="campo" style="max-width:26rem">
          <label for="qual">Which tour</label>
          <select id="qual"></select>
        </div>

        <div class="janelas">
          <div class="janela">
            <h3>Booking window</h3>
            <p>When the customer has to book to get it. Leave both empty
              and it is always on.</p>
            <div class="linha2">
              <div class="campo">
                <label for="bd">From</label>
                <input type="date" id="bd">
              </div>
              <div class="campo">
                <label for="ba">Until</label>
                <input type="date" id="ba">
              </div>
            </div>
          </div>
          <div class="janela">
            <h3>Travel window</h3>
            <p>Which tour dates it applies to. This is what fills a quiet
              month without discounting the busy one.</p>
            <div class="linha2">
              <div class="campo">
                <label for="vd">From</label>
                <input type="date" id="vd">
              </div>
              <div class="campo">
                <label for="va">Until</label>
                <input type="date" id="va">
              </div>
            </div>
          </div>
        </div>

        <p class="aviso" id="av-novo" role="status" hidden></p>

        <div class="acoes">
          <button type="button" class="bt bt-p" id="bt-criar">Add
            offer</button>
        </div>
      </div>
    </div>
  </div>
</main>'''


def gerar():
    pagina.verificar_contraste()
    html = portal_base.envolver(
        titulo='Offers — Exclusive World Tours',
        corpo=corpo(), js=JS, etiqueta='Operator portal',
        nav=NAV, atual='/portal/offers/', css_extra=CSS)
    pagina.escrever(html, 'portal/offers/index.html')


if __name__ == '__main__':
    gerar()
