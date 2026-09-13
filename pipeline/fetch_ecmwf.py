"""Busca de dados do ECMWF Open Data (HRES) para ondas e vento."""
import os
from ecmwf.opendata import Client

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")


def hres_steps(max_hours: int) -> list[int]:
    """Lista de passos validos do HRES ate max_hours (3/3h ate 144h, 6/6h depois)."""
    steps = list(range(0, min(max_hours, 144) + 1, 3))
    if max_hours > 144:
        steps += list(range(150, min(max_hours, 240) + 1, 6))
    return steps


def fetch_wave(max_hours: int = 168, date=None) -> tuple[str, object]:
    os.makedirs(RAW_DIR, exist_ok=True)
    target = os.path.join(RAW_DIR, "wave_latest.grib2")
    client = Client(source="ecmwf")
    request = dict(
        stream="wave",
        type="fc",
        step=hres_steps(max_hours),
        param=["swh", "mwd", "mwp", "pp1d", "mp2"],
        target=target,
    )
    if date is not None:
        request["date"] = date
    result = client.retrieve(**request)
    return target, result.datetime


def fetch_wind(max_hours: int = 168, date=None) -> tuple[str, object]:
    os.makedirs(RAW_DIR, exist_ok=True)
    target = os.path.join(RAW_DIR, "wind_latest.grib2")
    client = Client(source="ecmwf")
    request = dict(
        stream="oper",
        type="fc",
        step=hres_steps(max_hours),
        param=["10u", "10v"],
        target=target,
    )
    if date is not None:
        request["date"] = date
    result = client.retrieve(**request)
    return target, result.datetime


def fetch_temp(max_hours: int = 168, date=None) -> tuple[str, object]:
    """Busca separada de temperatura (2m e skin) -- em chamada propria para
    reduzir o tamanho de cada download multipart e evitar quedas de conexao."""
    os.makedirs(RAW_DIR, exist_ok=True)
    target = os.path.join(RAW_DIR, "temp_latest.grib2")
    client = Client(source="ecmwf")
    request = dict(
        stream="oper",
        type="fc",
        step=hres_steps(max_hours),
        param=["2t", "skt"],
        target=target,
    )
    if date is not None:
        request["date"] = date
    result = client.retrieve(**request)
    return target, result.datetime
