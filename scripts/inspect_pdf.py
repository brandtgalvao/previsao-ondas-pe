import pdfplumber

with pdfplumber.open(r"C:\PREVISAO_ONDAS_PE\24 - PORTO DO RECIFE - 82 - 84.pdf") as pdf:
    page = pdf.pages[0]
    print("page size:", page.width, page.height)
    words = page.extract_words()
    for w in words[:80]:
        print(round(w["x0"],1), round(w["top"],1), w["text"])
