# As Edge Functions

O site é estático (Render, `publishPath: "."`, sem build) e portanto não
tem onde guardar uma chave do Stripe — todo o ficheiro na raiz é público.
Estas quatro funções são o único sítio do projeto com segredos, e os
segredos vivem nos **Secrets do projeto Supabase**, nunca no repositório.

| Função | Quem chama | JWT |
|---|---|---|
| `reservar` | o browser, com a chave publicável | sim |
| `stripe-webhook` | o Stripe | **não** (`--no-verify-jwt`) |
| `cobrar` | um cron, de hora a hora | **não**, segredo próprio no cabeçalho |
| `sessao` | a página `/booking-confirmed/` | sim |

## Os segredos

```bash
supabase secrets set --project-ref lmrvoakknsrypoeqmjbr \
  STRIPE_SECRET_KEY='sk_live_...' \
  STRIPE_WEBHOOK_SECRET='whsec_...' \
  CRON_SECRET='<uma string longa e aleatória>'
```

O `STRIPE_SECRET_KEY` é o da conta do **Airportlink** (decisão do
Ricardo, 5 out 2026) — está nas Environment Variables do serviço do
Airportlink no Render. O `SUPABASE_URL` e o `SUPABASE_SERVICE_ROLE_KEY`
já existem sozinhos dentro das Edge Functions; não se põem à mão.

## Publicar

```bash
supabase functions deploy reservar       --project-ref lmrvoakknsrypoeqmjbr
supabase functions deploy sessao         --project-ref lmrvoakknsrypoeqmjbr
supabase functions deploy stripe-webhook --project-ref lmrvoakknsrypoeqmjbr --no-verify-jwt
supabase functions deploy cobrar         --project-ref lmrvoakknsrypoeqmjbr --no-verify-jwt
```

## O webhook, no Stripe

No painel do Stripe (conta do Airportlink), **Developers → Webhooks →
Add endpoint**:

- URL: `https://lmrvoakknsrypoeqmjbr.supabase.co/functions/v1/stripe-webhook`
- Eventos: `checkout.session.completed` e `checkout.session.expired`

Copia o `whsec_...` que ele dá e põe-no nos Secrets.

**A conta do Stripe é partilhada** com o Airportlink e o The Epic Tours,
por isso este webhook vai receber eventos dos três. É por isso que a
primeira coisa que faz é filtrar por `metadata.tipo === 'tour'` e pela
existência de um `booking_id` — sem isso, tentava confirmar reservas de
transfers que não existem nesta base. Pela mesma razão, o webhook do
Airportlink vai receber os eventos daqui e tem de os ignorar: ele já
filtra pelo que conhece, mas vale a pena confirmar isso no dia em que se
ligar isto a sério.

## O cron

De hora a hora. Pode ser um Cron Job do Render ou o `pg_cron` do próprio
Supabase:

```sql
select cron.schedule('cobrar-reservas', '7 * * * *', $$
  select net.http_post(
    url := 'https://lmrvoakknsrypoeqmjbr.supabase.co/functions/v1/cobrar',
    headers := '{"x-cron-secret":"<o CRON_SECRET>"}'::jsonb) $$);
```

O minuto 7 e não o 0 de propósito: à hora em ponto é quando todos os
crons do mundo correm.

## O que NÃO está aqui

**Reembolsos.** A `cancelar_reserva()` guarda o estado e devolve o
`payment_intent` e o valor, mas não devolve dinheiro nenhum. Quem cobra é
o Stripe e quem devolve é o Stripe; se uma função fizesse as duas coisas,
um erro no Stripe deixava a base a dizer uma coisa e o dinheiro a dizer
outra. O reembolso faz-se a seguir, à mão ou numa função própria, e só
depois de a base já ter o cancelamento gravado.

**Emails.** Os avisos ao cliente e ao operador vão pela Resend, e os
registos DNS de `exclusiveworldtours.com` ainda não estão postos (o
domínio está em `not_started`). Até lá, o pagamento funciona e o aviso é
o que o Stripe manda.
