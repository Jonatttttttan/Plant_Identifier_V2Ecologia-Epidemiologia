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

service = Blueprint('service', __name__)

@service.route('/ecologia_home')
def ecologia_home():
    return render_template('ecologia_home.html')

@service.route('/home')
def home():
    return render_template('Home.html')

@service.route('/mapa')
@login_required
def mapa():
    acesso = current_user.tipo_acesso
    if acesso not in ['pro', 'premium']:
        return redirect(url_for('main.index'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT especie, latitude, longitude FROM angiospermas WHERE user_id = %s AND latitude IS NOT NULL AND longitude IS NOT NULL', (current_user.id,))
    pontos = cursor.fetchall()
    print(pontos)
    cursor.close()
    return render_template('mapa.html', pontos=pontos)

@service.route('/CuriosidadesAnimais', methods=['GET', 'POST'])
@login_required
def curiosidades_animais():
    if request.method == "POST":
        nome = request.form["nome"]
        print(nome)
        taxonKey = buscar_takonkey_gbif(nome)
        print(taxonKey)
        if taxonKey != None:
            curiosidades = buscar_ocorrencias_gbif(taxonKey)
            print(curiosidades)
            return render_template('resultado_curiosidades_animais.html', curiosidades=curiosidades, nome=nome)
        else:
            return redirect(url_for('service.curiosidades_animais'))
    return render_template('curiosidades_animais.html')

@service.route('/distribuicao', methods=['GET', 'POST'])
@login_required
def distribuicao_especie():
    acesso = current_user.tipo_acesso
    if acesso not in ['pro', 'premium']:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        nome = request.form['nome']
        taxonKey = buscar_takonkey_gbif(nome)
        if taxonKey:
            ocorrencias = buscar_ocorrencias_gbif(taxonKey)
            return render_template('resultado_distribuicao.html', nome=nome, ocorrencias=ocorrencias)
        else:
            flash("Espécie não encontrada.")
            return redirect(url_for('service.distribuicao_especie'))
    return render_template('form_distribuicao.html')
