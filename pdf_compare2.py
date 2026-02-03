import pdfplumber
import fitz  # PyMuPDF
import difflib
import re

PDF1_PATH = "dummy data.pdf"
PDF2_PATH = "dummy data1.pdf"

OUT1_PATH = "output_diff_1.pdf"
OUT2_PATH = "output_diff_2.pdf"


def extract_lines(pdf_path):
    pages_lines = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_lines.append(text.splitlines())
    return pages_lines


def underline_text(page, text):
    """
    Underline all occurrences of the given text on the page in RED
    """
    text_instances = page.search_for(text, quads=False)
    for inst in text_instances:
        annot = page.add_underline_annot(inst)
        annot.set_colors(stroke=(1, 0, 0))  # RED underline
        annot.set_border(width=1.5)
        annot.update()



def tokenize_words(line):
    """
    Split line into words while keeping punctuation attached
    """
    return line.split(" ")


def compare_words_and_annotate(doc1, doc2, page_num, line1, line2):
    """
    Compare two lines word-by-word and underline discrepant words
    """
    page1 = doc1[page_num]
    page2 = doc2[page_num]

    words1 = tokenize_words(line1)
    words2 = tokenize_words(line2)

    diff = difflib.ndiff(words1, words2)

    for d in diff:
        code = d[:2]
        word = d[2:]

        if not word.strip():
            continue

        # Word exists only in PDF1
        if code == "- ":
            underline_text(page1, word)

        # Word exists only in PDF2
        elif code == "+ ":
            underline_text(page2, word)


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

        line_idx1 = 0
        line_idx2 = 0

        for d in diff:
            code = d[:2]
            text = d[2:]

            if code == "  ":
                line_idx1 += 1
                line_idx2 += 1

            elif code == "- ":
                # Line exists only in PDF1 → underline entire line
                underline_text(doc1[page_num], text)
                line_idx1 += 1

            elif code == "+ ":
                # Line exists only in PDF2 → underline entire line
                underline_text(doc2[page_num], text)
                line_idx2 += 1

            elif code == "? ":
                # Hint line from ndiff → ignore
                pass

            else:
                # Line modified → word-level comparison
                if line_idx1 < len(lines1) and line_idx2 < len(lines2):
                    compare_words_and_annotate(
                        doc1,
                        doc2,
                        page_num,
                        lines1[line_idx1],
                        lines2[line_idx2],
                    )
                    line_idx1 += 1
                    line_idx2 += 1

    doc1.save(OUT1_PATH)
    doc2.save(OUT2_PATH)


if __name__ == "__main__":
    pdf1_lines = extract_lines(PDF1_PATH)
    pdf2_lines = extract_lines(PDF2_PATH)

    compare_and_annotate(pdf1_lines, pdf2_lines)

    print("✅ Line + word-level comparison complete. Annotated PDFs generated.")
