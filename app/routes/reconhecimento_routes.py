from flask import Blueprint, request, jsonify
from werkzeug.datastructures import FileStorage
from sqlalchemy import func
import tempfile, os, re

from app.models import Caminhao
from app.utils.face_utils import reconhecer_motorista_cadastrado
from app.utils.plate_utils import reconhecer_placa

reconhecimento_bp = Blueprint('reconhecimento', __name__)

def _as_tempfile(fs: FileStorage, suffix: str = ".jpg") -> str:
    # Compatível com Windows: fecha o descritor antes de salvar
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    fs.save(path)
    return path

def _is_image(fs: FileStorage) -> bool:
    mt = (fs.mimetype or "") if fs else ""
    fn = (fs.filename or "") if fs else ""
    return bool(fs and fn and mt.startswith("image/"))

def _json_error(http_code: int, code: str, msg: str):
    return jsonify({"ok": False, "error": {"code": code, "message": msg}}), http_code

@reconhecimento_bp.route('/completo', methods=['POST'])
def reconhecer_completo():
    rosto_fs = request.files.get('imagem_rosto')
    placa_fs = request.files.get('imagem_placa')

    if not _is_image(rosto_fs) or not _is_image(placa_fs):
        return _json_error(400, "bad_request", "Arquivos de imagem ausentes ou inválidos")

    rosto_path = placa_path = None
    try:
        rosto_path = _as_tempfile(rosto_fs, ".jpg")
        placa_path = _as_tempfile(placa_fs, ".jpg")

        from app.services.reconhecimento_service import processar_reconhecimento_completo
        resultado = processar_reconhecimento_completo(rosto_path, placa_path)

        # resultado deve ser dict serializável
        return jsonify({"ok": True, **(resultado or {})}), 200
    except Exception as e:
        return _json_error(500, "internal_error", str(e))
    finally:
        if rosto_path and os.path.exists(rosto_path):
            os.remove(rosto_path)
        if placa_path and os.path.exists(placa_path):
            os.remove(placa_path)

@reconhecimento_bp.route('/motorista', methods=['POST'])
def route_reconhecer_motorista():
    rosto_fs = request.files.get('imagem_rosto')
    if not _is_image(rosto_fs):
        return _json_error(400, "bad_request", "Imagem do rosto é obrigatória")

    tmp_path = None
    try:
        tmp_path = _as_tempfile(rosto_fs, ".jpg")
        motorista, confianca = reconhecer_motorista_cadastrado(tmp_path)

        if not motorista:
            return _json_error(404, "not_found", "Motorista não reconhecido")

        return jsonify({
            "ok": True,
            "motorista": {
                "id_motorista": motorista.id_motorista,
                "nome": getattr(motorista, "nome", None),
                "confianca": round(float(confianca), 4),
            }
        }), 200
    except Exception as e:
        return _json_error(500, "internal_error", str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

@reconhecimento_bp.route('/caminhao', methods=['POST'])
def route_reconhecer_caminhao():
    placa_fs = request.files.get('imagem_placa')
    if not _is_image(placa_fs):
        return _json_error(400, "bad_request", "Imagem da placa é obrigatória")

    tmp_path = None
    try:
        tmp_path = _as_tempfile(placa_fs, ".jpg")
        placa = reconhecer_placa(tmp_path)

        if not placa:
            return _json_error(404, "not_found", "Placa não reconhecida")

        placa_norm = re.sub(r'[^A-Z0-9]', '', placa.upper())
        caminhao = Caminhao.query.filter(func.upper(Caminhao.placa) == placa_norm).first()

        if not caminhao:
            return _json_error(404, "not_found", f"Caminhão com placa {placa_norm} não encontrado")

        return jsonify({
            "ok": True,
            "caminhao": {
                "id_caminhao": caminhao.id_caminhao,
                "placa": caminhao.placa,
                "modelo": getattr(caminhao, "modelo", None),
                "empresa": getattr(caminhao, "empresa", None),
            }
        }), 200
    except Exception as e:
        return _json_error(500, "internal_error", str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
