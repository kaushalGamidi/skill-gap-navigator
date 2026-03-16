import fitz  # PyMuPDF

def scan_pdf(pdf_file):
    doc = fitz.open(pdf_file)
    text = ""

    for page in doc:
        text += page.get_text()

    return text


# run scanner
pdf_path = "Kaushal teesexpo CV 1page version.pdf"   

result = scan_pdf(pdf_path)

print(result)

# optional save
with open("output.txt", "w", encoding="utf-8") as f:
    f.write(result)