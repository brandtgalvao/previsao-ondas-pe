"""Monta o forecast.json consumido pelo site a partir do ECMWF Open Data."""
import argparse
import glob
import json
import os
import sys
import warnings
from datetime import datetime, timezone

import numpy as np
import xarray as xr

warnings.filterwarnings("ignore", category=FutureWarning, module="cfgrib")

sys.path.insert(0, os.path.dirname(__file__))
from config import GRID_POINTS, PLACES, THESIS_POINTS, TIDE_STATION, TIDE_STATIONS_INFO  # noqa: E402
from fetch_ecmwf import fetch_wave, fetch_wind, fetch_temp  # noqa: E402
from compute import wind_speed_dir, wave_power_kw_m, wave_energy_j_m2, haversine_km  # noqa: E402
from tide import TideTable, ensure_cache  # noqa: E402
from alerts import run_alerts  # noqa: E402

TIDE_SOURCE_DIR = os.path.join(os.path.dirname(__file__), "tide_source")
TIDE_DATA_DIR = os.path.join(os.path.dirname(__file__), "tide_data")
TIDE_STATIONS = ["recife", "suape"]


def load_tide_tables():
    """Carrega e mescla TODOS os anos disponiveis (cache JSON) por estacao,
    sem depender de um ano fixo. Se houver um PDF novo em tide_source/ sem
    cache correspondente, gera o cache primeiro (requer pdfplumber local;
    no pipeline automatizado so os caches ja prontos sao usados)."""
    tables = {}
    for station in TIDE_STATIONS:
        for pdf_path in glob.glob(os.path.join(TIDE_SOURCE_DIR, f"{station}_*.pdf")):
            year = int(os.path.basename(pdf_path).split("_")[1].split(".")[0])
            cache_name = f"{station}_{year}.json"
            ensure_cache(pdf_path, year, cache_name)

        raw_all = []
        for cache_path in sorted(glob.glob(os.path.join(TIDE_DATA_DIR, f"{station}_*.json"))):
            with open(cache_path, "r", encoding="utf-8") as f:
                raw_all.extend(json.load(f))

        if not raw_all:
            print(f"Aviso: nenhuma tabua de mare disponivel para '{station}'; mare ficara indisponivel nesses pontos.")
            continue
        tables[station] = TideTable(raw=raw_all)
    return tables


OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "site", "data", "forecast.json")


def open_merged(path: str) -> xr.Dataset:
    """Abre um GRIB2 que pode conter mais de um 'hypercube' e junta tudo."""
    datasets = cfgrib_open_datasets(path)
    if len(datasets) == 1:
        return datasets[0]
    return xr.merge(datasets, compat="override", join="outer")


def cfgrib_open_datasets(path: str):
    import cfgrib
    backend_datasets = cfgrib.open_datasets(path)
    return [xr.Dataset(ds.data_vars, coords=ds.coords, attrs=ds.attrs) for ds in backend_datasets]


def extract_point_series(ds: xr.Dataset, lat: float, lon: float) -> xr.Dataset:
    point = ds.sel(latitude=lat, longitude=lon, method="nearest")
    if "step" not in point.dims:
        point = point.expand_dims("step")
    return point


def build(max_hours: int):
    print(f"Buscando previsao de onda (ate {max_hours}h)...")
    wave_path, wave_run = fetch_wave(max_hours)
    print(f"Rodada de onda: {wave_run}")

    print(f"Buscando previsao de vento (ate {max_hours}h)...")
    wind_path, wind_run = fetch_wind(max_hours, date=wave_run)
    print(f"Rodada de vento: {wind_run}")

    print(f"Buscando previsao de temperatura (ate {max_hours}h)...")
    temp_path, temp_run = fetch_temp(max_hours, date=wave_run)
    print(f"Rodada de temperatura: {temp_run}")

    if wind_run != wave_run or temp_run != wave_run:
        raise RuntimeError(
            f"Rodadas divergentes entre onda/vento/temperatura "
            f"(onda={wave_run}, vento={wind_run}, temperatura={temp_run}). "
            f"Abortando publicacao para nao misturar rodadas diferentes."
        )

    wave_ds = open_merged(wave_path)
    wind_ds = open_merged(wind_path)
    temp_ds = open_merged(temp_path)
    tide_tables = load_tide_tables()

    points_out = {}
    for point_id, coords in GRID_POINTS.items():
        lat, lon = coords["lat"], coords["lon"]
        wpt = extract_point_series(wave_ds, lat, lon)
        apt = extract_point_series(wind_ds, lat, lon)
        tpt = extract_point_series(temp_ds, lat, lon)
        tide_table = tide_tables.get(TIDE_STATION.get(point_id))

        steps_h = (wpt["step"].values / np.timedelta64(1, "h")).astype(int)
        valid_times = wpt["valid_time"].values

        forecast = []
        for i in range(len(steps_h)):
            hs = float(wpt["swh"].values[i])
            mwd = float(wpt["mwd"].values[i])
            mwp = float(wpt["mwp"].values[i])
            pp1d = float(wpt["pp1d"].values[i])
            mp2 = float(wpt["mp2"].values[i])
            u = float(apt["u10"].values[i]) if "u10" in apt else float(apt["10u"].values[i])
            v = float(apt["v10"].values[i]) if "v10" in apt else float(apt["10v"].values[i])
            air_temp_k = float(tpt["t2m"].values[i]) if "t2m" in tpt else float(tpt["2t"].values[i])
            water_temp_k = float(tpt["skt"].values[i])

            wind_speed, wind_dir = wind_speed_dir(u, v)
            power = wave_power_kw_m(hs, mwp)
            energy = wave_energy_j_m2(hs)

            vt = valid_times[i]
            vt_iso = np.datetime_as_string(vt, unit="m") + "Z"

            forecast.append({
                "step_h": int(steps_h[i]),
                "valid_time": vt_iso,
                "hs_m": round(hs, 2),
                "dir_deg": round(mwd, 0),
                "tm_s": round(mwp, 1),
                "tp_s": round(pp1d, 1),
                "tm02_s": round(mp2, 1),
                "wind_speed_ms": round(wind_speed, 1),
                "wind_dir_deg": round(wind_dir, 0),
                "power_kw_m": round(power, 1),
                "energy_j_m2": round(energy, 0),
                "air_temp_c": round(air_temp_k - 273.15, 1),
                "water_temp_c": round(water_temp_k - 273.15, 1),
            })

        tide_extrema = []
        if tide_table is not None and len(valid_times) > 0:
            start_utc = valid_times[0].astype("datetime64[s]").astype(datetime).replace(tzinfo=timezone.utc)
            end_utc = valid_times[-1].astype("datetime64[s]").astype(datetime).replace(tzinfo=timezone.utc)
            tide_extrema = tide_table.extrema_local_between(start_utc, end_utc)

        station_id = TIDE_STATION.get(point_id)
        points_out[point_id] = {
            "grid_lat": lat,
            "grid_lon": lon,
            "forecast": forecast,
            "tide_extrema": tide_extrema,
            "tide_station": TIDE_STATIONS_INFO.get(station_id),
        }

    places_out = {}
    for place_id, place in PLACES.items():
        gp = GRID_POINTS[place["grid_point"]]
        dist = haversine_km(place["lat"], place["lon"], gp["lat"], gp["lon"])
        places_out[place_id] = {**place, "grid_distance_km": round(dist, 1)}

    model_run = str(wave_run)
    output = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "model_run": model_run,
        "model_run_wave": model_run,
        "model_run_wind": model_run,
        "source": "ECMWF Open Data (HRES, IFS/WAM) - CC BY 4.0",
        "grid_points": points_out,
        "places": places_out,
    }

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nOK: {OUT_PATH}")
    print(f"Pontos de grade: {len(points_out)} | Passos por ponto: {len(forecast)}")

    print("\nVerificando alertas de ondas (Grande/Extrema)...")
    run_alerts(places_out, points_out, model_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-hours", type=int, default=168)
    parser.add_argument("--quick", action="store_true", help="teste rapido (24h)")
    args = parser.parse_args()
    build(24 if args.quick else args.max_hours)
