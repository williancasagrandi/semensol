from app.database import db
import numpy as np
from typing import Optional

class Motorista(db.Model):
    __tablename__ = 'tb_motoristas'

    id_motorista = db.Column(db.Integer, primary_key=True)
    cnh = db.Column(db.String(20), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)
    nome = db.Column(db.Text, nullable=False)
    biometria = db.Column(db.LargeBinary, nullable=True)  # bytes: 512 (f32) ou 1024 (f64)

    def set_biometria(self, encoding: np.ndarray, dtype: str = "float32") -> None:
        """
        Salva o vetor 128-D como bytes. Por padrão, armazena em float32 (512 bytes).
        """
        arr = np.asarray(encoding)
        if arr.ndim != 1 or arr.shape[0] != 128:
            raise ValueError("Encoding facial deve ter shape (128,)")
        if dtype not in ("float32", "float64"):
            raise ValueError("dtype deve ser 'float32' ou 'float64'")
        arr = arr.astype(np.float32 if dtype == "float32" else np.float64, copy=False)
        self.biometria = arr.tobytes()

    def get_biometria(self) -> Optional[np.ndarray]:
        """
        Lê os bytes e retorna np.ndarray shape (128,), preservando o dtype salvo.
        Aceita buffers de 512 (float32) ou 1024 (float64) bytes.
        """
        if not self.biometria:
            return None
        buf = memoryview(self.biometria)
        if len(buf) == 128 * 4:
            arr = np.frombuffer(buf, dtype=np.float32)
        elif len(buf) == 128 * 8:
            arr = np.frombuffer(buf, dtype=np.float64)
        else:
            # dado inválido/corrompido
            return None
        return arr  # shape (128,)
