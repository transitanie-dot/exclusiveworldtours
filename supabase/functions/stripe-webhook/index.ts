// =====================================================================
// POST /functions/v1/stripe-webhook
//
// O Stripe avisa que um pagamento entrou. Esta funcao nao decide nada:
// verifica a assinatura, tira o booking_id da metadata e chama a
// confirmar_reserva(), que e idempotente.
//
// A ASSINATURA E O QUE IMPEDE QUALQUER PESSOA DE CONFIRMAR RESERVAS
// -----------------------------------------------------------------
// Sem ela, bastava um POST com um booking_id para marcar uma reserva
// como paga. A verificacao usa o corpo CRU — o texto exato que o Stripe
// enviou. Um `await req.json()` antes disto parte a assinatura, e o erro
// que da e "No signatures found", que nao diz que a culpa foi disso.
//
// Responde 200 mesmo quando falha a tratar o evento. O Stripe repete um
// evento que nao recebeu 200, e repetir para sempre nao resolve um erro
// nosso — so enche o painel. A excecao e a assinatura: essa responde 400,
// porque um pedido nao assinado nao e do Stripe.
//
// NAO ESTA NO JWT DO SUPABASE
// ---------------------------
// Esta funcao tem de ser publicada com --no-verify-jwt: o Stripe nao
// manda um token do Supabase. Quem a autentica e a assinatura dele.
// =====================================================================
import Stripe from 'https://esm.sh/stripe@18.5.0?target=deno';
import { rpc, segredo } from '../_partilhado/comum.ts';

const stripe = new Stripe(segredo('STRIPE_SECRET_KEY'), {
  httpClient: Stripe.createFetchHttpClient(),
});
const verificador = Stripe.createSubtleCryptoProvider();

Deno.serve(async (req) => {
  const assinatura = req.headers.get('stripe-signature');
  if (!assinatura) return new Response('No signature', { status: 400 });

  // O corpo cru, antes de qualquer parse.
  const cru = await req.text();

  let evento: Stripe.Event;
  try {
    evento = await stripe.webhooks.constructEventAsync(
      cru, assinatura, segredo('STRIPE_WEBHOOK_SECRET'), undefined, verificador,
    );
  } catch (e) {
    console.error('[webhook] assinatura:', (e as Error).message);
    return new Response('Bad signature', { status: 400 });
  }

  try {
    if (evento.type === 'checkout.session.completed') {
      const s = evento.data.object as Stripe.Checkout.Session;
      const m = s.metadata ?? {};

      // So os nossos tours. A conta do Stripe e partilhada com o
      // Airportlink e com o The Epic Tours: sem este filtro, esta funcao
      // tentava confirmar reservas de transfers que nao existem aqui.
      if (m.tipo !== 'tour' || !m.booking_id) {
        console.log('[webhook] evento de outro produto, ignorado:', s.id);
        return new Response('ignored', { status: 200 });
      }

      // No modo setup o payment_method esta dentro do SetupIntent, nao na
      // sessao. Sem ele, a cobranca de 72 horas antes nao tem cartao para
      // usar: viagem feita e zero cobrado.
      let metodo: string | null = null;
      if (typeof s.setup_intent === 'string') {
        try {
          const si = await stripe.setupIntents.retrieve(s.setup_intent);
          metodo = typeof si.payment_method === 'string' ? si.payment_method : null;
        } catch (e) {
          console.error('[webhook] setup_intent:', (e as Error).message);
        }
      }

      const r = await rpc('confirmar_reserva', {
        p: {
          booking_id: m.booking_id,
          session_id: s.id,
          payment_intent: typeof s.payment_intent === 'string' ? s.payment_intent : null,
          customer: typeof s.customer === 'string' ? s.customer : null,
          payment_method: metodo,
          setup_intent: typeof s.setup_intent === 'string' ? s.setup_intent : null,
          name: s.customer_details?.name ?? null,
          email: s.customer_details?.email ?? null,
          phone: s.customer_details?.phone ?? null,
        },
      });

      console.log('[webhook]', r?.reference, r?.status, r?.repeated ? '(repetido)' : '');

      // O CARTAO GUARDADO E A COBRANCA QUE NAO EXISTE
      //
      // Uma reserva 'later' confirmada sem payment_method e uma viagem
      // que vai acontecer e nunca vai ser paga, e ninguem da por isso
      // ate olhar para as contas no fim do mes. Fica no registo, que e o
      // unico sitio onde isto se pode ver antes do dia da viagem.
      if (r?.status === 'confirmed' && !metodo) {
        console.error('[webhook] ATENCAO: reserva', r.reference,
          'confirmada SEM cartao guardado — nao vai poder ser cobrada.');
      }
    }

    if (evento.type === 'checkout.session.expired') {
      const s = evento.data.object as Stripe.Checkout.Session;
      const m = s.metadata ?? {};
      if (m.tipo === 'tour') {
        // Nao se cancela a reserva aqui: a limpar_marcas() ja o faz
        // passado o prazo. O que interessa e o endereco de recuperacao,
        // que abre o mesmo pagamento outra vez.
        console.log('[webhook] expirou', m.reference,
          'recuperar em:', s.after_expiration?.recovery?.url ?? '(sem link)');
      }
    }
  } catch (e) {
    console.error('[webhook] a tratar', evento.type + ':', (e as Error).message);
  }

  return new Response('ok', { status: 200 });
});
