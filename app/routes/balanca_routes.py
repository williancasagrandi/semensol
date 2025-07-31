from flask import Blueprint, request, jsonify
from app.services.balanca_service import (
    registrar_entrada,
    registrar_saida,
    get_motoristas,
    get_ciclos_abertos,
    get_historico
)

balanca_bp = Blueprint('balanca', __name__)

@balanca_bp.route('/motoristas', methods=['GET'])
def listar_motoristas():
    rows = get_motoristas()
    return jsonify([{'id': r[0], 'nome': r[1]} for r in rows]), 200

@balanca_bp.route('/entrada', methods=['POST'])
def entrada():
    data = request.get_json(force=True)
    for campo in ('placa', 'motorista_id', 'peso'):
        if not data.get(campo):
            return jsonify({'error': f'{campo} é obrigatório'}), 400

    try:
        evento_id = registrar_entrada(data['placa'], data['motorista_id'], data['peso'])
        return jsonify({'id_evento': evento_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@balanca_bp.route('/saida', methods=['POST'])
def saida():
    data = request.get_json(force=True)
    for campo in ('evento_id', 'peso'):
        if not data.get(campo):
            return jsonify({'error': f'{campo} é obrigatório'}), 400

    try:
        registrar_saida(data['evento_id'], data['peso'])
        return '', 204
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@balanca_bp.route('/ciclos-abertos', methods=['GET'])
def ciclos_abertos():
    try:
        ciclos = get_ciclos_abertos()
        return jsonify([{'id_pesagem': r[0], 'placa': r[1], 'motorista': r[2]} for r in ciclos]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@balanca_bp.route('/historico', methods=['GET'])
def historico():
    try:
        return jsonify(get_historico()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
