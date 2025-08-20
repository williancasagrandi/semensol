import os
from sqlalchemy import func
from typing import Dict, Any

from app.models import Caminhao
from app.utils.face_utils import reconhecer_motorista_cadastrado
from app.utils.plate_utils import reconhecer_placa

DEFAULT_TOL = float(os.getenv("FACE_TOLERANCIA", "0.6"))

def processar_reconhecimento_completo(path_rosto: str, path_placa: str) -> Dict[str, Any]:
    resp: Dict[str, Any] = {"motorista": None, "placa": None, "caminhao": None}

    # Face
    motorista, conf_face = reconhecer_motorista_cadastrado(path_rosto, tolerancia=DEFAULT_TOL)
    if motorista:
        resp["motorista"] = {
            "id_motorista": motorista.id_motorista,
            "nome": getattr(motorista, "nome", None),
            "confianca": round(float(conf_face), 4)
        }

    # Placa
    placa_txt = reconhecer_placa(path_placa)
    if placa_txt:
        placa_norm = placa_txt.upper()
        resp["placa"] = {"texto": placa_norm}

        caminhao = Caminhao.query.filter(func.upper(Caminhao.placa) == placa_norm).first()
        if caminhao:
            resp["caminhao"] = {
                "id_caminhao": caminhao.id_caminhao,
                "placa": caminhao.placa,
                "modelo": getattr(caminhao, "modelo", None),
                "empresa": getattr(caminhao, "empresa", None)
            }

    resp["sucesso"] = bool(resp["motorista"] and resp["caminhao"])
    return resp
