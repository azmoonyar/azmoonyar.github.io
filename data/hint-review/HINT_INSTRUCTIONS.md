# Short study hints for a driving-theory question bank (Persian)

Each question of a real Iranian driving-theory exam bank needs ONE short study hint (نکتهٔ آموزشی) that a learner
sees after answering. The hint explains WHY the keyed answer is right, so the learner remembers the rule next time.

## Inputs
- Your batch: batch-NN.json (a working file, not kept) — a JSON array. Per question: id, question, options, correctOptionId,
  correctAnswerText, image (path relative to the repository root, or null), imageAlt, bookPage (printed page of the official
  textbook), secondaryPages, bookReference (section), supportingText (verbatim excerpt of that page),
  referenceConfidence, reviewNote (notes of the reviewer who linked the question to the book),
  answerKeyConflictsWithBook (true = the book seems to disagree with the key), sourceTextIssue (typo/garbled text in the question).
- The textbook, transcribed verbatim: data/book-pages.json → {"pages":[{bookPage, headings, text, signs:[{caption,description}], figures}]}.
  Read the page (and secondary pages) of every question before writing its hint; grep it for keywords when useful.
  Sign colours/shapes are explained on book pages 20–21; sign catalogue pages 28–45.
- Question pictures: assets/questions/... Look at the picture (Read tool) when the hint depends on it —
  always for questions whose answer is only an option number («گزینه ۲») or a colour/position in a figure.

## Rules
1. Persian, 1–2 short sentences, ideally ≤ 150 characters, never more than 190. Use Persian digits (۰–۹).
2. Explain the rule / fact / sign meaning behind the KEYED answer. Do not just repeat the question; give the reason,
   the rule, or the visual cue to remember (e.g. «مثلث با حاشیهٔ قرمز = هشدار؛ خودروی لغزان یعنی «راه لغزنده».»).
3. Must agree with the keyed answer (correctOptionId). Never say or imply that another option is correct.
4. Ground the hint in the textbook page(s). Use the book's numbers and terms. Do NOT add facts that are neither in the
   book pages nor in the question/correct answer. If the book does not cover the point (referenceConfidence low /
   not_found), explain using only what the question and its correct answer themselves state, and set basis "answer".
5. If answerKeyConflictsWithBook is true: give the keyed answer's idea briefly and add what the book says, e.g.
   «پاسخ نمونه‌آزمون‌ها «۷۰» است، ولی کتاب آموزشی سقف ۶۰ کیلومتر را ذکر کرده است.» Set basis "book_conflict".
   Keep it neutral and short; the learner should know the discrepancy exists.
6. Options that are pictures («گزینه ۱» …): describe the correct sign/picture by its look and meaning, never by its
   number or position (the learner must recognise the sign itself).
7. «کدام … نیست / صحیح نمی‌باشد» questions: explain why the keyed option is the exception.
8. No option letters/numbers (الف/ب/گزینه ۲), no English, no emoji, no markdown, no quotation of long book passages
   (the verbatim excerpt is shown separately); do not start with «پاسخ درست …» every time — vary naturally.
9. sourceTextIssue: write the hint for the evidently intended question; do not repeat the typo.
10. No OCR software; read pictures with your own vision only.

## Output
Write data/hint-review/hints-NN.json (same NN as your batch): a JSON array, one object per question, same order:
{"id": "...", "hint": "…", "basis": "book" | "answer" | "book_conflict", "note": null | "short note (e.g. why basis is answer)"}
Every id exactly once. Save progress incrementally (rewrite the file every ~20 questions; if it exists at start, keep
its entries and continue — resume support). Before finishing, check programmatically: all ids present, every hint
non-empty and ≤ 190 characters, contains no Latin letters other than unavoidable abbreviations (e.g. ABS).
Finish with a very short report: counts per basis, anything you could not do.
