from app.database import db

class RegistroReconhecimento(db.Model):
    __tablename__ = 'tb_registros_reconhecimento'

    id = db.Column(db.Integer, primary_key=True)
    motorista_id = db.Column(db.Integer, db.ForeignKey('tb_motoristas.id_motorista'), nullable=True)
    caminhao_id = db.Column(db.Integer, db.ForeignKey('tb_caminhoes.id_caminhao'), nullable=True)
    ciclo_id = db.Column(db.Integer, db.ForeignKey('ciclos_pesagem.id_pesagem'), nullable=True)
    confianca_facial = db.Column(db.Float, nullable=True)
    imagem_rosto = db.Column(db.Text, nullable=True)
    imagem_placa = db.Column(db.Text, nullable=True)
    data_hora = db.Column(db.DateTime, server_default=db.func.current_timestamp())
    tipo_operacao = db.Column(db.Enum('entrada', 'saida', name='tipo_pesagem'), nullable=False)
