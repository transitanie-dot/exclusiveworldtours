// Testa as paginas do portal com a base simulada.
//
// O container nao chega ao Supabase (politica de egresso), e nao e isso
// que esta em causa aqui: o que precisa de ser verificado e o MEU codigo
// — se a fila desenha a diferenca certa, se o calendario pinta os dias
// certos, se um erro aparece em vez de uma pagina em branco. Por isso as
// respostas da base sao fabricadas aqui e intercetadas antes de sairem.
//
//   node tools/testar_portal.mjs

// A playwright esta instalada globalmente no container e e CommonJS,
// por isso entra pelo default e nao por nome.
import pw from '/opt/npm-tools/node_modules/playwright/index.js';
const { chromium } = pw;
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const RAIZ = process.cwd();
const PORTA = 8099;

const TIPOS = { '.html': 'text/html', '.js': 'text/javascript',
  '.css': 'text/css', '.json': 'application/json', '.woff2': 'font/woff2',
  '.svg': 'image/svg+xml' };

const servidor = http.createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (p.endsWith('/')) p += 'index.html';
  const f = path.join(RAIZ, p);
  if (!f.startsWith(RAIZ) || !fs.existsSync(f) || fs.statSync(f).isDirectory()) {
    res.writeHead(404); res.end('nao existe'); return;
  }
  res.writeHead(200, { 'content-type': TIPOS[path.extname(f)] || 'application/octet-stream' });
  res.end(fs.readFileSync(f));
});

// ------------------------------------------------------------ a base falsa
const UID = '11111111-1111-1111-1111-111111111111';
const OP = 'aaaaaaaa-0000-0000-0000-000000000001';
const AN = 'bbbbbbbb-0000-0000-0000-000000000001';

const V1 = {
  slug: 'example-sintra', title: 'Private Day in Sintra',
  kicker: 'Private day tour from Lisbon',
  lede: 'Eight hours through Sintra and along the coast.',
  city: 'Lisbon', countryName: 'Portugal', country: 'PT',
  durations: [{ h: '8h', price: 390, startTimes: ['08:30'],
    tiers: [{ max: 3, vehicle: 'Sedan', price: 390 },
            { max: 6, vehicle: 'Minivan', price: 490 }] }],
  stops: [{ when: '08:30', h: 'Your hotel', p: 'We collect you.' }],
  included: ['Private vehicle and driver'], notIncluded: 'Lunch.',
  faq: [['Group size?', 'Priced by vehicle.']], photos: []
};
const V2 = JSON.parse(JSON.stringify(V1));
V2.title = 'Private Day in Sintra & Cascais';
V2.lede = 'Nine hours through Sintra and along the Cascais coast.';
V2.durations[0].h = '9h';
V2.durations[0].tiers.push({ max: 8, vehicle: 'Van', price: 620 });
V2.stops.push({ when: '14:00', h: 'Cabo da Roca', p: 'The westernmost point.' });

const hoje = new Date();
const dia = (n) => {
  const d = new Date(hoje.getFullYear(), hoje.getMonth(), n);
  return d.toISOString().slice(0, 10);
};

function responder(url, metodo, corpo) {
  const u = new URL(url);
  const c = u.pathname;

  if (c === '/auth/v1/token' || c.startsWith('/auth/v1/otp')) return {};
  if (c === '/auth/v1/user') {
    return { id: UID, email: 'ricardo@example.invalid', aud: 'authenticated' };
  }
  if (c === '/rest/v1/rpc/is_admin') return true;
  if (c === '/rest/v1/rpc/marcar_dias') return 1;
  if (c === '/rest/v1/rpc/rever_versao') return null;
  if (c === '/rest/v1/rpc/submeter_versao') return 'cccccccc-0000-0000-0000-000000000001';

  if (c === '/rest/v1/operator_users') {
    return [{ operator_id: OP, role: 'owner',
      operators: { id: OP, name: 'Atlantic Private Tours',
                   status: 'approved', commission_rate: 0.2 } }];
  }
  if (c === '/rest/v1/listings') {
    if (metodo !== 'GET') return [{ id: AN, slug: 'example-sintra',
      status: 'draft', city: 'Lisbon', country: 'Portugal' }];
    return [{ id: AN, slug: 'example-sintra', status: 'live',
      city: 'Lisbon', country: 'Portugal',
      created_at: '2026-09-01T10:00:00Z',
      operators: { id: OP, name: 'Atlantic Private Tours',
                   status: 'approved', commission_rate: 0.2 } }];
  }
  if (c === '/rest/v1/listing_versions') {
    const q = u.searchParams.get('status') || '';
    const base = [
      { id: 'v2', listing_id: AN, version: 2, payload: V2, status: 'pending',
        submitted_at: '2026-10-02T21:00:00Z', review_note: null,
        listings: { id: AN, slug: 'example-sintra', status: 'live',
          city: 'Lisbon', country: 'Portugal',
          operators: { id: OP, name: 'Atlantic Private Tours',
                       status: 'approved', commission_rate: 0.2 } } },
      { id: 'v1', listing_id: AN, version: 1, payload: V1, status: 'approved',
        submitted_at: '2026-09-10T09:00:00Z', review_note: null }
    ];
    if (q.includes('pending'))  return base.filter(x => x.status === 'pending');
    if (q.includes('approved')) return base.filter(x => x.status === 'approved');
    return base;
  }
  if (c === '/rest/v1/rpc/dias_abertos') {
    var dd = corpo && corpo.p_de;
    if (RESPOSTA_DIAS === 'livre') return [{ day: dd, price: 520 }];
    if (RESPOSTA_DIAS === 'fechado') {
      // o dia pedido nao volta, mas os 90 seguintes voltam: o tour tem
      // calendario, aquele dia e que esta tomado
      return (corpo.p_ate !== corpo.p_de) ? [{ day: corpo.p_ate, price: null }] : [];
    }
    return [];   // 'sem calendario': nunca volta nada
  }
  if (c === '/rest/v1/availability') {
    return [{ day: dia(12), status: 'closed', price_override: null, seats_left: null },
            { day: dia(18), status: 'sold_out', price_override: null, seats_left: 0 },
            { day: dia(20), status: 'open', price_override: 520, seats_left: null }];
  }
  if (c === '/rest/v1/operator_applications') {
    if (metodo !== 'GET') return [];
    return [{ id: 'c1', company: 'Highland Private Drives',
      contact_name: 'A Contact', email: 'a@example.invalid',
      phone: '+44000', website: 'https://example.invalid',
      country: 'Scotland', city: 'Edinburgh', years: 11,
      licence_ref: 'X-0000',
      fleet: 'Two Mercedes V-Class for up to 6.',
      tours_text: 'Edinburgh to Glencoe and Loch Ness, leaving at seven.',
      status: 'new', created_at: '2026-10-01T08:00:00Z' }];
  }
  if (c === '/rest/v1/enquiries') {
    if (metodo !== 'GET') return [];
    return [{ id: 'p1', kind: 'date', listing_slug: 'example-sintra',
      wanted_on: dia(26), party: 4, name: 'An Enquiry',
      email: 'b@example.invalid', phone: '+353000',
      message: 'Four of us, can we add Cabo da Roca?',
      status: 'new', created_at: '2026-10-02T19:00:00Z' }];
  }
  return [];
}

// ---------------------------------------------------------------- correr
let RESPOSTA_DIAS = 'livre';
const erros = [];
const avisos = [];

const navegador = await chromium.launch();
await new Promise(r => servidor.listen(PORTA, r));

const ctx = await navegador.newContext({ viewport: { width: 1280, height: 1000 } });

// A sessao. O cliente guarda-a no localStorage com uma chave derivada do
// projeto; mete-se la antes de a pagina correr, para a pagina acordar ja
// com alguem autenticado.
await ctx.addInitScript(() => {
  const sessao = {
    access_token: 'falso.' + btoa(JSON.stringify({
      sub: '11111111-1111-1111-1111-111111111111',
      role: 'authenticated', exp: 9999999999
    })) + '.x',
    token_type: 'bearer', expires_in: 3600,
    expires_at: 9999999999, refresh_token: 'falso',
    user: { id: '11111111-1111-1111-1111-111111111111',
            email: 'ricardo@example.invalid', aud: 'authenticated',
            app_metadata: {}, user_metadata: {}, created_at: '2026-01-01' }
  };
  try {
    localStorage.setItem('sb-lmrvoakknsrypoeqmjbr-auth-token', JSON.stringify(sessao));
  } catch (e) {}
});

await ctx.route('**://*.supabase.co/**', async (rota) => {
  const req = rota.request();
  let corpo = null;
  try { corpo = req.postDataJSON(); } catch (e) {}
  const dados = responder(req.url(), req.method(), corpo);
  // Um pedido de contagem (`head: true`) nao leva corpo: a contagem vem
  // so do cabecalho content-range. Se o mock devolver o corpo e um
  // content-range de outro tamanho, mede-se o mock e nao a pagina.
  var n = Array.isArray(dados) ? dados.length : 1;
  var contagem = (req.headers()['prefer'] || '').indexOf('count=') >= 0
                 || req.method() === 'HEAD';
  await rota.fulfill({
    status: 200,
    contentType: 'application/json',
    headers: { 'access-control-allow-origin': '*',
               'access-control-allow-headers': '*',
               'access-control-allow-methods': '*',
               // Sem isto o browser recebe o content-range mas nao deixa
               // o JavaScript le-lo, e a contagem vem sempre a zero. E
               // o Supabase a serio manda este cabecalho.
               'access-control-expose-headers': 'content-range, content-length',
               'content-range': n ? '0-' + (n - 1) + '/' + n : '*/0' },
    body: contagem ? '' : JSON.stringify(dados)
  });
});

const pag = await ctx.newPage();
// O container nao chega ao Unsplash (politica de egresso), por isso as
// fotografias falham sempre aqui e falham so aqui. Contar isso como erro
// faria o teste reprovar toda a pagina que tem uma fotografia — e e
// precisamente para esse caso que existe a cor cheia por baixo.
const FORA = /unsplash|ERR_TUNNEL|ERR_NAME_NOT_RESOLVED|favicon/i;
pag.on('console', (m) => {
  if (m.type() === 'error' && !FORA.test(m.text())) erros.push(m.text());
  if (m.type() === 'warning') avisos.push(m.text());
});
pag.on('pageerror', (e) => {
  if (!FORA.test(e.message)) erros.push('pageerror: ' + e.message);
});

async function ver(nome, caminho, esperar, teste) {
  erros.length = 0;
  await pag.goto('http://localhost:' + PORTA + caminho,
                 { waitUntil: 'networkidle' });
  try {
    await pag.waitForSelector(esperar, { timeout: 6000 });
  } catch (e) {
    console.log('  FALHOU  ' + nome + ' — nao apareceu: ' + esperar);
    const t = await pag.locator('body').innerText();
    console.log('          ecra: ' + t.slice(0, 400).replace(/\n+/g, ' | '));
    if (erros.length) console.log('          erros: ' + erros.join(' / '));
    return false;
  }
  const r = teste ? await teste(pag) : [];
  const maus = (r || []).filter(x => x && x[1] === false).map(x => x[0]);
  if (erros.length) maus.push('erros de consola: ' + erros.join(' / '));
  if (maus.length) {
    console.log('  FALHOU  ' + nome);
    maus.forEach(m => console.log('          ' + m));
    return false;
  }
  console.log('  ok      ' + nome);
  return true;
}

console.log('\nAS PAGINAS DO PORTAL\n');
let bem = 0, total = 0;
async function t(...a) { total++; if (await ver(...a)) bem++; }

await t('a fila de revisao abre e mostra a submissao pendente',
  '/admin/', '.rv', async (p) => [
    ['titulo da versao nova', (await p.locator('.rv-n').first().innerText())
      .includes('Cascais')],
    ['diz que substitui a v1',
      (await p.locator('.rv-m').first().innerText()).includes('replacing v1')],
    ['a contagem de tours e 1 (mostra "'
       + (await p.locator('#n-tours').innerText()) + '")',
      (await p.locator('#n-tours').innerText()) === '1'],
    ['a diferenca mostra o titulo mudado',
      await p.locator('.dif-l:has-text("Title")').count() > 0],
    ['a diferenca mostra o preco mudado',
      await p.locator('.dif-l:has-text("Prices")').count() > 0],
    ['nao mostra como mudado o que nao mudou',
      await p.locator('.dif-l:has-text("Kicker")').count() === 0],
    ['a paragem nova aparece',
      (await p.locator('.dif-dentro').allInnerTexts()).join(' ')
        .includes('Cabo da Roca')],
    ['ha botao de aprovar e de devolver',
      await p.locator('[data-sim]').count() === 1 &&
      await p.locator('[data-nao]').count() === 1]
  ]);

await t('a fila nao deixa devolver sem razao escrita',
  '/admin/', '[data-nao]', async (p) => {
    await p.locator('[data-nao]').first().click();
    await p.waitForTimeout(300);
    const av = await p.locator('.rv-acoes .aviso').first();
    return [
      ['explica que falta a razao',
        (await av.innerText()).toLowerCase().includes('why')],
      ['o aviso fica visivel', await av.isVisible()]
    ];
  });

await t('a aba dos operadores mostra a candidatura',
  '/admin/', '.aba', async (p) => {
    await p.locator('#aba-ops').click();
    await p.waitForSelector('.rv-n', { timeout: 5000 });
    return [
      ['mostra a empresa',
        (await p.locator('.rv-n').first().innerText()).includes('Highland')],
      ['mostra o tour que eles descrevem',
        (await p.locator('.rv-c').first().innerText()).includes('Glencoe')],
      ['tem botao de aprovar', await p.locator('[data-cand]').count() === 1]
    ];
  });

await t('a aba dos pedidos mostra o pedido',
  '/admin/', '.aba', async (p) => {
    await p.locator('#aba-peds').click();
    await p.waitForSelector('table.tab', { timeout: 5000 });
    return [
      ['mostra quem perguntou',
        (await p.locator('table.tab').innerText()).includes('An Enquiry')],
      ['mostra a mensagem',
        (await p.locator('table.tab').innerText()).includes('Cabo da Roca')]
    ];
  });

await t('o painel do operador lista o anuncio',
  '/portal/', '.an-l', async (p) => [
    ['mostra o titulo',
      (await p.locator('.an-n').first().innerText()).includes('Sintra')],
    ['avisa que ha uma versao a espera',
      (await p.locator('.an-pend').first().innerText()).includes('Waiting for review')],
    ['o cabecalho do painel nao foi apagado',
      await p.locator('.pt-cab h1').count() === 1],
    ['conta 1 a espera',
      (await p.locator('.rs b').nth(2).innerText()) === '1']
  ]);

await t('o editor abre a ultima versao, nao a que esta no ar',
  '/portal/listing/?id=' + AN, '#titulo', async (p) => [
    ['abre a versao pendente',
      (await p.locator('#titulo').inputValue()).includes('Cascais')],
    ['tem os tres escaloes',
      await p.locator('#escaloes .rep-l').count() === 3],
    ['tem as duas paragens',
      await p.locator('#paragens .rep-l').count() === 2],
    ['mostra a comissao de 20%',
      (await p.locator('#conta').innerText()).includes('20%')],
    ['mostra o que o operador recebe no escalao mais baixo',
      (await p.locator('#conta').innerText()).includes('312')],
    ['mostra o historico de versoes',
      await p.locator('#hist .est').count() === 2]
  ]);

await t('o editor recusa submeter sem o obrigatorio',
  '/portal/listing/', '#titulo', async (p) => {
    await p.locator('#bt-submeter').click();
    await p.waitForTimeout(300);
    return [
      ['diz o que falta',
        (await p.locator('#av-ed').innerText()).length > 10],
      ['marca o campo como invalido',
        await p.locator('#titulo[aria-invalid="true"]').count() === 1]
    ];
  });

await t('o endereco web sugere-se a partir do titulo',
  '/portal/listing/', '#titulo', async (p) => {
    await p.locator('#titulo').fill('Private Tour: Ring of Kerry & Killarney');
    await p.waitForTimeout(200);
    return [['sugeriu o slug',
      (await p.locator('#slug').inputValue()) === 'private-tour-ring-of-kerry-killarney']];
  });

await t('o calendario desenha os dias e distingue os estados',
  '/portal/calendar/?tour=' + AN, '.dia[data-d]', async (p) => [
    ['ha dias desenhados', await p.locator('.dia[data-d]').count() >= 28],
    ['um dia fechado', await p.locator('.dia-closed').count() === 1],
    ['um dia esgotado', await p.locator('.dia-sold').count() === 1],
    ['um preco de dia aparece',
      (await p.locator('.dia .p').first().innerText()).includes('520')],
    ['o estado vai no aria-label e nao so na cor',
      (await p.locator('.dia-closed').getAttribute('aria-label')).includes('closed')],
    ['nao se pode mexer no passado',
      await p.locator('.dia[disabled]').count() > 0]
  ]);

await t('tocar num dia muda-o logo',
  '/portal/calendar/?tour=' + AN, '.dia[data-d]', async (p) => {
    const alvo = p.locator('.dia[data-d]:not([disabled])').first();
    const d = await alvo.getAttribute('data-d');
    await alvo.click();
    await p.waitForTimeout(400);
    return [['o dia ficou fechado',
      await p.locator('.dia[data-d="' + d + '"].dia-closed').count() === 1]];
  });

await t('a pagina de contacto abre com o tour e a data do endereco',
  '/contact/?tour=example-sintra&date=2026-11-20', '#f-ped', async (p) => [
    ['diz de que tour se trata',
      (await p.locator('#sobre').innerText()).includes('example sintra')],
    ['a data ja esta preenchida',
      (await p.locator('#quando').inputValue()) === '2026-11-20']
  ]);

await t('o contacto recusa um email incompleto',
  '/contact/', '#f-ped', async (p) => {
    await p.locator('#nome').fill('Ricardo');
    await p.locator('#email').fill('nao-e-um-email');
    await p.locator('#bt-ped').click();
    await p.waitForTimeout(300);
    return [['avisa', (await p.locator('#av-ped').innerText()).length > 5],
            ['marca o campo',
              await p.locator('#email[aria-invalid="true"]').count() === 1]];
  });

await t('a candidatura exige a descricao do tour',
  '/suppliers/apply/', '#f-cand', async (p) => {
    await p.locator('#empresa').fill('Alguma Empresa');
    await p.locator('#pessoa').fill('Alguem');
    await p.locator('#email').fill('a@b.com');
    await p.locator('#pais').fill('Portugal');
    await p.locator('#cidade').fill('Lisboa');
    await p.locator('#tours').fill('curto');
    await p.locator('#bt-cand').click();
    await p.waitForTimeout(300);
    return [['pede uma descricao a serio',
      (await p.locator('#av-cand').innerText()).toLowerCase().includes('describe')]];
  });

// ------------------------------------------------- a data, na pagina do tour
async function diaDiz(nome, modo, contem) {
  RESPOSTA_DIAS = modo;
  total++;
  if (await ver(nome, '/tours/cliffs-of-moher-galway/', '[data-data]',
    async (p) => {
      const d = new Date();
      d.setDate(d.getDate() + 30);
      await p.locator('[data-data]').fill(d.toISOString().slice(0, 10));
      await p.waitForTimeout(700);
      const t = await p.locator('[data-dia]').innerText();
      return [
        ['o aviso aparece', await p.locator('[data-dia]').isVisible()],
        ['diz "' + contem + '" (disse: "' + t.slice(0, 70) + '")',
          t.toLowerCase().includes(contem.toLowerCase())]
      ];
    })) bem++;
}

await diaDiz('a data livre diz que esta aberta', 'livre', 'that day is open');
await diaDiz('a data fechada diz que esta tomada', 'fechado', 'that day is taken');
await diaDiz('sem calendario nao afirma nada', 'sem', 'we confirm this date');
RESPOSTA_DIAS = 'livre';

// Em ecra pequeno, que e onde o operador vai mesmo usar isto.
await pag.setViewportSize({ width: 390, height: 844 });
await t('o calendario e usavel no telemovel',
  '/portal/calendar/?tour=' + AN, '.dia[data-d]', async (p) => {
    const c = await p.locator('.dia[data-d]:not([disabled])').first().boundingBox();
    const rolo = await p.evaluate(() =>
      document.documentElement.scrollWidth > window.innerWidth + 1);
    return [
      ['os dias tem pelo menos 40px de lado', c.width >= 40 && c.height >= 40],
      ['a pagina nao rola para o lado', rolo === false]
    ];
  });

await t('a fila de revisao e usavel no telemovel',
  '/admin/', '.rv', async (p) => {
    const culpado = await p.evaluate(() => {
      const L = window.innerWidth;
      let pior = null;
      document.querySelectorAll('*').forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.right > L + 1 && (!pior || r.right > pior.right)) {
          pior = { right: Math.round(r.right),
                   quem: el.tagName.toLowerCase() + '.' + (el.className || ''),
                   texto: (el.textContent || '').slice(0, 60) };
        }
      });
      return { largura: L, scroll: document.documentElement.scrollWidth, pior: pior };
    });
    if (culpado.pior) {
      console.log('          estica: ' + culpado.pior.quem
        + ' ate ' + culpado.pior.right + 'px (ecra ' + culpado.largura + ')');
    }
    return [['a pagina nao rola para o lado',
      culpado.scroll <= culpado.largura + 1]];
  });

console.log('\n' + bem + '/' + total + ' passaram\n');

await navegador.close();
servidor.close();
process.exit(bem === total ? 0 : 1);
