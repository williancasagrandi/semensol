from app.database import db

class CicloPesagem(db.Model):
    __tablename__ = 'ciclos_pesagem'

    id_pesagem = db.Column(db.Integer, primary_key=True)
    caminhao_id = db.Column(db.Integer, db.ForeignKey('tb_caminhoes.id_caminhao'), nullable=False)
    motorista_id = db.Column(db.Integer, db.ForeignKey('tb_motoristas.id_motorista'), nullable=False)
    data_entrada = db.Column(db.Time, nullable=True)
    peso_entrada = db.Column(db.Float, nullable=True)
    data_saida = db.Column(db.Time, nullable=True)
    peso_saida = db.Column(db.Float, nullable=True)
    peso_liquido = db.Column(db.Float, nullable=True)
