from app.database import db
import numpy as np

class Motorista(db.Model):
    __tablename__ = 'tb_motoristas'

    id_motorista = db.Column(db.Integer, primary_key=True)
    cnh = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    nome = db.Column(db.Text, nullable=False)
    biometria = db.Column(db.LargeBinary, nullable=True)

    def set_biometria(self, encoding):
        self.biometria = np.asarray(encoding, dtype=np.float32).tobytes()

    def get_biometria(self):
        if self.biometria:
            return np.frombuffer(self.biometria, dtype=np.float32)
        return None
