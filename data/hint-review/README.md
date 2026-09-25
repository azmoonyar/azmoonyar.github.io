# Study hints: sources and review record

`data/question-hints.js` (one short Persian hint per question, shown after answering) is generated from this folder:

```
node scripts/tiering/dump_bank.mjs BANK.json
python3 scripts/tiering/merge_hints.py BANK.json data/hint-review
```

- `hints-01.json` … `hints-20.json`: the hints, one entry per question (`id`, `hint`, `basis`, `note`, `checked`).
  - `basis` is `book` (grounded in the linked textbook page), `answer` (explains the keyed answer only), or `book_conflict` (the keyed answer disagrees with the textbook; the hint says so neutrally, and the question is listed in `data/manual-review.json`).
  - `note` starting with "revised after independent check" means the second reviewer's correction was applied.
  - `editedAfterCheck` marks hints the editor reworded after reading the verdict; `scripts/tiering/apply_hint_verdicts.py` leaves those alone.
- `HINT_INSTRUCTIONS.md`: the writing rules (grounded in the book page, 190 characters or less, no option numbers, no remarks about other questions, and so on).
- `verification/`: the independent second check of every hint against the book page, the answer key and the question picture.
  - `CHECK_INSTRUCTIONS.md` holds the checking rules.
  - `verdict-1..3.json` cover the first 180-hint sample; `verdict-full-01..16.json` cover the other 1360.
  - Each verdict is `ok`, or `fix` with the problem and a corrected hint.

Hints of questions removed at the owner's request (`data/question-removals.js`) stay here for the record and are left out of `data/question-hints.js`.

No hint changes a question, an option or an answer key. Hints were written from the visual book transcription (`data/book-pages.json`) and the page renders, never with OCR.
