import cv2
import easyocr
import re
import tempfile
import os

# Regex compatível com placas do Brasil (antigas e Mercosul)
PADRAO_PLACA_BR = re.compile(r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$')

def preprocessar_imagem(imagem_path):
    imagem = cv2.imread(imagem_path)
    imagem = cv2.resize(imagem, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    imagem = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    imagem = cv2.bilateralFilter(imagem, 9, 75, 75)
    imagem = cv2.equalizeHist(imagem)

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    cv2.imwrite(temp_file.name, imagem)
    return temp_file.name

def reconhecer_placa(imagem_path, debug=True):
    try:
        imagem_processada = preprocessar_imagem(imagem_path)

        reader = easyocr.Reader(['pt'], gpu=False)
        resultados = reader.readtext(imagem_processada, allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')

        os.remove(imagem_processada)

        placa_detectada = None
        maior_area = 0

        for bbox, texto, confianca in resultados:
            texto_limpo = re.sub(r'[^A-Z0-9]', '', texto.upper())
            x0, y0 = bbox[0]
            x1, y1 = bbox[2]
            area = abs((x1 - x0) * (y1 - y0))

            if debug:
                print(f"[conf={confianca:.2f}] {texto} → {texto_limpo} | área: {area} | bbox: {bbox}")

            if PADRAO_PLACA_BR.fullmatch(texto_limpo) and area > maior_area:
                placa_detectada = texto_limpo
                maior_area = area
                if debug:
                    print(f"Placa válida por regex: {placa_detectada}")

            elif placa_detectada is None and 6 <= len(texto_limpo) <= 8 and texto_limpo.isalnum():
                placa_detectada = texto_limpo
                if debug:
                    print(f"Placa aceita por fallback flexível: {placa_detectada}")

        return placa_detectada

    except Exception as e:
        if debug:
            print("Erro ao reconhecer placa:", e)
        return None

