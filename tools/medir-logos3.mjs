import { chromium } from '/opt/npm-tools/node_modules/playwright/index.mjs';
const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
// janela larga de proposito: assim o min() nunca morde e mede-se o natural
const p = await b.newPage({ viewport: { width: 2400, height: 900 } });
await p.goto('http://127.0.0.1:8778/logos3.html', { waitUntil: 'load' });
await p.waitForTimeout(900);
const r = await p.evaluate(() => {
  const out = [];
  document.querySelectorAll('section').forEach(sec => {
    const letra = sec.querySelector('.selo').textContent.trim();
    const m = sec.querySelector('.palco .marca');
    const t = parseFloat(getComputedStyle(m).fontSize);
    out.push([letra, Math.round(m.getBoundingClientRect().width), t]);
  });
  return out;
});
for (const [letra, largura, t] of r)
  console.log(letra, 'largura', largura, 'px a', t, 'px  ->  k =', (t / largura).toFixed(4));
await b.close();
