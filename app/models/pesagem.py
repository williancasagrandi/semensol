from app.database import db

class Pesagem(db.Model):
    __tablename__ = 'tb_pesagens'

    id_pesagem = db.Column(db.Integer, primary_key=True)
    ciclo_id = db.Column(db.Integer, db.ForeignKey('ciclos_pesagem.id_pesagem'), nullable=False)
    peso_kg = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.Enum('entrada', 'saida', name='tipo_pesagem'), nullable=False)
    data_hora = db.Column(db.Time, nullable=False)
    origem_leitura = db.Column(db.Text, nullable=False, default='tc420')
