// =====================================================================
// POST /functions/v1/cobrar     (de hora a hora, por um cron)
//
// Cobra os cartoes guardados das reservas "pagar depois" que chegaram a
// hora. Quais e que chegaram, quantas tentativas levam e quanto se
// espera entre elas e a BASE que diz — a reservas_a_cobrar() ja aplica
// tudo isso. Esta funcao so fala com o Stripe e devolve o resultado.
//
// NAO ESTA NO JWT DO SUPABASE
// ---------------------------
// Publicada com --no-verify-jwt e protegida por um segredo proprio no
// cabecalho. Um cron nao tem sessao de utilizador.
// =====================================================================
import Stripe from 'https://esm.sh/stripe@18.5.0?target=deno';
import { json, rpc, segredo } from '../_partilhado/comum.ts';

const stripe = new Stripe(segredo('STRIPE_SECRET_KEY'), {
  httpClient: Stripe.createFetchHttpClient(),
});

Deno.serve(async (req) => {
  if (req.headers.get('x-cron-secret') !== segredo('CRON_SECRET')) {
    console.warn('[cobrar] chamada com segredo errado');
    return json({ error: 'Forbidden' }, 403);
  }

  // Primeiro a limpeza: solta os veiculos de reservas que ficaram por
  // pagar. Corre antes das cobrancas para o dia voltar a ficar a venda o
  // mais cedo possivel.
  let soltas = 0;
  try {
    soltas = await rpc('limpar_marcas', {});
  } catch (e) {
    console.error('[cobrar] limpar_marcas:', (e as Error).message);
  }

  let fila: any[];
  try {
    fila = await rpc('reservas_a_cobrar', {});
  } catch (e) {
    console.error('[cobrar] reservas_a_cobrar:', (e as Error).message);
    return json({ error: 'A base nao respondeu.' }, 503);
  }

  const conta = { soltas, vistas: fila.length, cobradas: 0, falhadas: 0 };

  for (const b of fila) {
    try {
      const intencao = await stripe.paymentIntents.create({
        amount: Number(b.amount_cents),
        currency: String(b.currency ?? 'EUR').toLowerCase(),
        customer: b.stripe_customer_id,
        payment_method: b.stripe_payment_method_id,
        // off_session: o cliente nao esta no site. O banco pode recusar
        // por isso mesmo, e e esse o caso que se trata em baixo.
        off_session: true,
        confirm: true,
        description: `Tour: ${b.tour_title} — ${b.booking_date} (${b.reference})`,
        metadata: {
          tipo: 'tour',
          booking_id: String(b.booking_id),
          reference: String(b.reference),
          cobranca_agendada: 'true',
        },
      }, {
        // A CHAVE DE IDEMPOTENCIA
        //
        // Se a resposta do Stripe se perder depois de ele ter cobrado, a
        // tentativa seguinte traz a mesma chave e o Stripe devolve o
        // mesmo pagamento em vez de cobrar duas vezes. Leva o numero da
        // tentativa: a tentativa 2 TEM de poder cobrar depois de a 1 ter
        // falhado a serio.
        idempotencyKey: `ewt-${b.booking_id}-${b.attempt}`,
      });

      await rpc('registar_cobranca', {
        p: {
          booking_id: b.booking_id, ok: true, attempt: b.attempt,
          payment_intent: intencao.id,
        },
      });
      conta.cobradas += 1;
      console.log('[cobrar]', b.reference, 'cobrada', b.amount_cents);
    } catch (e) {
      const err = e as { code?: string; message?: string };
      await rpc('registar_cobranca', {
        p: {
          booking_id: b.booking_id, ok: false, attempt: b.attempt,
          code: err.code ?? 'erro', message: (err.message ?? '').slice(0, 300),
        },
      }).catch(() => {});
      conta.falhadas += 1;
      console.error('[cobrar]', b.reference, 'falhou:', err.code, err.message);
    }
  }

  console.log('[cobrar]', JSON.stringify(conta));
  return json({ ok: true, ...conta });
});
