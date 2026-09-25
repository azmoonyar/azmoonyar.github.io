#!/usr/bin/env python3
"""Propose bank questions that test the facts highlighted in nokat.pdf («نکات مهم»).

nokat.pdf (read visually, no OCR) lists tips and short Q&A that its publisher marks as
important for the exam. For every item this script ranks the bank questions lexically
(question + correct answer); the proposals are then reviewed one by one and only
questions that test the same fact are kept.

usage: match_tips.py BANK.json NOKAT_ITEMS.json OUT.json
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from retrieve_candidates import Bm25, word_tokens  # noqa: E402
from textnorm import char_ngrams, jaccard  # noqa: E402


def main(bank_path, items_path, out_path, per_item=8):
    bank = json.loads(Path(bank_path).read_text(encoding="utf-8"))
    items = [item for item in json.loads(Path(items_path).read_text(encoding="utf-8")) if item["kind"] in ("tip", "qa")]
    documents = []
    for question in bank:
        answer = next(o["text"] for o in question["options"] if o["id"] == question["correctOptionId"])
        documents.append(f"{question['text']} {answer} {answer}")
    bm25 = Bm25([word_tokens(document) for document in documents])
    grams = [char_ngrams(document) for document in documents]
    output = []
    for number, item in enumerate(items, 1):
        query_text = f"{item['text']} {item.get('answer') or ''}"
        lexical = bm25.scores(Counter(word_tokens(query_text)))
        query_grams = char_ngrams(query_text)
        top = max(lexical.values(), default=1) or 1
        scored = sorted(((0.7 * lexical.get(i, 0) / top + 0.3 * jaccard(query_grams, grams[i]), i) for i in set(lexical)), reverse=True)[:per_item]
        output.append({
            "item": number, "page": item["page"], "kind": item["kind"], "text": item["text"], "answer": item.get("answer"),
            "candidates": [{"id": bank[i]["id"], "question": bank[i]["text"],
                            "correctAnswer": next(o["text"] for o in bank[i]["options"] if o["id"] == bank[i]["correctOptionId"]),
                            "score": round(score, 3)} for score, i in scored],
        })
    Path(out_path).write_text(json.dumps(output, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"items={len(output)} candidates={sum(len(o['candidates']) for o in output)}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
