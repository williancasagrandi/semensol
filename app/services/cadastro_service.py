import os
from app.models import Motorista, Caminhao
from app.database import db
from app.utils.face_utils import extrair_biometria_facial
from werkzeug.datastructures import FileStorage
from uuid import uuid4
from flask import current_app


def cadastrar_motorista(data: dict, imagem: FileStorage):
    nome = data['nome']
    cpf = data['cpf']
    cnh = data['cnh']

    # Validar imagem
    if not imagem or not imagem.filename:
        raise ValueError("Imagem inválida ou ausente")

    # Salvar imagem no diretório de uploads
    extensao = imagem.filename.rsplit('.', 1)[-1].lower()
    nome_arquivo = f"{uuid4().hex}.{extensao}"
    caminho_upload = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_arquivo)

    imagem.save(caminho_upload)

    # Extrair biometria facial
    biometria = extrair_biometria_facial(caminho_upload)
    if biometria is None:
        os.remove(caminho_upload)  # remover imagem se inválida
        raise ValueError("Não foi possível extrair a biometria da imagem")

    # Criar motorista
    motorista = Motorista(nome=nome, cpf=cpf, cnh=cnh)
    motorista.set_biometria(biometria)

    db.session.add(motorista)
    db.session.commit()

    return {
        'id_motorista': motorista.id_motorista,
        'nome': motorista.nome,
        'cpf': motorista.cpf,
        'cnh': motorista.cnh
    }


def cadastrar_caminhao(data: dict):
    placa = data['placa']
    modelo = data['modelo']
    empresa = data['empresa']

    caminhao = Caminhao(placa=placa, modelo=modelo, empresa=empresa)
    db.session.add(caminhao)
    db.session.commit()

    return {
        'id_caminhao': caminhao.id_caminhao,
        'placa': caminhao.placa,
        'modelo': caminhao.modelo,
        'empresa': caminhao.empresa
    }
