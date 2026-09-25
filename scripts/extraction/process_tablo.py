#!/usr/bin/env python3
"""Parse tablo.pdf's native text, read its colored answer marks, and crop sign art.

This script performs no OCR. Text and geometry come from PDFKit JSON, while Pillow
is used only for pixel-colour checks and cropping already-rendered pages.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops


QUESTION_RE = re.compile(r"^(\d+)\s*-\s*(.+)$")
OPTION_RE = re.compile(r"^([1-4])\s*[()]\s*(.*)$")
IDS = ("a", "b", "c", "d")


def clean(text: str) -> str:
    text = " ".join(text.replace("\u200c", "‌").split())
    repairs = {
        "سؤاات": "سؤالات",
        "عائم": "علائم",
        "سرباایی": "سربالایی",
        "آات": "آلات",
        "عامت": "علامت",
        "کواک": "کولاک",
    }
    for bad, good in repairs.items():
        text = text.replace(bad, good)
    return text


def parse_questions(pages: list[dict]) -> list[dict]:
    questions: list[dict] = []
    current = None
    current_option = None

    for page in pages:
        for line in sorted(page["lines"], key=lambda item: -item["y"]):
            text = clean(line["text"])
            if not text or text == "www.driveing.ir":
                continue

            if current is not None and text.startswith("-") and "مفهوم تابلوی روبرو" in text:
                questions.append(current)
                current = {
                    "number": current["number"] + 1,
                    "page": page["page"],
                    "text": text.lstrip("- "),
                    "options": [],
                    "lines": [{**line, "page": page["page"], "kind": "question"}],
                }
                current_option = None
                continue

            if current is not None:
                fused_prefix = f'{current["number"]}1)'
                if text.startswith(fused_prefix):
                    text = text[len(str(current["number"])):]

            question_match = QUESTION_RE.match(text)
            option_match = OPTION_RE.match(text)

            if question_match:
                number = int(question_match.group(1))
                if 1 <= number <= 301:
                    if current is not None:
                        questions.append(current)
                    current = {
                        "number": number,
                        "page": page["page"],
                        "text": question_match.group(2),
                        "options": [],
                        "lines": [],
                    }
                    current_option = None
                    current["lines"].append({**line, "page": page["page"], "kind": "question"})
                    continue

            if current is None:
                continue

            if option_match:
                option_number = int(option_match.group(1))
                if option_number == len(current["options"]) + 1:
                    current["options"].append(option_match.group(2))
                    current_option = option_number - 1
                    current["lines"].append({**line, "page": page["page"], "kind": "option", "option": option_number})
                    continue

            # PDFKit sometimes splits a wrapped question or option across lines.
            if text.startswith(("سؤالات بخش", "عائم راهنمایی", "علائم راهنمایی")):
                continue
            if current_option is None:
                current["text"] = clean(current["text"] + " " + text)
            elif current_option < len(current["options"]):
                current["options"][current_option] = clean(current["options"][current_option] + " " + text)

    if current is not None:
        questions.append(current)
    return questions


def is_answer_colour(pixel: tuple[int, ...]) -> bool:
    r, g, b = pixel[:3]
    red = r > 105 and r > g * 1.45 and r > b * 1.45
    green = g > 65 and g > r * 1.18 and g > b * 1.08
    return red or green


def load_image(render_dir: Path, page_number: int, cache: dict[int, Image.Image]) -> Image.Image:
    if page_number not in cache:
        cache[page_number] = Image.open(render_dir / f"page-{page_number:03}.png").convert("RGB")
    return cache[page_number]


def answer_for(question: dict, pages_by_number: dict[int, dict], render_dir: Path, cache: dict[int, Image.Image]) -> tuple[str | None, dict[int, int]]:
    scores: dict[int, int] = {}
    for line in question["lines"]:
        if line.get("kind") != "option":
            continue
        page_number = line["page"]
        page = pages_by_number[page_number]
        image = load_image(render_dir, page_number, cache)
        scale_y = image.height / page["height"]
        expected_y = (page["height"] - (line["y"] + line["height"] / 2)) * scale_y
        y0 = max(0, round(expected_y - 14 * scale_y))
        y1 = min(image.height, round(expected_y + 14 * scale_y))
        x0 = round(image.width * 0.88)
        pixels = np.asarray(image)[y0:y1, x0:image.width, :3].astype(np.int16)
        red = (pixels[:, :, 0] > 105) & (pixels[:, :, 0] > pixels[:, :, 1] * 1.45) & (pixels[:, :, 0] > pixels[:, :, 2] * 1.45)
        green = (pixels[:, :, 1] > 65) & (pixels[:, :, 1] > pixels[:, :, 0] * 1.18) & (pixels[:, :, 1] > pixels[:, :, 2] * 1.08)
        score = int(np.count_nonzero(red | green))
        scores[line["option"]] = score

    if not scores:
        return None, scores
    option, score = max(scores.items(), key=lambda item: item[1])
    # At 120 dpi every source mark contributes dozens of coloured pixels.
    if score < 8:
        return None, scores
    ordered = sorted(scores.values(), reverse=True)
    if len(ordered) > 1 and ordered[1] >= score * 0.72:
        return None, scores
    return IDS[option - 1], scores


def nonwhite_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    pixels = np.asarray(image.convert("RGB"))[:, :, :3].astype(np.int16)
    colourful = (pixels.max(axis=2) - pixels.min(axis=2) > 24) & (pixels.min(axis=2) < 235)
    dark = np.all(pixels < 105, axis=2)
    ys, xs = np.nonzero(colourful | dark)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def crop_question_image(question: dict, questions: list[dict], pages_by_number: dict[int, dict], render_dir: Path, assets_dir: Path, cache: dict[int, Image.Image]) -> str | None:
    number = question["number"]
    page_number = question["page"]
    candidate_pages = sorted({page_number, *(line["page"] for line in question["lines"])})
    if page_number + 1 not in candidate_pages:
        candidate_pages.append(page_number + 1)

    for candidate in candidate_pages:
        page = pages_by_number.get(candidate)
        image_path = render_dir / f"page-{candidate:03}.png"
        if page is None or not image_path.exists():
            continue
        image = load_image(render_dir, candidate, cache)
        scale_y = image.height / page["height"]

        q_lines = [line for line in question["lines"] if line["page"] == candidate]
        if q_lines:
            top = min((page["height"] - (line["y"] + line["height"])) * scale_y for line in q_lines)
            bottom = max((page["height"] - line["y"]) * scale_y for line in q_lines)
            top = max(0, top - 28 * scale_y)
            bottom = min(image.height, bottom + 28 * scale_y)
        else:
            top, bottom = 0, image.height * 0.25

        # Use neighbouring question headers as stronger vertical band boundaries.
        headers = []
        for other in questions:
            for line in other["lines"]:
                if line.get("kind") == "question" and line["page"] == candidate:
                    headers.append(((page["height"] - (line["y"] + line["height"])) * scale_y, other["number"]))
        headers.sort()
        own_headers = [y for y, n in headers if n == number]
        if own_headers:
            top = max(0, own_headers[0] - 18 * scale_y)
            later = [y for y, n in headers if y > own_headers[0] + 2]
            bottom = (later[0] - 20 * scale_y) if later else image.height
        elif candidate != page_number:
            bottom = (headers[0][0] - 20 * scale_y) if headers else image.height * 0.25

        left = round(image.width * 0.055)
        right = round(image.width * 0.515)
        top_px = max(0, round(top))
        bottom_px = min(image.height, max(top_px + 1, round(bottom)))
        band = image.crop((left, top_px, right, bottom_px))
        bbox = nonwhite_bbox(band)
        if bbox is None:
            continue
        x0, y0, x1, y1 = bbox
        if (x1 - x0) * (y1 - y0) < 850:
            continue
        pad = round(min(image.width, image.height) * 0.012)
        x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
        x1, y1 = min(band.width, x1 + pad), min(band.height, y1 + pad)
        crop = band.crop((x0, y0, x1, y1))
        output_name = f"q-src-tablo-p{page_number:03}-n{number:03}.png"
        crop.save(assets_dir / output_name, optimize=True)
        return f"./assets/questions/{output_name}"
    return None


def js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def write_module(questions: list[dict], output: Path) -> None:
    lines = [
        'const I=["a","b","c","d"];',
        'const q=(p,n,t,o,a,x=null)=>({id:`q-tablo-p${String(p).padStart(3,"0")}-n${String(n).padStart(3,"0")}`,text:t,options:o.map((text,i)=>({id:I[i],text})),correctOptionId:a,image:x?{src:x,alt:"تصویر تابلوی مربوط به سؤال"}:null,isImportant:false,bookPage:null,bookReference:null,explanation:null,sources:[{pdf:"tablo.pdf",page:p,questionNumber:n}],duplicateCount:0});',
        'export const questionsTabloPages33To118=[',
    ]
    for item in questions:
        answer = js_string(item["answer"]) if item["answer"] else "null"
        image = js_string(item["image"]) if item["image"] else "null"
        args = ",".join([
            str(item["page"]), str(item["number"]), js_string(item["text"]),
            json.dumps(item["options"], ensure_ascii=False), answer, image,
        ])
        lines.append(f"q({args}),")
    lines.append("];\n")
    output.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lines", type=Path, required=True)
    parser.add_argument("--render-dir", type=Path, required=True)
    parser.add_argument("--assets-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    pages = json.loads(args.lines.read_text(encoding="utf-8"))
    pages_by_number = {page["page"]: page for page in pages}
    questions = parse_questions(pages)
    args.assets_dir.mkdir(parents=True, exist_ok=True)
    image_cache: dict[int, Image.Image] = {}

    report = {"questionCount": len(questions), "incomplete": [], "unresolved": [], "answerScores": {}}
    for item in questions:
        answer, scores = answer_for(item, pages_by_number, args.render_dir, image_cache)
        item["answer"] = answer
        report["answerScores"][str(item["number"])] = scores
        if answer is None:
            report["unresolved"].append(item["number"])
        if len(item["options"]) != 4 or any(not option for option in item["options"]):
            report["incomplete"].append({"number": item["number"], "page": item["page"], "options": item["options"]})
        item["image"] = crop_question_image(item, questions, pages_by_number, args.render_dir, args.assets_dir, image_cache)

    write_module(questions, args.output)
    report["imageCount"] = sum(bool(item["image"]) for item in questions)
    report["resolvedCount"] = sum(bool(item["answer"]) for item in questions)
    report["sequence"] = [item["number"] for item in questions]
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key not in ("answerScores", "sequence")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
