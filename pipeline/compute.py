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


def wave_energy_j_m2(hs: float) -> float:
    """Densidade de energia da onda (J/m^2), aguas profundas, teoria linear.

    E = (1/16) * rho * g * Hs^2. Nao depende do periodo -- e uma grandeza
    "por area de mar", diferente da potencia (que e um fluxo, por metro
    de crista de onda). Convencao em Joules/m2, como o Surfguru usa.
    """
    if hs is None or math.isnan(hs):
        return float("nan")
    return (RHO_SEAWATER * G / 16) * (hs ** 2)


def wave_power_kw_m(hs: float, te: float) -> float:
    """Potencia (fluxo de energia) da onda em aguas profundas (kW/m).

    P = 0.49 * Hs^2 * Te (kW/m), com Te o periodo de energia. Usamos o
    'mwp' do ECMWF diretamente como Te (em vez de aproximar por 0,9*Tp),
    ja que e o periodo medio do proprio modelo -- mais direto e melhor
    para estados de mar mistos (vagas locais + swell) do que uma
    aproximacao generica de forma espectral JONSWAP.
    Equivale a P = E * Cg, com Cg = g*Te/(4*pi) a velocidade de grupo.
    """
    if hs is None or te is None or math.isnan(hs) or math.isnan(te):
        return float("nan")
    return 0.49 * (hs ** 2) * te


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia em linha reta (km) entre duas coordenadas geograficas."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
