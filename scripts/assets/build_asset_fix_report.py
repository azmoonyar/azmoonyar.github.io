#!/usr/bin/env python3
"""Write data/asset-fix-report.json: every question picture repaired in the 2026-09-25 pass.

Lists the fix scripts, the files each one rewrites (file names unchanged) and the questions
that display them. Untouched originals of rewritten files are kept in tmp/asset-originals/.

usage: build_asset_fix_report.py BANK.json
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import fix_answer_leak_assets as leaks  # noqa: E402
import fix_ayin1_option_images as ayin1  # noqa: E402
import fix_broken_question_images as broken  # noqa: E402
import fix_option_grid_assets as grids  # noqa: E402


def main(bank_path):
    bank = json.loads(Path(bank_path).read_text(encoding="utf-8"))
    users = {}
    for question in bank:
        if question.get("image"):
            users.setdefault(Path(question["image"]["src"]).name, []).append(question["id"])

    groups = {
        "scripts/assets/fix_option_grid_assets.py": {
            "reason": "4_5888 four-option sign composites: tiles were offset (half signs, blank tiles, red «گزینه» answer label)",
            "files": [f"q-src-4-5888983329180487891-1-p{p:03d}-n{n:02d}.png" for (p, n) in grids.TILES]},
        "scripts/assets/fix_answer_leak_assets.py": {
            "reason": "answer markers (asterisk / check / red answer text) or neighbouring option text inside the crop; masked or cropped to the figure",
            "files": sorted(leaks.FIXES)},
        "scripts/assets/fix_ayin1_option_images.py": {
            "reason": "ایین نامه-1 pictures rebuilt from the page renders: option order matching the question's key, and green answer checks removed",
            "files": sorted(list(ayin1.COMPOSITES) + list(ayin1.SINGLES))},
        "scripts/assets/fix_broken_question_images.py": {
            "reason": "crop missed the stimulus (showed option text, another question or half a sign); re-cropped from the source page",
            "files": sorted(broken.CROPS)},
    }
    for group in groups.values():
        group["count"] = len(group["files"])
        group["files"] = [{"file": name, "questions": users.get(name, [])} for name in group["files"]]
    distinct = {f["file"] for g in groups.values() for f in g["files"]}
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method": "Problems were found by pixel scans (red/green/dark marks on the page background, thin red text, text-only crops) and every candidate was checked visually on contact sheets; boxes were measured with a coordinate ruler. No OCR.",
        "distinctFilesRewritten": len(distinct),
        "originalsKeptIn": "tmp/asset-originals/",
        "note": "extraction-qa-report.json (2026-09-24) recorded 0 remaining answer leaks after an 80-candidate review; this full pass found and fixed the ones listed here.",
        "groups": groups,
        "questionLevelCorrections": "data/question-corrections.js",
    }
    (ROOT / "data" / "asset-fix-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"files={len(distinct)}")


if __name__ == "__main__":
    main(sys.argv[1])
