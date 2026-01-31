import pdfplumber
import fitz  # PyMuPDF
import difflib

PDF1_PATH = "SSEN_CV.pdf"
PDF2_PATH = "SSEN_CV1.pdf"

OUT1_PATH = "output_diff_1.pdf"
OUT2_PATH = "output_diff_2.pdf"


def extract_lines(pdf_path):
    pages_lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_lines.append(text.splitlines())
    return pages_lines


def underline_line(doc, page_number, line_text):
    page = doc[page_number]
    text_instances = page.search_for(line_text)

    for inst in text_instances:
        annot = page.add_underline_annot(inst)
        annot.update()


def compare_and_annotate(pdf1_lines, pdf2_lines):
    doc1 = fitz.open(PDF1_PATH)
    doc2 = fitz.open(PDF2_PATH)

    max_pages = max(len(pdf1_lines), len(pdf2_lines))

    for page_num in range(max_pages):

        # Handle extra pages
        if page_num >= len(pdf1_lines):
            page = doc2[page_num]
            page.add_rect_annot(page.rect).update()
            continue

        if page_num >= len(pdf2_lines):
            page = doc1[page_num]
            page.add_rect_annot(page.rect).update()
            continue

        lines1 = pdf1_lines[page_num]
        lines2 = pdf2_lines[page_num]

        diff = difflib.ndiff(lines1, lines2)

        for d in diff:
            code = d[:2]
            text = d[2:]

            if not text.strip():
                continue

            # Line exists only in PDF1
            if code == "- ":
                underline_line(doc1, page_num, text)

            # Line exists only in PDF2
            elif code == "+ ":
                underline_line(doc2, page_num, text)

    doc1.save(OUT1_PATH)
    doc2.save(OUT2_PATH)


if __name__ == "__main__":
    pdf1_lines = extract_lines(PDF1_PATH)
    pdf2_lines = extract_lines(PDF2_PATH)

    compare_and_annotate(pdf1_lines, pdf2_lines)

    print("✅ Comparison complete. Annotated PDFs generated.")
