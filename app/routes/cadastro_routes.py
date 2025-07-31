from flask import Blueprint, request, jsonify
from app.services.cadastro_service import cadastrar_motorista, cadastrar_caminhao

cadastro_bp = Blueprint('cadastro', __name__)

@cadastro_bp.route('/motorista', methods=['POST'])
def route_cadastrar_motorista():
    if 'imagem' not in request.files:
        return jsonify({'erro': 'Imagem do motorista é obrigatória'}), 400

    imagem = request.files['imagem']

    nome = request.form.get('nome')
    cpf = request.form.get('cpf')
    cnh = request.form.get('cnh')

    for campo, valor in [('nome', nome), ('cpf', cpf), ('cnh', cnh)]:
        if not valor:
            return jsonify({'erro': f'{campo} é obrigatório'}), 400

    try:
        dados = {'nome': nome, 'cpf': cpf, 'cnh': cnh}
        motorista = cadastrar_motorista(dados, imagem)
        return jsonify(motorista), 201
    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@cadastro_bp.route('/caminhao', methods=['POST'])
def criar_caminhao():
    data = request.get_json(force=True)
    for campo in ('placa', 'modelo', 'empresa'):
        if not data.get(campo):
            return jsonify({'error': f'{campo} é obrigatório'}), 400

    try:
        id_caminhao = cadastrar_caminhao(data['placa'], data['modelo'], data['empresa'])
        return jsonify({'id_caminhao': id_caminhao}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
