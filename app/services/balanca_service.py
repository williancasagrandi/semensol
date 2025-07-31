from app.models import CicloPesagem, Pesagem, Caminhao, Motorista
from app.database import db
from datetime import datetime


def registrar_entrada(placa, motorista_id, peso):
    caminhao = Caminhao.query.filter_by(placa=placa).first()
    if not caminhao:
        raise ValueError("Caminhão não cadastrado")

    ciclo = CicloPesagem(
        caminhao_id=caminhao.id_caminhao,
        motorista_id=motorista_id,
        data_entrada=datetime.now().time(),
        peso_entrada=peso
    )
    db.session.add(ciclo)
    db.session.commit()
    return ciclo.id_pesagem


def registrar_saida(evento_id, peso):
    ciclo = CicloPesagem.query.get(evento_id)
    if not ciclo:
        raise ValueError("Ciclo de pesagem não encontrado")

    ciclo.data_saida = datetime.now().time()
    ciclo.peso_saida = peso
    ciclo.peso_liquido = peso - ciclo.peso_entrada if ciclo.peso_entrada else None
    db.session.commit()


def get_motoristas():
    return Motorista.query.with_entities(Motorista.id_motorista, Motorista.nome).all()


def get_ciclos_abertos():
    return (
        db.session.query(
            CicloPesagem.id_pesagem,
            Caminhao.placa,
            Motorista.nome
        )
        .join(Caminhao, Caminhao.id_caminhao == CicloPesagem.caminhao_id)
        .join(Motorista, Motorista.id_motorista == CicloPesagem.motorista_id)
        .filter(CicloPesagem.data_saida.is_(None))
        .all()
    )


def get_historico():
    ciclos = CicloPesagem.query.order_by(CicloPesagem.id_pesagem.desc()).all()
    return [c.to_dict() for c in ciclos]
