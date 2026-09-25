"""Build an incremental, OCR-free manifest for the supplied question PDFs.

This script deliberately only inspects PDF metadata, embedded image counts, and
the native PDF text layer. It performs no OCR and does not infer question text.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[2]
PDF_DIR = ROOT / "pdf's"
OUT_DIR = ROOT / "data"
MAIN_BOOK = "main book.pdf"


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    documents = []
    total_pages = 0
    for pdf_path in sorted(PDF_DIR.glob("*.pdf"), key=lambda path: path.name.casefold()):
        is_reference = pdf_path.name == MAIN_BOOK
        # The reference book is intentionally catalogued but never traversed in
        # this phase. It is not a question source and must not be processed.
        if is_reference:
            documents.append(
                {
                    "fileName": pdf_path.name,
                    "relativePath": str(pdf_path.relative_to(ROOT)),
                    "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
                    "pageCount": 0,
                    "isReferenceBook": True,
                    "pages": [],
                }
            )
            continue
        reader = PdfReader(str(pdf_path))
        page_entries = []
        for page_number, page in enumerate(reader.pages, start=1):
            try:
                native_text = page.extract_text() or ""
            except Exception as error:  # Keep a reviewable record instead of hiding it.
                native_text = ""
                text_error = str(error)
            else:
                text_error = None
            text_chars = len("".join(native_text.split()))
            page_entries.append(
                {
                    "pageNumber": page_number,
                    "nativeTextCharacters": text_chars,
                    "hasUsableTextLayer": text_chars >= 40,
                    # Image extraction is deferred until a direct visual review
                    # can associate a crop with a specific question.
                    "embeddedImageCount": None,
                    "requiresVisionReview": text_chars < 40,
                    "status": "pending",
                    "textExtractionError": text_error,
                }
            )
        if not is_reference:
            total_pages += len(page_entries)
        documents.append(
            {
                "fileName": pdf_path.name,
                "relativePath": str(pdf_path.relative_to(ROOT)),
                "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
                "pageCount": len(page_entries),
                "isReferenceBook": is_reference,
                "pages": page_entries,
            }
        )

    manifest = {
        "schemaVersion": 1,
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "policy": {
            "mainBookExcludedFromQuestionExtraction": True,
            "localOcrUsed": False,
            "nativeTextLayerOnly": True,
        },
        "documents": documents,
        "summary": {
            "sampleQuestionPdfCount": sum(not item["isReferenceBook"] for item in documents),
            "sampleQuestionPageCount": total_pages,
            "pagesWithUsableNativeText": sum(
                page["hasUsableTextLayer"]
                for document in documents
                if not document["isReferenceBook"]
                for page in document["pages"]
            ),
            "pagesRequiringVisionReview": sum(
                page["requiresVisionReview"]
                for document in documents
                if not document["isReferenceBook"]
                for page in document["pages"]
            ),
        },
    }
    (OUT_DIR / "pdf-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "extraction-progress.json").write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "updatedAt": manifest["createdAt"],
                "status": "in_progress",
                "processedDocuments": [],
                "remainingDocuments": [item["fileName"] for item in documents if not item["isReferenceBook"]],
                "counters": {
                    "sampleQuestionPdfCount": manifest["summary"]["sampleQuestionPdfCount"],
                    "pagesProcessed": 0,
                    "pagesRemaining": total_pages,
                    "rawQuestions": 0,
                    "uniqueQuestions": 0,
                    "duplicates": 0,
                    "imageBasedQuestions": 0,
                    "unresolvedAnswers": 0,
                },
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
