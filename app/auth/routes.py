from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user
from ..models import User
from ..db import get_db_connection


auth_bp = Blueprint('auth', __name__, url_prefix='/')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM usuarios WHERE username = %s', (username,) )
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password'], password):
            user_obj = User(id=user['id'], username=user['username'], password=user['password'], tipo_acesso=user['tipo_acesso'])
            login_user(user_obj)
            id = user['id']

            #session['user_id'] = user['id']
           # session['username'] = user['username']
            return redirect(url_for('service.home'))
        else:
            flash('Usuário ou senha incorretos')
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Gera hash da senha
        password_hash = generate_password_hash(password)
        tipo_acesso = 'free'

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO usuarios (username, password, tipo_acesso) VALUES (%s, %s, %s)', (username, password_hash, tipo_acesso))
            conn.commit()
            flash('Usuário cadastrado com sucesso! Faça login.')
            return redirect(url_for('auth.login'))
        except:
            flash("Erro ao cadastrar usuário")
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/liberar')
def liberar_acesso():
    email = request.args.get('email')
    token = request.args.get('token')

    if token == 'testando123':
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET tipo_acesso = 'pro' WHERE username = %s", (email,))
        conn.commit()
        flash('Acesso Pro liberado para testes.', 'sucess')
        return redirect(url_for('auth.login'))
    flash('Token inválido.', 'danger')
    return redirect(url_for('main.index'))

@auth_bp.route('/teste', methods=['GET', 'POST'])
def teste():
    if request.method == 'POST':
        email = request.form['email']
        flash('Obrigado! Você receberá o acesso por e-mail.', 'success')
    return render_template('teste.html')

