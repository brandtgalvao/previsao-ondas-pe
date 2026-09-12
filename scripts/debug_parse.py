import pdfplumber
import re

DAY_RE = re.compile(r"^([1-9]|[12]\d|3[01])$")
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


with pdfplumber.open(r"C:\PREVISAO_ONDAS_PE\24 - PORTO DO RECIFE - 82 - 84.pdf") as pdf:
    page = pdf.pages[0]
    words = page.extract_words()
    body = [w for w in words if w["top"] > 105 and w["top"] < page.height - 25]

    day_x = cluster_x([w["x0"] for w in body if DAY_RE.match(w["text"])])
    hora_x = cluster_x([w["x0"] for w in body if HORA_RE.match(w["text"])])
    alt_x = cluster_x([w["x0"] for w in body if ALT_RE.match(w["text"])])
    print("day_x", len(day_x), day_x)
    print("hora_x", len(hora_x), hora_x)
    print("alt_x", len(alt_x), alt_x)
