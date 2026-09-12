"""Teste de conectividade e leitura do ECMWF Open Data (ondas) para um ponto de Pernambuco."""
import os
from ecmwf.opendata import Client
import xarray as xr

if not os.path.exists("test_wave.grib2"):
    client = Client(source="ecmwf")
    result = client.retrieve(
        stream="wave",
        type="fc",
        step=24,
        param=["swh", "mwd", "mwp", "pp1d"],
        target="test_wave.grib2",
    )
    print("Rodada do modelo utilizada:", result.datetime)

ds = xr.open_dataset("test_wave.grib2", engine="cfgrib")
print(ds)

# Ponto de referência: próximo a Suape/Ipojuca (~34.95 W, 8.40 S)
# Grade do ECMWF Open Data usa longitude de -180 a 180 (oeste é negativo)
lat, lon = -8.40, -34.95
point = ds.sel(latitude=lat, longitude=lon, method="nearest")

print("\n--- Previsão em Suape/Ipojuca (ponto de grade mais próximo) ---")
print("Lat/Lon da grade:", float(point.latitude), float(point.longitude))
print("Altura significativa (swh, m):", float(point["swh"].values))
print("Direção média (mwd, graus):", float(point["mwd"].values))
print("Período médio (mwp, s):", float(point["mwp"].values))
print("Período de pico (pp1d, s):", float(point["pp1d"].values))
