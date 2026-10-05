// =====================================================================
// POST /functions/v1/reservar
//
// Recebe o que o cliente escreveu, pede a BASE para criar a reserva (e e
// a base que calcula o preco e prende o veiculo, na mesma transacao), e
// abre a pagina do Stripe.
//
// O PRECO NUNCA VEM DAQUI
// -----------------------
// Esta funcao nao calcula preco nenhum. Manda o slug, o dia, a hora e
// quantas pessoas a reservar(), e usa o `amount_cents` que a base
// devolve. Um preco mudado no browser nao passa daqui, e — mais
// importante — nao ha uma segunda copia da regra do preco a divergir da
// primeira.
//
// DUAS FORMAS DE PAGAR
// --------------------
//   now     mode 'payment' — o Stripe cobra agora
//   later   mode 'setup'   — o Stripe guarda o cartao e nao cobra nada
//
// Quem decide se o "later" e permitido e a base, nao o browser: a
// reservar() devolve o modo que ficou gravado, e e esse que se usa.
// =====================================================================
import Stripe from 'https://esm.sh/stripe@18.5.0?target=deno';
import { CORS, MARCA, SITE, SUFIXO_EXTRATO, VERSAO_BRANDING, json, rpc, segredo, texto }
  from '../_partilhado/comum.ts';

const stripe = new Stripe(segredo('STRIPE_SECRET_KEY'), {
  httpClient: Stripe.createFetchHttpClient(),
});

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') return new Response('ok', { headers: CORS });
  if (req.method !== 'POST') return json({ error: 'POST only' }, 405);

  let b: Record<string, unknown>;
  try {
    b = await req.json();
  } catch {
    return json({ error: 'Send JSON.' }, 400);
  }

  const email = texto(b.email, 160);
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return json({ error: 'We need an email to send the confirmation to.' }, 400);
  }
  if (texto(b.name, 120).length < 2) {
    return json({ error: 'Tell us your name.' }, 400);
  }

  // A BASE DECIDE TUDO
  //
  // Preco, disponibilidade, lead time, hora de partida, veiculo livre e
  // modo de pagamento. Se disser que nao, a razao que vem dela e a que o
  // cliente le — ja esta escrita em ingles e ja diz o numero concreto.
  let r: any;
  try {
    r = await rpc('reservar', {
      p: {
        slug: texto(b.slug, 80),
        date: texto(b.date, 10),
        time: texto(b.time, 5),
        pax: Number(b.pax),
        payment_mode: b.payment_mode === 'later' ? 'later' : 'now',
        name: texto(b.name, 120),
        email,
        phone: texto(b.phone, 30),
        pickup: texto(b.pickup, 300),
        notes: texto(b.notes, 600),
      },
    });
  } catch (e) {
    console.error('[reservar] base:', (e as Error).message);
    return json({
      error: 'Booking is not available right now. Send us a message and we will book it for you.',
    }, 503);
  }

  if (!r?.ok) {
    return json({ error: r?.error ?? 'We could not take that booking.', code: r?.code }, 400);
  }

  const maisTarde = r.payment_mode === 'later';
  const resumo = [
    r.date,
    r.time ? `at ${String(r.time).slice(0, 5)}` : null,
    `${r.pax} ${r.pax === 1 ? 'person' : 'people'}`,
    r.vehicle_name || r.vehicle || null,
  ].filter(Boolean).join(', ');

  // A metadata e o que liga o pagamento a reserva. O webhook so precisa
  // do booking_id, mas o resto esta aqui para quem abrir o painel do
  // Stripe saber o que esta a ver sem ir a base.
  const metadata = {
    tipo: 'tour',
    booking_id: String(r.booking_id),
    reference: String(r.reference),
    tour_slug: texto(r.slug, 80),
    tour_title: texto(r.title, 200),
    operator: texto(r.operator, 120),
    tour_date: texto(r.date, 10),
    start_time: texto(r.time, 8),
    pax: String(r.pax),
    price_eur: String(r.price),
    payment_mode: r.payment_mode,
    // A VERDADE, E NAO O QUE DA JEITO
    //
    // No modo 'later' nao entrou dinheiro nenhum. Escrever 'paid' aqui
    // poupava um `if` e enganava quem fosse ao painel do Stripe
    // investigar um problema.
    status: maisTarde ? 'confirmed' : 'paid',
  };

  const comum = {
    customer_email: email,
    customer_creation: 'always' as const,
    metadata,
    success_url: `${SITE}/booking-confirmed/?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${SITE}/tours/${texto(r.slug, 80)}/#book`,
  };

  const pedido = maisTarde
    // GUARDAR O CARTAO SEM COBRAR
    //
    // No modo setup o Stripe nao mostra preco nenhum — so pede o cartao.
    // Do lado do cliente isso e dar os dados do cartao sem ver quanto vai
    // ser cobrado, que e o momento em que mais gente desiste. O
    // custom_text poe uma linha por cima do formulario a dizer o
    // essencial: quanto, e quando.
    //
    // O customer_creation: 'always' e obrigatorio e nao e obvio. Com so
    // customer_email o cartao fica guardado sem cliente nenhum, e a
    // cobranca de 72 horas antes nunca acontece — precisa dos dois. Viagem
    // feita e zero cobrado. E criar o cliente ANTES da sessao enchia o
    // painel de clientes sem cartao e sem reserva (pessoas que abriram o
    // checkout e fecharam a janela); com 'always' o Stripe so o cria
    // quando a sessao e COMPLETADA.
    ? {
        ...comum,
        mode: 'setup' as const,
        payment_method_types: ['card'],
        custom_text: {
          submit: {
            message:
              `EUR ${Number(r.price).toFixed(2)} · ${texto(r.title, 70)} · ${resumo}. ` +
              `Nothing is charged today. We take it 72 hours before the tour, ` +
              `and you can cancel free up to 24 hours before.`,
          },
        },
        setup_intent_data: { metadata },
      }
    : {
        ...comum,
        mode: 'payment' as const,
        // O botao diz "Book" em vez de "Pay".
        submit_type: 'book' as const,
        line_items: [{
          quantity: 1,
          price_data: {
            currency: 'eur',
            unit_amount: Number(r.amount_cents),
            product_data: {
              name: texto(r.title, 250),
              description: texto(resumo, 500),
              ...(/^https:\/\//.test(String(r.photo ?? ''))
                ? { images: [String(r.photo)] } : {}),
            },
          },
        }],
        custom_text: {
          submit: { message: 'Free cancellation up to 24 hours before departure.' },
        },
        payment_intent_data: {
          description: texto(`Tour: ${r.title} — ${resumo}`, 500),
          statement_descriptor_suffix: SUFIXO_EXTRATO,
          metadata,
        },
        // Quem chega ao pagamento e nao termina e a venda mais facil de
        // recuperar: o evento checkout.session.expired passa a trazer um
        // endereco que abre o mesmo pagamento outra vez.
        after_expiration: { recovery: { enabled: true } },
      };

  // O telefone so se pede no Stripe se o cliente nao o escreveu no site:
  // e por ele que se combina a recolha no dia.
  const comTelefone = {
    ...pedido,
    phone_number_collection: { enabled: !texto(b.phone, 30) },
  };

  try {
    let sessao;
    try {
      sessao = await stripe.checkout.sessions.create(
        { ...comTelefone, branding_settings: MARCA } as never,
        { apiVersion: VERSAO_BRANDING } as never,
      );
    } catch (e) {
      // Tenta sem o que e novo (a marca, o sufixo do extrato e a
      // fotografia). O cliente paga na mesma.
      console.error('[reservar] stripe com marca:', (e as Error).message);
      sessao = await stripe.checkout.sessions.create(comTelefone as never);
    }

    return json({
      ok: true,
      url: sessao.url,
      reference: r.reference,
      payment_mode: r.payment_mode,
      hold_minutes: r.hold_minutes,
    });
  } catch (e) {
    console.error('[reservar] stripe:', (e as Error).message);
    // A RESERVA FICA, E E DE PROPOSITO
    //
    // A reserva ja existe na base em 'pending' com o veiculo preso por
    // `hold_minutes`. Se o Stripe falhou, a limpar_marcas() solta-a
    // sozinha passado o prazo. Apagar aqui era mais limpo em teoria e
    // pior na pratica: se a pagina do Stripe tiver sido criada e a
    // resposta se tiver perdido pelo caminho, o cliente paga uma reserva
    // que ja nao existe.
    return json({
      error: 'The payment page did not open. Try again, or send us a message.',
      reference: r.reference,
    }, 502);
  }
});
