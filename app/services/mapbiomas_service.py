import requests
from collections import defaultdict
from datetime import datetime

BASE_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

def obter_clima_atual(latitude: float, longitude: float):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
        "timezone": "auto",
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current_weather") or {}
        print(data)

        # Normaliza em um dict simples para usar no template
        return {
            "temperature": current.get("temperature"),
            "windspeed": current.get("windspeed"),
            "winddirection": current.get("winddirection"),
            "weathercode": current.get("weathercode"),
            "time": current.get("time"),
            "timezone": data.get("timezone"),
            "elevation": data.get("elevation"),
        }
    except Exception:
        return None



def obter_temperatura_intervalo(
    latitude: float,
    longitude: float,
    ano_inicio: int,
    ano_fim: int,
    frequencia: str,
):
    """
    Busca temperatura média diária entre ano_inicio e ano_fim (inclusive)
    e devolve uma lista agregada por mês ou por semana.

    frequencia: "mensal" ou "semanal"
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": f"{ano_inicio}-01-01",
        "end_date": f"{ano_fim}-12-31",
        "daily": "temperature_2m_mean",
        "timezone": "auto",
    }

    try:
        resp = requests.get(ARCHIVE_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        print(frequencia)
    except Exception:
        return None

    daily = data.get("daily") or {}
    datas = daily.get("time") or []
    temps = daily.get("temperature_2m_mean") or []

    if not datas or not temps or len(datas) != len(temps):
        return None

    # Agrupar: chave -> soma e contagem
    soma = defaultdict(float)
    cont = defaultdict(int)

    for dt_str, temp in zip(datas, temps):
        if temp is None:
            continue

        try:
            dt = datetime.fromisoformat(dt_str)
        except Exception:
            continue

        if frequencia == "semanal":
            iso_year, iso_week, _ = dt.isocalendar()  # ano/semana ISO
            chave = (iso_year, iso_week)
            print("Semanal")
        else:  # padrão: mensal
            chave = (dt.year, dt.month)

        soma[chave] += temp
        cont[chave] += 1

    # Montar lista ordenada
    resultado = []
    for (ano, idx) in sorted(soma.keys()):
        media = soma[(ano, idx)] / cont[(ano, idx)] if cont[(ano, idx)] > 0 else None
        resultado.append(
            {
                "ano": ano,
                "indice": idx,  # mês (1–12) ou semana (1–53)
                "temperatura_media": media,
            }
        )

    return resultado



