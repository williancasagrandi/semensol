from typing import Dict, Any
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
import re

from app.database import db # ajuste para onde você expõe o SQLAlchemy
from app.models import Motorista, Caminhao
from app.utils.face_utils import validar_qualidade_imagem, extrair_biometria_facial


_PADRAO_PLACA_BR = re.compile(r'^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$')

def _digits(txt: str) -> str:
    return re.sub(r'\D', '', txt or '')

def _valida_cpf(cpf: str) -> bool:
    cpf = _digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0]*11:
        return False
    # dígitos verificadores
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    d1 = (soma * 10) % 11
    d1 = 0 if d1 == 10 else d1
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    d2 = (soma * 10) % 11
    d2 = 0 if d2 == 10 else d2
    return cpf[-2:] == f"{d1}{d2}"

def _valida_cnh(cnh: str) -> bool:
    cnh = _digits(cnh)
    return len(cnh) == 11 and cnh != cnh[0]*11

def _normaliza_placa(placa: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', (placa or '').upper())

def _valida_placa(placa_norm: str) -> bool:
    return bool(_PADRAO_PLACA_BR.fullmatch(placa_norm))



def cadastrar_motorista(dados: Dict[str, Any], imagem_path: str) -> Dict[str, Any]:
    nome = (dados.get("nome") or "").strip()
    cpf  = _digits(dados.get("cpf"))
    cnh  = _digits(dados.get("cnh"))

    if not nome:
        raise ValueError("nome inválido")
    if not _valida_cpf(cpf):
        raise ValueError("cpf inválido")
    if not _valida_cnh(cnh):
        raise ValueError("cnh inválida")

    # qualidade da imagem
    ok, msg = validar_qualidade_imagem(imagem_path)
    if not ok:
        raise ValueError(f"imagem inválida: {msg}")

    encoding = extrair_biometria_facial(imagem_path)
    if encoding is None:
        raise ValueError("não foi possível extrair a biometria facial")

    # unicidade por CPF e CNH
    ja_existe = (
        db.session.query(Motorista)
        .filter((func.replace(func.replace(Motorista.cpf, '.', ''), '-', '') == cpf) | (Motorista.cnh == cnh))
        .first()
    )
    if ja_existe:
        raise ValueError("motorista já cadastrado (CPF/CNH)")

    m = Motorista(nome=nome, cpf=cpf, cnh=cnh)
    # Armazene usando o método do seu modelo (assumindo que existe):
    if hasattr(m, "set_biometria"):
        m.set_biometria(encoding)
    else:
        # fallback: salve como lista (JSON) ou bytes se houver coluna apropriada
        # ajuste conforme seu modelo
        m.biom_embed = encoding.tolist()  # exemplo

    db.session.add(m)
    try:
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        raise ValueError("violação de unicidade no banco (CPF/CNH/constraints)") from ie

    return {
        "id_motorista": m.id_motorista,
        "nome": m.nome,
        "cpf": m.cpf,
        "cnh": m.cnh,
    }

def cadastrar_caminhao(placa: str, modelo: str, empresa: str) -> int:
    placa_norm = _normaliza_placa(placa)
    if not _valida_placa(placa_norm):
        raise ValueError("placa inválida")

    # evitar duplicidade, case-insensitive
    existente = (
        db.session.query(Caminhao)
        .filter(func.upper(Caminhao.placa) == placa_norm)
        .first()
    )
    if existente:
        return existente.id_caminhao

    c = Caminhao(placa=placa_norm, modelo=(modelo or "").strip(), empresa=(empresa or "").strip())
    db.session.add(c)
    try:
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        raise ValueError("violação de unicidade no banco (placa)") from ie

    return c.id_caminhao
