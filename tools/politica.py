# -*- coding: utf-8 -*-
"""A politica de cancelamento, num sitio so.

Decidida pelo Ricardo a 2 de outubro de 2026: gratis ate 24 horas antes
da partida.

Esta num modulo proprio e nao espalhada pelas paginas porque uma
politica escrita em quatro sitios e uma politica que vai divergir, e o
dia em que divergir e o dia em que a pagina do tour promete uma coisa e a
pagina de contacto outra. Alterar a regra e alterar HORAS aqui e gerar o
site outra vez.

Enquanto nao houver pagamento no site, isto descreve o que acontece a um
pedido confirmado — nao um reembolso automatico que nao existe. Nao se
promete um mecanismo que ainda nao foi construido.
"""

HORAS = 24

# Uma linha, para cartoes e barras.
CURTA = 'Free cancellation up to %d hours before departure' % HORAS

# Uma frase, para o corpo de uma pagina.
FRASE = ('Free cancellation up to %d hours before departure. After that '
         'the day is yours and we cannot refund it.' % HORAS)

# O paragrafo completo, para a pagina do tour e a de contacto. Diz
# tambem o que NAO e um cancelamento, que e a pergunta que vem a seguir.
PARAGRAFOS = [
    ('Cancel up to %d hours before your departure time and you pay '
     'nothing. Inside %d hours the vehicle and the driver are already '
     'committed to your day, so we cannot refund it.' % (HORAS, HORAS)),
    ('Weather is not a cancellation. These are private days: if a stop '
     'is genuinely unsafe or a road is closed, your driver changes the '
     'route and tells you why, and you still get a full day out. That '
     'is the thing a coach tour cannot do.'),
    ('If we have to cancel &mdash; conditions that make the roads '
     'unsafe, a vehicle that fails its check &mdash; you are refunded in '
     'full, whenever it happens.'),
]

# A pergunta-tipo, para entrar nas FAQ de qualquer tour que nao tenha
# uma sua. Assim nenhuma pagina de tour fica sem a regra.
PERGUNTA = ('Can we cancel?',
            'Free up to %d hours before departure, at no cost. After '
            'that we cannot refund the day. If we cancel because '
            'conditions are unsafe, you are refunded in full.' % HORAS)
