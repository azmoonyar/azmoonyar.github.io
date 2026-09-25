#!/usr/bin/env python3
"""Validate the reviewed question→book links and write data/book-references.json.

Each reviewed link is checked mechanically before it is accepted:
- bookPage is an integer printed page 1-220 that exists in data/book-pages.json;
- supportingText is an exact substring of that page's transcription (after whitespace/ZWNJ
  normalisation); if not, the excerpt is dropped and confidence is capped at "low";
- chapterId agrees with the chapter range of bookPage;
- every question of the bank has exactly one entry.

usage: merge_references.py BANK.json RESULTS_DIR
"""
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from removals import removed_question_ids  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
CONFIDENCE = ("high", "medium", "low", "not_found")


def loose(text):
    text = unicodedata.normalize("NFKC", str(text or ""))
    text = text.replace("ي", "ی").replace("ى", "ی").replace("ك", "ک").replace("‌", " ").replace("‍", "")
    text = re.sub(r"\[کادر\]\s*", "", text)
    text = re.sub(r"(?:(?<=\s)|^)[-–ـ]+(?=\s)", " ", text)  # list markers, on either side
    return re.sub(r"\s+", " ", text).strip()


def page_corpus(page):
    parts = [page["text"], *page["headings"]]
    parts += [s.get("caption", "") for s in page["signs"]]
    parts += [f.get("caption") or "" for f in page["figures"]]
    return loose("\n".join(parts))


def box_corpus(page):
    return loose("\n".join(p for p in re.split(r"\n\s*\n|\n(?=- )", page["text"]) if p.strip().startswith("[کادر]")))


def main(bank_path, results_dir):
    bank = json.loads(Path(bank_path).read_text(encoding="utf-8"))
    pages = {p["bookPage"]: p for p in json.loads((DATA / "book-pages.json").read_text(encoding="utf-8"))["pages"]}
    structure = json.loads((DATA / "book-structure.json").read_text(encoding="utf-8"))
    chapter_range = {c["id"]: (c["startBookPage"], c["endBookPage"]) for c in structure["chapters"]}
    chapter_titles = {c["id"]: c["title"] for c in structure["chapters"]}
    corpus = {number: page_corpus(page) for number, page in pages.items()}
    boxes = {number: box_corpus(page) for number, page in pages.items()}

    raw = {}
    duplicates = []
    for path in sorted(Path(results_dir).glob("result-*.json")):
        for item in json.loads(path.read_text(encoding="utf-8")):
            if item["id"] in raw:
                duplicates.append(item["id"])
            raw[item["id"]] = item

    def chapter_of(page):
        return next((cid for cid, (start, end) in chapter_range.items() if start <= page <= end), None)

    references, issues = {}, Counter()
    issue_examples = {}
    for question in bank:
        item = raw.get(question["id"])
        if item is None:
            issues["missing_review"] += 1
            references[question["id"]] = {"bookPage": None, "bookPdfPage": None, "referenceConfidence": "not_found", "chapterId": None,
                                          "chapterBasis": None, "bookReference": None, "supportingText": None, "secondaryReferences": [], "note": "not reviewed"}
            continue
        confidence = item.get("confidence") if item.get("confidence") in CONFIDENCE else "low"
        page = item.get("bookPage")
        page = int(page) if isinstance(page, (int, float, str)) and str(page).isdigit() else None
        excerpt = (item.get("supportingText") or "").strip() or None
        note = item.get("note")
        if page is not None and page not in pages:
            issues["page_out_of_range"] += 1
            page, confidence = None, "not_found"
        if page is None:
            confidence, excerpt = "not_found", None
        elif confidence == "not_found":
            confidence = "low"
        in_box = False
        if page is not None and excerpt:
            normalized = loose(excerpt).rstrip(".…").strip()
            if normalized and normalized in corpus[page]:
                in_box = bool(boxes[page]) and normalized in boxes[page]
            else:
                issues["excerpt_not_verbatim"] += 1
                issue_examples.setdefault("excerpt_not_verbatim", []).append(question["id"])
                excerpt = None
                if confidence in ("high", "medium"):
                    confidence = "low"
        if page is not None and not excerpt and confidence == "high":
            confidence = "medium"
        chapter = chapter_of(page) if page is not None else item.get("chapterId")
        basis = "page" if page is not None else (item.get("chapterBasis") if item.get("chapterId") else None)
        if page is not None and item.get("chapterId") not in (None, chapter):
            issues["chapter_corrected_from_page"] += 1
        if chapter not in chapter_titles:
            chapter, basis = None, None
        secondary = []
        for extra in item.get("secondaryPages") or []:
            if isinstance(extra, int) and extra in pages and extra != page and len(secondary) < 2:
                secondary.append({"bookPage": extra, "bookPdfPage": extra + 2})
        references[question["id"]] = {
            "bookPage": page, "bookPdfPage": page + 2 if page is not None else None,
            "referenceConfidence": confidence, "chapterId": chapter, "chapterBasis": basis,
            "bookReference": (item.get("bookReference") or None) if page is not None else None,
            "supportingText": excerpt, "inBox": in_box, "secondaryReferences": secondary, "note": note,
        }

    counts = Counter(ref["referenceConfidence"] for ref in references.values())
    output = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": "Lexical candidate retrieval over the visual transcription of main book.pdf, then per-question review of the candidates and the full transcription; links were mechanically validated (page range, verbatim excerpt, chapter range). No local OCR.",
        "pageNumbering": "bookPage is the printed page number; bookPdfPage = bookPage + 2 (PDF pages 1-2 are cover/advertisement).",
        "summary": {"questions": len(bank), "confidence": dict(counts), "withPage": sum(1 for r in references.values() if r["bookPage"]),
                    "withChapter": sum(1 for r in references.values() if r["chapterId"]), "validationIssues": dict(issues),
                    "duplicateReviewEntries": len(duplicates), "unknownReviewIds": sorted(set(raw) - {q["id"] for q in bank} - removed_question_ids()),
                    "removedQuestions": sorted(set(raw) & removed_question_ids())},
        "issueExamples": {k: v[:25] for k, v in issue_examples.items()},
        "references": references,
    }
    (DATA / "book-references.json").write_text(json.dumps(output, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(output["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
