import pymupdf


def extract_text_from_pdf(pdf_file):
    pdf_bytes = pdf_file.read()

    document = pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    extracted_text = ""

    for page in document:
        extracted_text += page.get_text() + "\n"

    document.close()

    return extracted_text