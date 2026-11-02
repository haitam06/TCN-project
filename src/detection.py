import re

# ---------- 1. Numbers written with digits ----------
NUM_RE = re.compile(
    r"(?<!\d)(?P<num>"
    r"\d{1,3}(?:[ \u00a0\u202f]\d{3})+(?:,\d+)?"   # 1 250 000  /  1 234,56
    r"|\d{1,3}(?:,\d{3})+(?:\.\d+)?"               # 1,250,000  /  1,234.56
    r"|\d{1,3}(?:\.\d{3})+(?:,\d+)?"               # 1.500      /  1.234,56
    r"|\d+(?:[.,]\d+)?"                            # 1500 / 3,14 / 3.14
    r")(?P<pct>[ \u00a0\u202f]?%)?(?!\d)"
)


def parse_digits(s, lang):
    """Turn '1 250 000' or '3,14' into a real number, depending on the language."""
    s = re.sub(r"[ \u00a0\u202f]", "", s)
    if lang == "fr":
        if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", s):   # 1.500 -> thousands
            s = s.replace(".", "").replace(",", ".")
        else:                                              # 3,14 -> decimal
            s = s.replace(",", ".")
    else:                                                  # English: comma = thousands
        s = s.replace(",", "")
    value = float(s)
    return int(value) if value.is_integer() else value


# ---------- 2. Numbers written in words ----------
FR_WORDS = {
    "zéro": 0, "un": 1, "une": 1, "deux": 2, "trois": 3, "quatre": 4, "cinq": 5,
    "six": 6, "sept": 7, "huit": 8, "neuf": 9, "dix": 10, "onze": 11, "douze": 12,
    "treize": 13, "quatorze": 14, "quinze": 15, "seize": 16,
    "vingt": 20, "vingts": 20, "trente": 30, "quarante": 40,
    "cinquante": 50, "soixante": 60,
}
FR_SCALES = {
    "cent": 100, "cents": 100, "mille": 1000,
    "million": 10**6, "millions": 10**6, "milliard": 10**9, "milliards": 10**9,
}
EN_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}
EN_SCALES = {"hundred": 100, "thousand": 1000, "million": 10**6, "billion": 10**9}

WORD_RE = re.compile(r"[A-Za-zÀ-ÿ]+(?:-[A-Za-zÀ-ÿ]+)*")


def _vocab(lang):
    if lang == "fr":
        return FR_WORDS, FR_SCALES, "et"
    return EN_WORDS, EN_SCALES, "and"


def words_to_number(tokens, lang):
    """['quatre','vingt','dix','sept'] -> 97"""
    words, scales, connector = _vocab(lang)
    total = current = 0
    prev = None
    for tok in tokens:
        if tok == connector:
            continue
        if tok in words:
            if lang == "fr" and tok in ("vingt", "vingts") and prev == "quatre":
                current += 76            # quatre (4) + 76 = quatre-vingt (80)
            else:
                current += words[tok]
        else:
            scale = scales[tok]
            if scale == 100:
                current = (current or 1) * 100
            else:
                total += (current or 1) * scale
                current = 0
        prev = tok
    return total + current


def _detect_words(text, lang):
    words, scales, connector = _vocab(lang)
    vocab = set(words) | set(scales) | {connector}

    # 1) keep only the words made of number-words (e.g. 'quatre-vingt-dix-sept')
    candidates = [m for m in WORD_RE.finditer(text)
                  if all(p in vocab for p in m.group(0).lower().split("-"))]

    # 2) group candidates that are separated by exactly one space
    groups, current = [], []
    for m in candidates:
        if current and text[current[-1].end():m.start()] == " ":
            current.append(m)
        else:
            if current:
                groups.append(current)
            current = [m]
    if current:
        groups.append(current)

    results = []
    for g in groups:
        # remove 'et' / 'and' at the start or end of a group
        while g and g[0].group(0).lower() == connector:
            g.pop(0)
        while g and g[-1].group(0).lower() == connector:
            g.pop()
        if not g:
            continue
        tokens = [p for m in g for p in m.group(0).lower().split("-")]
        if tokens in (["un"], ["une"], ["one"]):   # article / pronoun, not a number
            continue
        start, end = g[0].start(), g[-1].end()
        results.append({
            "text": text[start:end],
            "value": words_to_number(tokens, lang),
            "start": start, "end": end, "kind": "word",
        })
    return results


# ---------- 3. Main function ----------
def detect_numbers(text, lang="fr"):
    """Return all numbers found in text, sorted by position."""
    results = []
    for m in NUM_RE.finditer(text):
        results.append({
            "text": m.group(0),
            "value": parse_digits(m.group("num"), lang),
            "start": m.start(), "end": m.end(),
            "kind": "percent" if m.group("pct") else "digit",
        })
    results.extend(_detect_words(text, lang))
    return sorted(results, key=lambda r: r["start"])


if __name__ == "__main__":
    demo = [
        ("Il y a 12 filles et 18 garçons.", "fr"),
        ("La ville compte 1 250 000 habitants.", "fr"),
        ("Le prix est de 3,14 euros, soit 15 % de plus.", "fr"),
        ("Il a quatre-vingt-dix-sept ans.", "fr"),
        ("The city has 1,250,000 inhabitants.", "en"),
        ("He is ninety-seven years old.", "en"),
    ]
    for text, lang in demo:
        print(text)
        for r in detect_numbers(text, lang):
            print("   ", r["kind"], "|", repr(r["text"]), "->", r["value"])