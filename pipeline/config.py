"""Configuracao dos pontos de previsao para a costa de Pernambuco.

Cada municipio agora tem DOIS pontos de grade do ECMWF Open Data (0.25 graus),
ambos ja verificados como pontos de mar validos: um "costeiro" (o mais perto
da costa disponivel na grade) e um "oceanico" (a proxima faixa de grade mar
adentro, mesma longitude usada pela referencia historica P2/ERA5 da tese em
boa parte do litoral). Varios municipios apontam para o mesmo par de pontos
quando caem na mesma celula de 0.25 grau -- isso e esperado nessa resolucao
(ver metodologia: municipios vizinhos mais proximos entre si do que ~14km,
metade da celula de 28km, inevitavelmente competem pelo mesmo vizinho).

Levantamento completo da grade (todas as faixas costeira/intermediaria/
offshore disponiveis) em scripts/map_grid_bands.py.
"""

GRID_POINTS = {
    "gp_costeira_01": {"lat": -7.50, "lon": -34.75},
    "gp_costeira_02": {"lat": -7.75, "lon": -34.75},
    "gp_costeira_03": {"lat": -8.00, "lon": -34.75},
    "gp_costeira_04": {"lat": -8.25, "lon": -34.75},
    "gp_costeira_05": {"lat": -8.50, "lon": -34.75},
    "gp_costeira_06": {"lat": -8.75, "lon": -35.00},
    "gp_costeira_07": {"lat": -9.00, "lon": -35.00},
    "gp_oceanica_01": {"lat": -7.50, "lon": -34.50},
    "gp_oceanica_02": {"lat": -7.75, "lon": -34.50},
    "gp_oceanica_03": {"lat": -8.00, "lon": -34.50},  # mesma longitude do P2/ERA5 da tese
    "gp_oceanica_04": {"lat": -8.25, "lon": -34.50},
    "gp_oceanica_05": {"lat": -8.50, "lon": -34.50},
    "gp_oceanica_06": {"lat": -8.75, "lon": -34.75},
    "gp_oceanica_07": {"lat": -9.00, "lon": -34.75},
}

# Nome de exibicao (praia/municipio) -> par de grid points (costeiro/oceanico)
# que o representa. lat/lon aqui sao a posicao real da cidade/praia (para o
# mapa e o calculo de distancia), nao a celula de grade do modelo (essa fica
# em GRID_POINTS).
PLACES = {
    "goiana": {"label": "Goiana", "grid_point_costeira": "gp_costeira_01", "grid_point_oceanica": "gp_oceanica_01", "lat": -7.55, "lon": -34.83},
    "itamaraca": {"label": "Ilha de Itamaracá", "grid_point_costeira": "gp_costeira_02", "grid_point_oceanica": "gp_oceanica_02", "lat": -7.75, "lon": -34.82},
    "paulista": {"label": "Paulista", "grid_point_costeira": "gp_costeira_03", "grid_point_oceanica": "gp_oceanica_03", "lat": -7.91, "lon": -34.84},
    "olinda": {"label": "Olinda", "grid_point_costeira": "gp_costeira_03", "grid_point_oceanica": "gp_oceanica_03", "lat": -7.99, "lon": -34.84},
    "recife_boa_viagem": {"label": "Recife", "grid_point_costeira": "gp_costeira_03", "grid_point_oceanica": "gp_oceanica_03", "lat": -8.12, "lon": -34.87},
    "jaboatao": {"label": "Jaboatão dos Guararapes", "grid_point_costeira": "gp_costeira_04", "grid_point_oceanica": "gp_oceanica_04", "lat": -8.19, "lon": -34.92},
    "cabo_santo_agostinho": {"label": "Cabo de Santo Agostinho", "grid_point_costeira": "gp_costeira_05", "grid_point_oceanica": "gp_oceanica_05", "lat": -8.29, "lon": -34.95},
    "ipojuca_suape": {"label": "Ipojuca", "grid_point_costeira": "gp_costeira_05", "grid_point_oceanica": "gp_oceanica_05", "lat": -8.395, "lon": -34.9367},
    "sirinhaem": {"label": "Sirinhaém", "grid_point_costeira": "gp_costeira_06", "grid_point_oceanica": "gp_oceanica_06", "lat": -8.59, "lon": -35.05},
    "tamandare": {"label": "Tamandaré", "grid_point_costeira": "gp_costeira_06", "grid_point_oceanica": "gp_oceanica_06", "lat": -8.76, "lon": -35.10},
    "barreiros": {"label": "Barreiros", "grid_point_costeira": "gp_costeira_06", "grid_point_oceanica": "gp_oceanica_06", "lat": -8.82, "lon": -35.13},
    "sao_jose_coroa_grande": {"label": "São José da Coroa Grande", "grid_point_costeira": "gp_costeira_07", "grid_point_oceanica": "gp_oceanica_07", "lat": -8.897, "lon": -35.15},
}

# Pontos cientificos da tese, para referencia/citacao no site (nao usados
# diretamente na extracao). P1/P2 sao os nos da grade regular de 0.5 grau
# usados na tese para a serie historica ERA5; B1/B2/B3/B4 sao os ondografos
# reais. gp_oceanica_03 (-8.00,-34.50) coincide com o P2.
THESIS_POINTS = {
    "P1": {"lat": -8.50, "lon": -35.00, "desc": "ERA5/costeiro, controle espacial de Hs (nao existe como ponto de mar no ECMWF Open Data operacional - mascara terra-mar diferente do ERA5)"},
    "P2": {"lat": -8.00, "lon": -34.50, "desc": "ERA5/offshore, eixo principal das analises historicas de longo prazo - mesma coordenada de gp_oceanica_03"},
    "B1_B3_B4": {"lat": -8.395, "lon": -34.9367, "desc": "Ondografo costeiro (fundeio ~17m), fora da resolucao do ECMWF Open Data"},
    "B2": {"lat": -8.1483, "lon": -34.56, "desc": "Ondografo offshore (fundeio ~200m), base da comparacao B2 x P2"},
}

WAVE_PARAMS = ["swh", "mwd", "mwp", "pp1d", "mp2"]
WIND_PARAMS = ["10u", "10v"]

# Estacao de mare (DHN) de referencia para cada ponto, costeiro e oceanico.
# A mare varia pouco entre as duas distancias (e um fenomeno de grande
# escala), entao cada ponto oceanico reaproveita a mesma
# tabua/estacao do ponto costeiro da mesma faixa de latitude - sem isso, o
# usuario que prefere acompanhar a previsao oceanica perderia a mare, que
# so faz sentido medida perto da costa/porto.
# Recife (08 03.4S) cobre o litoral norte/central; Suape (08 23.6S) cobre
# do Cabo de Santo Agostinho para o sul, por ser geograficamente mais perto.
TIDE_STATIONS_INFO = {
    "recife": {"name": "Porto de Recife", "lat": -8.06, "lon": -34.87},
    "suape": {"name": "Porto de Suape", "lat": -8.39, "lon": -34.96},
}

TIDE_STATION = {
    "gp_costeira_01": "recife",
    "gp_costeira_02": "recife",
    "gp_costeira_03": "recife",
    "gp_costeira_04": "suape",
    "gp_costeira_05": "suape",
    "gp_costeira_06": "suape",
    "gp_costeira_07": "suape",
    "gp_oceanica_01": "recife",
    "gp_oceanica_02": "recife",
    "gp_oceanica_03": "recife",
    "gp_oceanica_04": "suape",
    "gp_oceanica_05": "suape",
    "gp_oceanica_06": "suape",
    "gp_oceanica_07": "suape",
}
