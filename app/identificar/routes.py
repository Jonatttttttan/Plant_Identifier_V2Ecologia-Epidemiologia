from flask import Blueprint, request, render_template, flash, current_app, redirect, url_for
from flask_login import login_required, current_user
import os, base64, requests
from ..db import get_db_connection
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from ..main.routes import allowed_file
#from PROJETO_PLANTAE.app.utils.api_control import can_call_api, oncrement_api_usage, log_api_usage
from ..utils.api_control import can_call_api, oncrement_api_usage, log_api_usage

load_dotenv()
PLANT_ID_API_KEY = os.getenv('PLANT_ID_API_KEY')

identificar_bp = Blueprint('identificar', __name__)
UPLOADER_FOLDER = 'static/uploads'

@identificar_bp.route('/identificar', methods=['GET', 'POST'])
@login_required
def identificar():
    acesso = current_user.tipo_acesso
    if acesso not in ['pro', 'premium']:
        return redirect(url_for('main.index'))
    if not can_call_api(current_user.id):
        flash("Limite de uso mensal atingido. Faça upgrade para continuar.", "warning")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        imagem = request.files['imagem']
        estado_id = request.form['estado']
        municipio_id = request.form['municipio']

        if imagem and allowed_file(imagem.filename):
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(imagem.filename))
            imagem.save(filepath)

            # Converter imagem para base64
            with open(filepath, "rb") as img_file:
                ima_base64 = base64.b64encode(img_file.read()).decode('utf-8')

            # Requisição para a API Plant.id
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
                '''conn = get_db_connection()
                cursor = conn.cursor()'''
                especie = result['suggestions'][0]['plant_name']
                descricao = result['suggestions'][0].get('plant_details', {}).get('wiki_description', {}).get('value', 'Descrição não disponível')
                '''cursor.execute('INSERT INTO angiospermas (especie, familia, nome_popular, habitat, descricao, situacao) VALUES (%s, %s, %s, %s, %s, %s)', (especie, "teste", "teste2", "teste3", descricao, "teste4" ))
                conn.commit()
                cursor.close()
                conn.close()'''

                # Chamada da API do IBGE com o ID do municípo
                url_ibge = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios/" + municipio_id
                resposta = requests.get(url_ibge)
                print("Resposta IBGE:", str(resposta.status_code) + " | " + resposta.text)
                dados_municipio = resposta.json()

                nome_municipio = dados_municipio['nome']
                microrregiao = dados_municipio['microrregiao']['nome']
                estado_nome = dados_municipio['microrregiao']['mesorregiao']['UF']['nome']
                regiao_nome = dados_municipio['microrregiao']['mesorregiao']['UF']['regiao']['nome']
                cod_ibge = dados_municipio['id']

                oncrement_api_usage(current_user.id)
                log_api_usage(current_user.id, 'plant.id', 'success')


                return render_template('resultado_identificacao.html', especie=especie, descricao=descricao, imagem=filepath, nome_municipio=nome_municipio, estado_nome=estado_nome, regiao_nome=regiao_nome,cod_ibge=cod_ibge)

            else:
                flash("Não foi possível identificar a planta")
                log_api_usage(current_user.id, 'plant.id', 'fail')
    return render_template('identificar.html') # MAP Biomas e GBIF

@identificar_bp.route("/identificar_insetos", methods = ['GET', 'POST'])
@login_required
def identificar_insetos():
    acesso = current_user.tipo_acesso
    if acesso not in ['pro', 'premium']:
        return redirect(url_for('main.index'))
    if not can_call_api(current_user.id):
        flash("Limite de uso mensal atingido. Faça upgrade para continuar.", "warning")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        imagem = request.files['imagem']
        if imagem and allowed_file(imagem.filename):
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(imagem.filename))
            imagem.save(filepath)
        # Converter imagem para base 64
        with open(filepath, 'rb') as img_file:
            ima_base64 = base64.b64encode(img_file.read()).decode('utf-8')

        # requisição para a API
        url = 'https://insect.kindwise.com/api/v1/identification'
        headers = {
            "Content-Type":"application/json",
            "Api-Key": os.getenv('INSECT_ID_API_KEY')
        }
        payload = {
            "images":[ima_base64],
            "similar_images": True
        }


        try:
          response = requests.post(url, json=payload, headers=headers)
          print("Status code:", response.status_code)
          print(response.text)
          data = response.json()
          #response = requests.post(url, json=payload, headers=headers)
          #data = response.json()


          if response.status_code==201 and 'result' in data:
              sugestoes = data['result']['classification']['suggestions']

              imagem_nome = imagem.filename

              return render_template('resultado_identificacao_insetos.html', sugestoes=sugestoes, imagem=imagem_nome)
          else:
              flash("Não foi possível identificar o inseto. Tente novamente")
              return redirect(url_for('identificar.identificar_insetos'))
        except Exception as a:
            print("Erro:", a)
            flash("Erro na comunicação com a API")
            return redirect(url_for('identificar.identificar_insetos'))
    return render_template("identificar_insetos.html")

@identificar_bp.route('/identificar_cogumelos', methods=['GET', 'POST'])
@login_required
def identificar_cogumelos():
    acesso = current_user.tipo_acesso
    if acesso not in ['pro', 'premium']:
        return redirect(url_for('main.index'))
    if not can_call_api(current_user.id):
        flash("Limite de uso mensal atingido. Faça upgrade para continuar.", "warning")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        imagem = request.files['imagem']
        print(imagem.filename)
        if imagem and allowed_file(imagem.filename):
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(imagem.filename))
            imagem.save(filepath)
        # Converter a imagem por base 64
            with open(filepath, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

        # Requisição API
            url ='https://mushroom.kindwise.com/api/v1/identification?details=common_names,url,edibility,psychoactive,characteristic,look_alike&language=pt'
            headers = {
                "Content-Type":"application/json",
                "Api-Key":os.getenv("MUSHROOM_ID_API_KEY")
            }
            payload = {
                "images":[img_base64],
                "similar_images":True
            }

            try:

                response = requests.post(url, json=payload, headers=headers)
                print(response.status_code)
                if response.status_code == 200 or response.status_code == 201:

                    data = response.json()
                    sugestoes = data["result"]["classification"]["suggestions"]
                    print("Teste")
                    imagem_nome = imagem.filename
                    return render_template('resultado_identificacao_cogumelos.html', sugestoes=sugestoes, imagem=imagem_nome)
                else:
                    print("Teste else")
                    flash("Erro o identificar o cogumelo. Verifique a imagem ou tente novamente")
                    return redirect(url_for("identificar.identificar_cogumelos"))
            except Exception as e:
                print("Teste erro")
                print("Erro:", e)
                flash("Erro ao se conectar com a API de identificação")
                return redirect(url_for("identificar.identificar_cogumelos"))
        else:
            return redirect(url_for("identificar.identificar_cogumelos"))
    return render_template("identificar_cogumelos.html")

@identificar_bp.route('/identificar_pg', methods=['GET', 'POST'])
@login_required
def identificar_pg():
    acesso = current_user.tipo_acesso
    if acesso not in ['pro', 'premium']:
        return redirect(url_for('main.index'))
    if not can_call_api(current_user.id):
        flash("Limite de uso mensal atingido. Faça upgrade para continuar.", "warning")
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        imagem = request.files['imagem']
        print(imagem)
        if imagem and allowed_file(imagem.filename):
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(imagem.filename))
            print(filepath)
            imagem.save(filepath)
        # Converter imagem para base 64
            with open(filepath, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')

        # Requisição API
            url = 'https://crop.kindwise.com/api/v1/identification'
            headers = {
                "Content-Type":"application/json",
                "Api-Key":os.getenv("AUTH_ID_API_KEY")
            }
            payload = {
                "images":[img_base64],
                "similar_images":True
            }
            try:
                response = requests.post(url, json=payload, headers=headers)
                print("Status code:", response.status_code)
                print(response.text)
                if response.status_code == 200 or response.status_code == 201:
                    data = response.json()
                    sugestoes = data.get("result", {}).get("disease",{}).get("suggestions", [])
                    imagem_nome = imagem.filename

                    return render_template("resultado_health.html", sugestoes=sugestoes, imagem=imagem_nome)
                else:
                    flash("Não foi possível ientificar imagem")
                    print("Teste2")
                    return redirect(url_for('identificar.identificar_pg'))
            except Exception as a:
                print("Erro:", a)
                return redirect(url_for('identificar.identificar_pg'))
        else:
            print("falha")
            return redirect(url_for('identificar.identificar_pg'))
    return render_template('identificar_health.html')

# Identificação de aves
'''@identificar_bp.route("/identificar_plantas2", methods=['GET','POST'])
@login_required
def identificar_aves():
    if request.method == 'POST':
        imagem = request.files['imagem']
        if imagem and allowed_file(imagem.filename):
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(imagem.filename))
            imagem.save(filepath)
           
            with open(filepath, 'rb') as img_i:
                img_base64 = base64.b64encode(img_i.read()).decode('utf-8')
            
            api_key = os.getenv('PLANT_NET_API_KEY')
            url = 'https://my-api.plantnet.org/v2/identify/all?api-key=' + api_key

            with open(filepath, 'rb') as img_file:
                print(img_file)
                files = [('images', (secure_filename(imagem.filename), img_file,'image/jpeg'))]
                data = {
                    'organs':'auto'

                }


                response = requests.post(url, files=files, data=data)
            print("Response status code:", response.status_code)
            print(response.text)

            # Visualizar resposta

            if response.status_code == 200 or response.status_code == 201:
                resultado = response.json()
                # Verifica se há resultados
                if resultado['results']:
                    melhor = resultado['results'][0]
                    especie = melhor['species']
                    nome_cientifico = especie.get('scientificNameWithoutAuthor', 'Desconhecido')
                    nome_comum = especie.get('commonNames', ['Desconhecido'])[0]

                    confianca = melhor['score'] * 100
                    return render_template('resultado_aves.html',
                                           nome_comum=nome_comum,
                                           nome_cientifico=nome_cientifico,
                                           confianca=round(confianca,1))
                else:
                    flash('Falha ao identificar imagem')
                    print("Falha nos reults")
            else:
                flash("Falha na API")
                print("Falha na API")
            return redirect(url_for('identificar.identificar_plantas2'))

        else:
            flash("Falha ao identifica imagem")
            return redirect(url_for('identificar.identificar_plantas2'))

    else:
        return render_template('identificar_aves.html')
'''

