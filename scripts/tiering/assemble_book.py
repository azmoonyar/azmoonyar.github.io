#!/usr/bin/env python3
"""Assemble the visual page transcriptions of main book.pdf into project data files.

Inputs : per-page JSON transcriptions produced by direct visual review of rendered
         pages (no OCR), e.g. <scratch>/book/transcripts/page-020.json
Outputs: data/book-pages.json      one record per printed page (verbatim transcription)
         data/book-structure.json  chapters, page mapping and section index

usage: assemble_book.py TRANSCRIPT_DIR
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PDF_PAGE_COUNT = 222
FIRST_BOOK_PDF_PAGE = 3  # PDF pages 1-2 are cover/advertisement without a printed number

CHAPTERS = [
    {"id": 1, "title": "قوانین و مقررات راهنمایی و رانندگی", "startBookPage": 2, "endBookPage": 76},
    {"id": 2, "title": "رانندگی ایمن", "startBookPage": 77, "endBookPage": 113},
    {"id": 3, "title": "آشنایی با سیستمهای فنی خودرو و سرویس و نگهداری", "startBookPage": 114, "endBookPage": 156},
    {"id": 4, "title": "فرهنگ رانندگی", "startBookPage": 157, "endBookPage": 188},
    {"id": 5, "title": "امداد و نجات", "startBookPage": 189, "endBookPage": 201},
    {"id": 6, "title": "آلودگی های ترافیک", "startBookPage": 202, "endBookPage": 219},
]
FRONT_BACK = [
    {"id": 0, "title": "فهرست مطالب", "startBookPage": 1, "endBookPage": 1},
    {"id": 7, "title": "مراجع", "startBookPage": 220, "endBookPage": 220},
]
PERSIAN_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def chapter_for(book_page):
    for chapter in CHAPTERS + FRONT_BACK:
        if chapter["startBookPage"] <= book_page <= chapter["endBookPage"]:
            return chapter["id"]
    return None


def main(transcript_dir: Path):
    pages, problems = [], []
    for pdf_page in range(FIRST_BOOK_PDF_PAGE, PDF_PAGE_COUNT + 1):
        path = transcript_dir / f"page-{pdf_page:03d}.json"
        if not path.exists():
            problems.append(f"missing transcription for PDF page {pdf_page}")
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        book_page = pdf_page - 2
        printed = record.get("printedPageNumber")
        printed_value = int(str(printed).translate(PERSIAN_DIGITS)) if printed and str(printed).translate(PERSIAN_DIGITS).isdigit() else None
        if printed_value is not None and printed_value != book_page:
            problems.append(f"PDF page {pdf_page}: printed number {printed} != expected {book_page}")
        if record.get("pdfPage") != pdf_page:
            problems.append(f"PDF page {pdf_page}: record says pdfPage={record.get('pdfPage')}")
        pages.append({
            "bookPage": book_page,
            "bookPdfPage": pdf_page,
            "printedPageNumber": printed,
            "printedNumberMatches": printed_value == book_page if printed_value is not None else None,
            "chapterId": chapter_for(book_page),
            "headings": [h.strip() for h in record.get("headings") or [] if h and h.strip()],
            "text": (record.get("text") or "").strip(),
            "signs": [s for s in record.get("signs") or [] if (s.get("caption") or "").strip()],
            "figures": record.get("figures") or [],
            "legibilityIssues": record.get("legibilityIssues"),
        })

    # Section index: a section starts at every heading and runs until the next heading.
    # When the next heading opens its page, the previous section ends on the page before.
    starts = []
    for page in pages:
        for position, heading in enumerate(page["headings"]):
            body = re.sub(r"^(\s*(-|\[کادر\])\s*)+", "", page["text"])
            opens_page = position == 0 and (not body or body.startswith(heading[:12]))
            starts.append({"title": heading, "chapterId": page["chapterId"], "startBookPage": page["bookPage"], "opensPage": opens_page})
    sections = []
    for index, start in enumerate(starts):
        following = starts[index + 1] if index + 1 < len(starts) else None
        if following is None:
            end = pages[-1]["bookPage"]
        elif following["opensPage"]:
            end = max(start["startBookPage"], following["startBookPage"] - 1)
        else:
            end = following["startBookPage"]
        previous = sections[-1] if sections else None
        if previous and previous["title"] == start["title"] and previous["endBookPage"] + 1 >= start["startBookPage"]:
            previous["endBookPage"] = max(previous["endBookPage"], end)  # same heading repeated on consecutive pages
            continue
        sections.append({"title": start["title"], "chapterId": start["chapterId"], "startBookPage": start["startBookPage"], "endBookPage": end})
    for index, section in enumerate(sections, 1):
        section["id"] = f"s{index:03d}"
        section["startPdfPage"] = section["startBookPage"] + 2
        section["endPdfPage"] = section["endBookPage"] + 2

    chapters = [dict(chapter, startPdfPage=chapter["startBookPage"] + 2, endPdfPage=chapter["endBookPage"] + 2,
                     sectionIds=[s["id"] for s in sections if s["chapterId"] == chapter["id"]]) for chapter in CHAPTERS]
    structure = {
        "schemaVersion": 1,
        "source": {"fileName": "main book.pdf", "relativePath": "pdf's/main book.pdf", "pdfPageCount": PDF_PAGE_COUNT,
                   "title": "کتاب آموزشی هنرجویان پایه سوم"},
        "pageNumbering": {
            "rule": "bookPage = bookPdfPage - 2",
            "firstNumberedPdfPage": FIRST_BOOK_PDF_PAGE,
            "unnumberedPdfPages": [{"pdfPage": 1, "content": "جلد"}, {"pdfPage": 2, "content": "صفحهٔ تبلیغاتی سایت"}],
            "verifiedPages": sum(1 for p in pages if p["printedNumberMatches"]),
            "mismatchedPages": [p["bookPdfPage"] for p in pages if p["printedNumberMatches"] is False],
            "method": "Printed header numbers were read visually on every rendered page; the table of contents on PDF page 3 lists the chapter start pages.",
        },
        "tableOfContents": [{"title": "فهرست مطالب", "bookPage": 1}] + [{"title": f"فصل {c['id']}: {c['title']}", "bookPage": c["startBookPage"]} for c in CHAPTERS] + [{"title": "مراجع", "bookPage": 220}],
        "chapters": chapters,
        "frontAndBackMatter": [dict(item, startPdfPage=item["startBookPage"] + 2, endPdfPage=item["endBookPage"] + 2) for item in FRONT_BACK],
        "sections": sections,
        "transcription": {
            "method": "Rendered with PDFKit (scripts/render_pdf_pages.swift) and read visually by the model; the PDF text layer holds only dots and URLs. No local OCR.",
            "pagesTranscribed": len(pages),
            "pagesWithLegibilityNotes": [p["bookPage"] for p in pages if p["legibilityIssues"]],
            "problems": problems,
        },
    }
    (ROOT / "data" / "book-pages.json").write_text(json.dumps({"schemaVersion": 1, "pages": pages}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (ROOT / "data" / "book-structure.json").write_text(json.dumps(structure, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"pages={len(pages)} sections={len(sections)} problems={len(problems)}")
    for problem in problems:
        print("  -", problem)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
