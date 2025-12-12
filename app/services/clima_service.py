import requests
from collections import defaultdict
from datetime import datetime

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

def obter_precipitacao_intervalo(
        latitude: float,
        longitude: float,
        ano_inicio: int,
        ano_fim: int,
        frequencia: str = "mensal",
):
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": f"{ano_inicio}-01-01",
        "end_date": f"{ano_fim}-12-31",
        "daily": "precipitation_sum", # chuva total do dia
        "timezone": "auto",
    }

    try:
        resp = requests.get(ARCHIVE_URL, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print("Erro ao chamar Open-Meteo (chuva):", e)
        return None

    daily = data.get("daily") or {}
    datas = daily.get("time") or []
    chuva = daily.get("precipitation_sum") or []

    if not datas or not chuva or len(datas) != len(chuva):
        return None

    soma = defaultdict(float)
    cont = defaultdict(int)

    for dt_str, mm in zip(datas, chuva):
        if mm is None:
            continue

        try:
            dt = datetime.fromisoformat(dt_str)
        except Exception:
            continue

        if frequencia == "semanal":
            iso_year, iso_week, _ = dt.isocalendar()
            chave = (iso_year, iso_week)
        else:
            chave = (dt.year, dt.month)

        soma[chave] += mm
        cont[chave] += 1

    resultado = []
    for (ano, idx) in sorted(soma.keys()):
        total_mm = soma[(ano, idx)]
        resultado.append(
            {
                "ano": ano,
                "indice": idx,
                "chuva_mm": total_mm,
            }
        )
    return resultado



