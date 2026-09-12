"""Variaveis derivadas: vento (modulo/direcao) e energia/potencia das ondas."""
import math


def wind_speed_dir(u: float, v: float) -> tuple[float, float]:
    """u,v em m/s -> (velocidade em m/s, direcao de onde vem o vento, graus)."""
    speed = math.hypot(u, v)
    # Direcao meteorologica: de onde o vento sopra (oposto ao vetor u,v)
    direction = (math.degrees(math.atan2(-u, -v))) % 360
    return speed, direction


def wave_power_kw_m(hs: float, tp: float, alpha: float = 0.9) -> float:
    """Potencia de onda em aguas profundas (kW/m).

    P = 0.49 * Hs^2 * Te, com Te (periodo de energia) aproximado por
    alpha * Tp (Tp = periodo de pico), assumindo espectro JONSWAP
    (alpha ~ 0.9), conforme IEC TS 62600-101.
    """
    if hs is None or tp is None or math.isnan(hs) or math.isnan(tp):
        return float("nan")
    te = alpha * tp
    return 0.49 * (hs ** 2) * te
