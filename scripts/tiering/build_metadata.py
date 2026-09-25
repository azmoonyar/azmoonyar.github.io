#!/usr/bin/env python3
"""Compute study tiers (1-5) and priority scores, then write the UI metadata.

Inputs : BANK.json (node scripts/tiering/dump_bank.mjs), data/book-references.json,
         data/book-structure.json, data/book-pages.json
Outputs: data/question-metadata.js           tier + book reference per question id (loaded by questions.js)
         data/tier-classification-report.json audit report

Tiers are a study-priority ranking built from evidence in this dataset and the book;
they are not official exam probabilities.

usage: build_metadata.py BANK.json
"""
import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from textnorm import answer_kind, char_ngrams, compact, jaccard, norm  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"

# ---- Scoring model (additive points on a 0-100 scale) -------------------------------------------
# Evidence ladder: the same exam item seen in several independent sample-question PDFs is the
# strongest signal; chapter, topic density in the bank, exam style and book emphasis refine it.
WEIGHTS = {
    "base": 4,
    # Merged exact duplicates (identical stem, options and key) in >=2 PDFs; always Tier 1.
    "cross_source_duplicate": {2: 44, 3: 50},
    "duplicate_also_reworded_elsewhere": 4,        # a merged duplicate whose concept reaches one more PDF
    # Not merged (options reordered / wording differs), but the same item is found in other PDFs.
    # Keyed by the number of distinct PDFs covering the concept.
    "cross_source_equivalent": {
        "same_question": {2: 28, 3: 36},            # stem and correct answer (near-)identical
        "same_question_reworded": {2: 25, 3: 32},   # stem reworded, same correct answer
        "same_sign_asked": {2: 21, 3: 28},          # the same sign name asked with a sign picture
    },
    "in_sample_exam": 8,                             # printed in a 30-question sample exam (4_5888 / 600-driveing / ایین نامه-1),
                                                     # not only in the tablo.pdf sign catalogue
    "repeated_within_source": 5,                     # asked twice in one PDF: weaker than cross-source
    "chapter": {1: 18, 2: 9, 3: 6, 5: 6, 4: 4, 6: 4},  # ~2/3 of every sample exam comes from chapter 1
    "topic_density": 14,                             # x percentile of bank questions linked to the page (+-2 pages)
    "exam_style": 5,                                 # explicit number / prohibition / right of way / definition / sign
    "reference_confidence": {"high": 3, "medium": 1.5, "low": 0, "not_found": 0},
    "book_emphasis_box": 2,                          # supporting text sits in a highlighted box of the book
}
EXAM_FORMAT_SOURCES = {"4_5888983329180487891-1.pdf", "600-driveing.pdf", "ایین نامه-1.pdf"}
# Tier cut points were set at natural gaps of the observed score distribution (see the report):
# the suggested 80/60/40/20 bands would have put ~34% of the bank in Tier 1 and split the large
# cluster of tablo-only sign questions (score 42-44) across two tiers.
THRESHOLDS = [(1, 87), (2, 70), (3, 45), (4, 32), (5, 0)]
CROSS_SOURCE_DUPLICATE_FLOOR = THRESHOLDS[0][1]    # hard rule: merged duplicates across PDFs are Tier 1
SIGN_STEM = re.compile(r"(تابلو|علامت|علائم)")
SIGN_QUESTION = re.compile(r"(چیست|معنا|مفهوم|بیانگر|نام|عنوان|منظور|اشاره)")
GENERIC_STEMS = {compact(text) for text in [
    "این تابلو بیانگر چیست؟", "مفهوم این تابلو چیست؟", "نام این تابلو چیست؟", "عنوان این تابلو چیست؟",
    "مفهوم تابلوی روبرو چیست ؟", "تابلوی زیر به چه معناست؟", "تابلو مقابل به چه معناست؟", "این شکل بیانگر چیست؟",
    "تابلوی مقابل به چه معنا می باشد ؟", "این تابلوها بیانگر چیست؟", "این علامت بیانگر چیست؟",
]}


POINTER_NUMBER = re.compile(r"(گزینه|شکل|تصویر|تابلو|تابلوی|شماره|مورد|موارد|خودرو|خودروی|خودروهای|خودروها|وسیله|وسایل|ردیف)\s*\d+(\s*(و|،|,)\s*\d+)*")


def has_fact_number(text):
    """True when the text carries a factual number (speed, distance, time...), not an option/figure pointer."""
    cleaned = POINTER_NUMBER.sub(" ", norm(text))
    return bool(re.search(r"\d", cleaned))


def correct_text(question):
    return next(option["text"] for option in question["options"] if option["id"] == question["correctOptionId"])


def pdf_set(question):
    return frozenset(source["pdf"] for source in question["sources"])


# ---------------------------------------------------------------- equivalence
def equivalence_clusters(bank):
    """Link questions that are the same exam item with different wording (never merged)."""
    info = []
    for question in bank:
        answer = correct_text(question)
        info.append({
            "q": char_ngrams(question["text"]), "a": char_ngrams(answer), "kind": answer_kind(answer),
            "answer": compact(answer), "stem": compact(question["text"]), "image": bool(question.get("image")),
            "signStem": bool(SIGN_STEM.search(question["text"]) and SIGN_QUESTION.search(question["text"])),
        })
    index = defaultdict(set)
    for i, item in enumerate(info):
        for gram in item["q"] | item["a"]:
            index[gram].add(i)

    parent = list(range(len(bank)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    links = defaultdict(set)
    for i, x in enumerate(info):
        shared = Counter()
        for gram in sorted(x["q"] | x["a"]):  # sorted: set order depends on the per-process hash seed
            members = index[gram]
            if len(members) < 300:
                for j in sorted(members):
                    if j > i:
                        shared[j] += 1
        for j, _ in sorted(shared.items(), key=lambda item: (-item[1], item[0]))[:80]:
            y = info[j]
            if x["kind"] != y["kind"]:
                continue
            q_sim, a_sim = jaccard(x["q"], y["q"]), jaccard(x["a"], y["a"])
            kind = None
            if x["kind"] == "text" and q_sim >= 0.9 and a_sim >= 0.9:
                kind = "same_question"
            elif x["kind"] == "text" and q_sim >= 0.75 and a_sim >= 0.75:
                kind = "same_question_reworded"
            elif x["kind"] == "numeric" and q_sim >= 0.8 and x["answer"] == y["answer"]:
                kind = "same_question" if q_sim >= 0.9 else "same_question_reworded"
            elif x["kind"] == "pointer" and q_sim >= 0.9 and x["stem"] not in GENERIC_STEMS and len(x["stem"]) >= 25:
                kind = "same_question_reworded"
            elif x["kind"] == "text" and x["image"] and y["image"] and x["signStem"] and y["signStem"] and a_sim >= 0.9 and len(x["answer"]) >= 4:
                kind = "same_sign_asked"
            if kind:
                parent[find(i)] = find(j)
                links[i].add((j, kind))
                links[j].add((i, kind))
    clusters = defaultdict(list)
    for i in range(len(bank)):
        clusters[find(i)].append(i)
    result = []
    for i, question in enumerate(bank):
        members = clusters[find(i)]
        pdfs = frozenset().union(*(pdf_set(bank[m]) for m in members))
        other_source_kinds = {kind for j, kind in links[i] if not (pdf_set(bank[j]) <= pdf_set(question))}
        result.append({"clusterSize": len(members), "clusterPdfs": pdfs, "linkKinds": other_source_kinds,
                       "clusterIds": [bank[m]["id"] for m in members]})
    return result


# ---------------------------------------------------------------- sections
def load_sections():
    structure = json.loads((DATA / "book-structure.json").read_text(encoding="utf-8"))
    merged = []
    for section in structure["sections"]:
        if merged and merged[-1]["title"] == section["title"] and merged[-1]["endBookPage"] + 1 >= section["startBookPage"]:
            merged[-1]["endBookPage"] = max(merged[-1]["endBookPage"], section["endBookPage"])
            continue
        merged.append(dict(section))
    return structure, merged


def section_for(sections, page):
    if page is None:
        return None
    matches = [s for s in sections if s["startBookPage"] <= page <= s["endBookPage"]]
    return matches[-1] if matches else None


# ---------------------------------------------------------------- main
def main(bank_path):
    bank = json.loads(Path(bank_path).read_text(encoding="utf-8"))
    references = json.loads((DATA / "book-references.json").read_text(encoding="utf-8"))["references"] if (DATA / "book-references.json").exists() else {}
    structure, sections = load_sections()
    chapter_titles = {c["id"]: c["title"] for c in structure["chapters"]}
    pages = {p["bookPage"]: p for p in json.loads((DATA / "book-pages.json").read_text(encoding="utf-8"))["pages"]}
    equivalence = equivalence_clusters(bank)

    rows = []
    for question, eq in zip(bank, equivalence):
        ref = references.get(question["id"], {})
        page = ref.get("bookPage")
        section = section_for(sections, page)
        pdfs = pdf_set(question)
        per_pdf = Counter(source["pdf"] for source in question["sources"])
        rows.append({
            "question": question, "ref": ref, "page": page, "section": section, "eq": eq,
            "mergedPdfCount": len(pdfs), "clusterPdfCount": len(eq["clusterPdfs"]),
            "withinRepeat": max(per_pdf.values()) > 1,
            "chapterId": ref.get("chapterId"),
        })

    # Topic density: kernel density of bank questions linked to pages around each book page
    # (+-2 pages). A concept asked many times, in any wording, makes its pages dense; source
    # agreement is scored separately, so it is not mixed in here. Questions are never merged.
    page_rows = defaultdict(list)
    for row in rows:
        if row["page"]:
            page_rows[row["page"]].append(row)
    kernel = {0: 1.0, 1: 0.5, 2: 0.25}
    page_density = {}
    for page in page_rows:
        page_density[page] = sum(weight * len(page_rows.get(neighbour, []))
                                 for offset, weight in kernel.items() for neighbour in {page - offset, page + offset})
    density_values = sorted(page_density.values())

    def density_percentile(value):
        return sum(1 for d in density_values if d <= value) / len(density_values) if density_values else 0

    row_by_id = {row["question"]["id"]: row for row in rows}
    for row in rows:
        question, ref = row["question"], row["ref"]
        answer = correct_text(question)
        text_all = norm(question["text"] + " " + answer)
        reasons, score = [], WEIGHTS["base"]
        cross_duplicate = row["mergedPdfCount"] > 1
        kinds = row["eq"]["linkKinds"]
        if cross_duplicate:
            score += WEIGHTS["cross_source_duplicate"][min(3, row["mergedPdfCount"])]
            reasons.append("cross_source_duplicate")
            if row["clusterPdfCount"] > row["mergedPdfCount"]:
                score += WEIGHTS["duplicate_also_reworded_elsewhere"]
                reasons.append("also_reworded_in_other_source")
        elif row["clusterPdfCount"] > 1:
            strongest = next((kind for kind in ("same_question", "same_question_reworded", "same_sign_asked") if kind in kinds), "same_question_reworded")
            score += WEIGHTS["cross_source_equivalent"][strongest][min(3, row["clusterPdfCount"])]
            reasons.append({"same_question": "cross_source_same_question", "same_question_reworded": "cross_source_reworded",
                            "same_sign_asked": "cross_source_same_sign"}[strongest])
            if row["clusterPdfCount"] >= 3:
                reasons.append("seen_in_3_or_more_sources")
        else:
            reasons.append("single_source")
        if row["withinRepeat"]:
            score += WEIGHTS["repeated_within_source"]
            reasons.append("repeated_within_source")
        if pdf_set(question) & EXAM_FORMAT_SOURCES or any(pdf_set(row_by_id[other]["question"]) & EXAM_FORMAT_SOURCES for other in row["eq"]["clusterIds"]):
            score += WEIGHTS["in_sample_exam"]
            reasons.append("in_sample_exam")
        chapter = row["chapterId"]
        if chapter in WEIGHTS["chapter"]:
            score += WEIGHTS["chapter"][chapter]
            reasons.append(f"chapter_{chapter}")
        if row["page"]:
            pct = density_percentile(page_density[row["page"]])
            row["topicDensityPercentile"] = round(pct, 3)
            score += WEIGHTS["topic_density"] * pct
            if pct >= 0.75:
                reasons.append("high_frequency_topic")
            elif pct >= 0.4:
                reasons.append("medium_frequency_topic")
            else:
                reasons.append("low_frequency_topic")
        style = []
        if has_fact_number(answer) or has_fact_number(question["text"]):
            style.append("explicit_number")
        if "تقدم" in text_all:
            style.append("right_of_way")
        if re.search(r"ممنوع|مجاز|نباید|الزامی|مکلف|اجباری", text_all):
            style.append("prohibition_rule")
        if re.search(r"^منظور از|به چه معنا|تعریف|گفته می ?شود|اطلاق می ?شود", norm(question["text"])):
            style.append("definition")
        if question.get("image") and SIGN_STEM.search(question["text"]) or (row["page"] and 20 <= row["page"] <= 45):
            style.append("sign_or_marking")
        if style:
            score += WEIGHTS["exam_style"]
            reasons.extend(sorted(set(style)))
        confidence = ref.get("referenceConfidence", "not_found")
        score += WEIGHTS["reference_confidence"].get(confidence, 0)
        if confidence in ("high", "medium"):
            reasons.append(f"book_reference_{confidence}")
        if ref.get("inBox"):
            score += WEIGHTS["book_emphasis_box"]
            reasons.append("book_emphasis_box")
        score = max(0, min(100, round(score)))
        if cross_duplicate and score < CROSS_SOURCE_DUPLICATE_FLOOR:
            score = CROSS_SOURCE_DUPLICATE_FLOOR  # the duplicate rule takes precedence over the score
            reasons.append("tier1_by_duplicate_rule")
        row["score"], row["reasons"] = score, reasons
        row["tier"] = 1 if cross_duplicate else next(tier for tier, floor in THRESHOLDS if score >= floor)

    write_metadata(rows, chapter_titles)
    write_report(rows, sections)


def write_metadata(rows, chapter_titles):
    """Compact module: empty/null fields are omitted (questions.js supplies the defaults) and
    chapter titles are stored once, which keeps the file small for the first page load."""
    lines = [
        "// Generated by scripts/tiering/build_metadata.py — do not edit by hand.",
        "// tier / priorityScore / tierReasons: study-priority ranking from this dataset and the book, not official exam probabilities.",
        "// Book references were verified against the visual transcription of main book.pdf (data/book-pages.json);",
        "// bookPage is the printed page number, bookPdfPage = bookPage + 2.",
        f"export const chapterTitles = {json.dumps({str(k): v for k, v in sorted(chapter_titles.items())}, ensure_ascii=False)};",
        "export const questionMetadata = {",
    ]
    for row in rows:
        ref = row["ref"]
        meta = {
            "tier": row["tier"], "priorityScore": row["score"], "tierReasons": row["reasons"], "chapterId": row["chapterId"],
            "bookPage": ref.get("bookPage"), "bookPdfPage": ref.get("bookPdfPage"), "bookReference": ref.get("bookReference"),
            "supportingText": ref.get("supportingText"), "referenceConfidence": ref.get("referenceConfidence", "not_found"),
            "secondaryReferences": [reference["bookPage"] for reference in ref.get("secondaryReferences", [])],
        }
        meta = {key: value for key, value in meta.items() if value not in (None, [], "")}
        lines.append(f"  {json.dumps(row['question']['id'])}:{json.dumps(meta, ensure_ascii=False, separators=(',', ':'))},")
    lines.append("};")
    (DATA / "question-metadata.js").write_text("\n".join(lines) + "\n", encoding="utf-8")


def evidence_classes(rows):
    counts = Counter()
    for r in rows:
        if r["mergedPdfCount"] > 1:
            counts["merged_duplicate_in_%d_pdfs" % r["mergedPdfCount"]] += 1
        elif r["clusterPdfCount"] > 1:
            counts["equivalent_in_%s_pdfs" % ("3+" if r["clusterPdfCount"] >= 3 else "2")] += 1
        else:
            counts["single_source"] += 1
    return dict(sorted(counts.items()))


def exam_chapter_validation(rows):
    """Chapter mix of the 30-question sample exams, used to check the '20 of 30 from chapter 1' rule."""
    per_exam = defaultdict(Counter)
    for r in rows:
        for source in r["question"]["sources"]:
            if source.get("examNumber") and source["pdf"] in ("ایین نامه-1.pdf", "600-driveing.pdf"):
                per_exam[(source["pdf"], source["examNumber"])][r["chapterId"]] += 1
    result = {}
    for pdf in ("ایین نامه-1.pdf", "600-driveing.pdf"):
        exams = [counts for (name, _), counts in sorted(per_exam.items()) if name == pdf]
        chapter_one = [counts[1] for counts in exams]
        result[pdf] = {"exams": len(exams), "chapter1PerExam": chapter_one,
                       "averageChapter1Of30": round(sum(chapter_one) / len(chapter_one), 1) if chapter_one else None,
                       "range": [min(chapter_one), max(chapter_one)] if chapter_one else None}
    result["conclusion"] = "In the 20 photographed exam papers of ایین نامه-1.pdf and the 20 exams of 600-driveing.pdf, chapter 1 supplies about 18 of 30 questions (range 14-21), which supports the 20 + 10 split used by the simulated exam."
    return result


def write_report(rows, sections):
    total = len(rows)
    tiers = Counter(row["tier"] for row in rows)
    confidence = Counter(row["ref"].get("referenceConfidence", "not_found") for row in rows)
    chapters = Counter(row["chapterId"] for row in rows)
    reason_counts = Counter(reason for row in rows for reason in row["reasons"])
    by_topic = defaultdict(list)
    for row in rows:
        if row["section"]:
            by_topic[(row["section"]["chapterId"], row["section"]["title"])].append(row)
    topics = []
    for (chapter, title), members in sorted(by_topic.items(), key=lambda item: -len(item[1])):
        pages = sorted({r["page"] for r in members})
        topics.append({"title": title, "chapterId": chapter, "bookPages": f"{pages[0]}-{pages[-1]}", "questions": len(members),
                       "multiSourceQuestions": sum(1 for r in members if r["clusterPdfCount"] > 1),
                       "tierCounts": {str(t): sum(1 for r in members if r["tier"] == t) for t in range(1, 6)}})
    examples = {}
    for tier in range(1, 6):
        picked = sorted([r for r in rows if r["tier"] == tier], key=lambda r: (-r["score"], r["question"]["id"]))
        sample = picked[:2] + picked[len(picked) // 2: len(picked) // 2 + 2] + picked[-2:] if len(picked) > 6 else picked
        examples[str(tier)] = [{"id": r["question"]["id"], "text": r["question"]["text"], "priorityScore": r["score"], "tierReasons": r["reasons"],
                                "sourcePdfs": sorted(pdf_set(r["question"])), "bookPage": r["ref"].get("bookPage"), "chapterId": r["chapterId"]} for r in sample]
    cross_duplicates = [r for r in rows if r["mergedPdfCount"] > 1]
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "complete",
        "disclaimer": "Tiers are a study-priority ranking derived from evidence in this dataset and the reference book; they are not official exam probabilities.",
        "totalQuestions": total,
        "tier1Count": tiers[1], "tier2Count": tiers[2], "tier3Count": tiers[3], "tier4Count": tiers[4], "tier5Count": tiers[5],
        "tierSharePercent": {str(t): round(100 * tiers[t] / total, 1) for t in range(1, 6)},
        "crossSourceDuplicateCount": len(cross_duplicates),
        "crossSourceDuplicatesInTier1": sum(1 for r in cross_duplicates if r["tier"] == 1),
        "crossSourceDuplicateBySourceCount": {str(k): v for k, v in sorted(Counter(r["mergedPdfCount"] for r in cross_duplicates).items())},
        "crossSourceEquivalentCount": sum(1 for r in rows if r["mergedPdfCount"] == 1 and r["clusterPdfCount"] > 1),
        "repeatedWithinSingleSourceCount": sum(1 for r in rows if r["withinRepeat"] and r["mergedPdfCount"] == 1),
        "chapter1Count": chapters[1],
        "otherChapterCount": sum(v for k, v in chapters.items() if k and k != 1),
        "chapterCounts": {str(k) if k else "unknown": v for k, v in sorted(chapters.items(), key=lambda item: (item[0] is None, item[0] or 0))},
        "questionsWithBookReference": sum(1 for r in rows if r["ref"].get("bookPage")),
        "questionsWithoutBookReference": sum(1 for r in rows if not r["ref"].get("bookPage")),
        "highConfidenceReferences": confidence["high"], "mediumConfidenceReferences": confidence["medium"],
        "lowConfidenceReferences": confidence["low"], "notFoundReferences": confidence["not_found"],
        "tierByChapter": {str(chapter): {str(t): sum(1 for r in rows if r["chapterId"] == chapter and r["tier"] == t) for t in range(1, 6)}
                          for chapter in sorted(c for c in chapters if c)},
        "evidenceClassCounts": evidence_classes(rows),
        "scoringModel": {
            "weights": WEIGHTS,
            "tierThresholds": {str(t): f for t, f in THRESHOLDS},
            "thresholdRationale": "Cut points sit at natural gaps of the observed score distribution. The suggested 80/60/40/20 bands would have put ~34% of the bank in Tier 1 and split the cluster of tablo-only sign questions (score 42-44) across two tiers.",
            "crossSourceDuplicateRule": f"questions merged from >=2 different PDFs are always Tier 1 (score floor {CROSS_SOURCE_DUPLICATE_FLOOR}); tierReasons record tier1_by_duplicate_rule when the floor was applied",
            "topicDensity": "for each book page, the number of bank questions linked to it and to its neighbours (weights 1, 0.5, 0.25 for 0/1/2 pages away), converted to a percentile; a concept asked many times in any wording makes its pages dense",
            "equivalence": "questions that were not merged are linked when stem and correct answer are near-identical (char-trigram Jaccard >= 0.9 / >= 0.75 for rewordings) or the same sign name is asked with a sign picture; linked questions are never merged, edited or removed",
            "inSampleExam": "4_5888983329180487891-1.pdf, 600-driveing.pdf and ایین نامه-1.pdf are organised as 30-question sample exams; tablo.pdf is a sign catalogue quiz",
        },
        "examFormatValidation": exam_chapter_validation(rows),
        "reasonCounts": dict(reason_counts.most_common()),
        "topicDistribution": topics[:40],
        "examplesByTier": examples,
        "sourceProvenance": {
            "note": "Distinct PDF files are treated as independent sources, as specified. 600-driveing.pdf, tablo.pdf and ایین نامه-1.pdf carry the driveing.ir watermark; 4_5888983329180487891-1.pdf has no publisher mark. link.pdf, n-sh-driveing.ir.pdf, nokat.pdf and tablomoshabe1.pdf contain no four-option questions.",
        },
    }
    (DATA / "tier-classification-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["totalQuestions", "tier1Count", "tier2Count", "tier3Count", "tier4Count", "tier5Count", "crossSourceDuplicateCount", "crossSourceDuplicatesInTier1", "crossSourceEquivalentCount", "chapter1Count", "otherChapterCount", "questionsWithBookReference"]}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1])
