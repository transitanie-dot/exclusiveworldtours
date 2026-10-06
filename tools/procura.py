#!/usr/bin/env python3
"""
A barra de procura, no sistema da GetYourGuide.

O que eles fazem, e o que daqui se copia
----------------------------------------
A GetYourGuide corre a procura em OpenSearch. O que importa nao e o
motor — e o comportamento, e esse replica-se inteiro do lado do cliente
com 45 KB de indice:

1. **Uma caixa so.** Nao ha um campo para a cidade e outro para a data.
   Escreve-se o que se quiser e o sistema e que percebe se aquilo e um
   sitio ou uma coisa para fazer.

2. **Sugestoes agrupadas por tipo**, com cabecalho — destinos primeiro,
   tours a seguir — e um numero pequeno de lugares. Eles falam em sete;
   aqui sao sete tambem, porque uma lista que enche o ecra deixa de ser
   uma sugestao e passa a ser um catalogo.

3. **Tolerancia a gralhas, mas sempre em ultimo.** Eles poem o fuzzy
   match com um peso de 0.01 — ou seja, so aparece quando nao ha nada
   exato. Aqui e igual: quem escreve certo nunca ve um resultado
   aproximado a frente do seu.

4. **Apelidos indexados.** Eles geraram aliases para as categorias;
   aqui cada cidade leva os codigos IATA e os nomes dos aeroportos, por
   isso "LHR", "Heathrow" e "Gatwick" chegam todos a Londres.

5. **Popularidade limitada.** O tier do aeroporto desempata resultados
   igualmente bons e nunca passa a frente da relevancia do texto — e
   exatamente a ressalva que eles fazem, para a lista continuar
   intuitiva em vez de ser mandada pelo negocio.

6. **Com a caixa vazia, mostra destinos populares** em vez de nada.

O que nao se copia: a procura por linguagem natural ("explore Paris"),
que do lado deles passa por um modelo. Isso nao se faz com um ficheiro
estatico e nao vou fingir que faz.

Fica a funcionar sem JavaScript: e um <input> dentro de um <form> que
vai para /tours/. Sem JS nao ha sugestoes, mas escrever e carregar em
procurar continua a funcionar.
"""

def html(cidades=None):
    """A caixa de procura. `cidades` sao as cidades de partida reais; com
    elas, o campo passa a VIAJAR por elas em vez de ficar parado numa
    pergunta. Sem elas, fica a pergunta e mais nada — nunca se inventa
    uma cidade onde nao ha tours."""
    attr = ''
    if cidades:
        attr = ' data-cidades="%s"' % e(', '.join(cidades))
    return HTML.replace('placeholder="Where are you going?"',
                        'placeholder="Where are you going?"' + attr)


def e(t):
    return (str(t).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


HTML = '''<div class="pc" data-pc>
  <div class="pc-caixa">
    <svg class="pc-lupa" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="11" cy="11" r="7"/><path d="M16.5 16.5 L21 21"/>
    </svg>
    <label class="pc-oculto" for="pc-input">Where are you going?</label>
    <input id="pc-input" name="q" type="text" autocomplete="off"
           spellcheck="false" placeholder="Where are you going?"
           role="combobox" aria-expanded="false" aria-controls="pc-lista"
           aria-autocomplete="list" aria-describedby="pc-ajuda">
    <button class="botao pc-botao" type="submit">Search</button>
  </div>
  <div id="pc-lista" class="pc-lista" role="listbox" hidden
       aria-label="Suggestions"></div>
  <p id="pc-ajuda" class="pc-oculto">Type a city, an airport code or a tour.
    Use the up and down arrows to choose a suggestion.</p>
  <p class="pc-oculto" role="status" aria-live="polite" data-pc-aviso></p>
</div>'''


CSS = '''
.pc{position:relative;width:100%%}
.pc-caixa{display:flex;align-items:center;gap:12px;background:var(--branco);
  border-radius:var(--r-c);padding:8px 8px 8px 24px;
  box-shadow:0 18px 46px -22px rgba(11,43,42,.55)}
.pc-lupa{width:21px;height:21px;flex:none;fill:none;stroke:var(--mudo);
  stroke-width:2;stroke-linecap:round}
.pc-caixa input{flex:1;min-width:0;border:0;padding:16px 0;font:inherit;
  font-size:17px;color:var(--tinta);background:transparent}
.pc-caixa input::placeholder{color:var(--mudo)}
.pc-caixa input:focus{outline:0}
.pc-caixa:focus-within{box-shadow:0 0 0 3px var(--cor),
  0 18px 46px -22px rgba(11,43,42,.55)}
.pc-botao{min-height:52px}
.pc-oculto{position:absolute;width:1px;height:1px;overflow:hidden;
  clip:rect(0 0 0 0);clip-path:inset(50%%);white-space:nowrap;margin:0}

.pc-lista{position:absolute;z-index:50;left:0;right:0;top:calc(100%% + 10px);
  padding:10px;background:var(--branco);
  border-radius:var(--r-g);max-height:400px;overflow:auto;
  box-shadow:0 24px 54px -26px rgba(11,43,42,.5);text-align:left}
.pc-lista[hidden]{display:none}
.pc-grupo{font-size:12.5px;color:var(--mudo);font-weight:600;
  padding:12px 12px 6px}
.pc-grupo:first-child{padding-top:6px}
.pc-op{display:flex;align-items:center;gap:12px;padding:10px 12px;
  border-radius:var(--r-m);cursor:pointer;color:var(--texto);font-size:15px}
.pc-op[aria-selected="true"],.pc-op:hover{background:var(--papel)}
.pc-icone{width:34px;height:34px;flex:none;border-radius:var(--r-p);
  background:var(--papel);display:grid;place-items:center;color:var(--tinta)}
.pc-op[aria-selected="true"] .pc-icone{background:var(--branco)}
.pc-icone svg{width:17px;height:17px;fill:none;stroke:currentColor;
  stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.pc-txt{min-width:0;flex:1}
.pc-t1{display:block;color:var(--tinta);font-weight:600;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pc-t2{display:block;color:var(--mudo);font-size:13px;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pc-n{flex:none;font-size:12px;font-weight:600;color:var(--branco);
  background:var(--cor-escura);border-radius:999px;padding:3px 10px}
.pc-nada{flex:none;font-size:12.5px;color:var(--mudo)}
.pc-vazio{padding:16px 12px 18px;color:var(--mudo);font-size:14.5px}
.pc-vazio b{color:var(--tinta)}
/* NO TELEMOVEL A PASTILHA DESFAZ-SE
   O campo e o botao empilham — num ecra de 390 nao cabem lado a lado
   sem o campo ficar inutilizavel. Mas o raio de pastilha fica para uma
   caixa de UMA linha: numa caixa de duas, os 999px cortam os cantos de
   cima e de baixo e o que aparece e uma mancha branca com um botao a
   boiar la dentro. Era exactamente o que se via a 390px.
   Empilhado, a forma e um rectangulo redondo — a mesma dos cartoes. */
@media (max-width:700px){
  /* O contentor DESAPARECE: empilhado, o campo e o botao ja tem fundo
     proprio, e a caixa branca por tras deles so acrescentava uma
     moldura de 8px a toda a volta — que e o que fazia a barra parecer
     uma mancha em vez de dois controlos. */
  .pc-caixa{flex-wrap:wrap;padding:0;gap:10px;border-radius:0;
    background:transparent;box-shadow:none}
  .pc-caixa:focus-within{box-shadow:none}
  .pc-caixa input{flex:1 1 100%%;padding:15px 18px;border-radius:var(--r-g);
    background:var(--branco);box-shadow:0 10px 26px -16px rgba(11,43,42,.5)}
  .pc-caixa input:focus-visible{outline:3px solid var(--cor);outline-offset:2px}
  .pc-lupa{display:none}
  /* O BOTAO TROCA DE COR, E NAO E CAPRICHO
     Em ecra largo o botao e escuro dentro de uma caixa branca e le-se
     muito bem. Sem a caixa branca por tras, esse mesmo escuro fica
     sobre o fundo escuro do heroi — e o botao desaparece. Vi-o num
     screenshot: ficava "Search" em texto branco a flutuar.
     Passa ao ambar ESCURO com branco por cima: 5.31:1, com folga.
     O ambar normal com a tinta por cima dava 4.52 — tecnicamente passa
     o minimo de 4.5, e por 0.02 nao se poe nada em producao: o axe
     recusou-o, e tinha razao. Uma cor a dois centesimos da norma e uma
     cor que reprova mal alguem lhe mexa um tom.
     52px de altura: o minimo decente para um alvo de dedo e 44. */
  .pc-botao{flex:1 1 100%%;min-height:52px;border-radius:var(--r-g);
    background:var(--cor-escura);color:var(--branco)}
  .pc-botao:hover{filter:brightness(1.1)}
}
'''


VIAJAR = r'''
(function () {
  // ----------------------------------------------------- o campo viaja
  //
  // O site diz "19 departure cities" numa linha de numeros. Isto mostra
  // as 19 — e mostrar vale mais do que contar. Nao e decoracao: alguem
  // que chega sem saber o que ha aqui fica a saber em cinco segundos.
  //
  // As cidades vem do atributo, que o gerador preenche a partir dos
  // tours que existem mesmo. Sem o atributo nao ha viagem: nunca se
  // inventa uma cidade onde nao ha tours.
  var campo = document.getElementById('pc-input');
  if (!campo) return;
  var lista = (campo.getAttribute('data-cidades') || '')
                .split(',').map(function (x) { return x.trim(); })
                .filter(Boolean);
  if (lista.length < 3) return;

  // Quem pediu menos movimento fica com a pergunta parada. Nao e uma
  // gentileza: para algumas pessoas o texto a mudar sozinho torna o
  // campo impossivel de usar.
  var q = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (q.matches) return;

  var PERGUNTA = 'Where are you going?';
  var i = -1, t = null, parado = false;

  function parar() {
    parado = true;
    if (t) { clearTimeout(t); t = null; }
    campo.placeholder = PERGUNTA;
  }

  // Assim que a pessoa toca no campo, a viagem acaba para sempre. Um
  // placeholder que muda enquanto se escreve e um campo que pisca por
  // baixo do que se esta a fazer.
  campo.addEventListener('focus', parar, { once: true });
  campo.addEventListener('input', parar, { once: true });

  function passo() {
    if (parado) return;
    i = (i + 1) % (lista.length + 1);
    // De volta a pergunta de vez em quando: sem isso, quem chega a meio
    // ve um nome de cidade num campo vazio e nao percebe que e um campo
    // de procura.
    campo.placeholder = i === 0 ? PERGUNTA : lista[i - 1];
    t = setTimeout(passo, i === 0 ? 2600 : 1500);
  }

  // Parada enquanto o separador esta escondido: um temporizador a correr
  // numa janela que ninguem ve gasta bateria e nao mostra nada.
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) { if (t) { clearTimeout(t); t = null; } }
    else if (!parado && !t) { t = setTimeout(passo, 900); }
  });

  t = setTimeout(passo, 2200);
})();
'''


JS = r'''
(function () {
  var raiz = document.querySelector('[data-pc]');
  if (!raiz) return;
  var campo = raiz.querySelector('input');
  var lista = raiz.querySelector('.pc-lista');
  var aviso = raiz.querySelector('[data-pc-aviso]');
  var form = raiz.closest('form');
  var dados = null, aCarregar = null, itens = [], activo = -1;
  var LUGARES = 7;

  var ICONE_D = '<svg viewBox="0 0 24 24"><path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11z"/><circle cx="12" cy="10" r="2.6"/></svg>';
  var ICONE_T = '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3.2 12h17.6M12 3.2c4.5 5 4.5 12.6 0 17.6-4.5-5-4.5-12.6 0-17.6"/></svg>';

  function chave(s) {
    return s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  }

  function carregar() {
    if (dados) return Promise.resolve();
    if (aCarregar) return aCarregar;
    aCarregar = fetch('/assets/procura.json')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        d.cidades.forEach(function (c) {
          c.k = chave(c.n);
          c.kp = chave(c.p);
          c.ka = (c.a || []).map(chave);
        });
        d.tours.forEach(function (t) {
          t.k = chave(t.titulo);
          t.kc = chave(t.cidade);
        });
        dados = d;
      })
      .catch(function () { dados = null; aCarregar = null; });
    return aCarregar;
  }

  // distancia de edicao com tecto: assim que passa do limite, desiste.
  // So serve para apanhar gralhas; nunca para inventar resultados.
  function perto(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    var ant = [], act = [], i, j;
    for (j = 0; j <= b.length; j++) ant[j] = j;
    for (i = 1; i <= a.length; i++) {
      act[0] = i;
      var melhor = act[0];
      for (j = 1; j <= b.length; j++) {
        act[j] = Math.min(ant[j] + 1, act[j - 1] + 1,
                          ant[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (act[j] < melhor) melhor = act[j];
      }
      if (melhor > max) return max + 1;
      ant = act.slice();
    }
    return ant[b.length];
  }

  // Quanto mais baixo, melhor. O texto manda; a popularidade so desempata.
  // O fuzzy comeca nos 400 de propósito: nunca passa a frente de nada
  // que tenha sido escrito como deve ser.
  function pontuar(k, campos, q) {
    var melhor = 1e9;
    for (var i = 0; i < campos.length; i++) {
      var c = campos[i], pen = i * 2;        // o nome vale mais que o pais
      if (!c) continue;
      if (c === q) melhor = Math.min(melhor, 0 + pen);
      else if (c.indexOf(q) === 0) melhor = Math.min(melhor, 10 + pen);
      else if (c.indexOf(' ' + q) > -1) melhor = Math.min(melhor, 20 + pen);
      else if (c.indexOf(q) > -1) melhor = Math.min(melhor, 40 + pen);
    }
    if (melhor < 1e9) return melhor;
    if (q.length >= 4) {
      var max = q.length >= 7 ? 2 : 1;
      for (var j = 0; j < campos.length; j++) {
        var d = perto(q, (campos[j] || '').slice(0, q.length + max), max);
        if (d <= max) return 400 + d * 10 + j * 2;
      }
    }
    return 1e9;
  }

  function procurar(q) {
    var k = chave(q.trim());
    if (!dados || k.length < 2) return [];
    var res = [];
    dados.cidades.forEach(function (c) {
      var p = pontuar(k, [c.k, c.kp].concat(c.ka), k);
      if (p >= 1e9) return;
      // popularidade limitada: no maximo tira 4 pontos, nunca inverte
      // uma diferenca de relevancia de texto
      res.push({ tipo: 'd', p: p + c.t - (c.x ? 4 : 0), d: c });
    });
    dados.tours.forEach(function (t) {
      var p = pontuar(k, [t.k, t.kc], k);
      if (p >= 1e9) return;
      res.push({ tipo: 't', p: p + 1, d: t });
    });
    res.sort(function (a, b) { return a.p - b.p; });

    // os sete lugares: ate cinco destinos, o resto tours
    var ds = res.filter(function (r) { return r.tipo === 'd'; }).slice(0, 5);
    var ts = res.filter(function (r) { return r.tipo === 't'; })
                .slice(0, LUGARES - ds.length);
    return ds.concat(ts).sort(function (a, b) { return a.p - b.p; });
  }

  function populares() {
    if (!dados) return [];
    var com = dados.cidades.filter(function (c) { return c.x; });
    com.sort(function (a, b) { return b.x - a.x || a.t - b.t; });
    return com.slice(0, LUGARES).map(function (c) {
      return { tipo: 'd', d: c };
    });
  }

  function linha(r, i) {
    var el = document.createElement('div');
    el.className = 'pc-op';
    el.id = 'pc-op-' + i;
    el.setAttribute('role', 'option');
    el.setAttribute('aria-selected', 'false');
    var ic = document.createElement('span');
    ic.className = 'pc-icone';
    ic.innerHTML = r.tipo === 'd' ? ICONE_D : ICONE_T;
    var tx = document.createElement('span');
    tx.className = 'pc-txt';
    var t1 = document.createElement('span');
    t1.className = 'pc-t1';
    var t2 = document.createElement('span');
    t2.className = 'pc-t2';
    if (r.tipo === 'd') {
      t1.textContent = r.d.n;
      t2.textContent = r.d.p + (r.d.a && r.d.a.length
        ? ' · ' + r.d.a.filter(function (x) { return x.length === 3; })
            .join(' ') : '');
    } else {
      t1.textContent = r.d.titulo;
      t2.textContent = r.d.cidade + ', ' + r.d.pais + ' · ' + r.d.h
        + ' · from €' + r.d.preco;
    }
    tx.appendChild(t1); tx.appendChild(t2);
    el.appendChild(ic); el.appendChild(tx);
    // a direita so leva coisa nos destinos: nos tours repetia o
    // cabecalho do grupo, que ja diz que aquilo e um tour
    if (r.tipo === 'd') {
      var fim = document.createElement('span');
      if (r.d.x) {
        fim.className = 'pc-n';
        fim.textContent = r.d.x + (r.d.x === 1 ? ' tour' : ' tours');
      } else {
        fim.className = 'pc-nada';
        fim.textContent = 'no tours yet';
      }
      el.appendChild(fim);
    }
    el.addEventListener('mousedown', function (ev) {
      ev.preventDefault(); escolher(i);
    });
    return el;
  }

  function desenhar(res, q, titulo) {
    lista.innerHTML = '';
    itens = res;
    activo = -1;
    if (!res.length) {
      if (!q) { fechar(); return; }
      var v = document.createElement('div');
      v.className = 'pc-vazio';
      v.innerHTML = dados
        ? 'Nothing matches <b></b> yet. Try a city or an airport code.'
        : 'Could not load the suggestions. You can still press Search.';
      if (dados) v.querySelector('b').textContent = q;
      lista.appendChild(v);
      abrir();
      dizer('No suggestions.');
      return;
    }
    var grupo = null, n = 0;
    res.forEach(function (r) {
      var g = r.tipo === 'd' ? (titulo || 'Destinations') : 'Tours';
      if (g !== grupo) {
        grupo = g;
        var h = document.createElement('div');
        h.className = 'pc-grupo';
        h.textContent = g;
        h.setAttribute('role', 'presentation');
        lista.appendChild(h);
      }
      lista.appendChild(linha(r, n++));
    });
    abrir();
    dizer(res.length + (res.length === 1 ? ' suggestion' : ' suggestions')
          + ' available.');
  }

  function dizer(t) { if (aviso) aviso.textContent = t; }
  function abrir() { lista.hidden = false;
    campo.setAttribute('aria-expanded', 'true'); }
  function fechar() {
    lista.hidden = true;
    campo.setAttribute('aria-expanded', 'false');
    campo.removeAttribute('aria-activedescendant');
    activo = -1;
  }

  function marcar(i) {
    var os = lista.querySelectorAll('.pc-op');
    for (var j = 0; j < os.length; j++) {
      os[j].setAttribute('aria-selected', j === i ? 'true' : 'false');
    }
    if (i >= 0 && os[i]) {
      campo.setAttribute('aria-activedescendant', os[i].id);
      os[i].scrollIntoView({ block: 'nearest' });
    } else {
      campo.removeAttribute('aria-activedescendant');
    }
    activo = i;
  }

  function escolher(i) {
    var r = itens[i];
    if (!r) return;
    if (r.tipo === 't') { window.location.href = '/tours/' + r.d.slug + '/'; return; }
    campo.value = r.d.n;
    fechar();
    dizer(r.d.n + ' selected.');
    if (form) form.submit();
  }

  var espera;
  campo.addEventListener('input', function () {
    var q = campo.value;
    clearTimeout(espera);
    espera = setTimeout(function () {
      carregar().then(function () {
        if (q.trim().length < 2) {
          desenhar(populares(), '', 'Popular destinations');
        } else {
          desenhar(procurar(q), q.trim());
        }
      });
    }, 90);
  });

  campo.addEventListener('focus', function () {
    carregar().then(function () {
      if (campo.value.trim().length < 2) {
        desenhar(populares(), '', 'Popular destinations');
      }
    });
  });

  campo.addEventListener('keydown', function (ev) {
    if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') {
      if (lista.hidden) {
        carregar().then(function () {
          desenhar(campo.value.trim().length < 2
            ? populares() : procurar(campo.value), campo.value.trim(),
            campo.value.trim().length < 2 ? 'Popular destinations' : null);
        });
        return;
      }
      ev.preventDefault();
      if (ev.key === 'ArrowDown') {
        marcar(activo + 1 >= itens.length ? 0 : activo + 1);
      } else {
        marcar(activo - 1 < 0 ? itens.length - 1 : activo - 1);
      }
    } else if (ev.key === 'Enter') {
      if (activo >= 0) { ev.preventDefault(); escolher(activo); }
    } else if (ev.key === 'Escape') {
      fechar();
    }
  });

  document.addEventListener('click', function (ev) {
    if (!raiz.contains(ev.target)) fechar();
  });
})();
'''
