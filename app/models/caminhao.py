from app.database import db

class Caminhao(db.Model):
    __tablename__ = 'tb_caminhoes'

    id_caminhao = db.Column(db.Integer, primary_key=True)
    placa = db.Column(db.String(15), nullable=False)
    modelo = db.Column(db.Text, nullable=False)
    empresa = db.Column(db.Text)
