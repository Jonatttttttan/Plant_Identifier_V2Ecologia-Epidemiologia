import requests

WORLD_BANK_BASE = "https://api.worldbank.org/v2"

def get_forest_area_percent_series(country_code: str):
    url = f"{WORLD_BANK_BASE}/country/{country_code}/indicator/AG.LND.FRST.ZS"
    print("chamado api")
    params = {"format": "json", "per_page": 200}

    r = requests.get(url, params=params, timeout=20)
    print(r.status_code)
    r.raise_for_status()
    payload = r.json()

    if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
        raise ValueError("Resposta inesperada do Banco Mundial")
    rows = payload[1]
    pares = []
    for row in rows:
        ano = row.get("date")
        val = row.get("value")
        if ano is None or val is None:
            continue
        try:
            pares.append((int(ano), float(val)))
        except ValueError:
            continue
    pares.sort(key=lambda x: x[0])
    print(pares)

    return {
        "anos": [a for a, _ in pares],
        "valores": [v for _, v in pares],
    }
