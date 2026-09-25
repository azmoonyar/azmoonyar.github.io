"""Export one source PDF page to a temporary single-page PDF for visual review.

It only copies the page; it does not extract text or run OCR.
"""
from pathlib import Path
import sys
from pypdf import PdfReader, PdfWriter


if len(sys.argv) not in (4, 5):
    raise SystemExit("usage: export_pdf_page.py INPUT.pdf START_PAGE OUTPUT [END_PAGE]")

source, start_page, output = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
end_page = int(sys.argv[4]) if len(sys.argv) == 5 else start_page
reader = PdfReader(str(source))

for page_number in range(start_page, end_page + 1):
    writer = PdfWriter()
    writer.add_page(reader.pages[page_number - 1])
    page_output = output / f"page-{page_number:02d}.pdf" if start_page != end_page else output
    page_output.parent.mkdir(parents=True, exist_ok=True)
    with page_output.open("wb") as stream:
        writer.write(stream)
