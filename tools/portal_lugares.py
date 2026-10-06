# -*- coding: utf-8 -*-
"""Os pontos de encontro do operador.

Pertencem ao operador e nao ao anuncio, pela mesma razao que os veiculos:
quem parte sempre da mesma praca nao deve escrever a mesma morada em seis
tours, nem corrigi-la em seis sitios quando uma obra fechar a rua.

E sao dados rapidos — nao passam por revisao. Um ponto de encontro errado
no dia e um cliente parado no sitio errado; fazer isso esperar pela minha
leitura seria o mesmo erro que fazer o calendario esperar.

A FOTOGRAFIA
------------
Esta e a parte barata com retorno directo: menos pessoas perdidas, menos
telefonemas ao motorista. Um "canto nordeste da praca, ao pe do quiosque
verde" explica-se em duas linhas e falha; uma fotografia nao falha.

Antes, por uma fotografia o operador tinha de ter onde alojar imagens e
saber o que e uma URL directa. Agora escolhe o ficheiro.
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
.lg { display: grid; gap: 1.2rem; }
@media (min-width: 1000px) {
  .lg { grid-template-columns: 20rem minmax(0, 1fr); align-items: start; }
}

.p-lista { display: grid; gap: .6rem; }
.p {
  display: block; width: 100%%; text-align: left; cursor: pointer;
  background: %(branco)s; border-radius: var(--r-g);
  box-shadow: var(--sombra);
  border-left: 4px solid %(risco)s; padding: .8rem .9rem;
  font: 400 .9rem/1.45 'Inter', system-ui, sans-serif; color: %(mudo)s;
}
.p:hover { border-color: %(mudo)s; }
.p[aria-pressed="true"] { border-left-color: %(cor)s; background: %(papel)s; }
.p:focus-visible { outline: 3px solid %(cor)s; outline-offset: 2px; }
.p b {
  display: block; font: 700 1rem/1.25 'Inter', system-ui, sans-serif;
  color: %(tinta)s; margin-bottom: .15rem;
}
/* A etiqueta estava a colar-se a morada: "Eyre Square, Galway1 TOUR".
   Um bloco proprio resolve, e e o que ela e — uma linha a parte. */
.p-usos {
  display: block; margin-top: .35rem;
  font: 600 .66rem/1 'Inter', system-ui, sans-serif;
  color: %(cor_escura)s;
}
.p-usos + .p-usos { margin-top: .2rem; }

/* ------------------------------------------------------- a fotografia */
.foto-cx { display: grid; gap: .7rem; }
.foto-pre {
  position: relative; border-radius: var(--r-m); overflow: hidden;
  background: %(papel)s; border: 1px solid %(risco)s;
  aspect-ratio: 4 / 3; display: flex; align-items: center;
  justify-content: center;
}
.foto-pre img { width: 100%%; height: 100%%; object-fit: cover; display: block; }
.foto-pre p {
  margin: 0; padding: 1rem; text-align: center;
  font: 400 .86rem/1.55 'Inter', system-ui, sans-serif; color: %(mudo)s;
}
.foto-bts { display: flex; flex-wrap: wrap; gap: .5rem; }
.foto-escolher {
  position: relative; overflow: hidden; display: inline-block;
}
.foto-escolher input[type=file] {
  position: absolute; inset: 0; opacity: 0; cursor: pointer; width: 100%%;
}

/* O mapa e para confirmar que o pino caiu onde devia, nao para navegar.
   Com 16/9 num ecra largo ficava com 500px de altura e empurrava as
   coordenadas — que sao o que a pessoa esta a editar — para fora do
   ecra. */
.mapa-mini {
  border: 1px solid %(risco)s; border-radius: var(--r-m); overflow: hidden;
  background: %(papel)s; aspect-ratio: 16 / 9; max-height: 15rem;
}
.mapa-mini iframe { width: 100%%; height: 100%%; border: 0; display: block; }
.coord { display: grid; gap: .8rem; }
@media (min-width: 560px) { .coord { grid-template-columns: 1fr 1fr; } }
""" % CORES


JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  var E = { operador: null, lugares: [], anuncios: [], escolhido: null,
            foto: null };

  // ------------------------------------------------------------ a lista
  function desenharLista() {
    var c = document.getElementById('p-lista');
    if (!E.lugares.length) {
      c.innerHTML = '<div class="vazio"><h3>No meeting points yet</h3>'
        + '<p>Only add one if guests come to you. A private day that '
        + 'collects at the hotel door needs none — that is the normal '
        + 'case and the better one.</p></div>';
      return;
    }
    c.innerHTML = E.lugares.map(function (p) {
      var usos = E.anuncios.filter(function (a) {
        return a.meeting_point_id === p.id;
      }).length;
      return '<button type="button" class="p" data-p="' + p.id + '"'
        + ' aria-pressed="' + (E.escolhido === p.id ? 'true' : 'false') + '">'
        + '<b>' + ewt.escapar(p.name) + '</b>'
        + ewt.escapar(p.address || 'No address yet')
        + (usos ? '<span class="p-usos">' + usos
                  + (usos === 1 ? ' tour' : ' tours') + '</span>' : '')
        + (p.photo_url ? '' : '<span class="p-usos">No photo</span>')
        + '</button>';
    }).join('');
  }

  function vazio() {
    return { id: null, name: '', address: '', lat: null, lng: null,
             instructions: '', photo_url: null };
  }

  function actual() {
    return E.lugares.filter(function (p) { return p.id === E.escolhido; })[0]
           || vazio();
  }

  // ------------------------------------------------------------ o form
  function espalhar() {
    var p = actual();
    document.getElementById('p-nome').value = p.name || '';
    document.getElementById('p-morada').value = p.address || '';
    document.getElementById('p-lat').value = p.lat == null ? '' : p.lat;
    document.getElementById('p-lng').value = p.lng == null ? '' : p.lng;
    document.getElementById('p-notas').value = p.instructions || '';
    E.foto = p.photo_url || null;
    desenharFoto();
    desenharMapa();
    desenharTours();
    document.getElementById('bt-apaga').hidden = !p.id;
    document.getElementById('p-titulo').textContent =
      p.id ? 'Edit this meeting point' : 'A new meeting point';
  }

  function desenharFoto() {
    var c = document.getElementById('foto-pre');
    c.innerHTML = E.foto
      ? '<img src="' + ewt.escapar(E.foto) + '" alt="The meeting point">'
      : '<p>No photograph yet. This is the cheapest thing on this page '
        + 'with a real return: a guest who can see the doorway does not '
        + 'ring the driver.</p>';
    document.getElementById('bt-tira-foto').hidden = !E.foto;
  }

  // Um mapa sem chave de API e sem seguir ninguem: o OpenStreetMap num
  // iframe. Nao e para navegar, e para o operador confirmar que o pino
  // caiu onde ele queria.
  function desenharMapa() {
    var c = document.getElementById('mapa');
    var lat = parseFloat(document.getElementById('p-lat').value);
    var lng = parseFloat(document.getElementById('p-lng').value);
    if (!isFinite(lat) || !isFinite(lng)) {
      c.innerHTML = '<p class="lado-nota" style="padding:1rem;margin:0">'
        + 'Paste coordinates below and the pin appears here, so you can '
        + 'check it landed where you meant.</p>';
      return;
    }
    var d = 0.004;
    c.innerHTML = '<iframe loading="lazy" title="Where the pin is"'
      + ' src="https://www.openstreetmap.org/export/embed.html?bbox='
      + (lng - d) + '%2C' + (lat - d) + '%2C' + (lng + d) + '%2C' + (lat + d)
      + '&layer=mapnik&marker=' + lat + '%2C' + lng + '"></iframe>';
  }

  function desenharTours() {
    var c = document.getElementById('p-tours');
    var p = actual();
    if (!p.id) {
      c.innerHTML = '<p class="lado-nota">Save it first, then pick which '
        + 'tours meet here.</p>';
      return;
    }
    if (!E.anuncios.length) {
      c.innerHTML = '<p class="lado-nota">You have no tours yet.</p>';
      return;
    }
    c.innerHTML = E.anuncios.map(function (a) {
      return '<label class="v-t"><input type="checkbox" data-usa="' + a.id
        + '"' + (a.meeting_point_id === p.id ? ' checked' : '') + '>'
        + '<span>' + ewt.escapar(a.titulo)
        + (a.meeting_point_id && a.meeting_point_id !== p.id
            ? ' <span>— meets somewhere else</span>' : '')
        + '</span></label>';
    }).join('');
  }

  // ---------------------------------------------------------- gravar
  function num(id) {
    var v = document.getElementById(id).value.trim();
    if (!v) return null;
    var n = Number(v);
    return isFinite(n) ? n : NaN;
  }

  async function gravar(ev) {
    ev.preventDefault();
    ewt.dizer('av-lg', '', '');
    var nome = document.getElementById('p-nome').value.trim();
    if (nome.length < 2) {
      ewt.dizer('av-lg', 'Give it a name you will recognise in a list.', 'mal');
      document.getElementById('p-nome').focus();
      return;
    }
    var lat = num('p-lat'), lng = num('p-lng');
    if (isNaN(lat) || isNaN(lng)) {
      ewt.dizer('av-lg', 'Those coordinates are not numbers. Copy them from '
        + 'a map as two decimals, like 53.349805 and -6.260310.', 'mal');
      return;
    }
    // Meia coordenada desenha um pino no oceano. A base tambem recusa,
    // mas dizer aqui poupa uma mensagem tecnica.
    if ((lat === null) !== (lng === null)) {
      ewt.dizer('av-lg', 'Latitude and longitude go together — fill both '
        + 'or neither.', 'mal');
      return;
    }

    var campos = {
      operator_id: E.operador.id,
      name: nome,
      address: document.getElementById('p-morada').value.trim() || null,
      lat: lat, lng: lng,
      instructions: document.getElementById('p-notas').value.trim() || null,
      photo_url: E.foto
    };

    var bt = document.getElementById('bt-grava');
    bt.disabled = true; bt.textContent = 'Saving…';
    var r = E.escolhido
      ? await ewt.sb.from('meeting_points').update(campos).eq('id', E.escolhido)
      : await ewt.sb.from('meeting_points').insert(campos).select('id').single();
    bt.disabled = false; bt.textContent = 'Save meeting point';

    if (r.error) { ewt.dizer('av-lg', ewt.legivel(r.error), 'mal'); return; }
    if (!E.escolhido && r.data) E.escolhido = r.data.id;
    await carregar();
    ewt.dizer('av-lg', 'Saved. It applies to every tour that meets here, '
      + 'immediately — no review.', 'bem');
  }

  async function apagar() {
    var p = actual();
    if (!p.id) return;
    var usos = E.anuncios.filter(function (a) {
      return a.meeting_point_id === p.id;
    }).length;
    if (!confirm(usos
        ? 'Delete "' + p.name + '"? ' + usos + (usos === 1 ? ' tour' : ' tours')
          + ' will go back to hotel pick-up.'
        : 'Delete "' + p.name + '"?')) return;
    var r = await ewt.sb.from('meeting_points').delete().eq('id', p.id);
    if (r.error) { ewt.dizer('av-lg', ewt.legivel(r.error), 'mal'); return; }
    E.escolhido = null;
    await carregar();
    ewt.dizer('av-lg', 'Deleted.', 'bem');
  }

  async function usar(listingId, usa) {
    var r = await ewt.sb.from('listings')
      .update({ meeting_point_id: usa ? E.escolhido : null })
      .eq('id', listingId);
    if (r.error) { ewt.dizer('av-lg', ewt.legivel(r.error), 'mal'); return; }
    await carregar();
  }

  // ----------------------------------------------------------- a foto
  async function escolheuFicheiro(ev) {
    var f = ev.target.files && ev.target.files[0];
    if (!f) return;
    ewt.dizer('av-foto', 'Uploading…', '');
    var r = await ewt.enviar_foto(f, E.operador.id);
    ev.target.value = '';
    if (r.erro) { ewt.dizer('av-foto', r.erro, 'mal'); return; }
    E.foto = r.url;
    desenharFoto();
    ewt.dizer('av-foto', 'Uploaded. Save the meeting point to keep it.', 'bem');
  }

  // ----------------------------------------------------------- arranque
  async function carregar() {
    var r = await ewt.sb.from('meeting_points')
      .select('*').order('name');
    if (r.error) { ewt.dizer('av-lg', ewt.legivel(r.error), 'mal'); return; }
    E.lugares = r.data || [];

    var a = await ewt.sb.from('listings')
      .select('id, slug, meeting_point_id').order('created_at');
    E.anuncios = (a.data || []).map(function (x) {
      return { id: x.id, titulo: x.slug, meeting_point_id: x.meeting_point_id };
    });
    if (E.anuncios.length) {
      var vv = await ewt.sb.from('listing_versions')
        .select('listing_id, version, payload')
        .in('listing_id', E.anuncios.map(function (x) { return x.id; }))
        .order('version', { ascending: false });
      var t = {};
      (vv.data || []).forEach(function (x) {
        if (!t[x.listing_id] && x.payload && x.payload.title) {
          t[x.listing_id] = x.payload.title;
        }
      });
      E.anuncios.forEach(function (x) { x.titulo = t[x.id] || x.titulo; });
    }

    // Quem chega a pagina ve o que ja tem, nao um formulario em branco.
    // O formulario vazio e um clique de distancia, no "Add a meeting
    // point"; o ponto que ele ja criou nao devia estar.
    var existe = E.lugares.some(function (p) { return p.id === E.escolhido; });
    if (!existe) {
      E.escolhido = E.lugares.length ? E.lugares[0].id : null;
    }
    desenharLista();
    espalhar();
  }

  (async function () {
    var p = await ewt.exigir_entrada();
    if (!p) return;
    document.getElementById('carrega').hidden = true;
    if (!p.operadores.length) {
      document.getElementById('conteudo').innerHTML =
        '<div class="vazio"><h3>Your account is not linked to a company</h3>'
        + '<a class="bt bt-s" href="/portal/">Back to the portal</a></div>';
      return;
    }
    E.operador = p.operadores[0];
    document.getElementById('lg').hidden = false;

    document.getElementById('f-lugar').addEventListener('submit', gravar);
    document.getElementById('bt-apaga').addEventListener('click', apagar);
    document.getElementById('bt-novo-lugar').addEventListener('click', function () {
      E.escolhido = null;
      desenharLista();
      espalhar();
      document.getElementById('p-nome').focus();
    });
    document.getElementById('p-lista').addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-p]');
      if (!b) return;
      E.escolhido = b.getAttribute('data-p');
      desenharLista();
      espalhar();
    });
    document.getElementById('p-tours').addEventListener('change', function (ev) {
      var c = ev.target.closest('[data-usa]');
      if (c) usar(c.getAttribute('data-usa'), c.checked);
    });
    document.getElementById('foto-ficheiro')
      .addEventListener('change', escolheuFicheiro);
    document.getElementById('bt-tira-foto').addEventListener('click', function () {
      E.foto = null;
      desenharFoto();
      ewt.dizer('av-foto', 'Removed here. Save to apply it.', '');
    });
    ['p-lat', 'p-lng'].forEach(function (id) {
      document.getElementById(id).addEventListener('change', desenharMapa);
    });

    await carregar();
  })();
})();
"""


def corpo():
    return '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">
    <p class="carrega" id="carrega">Loading&hellip;</p>

    <div id="lg" hidden>
      <div class="pt-cab">
        <h1>Meeting points</h1>
        <p>Only needed when guests come to you. A private day that
          collects at the hotel door needs none &mdash; that is the normal
          case, and the better one. When you do need one, a photograph of
          the doorway saves more phone calls than any paragraph.</p>
      </div>

      <p class="aviso" id="av-lg" role="status" hidden></p>

      <div class="lg">
        <div>
          <div class="cx">
            <p class="cx-t">Your meeting points</p>
            <div class="p-lista" id="p-lista"></div>
            <button type="button" class="rep-mais" id="bt-novo-lugar"
                    style="margin-top:.8rem">Add a meeting point</button>
          </div>

          <div class="cx">
            <p class="cx-t">Which tours meet here</p>
            <div class="v-tours" id="p-tours"></div>
            <p class="lado-nota">A tour with no meeting point ticked
              collects at the hotel.</p>
          </div>
        </div>

        <div class="cx">
          <p class="cx-t" id="p-titulo">A new meeting point</p>
          <form id="f-lugar" novalidate>
            <div class="campo">
              <label for="p-nome">What you call it</label>
              <input type="text" id="p-nome" maxlength="120"
                     placeholder="Molly Malone statue">
              <span class="ajuda">For your own list. The guest sees the
                address and the photograph.</span>
            </div>

            <div class="campo">
              <label for="p-morada">Address</label>
              <input type="text" id="p-morada" maxlength="250"
                     placeholder="Suffolk Street, Dublin 2">
            </div>

            <div class="campo">
              <span class="rotc">Where the pin falls</span>
              <div class="mapa-mini" id="mapa"></div>
            </div>

            <div class="coord">
              <div class="campo">
                <label for="p-lat">Latitude</label>
                <input type="text" id="p-lat" maxlength="20" inputmode="decimal"
                       placeholder="53.343800">
              </div>
              <div class="campo">
                <label for="p-lng">Longitude</label>
                <input type="text" id="p-lng" maxlength="20" inputmode="decimal"
                       placeholder="-6.259700">
              </div>
            </div>

            <div class="campo">
              <label for="p-notas">How to find it</label>
              <textarea id="p-notas" maxlength="600" rows="3"
                placeholder="On the corner by the kiosk, not the main door. Your driver holds a sign with your name."></textarea>
              <span class="ajuda">Write it for someone who has never been
                to the city and is already a little late.</span>
            </div>

            <div class="campo">
              <span class="rotc">Photograph of the spot</span>
              <div class="foto-cx">
                <div class="foto-pre" id="foto-pre"></div>
                <div class="foto-bts">
                  <span class="bt bt-s foto-escolher">
                    Choose a photograph
                    <input type="file" id="foto-ficheiro"
                           accept="image/jpeg,image/png,image/webp,image/avif"
                           aria-label="Choose a photograph of the meeting point">
                  </span>
                  <button type="button" class="bt bt-mal" id="bt-tira-foto"
                          hidden>Remove</button>
                </div>
                <p class="aviso" id="av-foto" role="status" hidden></p>
                <p class="ajuda">Take it standing where the guest will
                  stand, looking at where the car waits. Up to 5 MB.</p>
              </div>
            </div>

            <div class="acoes" style="margin-top:1.2rem">
              <button type="submit" class="bt bt-p" id="bt-grava">Save
                meeting point</button>
              <button type="button" class="bt bt-mal" id="bt-apaga"
                      hidden>Delete</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</main>'''


def gerar():
    pagina.verificar_contraste()
    html = portal_base.envolver(
        titulo='Meeting points — Exclusive World Tours',
        corpo=corpo(), js=JS, etiqueta='Operator portal',
        nav=NAV, atual='/portal/places/', css_extra=CSS)
    pagina.escrever(html, 'portal/places/index.html')


if __name__ == '__main__':
    gerar()
