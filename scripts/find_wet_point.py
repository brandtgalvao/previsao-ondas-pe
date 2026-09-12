import numpy as np
import xarray as xr

ds = xr.open_dataset("test_wave.grib2", engine="cfgrib")

targets = {
    "Suape/Ipojuca (B1/B3/B4, tese)": (-8.40, -34.95),
    "Boia B2 offshore (tese)": (-8.148, -34.560),
    "Recife/Boa Viagem": (-8.12, -34.87),
    "Tamandare": (-8.76, -35.10),
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
                dist = (dlat**2 + dlon**2) ** 0.5
                if best is None or dist < best[0]:
                    best = (dist, float(pt.latitude), float(pt.longitude), val, float(pt["mwd"].values), float(pt["mwp"].values), float(pt["pp1d"].values))
    print(f"\n{name} (alvo {lat0},{lon0}):")
    if best:
        dist, glat, glon, swh, mwd, mwp, pp1d = best
        print(f"  ponto de mar mais proximo: {glat},{glon} (dist ~{dist*111:.0f} km)")
        print(f"  Hs={swh:.2f} m | dir={mwd:.0f} graus | Tm={mwp:.1f} s | Tp={pp1d:.1f} s")
    else:
        print("  nenhum ponto de mar encontrado no raio de 1 grau")
