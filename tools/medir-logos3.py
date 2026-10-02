#!/usr/bin/env python3
"""
Mede a largura natural de cada marca grande do logos3 e diz qual devia
ser o --k de cada proposta.

O --k e o tamanho cheio a dividir pela largura natural: e o fator que,
multiplicado pela largura disponivel, da o tamanho a que a marca encosta
nas margens sem passar. Medir e preciso porque a largura depende da
fonte, do peso e do espacejamento — a olho nunca da certo, e uma marca
cortada no telemovel e um erro que so se ve depois de enviada.

    node tools/medir-logos3.mjs    # (precisa do servidor em 127.0.0.1:8778)
"""
