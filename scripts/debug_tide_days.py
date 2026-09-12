import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "pipeline"))
from tide_parse import parse_tide_pdf

data = parse_tide_pdf(r"C:\PREVISAO_ONDAS_PE\pipeline\tide_source\suape_2026.pdf")
for day in range(10, 18):
    print(f"Setembro dia {day}:", data.get(9, {}).get(day))
