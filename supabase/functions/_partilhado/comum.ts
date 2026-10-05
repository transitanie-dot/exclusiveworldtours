// =====================================================================
// O QUE AS TRES FUNCOES PARTILHAM
//
// O site e estatico e nao tem onde guardar uma chave do Stripe. Estas
// Edge Functions sao o unico sitio do projeto com segredos, e os
// segredos estao nos Secrets do projeto Supabase — nunca no
// repositorio, que e servido com publishPath "." e portanto e todo
// publico.
// =====================================================================

export const SITE = 'https://exclusiveworldtours.com';

/**
 * A pagina do Stripe com a cara da Exclusive World Tours.
 *
 * A conta do Stripe e a do Airportlink (decisao do Ricardo, 5 out 2026),
 * por isso a pagina de pagamento mostraria a marca Airportlink a quem
 * esta a reservar um tour privado em Sevilha. O branding_settings do
 * Checkout muda, SO NESTA SESSAO, o nome no topo, o logotipo, as cores e
 * a letra. O resto da conta fica igual.
 *
 * O nome do Airportlink continua no recibo e nos termos do Stripe,
 * porque e o nome da conta. No extrato do cartao aparece o prefixo da
 * conta seguido de "EXCL WORLD TOURS".
 *
 * Se o Stripe recusar o branding, a sessao cria-se na mesma sem ele:
 * mais vale uma pagina com a marca errada do que um cliente sem pagina.
 */
export const VERSAO_BRANDING = '2025-09-30.clover';

export const MARCA = {
  display_name: 'Exclusive World Tours',
  logo: { type: 'url', url: SITE + '/logos/exclusive-world-tours.png' },
  icon: { type: 'url', url: SITE + '/icon-512.png' },
  background_color: '#FFFFFF',
  button_color: '#1B2A35',
  font_family: 'inter',
  border_style: 'rounded',
};

export const SUFIXO_EXTRATO = 'EXCL WORLD TOURS';

/** Um segredo que TEM de existir. Falhar no arranque e melhor do que
 *  falhar a meio de um pagamento. */
export function segredo(nome: string): string {
  const v = Deno.env.get(nome);
  if (!v) throw new Error(`Falta o segredo ${nome}`);
  return v;
}

export const CORS = {
  'Access-Control-Allow-Origin': SITE,
  'Access-Control-Allow-Headers': 'content-type, authorization',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
};

export function json(corpo: unknown, estado = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status: estado,
    headers: { 'content-type': 'application/json', ...CORS },
  });
}

/**
 * Uma chamada a base com a chave de SERVICO.
 *
 * A chave de servico passa por cima do RLS, e e por isso que vive aqui e
 * nunca no browser. As funcoes que ela chama — reservar(),
 * confirmar_reserva(), registar_cobranca() — estao REVOGADAS ao anon e
 * ao authenticated de proposito: o unico caminho para elas e este.
 */
export async function rpc(nome: string, args: unknown): Promise<any> {
  const url = segredo('SUPABASE_URL');
  const chave = segredo('SUPABASE_SERVICE_ROLE_KEY');

  const r = await fetch(`${url}/rest/v1/rpc/${nome}`, {
    method: 'POST',
    headers: {
      apikey: chave,
      authorization: `Bearer ${chave}`,
      'content-type': 'application/json',
    },
    body: JSON.stringify(args),
  });

  const texto = await r.text();
  if (!r.ok) throw new Error(`${nome}: ${r.status} ${texto.slice(0, 300)}`);
  return texto ? JSON.parse(texto) : null;
}

/** O texto que vai para o Stripe, sem caracteres de controlo e cortado.
 *  O Stripe recusa a SESSAO INTEIRA se um valor passar dos limites, e a
 *  recusa nao diz qual foi o campo. */
export function texto(v: unknown, max: number): string {
  return String(v ?? '').replace(/[\u0000-\u001f\u007f]/g, ' ').trim().slice(0, max);
}
