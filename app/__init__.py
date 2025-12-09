from flask import Flask
from flask_login import LoginManager
from .models import User
from .db import get_db_connection
import os

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.secret_key = 'Mina96#####'
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Importa e registra os blueprints
    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .identificar.routes import identificar_bp
    from .services.service import service

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(identificar_bp)
    app.register_blueprint(service)

    return app

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM usuarios WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user:
        return User(id=user['id'], username=user['username'], password=user['password'], tipo_acesso=user['tipo_acesso'])
    return None
