"""Previsao de mare por interpolacao entre extremos (alta/baixa) da Tabua DHN.

As Tabuas de Mare trazem so os horarios/alturas de preamar e baixa-mar
(nao as constantes harmonicas). Entre dois extremos consecutivos, a mare
e aproximada por uma curva em cosseno (equivalente continuo da "regra
das duodecimas" usada em navegacao) -- boa aproximacao para mares
semidiurnas como as de Pernambuco.
"""
import json
import math
import os
from bisect import bisect_left
from datetime import datetime, timedelta, timezone

TIDE_DIR = os.path.join(os.path.dirname(__file__), "tide_data")
LOCAL_UTC_OFFSET_H = 3  # Fuso UTC -03:00 (tabuas DHN em hora local de Brasilia)


def build_cache(pdf_path: str, year: int, out_name: str) -> str:
    """Parseia o PDF da tabua e salva uma lista de extremos (UTC) em JSON.

    So e chamada quando o cache JSON ainda nao existe; pdfplumber e
    importado aqui (nao no topo do modulo) para nao ser uma dependencia
    obrigatoria no pipeline automatizado, que so le o cache ja pronto.
    """
    from tide_parse import parse_tide_pdf
    parsed = parse_tide_pdf(pdf_path)
    extrema = []
    for month, days in parsed.items():
        for day, entries in days.items():
            for hhmm, height in entries:
                hour, minute = int(hhmm[:2]), int(hhmm[2:])
                local_dt = datetime(year, month, day, hour, minute)
                utc_dt = local_dt + timedelta(hours=LOCAL_UTC_OFFSET_H)
                extrema.append((utc_dt.isoformat(), height))
    extrema.sort(key=lambda e: e[0])

    os.makedirs(TIDE_DIR, exist_ok=True)
    out_path = os.path.join(TIDE_DIR, out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(extrema, f)
    return out_path


class TideTable:
    def __init__(self, json_path: str):
        with open(json_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.times = [datetime.fromisoformat(t).replace(tzinfo=timezone.utc) for t, _ in raw]
        self.heights = [h for _, h in raw]

    def height_at(self, dt_utc: datetime):
        if dt_utc.tzinfo is None:
            dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        if not self.times or dt_utc < self.times[0] or dt_utc > self.times[-1]:
            return None
        i = bisect_left(self.times, dt_utc)
        if i == 0:
            return self.heights[0]
        if self.times[i - 1] == dt_utc:
            return self.heights[i - 1]
        t0, t1 = self.times[i - 1], self.times[i]
        h0, h1 = self.heights[i - 1], self.heights[i]
        frac = (dt_utc - t0).total_seconds() / (t1 - t0).total_seconds()
        return h0 + (h1 - h0) * (1 - math.cos(math.pi * frac)) / 2


def ensure_cache(pdf_path: str, year: int, out_name: str) -> str:
    out_path = os.path.join(TIDE_DIR, out_name)
    if not os.path.exists(out_path):
        build_cache(pdf_path, year, out_name)
    return out_path
