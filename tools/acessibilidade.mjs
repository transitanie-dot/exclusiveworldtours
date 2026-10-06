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

  // A cotacao e a confirmacao, para o axe poder ver o formulario com o
  // preco preenchido e a pagina de confirmacao com as linhas todas — e
  // nao a pagina vazia a dizer "One moment".
  if (c === '/rest/v1/rpc/agenda_do_operador') {
    return [{ reference: 'EWAAAA22', tour_title: 'Private Day in Sintra',
      booking_date: '2026-12-01', start_time: '08:30:00', pax: 2,
      vehicle_name: 'Sedan', customer_name: 'Maria Oliveira',
      customer_phone: '+351 900 000 000', pickup: 'Hotel Avenida',
      notes: 'One child seat.', you_receive: 444.00, status: 'paid',
      paid_out: false }];
  }
  if (c === '/rest/v1/rpc/reservas_a_convidar') {
    return [{ booking_id: '77777777-0000-0000-0000-000000000007',
      reference: 'EWCCCC44', tour_title: 'Private Day in Sintra',
      booking_date: '2026-09-20', customer_name: 'Ana Pires',
      customer_email: 'ana@example.invalid' }];
  }
  if (c === '/rest/v1/rpc/a_pagar') {
    return [{ operator_id: OP, operator_name: 'Atlantic Private Tours',
      operator_email: 'ops@example.invalid', reservas: 3, total: 1236.00,
      mais_antiga: '2026-09-20' }];
  }
  if (c === '/rest/v1/bookings') {
    return [{ id: '88888888-0000-0000-0000-000000000008',
      reference: 'EWEEEE66', listing_slug: 'example-sintra',
      tour_title: 'Private Day in Sintra', booking_date: '2099-12-01',
      start_time: '08:30:00', pax: 2, vehicle_name: 'Sedan',
      price_total: 555, currency: 'EUR', commission_rate: 0.2,
      platform_amount: 111, operator_amount: 444, payment_mode: 'later',
      status: 'confirmed', charge_at: '2099-11-28T08:30:00Z',
      charge_attempts: 0, stripe_payment_method_id: null,
      customer_name: 'Maria Oliveira', customer_email: 'maria@example.invalid',
      customer_phone: '+351 900 000 000', pickup: 'Hotel Avenida',
      notes: null, payout_at: null, cancel_reason: null }];
  }
  if (c === '/rest/v1/rpc/cotar') {
    return { ok: true, slug: 'example-sintra', title: 'Private Day in Sintra',
      operator: 'Atlantic Private Tours', date: '2026-12-01', time: null,
      pax: 2, vehicle: 'Sedan', maxPax: 6, price: 555, currency: 'EUR',
      hoursToStart: 900, payLater: true };
  }
  if (c === '/functions/v1/sessao') {
    return { confirmed: true, payment_mode: 'later', reference: 'EWABCD23',
      tour: 'Private Day in Sintra', operator: 'Atlantic Private Tours',
      date: '2026-12-01', time: '08:30', pax: 2, amount: 555,
      currency: 'EUR', email: 'cliente@example.invalid' };
  }
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
      country: 'Portugal', created_at: '2026-09-01', schedule_mode: 'departures',
      listing_versions: [{ payload: V }],
      operators: { id: OP, name: 'Atlantic Private Tours', status: 'approved', commission_rate: 0.2 } }];
  }
  // As epocas. Duas, de proposito: uma a decorrer e uma ja terminada —
  // a terminada e que faz aparecer o estado "ended", que e o que o axe
  // tem de ver com contraste suficiente nos dois temas.
  // A fita do ano pergunta que dias estao abertos nos proximos 12
  // meses. Devolvem-se os dias uteis de uns meses e NENHUM de outros,
  // para a fita ter buracos a serio: e com buracos que ela mostra o
  // aviso, e e o aviso que o axe tem de ver.
  if (c === '/rest/v1/rpc/dias_abertos') {
    const out = [];
    const h = new Date();
    for (let i = 0; i < 365; i++) {
      const d = new Date(h.getFullYear(), h.getMonth(), h.getDate() + i);
      const m = d.getMonth();
      if (m === 0 || m === 1) continue;          // dois meses sem nada
      const dow = d.getDay();
      if (dow === 0 || dow === 6) continue;      // so dias uteis
      out.push({ dia: d.toISOString().slice(0, 10) });
    }
    return out;
  }
  if (c === '/rest/v1/listing_seasons') {
    return [{ id: 'ep1', starts_on: '2026-06-01', ends_on: null,
      weekdays: [1, 2, 3, 4, 5], opens_at: null, closes_at: null,
      note: 'Summer, two drivers',
      season_times: [{ starts_at: '09:00:00' }, { starts_at: '14:00:00' }] },
      { id: 'ep2', starts_on: '2025-06-01', ends_on: '2025-09-30',
      weekdays: [6, 7], opens_at: null, closes_at: null, note: null,
      season_times: [{ starts_at: '10:00:00' }] }];
  }
  if (c === '/rest/v1/listing_versions') {
    return [{ id: 'v2', listing_id: AN, version: 2, payload: V, status: 'pending',
      submitted_at: '2026-10-02T21:00:00Z',
      listings: { id: AN, slug: 'exemplo', status: 'live', city: 'Lisbon',
        country: 'Portugal',
        operators: { id: OP, name: 'Atlantic Private Tours', status: 'approved', commission_rate: 0.2 } } }];
  }
  if (c === '/rest/v1/meeting_points') {
    return [{ id: 'mp1', operator_id: OP, name: 'Molly Malone statue',
      address: 'Suffolk Street, Dublin 2', lat: 53.3438, lng: -6.2597,
      instructions: 'On the corner by the kiosk.',
      photo_url: 'https://exemplo.invalid/ponto.jpg' }];
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
  ['epocas', '/portal/seasons/', '.ep-f'],
  ['calendario', '/portal/calendar/?tour=' + AN, '.hora'],
  ['conta do operador', '/portal/account/', '.ct .cx'],
  ['frota', '/portal/fleet/', '.vd[data-d]'],
  ['pontos de encontro', '/portal/places/', '.p[data-p]'],
  ['fila de revisao', '/admin/', '.rv'],
  ['operadores', '/admin/operators/', 'table.tab'],
  ['procuras', '/admin/searches/', '.cx'],
  ['agenda do operador', '/portal/bookings/', '.ag-soma'],
  ['reservas no admin', '/admin/bookings/', '.rb'],
  // A reserva confirmada: o estado que o cliente ve a seguir a pagar, e
  // nao o "One moment" de antes da resposta.
  ['reserva confirmada',
   '/booking-confirmed/?session_id=cs_test_abcdefghij1234567890',
   '[data-detalhe]:not([hidden])']
];

const TAMANHOS = [[1440, 900], [768, 1024], [390, 844]];

// Os dois temas. O escuro nao e um extra: desde que o portal passou a
// ter fichas de cor, metade das paginas que uma pessoa ve e a versao
// escura — e um tema que ninguem testa apodrece sem se dar por isso.
// Ja aconteceu uma vez: o titulo "Operator sign-in" saiu verde-escuro
// sobre verde-escuro e so se viu num screenshot, porque o axe corria
// so em claro.
//
// O escuro corre no ecra largo e no telemovel, nao nos tres: o do meio
// nao mostrava nada que os outros dois nao mostrem, e duplicar o tempo
// todo de uma verificacao que ja demora e como se garante que ela
// deixa de ser corrida.
const TEMAS = [
  ['claro',  'light', TAMANHOS],
  ['escuro', 'dark',  [TAMANHOS[0], TAMANHOS[2]]]
];

const navegador = await chromium.launch();
await new Promise(r => servidor.listen(PORTA, r));

let violacoes = 0, verificadas = 0;

for (const [nome, caminho, esperar] of PAGINAS) {
 for (const [tema, esquema, tamanhos] of TEMAS) {
  const ctx = await navegador.newContext({ colorScheme: esquema });
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
  for (const [l, a] of tamanhos) {
    await pag.setViewportSize({ width: l, height: a });
    await pag.goto('http://localhost:' + PORTA + caminho, { waitUntil: 'networkidle' });
    if (esperar) {
      try { await pag.waitForSelector(esperar, { timeout: 6000 }); }
      catch (e) {
        console.log('  ?  ' + nome + ' @' + l + '/' + tema + ' — nao chegou a ' + esperar);
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
      console.log('  FALHA  ' + nome + ' @' + l + 'px / ' + tema);
      r.violations.forEach(v => {
        console.log('         [' + v.impact + '] ' + v.id + ' — ' + v.help);
        v.nodes.slice(0, 3).forEach(n2 =>
          console.log('           ' + n2.html.slice(0, 120).replace(/\n/g, ' ')));
      });
    } else {
      console.log('  ok     ' + nome + ' @' + l + 'px / ' + tema);
    }
  }
  await ctx.close();
 }
}

console.log('\n' + verificadas + ' verificacoes, ' + violacoes + ' violacoes WCAG 2.1 AA\n');
await navegador.close();
servidor.close();
process.exit(violacoes ? 1 : 0);
