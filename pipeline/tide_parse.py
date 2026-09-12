"""Parser das Tabuas de Mare (DHN) em PDF -> {mes: {dia: [(HHMM, altura_m), ...]}}.

Layout do PDF: 4 meses por pagina, cada mes com 2 sub-colunas de dias
(aprox. 1-16 e 17-31). Cada dia ocupa ate 4 linhas empilhadas de
(hora, altura); a primeira linha traz tambem o numero do dia, a segunda
a abreviacao do dia da semana. As colunas sao detectadas por clustering
das proprias coordenadas x dos tokens (mais robusto que usar o cabecalho,
que nao fica alinhado com os dados).
"""
import re
import pdfplumber

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
         "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

DAY_RE = re.compile(r"^(0[1-9]|[12]\d|3[01])$")
HORA_RE = re.compile(r"^\d{4}$")
ALT_RE = re.compile(r"^-?\d+\.\d{2}$")


def _cluster_x(values, gap=5.0):
    values = sorted(values)
    clusters = []
    for v in values:
        if clusters and v - clusters[-1][-1] <= gap:
            clusters[-1].append(v)
        else:
            clusters.append([v])
    return [sum(c) / len(c) for c in clusters]


def _cluster_rows(words, tol=2.0):
    words = sorted(words, key=lambda w: w["top"])
    rows = []
    for w in words:
        if rows and abs(w["top"] - rows[-1][0]["top"]) <= tol:
            rows[-1].append(w)
        else:
            rows.append([w])
    return rows


def _near(x, target, tol=3.0):
    return abs(x - target) <= tol


def parse_tide_pdf(path: str) -> dict:
    result = {}
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            # x_tolerance menor que o padrao (3) evita juntar "DOM" (domingo)
            # com o horario seguinte em algumas linhas (ex: "DOM1110" -> deveria
            # ser "DOM" + "1110"), bug observado no layout desta tabua.
            words = page.extract_words(x_tolerance=2)
            month_row = [w for w in words if abs(w["top"] - 90.1) < 3]
            month_names = [w["text"] for w in sorted(month_row, key=lambda w: w["x0"])]
            if len(month_names) != 4 or not all(m in MESES for m in month_names):
                continue  # pagina sem tabua (ex: capa)

            body_words = [w for w in words if w["top"] > 105 and w["top"] < page.height - 25]
            day_x = _cluster_x([w["x0"] for w in body_words if DAY_RE.match(w["text"])])
            hora_x = _cluster_x([w["x0"] for w in body_words if HORA_RE.match(w["text"])])
            alt_x = _cluster_x([w["x0"] for w in body_words if ALT_RE.match(w["text"])])
            if len(day_x) != 8 or len(hora_x) != 8 or len(alt_x) != 8:
                raise ValueError(f"Layout inesperado na pagina {page.page_number}: "
                                  f"{len(day_x)} col. dia, {len(hora_x)} col. hora, {len(alt_x)} col. alt")

            for g in range(8):
                month = MESES.index(month_names[g // 2]) + 1
                day_col_x, hora_col_x, alt_col_x = day_x[g], hora_x[g], alt_x[g]

                group_words = [
                    w for w in body_words
                    if _near(w["x0"], day_col_x) or _near(w["x0"], hora_col_x) or _near(w["x0"], alt_col_x)
                ]
                rows = _cluster_rows(group_words)

                month_data = result.setdefault(month, {})
                current_day = None
                for row in rows:
                    label = hora = alt = None
                    for w in row:
                        if _near(w["x0"], day_col_x) and DAY_RE.match(w["text"]):
                            label = int(w["text"])
                        elif _near(w["x0"], hora_col_x) and HORA_RE.match(w["text"]):
                            hora = w["text"]
                        elif _near(w["x0"], alt_col_x) and ALT_RE.match(w["text"]):
                            alt = float(w["text"])
                    if label is not None:
                        current_day = label
                    if hora is not None and alt is not None and current_day is not None:
                        month_data.setdefault(current_day, []).append((hora, alt))
    return result


if __name__ == "__main__":
    import sys
    data = parse_tide_pdf(sys.argv[1])
    total_days = sum(len(d) for d in data.values())
    for month in sorted(data):
        days = data[month]
        expected = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30, 7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}[month]
        flag = "" if len(days) == expected else "  <<< ESPERADO %d" % expected
        print(f"Mes {month:2d}: {len(days)} dias parseados{flag}")
    print("\nTotal de dias:", total_days)
    print("Dia 1, mes 1:", data.get(1, {}).get(1))
    print("Dia 13, mes 1 (3 marcas):", data.get(1, {}).get(13))
    print("Dia 12, mes 9:", data.get(9, {}).get(12))
