from flask import Blueprint, request, jsonify
from werkzeug.datastructures import FileStorage
import os, tempfile, re

from app.services.cadastro_service import cadastrar_motorista, cadastrar_caminhao
from app.utils.plate_utils import reconhecer_placa

cadastro_bp = Blueprint('cadastro', __name__)

# ---------- helpers ----------
def _json_error(http_code: int, code: str, msg: str):
    return jsonify({"ok": False, "error": {"code": code, "message": msg}}), http_code

def _is_image(fs: FileStorage) -> bool:
    if not fs or not fs.filename:
        return False
    mt = fs.mimetype or ""
    return mt.startswith("image/")

def _as_tempfile(fs: FileStorage, suffix: str = ".jpg") -> str:
    # Compatível com Windows: fechar o descritor antes de salvar
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    fs.save(path)
    return path

def _norm_placa(txt: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', (txt or '').upper())

# ---------- rotas ----------
@cadastro_bp.route('/motorista', methods=['POST'])
def route_cadastrar_motorista():
    img_fs = request.files.get('imagem')
    if not _is_image(img_fs):
        return _json_error(400, "bad_request", "Imagem do motorista é obrigatória")

    nome = request.form.get('nome')
    cpf  = request.form.get('cpf')
    cnh  = request.form.get('cnh')

    for campo, valor in (('nome', nome), ('cpf', cpf), ('cnh', cnh)):
        if not valor:
            return _json_error(400, "bad_request", f"{campo} é obrigatório")

    tmp_path = None
    try:
        tmp_path = _as_tempfile(img_fs, ".jpg")
        # serviço deve validar CPF/CNH, qualidade e extrair embedding
        motorista = cadastrar_motorista(
            dados={"nome": nome, "cpf": cpf, "cnh": cnh},
            imagem_path=tmp_path
        )
        # motorista deve ser dict serializável retornado pelo serviço
        return jsonify({"ok": True, "motorista": motorista}), 201
    except ValueError as ve:
        # erros de validação/duplicidade mapeados para 400
        return _json_error(400, "validation_error", str(ve))
    except Exception as e:
        return _json_error(500, "internal_error", str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

@cadastro_bp.route('/caminhao/manual', methods=['POST'])
def criar_caminhao_manual():
    data = request.get_json(silent=True) or {}
    placa   = data.get('placa')
    modelo  = data.get('modelo')
    empresa = data.get('empresa')

    if not placa or not modelo or not empresa:
        return _json_error(400, "bad_request", "placa, modelo e empresa são obrigatórios")

    try:
        placa_norm = _norm_placa(placa)  # defensivo; o serviço também deve normalizar
        id_caminhao = cadastrar_caminhao(placa_norm, modelo, empresa)
        return jsonify({"ok": True, "id_caminhao": id_caminhao, "placa": placa_norm}), 201
    except ValueError as ve:
        return _json_error(400, "validation_error", str(ve))
    except Exception as e:
        return _json_error(500, "internal_error", str(e))

@cadastro_bp.route('/caminhao/imagem', methods=['POST'])
def criar_caminhao_por_imagem():
    img_fs = request.files.get('imagem')
    if not _is_image(img_fs):
        return _json_error(400, "bad_request", "Imagem da placa é obrigatória")

    modelo  = request.form.get('modelo')
    empresa = request.form.get('empresa')
    if not modelo or not empresa:
        return _json_error(400, "bad_request", "modelo e empresa são obrigatórios")

    tmp_path = None
    try:
        tmp_path = _as_tempfile(img_fs, ".jpg")
        placa_txt = reconhecer_placa(tmp_path, debug=False)
        if not placa_txt:
            return _json_error(400, "ocr_failed", "Não foi possível reconhecer a placa na imagem")

        placa_norm = _norm_placa(placa_txt)  # defensivo
        id_caminhao = cadastrar_caminhao(placa_norm, modelo, empresa)
        return jsonify({"ok": True, "id_caminhao": id_caminhao, "placa": placa_norm}), 201
    except ValueError as ve:
        return _json_error(400, "validation_error", str(ve))
    except Exception as e:
        return _json_error(500, "internal_error", str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
