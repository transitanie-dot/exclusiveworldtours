// O axe sobre as paginas geradas, nos tamanhos que importam.
//
// Corre com a base simulada, como o testar_portal.mjs, porque uma pagina
// do portal antes de os dados chegarem e um ecra "Loading" — e nao e
// disso que vale a pena saber a acessibilidade.
//
//   node tools/acessibilidade.mjs

import pw from '/opt/npm-tools/node_modules/playwright/index.js';
const { chromium } = pw;
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const RAIZ = process.cwd();
const PORTA = 8098;
const AXE = fs.readFileSync(path.join(RAIZ, 'node_modules/axe-core/axe.min.js'), 'utf8');

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

const UID = '11111111-1111-1111-1111-111111111111';
const OP = 'aaaaaaaa-0000-0000-0000-000000000001';
const AN = 'bbbbbbbb-0000-0000-0000-000000000001';
const V = {
  slug: 'exemplo', title: 'Private Day in Sintra', kicker: 'From Lisbon',
  lede: 'Eight hours through Sintra and along the coast, in a vehicle that carries nobody but your group.',
  city: 'Lisbon', countryName: 'Portugal', country: 'PT',
  durations: [{ h: '8h', price: 390, startTimes: ['08:30'],
    tiers: [{ max: 3, vehicle: 'Sedan', price: 390 },
            { max: 6, vehicle: 'Minivan', price: 490 }] }],
  stops: [{ when: '08:30', h: 'Your hotel', p: 'We collect you.' }],
  included: ['Private vehicle and driver'], notIncluded: 'Lunch.',
  faq: [['Group size?', 'Priced by vehicle.']], photos: []
};

function responder(url) {
  const c = new URL(url).pathname;
  if (c === '/auth/v1/user') return { id: UID, email: 'ricardo@example.invalid', aud: 'authenticated' };
  if (c === '/rest/v1/rpc/is_admin') return true;
  if (c === '/rest/v1/operator_users') {
    return [{ operator_id: OP, role: 'owner',
      operators: { id: OP, name: 'Atlantic Private Tours', status: 'approved', commission_rate: 0.2 } }];
  }
  if (c === '/rest/v1/operators') {
    return [{ id: OP, name: 'Atlantic Private Tours', legal_name: 'Atlantic Lda',
      city: 'Lisbon', country: 'Portugal', email: 'a@example.invalid',
      phone: '+351000', website: 'https://example.invalid',
      status: 'approved', commission_rate: 0.2, listings: [{ id: AN, status: 'live' }],
      created_at: '2026-01-01' }];
  }
  if (c === '/rest/v1/listings') {
    return [{ id: AN, slug: 'exemplo', status: 'live', city: 'Lisbon',
      country: 'Portugal', created_at: '2026-09-01',
      operators: { id: OP, name: 'Atlantic Private Tours', status: 'approved', commission_rate: 0.2 } }];
  }
  if (c === '/rest/v1/listing_versions') {
    return [{ id: 'v2', listing_id: AN, version: 2, payload: V, status: 'pending',
      submitted_at: '2026-10-02T21:00:00Z',
      listings: { id: AN, slug: 'exemplo', status: 'live', city: 'Lisbon',
        country: 'Portugal',
        operators: { id: OP, name: 'Atlantic Private Tours', status: 'approved', commission_rate: 0.2 } } }];
  }
  if (c === '/rest/v1/listing_times') {
    return [{ starts_at: '08:00:00' }, { starts_at: '17:00:00' }];
  }
  if (c === '/rest/v1/vehicles') {
    return [{ id: 'vv1', name: 'Mercedes V-Class', max_pax: 6,
      plate: '191-D-1234', active: true, listing_vehicles: [{ listing_id: AN }] },
      { id: 'vv2', name: 'Skoda Superb', max_pax: 3, plate: null,
        active: true, listing_vehicles: [] }];
  }
  if (c === '/rest/v1/vehicle_days') {
    const d = new Date();
    const dia = (n) => new Date(d.getFullYear(), d.getMonth(), n).toISOString().slice(0, 10);
    return [{ day: dia(14), status: 'booked' }, { day: dia(21), status: 'closed' }];
  }
  if (c === '/rest/v1/listing_vehicles') return [];
  if (c === '/rest/v1/availability') {
    const d = new Date();
    const dia = (n) => new Date(d.getFullYear(), d.getMonth(), n).toISOString().slice(0, 10);
    return [{ day: dia(14), status: 'closed' }, { day: dia(19), status: 'sold_out' }];
  }
  if (c === '/rest/v1/operator_applications') {
    return [{ id: 'c1', company: 'Highland Private Drives', contact_name: 'A Contact',
      email: 'a@example.invalid', country: 'Scotland', city: 'Edinburgh',
      years: 11, fleet: 'Two vans.', tours_text: 'Edinburgh to Glencoe.',
      status: 'new', created_at: '2026-10-01' }];
  }
  if (c === '/rest/v1/enquiries') {
    return [{ id: 'p1', kind: 'date', listing_slug: 'exemplo', wanted_on: '2026-11-20',
      party: 4, name: 'An Enquiry', email: 'b@example.invalid',
      message: 'Four of us.', status: 'new', created_at: '2026-10-02' }];
  }
  if (c === '/rest/v1/search_queries') {
    return [{ q: 'marrakech', results: 0, city_match: null, country: null, created_at: '2026-10-01' },
            { q: 'dublin', results: 6, city_match: 'Dublin', country: 'Ireland', created_at: '2026-10-02' }];
  }
  return [];
}

const PAGINAS = [
  ['a homepage', '/', null],
  ['todos os tours', '/tours/', null],
  ['uma pagina de tour', '/tours/cliffs-of-moher-galway/', null],
  ['para operadores', '/suppliers/', null],
  ['candidatura', '/suppliers/apply/', '#f-cand'],
  ['contacto', '/contact/', '#f-ped'],
  ['entrada do portal', '/portal/', '#entrada'],
  ['painel do operador', '/portal/', '.an-l'],
  ['editor de anuncio', '/portal/listing/?id=' + AN, '#titulo'],
  ['calendario', '/portal/calendar/?tour=' + AN, '.hora'],
  ['conta do operador', '/portal/account/', '.ct .cx'],
  ['frota', '/portal/fleet/', '.vd[data-d]'],
  ['fila de revisao', '/admin/', '.rv'],
  ['operadores', '/admin/operators/', 'table.tab'],
  ['procuras', '/admin/searches/', '.cx']
];

const TAMANHOS = [[1440, 900], [768, 1024], [390, 844]];

const navegador = await chromium.launch();
await new Promise(r => servidor.listen(PORTA, r));

let violacoes = 0, verificadas = 0;

for (const [nome, caminho, esperar] of PAGINAS) {
  const ctx = await navegador.newContext();
  await ctx.addInitScript(() => {
    const s = {
      access_token: 'falso.' + btoa(JSON.stringify({
        sub: '11111111-1111-1111-1111-111111111111', role: 'authenticated', exp: 9999999999 })) + '.x',
      token_type: 'bearer', expires_in: 3600, expires_at: 9999999999,
      refresh_token: 'falso',
      user: { id: '11111111-1111-1111-1111-111111111111',
        email: 'ricardo@example.invalid', aud: 'authenticated',
        app_metadata: {}, user_metadata: {}, created_at: '2026-01-01' }
    };
    try { localStorage.setItem('sb-lmrvoakknsrypoeqmjbr-auth-token', JSON.stringify(s)); } catch (e) {}
  });
  // A entrada do portal tem de ser vista SEM sessao, senao nunca aparece.
  if (nome === 'entrada do portal') {
    await ctx.addInitScript(() => { try { localStorage.clear(); } catch (e) {} });
  }
  await ctx.route('**://*.supabase.co/**', async (rota) => {
    const dados = responder(rota.request().url());
    const n = Array.isArray(dados) ? dados.length : 1;
    const contagem = (rota.request().headers()['prefer'] || '').includes('count=');
    await rota.fulfill({ status: 200, contentType: 'application/json',
      headers: { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*',
        'access-control-expose-headers': 'content-range',
        'content-range': n ? '0-' + (n - 1) + '/' + n : '*/0' },
      body: contagem ? '' : JSON.stringify(dados) });
  });

  const pag = await ctx.newPage();
  for (const [l, a] of TAMANHOS) {
    await pag.setViewportSize({ width: l, height: a });
    await pag.goto('http://localhost:' + PORTA + caminho, { waitUntil: 'networkidle' });
    if (esperar) {
      try { await pag.waitForSelector(esperar, { timeout: 6000 }); }
      catch (e) {
        console.log('  ?  ' + nome + ' @' + l + ' — nao chegou a ' + esperar);
        continue;
      }
    }
    await pag.addScriptTag({ content: AXE });
    const r = await pag.evaluate(async () => await window.axe.run(document, {
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] }
    }));
    verificadas++;
    if (r.violations.length) {
      violacoes += r.violations.length;
      console.log('  FALHA  ' + nome + ' @' + l + 'px');
      r.violations.forEach(v => {
        console.log('         [' + v.impact + '] ' + v.id + ' — ' + v.help);
        v.nodes.slice(0, 3).forEach(n2 =>
          console.log('           ' + n2.html.slice(0, 120).replace(/\n/g, ' ')));
      });
    } else {
      console.log('  ok     ' + nome + ' @' + l + 'px');
    }
  }
  await ctx.close();
}

console.log('\n' + verificadas + ' verificacoes, ' + violacoes + ' violacoes WCAG 2.1 AA\n');
await navegador.close();
servidor.close();
process.exit(violacoes ? 1 : 0);
