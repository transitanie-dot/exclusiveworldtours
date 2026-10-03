#!/usr/bin/env python3
"""
A pagina de resultados de pesquisa.

Escreve-se o que se quiser na barra, carrega-se em procurar, e chega-se
aqui. **Sempre.** Mesmo quando nao ha nada: uma procura que nao leva a
lado nenhum e uma procura avariada, e quem escreveu "Tokyo" merece que
lhe digam que ainda nao ha, em vez de ficar a olhar para uma caixa.

O mesmo ficheiro serve duas moradas:

  /tours/     sem pergunta, e o catalogo: os 36 tours todos.
  /search/    com ?q=..., e a pagina de resultados.

Sao a mesma pagina de proposito. E assim que a GetYourGuide faz — a
pagina de resultados e o catalogo com um filtro posto — e evita ter duas
paginas parecidas a divergir uma da outra.

A filtragem e toda no browser, sobre o mesmo /assets/procura.json que a
barra ja carregou. Com 36 tours, isto e instantaneo e nao precisa de
servidor nenhum.

Sem JavaScript continua a ver-se o catalogo inteiro, que e a coisa util
a mostrar quando nao se consegue filtrar.

    python3 tools/resultados.py      # escreve tours/ e search/
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pagina  # noqa: E402
import procura  # noqa: E402
from pagina import (CORES, cabecalho, cartao_tour, carregar, e, envolver,  # noqa: E402
                    escrever, por_pais, rodape)

CSS = '''<style>
.capa{background:var(--papel);border-bottom:1px solid var(--risco);
  padding:40px 0 34px}
.capa h1{font-size:clamp(1.8rem, 1.3rem + 1.8vw, 2.6rem);margin:0 0 6px}
.capa .sub{color:var(--mudo);margin:0 0 26px}
.capa .procura{max-width:680px}

.corpo{padding:34px 0 80px}
.barra-f{display:flex;gap:10px;flex-wrap:wrap;align-items:center;
  margin:0 0 26px}
.filtro{position:relative}
.filtro select{appearance:none;font:inherit;font-size:14.5px;
  color:var(--tinta);background:var(--branco);border:1px solid var(--risco);
  border-radius:999px;padding:9px 34px 9px 16px;cursor:pointer}
.filtro::after{content:'';position:absolute;right:14px;top:50%;
  width:7px;height:7px;border-right:2px solid var(--mudo);
  border-bottom:2px solid var(--mudo);transform:translateY(-70%) rotate(45deg);
  pointer-events:none}
.limpar{border:0;background:transparent;font:inherit;font-size:14.5px;
  color:var(--cor-escura);font-weight:600;cursor:pointer;padding:9px 4px}
.limpar[hidden]{display:none}
.conta{margin-left:auto;color:var(--mudo);font-size:14.5px}

.nada{border:1px solid var(--risco);border-radius:var(--raio);
  padding:36px 28px;margin:0 0 34px;background:var(--papel)}
.nada h2{font-size:1.35rem;margin:0 0 8px}
.nada p{margin:0;color:var(--mudo);max-width:56ch}
.nada .destino{display:flex;align-items:center;gap:13px;margin-top:20px;
  padding:14px 16px;background:var(--branco);border:1px solid var(--risco);
  border-radius:11px}
.nada .destino b{color:var(--tinta)}
.nada .destino span{color:var(--mudo);font-size:14px}
.sugestao{margin:30px 0 14px;font-size:1.1rem}
</style>'''


JS = r'''
(function () {
  var grelha = document.querySelector('[data-grelha]');
  if (!grelha) return;
  var cartoes = [].slice.call(grelha.children);
  var conta = document.querySelector('[data-conta]');
  var nada = document.querySelector('[data-nada]');
  var sugestao = document.querySelector('[data-sugestao]');
  var limpar = document.querySelector('[data-limpar]');
  var titulo = document.querySelector('[data-titulo]');
  var sub = document.querySelector('[data-sub]');
  var fPais = document.querySelector('[data-f="country"]');
  var fDur = document.querySelector('[data-f="hours"]');
  var fGrupo = document.querySelector('[data-f="people"]');
  var campo = document.querySelector('#pc-input');
  var dados = null;

  function chave(s) {
    return (s || '').normalize('NFD').replace(/[̀-ͯ]/g, '')
      .toLowerCase().trim();
  }

  function params() {
    return new URLSearchParams(window.location.search);
  }

  function aplicar() {
    var p = params();
    var q = chave(p.get('q') || p.get('city') || '');
    var pais = p.get('country') || '';
    var dur = p.get('hours') || '';
    var pes = parseInt(p.get('people') || '0', 10) || 0;

    var n = 0;
    cartoes.forEach(function (c) {
      var ok = true;
      if (q) {
        ok = chave(c.dataset.busca).indexOf(q) > -1;
      }
      if (ok && pais) ok = c.dataset.country === pais;
      if (ok && dur) {
        var h = parseFloat(c.dataset.hours);
        ok = dur === 'short' ? h <= 5 : dur === 'half' ? (h > 5 && h <= 9) : h > 9;
      }
      if (ok && pes) ok = parseInt(c.dataset.max, 10) >= pes;
      c.hidden = !ok;
      if (ok) n++;
    });

    conta.textContent = n + (n === 1 ? ' tour' : ' tours');
    if (limpar) limpar.hidden = !(q || pais || dur || pes);
    if (fPais) fPais.value = pais;
    if (fDur) fDur.value = dur;
    if (fGrupo) fGrupo.value = pes ? String(pes) : '';
    if (campo && (p.get('q') || p.get('city'))) {
      campo.value = p.get('q') || p.get('city');
    }

    var termo = p.get('q') || p.get('city') || '';
    if (titulo) {
      titulo.textContent = termo ? 'Search: ' + termo : 'All tours';
    }
    if (sub) {
      sub.textContent = termo
        ? n + (n === 1 ? ' tour matches' : ' tours match') + ' what you typed.'
        : 'Every private day we run, in one place.';
    }
    document.title = (termo ? 'Search: ' + termo : 'All tours')
      + ' — Exclusive World Tours';

    mostrarVazio(n, termo);
  }

  function mostrarVazio(n, termo) {
    if (!nada) return;
    if (n > 0 || !termo) { nada.hidden = true;
      if (sugestao) sugestao.hidden = true; return; }
    nada.hidden = false;
    // sem resultados, mostram-se todos: o titulo diz "everything we do
    // run" e tem de haver mesmo alguma coisa por baixo dele
    cartoes.forEach(function (c) { c.hidden = false; });
    var h = nada.querySelector('h2');
    var p = nada.querySelector('p');
    var d = nada.querySelector('[data-destino]');
    h.textContent = 'No tours for “' + termo + '” yet.';
    p.textContent = 'We run private days in six countries so far. '
      + 'Here is everything we do have.';
    d.hidden = true;
    // se o sitio existe na lista de destinos, diz-se que existe e que
    // ainda nao ha tours la — e mais honesto do que um vazio sem nome
    carregar().then(function () {
      if (!dados) return;
      var k = chave(termo);
      var c = null;
      for (var i = 0; i < dados.cidades.length; i++) {
        var x = dados.cidades[i];
        if (chave(x.n) === k || (x.a || []).some(function (a) {
          return chave(a) === k;
        })) { c = x; break; }
      }
      if (!c) return;
      d.hidden = false;
      d.querySelector('b').textContent = c.n + ', ' + c.p;
      d.querySelector('span').textContent =
        'We know this one — there is just no tour here yet.';
    });
    if (sugestao) sugestao.hidden = false;
  }

  function carregar() {
    if (dados) return Promise.resolve();
    return fetch('/assets/procura.json')
      .then(function (r) { return r.json(); })
      .then(function (d) { dados = d; })
      .catch(function () { dados = null; });
  }

  function mudar(chaveP, valor) {
    var p = params();
    if (valor) p.set(chaveP, valor); else p.delete(chaveP);
    var u = window.location.pathname + (p.toString() ? '?' + p : '');
    history.replaceState(null, '', u);
    aplicar();
  }

  [['country', fPais], ['hours', fDur], ['people', fGrupo]].forEach(function (x) {
    if (x[1]) x[1].addEventListener('change', function () {
      mudar(x[0], x[1].value);
    });
  });
  if (limpar) limpar.addEventListener('click', function () {
    history.replaceState(null, '', window.location.pathname);
    if (campo) campo.value = '';
    aplicar();
  });

  aplicar();
})();
'''


def main():
    tours = carregar()
    paises = por_pais(tours)

    cartoes = []
    for t in sorted(tours, key=lambda x: (x['countryName'], x['city'], x['title'])):
        # tudo o que serve para filtrar vai no proprio cartao, em
        # data-*: assim o filtro nao precisa de voltar a buscar nada
        horas = t['_h'].replace('h', '').split()
        try:
            h = float(horas[0]) + (float(horas[1].replace('m', '')) / 60
                                   if len(horas) > 1 else 0)
        except (ValueError, IndexError):
            h = 0
        busca = ' '.join([t['title'], t['city'], t['countryName'],
                          t.get('ticketTo') or '', t.get('kicker') or ''])
        html = cartao_tour(t)
        html = html.replace('<a class="tour"',
                            '<a class="tour" data-country="%s" data-hours="%.2f" '
                            'data-max="%d" data-busca="%s"'
                            % (e(t['country']), h, t['_max'], e(busca)), 1)
        cartoes.append(html)

    corpo = '''
%(cabecalho)s
<main id="principal">

<section class="capa">
  <div class="folha">
    <h1 data-titulo>All tours</h1>
    <p class="sub" data-sub>Every private day we run, in one place.</p>
    <form class="procura" action="/search/" method="get" role="search">
      %(procura)s
    </form>
  </div>
</section>

<section class="corpo folha">
  <div class="barra-f">
    <span class="filtro">
      <label class="pc-oculto" for="f-country">Country</label>
      <select id="f-country" data-f="country">
        <option value="">All countries</option>
        %(opc_pais)s
      </select>
    </span>
    <span class="filtro">
      <label class="pc-oculto" for="f-hours">Length</label>
      <select id="f-hours" data-f="hours">
        <option value="">Any length</option>
        <option value="short">Up to 5 hours</option>
        <option value="half">5 to 9 hours</option>
        <option value="long">More than 9 hours</option>
      </select>
    </span>
    <span class="filtro">
      <label class="pc-oculto" for="f-people">Group size</label>
      <select id="f-people" data-f="people">
        <option value="">Any group size</option>
        %(opc_grupo)s
      </select>
    </span>
    <button type="button" class="limpar" data-limpar hidden>Clear filters</button>
    <span class="conta" data-conta>%(n)d tours</span>
  </div>

  <div class="nada" data-nada hidden>
    <h2></h2>
    <p></p>
    <div class="destino" data-destino hidden><b></b><span></span></div>
  </div>

  <h2 class="sugestao" data-sugestao hidden>Everything we do run</h2>

  <div class="tours" data-grelha>%(cartoes)s</div>
</section>

</main>
%(rodape)s''' % {
        'cabecalho': cabecalho(),
        'procura': procura.HTML,
        'opc_pais': '\n'.join('<option value="%s">%s</option>'
                              % (e(p['cod']), e(p['nome'])) for p in paises),
        'opc_grupo': '\n'.join('<option value="%d">%d or more</option>' % (n, n)
                               for n in (2, 4, 6, 8, 12, 16)),
        'n': len(tours),
        'cartoes': '\n'.join(cartoes),
        'rodape': rodape(paises),
    }

    html = envolver(
        'All tours — Exclusive World Tours',
        'Search every private day tour we run: %d tours in %d countries, '
        'priced for the whole group.' % (len(tours), len(paises)),
        CSS, corpo, js=procura.JS + JS)

    # a mesma pagina nas duas moradas: /tours/ e o catalogo, /search/ e a
    # pagina de resultados. O conteudo e o mesmo; quem muda e a pergunta
    # que vem no endereco.
    escrever(html, 'tours/index.html')
    escrever(html, 'search/index.html')
    print('%d tours, %d paises' % (len(tours), len(paises)))


if __name__ == '__main__':
    main()
