import pdfplumber

with pdfplumber.open(r"C:\PREVISAO_ONDAS_PE\pipeline\tide_source\suape_2026.pdf") as pdf:
    page = pdf.pages[2]
    for tol in [3, 2, 1.5, 1, 0.5]:
        words = page.extract_words(x_tolerance=tol)
        merged = [w["text"] for w in words if any(c.isalpha() for c in w["text"]) and any(c.isdigit() for c in w["text"])]
        print(f"x_tolerance={tol}: {len(merged)} tokens alfanumericos suspeitos -> {merged[:10]}")
