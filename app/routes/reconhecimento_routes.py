from flask import Blueprint, request, jsonify

from app.models import Caminhao
from app.services.reconhecimento_service import processar_reconhecimento_completo
from app.utils.face_utils import reconhecer_motorista_cadastrado
import tempfile
import cv2
import os

from app.utils.plate_utils import reconhecer_placa

reconhecimento_bp = Blueprint('reconhecimento', __name__)

@reconhecimento_bp.route('/completo', methods=['POST'])
def reconhecer_completo():
    if 'imagem_rosto' not in request.files or 'imagem_placa' not in request.files:
        return jsonify({'error': 'Arquivos de imagem ausentes'}), 400

    rosto_file = request.files['imagem_rosto']
    placa_file = request.files['imagem_placa']

    temp_rosto = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    temp_placa = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
    rosto_file.save(temp_rosto.name)
    placa_file.save(temp_placa.name)

    resultado = processar_reconhecimento_completo(temp_rosto.name, temp_placa.name)

    os.remove(temp_rosto.name)
    os.remove(temp_placa.name)

    return jsonify(resultado), 200

@reconhecimento_bp.route('/motorista', methods=['POST'])
def route_reconhecer_motorista():
    if 'imagem_rosto' not in request.files:
        return jsonify({'erro': 'Imagem do rosto é obrigatória'}), 400

    imagem_file = request.files['imagem_rosto']
    if imagem_file.filename == '':
        return jsonify({'erro': 'Arquivo de imagem vazio'}), 400

    try:
        # Salva imagem temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            imagem_file.save(temp_file.name)
            temp_path = temp_file.name

        # Reconhece motorista
        motorista, confianca = reconhecer_motorista_cadastrado(temp_path)

        os.remove(temp_path)  # Remove imagem temporária

        if not motorista:
            return jsonify({'mensagem': 'Motorista não reconhecido'}), 404

        return jsonify({
            'id_motorista': motorista.id_motorista,
            'nome': motorista.nome,
            'confianca': round(confianca, 4)
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500


@reconhecimento_bp.route('/caminhao', methods=['POST'])
def route_reconhecer_caminhao():
    if 'imagem_placa' not in request.files:
        return jsonify({'erro': 'Imagem da placa é obrigatória'}), 400

    imagem_file = request.files['imagem_placa']
    if imagem_file.filename == '':
        return jsonify({'erro': 'Arquivo de imagem vazio'}), 400

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            imagem_file.save(temp_file.name)
            temp_path = temp_file.name

        placa = reconhecer_placa(temp_path)

        os.remove(temp_path)

        if not placa:
            return jsonify({'mensagem': 'Placa não reconhecida'}), 404

        caminhao = Caminhao.query.filter_by(placa=placa).first()

        if not caminhao:
            return jsonify({'mensagem': f'Caminhão com placa {placa} não encontrado'}), 404

        return jsonify({
            'id_caminhao': caminhao.id_caminhao,
            'placa': caminhao.placa,
            'modelo': caminhao.modelo,
            'empresa': caminhao.empresa
        }), 200

    except Exception as e:
        return jsonify({'erro': str(e)}), 500