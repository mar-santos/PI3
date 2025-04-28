# app/__init__.py
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    print("Iniciando create_app")  # Debug print
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app.auth import auth_bp
    from app.routes import routes_bp
    from app.routes.routes_pets import routes_pets_bp

    print("Registrando blueprint: auth_bp")  # Debug print
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    print("Registrando blueprint: routes_bp")  # Debug print
    app.register_blueprint(routes_bp, url_prefix='/')
    
    print("Registrando blueprint: routes_pets_bp")  # Debug print
    app.register_blueprint(routes_pets_bp, url_prefix='/pets')

    print("Blueprints registrados:", app.blueprints.keys())  # Debug print

    return app