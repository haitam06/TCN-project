import re

from num2words import num2words

from src.detection import detect_numbers, words_to_number, _vocab

SUPPORTED = ("fr", "en")


# ---------- 1. Number -> words ----------
def number_to_words(value, lang="fr"):
    """97 -> 'quatre-vingt-dix-sept' (fr) / 'ninety-seven' (en)"""
    if lang not in SUPPORTED:
        raise ValueError(f"Unsupported language: {lang}")
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return num2words(value, lang=lang)


# ---------- 2. Words -> number ----------
def _clean_tokens(text):
    text = text.lower().replace(",", " ")      # num2words (en) adds commas
    return [t for t in re.split(r"[\s-]+", text) if t]


def words_to_digits(text, lang="fr"):
    """'quatre-vingt-dix-sept' -> 97"""
    words, scales, connector = _vocab(lang)
    vocab = set(words) | set(scales) | {connector}
    tokens = _clean_tokens(text)
    if not tokens or any(t not in vocab for t in tokens):
        raise ValueError(f"Not a valid number in words ({lang}): {text!r}")
    return words_to_number(tokens, lang)


# ---------- 3. Inside a full sentence ----------
def _replace_spans(text, results, make_replacement):
    # go from right to left so the positions stay valid
    for r in sorted(results, key=lambda r: r["start"], reverse=True):
        text = text[:r["start"]] + make_replacement(r) + text[r["end"]:]
    return text


def digits_to_words_in_text(text, lang="fr"):
    """'Il a 97 ans.' -> 'Il a quatre-vingt-dix-sept ans.'"""
    found = [r for r in detect_numbers(text, lang) if r["kind"] == "digit"]
    return _replace_spans(text, found, lambda r: number_to_words(r["value"], lang))


def words_to_digits_in_text(text, lang="fr"):
    """'Il a quatre-vingt-dix-sept ans.' -> 'Il a 97 ans.'"""
    found = [r for r in detect_numbers(text, lang) if r["kind"] == "word"]
    return _replace_spans(text, found, lambda r: str(r["value"]))


if __name__ == "__main__":
    for n in (0, 21, 70, 80, 97, 200, 2320, 1250000):
        print(n, "|", number_to_words(n, "fr"), "|", number_to_words(n, "en"))
    print(number_to_words(3.14, "fr"))
    print(number_to_words(3.14, "en"))
    print(digits_to_words_in_text("Il y a 12 filles et 18 garçons.", "fr"))
    print(words_to_digits_in_text("Il a quatre-vingt-dix-sept ans.", "fr"))
    print(digits_to_words_in_text("There are 12 girls and 18 boys.", "en"))
    print(words_to_digits_in_text("He is ninety-seven years old.", "en"))