# -*- coding: utf-8 -*-
"""O formulario de reserva da pagina do tour.

Vive num ficheiro proprio e nao dentro do tour.py por uma razao: o
tour.py tem 1200 linhas e desenha a pagina toda. Isto e a unica parte da
pagina que mexe em dinheiro, e quando um dia houver um problema com um
pagamento quero poder abrir UM ficheiro de 300 linhas e nao caca-lo no
meio do resto.

O QUE ESTE FORMULARIO NAO FAZ
-----------------------------
Nao calcula precos. Nenhuma linha de JavaScript aqui multiplica nada. O
preco que a pessoa ve vem da `cotar()` na base — a MESMA funcao que a
`reservar()` usa para criar a reserva e que a Edge Function usa para
dizer ao Stripe quanto cobrar. Uma copia so, no sitio onde nao se pode
mexer do browser.

Isto parece ineficiente (uma chamada a rede para mostrar um numero que
esta no HTML) e e deliberado. Os escaloes estao no HTML para a pagina
abrir com um preco sem esperar pela rede, mas o numero que aparece ao
lado do botao de pagar — o que a pessoa vai ver no extrato do cartao —
veio de quem cobra.

AS DUAS FORMAS DE PAGAR
-----------------------
A base diz se "pagar depois" e permitido, e diz porque nao quando nao e.
A pagina mostra a razao com o numero concreto ("the tour starts in about
43 hours") em vez de um "not available" que parece uma avaria.
"""

from pagina import e  # noqa: F401


CSS = '''
/* O formulario de reserva. Herda as variaveis de cor da pagina. */
.rs{margin-top:var(--e3)}
.rs-grelha{display:grid;gap:14px;grid-template-columns:1fr 1fr}
.rs-grelha .larga{grid-column:1/-1}
@media (max-width:640px){.rs-grelha{grid-template-columns:1fr}}
.rs-campo label{display:block;font-size:11px;letter-spacing:.09em;
  text-transform:uppercase;color:var(--mudo);font-weight:600;margin:0 0 5px}
.rs-campo input,.rs-campo textarea,.rs-campo select{width:100%;
  padding:11px 12px;border:1px solid var(--linha);border-radius:8px;
  font:inherit;font-size:15px;background:#fff;color:var(--cor-escura)}
.rs-campo textarea{min-height:76px;resize:vertical}
.rs-campo input:focus,.rs-campo textarea:focus,.rs-campo select:focus{
  outline:2px solid var(--cor-escura);outline-offset:1px;border-color:transparent}
.rs-ajuda{font-size:12.5px;color:var(--mudo);margin:5px 0 0}

/* O preco, vindo da base. Nunca uma conta feita aqui. */
.rs-total{display:flex;flex-wrap:wrap;align-items:baseline;gap:10px;
  padding:14px 16px;border:1px solid var(--linha);border-radius:10px;
  background:var(--creme);margin:0 0 14px}
.rs-total b{font-size:26px;letter-spacing:-.02em;line-height:1}
.rs-total span{font-size:13px;color:var(--mudo)}
.rs-total[data-estado="pensar"]{opacity:.55}

/* Pagar agora ou pagar depois. Dois cartoes, nao dois radios nus: a
   diferenca entre eles e uma frase e nao uma palavra. */
.rs-modos{display:grid;gap:10px;grid-template-columns:1fr 1fr;margin:0 0 14px}
@media (max-width:640px){.rs-modos{grid-template-columns:1fr}}
.rs-modo{position:relative;display:block;padding:13px 14px;
  border:1px solid var(--linha);border-radius:10px;cursor:pointer;
  background:#fff;transition:border-color .15s,box-shadow .15s}
.rs-modo:hover{border-color:var(--cor-escura)}
.rs-modo input{position:absolute;opacity:0;width:1px;height:1px}
.rs-modo input:focus-visible+.rs-modo-i{outline:2px solid var(--cor-escura);
  outline-offset:3px;border-radius:4px}
.rs-modo:has(input:checked){border-color:var(--cor-escura);
  box-shadow:inset 0 0 0 1px var(--cor-escura)}
.rs-modo-i{display:block}
.rs-modo-t{display:block;font-weight:650;font-size:14.5px;margin:0 0 3px}
.rs-modo-d{display:block;font-size:12.5px;color:var(--mudo);line-height:1.45}
.rs-modo[aria-disabled="true"]{opacity:.5;cursor:not-allowed}
.rs-modo[aria-disabled="true"]:hover{border-color:var(--linha)}

.rs-aviso{font-size:12.5px;color:var(--mudo);margin:0 0 14px;
  padding-left:11px;border-left:2px solid var(--linha)}

.rs-erro{margin:0 0 14px;padding:11px 13px;border-radius:8px;
  background:#fdf1f1;border:1px solid #e7c3c3;color:#8a2a2a;font-size:13.5px}
.rs-erro[hidden]{display:none}

.rs-botao{display:block;width:100%;text-align:center}
.rs-botao[disabled]{opacity:.55;cursor:default}
.rs-seguro{display:block;text-align:center;font-size:12px;color:var(--mudo);
  margin:9px 0 0}
'''


def html(t):
    """O formulario. Recebe o tour so para o slug e o maximo de pessoas —
    o preco nao passa por aqui."""
    maximo = t['_max']
    return '''<form class="rs" data-reserva data-slug="%(slug)s"
      data-max="%(max)d" novalidate>

  <p class="rs-total" data-total data-estado="vazio">
    <b data-valor>&mdash;</b>
    <span data-detalhe>Pick a day and tell us how many of you there are.</span>
  </p>

  <div class="rs-erro" data-erro role="alert" hidden></div>

  <div class="rs-grelha">
    <div class="rs-campo">
      <label for="rs-data">Day of the tour</label>
      <input id="rs-data" type="date" name="date" required>
    </div>
    <div class="rs-campo">
      <label for="rs-pax">How many of you</label>
      <input id="rs-pax" type="number" name="pax" min="1" max="%(max)d"
             step="1" value="2" required>
      <p class="rs-ajuda">Up to %(max)d in one group. The price is for the
        whole vehicle.</p>
    </div>
    <div class="rs-campo" data-horas-campo hidden>
      <label for="rs-hora">Start time</label>
      <select id="rs-hora" name="time"></select>
    </div>
    <div class="rs-campo">
      <label for="rs-nome">Your name</label>
      <input id="rs-nome" type="text" name="name" autocomplete="name"
             maxlength="120" required>
    </div>
    <div class="rs-campo">
      <label for="rs-email">Email</label>
      <input id="rs-email" type="email" name="email" autocomplete="email"
             maxlength="160" required>
      <p class="rs-ajuda">The confirmation goes here.</p>
    </div>
    <div class="rs-campo">
      <label for="rs-tel">Phone (with country code)</label>
      <input id="rs-tel" type="tel" name="phone" autocomplete="tel"
             maxlength="30">
      <p class="rs-ajuda">So the driver can reach you on the day.</p>
    </div>
    <div class="rs-campo larga">
      <label for="rs-recolha">Where we pick you up</label>
      <input id="rs-recolha" type="text" name="pickup" maxlength="300"
             placeholder="Hotel name or address">
    </div>
    <div class="rs-campo larga">
      <label for="rs-notas">Anything we should know</label>
      <textarea id="rs-notas" name="notes" maxlength="600"
        placeholder="Child seats, wheelchair, a stop you care about, a flight time."></textarea>
    </div>
  </div>

  <h3 class="sub-h">When you pay</h3>
  <div class="rs-modos" data-modos>
    <label class="rs-modo">
      <input type="radio" name="payment_mode" value="now" checked>
      <span class="rs-modo-i">
        <span class="rs-modo-t">Pay now</span>
        <span class="rs-modo-d">Card charged today. Free cancellation up to
          24 hours before departure, refunded in full.</span>
      </span>
    </label>
    <label class="rs-modo" data-modo-later>
      <input type="radio" name="payment_mode" value="later">
      <span class="rs-modo-i">
        <span class="rs-modo-t">Book now, pay later</span>
        <span class="rs-modo-d">We hold your card and take
          nothing today. We charge it 72 hours before the tour.</span>
      </span>
    </label>
  </div>

  <p class="rs-aviso" data-aviso hidden></p>

  <button class="botao rs-botao" type="submit" data-enviar>
    Continue to payment</button>
  <span class="rs-seguro">Card details are handled by Stripe. We never see
    them. You can still cancel free up to 24 hours before departure.</span>
</form>''' % {'slug': e(t['slug']), 'max': maximo}


JS = r"""
(function () {
  'use strict';
  var f = document.querySelector('[data-reserva]');
  if (!f || !window.ewt || window.ewt.avariado) return;

  var slug    = f.dataset.slug;
  var data    = f.querySelector('[name=date]');
  var pax     = f.querySelector('[name=pax]');
  var horaC   = f.querySelector('[data-horas-campo]');
  var hora    = f.querySelector('[name=time]');
  var total   = f.querySelector('[data-total]');
  var valor   = f.querySelector('[data-valor]');
  var detalhe = f.querySelector('[data-detalhe]');
  var erro    = f.querySelector('[data-erro]');
  var aviso   = f.querySelector('[data-aviso]');
  var botao   = f.querySelector('[data-enviar]');
  var modoL   = f.querySelector('[data-modo-later]');
  var radioL  = modoL.querySelector('input');
  var radioN  = f.querySelector('[value=now]');
  var painel  = document.querySelector('[data-painel]');

  // Amanha e o minimo que o browser aceita. O lead time a serio e da
  // base, e e ela que recusa: isto e so para nao propor ontem.
  var amanha = new Date(Date.now() + 864e5).toISOString().slice(0, 10);
  data.min = amanha;
  data.max = new Date(Date.now() + 400 * 864e5).toISOString().slice(0, 10);

  // O PAINEL E O FORMULARIO DIZEM O MESMO
  //
  // A pessoa escolhe o dia e o grupo no painel do lado, carrega em
  // "Check this date" e cai aqui. Se o formulario abrisse vazio, tinha
  // de escrever as duas coisas outra vez — e a segunda vez e onde se
  // desiste.
  if (painel) {
    var pd = painel.querySelector('[data-data]');
    var pp = painel.querySelector('[data-pessoas]');
    var copiar = function () {
      if (pd && pd.value) data.value = pd.value;
      if (pp && pp.textContent.trim()) pax.value = pp.textContent.trim();
      cotar();
    };
    var ir = painel.querySelector('[data-ir]');
    if (ir) ir.addEventListener('click', copiar);
    if (pd) pd.addEventListener('change', copiar);
  }

  function mostrarErro(msg) {
    if (!msg) { erro.hidden = true; erro.textContent = ''; return; }
    erro.textContent = msg;
    erro.hidden = false;
  }

  function pedido() {
    return {
      slug: slug,
      date: data.value,
      time: (horaC.hidden ? '' : hora.value) || '',
      pax: Number(pax.value) || 0
    };
  }

  var aPensar = 0;

  // A COTACAO
  //
  // Uma chamada por mudanca, com o pedido mais recente a ganhar: quem
  // escreve "4" depois de "2" ve o preco de 4 mesmo se a resposta de 2
  // chegar depois. Sem o contador, a resposta lenta de um pedido antigo
  // escrevia por cima da resposta certa.
  async function cotar() {
    if (!data.value || !pax.value) {
      total.dataset.estado = 'vazio';
      valor.innerHTML = '&mdash;';
      detalhe.textContent = 'Pick a day and tell us how many of you there are.';
      botao.disabled = false;
      return;
    }

    var meu = ++aPensar;
    total.dataset.estado = 'pensar';

    var c;
    try {
      c = await window.ewt.cotar(pedido());
    } catch (err) {
      if (meu !== aPensar) return;
      total.dataset.estado = 'vazio';
      // A rede falhou, nao o pedido. Nao se bloqueia o botao: a Edge
      // Function volta a verificar tudo e, se o dia nao servir, diz.
      detalhe.textContent = 'We could not check that date just now.';
      valor.innerHTML = '&mdash;';
      botao.disabled = false;
      return;
    }
    if (meu !== aPensar) return;
    total.dataset.estado = 'feito';

    if (!c.ok) {
      valor.innerHTML = '&mdash;';
      detalhe.textContent = c.error || 'That date is not available.';
      botao.disabled = true;
      travarLater('');
      return;
    }

    botao.disabled = false;
    valor.textContent = '€' + Number(c.price).toFixed(0);
    detalhe.textContent = 'for the whole vehicle · ' +
      c.pax + (c.pax === 1 ? ' person' : ' people') +
      (c.vehicle ? ' · ' + c.vehicle : '');

    travarLater(c.payLater ? '' : (c.payLaterReason || ''));
  }

  /** "Pagar depois" so existe quando a base diz que sim — e quando diz
   *  que nao, diz porque. A razao fica a vista: "not available" sem
   *  explicacao parece uma avaria, e "the tour starts in about 43 hours"
   *  e uma regra que a pessoa percebe e pode contornar escolhendo outra
   *  data. */
  function travarLater(razao) {
    var fechado = !!razao;
    radioL.disabled = fechado;
    modoL.setAttribute('aria-disabled', fechado ? 'true' : 'false');
    if (fechado && radioL.checked) radioN.checked = true;
    aviso.textContent = razao;
    aviso.hidden = !fechado;
  }

  // AS HORAS DE PARTIDA, AO VIVO
  //
  // Quais e que ainda estao dentro do prazo muda ao longo do dia, por
  // isso nao podem estar no HTML: as 9h da manha a partida das 14h ainda
  // da, as 13h ja nao. A base compara o instante exato no fuso do
  // anuncio.
  async function horasDoDia() {
    if (!data.value) { horaC.hidden = true; return; }
    try {
      var r = await window.ewt.sb.rpc('partidas_no_dia',
        { p_slug: slug, p_day: data.value });
      var hs = (r.data || []).map(function (x) { return x.starts_at; });
      if (!hs.length) { horaC.hidden = true; hora.innerHTML = ''; return; }
      hora.innerHTML = hs.map(function (h) {
        var hh = String(h).slice(0, 5);
        return '<option value="' + hh + '">' + hh + '</option>';
      }).join('');
      horaC.hidden = false;
    } catch (err) {
      // Sem horas, a reserva vai sem hora e combina-se depois. Melhor
      // do que um formulario que nao deixa reservar.
      horaC.hidden = true;
    }
  }

  data.addEventListener('change', function () { horasDoDia().then(cotar); });
  pax.addEventListener('input', cotar);
  pax.addEventListener('change', cotar);
  hora.addEventListener('change', cotar);

  f.addEventListener('submit', async function (ev) {
    ev.preventDefault();
    mostrarErro('');

    // A validacao do browser primeiro: e instantanea e poupa uma ida a
    // rede para dizer "falta o email".
    if (!f.checkValidity()) {
      var mau = f.querySelector(':invalid');
      if (mau) { mau.focus(); mau.reportValidity(); }
      return;
    }

    botao.disabled = true;
    var texto = botao.textContent;
    botao.textContent = 'Opening payment…';

    var p = pedido();
    p.payment_mode = radioL.checked && !radioL.disabled ? 'later' : 'now';
    p.name    = f.querySelector('[name=name]').value;
    p.email   = f.querySelector('[name=email]').value;
    p.phone   = f.querySelector('[name=phone]').value;
    p.pickup  = f.querySelector('[name=pickup]').value;
    p.notes   = f.querySelector('[name=notes]').value;

    try {
      var r = await window.ewt.reservar(p);
      if (!r || !r.url) throw new Error('The payment page did not open.');
      // A reserva ja existe na base e o veiculo ja esta preso. Daqui em
      // diante e o Stripe.
      window.location.href = r.url;
    } catch (err) {
      mostrarErro(err.message ||
        'We could not take that booking. Try again, or send us a message.');
      botao.disabled = false;
      botao.textContent = texto;
      // Se o dia fechou entretanto, o preco em cima tem de mudar com a
      // mensagem: deixar la o valor antigo e dizer "nao da" ao mesmo
      // tempo e contraditorio.
      cotar();
    }
  });

  if (data.value) horasDoDia().then(cotar);
})();
"""
