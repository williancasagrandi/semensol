from flask import Blueprint
from .reconhecimento_routes import reconhecimento_bp
from .cadastro_routes import cadastro_bp
from .balanca_routes import balanca_bp

def register_blueprints(app):
    app.register_blueprint(reconhecimento_bp, url_prefix='/api/reconhecimento')
    app.register_blueprint(cadastro_bp, url_prefix='/api/cadastro')
    app.register_blueprint(balanca_bp, url_prefix='/api/balanca')
