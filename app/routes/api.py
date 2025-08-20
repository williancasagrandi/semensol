from flask import Blueprint, request, jsonify
from app.services.cadastro_service import cadastrar_motorista, cadastrar_caminhao
from app.services.balanca_service import get_caminhao, get_motoristas

api_bp = Blueprint('api', __name__)

@api_bp.route('/motorista/cadastrar', methods=['POST'])
def route_cadastrar_motorista():
    data = request.get_json()
    for campo in ('nome', 'cpf', 'cnh'):
        if not data.get(campo):
            return jsonify({'erro': f'{campo} é obrigatório'}), 400
    try:
        motorista = cadastrar_motorista(data)
        return jsonify(motorista), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@api_bp.route('/caminhao/cadastrar', methods=['POST'])
def route_cadastrar_caminhao():
    data = request.get_json()
    for campo in ('placa', 'modelo', 'empresa'):
        if not data.get(campo):
            return jsonify({'erro': f'{campo} é obrigatório'}), 400
    try:
        caminhao = cadastrar_caminhao(data)
        return jsonify(caminhao), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@api_bp.route('/motoristas', methods=['GET'])
def listar_motoristas():
    rows = get_motoristas()
    return jsonify([{'id': r[0], 'nome': r[1]} for r in rows]), 200

@api_bp.route('/caminhoes', methods=['GET'])
def listar_caminhoes():
    rows = get_caminhao()
    return jsonify([{'id': r[0], 'placa': r[1]} for r in rows]), 200




