"""Configuracao dos pontos de previsao para a costa de Pernambuco.

Cada `grid_points` e um ponto de grade do ECMWF Open Data (0.25 graus) ja
verificado como ponto de mar valido (ver scripts/check_all_points.py).
Varias praias/municipios (`places`) apontam para o mesmo grid point quando
caem na mesma celula de 0.25 grau -- isso e esperado nessa resolucao.
"""

GRID_POINTS = {
    "gp_goiana": {"lat": -7.50, "lon": -34.75},
    "gp_itamaraca": {"lat": -7.75, "lon": -34.75},
    "gp_recife_norte": {"lat": -8.00, "lon": -34.75},
    "gp_jaboatao_cabo": {"lat": -8.25, "lon": -34.75},
    "gp_b2_ipojuca_suape": {"lat": -8.25, "lon": -34.50},  # boia B2 da tese
    "gp_sirinhaem": {"lat": -8.50, "lon": -34.75},
    "gp_tamandare_barreiros": {"lat": -8.75, "lon": -35.00},
    "gp_sao_jose": {"lat": -9.00, "lon": -35.00},
}

# Nome de exibicao (praia/municipio) -> grid point que o representa.
# lat/lon aqui sao a posicao real da cidade/praia (para o mapa), nao a
# celula de grade do modelo (essa fica em GRID_POINTS).
PLACES = {
    "goiana": {"label": "Goiana", "grid_point": "gp_goiana", "lat": -7.55, "lon": -34.83},
    "itamaraca": {"label": "Ilha de Itamaracá", "grid_point": "gp_itamaraca", "lat": -7.75, "lon": -34.82},
    "paulista": {"label": "Paulista", "grid_point": "gp_recife_norte", "lat": -7.91, "lon": -34.84},
    "olinda": {"label": "Olinda", "grid_point": "gp_recife_norte", "lat": -7.99, "lon": -34.84},
    "recife_boa_viagem": {"label": "Recife", "grid_point": "gp_recife_norte", "lat": -8.12, "lon": -34.87},
    "jaboatao": {"label": "Jaboatão dos Guararapes", "grid_point": "gp_jaboatao_cabo", "lat": -8.19, "lon": -34.92},
    "cabo_santo_agostinho": {"label": "Cabo de Santo Agostinho", "grid_point": "gp_jaboatao_cabo", "lat": -8.29, "lon": -34.95},
    "ipojuca_suape": {"label": "Ipojuca", "grid_point": "gp_b2_ipojuca_suape", "lat": -8.395, "lon": -34.9367},
    "sirinhaem": {"label": "Sirinhaém", "grid_point": "gp_sirinhaem", "lat": -8.59, "lon": -35.05},
    "tamandare": {"label": "Tamandaré", "grid_point": "gp_tamandare_barreiros", "lat": -8.76, "lon": -35.10},
    "barreiros": {"label": "Barreiros", "grid_point": "gp_tamandare_barreiros", "lat": -8.82, "lon": -35.13},
    "sao_jose_coroa_grande": {"label": "São José da Coroa Grande", "grid_point": "gp_sao_jose", "lat": -8.897, "lon": -35.15},
}

# Pontos cientificos da tese, para referencia/citacao no site (nao usados
# diretamente na extracao -- B1/B3/B4 ficam fora d'agua na grade do ECMWF,
# ver metodologia; B2 e o gp_b2_ipojuca_suape acima)
THESIS_POINTS = {
    "B1_B3_B4": {"lat": -8.395, "lon": -34.9367, "desc": "Setor costeiro (nearshore), fora da resolucao do ECMWF Open Data"},
    "B2": {"lat": -8.1483, "lon": -34.56, "desc": "Offshore, usado como gp_b2_ipojuca_suape"},
}

WAVE_PARAMS = ["swh", "mwd", "mwp", "pp1d", "mp2"]
WIND_PARAMS = ["10u", "10v"]

# Estacao de mare (DHN) de referencia para cada ponto de grade.
# Recife (08 03.4S) cobre o litoral norte/central; Suape (08 23.6S) cobre
# do Cabo de Santo Agostinho para o sul, por ser geograficamente mais perto.
TIDE_STATION = {
    "gp_goiana": "recife",
    "gp_itamaraca": "recife",
    "gp_recife_norte": "recife",
    "gp_jaboatao_cabo": "suape",
    "gp_b2_ipojuca_suape": "suape",
    "gp_sirinhaem": "suape",
    "gp_tamandare_barreiros": "suape",
    "gp_sao_jose": "suape",
}
