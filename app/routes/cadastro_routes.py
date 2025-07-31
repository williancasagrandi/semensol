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


@cadastro_bp.route('/caminhao/manual', methods=['POST'])
def criar_caminhao_manual():
    data = request.get_json()
    placa = data.get('placa')
    modelo = data.get('modelo')
    empresa = data.get('empresa')

    if not placa or not modelo or not empresa:
        return jsonify({'error': 'placa, modelo e empresa são obrigatórios'}), 400

    try:
        id_caminhao = cadastrar_caminhao(placa.upper(), modelo, empresa)
        return jsonify({'id_caminhao': id_caminhao}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@cadastro_bp.route('/caminhao/imagem', methods=['POST'])
def criar_caminhao_por_imagem():
    if 'imagem' not in request.files:
        return jsonify({'error': 'Imagem da placa é obrigatória'}), 400

    modelo = request.form.get('modelo')
    empresa = request.form.get('empresa')

    if not modelo or not empresa:
        return jsonify({'error': 'modelo e empresa são obrigatórios'}), 400

    imagem_file = request.files['imagem']
    if imagem_file.filename == '':
        return jsonify({'error': 'Arquivo de imagem vazio'}), 400

    import tempfile, os
    from app.utils.plate_utils import reconhecer_placa

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            imagem_file.save(temp_file.name)
            temp_path = temp_file.name

        placa = reconhecer_placa(temp_path)
        os.remove(temp_path)

        if not placa:
            return jsonify({'error': 'Não foi possível reconhecer a placa na imagem'}), 400

        id_caminhao = cadastrar_caminhao(placa.upper(), modelo, empresa)
        return jsonify({
            'id_caminhao': id_caminhao,
            'placa': placa.upper()
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500

