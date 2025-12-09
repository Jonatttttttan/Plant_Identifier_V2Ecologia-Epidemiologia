from flask import Flask, render_template, redirect, request, url_for
import os
import mysql.connector
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session, flash # Componentes de login
import base64
import requests
from dotenv import load_dotenv # Proteger API_KEY
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin # pip install flask-login


load_dotenv()

login_manager = LoginManager()


PLANT_ID_API_KEY = os.getenv('PLANT_ID_API_KEY')
app = Flask(__name__)
login_manager.init_app(app)
login_manager.login_view = 'login'
UPLOAD_fOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
app.config["UPLOAD_FOLDER"] = UPLOAD_fOLDER
app.secret_key = 'Mina96#####'

# Função para conectar com o banco mysql
def get_db_connection():
    conn = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        password = 'password',
        database = 'plantas'
    )
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Cria tabela se não existir
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        '''CREATE TABLE IF NOT EXISTS angiospermas(
        id INT AUTO_INCREMENT PRIMARY KEY,
        especie VARCHAR(255) NOT NULL,
        familia VARCHAR(255),
        nome_popular VARCHAR(255),
        habitat VARCHAR(255) NOT NULL,
        descricao VARCHAR(255) NOT NULL,
        imagem VARCHAR(255)
    )''')

    # Cria tabela de imagens
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS imagens_angiospermas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    planta_id INT NOT NULL,
    imagem VARCHAR(255) NOT NULL,
    FOREIGN KEY (planta_id) REFERENCES angiospermas(id) ON DELETE CASCADE
    )''')

    # Cria login
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usuarios (
      id INT AUTO_INCREMENT PRIMARY KEY,
      username VARCHAR(255) UNIQUE NOT NULL,
      password VARCHAR(255) NOT NULL)
    ''')

    conn.commit()
    cursor.close()
    conn.close()

# Classe
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM usuarios WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        return User(id=user['id'], username=user['username'], password=user['password'])
    return None

# Rotas
# Página Inicial
@app.route('/', methods = ('GET',))
@login_required
def index():
    conn = get_db_connection();
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM angiospermas")
    plantas = cursor.fetchall()
    cursor.close()
    conn.close()
    print(request.endpoint)
    return render_template('index.html',plantas = plantas)

# Adicionar plantas
@app.route('/adicionar', methods = ('GET', 'POST',))
@login_required
def adicionar():
    if request.method == 'POST':
        especie = request.form['especie']
        familia = request.form['familia']
        nome_popular = request.form['nome_popular']
        habitat = request.form['habitat']
        descricao = request.form['descricao']

        lista = {"espécie" : especie, "familia" : familia, "habitat":habitat}
        excecao = list(map(lambda x:  "Campo obrigatório-" + x if not lista[x] else "-" + x ,lista.keys()))
        for x in excecao:
            if x.split("-")[0] ==  "Campo obrigatório":
                flash("Campo obrigatório:" + lista[x.split("-")[-1]])
                return redirect(url_for('adicionar'))



        # Tratamentos exceção


        #imagem = request.files['imagem']
        #imagem_filename = None

        '''if imagem and allowed_file(imagem.filename):
            filename = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagem_filename = filename'''

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO angiospermas (especie, familia, nome_popular, habitat, descricao) VALUES (%s, %s, %s, %s, %s)', (especie, familia, nome_popular, habitat, descricao))
        planta_id = cursor.lastrowid

        # Agora, salva as imagens
        imagens = request.files.getlist('imagens')
        for imagem in imagens:
            if imagem and allowed_file(imagem.filename):
                filename = secure_filename(imagem.filename)
                imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                cursor.execute('INSERT INTO imagens_angiospermas (planta_id, imagem) VALUES (%s, %s)', (planta_id, filename))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    return render_template('adicionar.html')

# Editar plantas
@app.route('/edit/<int:id>', methods = ('GET', 'POST'))
@login_required
def editar(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM angiospermas WHERE id = %s', (id,))
    planta = cursor.fetchone()

    if request.method == 'POST':
        especie = request.form['especie']
        familia = request.form['familia']
        nome_popular = request.form['nome_popular']
        habitat = request.form['habitat']

        cursor.execute('UPDATE angiospermas SET especie = %s, familia = %s, nome_popular = %s, habitat = %s WHERE id = %s', (especie, familia, nome_popular, habitat, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('index'))
    conn.close()
    cursor.close()
    return render_template('editar.html', planta = planta)

# Deletar Livro
@app.route('/delete/<int:id>', methods = ('POST',))
@login_required
def deletar(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM imagens_angiospermas WHERE planta_id = %s', (id,))
    cursor.execute('DELETE FROM angiospermas WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

# Informações
@app.route('/info/<int:id>', methods = ('GET',))
@login_required
def info(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM angiospermas WHERE id = %s', (id,))
    planta = cursor.fetchone()

    cursor.execute('SELECT * FROM imagens_angiospermas WHERE planta_id = %s', (id,))
    imagens = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('informacoes.html', planta = planta, imagens=imagens)

# Rota de identificação
@app.route('/identificar', methods = ['GET', 'POST'])
@login_required
def identificar():
    if request.method == 'POST':
        imagem = request.files['imagem']
        if imagem and allowed_file(imagem.filename):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(imagem.filename))
            imagem.save(filepath)

            # Converter imagem para base64
            with open(filepath, "rb") as img_file:
                ima_base64 = base64.b64encode(img_file.read()).decode('utf-8')

            # Requisição para a API
            url = "https://api.plant.id/v2/identify"
            headers = {
                "Content-Type" : "application/json",
                "Api-Key": PLANT_ID_API_KEY
            }
            payload = {
                "images": [ima_base64],
                "organs": ["leaf", "flowers", "fruit"],
                "details": ["common_names", "url", "name_authority", "wiki_description"]
            }
            response = requests.post(url, json=payload, headers=headers)
            print("Status code:", response.status_code)
            print("Response text:", response.text)
            result = response.json()

            if 'suggestions' in result:
                conn = get_db_connection()
                cursor = conn.cursor()
                especie = result['suggestions'][0]['plant_name']
                descricao = result['suggestions'][0].get('plant_details', {}).get('wiki_description', {}).get('value', 'Descrição não disponível')
                cursor.execute('INSERT INTO angiospermas (especie, familia, nome_popular, habitat, descricao) VALUES (%s, %s, %s, %s, %s)', (especie, "teste", "teste2", "teste3", descricao ))
                conn.commit()
                cursor.close()
                conn.close()
                print("Inseriu")
                return render_template('resultado_identificacao.html', especie=especie, descricao=descricao, imagem=filepath)
            else:
                flash("Não foi possível identificar a planta")
    return render_template('identificar.html')


# Rota de cadastrar
@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Gera hash da senha
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO usuarios (username, password) VALUES (%s, %s)', (username, password_hash))
            conn.commit()
            flash('Usuário cadastrado com sucesso! Faça login.')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash("Erro ao cadastrar: ", err)
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')


# Rota de Login
@app.route('/login', methods = ['GET', 'POST'])
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
            user_obj = User(id=user['id'], username=user['username'], password=user['password'])
            login_user(user_obj)

            #session['user_id'] = user['id']
           # session['username'] = user['username']
            return redirect(url_for('home'))
        else:
            flash('Usuário ou senha incorretos')
    return render_template('login.html')

# Rota Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Home
@app.route('/home')
def home():
    return render_template('Home.html')





# Proteger rotas
@app.before_request
def require_login():
    allowed_routes = ['login', 'register']


    if request.endpoint is None:
        return
    if 'user_id' not in session and not any(request.endpoint.startswith(route) for route in allowed_routes):

        return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)


# link Bootstrap https://getbootstrap.com/docs/5.3/content/images/