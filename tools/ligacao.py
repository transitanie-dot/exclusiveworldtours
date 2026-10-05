# -*- coding: utf-8 -*-
"""A ligacao do site a base de dados.

Escreve `assets/ligacao.js`, que e o unico sitio do site que sabe o
endereco da base e a chave publica. Todas as paginas que falam com a
base carregam este ficheiro e usam `ewt.*` — assim, mudar de projeto
Supabase e mudar duas linhas aqui e gerar outra vez, e nao procurar a
chave em dez paginas.

Sobre a chave
-------------
A chave que esta aqui e a PUBLICAVEL (`sb_publishable_...`). Nao e um
segredo: e desenhada para ir no browser, e sozinha nao da acesso a
nada. O que protege os dados e o RLS na base, nao o esconder da chave.

A chave de servico (`service_role`) ignora o RLS e NUNCA entra neste
repositorio nem em nenhum ficheiro do site. Vive numa variavel de
ambiente e e usada so pelo gerador, na maquina do Ricardo.
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

# O projeto Supabase do Exclusive World Tours, criado a 2 de outubro de
# 2026 na regiao eu-west-1 (Irlanda) — perto dos clientes e dentro da UE.
PROJETO = 'lmrvoakknsrypoeqmjbr'
URL = 'https://%s.supabase.co' % PROJETO
CHAVE_PUBLICA = 'sb_publishable_qZGKVMEj_q974y92A8hH7w_qeyU5m0o'

# Carregado por qualquer pagina que fale com a base.
SCRIPTS = ('<script src="/assets/lib/supabase.js"></script>\n'
           '<script src="/assets/ligacao.js"></script>')


JS = r"""/* Exclusive World Tours — a ligacao a base de dados.
   Gerado por tools/ligacao.py. Nao editar a mao. */
(function (w) {
  'use strict';

  var URL = '%(url)s';
  var CHAVE = '%(chave)s';

  if (!w.supabase || !w.supabase.createClient) {
    // Sem a biblioteca nao ha nada a fazer, mas a pagina nao deve
    // morrer em silencio: quem esta a usar o portal tem de saber que
    // o problema e de carregamento e nao dos dados dele.
    w.ewt = { avariado: true };
    return;
  }

  var sb = w.supabase.createClient(URL, CHAVE, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
      flowType: 'pkce'
    }
  });

  // -------------------------------------------------------------- texto
  //
  // As mensagens de erro da base vem em ingles tecnico e algumas dizem
  // coisas que nao interessam a ninguem de fora ("new row violates
  // row-level security policy"). Traduzem-se para o que a pessoa pode
  // fazer a respeito.
  var TRADUZIR = [
    [/row-level security/i,
     'You do not have permission to change this. If you think you should, write to us.'],
    [/duplicate key value.*slug/i,
     'There is already a tour with that web address. Change the title slightly.'],
    [/slug_valido/i,
     'The web address can only use lowercase letters, numbers and hyphens.'],
    [/Failed to fetch|NetworkError|network/i,
     'Could not reach the server. Check your connection and try again.'],
    [/invalid.*token|expired/i,
     'That sign-in link has expired. Ask for a new one.'],
    [/rate limit|too many/i,
     'Too many attempts. Wait a minute and try again.']
  ];

  function legivel(erro) {
    if (!erro) return 'Something went wrong.';
    var m = erro.message || erro.error_description || String(erro);
    for (var i = 0; i < TRADUZIR.length; i++) {
      if (TRADUZIR[i][0].test(m)) return TRADUZIR[i][1];
    }
    return m;
  }

  // ------------------------------------------------------------- avisos
  //
  // Um sitio so para dizer as coisas ao utilizador. O elemento tem de
  // ter role="status" no HTML para um leitor de ecra anunciar a
  // mudanca; sem isso a mensagem aparece e so quem ve e que sabe.
  function dizer(alvo, texto, tipo) {
    var el = typeof alvo === 'string' ? document.getElementById(alvo) : alvo;
    if (!el) return;
    el.textContent = texto || '';
    el.className = 'aviso' + (tipo ? ' aviso-' + tipo : '');
    el.hidden = !texto;
  }

  // ------------------------------------------------------------- sessao
  async function sessao() {
    var r = await sb.auth.getSession();
    return (r.data && r.data.session) || null;
  }

  async function utilizador() {
    var s = await sessao();
    return s ? s.user : null;
  }

  async function sair() {
    await sb.auth.signOut();
    w.location.href = '/';
  }

  // Quem sou eu aqui dentro: administrador, operador, ou nem uma coisa
  // nem outra. Uma chamada so, no arranque de cada pagina do portal.
  async function papel() {
    var u = await utilizador();
    if (!u) return { entrou: false };

    var a = await sb.rpc('is_admin');
    var o = await sb.from('operator_users')
      .select('operator_id, role, operators(id, name, status, commission_rate)');

    return {
      entrou: true,
      email: u.email,
      id: u.id,
      admin: a.data === true,
      operadores: (o.data || []).map(function (x) {
        return {
          id: x.operator_id,
          papel: x.role,
          nome: x.operators ? x.operators.name : '',
          estado: x.operators ? x.operators.status : '',
          comissao: x.operators ? x.operators.commission_rate : null
        };
      })
    };
  }

  // Manda para a entrada quem nao assinou, guardando a pagina onde
  // estava para voltar la depois de entrar.
  async function exigir_entrada() {
    var p = await papel();
    if (!p.entrou) {
      var volta = encodeURIComponent(w.location.pathname + w.location.search);
      w.location.replace('/portal/?volta=' + volta);
      return null;
    }
    return p;
  }

  // ---------------------------------------------------------------- datas
  function hoje() {
    var d = new Date();
    return d.getFullYear() + '-' + dois(d.getMonth() + 1) + '-' + dois(d.getDate());
  }
  function dois(n) { return (n < 10 ? '0' : '') + n; }
  function iso(d) {
    return d.getFullYear() + '-' + dois(d.getMonth() + 1) + '-' + dois(d.getDate());
  }

  // -------------------------------------------------------------- numeros
  function euros(v) {
    if (v === null || v === undefined || v === '') return '';
    var n = Number(v);
    if (!isFinite(n)) return '';
    var s = n.toFixed(2).replace(/\.00$/, '');
    return s.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  }

  // ------------------------------------------------------------ fotos
  //
  // Antes disto, "por uma fotografia" queria dizer: ter um sitio onde
  // alojar imagens, saber o que e uma URL directa, e perceber porque e
  // que a do Facebook nao serve. Na pratica queria dizer nao ter
  // fotografias.
  //
  // O caminho e sempre <operator_id>/<nome>, e a politica do balde
  // verifica a primeira pasta: um operador nao consegue escrever por
  // cima das fotografias de outro nem que tente.
  var FOTO_MAX = 5 * 1024 * 1024;
  var FOTO_TIPOS = ['image/jpeg', 'image/png', 'image/webp', 'image/avif'];

  async function enviar_foto(ficheiro, operador) {
    if (!ficheiro) return { erro: 'Pick a file first.' };
    if (FOTO_TIPOS.indexOf(ficheiro.type) < 0) {
      return { erro: 'That has to be a JPEG, PNG, WebP or AVIF image.' };
    }
    if (ficheiro.size > FOTO_MAX) {
      return { erro: 'That image is ' + Math.round(ficheiro.size / 1048576)
                     + ' MB. The limit is 5 MB \u2014 most phones can export '
                     + 'a smaller one.' };
    }

    // Um nome que nao colide e nao revela o nome do ficheiro original,
    // que as vezes e o nome de uma pessoa ou de um cliente.
    var ext = ({ 'image/jpeg': 'jpg', 'image/png': 'png',
                 'image/webp': 'webp', 'image/avif': 'avif' })[ficheiro.type];
    var nome = operador + '/' + Date.now() + '-'
             + Math.random().toString(36).slice(2, 8) + '.' + ext;

    var r = await sb.storage.from('fotos').upload(nome, ficheiro, {
      cacheControl: '31536000', upsert: false, contentType: ficheiro.type
    });
    if (r.error) return { erro: legivel(r.error) };

    var u = sb.storage.from('fotos').getPublicUrl(nome);
    return { url: u.data.publicUrl, caminho: nome };
  }

  function escapar(s) {
    return String(s === null || s === undefined ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }


  // =================================================================
  // O PAGAMENTO
  //
  // Tres chamadas, e nenhuma delas calcula um preco.
  //
  //   cotar()           pergunta a base quanto custa e se da para pagar
  //                     depois. A base responde, e a resposta inclui a
  //                     RAZAO quando nao da.
  //   reservar()        chama a Edge Function, que cria a reserva na
  //                     base e abre a pagina do Stripe. A chave do
  //                     Stripe esta la e nunca aqui.
  //   resumo_sessao()   o que a pagina de confirmacao mostra.
  //
  // Porque e que a cotar() vai a base e nao faz a conta aqui: a pagina
  // ja tem os escaloes no HTML e podia multiplicar sozinha. Mas entao
  // havia duas copias da regra do preco — esta e a da base — e no dia
  // em que uma mudasse, o cliente via um numero e o Stripe cobrava
  // outro. A pagina mostra exatamente o que vai ser cobrado porque
  // pergunta a quem cobra.
  // =================================================================

  async function cotar(pedido) {
    var r = await sb.rpc('cotar', { p: pedido });
    if (r.error) throw new Error(legivel(r.error));
    return r.data;
  }

  /** Chama uma Edge Function. A chave publicavel autentica o pedido; o
   *  que protege o dinheiro e o que esta DENTRO da funcao, nao isto. */
  async function funcao(nome, corpo, metodo) {
    var r = await fetch(URL + '/functions/v1/' + nome, {
      method: metodo || 'POST',
      headers: {
        'content-type': 'application/json',
        apikey: CHAVE,
        authorization: 'Bearer ' + CHAVE
      },
      body: metodo === 'GET' ? undefined : JSON.stringify(corpo || {})
    });
    var d = null;
    try { d = await r.json(); } catch (e) { /* resposta sem corpo */ }
    if (!r.ok) {
      // A mensagem da funcao vale mais do que um codigo HTTP: ela sabe
      // se o dia fechou, se o grupo nao cabe ou se o Stripe nao abriu.
      var err = new Error((d && d.error) || ('HTTP ' + r.status));
      err.codigo = d && d.code;
      throw err;
    }
    return d;
  }

  async function reservar(pedido) {
    return await funcao('reservar', pedido);
  }

  async function resumo_sessao(id) {
    var r = await fetch(URL + '/functions/v1/sessao?id=' + encodeURIComponent(id), {
      headers: { apikey: CHAVE, authorization: 'Bearer ' + CHAVE }
    });
    if (!r.ok) throw new Error('We could not find that booking.');
    return await r.json();
  }

  w.ewt = {
    sb: sb, legivel: legivel, dizer: dizer,
    sessao: sessao, utilizador: utilizador, sair: sair,
    papel: papel, exigir_entrada: exigir_entrada,
    hoje: hoje, iso: iso, euros: euros, escapar: escapar,
    enviar_foto: enviar_foto,
    cotar: cotar, reservar: reservar, resumo_sessao: resumo_sessao
  };
})(window);
"""


def escrever():
    destino = os.path.join(RAIZ, 'assets', 'ligacao.js')
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, 'w') as f:
        f.write(JS % {'url': URL, 'chave': CHAVE_PUBLICA})
    print('escrito: assets/ligacao.js (%.0f KB)'
          % (os.path.getsize(destino) / 1024))

    # A biblioteca tem de estar la: sem ela o portal nao faz nada, e o
    # erro so aparecia no browser do Ricardo.
    lib = os.path.join(RAIZ, 'assets', 'lib', 'supabase.js')
    if not os.path.exists(lib):
        sys.exit('Falta assets/lib/supabase.js. Corre:\n'
                 '  npm install @supabase/supabase-js\n'
                 '  cp node_modules/@supabase/supabase-js/dist/umd/supabase.js '
                 'assets/lib/supabase.js')


if __name__ == '__main__':
    escrever()
