# -*- coding: utf-8 -*-
"""As epocas: a regra, antes das excepcoes.

Porque e que esta pagina existe
-------------------------------
A queixa foi "o calendario e super confuso de mexer". Era, e o problema
nao estava no calendario: estava em ele ser o UNICO sitio onde se podia
dizer quando um tour acontece.

Um operador que trabalha de segunda a sexta de Junho a Setembro tinha de
abrir dia a dia — oitenta e tal toques — e repetir isso todos os anos.
Pior: um mes que ele se esquecesse de pintar aparecia fechado no site sem
ninguem dar por nada, e um tour que deixa de ter disponibilidade nao da
erro nenhum. Desaparece em silencio.

A Viator resolve isto ao contrario, e e o modelo certo: **aberto por
regra, fechado por excepcao**. Diz-se a regra uma vez — estes meses,
estes dias da semana, estas horas de partida — e o calendario passa a
servir so para o que foge a regra: o dia do casamento da filha, a semana
da revisao da carrinha.

O que esta pagina mostra, por esta ordem
----------------------------------------
1. **A fita do ano.** Doze meses como uma fita continua, cada um com a
   altura preenchida a dizer que parte dele esta aberta. E a unica
   coisa nesta pagina desenhada para ser vista de longe, e responde a
   pergunta que importa antes de todas as outras: *tenho algum buraco?*
   Um mes vazio a meio de uma fita cheia salta a vista; na grelha do
   calendario era preciso navegar ate la para o descobrir.

2. **As epocas, como frases.** "Open Mon to Fri, 1 Jun to 30 Sep,
   leaving at 09:00 and 14:00." Uma linha de tabela com seis colunas diz
   o mesmo e obriga a ler o cabecalho para saber o que e cada coluna.

3. **Acrescentar uma epoca**, que e um formulario curto.

A epoca sem data de fim
-----------------------
Uma epoca pode nao ter data de fim, e e esse o valor por omissao. Nao
significa "para sempre" — significa que rola 400 dias para a frente, que
e o limite do calendario. E a defesa contra o anuncio que se esgota em
silencio, e e por isso que o formulario pede a data de fim como OPCIONAL
e nao como obrigatoria: o caminho mais facil tem de ser o seguro.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import pagina
import portal_base
from portal import NAV

# As cores vem das fichas do tema, nao de hexadecimais fixos:
# ver a nota em portal_base.FICHAS.
CORES = portal_base.FICHAS

CSS = """
/* ----------------------------------------------------------- a fita
   Os doze meses como UMA fita, e nao doze cartoes. Doze cartoes sao
   doze molduras a dizer "sou uma caixa" quando o que interessa e a
   COMPARACAO entre eles — e uma fita continua faz a comparacao sem
   dizer nada. */
.fita {
  display: flex; gap: 4px; align-items: flex-end;
  background: var(--sup); border-radius: var(--r-g);
  padding: 1.2rem 1.1rem 1rem; margin-bottom: 1.6rem;
  box-shadow: var(--sombra); overflow-x: auto;
  scrollbar-width: none;
}
.fita::-webkit-scrollbar { display: none; }
.mes {
  flex: 1 1 0; min-width: 2.6rem;
  display: flex; flex-direction: column; align-items: center; gap: .45rem;
  padding: 0; background: none; border: 0; cursor: pointer;
}
.mes-b {
  width: 100%; height: 5.5rem; border-radius: var(--r-p);
  background: var(--sup-2); display: flex; align-items: flex-end;
  overflow: hidden;
}
/* A altura e `--p`, mas NAO e a percentagem crua. Um mes com 20 de 31
   dias abertos da 65%, e 22 de 30 da 73%: a olho, duas barras de 65% e
   73% numa altura de 5.5rem diferem em 4px e lem-se como iguais.
   O calc estica a escala — 0% fica em 0, 100% fica em 100, e o meio
   abre-se — para a diferenca entre "quase todo o mes" e "metade do
   mes" se ver sem contar os numeros. O numero exacto esta por baixo,
   em texto, para quem precisar dele. */
.mes-f {
  width: 100%; height: calc(12% + var(--p, 0%) * 0.88);
  background: var(--sel); border-radius: var(--r-p);
  transition: height .25s ease;
}
/* Zero dias abertos e zero altura, sem o minimo de 12%: uma barrinha
   num mes vazio dizia "ha aqui alguma coisa" quando nao ha nada. */
.mes-zero .mes-f { height: 0; }
/* O mes em que nao ha um unico dia aberto nao fica so vazio: fica
   pintado com a cor do que esta fechado. Um rectangulo vazio le-se
   como "ainda nao carregou"; este le-se como "aqui nao se vende". */
.mes-zero .mes-b { background: var(--fechado-f); }
.mes-n { font-size: .78rem; font-weight: 600; color: var(--tinta-2); }
.mes-d { font-size: .72rem; color: var(--mudo); }
.mes-agora .mes-n { color: var(--acento); }
.mes:hover .mes-b { background: var(--sup-3); }
.mes-zero:hover .mes-b { filter: brightness(.97); }

/* -------------------------------------------------- epocas como frases */
.eps { display: grid; gap: .7rem; margin-bottom: 1.6rem; }
.ep {
  background: var(--sup); border-radius: var(--r-g);
  padding: 1.1rem 1.2rem; box-shadow: var(--sombra);
  display: flex; flex-wrap: wrap; gap: .8rem 1rem; align-items: baseline;
}
.ep-f {
  flex: 1 1 22rem; margin: 0;
  font-size: 1rem; line-height: 1.6; color: var(--tinta-2);
}
.ep-f b { color: var(--tinta); font-weight: 600; }
.ep-nota {
  flex-basis: 100%; margin: 0;
  font-size: .85rem; line-height: 1.5; color: var(--mudo);
}
.ep-acoes { display: flex; gap: .5rem; margin-left: auto; }
/* Uma epoca que ja passou nao se apaga sozinha: fica, com a palavra
   "ended". Apagar o que aconteceu e perder a resposta a pergunta
   "porque e que Agosto do ano passado estava aberto?".

   Recuar NAO se faz com `opacity`. Foi a primeira tentativa e o axe
   recusou-a nos dois temas: o opacity apaga tudo o que esta dentro —
   incluindo a pastilha "ended" e o botao de remover, que tem de
   continuar a ler-se tao bem como os outros. Recua-se so o texto da
   frase, e com a ficha do texto apagado, que a porta de contraste ja
   garante sobre esta superficie. */
.ep-fim .ep-f { color: var(--mudo); }
.ep-fim .ep-f b { color: var(--mudo); font-weight: 500; }

/* ------------------------------------------------- os dias da semana */
.ds-l { display: flex; flex-wrap: wrap; gap: .4rem; }
.ds {
  padding: .55rem .9rem; border-radius: var(--r-c);
  background: var(--sup-2); color: var(--tinta-2);
  font-size: .87rem; font-weight: 600;
  transition: background .15s, color .15s;
}
.ds:hover { background: var(--sup-3); }
.ds-on { background: var(--sel); color: var(--sel-t); }
.ds-on:hover { background: var(--sel); filter: brightness(1.12); }

/* ------------------------------------------------------- as partidas */
.hs-l { display: flex; flex-wrap: wrap; gap: .5rem; align-items: center; }
.hora {
  display: inline-flex; align-items: center; gap: .4rem;
  background: var(--sup-2); border-radius: var(--r-c);
  padding: .4rem .45rem .4rem .9rem;
  font-size: .95rem; font-weight: 600; color: var(--tinta);
}
.hora button {
  width: 1.5rem; height: 1.5rem; border-radius: var(--r-c);
  background: var(--sup-3); color: var(--tinta-2);
  font-size: .9rem; font-weight: 600;
  display: inline-flex; align-items: center; justify-content: center;
}
.hora button:hover { background: var(--fechado-f); color: var(--fechado); }

/* ------------------------------------------------------- o formulario */
.ep-novo { background: var(--sup-2); }
.ep-novo .cx-t { margin-bottom: 1.2rem; }

/* O modo: duas opcoes, lado a lado, com a explicacao de cada uma por
   baixo. Um <select> com dois valores esconde metade da decisao atras
   de um toque — e esta decisao muda o que a pagina do tour pergunta ao
   cliente. */
.modos { display: grid; gap: .7rem; margin-bottom: 1.2rem; }
@media (min-width: 680px) { .modos { grid-template-columns: 1fr 1fr; } }
.modo {
  text-align: left; padding: 1rem 1.1rem; border-radius: var(--r-m);
  background: var(--sup); cursor: pointer;
}
.modo:hover { background: var(--sup-3); }
.modo-on { background: var(--sel); }
.modo-on:hover { background: var(--sel); filter: brightness(1.12); }
.modo b { display: block; font-size: .95rem; color: var(--tinta); }
.modo span {
  display: block; margin-top: .25rem;
  font-size: .83rem; line-height: 1.5; color: var(--mudo);
}
.modo-on b, .modo-on span { color: var(--sel-t); }
.modo-on span { opacity: .8; }
"""


JS = r"""
(function () {
  'use strict';
  if (!window.ewt || window.ewt.avariado) return;

  var DIAS = [[1,'Mon'],[2,'Tue'],[3,'Wed'],[4,'Thu'],[5,'Fri'],
              [6,'Sat'],[7,'Sun']];
  var MESES = ['Jan','Feb','Mar','Apr','May','Jun',
               'Jul','Aug','Sep','Oct','Nov','Dec'];

  var E = { anuncios: [], tour: null, slug: null, modo: 'departures',
            epocas: [], horas: [], dias: [1,2,3,4,5], novoModo: 'departures' };

  function hhmm(t) { return String(t || '').slice(0, 5); }
  function esc(s) { return ewt.escapar(String(s == null ? '' : s)); }

  // Uma data em ISO para o que se le. O `new Date('2026-06-01')` e UTC,
  // e num fuso a oeste de Greenwich isso mostra 31 de Maio — por isso a
  // data parte-se a mao em vez de se entregar ao construtor.
  function legivel(iso) {
    if (!iso) return '';
    var p = String(iso).split('-');
    var d = new Date(+p[0], +p[1] - 1, +p[2]);
    return d.toLocaleDateString(undefined,
      { day: 'numeric', month: 'short', year: 'numeric' });
  }

  // "Mon to Fri" quando sao seguidos, "Mon, Wed and Fri" quando nao sao.
  // Vale a pena porque "Mon, Tue, Wed, Thu, Fri" e a frase que o
  // operador mais vezes vai ler, e e a que menos se le.
  function frasedias(ws) {
    var s = (ws || []).slice().sort(function (a, b) { return a - b; });
    if (!s.length) return 'no days';
    if (s.length === 7) return 'every day';
    var nomes = s.map(function (n) { return DIAS[n - 1][1]; });
    var seguidos = s.every(function (v, i) { return i === 0 || v === s[i-1] + 1; });
    if (seguidos && s.length > 2) {
      return '<b>' + nomes[0] + '</b> to <b>' + nomes[nomes.length - 1] + '</b>';
    }
    var b = nomes.map(function (n) { return '<b>' + n + '</b>'; });
    if (b.length === 1) return b[0];
    return b.slice(0, -1).join(', ') + ' and ' + b[b.length - 1];
  }

  function frasequando(ep) {
    if (!ep.ends_on) {
      return 'from <b>' + legivel(ep.starts_on) + '</b> onwards';
    }
    return '<b>' + legivel(ep.starts_on) + '</b> to <b>'
         + legivel(ep.ends_on) + '</b>';
  }

  function frasehoras(ep) {
    if (E.modo === 'opening_hours') {
      if (!ep.opens_at) return '';
      return ', open <b>' + hhmm(ep.opens_at) + '</b> to <b>'
           + hhmm(ep.closes_at) + '</b>';
    }
    var hs = (ep.horas || []).map(hhmm);
    if (!hs.length) {
      // Isto nao e um detalhe cosmetico: uma epoca sem partidas nao
      // vende nada. Diz-se por palavras, aqui, em vez de o operador
      // descobrir pelo telefone que nao lhe entram reservas.
      return ', <b>but with no departure times — nothing can be '
           + 'booked</b>';
    }
    var b = hs.map(function (h) { return '<b>' + h + '</b>'; });
    return ', leaving at ' + (b.length === 1 ? b[0]
      : b.slice(0, -1).join(', ') + ' and ' + b[b.length - 1]);
  }

  // ------------------------------------------------------------ a fita
  async function desenharFita() {
    var c = document.getElementById('fita');
    if (!E.slug) { c.innerHTML = ''; return; }

    var hoje = new Date();
    var de = ewt.iso(hoje);
    var fim = new Date(hoje.getFullYear(), hoje.getMonth() + 12, 0);
    var r = await ewt.sb.rpc('dias_abertos',
      { p_slug: E.slug, p_de: de, p_ate: ewt.iso(fim) });
    if (r.error) { ewt.dizer('av', ewt.legivel(r.error), 'mal'); return; }

    // Quantos dias abertos por mes, e quantos dias tem cada mes a
    // contar de hoje (o mes corrente conta so a partir de hoje: dizer
    // "5 de 31" a 28 do mes era uma falsidade com ar de numero).
    var abertos = {}, total = {};
    (r.data || []).forEach(function (d) {
      var k = String(d.dia || d).slice(0, 7);
      abertos[k] = (abertos[k] || 0) + 1;
    });
    var cur = new Date(hoje.getFullYear(), hoje.getMonth(), hoje.getDate());
    while (cur <= fim) {
      var k2 = ewt.iso(cur).slice(0, 7);
      total[k2] = (total[k2] || 0) + 1;
      cur.setDate(cur.getDate() + 1);
    }

    var saida = [];
    Object.keys(total).sort().forEach(function (k, i) {
      var a = abertos[k] || 0, t = total[k] || 1;
      var pct = Math.round(a / t * 100);
      var nome = MESES[+k.slice(5, 7) - 1];
      saida.push('<button type="button" class="mes'
        + (i === 0 ? ' mes-agora' : '') + (a === 0 ? ' mes-zero' : '')
        + '" style="--p:' + pct + '%" data-mes="' + k
        + '" aria-label="' + nome + ': ' + a + ' of ' + t
        + ' days open. Open the calendar for this month.">'
        + '<span class="mes-b"><span class="mes-f"></span></span>'
        + '<span class="mes-n">' + nome + '</span>'
        + '<span class="mes-d">' + a + '</span></button>');
    });
    c.innerHTML = saida.join('');

    var vazios = Object.keys(total).filter(function (k) {
      return !(abertos[k] || 0);
    });
    var av = document.getElementById('av-fita');
    if (vazios.length) {
      av.innerHTML = '<b>' + vazios.length + ' of the next 12 months '
        + 'have no open day at all.</b> If that is not deliberate, the '
        + 'season covering them has ended — or there is none.';
      av.className = 'aviso aviso-nota';
      av.hidden = false;
    } else {
      av.hidden = true;
    }
  }

  // ---------------------------------------------------------- as epocas
  async function carregar() {
    if (!E.tour) return;
    document.getElementById('eps').innerHTML =
      '<p class="carrega">Loading…</p>';

    var r = await ewt.sb.from('listing_seasons')
      .select('id, starts_on, ends_on, weekdays, opens_at, closes_at, note, '
            + 'season_times(starts_at)')
      .eq('listing_id', E.tour)
      .order('starts_on');
    if (r.error) { ewt.dizer('av', ewt.legivel(r.error), 'mal'); return; }

    E.epocas = (r.data || []).map(function (x) {
      x.horas = (x.season_times || []).map(function (h) { return h.starts_at; })
                 .sort();
      return x;
    });
    desenharEpocas();
    await desenharFita();
  }

  function desenharEpocas() {
    var c = document.getElementById('eps');
    if (!E.epocas.length) {
      c.innerHTML = '<div class="vazio"><h3>No season yet</h3>'
        + '<p>Until there is one, this tour is offered on whatever days '
        + 'you opened by hand in the calendar — and on no others. '
        + 'One season below replaces all that tapping.</p></div>';
      return;
    }
    var hoje = ewt.iso(new Date());
    c.innerHTML = E.epocas.map(function (ep) {
      var acabou = ep.ends_on && ep.ends_on < hoje;
      return '<div class="ep' + (acabou ? ' ep-fim' : '') + '">'
        + '<p class="ep-f">Open ' + frasedias(ep.weekdays) + ', '
        + frasequando(ep) + frasehoras(ep) + '.'
        + (acabou ? ' <span class="est est-draft">ended</span>' : '')
        + '</p>'
        + '<div class="ep-acoes">'
        + '<button type="button" class="bt bt-mal bt-pq" data-apaga="'
        + esc(ep.id) + '">Remove</button></div>'
        + (ep.note ? '<p class="ep-nota">' + esc(ep.note) + '</p>' : '')
        + '</div>';
    }).join('');
  }

  // ------------------------------------------------------------ gravar
  async function criar() {
    var de = document.getElementById('de').value;
    var ate = document.getElementById('ate').value;
    var nota = document.getElementById('nota').value.trim();

    if (!de) {
      ewt.dizer('av-novo', 'A season needs a start date.', 'mal'); return;
    }
    if (ate && ate < de) {
      ewt.dizer('av-novo', 'The end date is before the start date.', 'mal');
      return;
    }
    if (!E.dias.length) {
      ewt.dizer('av-novo', 'Pick at least one day of the week.', 'mal');
      return;
    }

    var linha = { listing_id: E.tour, starts_on: de, ends_on: ate || null,
                  weekdays: E.dias.slice().sort(function (a,b) { return a-b; }),
                  note: nota || null };

    if (E.novoModo === 'opening_hours') {
      var ab = document.getElementById('abre').value;
      var fe = document.getElementById('fecha').value;
      if (!ab || !fe) {
        ewt.dizer('av-novo', 'Opening hours need both a start and an end.',
                  'mal');
        return;
      }
      if (fe <= ab) {
        ewt.dizer('av-novo', 'The closing time is not after the opening one.',
                  'mal');
        return;
      }
      linha.opens_at = ab + ':00';
      linha.closes_at = fe + ':00';
    } else if (!E.horas.length) {
      ewt.dizer('av-novo', 'Add at least one departure time — a season '
        + 'without one cannot be booked.', 'mal');
      return;
    }

    var b = document.getElementById('bt-criar');
    b.disabled = true;
    var r = await ewt.sb.from('listing_seasons').insert(linha).select('id');
    if (r.error) {
      b.disabled = false;
      ewt.dizer('av-novo', ewt.legivel(r.error), 'mal'); return;
    }
    var id = r.data[0].id;

    if (E.novoModo === 'departures' && E.horas.length) {
      var h = await ewt.sb.from('season_times').insert(
        E.horas.map(function (x) {
          return { season_id: id, starts_at: hhmm(x) + ':00' };
        }));
      if (h.error) {
        // A epoca ficou sem horas, e uma epoca sem horas nao vende. Nao
        // se deixa isso em pe: desfaz-se e diz-se porque.
        await ewt.sb.from('listing_seasons').delete().eq('id', id);
        b.disabled = false;
        ewt.dizer('av-novo', 'The season could not be saved with its '
          + 'departure times, so nothing was saved: '
          + ewt.legivel(h.error), 'mal');
        return;
      }
    }

    // O modo do anuncio acompanha a epoca que se acabou de criar: um
    // anuncio com uma epoca de janela e modo 'departures' pergunta ao
    // cliente uma hora de partida que nao existe.
    if (E.modo !== E.novoModo) {
      var m = await ewt.sb.from('listings')
        .update({ schedule_mode: E.novoModo }).eq('id', E.tour);
      if (!m.error) { E.modo = E.novoModo; }
    }

    b.disabled = false;
    E.horas = [];
    document.getElementById('nota').value = '';
    desenharHoras();
    ewt.dizer('av-novo', '', '');
    ewt.dizer('av', 'Season added. It is live on the site now.', 'bem');
    await carregar();
  }

  async function apagar(id) {
    var ep = E.epocas.filter(function (x) { return x.id === id; })[0];
    if (!ep) return;
    if (!window.confirm('Remove this season? Days that only this season '
        + 'opened stop being offered straight away.')) return;
    var r = await ewt.sb.from('listing_seasons').delete().eq('id', id);
    if (r.error) { ewt.dizer('av', ewt.legivel(r.error), 'mal'); return; }
    ewt.dizer('av', 'Season removed.', 'bem');
    await carregar();
  }

  // -------------------------------------------------------- o desenho
  function desenharDias() {
    document.getElementById('ds-l').innerHTML = DIAS.map(function (d) {
      var on = E.dias.indexOf(d[0]) >= 0;
      return '<button type="button" class="ds' + (on ? ' ds-on' : '')
        + '" data-d="' + d[0] + '" aria-pressed="' + on + '">'
        + d[1] + '</button>';
    }).join('');
  }

  function desenharHoras() {
    var c = document.getElementById('hs-l');
    c.innerHTML = E.horas.length
      ? E.horas.map(function (h) {
          return '<span class="hora">' + hhmm(h)
            + '<button type="button" data-tira="' + hhmm(h)
            + '" aria-label="Remove the ' + hhmm(h)
            + ' departure">×</button></span>';
        }).join('')
      : '<p class="campo" style="margin:0;color:var(--mudo);font-size:.87rem">'
        + 'No departure time yet.</p>';
  }

  function desenharModo() {
    ['departures', 'opening_hours'].forEach(function (m) {
      var b = document.getElementById('modo-' + m);
      var on = E.novoModo === m;
      b.className = 'modo' + (on ? ' modo-on' : '');
      b.setAttribute('aria-pressed', on);
    });
    document.getElementById('bl-horas').hidden = E.novoModo !== 'departures';
    document.getElementById('bl-janela').hidden = E.novoModo !== 'opening_hours';
  }

  // ------------------------------------------------------------- arranque
  (async function () {
    var u = await ewt.exigir_entrada();
    if (!u) return;

    var r = await ewt.sb.from('listings')
      .select('id, slug, city, country, schedule_mode, listing_versions(payload)')
      .order('created_at');
    if (r.error) { ewt.dizer('av', ewt.legivel(r.error), 'mal'); return; }

    var anuncios = (r.data || []).map(function (l) {
      var v = (l.listing_versions || [])[0];
      l.titulo = (v && v.payload && v.payload.title) || l.slug;
      return l;
    });

    document.getElementById('carrega').hidden = true;
    if (!anuncios.length) {
      document.getElementById('conteudo').innerHTML =
        '<div class="vazio"><h3>No tour yet</h3><p>Seasons say when a tour '
        + 'runs, so there has to be a tour first.</p>'
        + '<a class="bt bt-p" href="/portal/">Create a tour</a></div>';
      return;
    }
    document.getElementById('ep').hidden = false;

    var sel = document.getElementById('qual');
    sel.innerHTML = anuncios.map(function (a) {
      return '<option value="' + esc(a.id) + '">' + esc(a.titulo)
        + ' — ' + esc(a.city) + '</option>';
    }).join('');

    E.anuncios = anuncios;

    function escolher() {
      var a = anuncios.filter(function (x) { return x.id === sel.value; })[0];
      E.tour = a.id; E.slug = a.slug;
      E.modo = a.schedule_mode || 'departures';
      E.novoModo = E.modo;
      desenharModo();
      carregar();
    }

    sel.addEventListener('change', escolher);

    document.getElementById('ds-l').addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-d]');
      if (!b) return;
      var n = +b.getAttribute('data-d');
      var i = E.dias.indexOf(n);
      if (i >= 0) { E.dias.splice(i, 1); } else { E.dias.push(n); }
      desenharDias();
    });

    document.getElementById('f-hora').addEventListener('submit', function (ev) {
      ev.preventDefault();
      var i = document.getElementById('hora-nova');
      var v = hhmm(i.value);
      if (!v) { ewt.dizer('av-novo', 'Pick a time first.', 'mal'); return; }
      if (E.horas.map(hhmm).indexOf(v) >= 0) {
        ewt.dizer('av-novo', 'That departure is already there.', 'mal');
        return;
      }
      E.horas = E.horas.map(hhmm).concat([v]).sort();
      i.value = '';
      ewt.dizer('av-novo', '', '');
      desenharHoras();
    });

    document.getElementById('hs-l').addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-tira]');
      if (!b) return;
      var fora = b.getAttribute('data-tira');
      E.horas = E.horas.filter(function (h) { return hhmm(h) !== fora; });
      desenharHoras();
    });

    ['departures', 'opening_hours'].forEach(function (m) {
      document.getElementById('modo-' + m).addEventListener('click', function () {
        E.novoModo = m;
        desenharModo();
      });
    });

    document.getElementById('eps').addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-apaga]');
      if (b) apagar(b.getAttribute('data-apaga'));
    });

    document.getElementById('fita').addEventListener('click', function (ev) {
      var b = ev.target.closest('[data-mes]');
      if (b) {
        // A fita responde "onde e o buraco"; o calendario e onde se
        // trata dele. A ligacao leva o mes para a pessoa nao ter de o
        // procurar outra vez.
        window.location.href = '/portal/calendar/?m=' + b.getAttribute('data-mes');
      }
    });

    document.getElementById('bt-criar').addEventListener('click', criar);

    desenharDias();
    desenharHoras();
    escolher();
  })();
})();
"""


def corpo():
    return '''<main id="principal" class="pt-corpo">
  <div class="folha" id="conteudo">
    <p class="carrega" id="carrega">Loading your seasons&hellip;</p>

    <div id="ep" hidden>
      <div class="pt-cab">
        <h1>Seasons</h1>
        <p>A season is the rule: which months, which days of the week,
          which departure times. Say it once and the calendar is only
          for the exceptions &mdash; the one week you are away, the day
          the van is in for service.</p>
      </div>

      <div class="campo" style="max-width:26rem">
        <label for="qual">Tour</label>
        <select id="qual"></select>
      </div>

      <p class="aviso" id="av" role="status" hidden></p>

      <h2 class="cx-t" style="margin:1.4rem 0 .7rem">The next twelve months</h2>
      <div class="fita" id="fita"></div>
      <p class="aviso" id="av-fita" hidden></p>

      <h2 class="cx-t" style="margin:1.8rem 0 .7rem">Your seasons</h2>
      <div class="eps" id="eps"></div>

      <div class="cx ep-novo">
        <h2 class="cx-t">Add a season</h2>

        <div class="modos" role="group" aria-label="How this tour runs">
          <button type="button" class="modo" id="modo-departures"
                  aria-pressed="true">
            <b>Fixed departure times</b>
            <span>The tour leaves at set times. The customer picks
              one.</span>
          </button>
          <button type="button" class="modo" id="modo-opening_hours"
                  aria-pressed="false">
            <b>Driver at their disposal</b>
            <span>You are available within a window and the exact hour is
              agreed afterwards.</span>
          </button>
        </div>

        <div class="linha2">
          <div class="campo">
            <label for="de">First day</label>
            <input type="date" id="de">
          </div>
          <div class="campo">
            <label for="ate">Last day</label>
            <input type="date" id="ate">
            <span class="ajuda">Leave this empty and the season keeps
              rolling forward. That is the safe choice: a season with an
              end date stops quietly on the day it ends, and nothing
              warns you.</span>
          </div>
        </div>

        <div class="campo">
          <span class="rotc" id="rotc-dias">Days of the week</span>
          <div class="ds-l" id="ds-l" role="group"
               aria-labelledby="rotc-dias"></div>
        </div>

        <div class="campo" id="bl-horas">
          <span class="rotc">Departure times</span>
          <div class="hs-l" id="hs-l" style="margin-bottom:.6rem"></div>
          <form class="hs-l" id="f-hora">
            <label class="so-leitor" for="hora-nova">Add a departure
              time</label>
            <input type="time" id="hora-nova" step="300"
                   style="width:9rem">
            <button type="submit" class="bt bt-s bt-pq">Add</button>
          </form>
        </div>

        <div id="bl-janela" hidden>
          <div class="linha2">
            <div class="campo">
              <label for="abre">Available from</label>
              <input type="time" id="abre" step="300">
            </div>
            <div class="campo">
              <label for="fecha">Until</label>
              <input type="time" id="fecha" step="300">
            </div>
          </div>
        </div>

        <div class="campo">
          <label for="nota">Note to yourself <span
            class="ajuda" style="display:inline">(optional)</span></label>
          <input type="text" id="nota"
                 placeholder="Summer, two drivers">
          <span class="ajuda">Only you see this. It is here for the day
            you look at three overlapping seasons and wonder why.</span>
        </div>

        <p class="aviso" id="av-novo" role="status" hidden></p>

        <div class="acoes">
          <button type="button" class="bt bt-p" id="bt-criar">Add
            season</button>
        </div>
      </div>
    </div>
  </div>
</main>'''


def gerar():
    pagina.verificar_contraste()
    html = portal_base.envolver(
        titulo='Seasons — Exclusive World Tours',
        corpo=corpo(), js=JS, etiqueta='Operator portal',
        nav=NAV, atual='/portal/seasons/', css_extra=CSS)
    pagina.escrever(html, 'portal/seasons/index.html')


if __name__ == '__main__':
    gerar()
