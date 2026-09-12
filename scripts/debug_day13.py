import pdfplumber
import re

DAY_RE = re.compile(r"^(0[1-9]|[12]\d|3[01])$")
HORA_RE = re.compile(r"^\d{4}$")
ALT_RE = re.compile(r"^-?\d+\.\d{2}$")

def cluster_x(values, gap=5.0):
    values = sorted(values)
    clusters = []
    for v in values:
        if clusters and v - clusters[-1][-1] <= gap:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return [sum(c) / len(c) for c in clusters]

with pdfplumber.open(r"C:\PREVISAO_ONDAS_PE\pipeline\tide_source\suape_2026.pdf") as pdf:
    page = pdf.pages[2]  # Setembro/Outubro/Novembro/Dezembro
    words = page.extract_words()
    month_row = [w for w in words if abs(w["top"] - 90.1) < 3]
    print("meses:", [(w["text"], round(w["x0"],1)) for w in sorted(month_row, key=lambda w: w["x0"])])

    body = [w for w in words if w["top"] > 105 and w["top"] < page.height - 25]
    day_x = cluster_x([w["x0"] for w in body if DAY_RE.match(w["text"])])
    print("day_x group0 (Setembro dias 1-16):", day_x[0])

    # todas as palavras no grupo 0 (Setembro, dias 1-16), ordenadas por top
    hora_x = cluster_x([w["x0"] for w in body if HORA_RE.match(w["text"])])
    alt_x = cluster_x([w["x0"] for w in body if ALT_RE.match(w["text"])])
    g = 0
    def near(x, t, tol=3.0):
        return abs(x - t) <= tol
    group_words = [w for w in body if near(w["x0"], day_x[g]) or near(w["x0"], hora_x[g]) or near(w["x0"], alt_x[g])]
    group_words.sort(key=lambda w: w["top"])
    day13_top = next(w["top"] for w in group_words if w["text"] == "13" and near(w["x0"], day_x[g]))
    print("top do marcador '13':", day13_top)
    for w in group_words:
        if day13_top - 15 <= w["top"] <= day13_top + 60:
            print(round(w["top"],2), round(w["x0"],1), repr(w["text"]))
