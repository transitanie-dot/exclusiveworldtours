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

// O CENARIO DO PAGAMENTO
//
// A cotar() e a reservar() mudam de resposta de teste para teste — um
// dia fechado, um "pagar depois" recusado, o Stripe que nao abre — e e
// precisamente isso que precisa de ser verificado. Os testes escrevem
// aqui antes de navegar.
//
// O preco e 555 e os escaloes da pagina dizem 390 e 490 DE PROPOSITO: e
// a unica forma de provar que o numero que a pessoa ve veio da base e
// nao de uma multiplicacao feita no browser.
let CENARIO = {};

function cenarioPadrao() {
  CENARIO = {
    cotar: {
      ok: true, slug: 'example-sintra', title: 'Private Day in Sintra',
      operator: 'Atlantic Private Tours', version: 1,
      date: '2026-12-01', time: null, pax: 2, vehicle: 'Sedan',
      maxPax: 6, price: 555, currency: 'EUR', hoursToStart: 900,
      payLater: true, payLaterReason: null, payLaterCode: null
    },
    // O MANIFESTO DO QUE ESTA PUBLICADO
    //
    // Nao vem do Supabase: e um ficheiro do site, escrito pelo gerador.
    // Por isso tem rota propria. `null` faz o pedido falhar, que e o caso
    // em que o portal se tem de CALAR sobre o site em vez de adivinhar.
    // Faz a v2 passar de 'pending' a 'approved'. E a unica forma honesta
    // de encenar "o site esta atrasado": a base tem a v2 aprovada e o
    // manifesto ainda diz v1.
    aprovadaV2: false,
    publicado: {
      gerado_em: '2026-10-05T12:00:00Z',
      tours: { 'example-sintra': { versao: 1, url: '/tours/example-sintra/' } }
    },
    // null = deixa responder o mock que ja existia.
    horas: null,
    reservar: { ok: true, url: 'http://localhost:' + PORTA + '/cancellation/',
                reference: 'EWABCD23', payment_mode: 'now', hold_minutes: 30 },
    reservarEstado: 200,
    // A AGENDA DO OPERADOR
    //
    // A agenda_do_operador() nao devolve price_total nem commission_rate,
    // e o mock tambem nao os devolve: se devolvesse, o teste que prova
    // que a pagina nao os mostra passava por o mock nao os ter mandado e
    // nao por a pagina nao os mostrar.
    agenda: [
      { reference: 'EWAAAA22', tour_title: 'Private Day in Sintra',
        booking_date: '2026-12-01', start_time: '08:30:00', pax: 2,
        vehicle_name: 'Sedan', customer_name: 'Maria Oliveira',
        customer_phone: '+351 900 000 000', pickup: 'Hotel Avenida',
        notes: 'One child seat.', you_receive: 444.00,
        status: 'paid', paid_out: false },
      { reference: 'EWBBBB33', tour_title: 'Private Day in Sintra',
        booking_date: '2026-12-09', start_time: null, pax: 4,
        vehicle_name: 'Minivan', customer_name: 'John Reed',
        customer_phone: null, pickup: null, notes: null,
        you_receive: 392.00, status: 'confirmed', paid_out: false }
    ],
    aConvidar: [
      { booking_id: '77777777-0000-0000-0000-000000000007',
        reference: 'EWCCCC44', tour_title: 'Private Day in Sintra',
        booking_date: '2026-09-20', customer_name: 'Ana Pires',
        customer_email: 'ana@example.invalid' }
    ],
    aPagar: [
      { operator_id: OP, operator_name: 'Atlantic Private Tours',
        operator_email: 'ops@example.invalid', reservas: 3,
        total: 1236.00, mais_antiga: '2026-09-20' }
    ],
    token: '12345678-1234-1234-1234-123456789abc',
    cancelar: { ok: true, reference: 'EWDDDD55', was: 'paid', charged: true,
                payment_intent: 'pi_3Exemplo', amount: 555 },
    // A tabela das reservas, como o admin a le. Uma 'later' confirmada
    // SEM cartao guardado, que e o caso que ninguem ve a tempo.
    reservasTabela: [
      { id: '88888888-0000-0000-0000-000000000008', reference: 'EWEEEE66',
        listing_slug: 'example-sintra', tour_title: 'Private Day in Sintra',
        booking_date: '2099-12-01', start_time: '08:30:00', pax: 2,
        vehicle_name: 'Sedan', price_total: 555, currency: 'EUR',
        commission_rate: 0.2, platform_amount: 111, operator_amount: 444,
        payment_mode: 'later', status: 'confirmed',
        charge_at: '2099-11-28T08:30:00Z', charge_attempts: 0,
        stripe_payment_method_id: null,
        customer_name: 'Maria Oliveira', customer_email: 'maria@example.invalid',
        customer_phone: '+351 900 000 000', pickup: 'Hotel Avenida',
        notes: null, payout_at: null, cancel_reason: null }
    ],
    sessao: {
      confirmed: true, payment_mode: 'now', reference: 'EWABCD23',
      tour: 'Private Day in Sintra', operator: 'Atlantic Private Tours',
      date: '2026-12-01', time: '08:30', pax: 2, amount: 555,
      currency: 'EUR', email: 'cliente@example.invalid'
    }
  };
}
cenarioPadrao();

function responder(url, metodo, corpo) {
  const u = new URL(url);
  const c = u.pathname;

  if (c === '/rest/v1/rpc/cotar') return CENARIO.cotar;
  if (c === '/rest/v1/rpc/agenda_do_operador') return CENARIO.agenda;
  if (c === '/rest/v1/rpc/reservas_a_convidar') return CENARIO.aConvidar;
  if (c === '/rest/v1/rpc/a_pagar') return CENARIO.aPagar;
  if (c === '/rest/v1/rpc/convidar_por_reserva') return CENARIO.token;
  if (c === '/rest/v1/rpc/cancelar_reserva') return CENARIO.cancelar;
  if (c === '/rest/v1/rpc/marcar_pago') return 2;
  if (c === '/rest/v1/bookings') return CENARIO.reservasTabela;
  // So responde aqui se o cenario do pagamento tiver posto horas. A
  // partidas_no_dia ja tinha um mock em baixo, usado pelos testes do
  // painel do tour, e responder aqui sempre tapava-o — foi exatamente
  // o que aconteceu, e dois testes que passavam comecaram a falhar.
  if (c === '/rest/v1/rpc/partidas_no_dia' && Array.isArray(CENARIO.horas)) {
    return CENARIO.horas;
  }
  if (c === '/functions/v1/reservar') return CENARIO.reservar;
  if (c === '/functions/v1/sessao') return CENARIO.sessao;

  if (c === '/auth/v1/token') return { access_token: 'x', token_type: 'bearer',
    expires_in: 3600, refresh_token: 'y',
    user: { id: UID, email: 'ricardo@example.invalid', aud: 'authenticated' } };
  if (c.startsWith('/auth/v1/otp')) return {};
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
    const linha = { id: AN, slug: 'example-sintra', status: 'live',
      city: 'Lisbon', country: 'Portugal', meeting_point_id: 'mp1',
      created_at: '2026-09-01T10:00:00Z',
      operators: { id: OP, name: 'Atlantic Private Tours',
                   status: 'approved', commission_rate: 0.2 } };
    // A relacao incorporada, quando o select a pede. Sem isto o aviso do
    // admin ("aprovado e nao publicado") nunca encontrava nada e ficava
    // sempre a dizer que o site estava em dia — um teste a medir o mock.
    if ((u.searchParams.get('select') || '').indexOf('listing_versions') > -1) {
      linha.listing_versions = CENARIO.aprovadaV2
        ? [{ version: 1, status: 'approved' }, { version: 2, status: 'approved' }]
        : [{ version: 1, status: 'approved' }, { version: 2, status: 'pending' }];
    }
    return [linha];
  }
  if (c === '/rest/v1/listing_versions') {
    const q = u.searchParams.get('status') || '';
    const base = [
      { id: 'v2', listing_id: AN, version: 2, payload: V2,
        status: CENARIO.aprovadaV2 ? 'approved' : 'pending',
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
  if (c === '/rest/v1/vehicles') {
    if (metodo !== 'GET') return [{ id: 'vv1' }];
    return [
      { id: 'vv1', name: 'Mercedes V-Class', max_pax: 6, plate: '191-D-1234',
        active: true, listing_vehicles: [{ listing_id: AN }] },
      { id: 'vv2', name: 'Skoda Superb', max_pax: 3, plate: null,
        active: true, listing_vehicles: [] }
    ];
  }
  if (c === '/rest/v1/vehicle_days') {
    return [{ day: dia(14), status: 'booked', note: null },
            { day: dia(21), status: 'closed', note: 'oficina' }];
  }
  if (c === '/rest/v1/listing_vehicles') return [];
  if (c === '/rest/v1/rpc/marcar_veiculo') return 1;
  if (c === '/rest/v1/reviews') {
    if (metodo !== 'GET') return [];
    return [
      { id: 'rv1', listing_id: AN, rating: 5, title: 'A day we will remember',
        body: 'The driver knew where the light would be good.',
        author_name: 'Maria', author_country: 'Brazil',
        travelled_on: '2026-09-20', reply: null, state: 'published' },
      { id: 'rv2', listing_id: AN, rating: 2, title: 'Late and rushed',
        body: 'We left forty minutes late and lost the first stop.',
        author_name: 'Tom', author_country: null,
        travelled_on: '2026-09-02',
        reply: 'You are right and I am sorry \u2014 the van had a flat.',
        state: 'published' }
    ];
  }
  if (c === '/rest/v1/review_invites') {
    if (metodo !== 'GET') return [];
    return [{ enquiry_id: 'p1', token: 'tok-1', used_at: null }];
  }
  if (c === '/rest/v1/rpc/convidar_avaliacao') return 'tok-novo';
  if (c === '/rest/v1/rpc/responder_avaliacao') return null;
  if (c === '/rest/v1/rpc/convite') {
    if (RESPOSTA_CONVITE === 'valido') {
      return [{ valido: true, motivo: null, tour: 'Private Day in Sintra',
                slug: 'example-sintra', travelled_on: '2026-09-20',
                first_name: 'Maria' }];
    }
    if (RESPOSTA_CONVITE === 'usado') {
      return [{ valido: false, motivo: 'used', tour: 'x', slug: 'x',
                travelled_on: null, first_name: null }];
    }
    if (RESPOSTA_CONVITE === 'expirado') {
      return [{ valido: false, motivo: 'expired', tour: 'x', slug: 'x',
                travelled_on: null, first_name: null }];
    }
    return [];
  }
  if (c === '/rest/v1/rpc/deixar_avaliacao') return 'rv-novo';
  if (c === '/rest/v1/meeting_points') {
    if (metodo !== 'GET') return [{ id: 'mp1' }];
    return [{ id: 'mp1', operator_id: OP, name: 'Molly Malone statue',
      address: 'Suffolk Street, Dublin 2', lat: 53.3438, lng: -6.2597,
      instructions: 'On the corner by the kiosk, not the main door.',
      photo_url: 'https://exemplo.invalid/ponto.jpg' },
      { id: 'mp2', operator_id: OP, name: 'Heuston Station',
        address: null, lat: null, lng: null, instructions: null,
        photo_url: null }];
  }
  if (c === '/rest/v1/listing_times') {
    if (metodo !== 'GET') return [];
    return [{ starts_at: '08:00:00' }, { starts_at: '17:00:00' }];
  }
  if (c === '/rest/v1/rpc/definir_partidas') return 2;
  if (c === '/rest/v1/rpc/partidas_no_dia') {
    if (RESPOSTA_DIAS === 'livre') return [{ starts_at: '17:00:00' }];
    return [];
  }
  if (c === '/rest/v1/rpc/frota_no_dia') {
    if (RESPOSTA_DIAS === 'livre') {
      return [{ disponivel: true, veiculos: 2, max_pax: 6, price: 520,
                lead_time_hours: 24 }];
    }
    if (RESPOSTA_DIAS === 'fechado') {
      return [{ disponivel: false, veiculos: 0, max_pax: null, price: null,
                lead_time_hours: 24 }];
    }
    if (RESPOSTA_DIAS === 'cedo') {
      return [{ disponivel: false, veiculos: 2, max_pax: 6, price: null,
                lead_time_hours: 72 }];
    }
    return [];   // 'sem': o tour nao esta ligado a um operador
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
let RESPOSTA_CONVITE = 'valido';
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

// O /assets/publicado.json e um ficheiro do site, e o servidor de teste
// serve o que esta no repositorio. Para os testes poderem encenar "o
// site esta atrasado" ou "o manifesto nao carrega", interceta-se aqui.
await ctx.route('**/assets/publicado.json', async (rota) => {
  if (CENARIO.publicado === null) {
    await rota.fulfill({ status: 503, body: 'indisponivel' });
    return;
  }
  await rota.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify(CENARIO.publicado)
  });
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
    // Quase tudo responde 200. A excecao e a Edge Function do pagamento:
    // o teste do Stripe em baixo
    // precisa de um 502 para provar que a pagina mostra a mensagem dela
    // em vez de uma pagina em branco.
    status: req.url().includes('/functions/v1/reservar')
            ? CENARIO.reservarEstado : 200,
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

// O quinto argumento: um padrao de erros de consola que ESTE teste
// provoca de proposito. Sem ele, um teste que prova que a pagina se
// porta bem quando a rede devolve 502 reprovava por causa do 502 que
// ele mesmo pediu. Alargar o FORA global seria pior: passava a tapar
// um 502 de verdade em qualquer outra pagina.
async function ver(nome, caminho, esperar, teste, esperados) {
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
  const sobram = esperados ? erros.filter(x => !esperados.test(x)) : erros;
  if (sobram.length) maus.push('erros de consola: ' + sobram.join(' / '));
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

// ------------------------------------------------------------- a entrada
//
// Estes correm sem sessao: com sessao a pagina mostra o painel e o ecra
// de entrada nunca aparece. E uma janela separada, nao um apagar a meio.
async function semSessao(nome, teste) {
  total++;
  const c2 = await navegador.newContext({ viewport: { width: 1280, height: 1000 } });
  await c2.route('**://*.supabase.co/**', async (rota) => {
    const req = rota.request();
    let corpo = null;
    try { corpo = req.postDataJSON(); } catch (e) {}
    const dados = responder(req.url(), req.method(), corpo);
    const n = Array.isArray(dados) ? dados.length : 1;
    await rota.fulfill({ status: 200, contentType: 'application/json',
      headers: { 'access-control-allow-origin': '*',
                 'access-control-allow-headers': '*',
                 'access-control-expose-headers': 'content-range',
                 'content-range': n ? '0-' + (n - 1) + '/' + n : '*/0' },
      body: JSON.stringify(dados) });
  });
  const p2 = await c2.newPage();
  await p2.goto('http://localhost:' + PORTA + '/portal/', { waitUntil: 'networkidle' });
  try {
    await p2.waitForSelector('#entrada', { timeout: 6000 });
  } catch (e) {
    console.log('  FALHOU  ' + nome + ' — o ecra de entrada nao apareceu');
    await c2.close();
    return;
  }
  const r = await teste(p2);
  const maus = (r || []).filter(x => x && x[1] === false).map(x => x[0]);
  if (maus.length) {
    console.log('  FALHOU  ' + nome);
    maus.forEach(m => console.log('          ' + m));
  } else {
    console.log('  ok      ' + nome);
    bem++;
  }
  await c2.close();
}

await semSessao('a entrada pede a palavra-passe antes de tentar',
  async (p) => {
    await p.locator('#email').fill('ricardo@example.invalid');
    await p.locator('#bt-entrar').click();
    await p.waitForTimeout(300);
    const a = await p.locator('#av-entrada').innerText();
    return [
      ['explica que falta a palavra-passe', a.toLowerCase().includes('password')],
      ['oferece a outra via', a.toLowerCase().includes('link')],
      ['o campo da palavra-passe existe',
        await p.locator('#pw').count() === 1],
      ['o botao de ligacao existe',
        await p.locator('#bt-ligacao').count() === 1]
    ];
  });

await semSessao('a entrada pede o email antes de mandar a ligacao',
  async (p) => {
    await p.locator('#bt-ligacao').click();
    await p.waitForTimeout(300);
    return [['pede o email',
      (await p.locator('#av-entrada').innerText()).toLowerCase().includes('email')]];
  });

// ------------------------------------------------- a data, na pagina do tour
async function diaDiz(nome, modo, contem, daquiADias) {
  RESPOSTA_DIAS = modo;
  total++;
  if (await ver(nome, '/tours/cliffs-of-moher-galway/', '[data-data]',
    async (p) => {
      const d = new Date();
      d.setDate(d.getDate() + (daquiADias || 30));
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
await diaDiz('a data livre diz quantos cabem nesse dia', 'livre', 'up to 6 people');
await diaDiz('a data livre diz que partidas ainda dao', 'livre', 'departures still open');
await diaDiz('e mostra a hora que sobrou', 'livre', '17:00');
await diaDiz('a data cedo demais explica o aviso que falta', 'cedo', '3 days', 1);
await diaDiz('a data fechada diz que esta tomada', 'fechado', 'that day is taken');
await diaDiz('sem calendario nao afirma nada', 'sem', 'we confirm this date');
RESPOSTA_DIAS = 'livre';

// ------------------------------------------------ as horas de partida
await t('o calendario mostra e aceita horas de partida',
  '/portal/calendar/?tour=' + AN, '.hora', async (p) => [
    ['lista as duas partidas', await p.locator('.hora').count() === 2],
    ['mostra-as em hh:mm',
      (await p.locator('.hora').first().innerText()).indexOf('08:00') > -1],
    ['explica a regra com o aviso minimo',
      (await p.locator('#horas-nota').innerText()).toLowerCase()
        .indexOf('hours') > -1],
    ['cada hora tem como ser tirada',
      await p.locator('[data-tira]').count() === 2],
    ['o botao de tirar diz qual e',
      (await p.locator('[data-tira]').first().getAttribute('aria-label'))
        .indexOf('08:00') > -1]
  ]);

await t('o calendario recusa uma partida repetida',
  '/portal/calendar/?tour=' + AN, '.hora', async (p) => {
    await p.locator('#hora-nova').fill('08:00');
    await p.locator('#bt-hora').click();
    await p.waitForTimeout(300);
    return [['avisa que ja la esta',
      (await p.locator('#av-horas').innerText()).toLowerCase()
        .indexOf('already') > -1]];
  });

await t('o contacto recebe a partida pelo endereco',
  '/contact/?tour=example-sintra&date=2026-11-20&time=17:00', '#f-ped',
  async (p) => [
    ['a hora ja esta preenchida',
      (await p.locator('#a-que-horas').inputValue()).indexOf('17:00') === 0],
    ['e e dita no topo',
      (await p.locator('#sobre').innerText()).indexOf('17:00') > -1]
  ]);

// ------------------------------------------------------- as avaliacoes
await t('o operador ve as avaliacoes e pode responder a que falta',
  '/portal/reviews/', '.rv-c', async (p) => [
    ['mostra as duas', await p.locator('.rv-c').count() === 2],
    ['com a media', (await p.locator('.rs b').first().innerText()) === '3.5'],
    ['diz quantas esperam resposta',
      (await p.locator('.rs b').nth(2).innerText()) === '1'],
    ['a que ja tem resposta mostra-a, sem formulario',
      await p.locator('.rv-resp').count() === 1],
    ['a que falta tem formulario',
      await p.locator('[data-resp]').count() === 1],
    ['nao ha nenhum campo para mexer na nota',
      await p.locator('input[type=number]').count() === 0]
  ]);

await t('o operador nao pode responder com duas palavras',
  '/portal/reviews/', '[data-resp]', async (p) => {
    await p.locator('[data-resp] textarea').fill('ok');
    await p.locator('[data-resp] button').click();
    await p.waitForTimeout(300);
    const a = await p.locator('.rv-c .aviso').allInnerTexts();
    return [['diz que escreva a serio',
      a.join(' ').toLowerCase().indexOf('real reply') > -1]];
  });

async function convidaDiz(nome, modo, contem) {
  RESPOSTA_CONVITE = modo;
  total++;
  if (await ver(nome, '/review/?t=abc',
                '#form:not([hidden]), #erro:not([hidden])', async (p) => {
    const txt = await p.locator('#conteudo, main').first().innerText();
    return [['diz "' + contem + '"',
      txt.toLowerCase().indexOf(contem.toLowerCase()) > -1]];
  })) bem++;
}

await convidaDiz('o convite valido abre o formulario', 'valido', 'how was the day');
await convidaDiz('um convite ja usado diz que ja foi', 'usado', 'already in');
await convidaDiz('um convite expirado diz que expirou', 'expirado', 'expired');
await convidaDiz('um token que nao existe nao finge', 'nenhum', 'not one of ours');
RESPOSTA_CONVITE = 'valido';

await t('a pagina de avaliar exige a nota geral',
  '/review/?t=abc', '#f-av', async (p) => {
    await p.locator('#bt-av').click();
    await p.waitForTimeout(300);
    return [
      ['pede a nota',
        (await p.locator('#av-erro').innerText()).toLowerCase()
          .indexOf('rating') > -1],
      ['e o nome nao se escreve',
        await p.locator('#f-av input[id="nome"]').count() === 0]
    ];
  });

await t('as estrelas acendem-se ate a escolhida',
  '/review/?t=abc', '#f-av', async (p) => {
    await p.locator('[data-estrelas="rating"] input').nth(3).check();
    await p.waitForTimeout(200);
    return [
      ['quatro acesas',
        await p.locator('[data-estrelas="rating"] .acesa').count() === 4],
      ['o leitor de ecra ouve o numero',
        (await p.locator('[data-estrelas="rating"] label').nth(3).innerText())
          .indexOf('4 out of 5') > -1]
    ];
  });

// ------------------------------------------------ os pontos de encontro
await t('os pontos de encontro listam-se e abrem',
  '/portal/places/', '.p[data-p]', async (p) => [
    ['lista os dois', await p.locator('.p[data-p]').count() === 2],
    ['o primeiro vem aberto',
      (await p.locator('#p-nome').inputValue()).indexOf('Molly') === 0],
    ['com a morada', (await p.locator('#p-morada').inputValue()).length > 5],
    ['e as instrucoes',
      (await p.locator('#p-notas').inputValue()).indexOf('kiosk') > -1],
    ['mostra a fotografia que ja tem',
      await p.locator('#foto-pre img').count() === 1],
    ['e o mapa com o pino', await p.locator('#mapa iframe').count() === 1],
    ['diz que um tour o usa',
      await p.locator('.p-usos').count() >= 1]
  ]);

await t('um ponto sem coordenadas nao desenha pino nenhum',
  '/portal/places/', '.p[data-p]', async (p) => {
    await p.locator('.p[data-p]').nth(1).click();
    await p.waitForTimeout(300);
    return [
      ['abre o segundo',
        (await p.locator('#p-nome').inputValue()).indexOf('Heuston') === 0],
      ['sem mapa', await p.locator('#mapa iframe').count() === 0],
      ['e diz que falta a fotografia',
        (await p.locator('#foto-pre').innerText()).toLowerCase()
          .indexOf('no photograph') > -1]
    ];
  });

await t('os pontos de encontro recusam meia coordenada',
  '/portal/places/', '#f-lugar', async (p) => {
    await p.locator('.p[data-p]').nth(1).click();
    await p.waitForTimeout(200);
    await p.locator('#p-lat').fill('53.3438');
    await p.locator('#bt-grava').click();
    await p.waitForTimeout(300);
    const a = (await p.locator('#av-lg').innerText()).toLowerCase();
    return [['explica que vao aos pares',
      a.indexOf('together') > -1 || a.indexOf('both') > -1]];
  });

await t('e recusam coordenadas que nao sao numeros',
  '/portal/places/', '#f-lugar', async (p) => {
    await p.locator('#p-lat').fill('perto da ponte');
    await p.locator('#p-lng').fill('ao pe do rio');
    await p.locator('#bt-grava').click();
    await p.waitForTimeout(300);
    return [['diz que nao sao numeros',
      (await p.locator('#av-lg').innerText()).toLowerCase()
        .indexOf('not numbers') > -1]];
  });

// ------------------------------------------------------------- a frota
await t('a frota lista os veiculos e o calendario do escolhido',
  '/portal/fleet/', '.v[data-v]', async (p) => [
    ['lista os dois veiculos', await p.locator('.v[data-v]').count() === 2],
    ['mostra os lugares',
      (await p.locator('.v-pax').first().innerText()).indexOf('6') > -1],
    ['o primeiro vem escolhido',
      await p.locator('.v[aria-pressed="true"]').count() === 1],
    ['desenha o mes', await p.locator('.vd[data-d]').count() >= 28],
    ['um dia ocupado', await p.locator('.vd-booked').count() === 1],
    ['um dia indisponivel', await p.locator('.vd-closed').count() === 1],
    ['o estado vai no aria-label e nao so na cor',
      (await p.locator('.vd-booked').getAttribute('aria-label'))
        .indexOf('out on a job') > -1],
    ['diz a que tours o veiculo serve',
      (await p.locator('#vc-quem').innerText()).indexOf('tour') > -1]
  ]);

await t('a frota deixa ligar um veiculo a um tour',
  '/portal/fleet/', '.v-t input', async (p) => [
    ['ha uma caixa por tour', await p.locator('.v-t input').count() === 1],
    ['vem ligada, porque o v-class ja serve esse tour',
      await p.locator('.v-t input').first().isChecked() === true]
  ]);

await t('a frota recusa um veiculo sem lugares',
  '/portal/fleet/', '#f-novo', async (p) => {
    await p.locator('#v-nome').fill('Carrinha nova');
    await p.locator('#bt-novo').click();
    await p.waitForTimeout(300);
    return [['diz o que falta',
      (await p.locator('#av-novo').innerText()).toLowerCase()
        .indexOf('passengers') > -1]];
  });

await t('o editor tem o aviso minimo e deixa pedir mais de 10 horas',
  '/portal/listing/?id=' + AN, '#aviso', async (p) => {
    const opts = await p.locator('#aviso option').allTextContents();
    return [
      ['o campo existe', await p.locator('#aviso').count() === 1],
      ['tem opcoes acima das 10 horas da GetYourGuide',
        opts.some(x => x.indexOf('week') > -1 || x.indexOf('days') > -1)],
      ['os escaloes tem minimo e maximo',
        await p.locator('#escaloes [data-c="min"]').count() === 3 &&
        await p.locator('#escaloes [data-c="max"]').count() === 3]
    ];
  });

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


// =====================================================================
// A RESERVA E O PAGAMENTO
//
// O que se testa aqui nao e o caminho feliz. E o conjunto de casos em
// que uma pagina de reserva mente ao cliente: um preco que nao e o que
// vai ser cobrado, um "pagar depois" oferecido quando nao e permitido,
// um "pago" escrito a quem nao pagou nada.
// =====================================================================
console.log('\nA RESERVA E O PAGAMENTO\n');

/** Preenche o formulario com o minimo para poder submeter. */
async function preencher(p) {
  await p.fill('#rs-data', '2026-12-01');
  await p.fill('#rs-pax', '2');
  await p.fill('#rs-nome', 'Maria Oliveira');
  await p.fill('#rs-email', 'maria@example.invalid');
}

cenarioPadrao();
await t('o preco vem da base, nao dos escaloes que estao no HTML',
  '/tours/cliffs-of-moher-galway/', '[data-reserva]', async (p) => {
    await p.fill('#rs-data', '2026-12-01');
    await p.fill('#rs-pax', '2');
    await p.waitForFunction(
      () => document.querySelector('[data-total]').dataset.estado === 'feito',
      null, { timeout: 6000 });
    const v = await p.locator('[data-valor]').innerText();
    const d = await p.locator('[data-detalhe]').innerText();
    return [
      // 555 e o que o mock da base devolve. Qualquer numero dos escaloes
      // da pagina (380, 420, 490...) aqui significava uma segunda copia
      // da regra do preco a correr no browser.
      ['o total mostrado e o da base (mostra "' + v + '")', v.includes('555')],
      ['diz que e pelo veiculo inteiro', /whole vehicle/i.test(d)],
      ['diz o veiculo do escalao', /Sedan/.test(d)]
    ];
  });

cenarioPadrao();
CENARIO.cotar = Object.assign({}, CENARIO.cotar, {
  payLater: false, payLaterCode: 'tooSoon',
  payLaterReason: 'The tour starts in about 43 hours. Paying later needs at '
    + "least 72 hours' notice, so this one is paid at booking."
});
await t('"pagar depois" fecha-se com a razao a vista, e nao em silencio',
  '/tours/cliffs-of-moher-galway/', '[data-reserva]', async (p) => {
    await p.fill('#rs-data', '2026-12-01');
    await p.fill('#rs-pax', '2');
    await p.waitForFunction(
      () => document.querySelector('[data-modo-later]')
              .getAttribute('aria-disabled') === 'true',
      null, { timeout: 6000 });
    const av = await p.locator('[data-aviso]').innerText();
    return [
      ['o radio do pagar depois fica travado',
        await p.locator('[data-modo-later] input').isDisabled()],
      ['o pagar agora fica escolhido',
        await p.locator('[value=now]').isChecked()],
      ['a razao diz o numero concreto de horas (diz "'
        + av.slice(0, 40) + '")', /43 hours/.test(av)]
    ];
  });

cenarioPadrao();
CENARIO.cotar = { ok: false, code: 'dayClosed',
  error: 'That day is not available. Pick another one.' };
await t('um dia fechado trava o botao em vez de deixar pagar',
  '/tours/cliffs-of-moher-galway/', '[data-reserva]', async (p) => {
    await p.fill('#rs-data', '2026-12-01');
    await p.fill('#rs-pax', '2');
    await p.waitForFunction(
      () => document.querySelector('[data-enviar]').disabled === true,
      null, { timeout: 6000 });
    const d = await p.locator('[data-detalhe]').innerText();
    const v = await p.locator('[data-valor]').innerText();
    return [
      ['diz porque e que nao da', /not available/i.test(d)],
      // Deixar o preco antigo no ecra ao lado de "nao disponivel" e a
      // forma mais rapida de alguem ligar a perguntar qual dos dois e
      // verdade.
      ['o preco antigo desaparece (mostra "' + v + '")', !/\d/.test(v)]
    ];
  });

cenarioPadrao();
await t('o formulario nao chega a rede sem email',
  '/tours/cliffs-of-moher-galway/', '[data-reserva]', async (p) => {
    await p.fill('#rs-data', '2026-12-01');
    await p.fill('#rs-nome', 'Maria Oliveira');
    await p.click('[data-enviar]');
    await p.waitForTimeout(400);
    return [['continuamos na pagina do tour',
      p.url().includes('/tours/cliffs-of-moher-galway/')]];
  });

cenarioPadrao();
await t('com tudo preenchido, abre a pagina do pagamento',
  '/tours/cliffs-of-moher-galway/', '[data-reserva]', async (p) => {
    await preencher(p);
    await p.waitForFunction(
      () => document.querySelector('[data-enviar]').disabled === false,
      null, { timeout: 6000 });
    await p.click('[data-enviar]');
    await p.waitForURL(/cancellation/, { timeout: 6000 });
    return [['foi para onde o Stripe mandou', /cancellation/.test(p.url())]];
  });

cenarioPadrao();
CENARIO.reservarEstado = 502;
CENARIO.reservar = { error: 'The payment page did not open. Try again, or '
  + 'send us a message.', reference: 'EWABCD23' };
await t('se o Stripe nao abre, a mensagem aparece e o botao volta',
  '/tours/cliffs-of-moher-galway/', '[data-reserva]', async (p) => {
    await preencher(p);
    await p.waitForFunction(
      () => document.querySelector('[data-enviar]').disabled === false,
      null, { timeout: 6000 });
    await p.click('[data-enviar]');
    await p.waitForSelector('[data-erro]:not([hidden])', { timeout: 6000 });
    const e = await p.locator('[data-erro]').innerText();
    return [
      ['mostra a mensagem da funcao', /did not open/i.test(e)],
      // Sem isto, quem teve um erro de rede fica com um botao morto e a
      // unica saida e recarregar a pagina e escrever tudo outra vez.
      ['o botao volta a poder ser carregado',
        (await p.locator('[data-enviar]').isDisabled()) === false]
    ];
  }, /502/);

cenarioPadrao();
CENARIO.horas = [{ starts_at: '08:30:00' }, { starts_at: '14:00:00' }];
await t('as horas de partida vem da base, ao vivo',
  '/tours/cliffs-of-moher-galway/', '[data-reserva]', async (p) => {
    await p.fill('#rs-data', '2026-12-01');
    await p.waitForSelector('[data-horas-campo]:not([hidden])', { timeout: 6000 });
    const n = await p.locator('#rs-hora option').count();
    return [
      ['aparecem as duas horas (aparecem ' + n + ')', n === 2],
      ['sem segundos no ecra',
        (await p.locator('#rs-hora option').first().innerText()) === '08:30']
    ];
  });

cenarioPadrao();
CENARIO.horas = [];   // uma lista VAZIA: a base respondeu e nao ha horas
await t('sem horas configuradas, o campo da hora nao aparece',
  '/tours/cliffs-of-moher-galway/', '[data-reserva]', async (p) => {
    await p.fill('#rs-data', '2026-12-01');
    await p.waitForTimeout(600);
    return [['o campo fica escondido',
      await p.locator('[data-horas-campo]').isHidden()]];
  });

cenarioPadrao();
await t('a confirmacao de quem pagou agora diz que pagou',
  '/booking-confirmed/?session_id=cs_test_abcdefghij1234567890',
  '[data-detalhe]:not([hidden])', async (p) => {
    const txt = await p.locator('main').innerText();
    return [
      ['a referencia esta a vista', /EWABCD23/.test(txt)],
      ['diz "Paid"', /\bPaid\b/.test(txt)],
      ['nao promete uma cobranca futura', !/72 hours before/.test(txt)]
    ];
  });

cenarioPadrao();
CENARIO.sessao = Object.assign({}, CENARIO.sessao, { payment_mode: 'later' });
await t('a confirmacao de quem vai pagar depois NAO diz que pagou',
  '/booking-confirmed/?session_id=cs_test_abcdefghij1234567890',
  '[data-detalhe]:not([hidden])', async (p) => {
    const txt = await p.locator('main').innerText();
    return [
      // Dizer "paid" a quem nao pagou nada e uma mentira que se descobre
      // 72 horas antes do tour, quando o cartao e cobrado e a pessoa
      // acha que ja tinha pagado.
      ['nao escreve "Paid" em sitio nenhum', !/\bPaid\b/.test(txt)],
      ['diz que nada foi cobrado ainda', /[Nn]othing has been charged/.test(txt)],
      ['diz quando sai o dinheiro', /72 hours before/.test(txt)],
      ['a linha do valor diz "To be charged"', /To be charged/.test(txt)]
    ];
  });

cenarioPadrao();
CENARIO.sessao = { confirmed: false, payment_mode: 'now' };
await t('um pagamento ainda a processar nao diz que falhou',
  '/booking-confirmed/?session_id=cs_test_abcdefghij1234567890',
  '.cerro', async (p) => {
    const txt = await p.locator('.cerro').innerText();
    return [
      // O Stripe manda para esta pagina assim que a sessao termina, e o
      // webhook pode ainda nao ter chegado. "Falhou" nessa janela e um
      // telefonema desnecessario.
      ['diz que esta a processar', /still being processed/i.test(txt)],
      ['nao diz que falhou', !/failed|error/i.test(txt)]
    ];
  });

cenarioPadrao();
await t('o formulario de reserva e usavel no telemovel',
  '/tours/cliffs-of-moher-galway/', '[data-reserva]', async (p) => {
    await p.setViewportSize({ width: 390, height: 844 });
    await p.waitForTimeout(250);
    const r = await p.evaluate(() => {
      const f = document.querySelector('[data-reserva]');
      const b = f.querySelector('[data-enviar]').getBoundingClientRect();
      const campos = [...f.querySelectorAll('input,select,textarea')]
        .filter((el) => el.type !== 'radio' && el.offsetParent)
        .map((el) => Math.round(el.getBoundingClientRect().height));
      return {
        estica: f.getBoundingClientRect().right > window.innerWidth + 1,
        botao: Math.round(b.height),
        menor: Math.min(...campos)
      };
    });
    await p.setViewportSize({ width: 1280, height: 900 });
    return [
      ['o formulario nao estica para fora do ecra', !r.estica],
      ['o botao tem altura de dedo (' + r.botao + 'px)', r.botao >= 44],
      ['os campos tem altura de dedo (' + r.menor + 'px)', r.menor >= 40]
    ];
  });


cenarioPadrao();
await t('a agenda do operador diz o que ele recebe, e nao o que o cliente pagou',
  '/portal/bookings/', '.ag-soma', async (p) => {
    const txt = await p.locator('#lista').innerText();
    return [
      ['mostra o que ele recebe', /444\.00/.test(txt)],
      ['soma o total dele', /836\.00/.test(txt)],
      // O total do cliente e a comissao nao vem da base nesta funcao, e
      // nao podem aparecer aqui nem por acidente.
      ['nao escreve o total que o cliente pagou', !/555/.test(txt)],
      ['nao escreve a comissao', !/111|20%|0\.2/.test(txt)],
      ['diz que ha dinheiro cobrado e ainda nao pago',
        /not yet paid to you/.test(txt)]
    ];
  });

cenarioPadrao();
await t('a agenda explica a diferenca entre confirmada e paga',
  '/portal/bookings/', '.ag-soma', async (p) => {
    const txt = await p.locator('#lista').innerText();
    return [
      ['a paga diz que foi cobrada', /collected/.test(txt)],
      // Ao operador nao interessa o jargao do Stripe; interessa saber
      // que o dia e dele e quando chega o dinheiro.
      ['a confirmada diz que o cliente e cobrado antes do tour',
        /charged before the tour/.test(txt)],
      ['uma reserva sem hora nao finge uma hora',
        /time to agree/.test(txt)]
    ];
  });

cenarioPadrao();
await t('o admin avisa quando uma reserva por pagar nao tem cartao guardado',
  '/admin/bookings/', '.rb', async (p) => {
    const txt = await p.locator('#lista').innerText();
    return [
      ['marca-a como pagar depois', /pay later/i.test(txt)],
      ['diz que nada foi cobrado', /Nothing charged yet/.test(txt)],
      // Sem este aviso, a pagina mostrava uma data de cobranca e parecia
      // tudo tratado. A viagem acontecia e nunca era paga.
      ['avisa que nao pode ser cobrada',
        /cannot be charged/.test(txt)],
      ['mostra o que a plataforma leva (aqui pode)', /111/.test(txt)]
    ];
  });

cenarioPadrao();
await t('o admin cria o link de avaliacao de uma reserva que ja viajou',
  '/admin/bookings/', '.rv-abas', async (p) => {
    await p.click('[data-aba="invites"]');
    await p.waitForSelector('[data-convidar]', { timeout: 6000 });
    await p.click('[data-convidar]');
    await p.waitForSelector('[data-lk]:not([hidden])', { timeout: 6000 });
    const l = await p.locator('[data-lk]').innerText();
    return [
      ['o link leva o token', /\/review\/\?t=12345678/.test(l)],
      ['o botao diz que ja esta feito',
        /copy it/i.test(await p.locator('[data-convidar]').innerText())]
    ];
  });

cenarioPadrao();
await t('a fila de pagamentos soma por operador e diz que nao transfere nada',
  '/admin/bookings/', '.rv-abas', async (p) => {
    await p.click('[data-aba="payouts"]');
    await p.waitForSelector('.pg', { timeout: 6000 });
    const txt = await p.locator('#lista').innerText();
    return [
      ['soma o que esta a pagar', /1236\.00/.test(txt)],
      ['diz quantas reservas', /3 booking\(s\)/.test(txt)],
      // Uma pagina que diz "mark as paid" e facil de confundir com uma
      // pagina que paga. Esta diz, por escrito, que nao paga nada.
      ['avisa que nao transfere nada', /does not transfer/.test(txt)]
    ];
  });


// =====================================================================
// O PORTAL E O SITE, LIGADOS
//
// O que se testa aqui e uma coisa so: o portal nao pode prometer ao
// operador que o tour dele esta no site quando nao esta. A base diz o
// que esta APROVADO; o site e estatico e so muda quando alguem corre o
// gerador. Eram duas coisas e o portal tratava-as como uma.
// =====================================================================
console.log('\nO PORTAL E O SITE\n');

cenarioPadrao();
await t('com a versao aprovada publicada, o portal diz que esta no site',
  '/portal/', '.an-l', async (p) => {
    const txt = await p.locator('.an-l').first().innerText();
    const liga = p.locator('.an-site a');
    return [
      ['diz que esta no site', /on the site/i.test(txt)],
      ['diz quando foi publicado', /published/i.test(txt)],
      ['tem ligacao para a pagina do tour',
        (await liga.getAttribute('href')) === '/tours/example-sintra/'],
      ['a ligacao abre noutro separador',
        (await liga.getAttribute('target')) === '_blank'],
      // "live version" era a frase antiga, e dizia uma coisa que o portal
      // nao sabia. Se voltar, este teste cai.
      ['nao escreve "live version"', !/live version/i.test(txt)]
    ];
  });

cenarioPadrao();
// A base aprovou a v2; o manifesto diz que o site tem a v1.
CENARIO.aprovadaV2 = true;
await t('com o site atrasado, diz que o site mostra a versao antiga',
  '/portal/', '.an-site', async (p) => {
    const txt = await p.locator('.an-l').first().innerText();
    return [
      ['avisa que a versao no site e mais antiga',
        /older version on the site/i.test(txt)],
      ['diz qual esta no site', /shows version 1/.test(txt)],
      // Este e o caso que mais confunde um operador: ele mudou o texto,
      // foi aprovado, e o site continua igual. Tem de ler que falta um
      // passo e que o passo nao e dele.
      ['explica que falta publicar', /next publish/i.test(txt)]
    ];
  });

cenarioPadrao();
CENARIO.publicado = { gerado_em: '2026-10-05T12:00:00Z', tours: {} };
await t('aprovado e nunca publicado diz exatamente isso',
  '/portal/', '.an-site', async (p) => {
    const txt = await p.locator('.an-l').first().innerText();
    return [
      ['diz que ainda nao esta no site', /not on the site yet/i.test(txt)],
      ['nao finge uma ligacao para uma pagina que nao existe',
        (await p.locator('.an-site a').count()) === 0]
    ];
  });

cenarioPadrao();
CENARIO.publicado = null;   // o ficheiro nao carrega
await t('sem o manifesto, o portal CALA-SE sobre o site em vez de adivinhar',
  '/portal/', '.an-l', async (p) => {
    const txt = await p.locator('.an-l').first().innerText();
    return [
      ['nao aparece nenhuma linha sobre o site',
        (await p.locator('.an-site').count()) === 0],
      // Continua a dizer o que a base SABE. Calar-se sobre o site nao e
      // calar-se sobre tudo.
      ['continua a dizer a versao aprovada', /approved version/i.test(txt)],
      // A frase "whatever is on the site now stays there" continua a
      // aparecer, e esta certa: nao afirma QUAL versao esta no site. O
      // que nao pode aparecer e uma etiqueta a dizer o estado, porque
      // essa seria uma afirmacao sem fonte.
      ['nenhuma etiqueta de estado do site',
        (await p.locator('.an-ar').count()) === 0],
      ['nao nomeia uma versao como estando no site',
        !/shows version|goes on the site/i.test(txt)]
    ];
  }, /503|publicado\.json/);

cenarioPadrao();
CENARIO.publicado = {
  gerado_em: '2026-10-05T12:00:00Z',
  tours: { 'example-sintra': { versao: 1, url: '/tours/example-sintra/' } }
};
await t('o resumo conta o que esta no site, nao o que a base aprovou',
  '/portal/', '.resumo', async (p) => {
    const txt = await p.locator('.resumo').innerText();
    return [
      ['a etiqueta fala do agora', /on the site now/i.test(txt)],
      // O anuncio esta 'live' na base mas com a v1 no site e a v1
      // aprovada: conta 1. Antes contava o status da base, que dizia 1
      // mesmo com o site vazio.
      ['conta 1', /\b1\b[\s\S]*on the site now/i.test(txt)]
    ];
  });

cenarioPadrao();
CENARIO.publicado = { gerado_em: '2026-10-05T12:00:00Z', tours: {} };
CENARIO.aprovadaV2 = true;
await t('o admin avisa que ha tours aprovados fora do site, com os comandos',
  '/admin/', '#publicar:not([hidden])', async (p) => {
    const txt = await p.locator('#publicar').innerText();
    return [
      ['diz quantos faltam', /1 tour is approved and not on the site/i.test(txt)],
      ['explica que aprovar nao publica',
        /database[\s\S]*static/i.test(txt)],
      ['diz o endereco em falta', /example-sintra/.test(txt)],
      ['da o comando do gerador', /tools\/gerar\.py/.test(txt)],
      // Antes o botao dizia "Approve and publish" e nao publicava nada.
      // Foi essa frase que fez o passo da publicacao desaparecer.
      ['o botao deixou de prometer que publica',
        !/Approve and publish/i.test(await p.locator('#fila').innerText())]
    ];
  });

cenarioPadrao();
await t('com tudo publicado, o admin diz que o site esta em dia',
  '/admin/', '#publicar:not([hidden])', async (p) => {
    const txt = await p.locator('#publicar').innerText();
    return [
      ['diz que esta em dia', /site is up to date/i.test(txt)],
      ['diz quando foi a ultima publicacao', /last publish/i.test(txt)]
    ];
  });

console.log('\n' + bem + '/' + total + ' passaram\n');

await navegador.close();
servidor.close();
process.exit(bem === total ? 0 : 1);
