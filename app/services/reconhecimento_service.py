from app.models import RegistroReconhecimento, Motorista, Caminhao, CicloPesagem
from app.utils.face_utils import reconhecer_motorista_cadastrado
from app.utils.plate_utils import reconhecer_placa
from app.database import db
from datetime import datetime


def processar_reconhecimento_completo(imagem_rosto_path, imagem_placa_path):
    motorista, confianca_facial = reconhecer_motorista_cadastrado(imagem_rosto_path)
    placa = reconhecer_placa(imagem_placa_path)

    caminhao = Caminhao.query.filter_by(placa=placa).first() if placa else None

    ciclo = None
    if caminhao and motorista:
        ciclo = (
            CicloPesagem.query
            .filter_by(caminhao_id=caminhao.id_caminhao, motorista_id=motorista.id_motorista)
            .order_by(CicloPesagem.id_pesagem.desc())
            .first()
        )

    tipo_operacao = 'entrada' if not ciclo or not ciclo.peso_saida else 'saida'

    registro = RegistroReconhecimento(
        motorista_id=motorista.id_motorista if motorista else None,
        caminhao_id=caminhao.id_caminhao if caminhao else None,
        ciclo_id=ciclo.id_pesagem if ciclo else None,
        confianca_facial=confianca_facial,
        imagem_rosto=imagem_rosto_path,
        imagem_placa=imagem_placa_path,
        tipo_operacao=tipo_operacao,
        data_hora=datetime.now()
    )

    db.session.add(registro)
    db.session.commit()

    return {
        'motorista': motorista.to_dict() if motorista else None,
        'placa': placa,
        'confianca_facial': confianca_facial,
        'tipo_operacao': tipo_operacao
    }
