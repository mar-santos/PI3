# app.py
import os
from flask import Flask
from config import Config
from app.models import db, init_app
from app.auth import auth_bp
from app.routes import routes_bp
from app.routes.routes_pets import routes_pets_bp
from flask_migrate import Migrate
from flask_login import LoginManager, current_user

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Garante que a pasta instance existe
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    init_app(app)
    Migrate(app, db)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models.models import Usuario
        try:
            return db.session.get(Usuario, int(user_id))
        except Exception:
            return Usuario.query.get(int(user_id))

    # Adiciona current_user a todos os templates
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)

    app.register_blueprint(auth_bp)
    app.register_blueprint(routes_bp)
    app.register_blueprint(routes_pets_bp, url_prefix='/pets')

    # Crie as tabelas do banco de dados
    with app.app_context():
        db.create_all()
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)





    