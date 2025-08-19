import face_recognition
import numpy as np
from app.models import motorista, Motorista


def extrair_biometria_facial(imagem_path):
    try:
        imagem = face_recognition.load_image_file(imagem_path)
        encodings = face_recognition.face_encodings(imagem)
        return encodings[0] if encodings else None
    except Exception as e:
        print(f"Erro ao extrair biometria: {e}")
        return None


def reconhecer_motorista_por_id(imagem_path, motorista_id, tolerancia=0.6):
    motorista = Motorista.query.get(motorista_id)
    if not motorista:
        return False, 0.0

    encoding_ref = motorista.get_biometria()
    encoding_img = extrair_biometria_facial(imagem_path)

    if encoding_ref is None or encoding_img is None:
        return False, 0.0

    distancia = face_recognition.face_distance([encoding_ref], encoding_img)[0]
    return distancia <= tolerancia, max(0, 1 - distancia)


def reconhecer_motorista_cadastrado(imagem_path, tolerancia=0.5):
    encoding_img = extrair_biometria_facial(imagem_path)
    if encoding_img is None:
        return None, 0.0

    motoristas = Motorista.query.all()
    melhor_match = None
    melhor_conf = 0.0

    for m in motoristas:
        ref = m.get_biometria()
        if ref is None:
            continue

        distancia = face_recognition.face_distance([ref], encoding_img)[0]
        confianca = max(0, 1 - distancia)
        if distancia <= tolerancia and confianca > melhor_conf:
            melhor_match = m
            melhor_conf = confianca

    return melhor_match, melhor_conf


def validar_qualidade_imagem(imagem_path):
    try:
        img = face_recognition.load_image_file(imagem_path)
        faces = face_recognition.face_locations(img)

        if len(faces) != 1:
            return False, "Imagem deve conter exatamente um rosto"

        top, right, bottom, left = faces[0]
        largura = right - left
        altura = bottom - top
        if largura < 50 or altura < 50:
            return False, "Rosto muito pequeno na imagem"

        return True, "Imagem válida"
    except Exception as e:
        return False, f"Erro ao validar imagem: {e}"