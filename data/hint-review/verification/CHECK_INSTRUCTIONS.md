# Independent check of study hints (Persian driving-theory bank)

Each item in your file is one exam question with its keyed answer (correctOptionId / correctAnswerText), the textbook
page it was linked to (bookPage, secondaryPages, supportingText), and the study HINT another writer produced
(hint, basis = book | answer | book_conflict). Learners see the hint after answering, so a wrong hint teaches a wrong rule.

Textbook transcription (verbatim): data/book-pages.json (pages[].bookPage/text/signs/figures).
Question pictures: assets/questions/... (look when the hint depends on the picture).
The writer's rules are in data/hint-review/HINT_INSTRUCTIONS.md — read them first.

For every item decide:
- "ok": the hint agrees with the keyed answer, every fact in it is supported by the linked book page(s) or by the
  question/answer itself, it is clear, and it does not point at option numbers.
- "fix": anything wrong — contradicts the key or the book, adds an unsupported fact, misdescribes the picture,
  is misleading/ambiguous, or (for book_conflict) is not neutral. Then write a corrected hint that follows the writer's rules.
Do not change answer keys and do not judge the question itself. No OCR software; read pictures with your own vision.

Write data/hint-review/verification/verdict-N.json (same N as your file): a JSON array, one object per item:
{"id": "...", "verdict": "ok" | "fix", "problem": null | "short English description", "suggestedHint": null | "corrected Persian hint"}
Save incrementally. Finish with a short report: number of ok / fix and the kinds of problems found.

## Problems found in an earlier sample (look for these especially)
- Over-general sign rules: a visual rule stated for "any" sign that is false for other signs (e.g. "a diagonal band =
  end of restriction" is false for red-bordered prohibition signs; "a train in the triangle" also matches the tram sign).
  A rule must be true for the whole book, or be limited to the sign in question.
- Remarks about other questions or about the dataset ("the same picture appears elsewhere with another key") — not allowed
  unless the item is basis book_conflict AND the key disagrees with the book; the hint must teach the book's rule.
- Ambiguous quoting of multi-step orders (write «۳ و ۴ هم‌زمان، سپس ۲، سپس ۱», not «سپس ۲ و ۱»).
- basis book_conflict although the key actually agrees with the book (then the hint should simply teach the rule; suggest basis "book" in "problem").
