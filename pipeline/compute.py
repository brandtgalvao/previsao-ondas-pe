"""Variaveis derivadas: vento (modulo/direcao) e energia/potencia das ondas."""
import math


def wind_speed_dir(u: float, v: float) -> tuple[float, float]:
    """u,v em m/s -> (velocidade em m/s, direcao de onde vem o vento, graus)."""
    speed = math.hypot(u, v)
    # Direcao meteorologica: de onde o vento sopra (oposto ao vetor u,v)
    direction = (math.degrees(math.atan2(-u, -v))) % 360
    return speed, direction


RHO_SEAWATER = 1025.0  # kg/m3
G = 9.81  # m/s2


def wave_energy_kj_m2(hs: float) -> float:
    """Densidade de energia da onda (kJ/m^2), aguas profundas, teoria linear.

    E = (1/16) * rho * g * Hs^2 (J/m^2). Nao depende do periodo -- e uma
    grandeza "por area de mar", diferente da potencia (que e um fluxo,
    por metro de crista de onda).
    """
    if hs is None or math.isnan(hs):
        return float("nan")
    e_j_m2 = (RHO_SEAWATER * G / 16) * (hs ** 2)
    return e_j_m2 / 1000.0


def wave_power_kw_m(hs: float, tp: float, alpha: float = 0.9) -> float:
    """Potencia (fluxo de energia) da onda em aguas profundas (kW/m).

    P = 0.49 * Hs^2 * Te, com Te (periodo de energia) aproximado por
    alpha * Tp (Tp = periodo de pico), assumindo espectro JONSWAP
    (alpha ~ 0.9), conforme IEC TS 62600-101. Equivale a P = E * Cg,
    com Cg = g*Te/(4*pi) a velocidade de grupo em aguas profundas.
    """
    if hs is None or tp is None or math.isnan(hs) or math.isnan(tp):
        return float("nan")
    te = alpha * tp
    return 0.49 * (hs ** 2) * te
