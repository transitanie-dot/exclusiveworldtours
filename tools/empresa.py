# -*- coding: utf-8 -*-
"""Quem e a empresa, para efeitos legais.

Isto existe por uma razao concreta: a partir do momento em que o site
aceita um cartao, as paginas de termos e de privacidade deixam de ser
boa pratica e passam a ser obrigacao — e as duas tem de dizer QUEM
cobra, com que numero de registo e a que morada se escreve. Nao e um
detalhe de rodape: e o que torna o contrato exequivel e o que a lei de
protecao de dados chama o responsavel pelo tratamento.

Esses dados estao aqui e so aqui, por duas razoes:

  1. espalhados por duas paginas, divergem. A morada numa e a morada na
     outra acabam diferentes, e a diferenca descobre-se numa reclamacao.

  2. **o que nao esta confirmado nao vai para o site.** Os campos que
     ainda nao tenho estao a `None`, e o gerador RECUSA-SE a escrever as
     paginas legais enquanto faltar algum. Um numero de registo inventado
     numa pagina de termos nao e um marcador de lugar: e uma declaracao
     falsa sobre a identidade de quem cobra, feita a quem esta a entregar
     um cartao.

Para publicar as paginas legais basta preencher os campos em falta e
gerar o site outra vez. Nao ha mais nada a fazer.
"""

# --------------------------------------------------------------- o que sei
NOME_COMERCIAL = 'Exclusive World Tours'
SITE = 'exclusiveworldtours.com'
EMAIL = 'info@exclusiveworldtours.com'

# Onde o dinheiro passa. Nao e um dado da empresa, e um facto que a
# pagina de privacidade tem de declarar: o cartao e tratado pelo Stripe
# e nunca chega aos nossos servidores.
PROCESSADOR = 'Stripe Payments Europe, Ltd.'

# --------------------------------------------------- o que falta confirmar
#
# NAO PREENCHER DE MEMORIA NEM POR DEDUCAO. Cada um destes campos e uma
# afirmacao legal sobre a identidade de quem recebe o dinheiro.
NOME_LEGAL = None        # a entidade que factura, como esta no registo
NUMERO_REGISTO = None    # o numero de registo comercial da entidade
NUMERO_IVA = None        # o numero de IVA, se a entidade o tiver
MORADA = None            # a morada da sede, como esta no registo
PAIS = None              # o pais onde a entidade esta registada


# Os campos sem os quais uma pagina legal nao se escreve. O IVA fica de
# fora de proposito: ha entidades sem numero de IVA, e exigi-lo travava
# a publicacao por uma razao que pode nao existir.
OBRIGATORIOS = [
    ('NOME_LEGAL', NOME_LEGAL, 'a entidade legal que factura'),
    ('NUMERO_REGISTO', NUMERO_REGISTO, 'o numero de registo comercial'),
    ('MORADA', MORADA, 'a morada da sede'),
    ('PAIS', PAIS, 'o pais de registo'),
]


def em_falta():
    """Os campos por preencher, com a descricao de cada um."""
    return [(n, d) for n, v, d in OBRIGATORIOS
            if v is None or not str(v).strip()]


def completa():
    return not em_falta()


def porque_nao():
    """A frase que o gerador escreve quando nao pode publicar."""
    f = em_falta()
    if not f:
        return ''
    return ('faltam %d dados da empresa: %s\n'
            '     Preenche-os em tools/empresa.py e gera outra vez. Nao os\n'
            '     invento: um numero de registo errado numa pagina de termos\n'
            '     e uma declaracao falsa sobre quem recebe o dinheiro.'
            % (len(f), ', '.join('%s (%s)' % (n, d) for n, d in f)))


def identidade_html(e):
    """O bloco de identidade, para o fim das duas paginas legais.

    `e` e a funcao de escape da pagina — passa-se em vez de se importar
    para este modulo nao depender do gerador."""
    linhas = [
        ('Trading name', NOME_COMERCIAL),
        ('Registered name', NOME_LEGAL),
        ('Company registration', NUMERO_REGISTO),
        ('VAT number', NUMERO_IVA),
        ('Registered address', MORADA),
        ('Country of registration', PAIS),
        ('Email', EMAIL),
    ]
    return '\n'.join(
        '<div class="id-l"><dt>%s</dt><dd>%s</dd></div>' % (e(r), e(v))
        for r, v in linhas if v)


if __name__ == '__main__':
    if completa():
        print('ok: os dados da empresa estao completos')
    else:
        print('FALTA ' + porque_nao())
