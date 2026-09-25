#!/usr/bin/env python3
"""Apply independent-check verdicts to the written hints (data/hint-review).

Every hint was re-read by a second reviewer against the textbook page and the answer key
(verdict ok / fix). For "fix" verdicts the reviewer's corrected hint replaces the original,
and the change is recorded in the hint's note. A basis suggested in the problem text
("suggest basis \"book\"") is applied too. Hints marked "editedAfterCheck" were reworded by
the editor after reading the verdict and are left as they are.

usage: apply_hint_verdicts.py HINTS_DIR VERDICTS_DIR
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path


def main(hints_dir, verdicts_dir):
    verdicts = {}
    for path in sorted(Path(verdicts_dir).glob("verdict*.json")):
        for item in json.loads(path.read_text(encoding="utf-8")):
            verdicts[item["id"]] = item
    counts = Counter()
    for path in sorted(Path(hints_dir).glob("hints-*.json")):
        hints = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for hint in hints:
            verdict = verdicts.get(hint["id"])
            if not verdict:
                counts["unchecked"] += 1
                continue
            hint["checked"] = True
            if hint.get("editedAfterCheck"):
                counts["edited"] += 1
                continue
            if verdict["verdict"] != "fix":
                counts["ok"] += 1
                continue
            suggestion = (verdict.get("suggestedHint") or "").strip()
            if not suggestion:
                counts["fix_without_suggestion"] += 1
                continue
            if suggestion != hint["hint"]:
                hint["hint"] = suggestion
                hint["note"] = f"revised after independent check: {verdict.get('problem') or ''}".strip()
                basis = re.search(r'basis\s*"?(book_conflict|book|answer)"?', verdict.get("problem") or "")
                if basis:
                    hint["basis"] = basis.group(1)
                counts["fixed"] += 1
                changed = True
        if changed or any("checked" in h for h in hints):
            path.write_text(json.dumps(hints, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(dict(counts))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
