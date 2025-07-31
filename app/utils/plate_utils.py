import easyocr
import re

PADRAO_PLACA_BR = re.compile(r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$')


def reconhecer_placa(imagem_path):
    reader = easyocr.Reader(['pt'])
    resultados = reader.readtext(imagem_path)

    for _, texto, _ in resultados:
        texto = texto.upper().replace(" ", "").replace("-", "")
        if PADRAO_PLACA_BR.fullmatch(texto):
            return texto
    return None
