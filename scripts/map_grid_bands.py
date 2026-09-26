"""
Mapeia, para cada faixa de latitude relevante da costa de PE, todos os pontos
de mar validos (nao-NaN em swh) da grade ECMWF 0.25 graus disponiveis no
arquivo de amostra test_wave.grib2, do mais proximo da costa (oeste) ao mais
offshore (leste), com distancia aproximada ate a referencia costeira
(municipio) mais proxima naquela latitude.

So leitura/analise - nao altera nada em config.py nem no site.
"""
import numpy as np
import xarray as xr

ds = xr.open_dataset("test_wave.grib2", engine="cfgrib")

# Referencias costeiras (lat/lon de PLACES em pipeline/config.py), usadas so
# para medir "quantos km da costa" cada ponto de grade fica.
COASTAL_REFS = [
    ("Goiana", -7.55, -34.83),
    ("Ilha de Itamaraca", -7.75, -34.82),
    ("Paulista", -7.91, -34.84),
    ("Olinda", -7.99, -34.84),
    ("Recife (Boa Viagem)", -8.12, -34.87),
    ("Jaboatao dos Guararapes", -8.19, -34.92),
    ("Cabo de Santo Agostinho", -8.29, -34.95),
    ("Ipojuca (Porto de Galinhas/Suape)", -8.395, -34.9367),
    ("Sirinhaem", -8.59, -35.05),
    ("Tamandare", -8.76, -35.10),
    ("Barreiros", -8.82, -35.13),
    ("Sao Jose da Coroa Grande", -8.897, -35.15),
]

def dist_km(lat0, lon0, lat1, lon1):
    dlat = lat1 - lat0
    dlon = (lon1 - lon0) * np.cos(np.radians((lat0 + lat1) / 2))
    return ((dlat ** 2 + dlon ** 2) ** 0.5) * 111.0

def nearest_coastal_ref(lat, lon):
    best = None
    for name, rlat, rlon in COASTAL_REFS:
        d = dist_km(lat, lon, rlat, rlon)
        if best is None or d < best[0]:
            best = (d, name)
    return best

# Faixa de latitude da costa de PE, do extremo norte (Goiana) ao sul (Sao Jose),
# em passos de 0.25 grau (resolucao nativa do ECMWF Open Data).
lat_min, lat_max = -9.25, -7.25
lon_min, lon_max = -35.75, -33.75

lats = np.round(np.arange(lat_min, lat_max + 0.001, 0.25), 2)
lons = np.round(np.arange(lon_min, lon_max + 0.001, 0.25), 2)

for lat in lats:
    row = []
    for lon in lons:
        try:
            pt = ds.sel(latitude=lat, longitude=lon, method="nearest", tolerance=0.01)
        except KeyError:
            continue
        actual_lat = float(pt.latitude)
        actual_lon = float(pt.longitude)
        if abs(actual_lat - lat) > 0.01 or abs(actual_lon - lon) > 0.01:
            continue  # fora da grade nativa (nearest devolveu ponto de fora do range pedido)
        val = float(pt["swh"].values)
        if not np.isnan(val):
            row.append((actual_lon, val))
    if not row:
        continue
    print(f"\n=== Latitude {lat:.2f} ===")
    for lon, swh in row:
        d, ref_name = nearest_coastal_ref(lat, lon)
        print(f"  lon={lon:7.2f}  Hs_amostra={swh:5.2f}m  dist_costa~{d:5.1f}km  (ref: {ref_name})")
