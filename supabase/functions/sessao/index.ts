// =====================================================================
// GET /functions/v1/sessao?id=cs_...
//
// O resumo de uma sessao, para a pagina /booking-confirmed/.
//
// So devolve o que o proprio cliente acabou de escrever (o tour, a data,
// o valor) e so de sessoes de tour. O id da sessao do Stripe e longo e
// aleatorio: nao se adivinha. Mesmo assim vai pelo Stripe e nao pela
// base, de proposito — a reserva na base tem telefone, recolha, notas,
// a reparticao e a comissao, e nada disso tem de passar por um endereco
// que basta saber o id para abrir.
// =====================================================================
import Stripe from 'https://esm.sh/stripe@18.5.0?target=deno';
import { CORS, json, segredo } from '../_partilhado/comum.ts';

const stripe = new Stripe(segredo('STRIPE_SECRET_KEY'), {
  httpClient: Stripe.createFetchHttpClient(),
});

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });

  const id = new URL(req.url).searchParams.get('id') ?? '';
  if (!/^cs_(test|live)_[A-Za-z0-9]{10,200}$/.test(id)) {
    return json({ error: 'Invalid session.' }, 400);
  }

  try {
    const s = await stripe.checkout.sessions.retrieve(id);
    const m = s.metadata ?? {};
    if (m.tipo !== 'tour') return json({ error: 'Not found.' }, 404);

    const maisTarde = m.payment_mode === 'later';

    return json({
      // No modo setup nao houve pagamento: o que confirma a reserva e o
      // cartao ter sido aceite. Dizer "paid" aqui era mentira, e a pagina
      // tem de escrever uma frase diferente.
      confirmed: maisTarde ? s.status === 'complete' : s.payment_status === 'paid',
      payment_mode: maisTarde ? 'later' : 'now',
      reference: m.reference ?? null,
      tour: m.tour_title ?? null,
      slug: m.tour_slug ?? null,
      operator: m.operator ?? null,
      date: m.tour_date ?? null,
      time: m.start_time ? String(m.start_time).slice(0, 5) : null,
      pax: Number(m.pax) || null,
      amount: maisTarde
        ? (m.price_eur ? Number(m.price_eur) : null)
        : (typeof s.amount_total === 'number' ? s.amount_total / 100 : null),
      currency: String(s.currency ?? 'eur').toUpperCase(),
      email: s.customer_details?.email ?? null,
    });
  } catch {
    return json({ error: 'Not found.' }, 404);
  }
});
