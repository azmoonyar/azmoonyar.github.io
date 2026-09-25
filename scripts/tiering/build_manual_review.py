#!/usr/bin/env python3
"""Collect everything that still needs a human decision into data/manual-review.json.

Nothing here is changed automatically: answer keys and question wording stay exactly as
extracted. Sources: the per-question book review (data/book-reference-review), the validated
references (data/book-references.json) and the documented image corrections.

usage: build_manual_review.py BANK.json
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from removals import removed_question_ids  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

# Content problems in the extracted text itself (typos / garbled stems / editor remarks),
# confirmed by the review notes. Listed explicitly so the category is not keyword-guessed.
SOURCE_TEXT_ISSUES = {
    "q-tablo-p098-n236": "option d contains an editor remark «دلیل پاسخ صحیح : گزینه 4 عوض شود»",
    "q-600-e10-p045-n29": "question stem is garbled (the options quote the rule on accidents causing injury or death)",
    "q-ayin1-e05-n11": "stem «اشکال و سطح معابر…» looks garbled; twin questions read «الکل و مواد مخدر…» with identical options",
    "q-ayin1-e05-n12": "stem says «چراغ ترمز», evidently «چراغ قرمز»",
    "q-e7-p015-n29": "keyed option «پیش نگه داشتن» looks like «روشن نگه داشتن»",
    "q-e11-p023-n26": "option «سیم های فنری» vs the book's «سیمهای فلزی»",
    "q-600-e9-p038-n08": "answer «فاصله اولیه» is evidently «فاصله طولی»",
    "q-600-e1-p007-n11": "key says «جسم خیلی قابل اشتعال»; the book says «جسم غیر قابل اشتعال»",
}

# The same picture appears in different sample PDFs with different answer keys.
SAME_FIGURE_DIFFERENT_KEYS = [
    ["q-600-e10-p045-n25", "q-visual-e14-p028-n13"],
    ["q-600-e15-p063-n09", "q-visual-e15-p030-n13", "q-600-e16-p067-n14"],
    ["q-ayin1-e09-n16", "q-visual-e15-p030-n08"],
]


def correct_text(question):
    return next(option["text"] for option in question["options"] if option["id"] == question["correctOptionId"])


def main(bank_path):
    bank = {q["id"]: q for q in json.loads(Path(bank_path).read_text(encoding="utf-8"))}
    references = json.loads((DATA / "book-references.json").read_text(encoding="utf-8"))["references"]
    reviews = {}
    for path in sorted((DATA / "book-reference-review").glob("result-*.json")):
        for item in json.loads(path.read_text(encoding="utf-8")):
            reviews[item["id"]] = item

    def entry(question_id, **extra):
        question, reference = bank[question_id], references[question_id]
        return {"id": question_id, "question": question["text"], "keyedAnswer": f"{question['correctOptionId']}) {correct_text(question)}",
                "sources": [f"{s['pdf']} p{s['page']} q{s.get('questionNumber')}" for s in question["sources"]],
                "bookPage": reference["bookPage"], "referenceConfidence": reference["referenceConfidence"], **extra}

    conflicts = [entry(qid, reviewNote=item["note"]) for qid, item in reviews.items()
                 if re.search(r"book_conflict", item.get("note") or "") and not item.get("revisedAfterImageCorrection")]
    low = [entry(qid, reviewNote=reviews[qid].get("note")) for qid, ref in references.items() if ref["referenceConfidence"] == "low"]
    not_found = [entry(qid, reviewNote=reviews[qid].get("note"), chapterFromTopic=ref["chapterId"]) for qid, ref in references.items() if ref["referenceConfidence"] == "not_found"]
    text_issues = [entry(qid, issue=issue) for qid, issue in SOURCE_TEXT_ISSUES.items()]
    figure_keys = [{"questions": [entry(qid) for qid in group],
                    "note": "Same figure, different keys in different sample PDFs; the book's right-of-way rules support only one order (see each reviewNote in data/book-reference-review)."}
                   for group in SAME_FIGURE_DIFFERENT_KEYS]

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "policy": "Nothing listed here was changed. Answer keys and wording stay as extracted from the sample PDFs; a human should decide each case against the source PDF and the book.",
        "counts": {"answerKeyConflictsWithBook": len(conflicts), "sameFigureDifferentKeys": len(figure_keys),
                   "sourceTextIssues": len(text_issues), "referenceNotFound": len(not_found), "lowConfidenceReferences": len(low)},
        "answerKeyConflictsWithBook": conflicts,
        "sameFigureDifferentKeys": figure_keys,
        "sourceTextIssues": text_issues,
        "referenceNotFound": not_found,
        "lowConfidenceReferences": low,
        "resolvedDuringThisPass": {
            "imageCorrections": "data/question-corrections.js (4 pictures whose option order contradicted the key, 1 missing picture added, 11 unrelated pictures removed from text-only tablo.pdf questions)",
            "textCorrections": "data/question-corrections.js (q-ayin1-e03-n06: the transcription read ۱۰۰۰ / ۲۰۰۰ متر where the source page prints ۱۰۰ / ۲۰۰ متر)",
            "assetRepairs": "data/asset-fix-report.json",
            "removedQuestions": f"data/question-removals.js ({', '.join(sorted(removed_question_ids())) or 'none'}; removed at the owner's request, with the reason)",
        },
    }
    (DATA / "manual-review.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report["counts"]))


if __name__ == "__main__":
    main(sys.argv[1])
