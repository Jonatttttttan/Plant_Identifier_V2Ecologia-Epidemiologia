import requests

def buscar_curiosidades_wikipedia(titulo):
    url = "https://pt.wikipedia.org/api/rest_v1/page/summary/" + titulo
    response = requests.get(url)
    if response.status_code == 200 or response.status_code == 201:
        print(response.text)
        return response.json()
    return None