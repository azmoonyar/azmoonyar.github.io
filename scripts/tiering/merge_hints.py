#!/usr/bin/env python3
"""Validate the reviewed study hints and write data/question-hints.js (+ data/hint-report.json).

A hint is one or two short Persian sentences shown after answering, explaining why the keyed
answer is right (grounded in the textbook page; see data/hint-review/HINT_INSTRUCTIONS.md).
Checks: exactly one hint per question, length limit, no option numbers/letters, no stray Latin
text, numbers of numeric answers present in the hint, conflict questions flagged as such (both
ways, against data/manual-review.json). The report also counts the independent second check
(data/hint-review/verification).

usage: merge_hints.py BANK.json RESULTS_DIR
"""
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from removals import removed_question_ids  # noqa: E402
from textnorm import answer_kind, norm  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
MAX_LENGTH = 190
BASES = {"book", "answer", "book_conflict"}
ALLOWED_LATIN = {"ABS", "LED", "WC", "PR"}  # letters printed on the signs themselves
OPTION_REFERENCE = re.compile(r"گزینه(ٔ|ی)?\s*(\d|[۰-۹]|الف|ب\b|ج\b|د\b)")


def numbers(text):
    return set(re.findall(r"\d+(?:[.,/]\d+)?", norm(text)))


def main(bank_path, results_dir):
    bank = json.loads(Path(bank_path).read_text(encoding="utf-8"))
    manual = json.loads((DATA / "manual-review.json").read_text(encoding="utf-8"))
    conflicts = {entry["id"] for entry in manual["answerKeyConflictsWithBook"]}
    listed = conflicts | {entry["id"] for entry in manual["sourceTextIssues"]} | {
        entry["id"] for group in manual["sameFigureDifferentKeys"] for entry in group["questions"]}
    raw, duplicates = {}, []
    for path in sorted(Path(results_dir).glob("hints-*.json")):
        for item in json.loads(path.read_text(encoding="utf-8")):
            if item["id"] in raw:
                duplicates.append(item["id"])
            raw[item["id"]] = item

    hints, problems, warnings = {}, [], []
    for question in bank:
        item = raw.get(question["id"])
        if not item or not (item.get("hint") or "").strip():
            problems.append({"id": question["id"], "problem": "missing hint"})
            continue
        hint = re.sub(r"\s+", " ", item["hint"]).strip()
        answer = next(o["text"] for o in question["options"] if o["id"] == question["correctOptionId"])
        if len(hint) > MAX_LENGTH:
            problems.append({"id": question["id"], "problem": f"too long ({len(hint)})", "hint": hint})
        if OPTION_REFERENCE.search(hint):
            problems.append({"id": question["id"], "problem": "refers to an option number/letter", "hint": hint})
        latin = {word for word in re.findall(r"[A-Za-z]{2,}", hint) if word.upper() not in ALLOWED_LATIN}
        if latin:
            problems.append({"id": question["id"], "problem": f"Latin text {sorted(latin)}", "hint": hint})
        if item.get("basis") not in BASES:
            warnings.append({"id": question["id"], "warning": f"unknown basis {item.get('basis')!r}"})
        if question["id"] in conflicts and item.get("basis") != "book_conflict":
            warnings.append({"id": question["id"], "warning": "answer-key conflict not flagged as book_conflict", "hint": hint})
        if item.get("basis") == "book_conflict" and question["id"] not in listed:
            warnings.append({"id": question["id"], "warning": "book_conflict hint but the question is not in manual-review.json", "hint": hint})
        answer_numbers = numbers(answer)
        points_at_option = answer_kind(answer) == "pointer" or (question.get("image") and re.fullmatch(r"\s*[1-4۱-۴]\s*", answer))
        written_out = {"4": "چهار", "10000": "۱۰ هزار"}.get(next(iter(answer_numbers), ""), "\0") in hint
        if answer_numbers and not points_at_option and not written_out and not (answer_numbers & numbers(hint)):
            warnings.append({"id": question["id"], "warning": f"numeric answer {sorted(answer_numbers)} not mentioned", "hint": hint})
        hints[question["id"]] = {"hint": hint, "basis": item.get("basis"), "note": item.get("note"), "checked": bool(item.get("checked"))}

    lengths = sorted(len(h["hint"]) for h in hints.values())
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "questions": len(bank),
        "withHint": len(hints),
        "basis": dict(Counter(h["basis"] for h in hints.values())),
        "independentCheck": {"checked": sum(h["checked"] for h in hints.values()),
                             "revised": sum((h["note"] or "").startswith("revised after independent check") for h in hints.values())},
        "length": {"max": lengths[-1] if lengths else 0, "median": lengths[len(lengths) // 2] if lengths else 0},
        "problems": problems,
        "warnings": warnings,
        "duplicateEntries": duplicates,
        "unknownIds": sorted(set(raw) - {q["id"] for q in bank} - removed_question_ids()),
        "removedQuestions": sorted(set(raw) & removed_question_ids()),
    }
    (DATA / "hint-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    lines = [
        "// Generated by scripts/tiering/merge_hints.py from data/hint-review/ — do not edit by hand.",
        "// Short study hints shown after answering; grounded in the textbook page of each question.",
        "export const questionHints = {",
    ]
    lines += [f"  {json.dumps(qid)}:{json.dumps(entry['hint'], ensure_ascii=False)}," for qid, entry in hints.items()]
    lines.append("};")
    (DATA / "question-hints.js").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("questions", "withHint", "basis", "independentCheck", "length")}, ensure_ascii=False),
          f"problems={len(problems)} warnings={len(warnings)} duplicates={len(duplicates)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
