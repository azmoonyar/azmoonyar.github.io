#!/usr/bin/env python3
"""Rank candidate book passages for every question (lexical retrieval only).

The ranking only proposes candidates; the final page/confidence for each
question is decided by reviewing the candidates against the question.

usage: retrieve_candidates.py BANK.json OUT_DIR [BATCH_SIZE]
Writes OUT_DIR/batch-XX.json files and OUT_DIR/candidates-all.json.
"""
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from textnorm import STOPWORDS, char_ngrams, compact, is_generic_answer, norm  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SPLIT_ITEMS = re.compile(r"\n+(?=- |\[کادر\])")


def word_tokens(text):
    return [w for w in norm(text).split() if (len(w) > 1 or w.isdigit()) and w not in STOPWORDS]


def build_passages(pages):
    passages = []
    for page in pages:
        base = {"bookPage": page["bookPage"], "chapterId": page["chapterId"], "headings": page["headings"]}
        for paragraph in re.split(r"\n\s*\n", page["text"]):
            for item in SPLIT_ITEMS.split(paragraph):
                item = item.strip()
                if len(compact(item)) < 6:
                    continue
                kind = "box" if item.startswith("[کادر]") else "text"
                # Long paragraphs are windowed so a single fact is not diluted.
                sentences = re.split(r"(?<=[.!؟?؛])\s+", item)
                window, chunks = "", []
                for sentence in sentences:
                    if window and len(window) + len(sentence) > 420:
                        chunks.append(window)
                        window = sentence
                    else:
                        window = f"{window} {sentence}".strip()
                if window:
                    chunks.append(window)
                for chunk in chunks:
                    passages.append(dict(base, kind=kind, text=chunk))
        for sign in page["signs"]:
            caption = sign.get("caption", "").strip()
            passages.append(dict(base, kind="sign", text=caption, description=sign.get("description")))
        for figure in page["figures"]:
            caption = (figure.get("caption") or "").strip()
            if caption:
                passages.append(dict(base, kind="figure", text=caption, description=figure.get("description")))
        for heading in page["headings"]:
            passages.append(dict(base, kind="heading", text=heading))
    for index, passage in enumerate(passages):
        passage["pid"] = index
    return passages


class Bm25:
    def __init__(self, docs, k1=1.4, b=0.72):
        self.docs = [Counter(doc) for doc in docs]
        self.lengths = [sum(doc.values()) for doc in self.docs]
        self.avg = sum(self.lengths) / max(1, len(self.lengths))
        df = Counter(term for doc in self.docs for term in doc)
        n = len(self.docs)
        self.idf = {term: math.log(1 + (n - freq + 0.5) / (freq + 0.5)) for term, freq in df.items()}
        self.index = defaultdict(list)
        for doc_id, doc in enumerate(self.docs):
            for term in doc:
                self.index[term].append(doc_id)
        self.k1, self.b = k1, b

    def scores(self, query_weights):
        result = defaultdict(float)
        for term, weight in query_weights.items():
            idf = self.idf.get(term)
            if not idf:
                continue
            for doc_id in self.index[term]:
                tf = self.docs[doc_id][term]
                denom = tf + self.k1 * (1 - self.b + self.b * self.lengths[doc_id] / self.avg)
                result[doc_id] += weight * idf * tf * (self.k1 + 1) / denom
        return result


def section_title_for(sections, page):
    matches = [s for s in sections if s["startBookPage"] <= page <= s["endBookPage"]]
    return matches[-1]["title"] if matches else None


def main(bank_path, out_dir, batch_size=70):
    bank = json.loads(Path(bank_path).read_text(encoding="utf-8"))
    pages = json.loads((ROOT / "data" / "book-pages.json").read_text(encoding="utf-8"))["pages"]
    sections = json.loads((ROOT / "data" / "book-structure.json").read_text(encoding="utf-8"))["sections"]
    passages = build_passages(pages)
    bm25 = Bm25([word_tokens(p["text"] + " " + (p.get("description") or "") * (p["kind"] == "sign")) for p in passages])
    grams = [char_ngrams(p["text"]) for p in passages]
    gram_index = defaultdict(list)
    for pid, gram_set in enumerate(grams):
        for gram in gram_set:
            gram_index[gram].append(pid)

    records = []
    for question in bank:
        correct = next(o["text"] for o in question["options"] if o["id"] == question["correctOptionId"])
        generic = is_generic_answer(correct)
        weights = Counter()
        for token in word_tokens(question["text"]):
            weights[token] += 1.0
        if not generic:
            for token in word_tokens(correct):
                weights[token] += 2.0
        lexical = bm25.scores(weights)

        # Character trigram overlap with the correct answer (sign names, spacing variants).
        answer_grams = char_ngrams(correct) if not generic else set()
        question_grams = char_ngrams(question["text"])
        overlap = Counter()
        for gram in answer_grams | question_grams:
            for pid in gram_index.get(gram, ()):
                overlap[pid] += 1
        combined = {}
        max_lex = max(lexical.values(), default=1) or 1
        for pid in set(lexical) | {pid for pid, _ in overlap.most_common(400)}:
            passage_grams = grams[pid]
            answer_cover = len(answer_grams & passage_grams) / len(answer_grams) if answer_grams else 0
            question_cover = len(question_grams & passage_grams) / max(1, len(question_grams))
            exact = 1.0 if answer_grams and passages[pid]["kind"] in ("sign", "figure") and compact(correct) == compact(passages[pid]["text"]) else 0.0
            combined[pid] = 0.55 * lexical.get(pid, 0) / max_lex + 0.30 * answer_cover + 0.15 * question_cover + 0.6 * exact
        ranked = sorted(combined.items(), key=lambda item: item[1], reverse=True)

        by_page = {}
        for pid, score in ranked:
            page = passages[pid]["bookPage"]
            if page not in by_page and len(by_page) >= 4:
                continue
            entry = by_page.setdefault(page, {"bookPage": page, "chapterId": passages[pid]["chapterId"], "section": section_title_for(sections, page), "score": round(score, 3), "passages": []})
            kind = passages[pid]["kind"]
            short_caption = kind in ("sign", "figure") and len(passages[pid]["text"]) <= 80
            if kind != "heading" and (not entry["passages"] or (len(entry["passages"]) < 2 and short_caption)):
                entry["passages"].append({"kind": kind, "text": passages[pid]["text"][:300]} | ({"signDescription": passages[pid]["description"][:140]} if kind == "sign" and passages[pid].get("description") else {}))
            if len(by_page) >= 4 and all(e["passages"] for e in by_page.values()):
                break
        candidates = sorted(by_page.values(), key=lambda e: e["score"], reverse=True)[:4]
        records.append({
            "id": question["id"],
            "text": question["text"],
            "options": [f"{o['id']}) {o['text']}" for o in question["options"]],
            "correctOptionId": question["correctOptionId"],
            "correctAnswerText": correct,
            "image": question["image"]["src"] if question.get("image") else None,
            "imageAlt": question["image"]["alt"] if question.get("image") else None,
            "candidates": candidates,
        })

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "candidates-all.json").write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    # Group related questions (same best page) so each review batch covers a coherent topic.
    records.sort(key=lambda r: (r["candidates"][0]["bookPage"] if r["candidates"] else 999, r["id"]))
    batches = [records[i:i + batch_size] for i in range(0, len(records), batch_size)]
    for number, batch in enumerate(batches, 1):
        (out / f"batch-{number:02d}.json").write_text(json.dumps(batch, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"passages={len(passages)} questions={len(records)} batches={len(batches)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 70)
