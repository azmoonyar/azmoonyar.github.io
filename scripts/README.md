# Scripts

Run everything from the repository root. Node 18+ for `.mjs`, Python 3 for `.py`, macOS (PDFKit / CoreText) for `.swift`.

| Folder / file | What it does | Needs local sources? |
|---|---|---|
| `tiering/validate_study_bank.mjs` | End-to-end check of the question bank: SHA-256 fingerprint of every question against `data/question-bank-baseline.json`, levels, book references, hints, and simulated exam sessions. Writes `data/study-validation-report.json`. | No (the verbatim-excerpt check runs only when `data/book-pages.json` is present) |
| `check_web_app.mjs` | Manifest, icons, install tags, every file the page loads (the offline cache follows the same references), and search / link-preview tags, sitemap, robots.txt and 404 page pointing at the published address. | No |
| `build_brand_assets.mjs` | Logo, app icons, favicon, README lockups and the GitHub social preview, all from one geometry, rendered with headless Chrome. | No (Chrome, internet for the web font) |
| `tiering/` | Study pipeline: book references, importance levels, hints, the manual-review list. Rebuild order: `dump_bank.mjs` → `merge_references.py` → `build_metadata.py` → `dump_bank.mjs` → `build_manual_review.py` → `merge_hints.py` → `validate_study_bank.mjs` (arguments in each file's header). | Yes: `data/book-pages.json` |
| `assets/` | Documented repairs of question pictures (`fix_*.py`) and their report (`build_asset_fix_report.py` → `data/asset-fix-report.json`). | Yes: page renders and originals in `tmp/` |
| `extraction/` | One-off scripts that built the question bank from the sample-exam PDFs: page exports, native text layer, picture crops. Kept as a record; they read page renders from temporary folders that no longer exist. | Yes: the PDFs |
| `render_pdf_pages.swift` | Renders PDF pages to PNG for visual review (no OCR anywhere in this project). | Yes: the PDFs |

The PDFs (`pdf's/`), the textbook transcription (`data/book-pages.json`) and working files (`tmp/`) are not in the repository.
