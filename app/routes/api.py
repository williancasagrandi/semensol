# routes/api.py
import os
import tempfile

from flask import Blueprint, request, jsonify

from app.routes.reconhecimento_routes import reconhecer_completo
from app.services.reconhecimento_service import processar_reconhecimento_completo
from app.services.cadastro_service import cadastrar_motorista, cadastrar_caminhao
from app.services.balanca_service import registrar_entrada, registrar_saida, get_historico, get_ciclos_abertos, get_caminhao
from app.utils.face_utils import reconhecer_motorista_cadastrado

api_bp = Blueprint('api', __name__)

# listar_motoristas, listar_caminhoes

# ---------------------- CADASTRO ----------------------

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



@api_bp.route('/caminhoes', methods=['GET'])
def listar_caminhoes():
    rows = get_caminhao()
    return jsonify([{'id': r[0], 'placa': r[1]} for r in rows]), 200

# ---------------------- RECONHECIMENTO ----------------------

@api_bp.route('/reconhecer-completo', methods=['POST'])
def route_reconhecer_completo():
    if 'imagem_rosto' not in request.files or 'imagem_placa' not in request.files:
        return jsonify({'erro': 'Imagens de rosto e placa são obrigatórias'}), 400

    imagem_rosto = request.files['imagem_rosto']
    imagem_placa = request.files['imagem_placa']

    try:
        resultado = reconhecer_completo(imagem_rosto, imagem_placa)
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


# ---------------------- BALANÇA ----------------------

@api_bp.route('/entrada', methods=['POST'])
def route_registrar_entrada():
    data = request.get_json(force=True)
    for campo in ('placa', 'motorista_id', 'peso'):
        if data.get(campo) is None:
            return jsonify({'erro': f'{campo} é obrigatório'}), 400
    try:
        eid = registrar_entrada(data['placa'], data['motorista_id'], data['peso'])
        return jsonify({'id_evento': eid}), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@api_bp.route('/saida', methods=['POST'])
def route_registrar_saida():
    data = request.get_json(force=True)
    for campo in ('evento_id', 'peso'):
        if data.get(campo) is None:
            return jsonify({'erro': f'{campo} é obrigatório'}), 400
    try:
        registrar_saida(data['evento_id'], data['peso'])
        return '', 204
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@api_bp.route('/historico', methods=['GET'])
def route_historico():
    try:
        hist = get_historico()
        return jsonify(hist), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@api_bp.route('/ciclos-abertos', methods=['GET'])
def route_ciclos_abertos():
    try:
        ciclos = get_ciclos_abertos()
        return jsonify(ciclos), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
