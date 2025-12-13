import time
import requests

WORLD_BANK_BASE = "https://api.worldbank.org/v2"

_CACHE = {"ts": 0, "data": None}
_CACHE_TTL_SECONDS = 60 * 60 * 6

def get_world_population_series():
    now = time.time()
    if _CACHE["data"] is not None and (now - _CACHE["ts"]) < _CACHE_TTL_SECONDS:
        return _CACHE["data"]

    url = f"{WORLD_BANK_BASE}/country/WLD/indicator/SP.POP.TOTL"
    params = {
        "format": "json",
        "per_page": 200,
    }
    r = requests.get(url, params=params, timeout=20)
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
            pares.append((int(ano), int(val)))
        except ValueError:
            continue
    pares.sort(key=lambda x: x[0])

    data = {
        "anos": [a for a, _ in pares],
        "populacao": [v for _, v in pares],
    }

    _CACHE["ts"] = now
    _CACHE["data"] = data
    return data



