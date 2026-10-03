#!/usr/bin/env python3
"""
Homepage, direcao "Marketplace".

A estrutura convencional de um marketplace de experiencias, sem
invencoes: pesquisa grande em cima, barra de confianca, mosaico de
destinos, filas de produtos por cidade, grelha de paises, porque
reservar connosco, e o rodape com as ligacoes todas para SEO.

Duas decisoes que resolvem problemas reais:

1. Nao ha retangulos cinzentos. Enquanto nao houver fotografia, cada
   destino tem um mosaico desenhado — um gradiente da familia da marca
   com o nome por cima. Nao finge ser fotografia e nao parece avariado.
   A classe `.foto` esta pronta: no dia em que houver imagens, poe-se
   uma <img> dentro e o mosaico fica por baixo como fundo.
2. Tudo o que aparece e contado a partir do tours.json e do atlas.json:
   os destinos, as contagens, os precos mais baixos e as coordenadas.
   Nenhum numero escrito a mao, nenhuma avaliacao inventada.

    python3 tools/atlas.py       # coordenadas, uma vez
    python3 tools/home3.py       # escreve index-marketplace.html
"""

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

PAISES = [
    ('ireland',  'Ireland'),
    ('uk',       'United Kingdom'),
    ('france',   'France'),
    ('italy',    'Italy'),
    ('spain',    'Spain'),
    ('portugal', 'Portugal'),
]
NOME_PAIS = dict(PAISES)

# Os seis gradientes dos mosaicos. Sao da familia da paleta e repetem-se
# por ordem, nao ao acaso: assim a pagina tem ritmo em vez de confusao.
GRADIENTES = [
    ('#2B2E83', '#5B4BD6'),
    ('#0E5C6B', '#19A5A0'),
    ('#6B2A63', '#B5458C'),
    ('#1C3C7A', '#2F79C4'),
    ('#7A3A1C', '#C4762F'),
    ('#1F5A3A', '#3FA06A'),
]



# ---------------------------------------------------------------- fotografia
#
# Fotografias do Unsplash, escolhidas uma a uma para o sitio certo. Sao
# provisorias: assim que o Ricardo tiver as dele, troca-se o id aqui e
# mais nada. A chave e o slug do tour ou o nome da cidade/pais.
#
# A licenca do Unsplash obriga a creditar o fotografo; os creditos saem
# no fim da pagina, gerados a partir desta tabela.
FOTOS = {
    # o heroi
    'hero': ('1768382651261-7cc3c02349d3', 'Sara Ruffoni', 'ssarasframes'),
    # cidades
    'Dublin':    ('1549918864-48ac978761a4', 'Gregory Dalleau', 'gregda'),
    'London':    ('1681407979872-0a4cbde28391', 'Jacob Diehl', 'jacob_diehl_film'),
    'Paris':     ('1502602898657-3e91760cbb34', 'Chris Karidis', 'chriskaridis'),
    'Rome':      ('1552832230-c0197dd311b5', 'David Kohler', 'davidkhlr'),
    'Lisbon':    ('1599069158346-684fee0e414a', 'Andre Lergier', 'andrelergier'),
    'Florence':  ('1585595684482-984bf2cf8041', 'Nicola Pavan', 'pavan_nicola'),
    'Algarve':   ('1662142063545-eef59b226744', 'Ryan Miller', 'rsjmiller'),
    'Madeira':   ('1757440156760-8880058ce691', 'Mick Waanders', 'mick_gw'),
    'Seville':   ('1661442196029-ecc4a8e0a0b8', 'Tania Mousinho', 'shotsbytania'),
    # tours
    'cliffs-of-moher-galway': ('1570875450638-044bca38ec92', 'Saad Chaudhry', 'saadchdhry'),
    'belfast-titanic-giants-causeway': ('1595538853083-dc3160ca6881', 'Sean Kuriyan', 'sean189'),
    'wicklow-glendalough': ('1571609227120-1ec3adc4249a', 'Hamed Alayoub', 'h_alayoub'),
    'dublin-private-chauffeur': ('1549918864-48ac978761a4', 'Gregory Dalleau', 'gregda'),
    'central-london': ('1681407979872-0a4cbde28391', 'Jacob Diehl', 'jacob_diehl_film'),
    'stonehenge-oxford': ('1599833975787-5c143f373c30', 'K. Mitch Hodge', 'kmitchhodge'),
    'london-photography-walk': ('1681407979872-0a4cbde28391', 'Jacob Diehl', 'jacob_diehl_film'),
    'bath-cotswolds': ('1568144510602-c4082cb85d43', 'Magda Vrabetz', '_twistedplot'),
    # paises
    'Ireland':        ('1570875450638-044bca38ec92', 'Saad Chaudhry', 'saadchdhry'),
    'United Kingdom': ('1599833975787-5c143f373c30', 'K. Mitch Hodge', 'kmitchhodge'),
    'France':         ('1502602898657-3e91760cbb34', 'Chris Karidis', 'chriskaridis'),
    'Italy':          ('1552832230-c0197dd311b5', 'David Kohler', 'davidkhlr'),
    'Spain':          ('1661442196029-ecc4a8e0a0b8', 'Tania Mousinho', 'shotsbytania'),
    'Portugal':       ('1599069158346-684fee0e414a', 'Andre Lergier', 'andrelergier'),
}

UNS = 'https://images.unsplash.com/photo-'
UTM = '?utm_source=exclusive_world_tours&utm_medium=referral'


def img_url(fid, w):
    return ('%s%s?auto=format&crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=76&w=%d'
            % (UNS, fid, w))


def e(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def euros(v):
    if v is None:
        return None
    return ('%d' % v) if float(v).is_integer() else ('%.2f' % v)


def mosaico(nome, i, chave=None, alt=None, larguras=(500, 900)):
    """O mosaico de um destino.

    Por baixo esta sempre o gradiente com o nome: e a rede de seguranca.
    Por cima entra a fotografia, quando existe uma para esta chave. Se a
    imagem nao carregar — ligacao lenta, ou um visualizador que bloqueie
    dominios de fora — o `onerror` esconde-a e fica o mosaico, que e
    legivel e nao parece avariado.
    """
    a, b = GRADIENTES[i % len(GRADIENTES)]
    foto = FOTOS.get(chave if chave is not None else nome)
    img = ''
    if foto:
        fid = foto[0]
        img = ('<img src="%s" srcset="%s" sizes="(min-width:1020px) 320px, 100vw" '
               'loading="lazy" decoding="async" alt="%s" '
               'onerror="this.style.display=&quot;none&quot;">'
               % (img_url(fid, larguras[1]),
                  ', '.join('%s %dw' % (img_url(fid, w), w) for w in larguras),
                  e(alt or nome)))
    return ('<span class="foto" style="--a:%s;--b:%s">'
            '<span class="foto-nome" aria-hidden="true">%s</span>%s</span>'
            % (a, b, e(nome), img))


def cartao_destino(cidade, ts, i, pais, menor, coord):
    return '''<a class="destino" href="/tours/?country=%s">
  %s
  <span class="destino-txt">
    <span class="d-meta">%s &middot; %d %s</span>
    <span class="d-preco">%s</span>
  </span>
</a>''' % (e(ts[0]['country']),
           mosaico(cidade, i, alt='%s, %s' % (cidade, pais)), e(pais),
           len(ts), 'tour' if len(ts) == 1 else 'tours',
           ('from &euro;%s' % euros(menor)) if menor else 'Price on request')


def cartao_tour(t, i):
    d = t['durations'][0]
    lot = d['tiers'][-1].get('max', 16) if d.get('tiers') else 16
    preco = euros(d.get('price'))
    return '''<a class="produto" href="/tours/%s/">
  %s
  <span class="produto-corpo">
    <span class="p-sitio">%s &middot; %s</span>
    <span class="p-nome">%s</span>
    <span class="p-meta">%s &middot; up to %d &middot; free cancellation</span>
    <span class="p-preco"><span class="de">From</span>
      <span class="v">&euro;%s</span><span class="un">per vehicle</span></span>
  </span>
</a>''' % (e(t['slug']),
           mosaico(t['ticketTo'] if t.get('ticketTo') else t['city'], i,
                   chave=t['slug'], alt=t['title'], larguras=(420, 760)),
           e(NOME_PAIS.get(t['country'], t['countryName'])), e(t['city']),
           e(t['title']), e(d['h']), lot, preco or '—')


def main():
    atlas = json.load(open(os.path.join(RAIZ, 'assets', 'atlas.json')))
    tours = json.load(open(os.path.join(RAIZ, 'tools', 'tours.json')))['tours']

    por_cidade, por_pais = {}, {}
    for t in tours:
        por_cidade.setdefault(t['city'], []).append(t)
        por_pais.setdefault(t['country'], []).append(t)

    def menor_preco(ts):
        return min((x['durations'][0]['price'] for x in ts
                    if x['durations'][0].get('price')), default=None)

    # ---- destinos: os oito com mais tours
    ordem = sorted(por_cidade.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    destinos = []
    for i, (cidade, ts) in enumerate(ordem[:8]):
        c = atlas['cidades'].get(cidade)
        destinos.append(cartao_destino(
            cidade, ts, i, NOME_PAIS.get(ts[0]['country'], ts[0]['countryName']),
            menor_preco(ts), c))

    # ---- fila de Dublin e fila de Londres: as duas cidades com mais tours
    filas = []
    for cidade, ts in ordem[:2]:
        cartoes = '\n'.join(cartao_tour(t, j) for j, t in enumerate(ts[:4]))
        filas.append('''<section class="secao" aria-labelledby="h-%s">
  <div class="largura">
    <div class="secao-cab">
      <div>
        <h2 id="h-%s">Private day tours from %s</h2>
        <p>%d %s, all leaving from your hotel door.</p>
      </div>
      <a class="ligacao" href="/tours/?country=%s">See all %s tours</a>
    </div>
    <div class="produtos">%s</div>
  </div>
</section>''' % (e(cidade.lower().replace(' ', '-')),
                 e(cidade.lower().replace(' ', '-')), e(cidade), len(ts),
                 'tour' if len(ts) == 1 else 'tours',
                 e(ts[0]['country']), e(cidade), cartoes))

    # ---- paises
    paises = []
    for i, (slug, nome) in enumerate(PAISES):
        ts = por_pais.get(slug, [])
        if not ts:
            continue
        cidades = sorted({x['city'] for x in ts})
        paises.append(
            '<a class="pais" href="/tours/?country=%s">%s<span class="pais-txt">'
            '<span class="pa-nome">%s</span>'
            '<span class="pa-meta">%d tours &middot; %d %s</span>'
            '<span class="pa-preco">%s</span></span></a>'
            % (e(slug), mosaico(nome, i, alt='Private day tours in %s' % nome,
                                  larguras=(600, 1100)),
               e(nome), len(ts), len(cidades),
               'city' if len(cidades) == 1 else 'cities',
               ('from &euro;%s' % euros(menor_preco(ts))) if menor_preco(ts)
               else 'Price on request'))

    # ---- o rodape de ligacoes, por pais
    ligacoes = []
    for slug, nome in PAISES:
        ts = por_pais.get(slug, [])
        if not ts:
            continue
        itens = ''.join(
            '<li><a href="/tours/%s/">%s</a></li>' % (e(x['slug']), e(x['title']))
            for x in ts)
        ligacoes.append('<div class="col"><h4>%s</h4><ul>%s</ul></div>'
                        % (e(nome), itens))

    vistos, creditos = set(), []
    for fid, nome, utilizador in FOTOS.values():
        if utilizador in vistos:
            continue
        vistos.add(utilizador)
        creditos.append('<a href="https://unsplash.com/@%s%s">%s</a>'
                        % (e(utilizador), UTM, e(nome)))

    hid, hnome, huser = FOTOS['hero']
    hero_srcset = ', '.join('%s %dw' % (img_url(hid, w), w)
                            for w in (900, 1400, 2000, 2600))

    html = (MODELO
            .replace('{{HERO_SRC}}', img_url(hid, 2000))
            .replace('{{HERO_SRCSET}}', hero_srcset)
            .replace('{{HERO_NOME}}', e(hnome))
            .replace('{{HERO_USER}}', e(huser))
            .replace('{{CREDITOS}}', ', '.join(creditos))
            .replace('{{DESTINOS}}', '\n'.join(destinos))
            .replace('{{FILAS}}', '\n'.join(filas))
            .replace('{{PAISES}}', '\n'.join(paises))
            .replace('{{LIGACOES}}', '\n'.join(ligacoes))
            .replace('{{N_TOURS}}', str(len(tours)))
            .replace('{{N_PAISES}}', str(len(por_pais)))
            .replace('{{N_CIDADES}}', str(len(por_cidade))))

    # A barra de revisao e o diagnostico so entram com --revisao; em
    # producao saem fora, junto com o <script> que os faz funcionar.
    if '--revisao' not in sys.argv:
        for abre, fecha in (('<div class="diag"', '</div>'),
                            ('<div class="revisao">', '</div>\n</div>'),
                            ('<script>\n/* Diagnostico das fotografias', '</script>')):
            i = html.find(abre)
            if i == -1:
                continue
            j = html.find(fecha, i)
            if j == -1:
                continue
            html = html[:i] + html[j + len(fecha):]

    destino = os.path.join(RAIZ, 'index-marketplace.html'
                           if '--revisao' in sys.argv else 'index.html')
    with open(destino, 'w') as f:
        f.write(html)
    print('escrito: %s (%.0f KB)' % (destino, os.path.getsize(destino) / 1024))
    print('%d destinos, %d filas, %d paises, %d tours nas ligacoes'
          % (len(destinos), len(filas), len(paises), len(tours)))


MODELO = r'''<!DOCTYPE html>
<html lang="en" data-pal="indigo">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Exclusive World Tours</title>
<meta name="description" content="Private day tours in six countries, booked direct with named local operators. One vehicle for your group, priced by group size.">
<meta name="robots" content="noindex, nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
/* =========================================================================
   Exclusive World Tours — homepage, direcao "Marketplace"

   A estrutura e a convencional: pesquisa grande, barra de confianca,
   mosaico de destinos, filas de produtos, grelha de paises, porque
   reservar connosco, ligacoes por pais, rodape.

   Enquanto nao houver fotografia, cada mosaico e um gradiente com o
   nome do destino. A classe .foto ja aceita uma <img> por cima no dia
   em que as imagens chegarem — nao e preciso mexer no resto.
   ========================================================================= */

:root{
  --branco:#FFFFFF;
  --p:#4338CA; --pf:#352BA3; --tint:#EEEDFB;
  --sup:#F6F6FA; --tinta:#161629; --mudo:#5B5B70; --linha:#E4E4EE;
  --rodape-mudo:#A8AAB8;   /* 5.9:1 na paleta mais clara das tres */
  --raio:14px; --raio-p:10px; --pill:999px;
  --sombra:0 1px 2px rgba(22,22,41,.06), 0 8px 20px -8px rgba(22,22,41,.12);
  --sombra-f:0 2px 6px rgba(22,22,41,.08), 0 18px 36px -12px rgba(22,22,41,.20);
  --ui:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif;
  --e1:4px; --e2:8px; --e3:12px; --e4:16px; --e5:20px;
  --e6:28px; --e7:40px; --e8:56px; --e9:76px;
}
html[data-pal="teal"]{--p:#0E6E6B;--pf:#0A5250;--tint:#E3F0EE;--sup:#F4F7F6;
  --tinta:#17322F;--mudo:#55666400;--mudo:#556664;--linha:#E2EAE8}
html[data-pal="rosa"]{--p:#B3246B;--pf:#8C1A53;--tint:#FBE8F1;--sup:#FBF5F8;
  --tinta:#2B1522;--mudo:#6B5260;--linha:#EEE1E8}

*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--branco);color:var(--tinta);font-family:var(--ui);
     font-size:16px;line-height:1.55;-webkit-font-smoothing:antialiased}
img,svg{max-width:100%;height:auto;display:block}
h1,h2,h3{margin:0;font-weight:700;letter-spacing:-0.03em;line-height:1.12}
h1{font-size:clamp(1.9rem, 1.3rem + 2.2vw, 3rem);letter-spacing:-0.038em}
h2{font-size:clamp(1.35rem, 1.1rem + 1vw, 1.75rem)}
h3{font-size:1rem;font-weight:600;letter-spacing:-0.02em}
p{margin:0 0 var(--e4);max-width:62ch}
p:last-child{margin-bottom:0}
a{color:inherit;text-decoration:none}
.num,.d-preco,.p-preco,.pa-preco{font-variant-numeric:tabular-nums}
:focus-visible{outline:2px solid var(--p);outline-offset:2px}
@media(prefers-reduced-motion:reduce){*{transition-duration:.001ms!important}}
.salto{position:absolute;left:-9999px;background:var(--p);color:#fff;
       padding:var(--e3) var(--e5);z-index:300;border-radius:var(--pill);font-weight:600}
.salto:focus{left:var(--e4);top:var(--e4)}
.invisivel{position:absolute;width:1px;height:1px;padding:0;margin:-1px;
           overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
.largura{width:100%;max-width:1280px;margin-inline:auto;padding-inline:var(--e4)}
@media(min-width:900px){.largura{padding-inline:var(--e6)}}


/* ----------------------------------------- diagnostico (so na revisao) */
.diag{position:sticky;top:0;z-index:400;font-family:var(--ui);font-size:14px;
  font-weight:600;padding:12px var(--e4);text-align:center;color:#fff;
  background:#5B5B70}
.diag.ok{background:#146C43}
.diag.mal{background:#A32B2B}
.diag small{display:block;font-weight:400;font-size:12.5px;opacity:.92;
            margin-top:3px}

/* ------------------------------------------- barra de revisao (so aqui) */
.revisao{background:var(--sup);border-bottom:1px solid var(--linha);
         padding:var(--e3) 0;font-size:13px}
.revisao-in{display:flex;flex-wrap:wrap;gap:var(--e3) var(--e5);align-items:center}
.revisao legend{color:var(--mudo);margin-right:var(--e3)}
.revisao fieldset{border:0;margin:0;padding:0;display:flex;gap:6px;flex-wrap:wrap}
.revisao button{font-family:var(--ui);font-size:13px;cursor:pointer;
  background:var(--branco);color:var(--tinta);border:1px solid var(--linha);
  border-radius:var(--pill);padding:7px 15px;min-height:34px}
.revisao button[aria-pressed="true"]{background:var(--p);color:#fff;border-color:var(--p)}
.revisao .nota{color:var(--mudo);flex:1 1 200px}

/* ============================================================== cabecalho */
.cabeca{background:var(--branco);border-bottom:1px solid var(--linha);
        position:sticky;top:0;z-index:150}
.cabeca-in{display:flex;align-items:center;gap:var(--e4);min-height:70px}
.marca{font-weight:700;font-size:15px;letter-spacing:-0.025em;color:var(--p);
       line-height:1.15;flex:0 0 auto}
.marca small{display:block;font-weight:500;font-size:10px;letter-spacing:.13em;
             color:var(--mudo);margin-top:2px}
.busca-top{display:none;flex:1 1 auto;max-width:420px;align-items:center;
  border:1px solid var(--linha);border-radius:var(--pill);padding-left:var(--e4);
  box-shadow:var(--sombra)}
@media(min-width:1000px){.busca-top{display:flex}}
.busca-top svg{color:var(--mudo);flex:0 0 auto}
.busca-top input{flex:1 1 auto;min-width:0;border:0;background:transparent;
  font-family:var(--ui);font-size:14.5px;color:var(--tinta);padding:0 var(--e3);
  min-height:44px}
.busca-top input:focus{outline:0}
.menu{display:none;gap:var(--e5);margin-left:auto;align-items:center}
@media(min-width:1180px){.menu{display:flex}}
.menu a{font-size:14.5px}
.menu a:hover{color:var(--p)}

/* ================================================================== heroi */
/* O heroi e fotografia a toda a largura, nao um campo de cor.
   Por cima da imagem vai um veu escuro em gradiente: sem ele o texto
   branco deixa de se ler quando a fotografia tem ceu claro, e isso
   muda de fotografia para fotografia. O veu garante o contraste seja
   qual for a imagem que la esteja. */
.heroi{position:relative;background:#081320;color:#fff;overflow:hidden;
       padding-block:var(--e9) var(--e9);min-height:clamp(440px,52vw,620px);
       display:flex;align-items:center}
.heroi-foto{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
            z-index:0;max-width:none}
.heroi::after{content:'';position:absolute;inset:0;z-index:1;pointer-events:none;
  background:linear-gradient(100deg, rgba(8,19,32,.86) 0%,
             rgba(8,19,32,.72) 44%, rgba(8,19,32,.38) 74%,
             rgba(8,19,32,.24) 100%)}
.heroi>.largura{position:relative;z-index:2}
.heroi h1{color:#fff;max-width:19ch;
          text-shadow:0 1px 20px rgba(0,0,0,.35)}
.heroi .sub{color:rgba(255,255,255,.94);margin-top:var(--e4);max-width:52ch;
            font-size:17px;text-shadow:0 1px 14px rgba(0,0,0,.35)}
.heroi-credito{position:absolute;right:var(--e4);bottom:var(--e3);z-index:3;
  font-size:11.5px;color:rgba(255,255,255,.72)}
.heroi-credito a{text-decoration:underline;text-underline-offset:2px}
.procura{margin-top:var(--e7);background:var(--branco);border-radius:var(--raio);
  padding:var(--e2);display:grid;gap:var(--e2);box-shadow:var(--sombra-f)}
@media(min-width:760px){
  .procura{grid-template-columns:minmax(0,1.5fr) minmax(154px,1fr)
           minmax(112px,.7fr) auto}
}
.procura .campo{padding:var(--e3) var(--e4);min-width:0;border-radius:var(--raio-p)}
.procura .campo+.campo{border-top:1px solid var(--linha)}
@media(min-width:760px){.procura .campo+.campo{border-top:0;
                                               border-left:1px solid var(--linha)}}
.procura label{display:block;font-size:12px;font-weight:600;color:var(--mudo);
               margin-bottom:2px}
.procura input,.procura select{width:100%;border:0;background:transparent;
  font-family:var(--ui);font-size:15.5px;color:var(--tinta);min-height:30px;padding:0}
.procura input:focus,.procura select:focus{outline:0}
.procura .ir{display:flex;align-items:center;justify-content:center;gap:var(--e2);
  background:var(--p);color:#fff;border:0;border-radius:var(--raio-p);
  font-family:var(--ui);font-size:16px;font-weight:600;cursor:pointer;
  min-height:60px;padding-inline:var(--e7);white-space:nowrap}
.procura .ir:hover{background:var(--pf)}
.atalhos{display:flex;flex-wrap:wrap;gap:var(--e2);margin:var(--e5) 0 0;
         list-style:none;padding:0;font-size:14px}
.atalhos span{color:rgba(255,255,255,.94);margin-right:var(--e2)}
.atalhos a{border:1px solid rgba(255,255,255,.46);border-radius:var(--pill);
           padding:6px 14px;background:rgba(8,19,32,.34)}
.atalhos a:hover{background:rgba(255,255,255,.14)}

/* ======================================================== barra de confianca */
.confianca{border-bottom:1px solid var(--linha);background:var(--sup)}
.confianca ul{display:grid;gap:var(--e4);list-style:none;margin:0;padding:0;
              padding-block:var(--e5)}
@media(min-width:720px){.confianca ul{grid-template-columns:repeat(4,1fr);
                                      gap:var(--e5)}}
.confianca li{display:grid;grid-template-columns:22px 1fr;gap:var(--e3);
              align-items:start;font-size:14px}
.confianca svg{color:var(--p);margin-top:1px}
.confianca b{display:block;font-weight:600}
.confianca span{color:var(--mudo)}

/* ================================================================= seccoes */
.secao{padding-block:var(--e9)}
.secao-sup{background:var(--sup)}
.secao-cab{display:flex;flex-wrap:wrap;gap:var(--e4);align-items:flex-end;
           justify-content:space-between;margin-bottom:var(--e6)}
.secao-cab p{color:var(--mudo);margin:var(--e2) 0 0}
.ligacao{font-size:15px;font-weight:600;color:var(--p);white-space:nowrap}
.ligacao:hover{text-decoration:underline;text-underline-offset:3px}

/* ============================================= o mosaico que substitui foto */
.foto{display:grid;place-items:center;position:relative;overflow:hidden;
  background:linear-gradient(140deg, var(--a) 0%, var(--b) 100%);
  isolation:isolate}
.foto::after{content:'';position:absolute;inset:0;
  background:radial-gradient(120% 80% at 18% 12%, rgba(255,255,255,.22) 0%,
             transparent 55%);pointer-events:none}
.foto>img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
  z-index:2;max-width:none}
.foto-nome{position:relative;z-index:1;color:#fff;font-weight:700;
  letter-spacing:-0.03em;font-size:clamp(1.1rem,.9rem + 1vw,1.6rem);
  text-align:center;padding:var(--e4);line-height:1.1;
  text-shadow:0 1px 10px rgba(0,0,0,.28)}

/* =============================================================== destinos */
.destinos{display:grid;gap:var(--e4)}
@media(min-width:560px){.destinos{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(min-width:900px){.destinos{grid-template-columns:repeat(4,minmax(0,1fr))}}
.destino{border-radius:var(--raio);overflow:hidden;background:var(--branco);
  border:1px solid var(--linha);display:flex;flex-direction:column;
  transition:box-shadow .18s ease, transform .18s ease}
.destino:hover{box-shadow:var(--sombra-f);transform:translateY(-2px)}
.destino .foto{aspect-ratio:4/3}
.destino-txt{padding:var(--e4);display:flex;flex-direction:column;gap:3px}
.d-nome{font-weight:700;font-size:16px;letter-spacing:-0.025em}
.d-meta{font-size:13.5px;color:var(--mudo);font-weight:500}
.d-preco{font-size:14px;font-weight:600;color:var(--p);margin-top:var(--e2)}

/* ============================================================== produtos */
.produtos{display:grid;gap:var(--e5)}
@media(min-width:580px){.produtos{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(min-width:1020px){.produtos{grid-template-columns:repeat(4,minmax(0,1fr))}}
.produto{background:var(--branco);border:1px solid var(--linha);
  border-radius:var(--raio);overflow:hidden;display:flex;flex-direction:column;
  transition:box-shadow .18s ease, transform .18s ease}
.produto:hover{box-shadow:var(--sombra-f);transform:translateY(-2px)}
.produto .foto{aspect-ratio:3/2}
.produto-corpo{padding:var(--e4);display:flex;flex-direction:column;gap:5px;
               flex:1 1 auto}
.p-sitio{font-size:11.5px;color:var(--mudo);letter-spacing:.05em;
         text-transform:uppercase}
.p-nome{font-size:15.5px;font-weight:600;letter-spacing:-0.02em;line-height:1.3}
.p-meta{font-size:13px;color:var(--mudo);margin-top:auto}
.p-preco{display:flex;align-items:baseline;gap:6px;flex-wrap:wrap;
  border-top:1px solid var(--linha);margin-top:var(--e3);padding-top:var(--e3)}
.p-preco .de{font-size:12.5px;color:var(--mudo)}
.p-preco .v{font-size:1.25rem;font-weight:700;letter-spacing:-0.035em;color:var(--pf)}
.p-preco .un{font-size:12px;color:var(--mudo)}

/* ================================================================= paises */
.paises{display:grid;gap:var(--e4)}
@media(min-width:560px){.paises{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(min-width:960px){.paises{grid-template-columns:repeat(3,minmax(0,1fr))}}
.pais{position:relative;border-radius:var(--raio);overflow:hidden;
  display:grid;transition:transform .18s ease}
.pais:hover{transform:translateY(-2px)}
.pais .foto{grid-area:1/1;aspect-ratio:16/7}
/* O nome do pais vive na legenda; no mosaico ficaria a dobrar. */
.pais .foto-nome{display:none}
.pais-txt{grid-area:1/1;position:relative;z-index:2;align-self:end;
  padding:var(--e5);display:flex;flex-direction:column;gap:2px;color:#fff;
  background:linear-gradient(to top, rgba(10,10,24,.72) 0%,
             rgba(10,10,24,.30) 55%, transparent 100%)}
.pa-nome{font-weight:700;font-size:1.25rem;letter-spacing:-0.03em}
.pa-meta{font-size:13.5px;color:rgba(255,255,255,.90)}
.pa-preco{font-size:14px;font-weight:600;margin-top:var(--e2)}

/* ================================================================= porque */
.porque{display:grid;gap:var(--e7)}
@media(min-width:760px){.porque{grid-template-columns:repeat(3,1fr)}}
.porque .n{display:grid;place-items:center;width:40px;height:40px;
  border-radius:var(--pill);background:var(--tint);color:var(--pf);
  font-weight:700;font-size:14px;margin-bottom:var(--e4)}
.porque h3{margin-bottom:var(--e2)}
.porque p{font-size:15px;color:var(--mudo);max-width:38ch}

/* ============================================================== ligacoes */
.ligacoes{display:grid;gap:var(--e6)}
@media(min-width:620px){.ligacoes{grid-template-columns:repeat(2,1fr)}}
@media(min-width:1000px){.ligacoes{grid-template-columns:repeat(3,1fr)}}
.ligacoes h4{font-size:13px;margin:0 0 var(--e3);font-weight:700}
.ligacoes ul{list-style:none;margin:0;padding:0}
.ligacoes li{margin-bottom:7px;font-size:13.5px;color:var(--mudo)}
.ligacoes a:hover{color:var(--p);text-decoration:underline;
                  text-underline-offset:2px}

/* ============================================================== creditos */
.creditos{border-top:1px solid var(--linha);padding-block:var(--e5)}
.creditos p{font-size:12.5px;color:var(--mudo);max-width:none;margin:0}
.creditos a{text-decoration:underline;text-underline-offset:2px}
.creditos a:hover{color:var(--p)}

/* ================================================================ rodape */
.rodape{background:var(--tinta);color:#C3C3D2;padding-block:var(--e8) var(--e5)}
.rodape-grelha{display:grid;gap:var(--e6)}
@media(min-width:760px){.rodape-grelha{grid-template-columns:2fr 1fr 1fr 1fr}}
.rodape .marca{color:#fff}
.rodape .marca small{color:var(--rodape-mudo)}
.rodape h4{font-size:12px;color:#fff;margin:0 0 var(--e3);font-weight:600;
           letter-spacing:.08em;text-transform:uppercase}
.rodape ul{list-style:none;margin:0;padding:0}
.rodape li{margin-bottom:7px;font-size:14px}
.rodape a:hover{color:#fff}
.rodape-fim{margin-top:var(--e7);padding-top:var(--e4);
  border-top:1px solid rgba(255,255,255,.16);display:flex;flex-wrap:wrap;
  gap:var(--e3);justify-content:space-between;font-size:13px}
.pagamentos{display:flex;flex-wrap:wrap;gap:var(--e3);margin-top:var(--e3)}
.pagamentos li{font-size:12.5px;color:var(--rodape-mudo);margin:0}
</style>
</head>
<body>

<a class="salto" href="#conteudo">Skip to content</a>

<div class="diag" id="diag" role="status">A verificar as fotografias&hellip;</div>

<div class="revisao">
  <div class="largura revisao-in">
    <fieldset>
      <legend>Paleta</legend>
      <button type="button" data-val="indigo" aria-pressed="true">Índigo</button>
      <button type="button" data-val="teal" aria-pressed="false">Petróleo</button>
      <button type="button" data-val="rosa" aria-pressed="false">Magenta</button>
    </fieldset>
    <p class="nota">Barra de revisão, não existe no site. Os mosaicos coloridos são onde entram as fotografias.</p>
  </div>
</div>

<header class="cabeca">
  <div class="largura cabeca-in">
    <a href="/" class="marca">Exclusive World Tours<small>PRIVATE DAY TOURS</small></a>
    <form class="busca-top" role="search" action="/tours/">
      <svg width="17" height="17" viewBox="0 0 18 18" aria-hidden="true">
        <circle cx="7.6" cy="7.6" r="5.4" fill="none" stroke="currentColor" stroke-width="1.8"/>
        <path d="M11.6 11.6l4.3 4.3" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
      </svg>
      <label class="invisivel" for="qt">Search tours</label>
      <input id="qt" name="q" type="search" placeholder="Search {{N_TOURS}} private day tours">
    </form>
    <nav class="menu" aria-label="Main">
      <a href="/tours/">All tours</a>
      <a href="/suppliers/">For operators</a>
      <!-- TRANSFERES: a decidir se aponta para airportlink.app ou para
           uma pagina propria. Ver a nota no fim deste ficheiro. -->
      <a href="/journal/">Journal</a>
      <a href="/contact/">Help</a>
    </nav>
  </div>
</header>

<section class="heroi">
  <img class="heroi-foto" src="{{HERO_SRC}}" srcset="{{HERO_SRCSET}}" sizes="100vw"
       width="2400" height="1600" fetchpriority="high"
       alt="A coast road winding along the water, seen from above"
       onerror="this.style.display='none'">
  <div class="largura">
    <h1>Private day tours in {{N_PAISES}} countries, booked direct.</h1>
    <p class="sub">{{N_TOURS}} full days with a vehicle for your group and
    nobody else, from {{N_CIDADES}} cities. Priced per vehicle, not per person.</p>

    <form class="procura" action="/tours/">
      <div class="campo">
        <label for="onde">Destination</label>
        <input id="onde" name="q" type="search" placeholder="Dublin, Rome, Lisbon…">
      </div>
      <div class="campo">
        <label for="quando">When</label>
        <input id="quando" name="date" type="date">
      </div>
      <div class="campo">
        <label for="quantos">Travellers</label>
        <select id="quantos" name="pax">
          <option>1</option><option>2</option><option>3</option>
          <option selected>4</option><option>5</option><option>6</option>
          <option>7</option><option>8</option><option>9</option><option>10</option>
          <option>11</option><option>12</option><option>13</option>
          <option>14</option><option>15</option><option>16</option>
        </select>
      </div>
      <button type="submit" class="ir">Search</button>
    </form>

    <ul class="atalhos">
      <li><span>Popular:</span></li>
      <li><a href="/tours/?country=ireland">Dublin</a></li>
      <li><a href="/tours/?country=uk">London</a></li>
      <li><a href="/tours/?country=france">Paris</a></li>
      <li><a href="/tours/?country=italy">Rome</a></li>
      <li><a href="/tours/?country=portugal">Lisbon</a></li>
    </ul>
  </div>
  <p class="heroi-credito">Photograph by
    <a href="https://unsplash.com/@{{HERO_USER}}?utm_source=exclusive_world_tours&amp;utm_medium=referral">{{HERO_NOME}}</a></p>
</section>

<div class="confianca">
  <div class="largura">
    <ul>
      <li><svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 16.5V9.8l2-4.3h12l2 4.3v6.7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><circle cx="7.5" cy="16.5" r="1.9" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="16.5" cy="16.5" r="1.9" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>
        <div><b>Priced per vehicle</b><span>Not per person. The group decides the price.</span></div></li>
      <li><svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><path d="M3.5 12.4l5 5 11-11.4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <div><b>Free cancellation</b><span>Full refund up to 24 hours before.</span></div></li>
      <li><svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="8.4" r="3.6" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M4.6 20c0-4 3.3-6.8 7.4-6.8s7.4 2.8 7.4 6.8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
        <div><b>Named local operators</b><span>You book their day, through us.</span></div></li>
      <li><svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <div><b>Customisable</b><span>Change the stops on the day.</span></div></li>
    </ul>
  </div>
</div>

<main id="conteudo">

<section class="secao" aria-labelledby="h-dest">
  <div class="largura">
    <div class="secao-cab">
      <div>
        <h2 id="h-dest">Popular destinations</h2>
        <p>The eight cities with the most private days.</p>
      </div>
      <a class="ligacao" href="/tours/">All {{N_CIDADES}} cities</a>
    </div>
    <div class="destinos">{{DESTINOS}}</div>
  </div>
</section>

{{FILAS}}

<section class="secao secao-sup" aria-labelledby="h-pais">
  <div class="largura">
    <div class="secao-cab">
      <div>
        <h2 id="h-pais">Browse by country</h2>
        <p>{{N_TOURS}} tours across {{N_PAISES}} countries.</p>
      </div>
    </div>
    <div class="paises">{{PAISES}}</div>
  </div>
</section>

<section class="secao" aria-labelledby="h-porque">
  <div class="largura">
    <div class="secao-cab"><h2 id="h-porque">Why book here</h2></div>
    <div class="porque">
      <div>
        <span class="n">1</span>
        <h3>The vehicle, not a seat</h3>
        <p>Sedan, van, or two vehicles travelling together. The price follows
        the size of your group and nobody else rides with you.</p>
      </div>
      <div>
        <span class="n">2</span>
        <h3>Direct with the operator</h3>
        <p>Every day belongs to a local operator with a name and a licence.
        We handle the booking; they drive the day.</p>
      </div>
      <div>
        <span class="n">3</span>
        <h3>Nothing is fixed but the start</h3>
        <p>Stretch the stop you love, skip the one you don't. Tell your guide
        in the morning or decide over lunch.</p>
      </div>
    </div>
  </div>
</section>

<section class="secao secao-sup" aria-labelledby="h-lig">
  <div class="largura">
    <div class="secao-cab">
      <div>
        <h2 id="h-lig">Every tour we run</h2>
        <p>All {{N_TOURS}} days, by country.</p>
      </div>
    </div>
    <div class="ligacoes">{{LIGACOES}}</div>
  </div>
</section>

</main>

<div class="creditos">
  <div class="largura">
    <p>Photographs by {{CREDITOS}} on
    <a href="https://unsplash.com/?utm_source=exclusive_world_tours&amp;utm_medium=referral">Unsplash</a>.
    Placeholders until our operators' own photography is in place.</p>
  </div>
</div>

<footer class="rodape">
  <div class="largura">
    <div class="rodape-grelha">
      <div>
        <span class="marca">Exclusive World Tours<small>PRIVATE DAY TOURS</small></span>
        <p style="color:var(--rodape-mudo);font-size:14px;max-width:32ch;margin-top:var(--e4)">Private
        day tours in six countries, run by named local operators.</p>
        <p style="font-size:13px;margin-top:var(--e6);color:#fff">Secure online payment with Stripe</p>
        <ul class="pagamentos"><li>Visa</li><li>Mastercard</li><li>PayPal</li><li>Apple Pay</li><li>Google Pay</li></ul>
      </div>
      <div><h4>Travellers</h4><ul><li><a href="/tours/">All tours</a></li>
        <li><a href="/cancellation/">Cancellation policy</a></li>
        <li><a href="/journal/">Journal</a></li>
        <li><a href="/contact/">Help</a></li></ul></div>
      <div><h4>Operators</h4><ul><li><a href="/suppliers/">How selling here works</a></li>
        <li><a href="/suppliers/apply/">List your tours</a></li></ul></div>
      <div><h4>Destinations</h4><ul><li><a href="/tours/?country=ireland">Ireland</a></li>
        <li><a href="/tours/?country=uk">United Kingdom</a></li><li><a href="/tours/?country=france">France</a></li>
        <li><a href="/tours/?country=italy">Italy</a></li><li><a href="/tours/?country=spain">Spain</a></li>
        <li><a href="/tours/?country=portugal">Portugal</a></li></ul></div>
    </div>
    <div class="rodape-fim">
      <span>&copy; 2026 Exclusive World Tours</span>
      <span>53.3500&deg; N, 6.2603&deg; W</span>
    </div>
  </div>
</footer>

<script>
/* Diagnostico das fotografias: conta quantas <img> carregaram mesmo.
   Serve para responder de uma vez a pergunta "porque e que nao vejo as
   fotos" — a pagina diz-o em vez de eu ter de adivinhar. */
(function () {
  var caixa = document.getElementById('diag');
  if (!caixa) return;
  var imgs = [].slice.call(document.images).filter(function (i) {
    return /images\.unsplash\.com/.test(i.currentSrc || i.src);
  });
  function carregada(i) { return i.complete && i.naturalWidth > 0; }
  function contar() {
    var ok = imgs.filter(carregada).length;
    var pendentes = imgs.filter(function (i) { return !i.complete; }).length;
    if (pendentes) { caixa.textContent = 'A carregar as fotografias\u2026 ' + ok + ' de ' + imgs.length; return; }
    if (ok === imgs.length && ok > 0) {
      caixa.className = 'diag ok';
      caixa.innerHTML = 'As ' + ok + ' fotografias carregaram.' +
        '<small>Est\u00e1s a ver a p\u00e1gina como um cliente a veria.</small>';
    } else if (ok > 0) {
      caixa.className = 'diag';
      caixa.innerHTML = ok + ' de ' + imgs.length + ' fotografias carregaram.' +
        '<small>Liga\u00e7\u00e3o lenta, ou algumas est\u00e3o bloqueadas.</small>';
    } else {
      caixa.className = 'diag mal';
      caixa.innerHTML = 'Nenhuma das ' + imgs.length + ' fotografias carregou aqui.' +
        '<small>O images.unsplash.com est\u00e1 bloqueado neste visualizador. ' +
        'Descarrega o ficheiro e abre-o no Chrome, ou espera pelo site no Render.</small>';
    }
  }
  imgs.forEach(function (i) {
    if (!i.complete) { i.addEventListener('load', contar); i.addEventListener('error', contar); }
  });
  contar();
  setTimeout(contar, 1200);
  setTimeout(contar, 4000);
})();

document.querySelectorAll('.revisao button').forEach(function (b) {
  b.addEventListener('click', function () {
    document.documentElement.setAttribute('data-pal', b.dataset.val);
    document.querySelectorAll('.revisao button').forEach(function (o) {
      o.setAttribute('aria-pressed', String(o === b));
    });
  });
});
</script>

</body>
</html>'''


if __name__ == '__main__':
    main()

# ---------------------------------------------------------------------
# NOTA SOBRE OS TRANSFERES DE AEROPORTO
#
# A homepage tinha "Airport transfers" no menu e no rodape, a apontar
# para /airporttransfers/, que nunca existiu — eram dois 404 na pagina
# mais vista do site.
#
# Para onde deve apontar e uma decisao do Ricardo e nao minha:
#
#   a) para https://www.airportlink.app/ — e a empresa dele que faz
#      transferes, e o cliente que acaba um tour precisa do aeroporto.
#      Manda trafego para fora deste dominio.
#   b) para uma pagina /airporttransfers/ neste site, com o widget da
#      Airportlink (data-src="exclusiveworldtours") la dentro. Fica tudo
#      no mesmo dominio, mas e uma pagina que ainda nao esta escrita.
#
# Enquanto nao decidir, as duas ligacoes estao desligadas e marcadas
# com TRANSFERES aqui em cima. Voltam numa linha.
# ---------------------------------------------------------------------
