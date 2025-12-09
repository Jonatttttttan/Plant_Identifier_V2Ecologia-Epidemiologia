from flask import Flask, request
import requests

def buscar_takonkey_gbif(nome):
    url = 'https://api.gbif.org/v1/species/match'
    params = {"name": nome}
    r = requests.get(url, params=params)

    if r.status_code == 200 or r.status_code == 201:
        data = r.json()
        print(r.text)
        return data.get("usageKey")
    return None

def buscar_ocorrencias_gbif(taxonkey, limite=50):
    url = "https://api.gbif.org/v1/occurrence/search"
    params = {"taxonkey":taxonkey, "limit": limite, "hasCoordinate":"true"}
    r = requests.get(url, params=params)
    print(r.status_code)

    ocorrencias_formatadas = []

    if r.status_code == 200 or r.status_code == 201:
        dados = r.json().get("results", [])

        for item in dados:
            latitude = item.get('decimalLatitude')
            longitude = item.get('decimalLongitude')
            if not latitude or not longitude:
                continue

            data = item.get('eventDate')
            local = item.get('locality', 'Local desconhecido')
            pais = item.get('country')
            localidade = item.get('locality') or item.get('municipality')
            classe = item.get('class')
            ordem = item.get('order')
            familia = item.get('family')
            identificado = item.get('publishingOrgKey')
            habitat = item.get('habitat')

            # Buscar imagem (se houver)
            imagem = None
            extensoes = item.get("extensions", {})
            multimidia = extensoes.get("http://rs.gbif.org/terms/1.0/Multimedia", [])
            if multimidia:
                imagem = multimidia[0].get('http://purl.org/dc/terms/identifier')

            ocorrencias_formatadas.append({
                "latitude": latitude,
                "longitude": longitude,
                "data": data,
                "local": local,
                "imagem": imagem,
                "pais":pais,
                "localidade": localidade,
                "classe": classe,
                "ordem": ordem,
                "familia": familia,
                "identificado": identificado,
                "habitat": habitat
            })

    return ocorrencias_formatadas





