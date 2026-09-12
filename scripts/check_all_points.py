import numpy as np
import xarray as xr

ds = xr.open_dataset("test_wave.grib2", engine="cfgrib")

# Pontos propostos para a v1 (litoral de PE, norte -> sul)
# B1/B3/B4 e B2 = pontos cientificos da tese; demais = aproximacao de sede municipal costeira
targets = {
    "Goiana": (-7.55, -34.83),
    "Ilha de Itamaraca": (-7.75, -34.82),
    "Paulista": (-7.91, -34.84),
    "Olinda": (-7.99, -34.84),
    "Recife (Boa Viagem)": (-8.12, -34.87),
    "Jaboatao dos Guararapes": (-8.19, -34.92),
    "Cabo de Santo Agostinho": (-8.29, -34.95),
    "Ipojuca / B1-B3-B4 (tese, nearshore)": (-8.395, -34.9367),
    "Ipojuca-Suape / B2 (tese, offshore) [PONTO ESCOLHIDO]": (-8.1483, -34.56),
    "Sirinhaem": (-8.59, -35.05),
    "Tamandare": (-8.76, -35.10),
    "Barreiros": (-8.82, -35.13),
    "Sao Jose da Coroa Grande": (-8.897, -35.15),
}

lat_res = 0.25
lon_res = 0.25

for name, (lat0, lon0) in targets.items():
    best = None
    for dlat in np.arange(-1.0, 1.01, lat_res):
        for dlon in np.arange(-1.0, 1.01, lon_res):
            lat, lon = lat0 + dlat, lon0 + dlon
            pt = ds.sel(latitude=lat, longitude=lon, method="nearest")
            val = float(pt["swh"].values)
            if not np.isnan(val):
                dist_km = ((dlat**2 + (dlon * np.cos(np.radians(lat0)))**2) ** 0.5) * 111
                if best is None or dist_km < best[0]:
                    best = (dist_km, float(pt.latitude), float(pt.longitude), val)
    flag = ""
    if best and best[0] > 15:
        flag = "  <<< ATENCAO: distancia grande"
    if best:
        dist_km, glat, glon, swh = best
        print(f"{name:55s} alvo=({lat0:.3f},{lon0:.3f}) -> grade=({glat:.2f},{glon:.2f}) dist~{dist_km:.0f}km Hs={swh:.2f}m{flag}")
    else:
        print(f"{name:55s} NENHUM ponto de mar em raio de 1 grau!")
