"""Ids of the questions removed from the bank at the project owner's request (data/question-removals.js).

The review records of a removed question (book review, hint, verification) are kept; the pipeline scripts
use these ids to report them as removed instead of as unknown.
"""
import re
from pathlib import Path

REMOVALS = Path(__file__).resolve().parents[2] / "data" / "question-removals.js"


def removed_question_ids():
    if not REMOVALS.exists():
        return set()
    return set(re.findall(r'^\s*"(q-[^"]+)":\s*\{', REMOVALS.read_text(encoding="utf-8"), flags=re.M))
