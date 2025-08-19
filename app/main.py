# app/main.py

from flask import Flask
from flask_migrate import Migrate
from app.database import db
from app.config import get_config
from app.routes import register_blueprints
import os
import logging
from logging.handlers import RotatingFileHandler


def create_app(config_name=None):
    app = Flask(__name__)

    # Ativa CORS globalmente para todas as rotas e origens
    from flask_cors import CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Configuração da aplicação
    config_class = get_config()
    app.config.from_object(config_class)

    # Inicializa o banco de dados
    db.init_app(app)

    # Inicializa as migrações
    Migrate(app, db)

    # Registra todos os blueprints das rotas
    register_blueprints(app)

    # Configura logs e diretórios
    setup_logging(app)
    setup_app_directories(app)

    from sqlalchemy import text

    @app.route('/health')
    def health_check():
        try:
            db.session.execute(text('SELECT 1'))
            return {'status': 'healthy', 'database': 'connected'}, 200
        except Exception as e:
            app.logger.error(f"Health check failed: {e}")
            return {'status': 'unhealthy', 'error': str(e)}, 500


    @app.route('/')
    def index():
        return {
            'message': 'Sistema de Reconhecimento de Motoristas e Pesagem',
            'version': '2.0.0',
            'database': 'Supabase/PostgreSQL',
            'endpoints': {
                'reconhecimento_completo': '/api/reconhecimento/completo',
                'cadastrar_motorista': '/api/cadastro/motorista',
                'cadastrar_caminhao': '/api/cadastro/caminhao',
                'motoristas': '/api/balanca/motoristas',
                'entrada': '/api/balanca/entrada',
                'saida': '/api/balanca/saida',
                'historico': '/api/balanca/historico',
                'ciclos_abertos': '/api/balanca/ciclos-abertos',
                'health_check': '/health'
            }
        }

    return app


def setup_logging(app):
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler(
            'logs/sistema_motoristas.log',
            maxBytes=10_000_000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)

        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Sistema de motoristas iniciado')


def setup_app_directories(app):
    directories = [
        app.config.get('UPLOAD_FOLDER', 'uploads'),
        'logs',
        'backups'
    ]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            app.logger.info(f'Diretório criado: {directory}')
