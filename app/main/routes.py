from itertools import groupby

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, make_response, send_file
from flask_login import login_required, current_user
from ..db import get_db_connection
import os
import io
from werkzeug.utils import secure_filename
#from xhtml2pdf import pisa
import openai
from openai import OpenAI
from dotenv import load_dotenv
import re
import pandas as pd

#from PROJETO_PLANTAE.app.utils.api_control import can_call_api, oncrement_api_usage, log_api_usage
from ..utils.api_control import can_call_api, oncrement_api_usage, log_api_usage
from ..utils.wikipedia import buscar_curiosidades_wikipedia as wiki
from ..utils.takon_key import buscar_ocorrencias_gbif, buscar_takonkey_gbif
from ..services.service import ecologia_home, home
from ..services.dengue import dengue
#pip install xhtml2pdf

from ..services.mapbiomas_service import obter_clima_atual, obter_temperatura_intervalo
from ..services.clima_service import obter_precipitacao_intervalo
from ..services.carbono import captura_carbono
from ..services.world_bank_service import get_world_population_series
from ..services.worldbank_forest_service import get_forest_area_percent_series
from ..services.geleiras import geleiras


CIDADES = {
    "São Paulo - SP": {"lat": -23.55, "lon": -46.63},
    "Rio de Janeiro - RJ": {"lat": -22.90, "lon": -43.20},
    "Brasília - DF": {"lat": -15.79, "lon": -47.88},
    "São José dos Campos - SP": {"lat": -23.1791, "lon": -45.8869}
}

main_bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

client = OpenAI(api_key=api_key)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')
    per_page = 10
    offset = (page - 1) * per_page
    print('offset', offset)


    conn = get_db_connection();
    cursor = conn.cursor(dictionary=True)
    id_usuario = current_user.id

    grupo = request.args.get('grupo')
    localizacao = request.args.get('localizacao')
    filtros = ['user_id = %s']
    params = [id_usuario]

    print("%", q)
    if q:
        filtros.append('(especie LIKE %s OR nome_popular LIKE %s OR familia LIKE %s OR grupo LIKE %s OR localizacao LIKE %s)')
        for _ in range(5):
            params.append("%",q)
    if grupo:
        filtros.append('grupo = %s')
        params.append(grupo)

    if localizacao:
        filtros.append('localizacao = %s')
        params.append(localizacao)





    # Se houver pesquisa
    where_clause = ' AND '.join(filtros)
    count_query =   'SELECT COUNT(*) as total FROM angiospermas WHERE ' + where_clause
    cursor.execute(count_query, tuple(params))
    total_rows = cursor.fetchone()['total']
    total_pages = (total_rows + per_page - 1) // per_page

    params_with_limit = params + [per_page, offset]
    query = 'SELECT * FROM angiospermas WHERE ' + where_clause + ' LIMIT %s OFFSET %s'
    cursor.execute(query, tuple(params_with_limit))
    plantas = cursor.fetchall()

    cursor.execute('SELECT DISTINCT localizacao FROM angiospermas WHERE user_id = %s AND localizacao IS NOT NULL', (id_usuario,))
    localizacoes = [row['localizacao'] for row in cursor.fetchall()]



    cursor.close()
    conn.close()
    print(request.endpoint)
    return render_template(
        'index.html',
        plantas=plantas,
        page = page,
        total_pages = total_pages,
        localizacoes=localizacoes,
        grupo_atual=grupo,
        localizacao_atual=localizacao,
        q=q,
        planta='planta',
        animal='animal',
        artropode='artropode',
        outros='outros'
    )

@main_bp.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar():
    if request.method == 'POST':
        especie = request.form['especie']
        familia = request.form['familia']
        nome_popular = request.form['nome_popular']
        habitat = request.form['habitat']
        localizacao = request.form['localizacao']
        descricao = request.form['descricao']
        situacao = request.form.getlist('situacao')
        grupo = request.form.getlist('grupo')
        latitude = request.form['latitude'] if len(request.form['latitude']) > 0 else None
        longitude = request.form['longitude'] if len(request.form['longitude'])>0 else None

        lista = {"espécie" : especie, "habitat":habitat}
        excecao = list(map(lambda x:  "Campo obrigatório-" + x if not lista[x] else "-" + x ,lista.keys()))
        for x in excecao:
            if x.split("-")[0] ==  "Campo obrigatório":
                flash("Campo obrigatório:" + lista[x.split("-")[-1]])
                return redirect(url_for('main.adicionar'))



        # Tratamentos exceção


        #imagem = request.files['imagem']
        #imagem_filename = None

        '''if imagem and allowed_file(imagem.filename):
            filename = secure_filename(imagem.filename)
            imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            imagem_filename = filename'''

        print('latitude:', latitude)
        conn = get_db_connection()
        cursor = conn.cursor()
        id_usuario = current_user.id
        cursor.execute('INSERT INTO angiospermas (especie, familia, nome_popular, habitat, localizacao, descricao, situacao, user_id, latitude, longitude, grupo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (especie, familia, nome_popular, habitat,localizacao, descricao, situacao[0], id_usuario, latitude, longitude, grupo[0]))
        planta_id = cursor.lastrowid

        # Agora, salva as imagens
        imagens = request.files.getlist('imagens')
        for imagem in imagens:
            if imagem and allowed_file(imagem.filename):
                filename = secure_filename(imagem.filename)
                imagem.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                cursor.execute('INSERT INTO imagens_angiospermas (planta_id, imagem) VALUES (%s, %s)', (planta_id, filename))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('main.index'))
    return render_template('adicionar.html')

@main_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
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
        localizacao = request.form['localizacao']

        cursor.execute(
            'UPDATE angiospermas SET especie = %s, familia = %s, nome_popular = %s, habitat = %s, localizacao = %s WHERE id = %s',
            (especie, familia, nome_popular, habitat,localizacao, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('main.index'))
    conn.close()
    cursor.close()
    return render_template('editar.html', planta=planta)

@main_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def deletar(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM imagens_angiospermas WHERE planta_id = %s', (id,))
    cursor.execute('DELETE FROM angiospermas WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('main.index'))

@main_bp.route('/info/<int:id>')
@login_required
def info(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM angiospermas WHERE id = %s', (id,))
    planta = cursor.fetchone()

    cursor.execute('SELECT * FROM imagens_angiospermas WHERE planta_id = %s', (id,))
    imagens = cursor.fetchall()

    cursor.execute('SELECT c.texto, c.data, u.username FROM comentarios2 c JOIN usuarios u ON c.usuario_id = u.id WHERE c.especie_id = %s ORDER BY c.data DESC', (id,))
    comentarios = cursor.fetchall()

    cursor.close()
    conn.close()

    curiosidades = wiki(planta['nome_popular'])

    return render_template('informacoes.html', planta=planta, imagens=imagens, curiosidades=curiosidades, comentarios=comentarios)

'''@main_bp.route('/home')
def home():

    return render_template('Home.html')'''

'''@main_bp.route('/ecologia_home')
def ecologia_home():
    return render_template('/ecologia_home.html')'''


'''@main_bp.route('/relatorio_pdf', methods = ['GET'])
@login_required
def gerar_relatorio_pdf():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    user_id = current_user.id
    grupo = request.args.getlist('grupo')
    localizacao = request.args.getlist('localizacao')
    lista = [grupo[0], localizacao[0]]

    query = [ ' AND ' +x+'@= %s' for x in lista]

    l = lambda c: c if not 'AND @=' in c else ''
    q = list(map(lambda e: e.replace('@',''),list(map(l, query))))
    print(q)

    print(grupo)
    print(len(localizacao[0]))
    if len(grupo[0]) > 2 and len(localizacao[0]) > 2:
        cursor.execute('SELECT * FROM angiospermas WHERE user_id = %s AND grupo = %s AND localizacao = %s', (user_id, grupo[0], localizacao[0]))
        print('entrou aqui')
        dados = cursor.fetchall()

    elif len(grupo[0]) <2  and  len(localizacao[0]) < 2:
        cursor.execute('SELECT * FROM angiospermas WHERE user_id = %s', (user_id,))
        dados = cursor.fetchall()
        print("entrou")


    cursor.execute('SELECT * FROM imagens_angiospermas')
    imagens = cursor.fetchall()
    caminho = 'file:///' + os.getcwd().replace('\\main','').replace('\\','/') + '/app/static/uploads/'

    html = render_template('relatorio_pdf.html', dados=dados, imagens=imagens, caminho=caminho)

    resultado = io.BytesIO()
    pisa.CreatePDF(src=html, dest=resultado)

    # Envia como resposta para download
    response = make_response(resultado.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=relatorio.pdf'
    return response'''





@main_bp.route('/descricao_organismo', methods=['GET', 'POST'])
@login_required
def descricao_organismo():
    acesso = current_user.tipo_acesso
    if acesso not in ['pro', 'premium']:
        return redirect(url_for('main.index'))
    if not can_call_api(current_user.id):
        flash("Limite de uso mensal atingido. Faça upgrade para continuar.", "warning")
        return redirect(url_for('main.index'))


    descricao = None
    erro = None
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()

        if not nome:
            flash("Por favor, digite o nome de um animal ou planta.")
            return redirect(url_for('main.descricao_organismo'))

        prompt = "Por favor, forneça uma descrição detalhada sobre o organismo chamado " + nome +"Incluindo características, habitat, alimentação, curiosidades e escreva o nome científico SEMPRE exatamente assim: Espécie:...."
        try:
            resposta = client.chat.completions.create(
                model = 'gpt-4o-mini',
                messages = [
                    {'role': 'system', 'content': 'Você é um assistente especializado em biologia'},
                    {'role': 'user', 'content': prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )


            descricao = resposta.choices[0].message.content
            oncrement_api_usage(current_user.id)
            log_api_usage(current_user.id, 'openAi', "success")

        except Exception as e:
            erro = str(e)
            log_api_usage(current_user.id, 'openAi', "fail")
    especie = list(re.findall("[Ee]sp[eé]cie: ?[*]{,2}? ?[A-z]* [A-z]*", descricao)) if descricao else None
    especie2 = especie[0].split(":")[-1].replace("*","").strip() if especie else None
    print("espécie: ", especie2)

    ocorrencias = ["-"]
    if especie2:
        taxonKey = buscar_takonkey_gbif(especie2)
        if taxonKey:
            ocorrencias = buscar_ocorrencias_gbif(taxonKey)

        else:
            flash("Espécie não encontrada.")

    return render_template('descricao_organismo.html', descricao=descricao, erro=erro, ocorrencias=ocorrencias, cont=len(ocorrencias))

@main_bp.route('/comentar/<int:especie_id>', methods=['POST'])
@login_required
def comentar(especie_id):
    texto = request.form['comentario']
    usuario_id = current_user.id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO comentarios2 (especie_id, usuario_id, texto) VALUES (%s, %s, %s)', (especie_id, usuario_id, texto))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('main.info', id=especie_id))

@main_bp.route('/relatorio/excel', methods=['GET'])
@login_required
def gerar_relatorio_excel():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    id = current_user.id
    cursor.execute('SELECT * FROM angiospermas WHERE user_id = %s', (id,))
    dados = cursor.fetchall()
    if dados:
        colunas = dados[0].keys()
        colunas = list(map(lambda x : str(x), colunas))
        dicionario = {colunas[x]: [dados[y][colunas[x]] for y in range(0, len(dados))] for x in range(0, len(colunas))}
        dataframe = pd.DataFrame(dicionario)
        print(dataframe)

        # Cria um buffer para Dataframe
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            dataframe.to_excel(writer, index=False, sheet_name='Relatório')
        output.seek(0)
        return  send_file(
            output,
            as_attachment=True,
            download_name='relatorio_especies.xlsx',
            mimetype='application,vnd.openxmlformats-officedocument.spreadsheetml.sheet')



@main_bp.route("/clima", methods=["GET", "POST"])
@login_required
def clima():
    clima_atual = None
    erro = None
    lat_val = None
    lon_val = None

    if request.method == "POST":
        lat = request.form.get("latitude", "").strip()
        lon = request.form.get("longitude", "").strip()

        lat_val = float(lat)
        lon_val = float(lon)

        if not lat or not lon:
            erro = "Por Favor, informe latitude e longitude."
        else:
            try:
                latitude = float(lat.replace(",", "."))
                longitude = float(lon.replace(",", "."))

                clima_atual = obter_clima_atual(latitude, longitude)
                if clima_atual is None:
                    erro = "Não foi possível obter os dados de clima."
            except ValueError:
                erro = "Coordenadas inválidas. Use números (ex.: -15.8 e -47.9)."
    return render_template(
            "clima.html",
            clima=clima_atual,
            erro=erro,
            latitude=lat_val,
            longitude=lon_val
        )

@main_bp.route("/clima_intervalo", methods=["GET", "POST"])
@login_required
def clima_intervalo():
    dados = None
    dados_por_ano = {}
    erro = None
    cidade_selecionada = None
    ano_ini_val = None
    ano_fim_val = None
    freq_val = "mensal"



    if request.method == "POST":
        cidade_selecionada = request.form.get('cidade', '').strip()

        ano_inicio = request.form.get("ano_inicio", "").strip()
        ano_fim = request.form.get("ano_fim", "").strip()
        frequencia = request.form.get("frequencia", "Semanal")

        ano_ini_val, ano_fim_val = ano_inicio, ano_fim



        freq_val = frequencia

        if not cidade_selecionada or cidade_selecionada not in CIDADES:
            erro = "Selecione uma cidade válida"
        elif not ano_inicio or not ano_fim:
            erro = "Informe o ano inicial e o ano final"
        else:
            try:
                ano_i = int(ano_inicio)
                ano_f = int(ano_fim)

                if ano_f < ano_i:
                    erro = "O ano final deve ser maior ou igual ao ano inicial"
                else:
                    coords = CIDADES[cidade_selecionada]
                    latitude = coords["lat"]
                    longitude = coords["lon"]
                    dados = obter_temperatura_intervalo(latitude, longitude, ano_i, ano_f, freq_val)
                    if dados is None:
                        erro = "Não foi possível obter os dados de temperatura"
                    else:
                        # Aqui montamos estrutura por ano para os gráficos
                        for row in dados:
                            ano = row["ano"]
                            if ano not in dados_por_ano:
                                dados_por_ano[ano] = {
                                    "indices": [],
                                    "temperaturas": [],
                                }
                            if row["temperatura_media"] is not None:
                                dados_por_ano[ano]["indices"].append(row["indice"])
                                dados_por_ano[ano]["temperaturas"].append(row["temperatura_media"])

            except ValueError:
                erro = "Valores inválidos. Use números válidos para coordenadas e anos"
    return render_template(
        "clima_intervalo.html",
        dados = dados,
        dados_por_ano=dados_por_ano,
        erro = erro,
        cidade_selecionada=cidade_selecionada,
        cidades = CIDADES,
        ano_inicio = ano_ini_val,
        ano_fim = ano_fim_val,
        frequencia = freq_val or "Semanal",
    )

@main_bp.route("/dengue_sjc")
@login_required
def dengue_sjc():
    erro = None
    dados_por_ano = {}

    try:
        dados_raw = dengue()

        for ano, df in dados_raw.items():
            semanas = df["data_iniSE"].tolist()[::-1]
            casos = df["casos"].tolist()[::-1]

            dados_por_ano[int(ano)] = {
                "semanas": semanas,
                "casos": casos,
            }
    except Exception as e:
        erro = f"Erro ao carregar dados de dengue: {e}"

    return render_template(
        "dengue_sjc.html",
        erro=erro,
        dados_por_ano=dados_por_ano,
    )

@main_bp.route("/chuva_intervalo", methods=["GET", "POST"])
@login_required
def chuva_intervalo():
    dados = None
    dados_por_ano = {}
    erro = None

    cidade_selecionada = None
    ano_ini_val = None
    ano_fim_val = None
    freq_val = "mensal"

    if request.method == "POST":
        cidade_selecionada = request.form.get("cidade", '').strip()
        ano_inicio = request.form.get("ano_inicio", "").strip()
        ano_fim = request.form.get("ano_fim", "").strip()
        frequencia = request.form.get("frequencia", "mensal")

        ano_ini_val, ano_fim_val = ano_inicio, ano_fim
        freq_val = frequencia

        if not cidade_selecionada or cidade_selecionada not in CIDADES:
            erro = "Selecione uma cidade válida"
        elif not ano_inicio or not ano_fim:
            erro = "Informe o ano inicial e o ano final"
        else:
            try:
                ano_i = int(ano_inicio)
                ano_f = int(ano_fim)

                if ano_f < ano_i:
                    erro = "O ano final deve ser maior ou igual ao ano inicial"
                else:
                    coords = CIDADES[cidade_selecionada]
                    latitude = coords["lat"]
                    longitude = coords["lon"]

                    dados = obter_precipitacao_intervalo(
                        latitude,
                        longitude,
                        ano_i,
                        ano_f,
                        frequencia=frequencia,
                    )
                    if dados is None:
                        erro = "Não foi possível obter os dados de precipitação"
                    else:
                        for row in dados:
                            ano = row["ano"]
                            if ano not in dados_por_ano:
                                dados_por_ano[ano] = {
                                    "indices": [],
                                    "chuva_mm": [],
                                }
                            if row["chuva_mm"] is not None:
                                dados_por_ano[ano]["indices"].append(row["indice"])
                                dados_por_ano[ano]["chuva_mm"].append(row["chuva_mm"])
            except ValueError:
                erro = "Anos inválidos. Use apenas números"
    return render_template(
        "chuva_intervalo.html",
        dados = dados,
        dados_por_ano = dados_por_ano,
        erro = erro,
        cidade_selecionada = cidade_selecionada,
        cidades = CIDADES,
        ano_inicio = ano_ini_val,
        ano_fim = ano_fim_val,
        frequencia = freq_val
    )

@main_bp.route("/carbono", methods=["GET","POST"])
@login_required
def carbono():
    erro = None
    dados_por_ano = {}

    ano_inicial_val = None
    ano_fim_val = None

    if request.method == "POST":
        ano_inicial_val = request.form.get("ano_inicio","").strip()
        ano_fim_val = request.form.get("ano_fim", "").strip()

        if not ano_inicial_val or not ano_fim_val:
            erro = "Informe o ano inicial e o ano final"
        else:
            try:
                ano_i = int(ano_inicial_val)
                ano_f = int(ano_fim_val)

                if ano_f < ano_i:
                    erro = "O ano final deve ser maior ou igual ao ano inicial"
                else:
                    dados_raw = captura_carbono(ano_i, ano_f)

                    for ano, df in dados_raw.items():
                        meses = df["month"].tolist()
                        valores = df["average"].tolist()

                        dados_por_ano[int(ano)] = {
                            "meses": meses,
                            "co2": valores,
                        }
            except Exception as e:
                erro = f"Erro ao gerar gráficos: {e}"
    return render_template(
        "carbono.html",
        erro = erro,
        dados_por_ano = dados_por_ano,
        ano_inicio = ano_inicial_val,
        ano_fim = ano_fim_val,
    )



@main_bp.route("/populacao_mundial")
@login_required
def populacao_mundial():
    erro = None
    anos = []
    populacao = []
    pairs = []

    try:
        serie = get_world_population_series()
        anos = serie["anos"]
        populacao = serie["populacao"]

        pairs = list(zip(anos, populacao))
    except Exception as e:
        erro = str(e)
    return render_template(
        "populacao_mundial.html",
        erro = erro,
        anos = serie["anos"],
        populacao = serie["populacao"],
        pairs = pairs,
    )

PAISES_FLORESTAS = {
    "Brasil": "BR",
    "Estados Unidos": "US",
    "Indonésia": "ID",
}

@main_bp.route("/florestas", methods=["GET", "POST"])
@login_required
def florestas():
    erro = None
    pais_escolhido = request.form.get("pais") if request.method == "POST" else "BR"
    anos = []
    valores = []

    try:
        if pais_escolhido not in PAISES_FLORESTAS.values():
            pais_escolhido = "BR"
        print("o")
        serie = get_forest_area_percent_series(pais_escolhido)
        print("i")
        anos = serie["anos"]
        valores = serie["valores"]
    except Exception as e:
        print("exceção")
        erro = str(e)

    return render_template(
        "florestas.html",
        erro = erro,
        paises = PAISES_FLORESTAS,
        pais_escolhido = pais_escolhido,
        anos = anos,
        valores = valores,
    )

def media_lista(valores):
    if not valores:
        return None
    vals = [float(v) for v in valores if v is not None]
    return (sum(vals) / len(vals)) if vals else None

@main_bp.route("/gelo_derretimento", methods=["GET", "POST"])
@login_required
def derretimento_gelo():
    erro = None

    ano_inicio = request.form.get("ano_inicio", "").strip() if request.method == "POST" else ""
    ano_fim = request.form.get("ano_fim", "").strip() if request.method == "POST" else ""

    dados_por_ano={}

    try:
        if ano_inicio and ano_fim:
            ai = int(ano_inicio)
            af = int(ano_fim)
            if af < ai:
                raise ValueError("Ano final deve ser >= ano inicial")
            bruto = geleiras(ai,af)
            print("foi")
        else:
            bruto = geleiras()

        for ano, meses_dict in bruto.items():
            meses_ordenados = sorted(meses_dict.keys(), key=lambda m: int(m))
            labels = []
            medias = []

            for mes in meses_ordenados:
                labels.append(str(mes))
                medias.append(media_lista(meses_dict.get(mes, [])))

            dados_por_ano[int(ano)] = {"meses": labels, "medias": medias}

        dados_por_ano = dict(sorted(dados_por_ano.items(), key=lambda x: x[0]))
    except Exception as e:
        erro = str(e)
    return render_template(
        "derretimento_gelo.html",
        erro = erro,
        dados_por_ano = dados_por_ano,
        ano_inicio = ano_inicio,
        ano_fim = ano_fim,
    )

