#!/usr/bin/env python3
"""
Verificacoes que correm sobre as paginas ja geradas.

Existe por uma razao concreta: tres vezes seguidas uma regra de CSS
ficou so na homepage e a pagina de resultados saiu partida — o botao sem
estilo, os cartoes como texto corrido. Sao erros que nao rebentam nada,
nao dao erro nenhum, e so se veem a olho. Por isso passam a ser
verificados por uma maquina.

    python3 tools/verificar.py
"""

import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

import glob

# TODAS as paginas geradas, e nao uma lista a mao
#
# Isto era uma lista escrita a mao e falhou exatamente como se esperava:
# acrescentei tres paginas novas (/booking-confirmed/, /admin/bookings/ e
# /portal/bookings/) e nenhuma delas entrou na lista. As paginas
# existiam, estavam publicadas, e nao eram verificadas por ninguem — e o
# numero no fim continuava a dizer 60, que parecia bem.
#
# Agora varre-se a arvore. Uma pagina nova e verificada no dia em que
# nasce, sem ninguem se lembrar de nada. O que fica de fora e so o que
# nao e uma pagina do site: as dependencias, as provas dos logotipos e as
# paginas de trabalho.
FORA = ('node_modules', 'assets', 'sql', 'tools', '.git')

# Ficheiros na RAIZ que nao sao paginas do site: provas de desenho que
# ficaram la de quando se escolheu o logotipo e a maquete antiga do
# marketplace. Nao se apagam (nao sao meus para apagar), mas tambem nao
# sao verificados: tem links para paginas que nunca existiram e
# atributos que nao passam, e deixa-los na lista fazia o verificar.py
# reclamar para sempre de coisas que ninguem vai corrigir.
#
# ATENCAO: estao na raiz, e a raiz e servida ao publico (publishPath ".").
# https://exclusiveworldtours.com/logos3.html abre para qualquer pessoa,
# e as logos3 a 6 nao tem noindex. Vale a pena apaga-las ou mete-las numa
# pasta fora do publishPath — e uma decisao do Ricardo, nao minha.
RASCUNHOS = ('index-marketplace.html', 'logos.html', 'logos2.html',
             'logos3.html', 'logos4.html', 'logos5.html', 'logos6.html')

# As mesmas provas tambem estao em pastas proprias (/logos/, /logos2/...).
RASCUNHO_PASTAS = ('logos', 'logos2', 'logos3', 'logos4', 'logos5', 'logos6')


def _todas():
    achadas = []
    for raiz, pastas, ficheiros in os.walk(RAIZ):
        pastas[:] = [d for d in pastas
                     if not d.startswith('.') and d not in FORA]
        for f in ficheiros:
            if not f.endswith('.html'):
                continue
            rel = os.path.relpath(os.path.join(raiz, f), RAIZ)
            if rel in RASCUNHOS:
                continue
            if rel.split(os.sep)[0] in RASCUNHO_PASTAS:
                continue
            achadas.append(rel)
    return sorted(achadas)


PAGINAS = _todas()

# As paginas que falam com a base tem de levar a biblioteca E a ligacao,
# nesta ordem. Faltar uma delas nao da erro visivel: a pagina abre, nao
# faz nada, e parece lenta.
#
# Quais sao elas descobre-se a LER o HTML e nao a lembrar-se: uma pagina
# que carrega a ligacao.js esta a falar com a base, e e isso que faz
# dela uma pagina a verificar. A lista a mao que estava aqui tinha uma
# entrada repetida e tres paginas a menos.
def _com_base():
    quais = []
    for nome in PAGINAS:
        caminho = os.path.join(RAIZ, nome)
        try:
            with open(caminho) as f:
                if 'assets/ligacao.js' in f.read():
                    quais.append(nome)
        except OSError:
            pass
    return quais


COM_BASE = _com_base()

# As paginas do portal e da administracao nunca podem sair sem noindex,
# por outra razao que nao os precos: um painel de operador indexado nao
# traz clientes, traz confusao.
PRIVADAS = [x for x in COM_BASE if x.startswith(('portal/', 'admin/'))]

# Classes que aparecem no HTML e tem mesmo de ter regra no CSS da propria
# pagina. Nao e a lista toda: sao as que ja falharam ou que, se
# faltarem, estragam a pagina sem dar erro.
EXIGIDAS = ['botao', 'tour', 'tours', 'painel', 'paragem', 'galeria',
            'tour-foto', 'tour-corpo', 'tour-preco',
            'etiq', 'marca', 'topo', 'rodape', 'folha', 'pc-caixa',
            'pc-lista',
            # o portal e a administracao
            'pt-topo', 'pt-nav', 'pt-corpo', 'pt-cab', 'cx', 'campo',
            'aviso', 'est', 'bt', 'vazio', 'tab', 'rep-l', 'rep-mais',
            'dia', 'grelha', 'aba', 'rv', 'dif-l', 'conta',
            'dia-estado', 'fr', 'v-lista', 'vgrelha', 'vd', 'vleg',
            'lg', 'p-lista', 'foto-pre', 'mapa-mini', 'encontro',
            'encontro-txt', 'encontro-foto', 'hora', 'horas',
            # os formularios publicos
            'fcapa', 'fcorpo', 'fcx', 'fcampo', 'faviso', 'flado',
            'bgrande', 'sub-h',
            # o blog
            'jcapa', 'jart', 'jtopo', 'jcorpo', 'jdados', 'jfim',
            'joutros', 'joutro', 'migalhas', 'botao-s',
            # as paginas de texto
            'pcapa', 'ptexto', 'pregra', 'pnota',
            # as avaliacoes
            'av-capa', 'av-corpo', 'av-cx', 'av-campo', 'av-bt', 'estrelas',
            'estrela', 'av-sec', 'av-nota', 'av-item', 'av-lista',
            'av-tema', 'av-barra', 'av-resposta', 'av-estrelas',
            'rv-c', 'rv-l', 'rv-est', 'rv-resp', 'rv-form', 'rv-resumo']


def classes_usadas(html):
    usadas = set()
    for m in re.finditer(r'class="([^"]+)"', html):
        usadas.update(m.group(1).split())
    return usadas


def main():
    falhas = []
    for nome in PAGINAS:
        caminho = os.path.join(RAIZ, nome)
        if not os.path.exists(caminho):
            falhas.append('%s: nao existe' % nome)
            continue
        html = open(caminho).read()
        css = '\n'.join(re.findall(r'<style>(.*?)</style>', html, re.S))
        usadas = classes_usadas(html)
        for c in EXIGIDAS:
            if c in usadas and ('.%s{' % c) not in css.replace(' ', '') \
                    and ('.%s ' % c) not in css and ('.%s,' % c) not in css \
                    and ('.%s:' % c) not in css and ('.%s[' % c) not in css:
                falhas.append('%s: usa .%s e nao tem regra para ela' % (nome, c))
        # o preco nunca pode sair com uma casa decimal so
        for m in re.finditer(r'&euro;([0-9 ,]+\.[0-9])(?![0-9])', html):
            falhas.append('%s: preco com uma casa decimal: %s' % (nome, m.group(0)))
        # Um & cru dentro de um href e HTML invalido. Os browsers
        # perdoam-no hoje; o verificador nao, porque e exatamente o tipo
        # de coisa que funciona ate um dia deixar de funcionar.
        for m in re.finditer(r'href="([^"]*&(?!amp;|lt;|gt;|quot;|#)[^"]*)"', html):
            falhas.append('%s: & por escapar num href: %s'
                          % (nome, m.group(1)[:70]))

        # <div> a mais ou a menos. Um browser fecha-as sozinho e a pagina
        # parece bem ate uma seccao aparecer dentro de outra num ecra
        # estreito. Aconteceu-me ao trocar um campo por uma lista: ficou
        # um </div> orfao e nada deu erro.
        corpo = html[html.index('<body'):] if '<body' in html else ''
        corpo = re.sub(r'<script.*?</script>', '', corpo, flags=re.S)
        abertas = len(re.findall(r'<div\b', corpo))
        fechadas = len(re.findall(r'</div>', corpo))
        if abertas != fechadas:
            falhas.append('%s: %d <div> abertas e %d fechadas'
                          % (nome, abertas, fechadas))

        # um <style> dentro de outro: o browser engole a regra seguinte
        # sem dar erro nenhum. Custou-me uma seccao com o fundo errado
        # para descobrir, por isso passa a ser verificado.
        if html.count('<style>') != 1 or html.count('</style>') != 1:
            falhas.append('%s: tem %d <style> (devia ter 1)'
                          % (nome, html.count('<style>')))
        # noindex ligado ate os precos estarem confirmados
        if 'noindex' not in html:
            falhas.append('%s: sem noindex (os precos ainda nao foram '
                          'confirmados pelo Ricardo)' % nome)

    for nome in COM_BASE:
        caminho = os.path.join(RAIZ, nome)
        if not os.path.exists(caminho):
            continue
        html = open(caminho).read()
        if '/assets/lib/supabase.js' not in html:
            falhas.append('%s: fala com a base e nao carrega a biblioteca'
                          % nome)
        if '/assets/ligacao.js' not in html:
            falhas.append('%s: fala com a base e nao carrega a ligacao' % nome)
        if (html.find('/assets/lib/supabase.js')
                > html.find('/assets/ligacao.js')):
            falhas.append('%s: a ligacao vem antes da biblioteca' % nome)
        # A chave de servico ignora o RLS. Se um dia aparecer numa pagina,
        # qualquer pessoa pode ler e escrever tudo.
        if 'service_role' in html or 'sb_secret' in html:
            falhas.append('%s: TEM UMA CHAVE DE SERVICO NO HTML' % nome)

    for nome in PRIVADAS:
        caminho = os.path.join(RAIZ, nome)
        if os.path.exists(caminho) and 'noindex' not in open(caminho).read():
            falhas.append('%s: area privada sem noindex' % nome)

    # As ligacoes internas tem de ir para alguma parte. A homepage andou
    # com cinco 404 — /operators/, /magazine/, /airporttransfers/ e duas
    # mais — e ninguem deu por isso porque um 404 nao da erro ao gerar.
    vistas = set()
    for nome in PAGINAS:
        caminho = os.path.join(RAIZ, nome)
        if not os.path.exists(caminho):
            continue
        html = open(caminho).read()
        for m in re.finditer(r'href="(/[^"#?]*)', html):
            destino = m.group(1)
            # Dentro do <script> ha href montados em JavaScript
            # ('/tours/' + slug + '/'). Nao sao ligacoes a verificar: o
            # destino so existe quando a pagina corre.
            if "'" in destino or '+' in destino or '\n' in destino:
                continue
            if destino in vistas:
                continue
            vistas.add(destino)
            if not destino.endswith('/'):
                # um ficheiro, nao uma pagina
                if not os.path.exists(os.path.join(RAIZ, destino.lstrip('/'))):
                    falhas.append('%s: liga para %s e esse ficheiro nao existe'
                                  % (nome, destino))
                continue
            alvo = os.path.join(RAIZ, destino.strip('/'), 'index.html')
            if not os.path.exists(alvo):
                falhas.append('%s: liga para %s e essa pagina nao existe'
                              % (nome, destino))

    if falhas:
        print('FALHOU:')
        for f in falhas:
            print('  ' + f)
        sys.exit(1)
    print('ok: %d paginas verificadas' % len(PAGINAS))


if __name__ == '__main__':
    main()
