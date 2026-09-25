"""Shared Persian text normalisation helpers for reference mapping and tiering (no OCR involved)."""
import re
import unicodedata

DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
ARABIC = str.maketrans({"ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه", "أ": "ا", "إ": "ا", "آ": "ا", "ؤ": "و"})
DIACRITICS = re.compile(r"[ً-ٰٟـ]")
NON_WORD = re.compile(r"[^\w\s]", re.UNICODE)

STOPWORDS = set("""
و در به از که این را با برای است می باشد باید کدام کدامیک کدام‌یک یک هر آن ها های یا تا اگر چه چیست چیزی بر نیز
شود شده کند کنید کرد کردن نمی هم پس بین روی زیر مقابل روبرو تابلو تابلوی تابلوهای مفهوم منظور عنوان بیانگر
گزینه صحیح غلط نظر نمونه صورت حالت مورد موارد اینکه آنکه بیشتر کمتر خود او ما شما آنها اینها چند چگونه چرا کجا کی
""".split())

def norm(value: str) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = text.translate(DIGITS).translate(ARABIC)
    text = DIACRITICS.sub("", text)
    text = text.replace("‌", " ").replace("‍", "")
    text = NON_WORD.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip().lower()

def compact(value: str) -> str:
    return norm(value).replace(" ", "")

def tokens(value: str, drop_stop=True):
    words = norm(value).split()
    return [w for w in words if not (drop_stop and w in STOPWORDS) and len(w) > 1 or w.isdigit()]

def char_ngrams(value: str, n=3):
    text = compact(value)
    return {text[i:i + n] for i in range(max(0, len(text) - n + 1))} if len(text) >= n else ({text} if text else set())

def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)

POINTER_WORDS = {"گزینه", "شکل", "تصویر", "تابلو", "تابلوی", "شماره", "مورد", "موارد", "علامت", "حالت", "الف", "ب", "ج", "د",
                 "هر", "دو", "سه", "همه", "هیچکدام", "هیچ", "کدام", "یک", "صحیح", "است", "بالا", "فوق", "و"}


def answer_kind(text: str) -> str:
    """Classify an answer as "pointer" (only points at an option/figure, e.g. «گزینه ۲», «هر دو مورد»),
    "numeric" (a bare number such as «۷۰») or "text" (a self-contained statement or sign name)."""
    words = norm(text).split()
    if not words:
        return "pointer"
    if all(word.isdigit() for word in words):
        return "numeric"
    if all(word.isdigit() or word in POINTER_WORDS for word in words):
        return "pointer"
    return "text"


def is_generic_answer(text: str) -> bool:
    """True when the answer text alone does not identify the fact (pointer or bare number)."""
    return answer_kind(text) != "text"
