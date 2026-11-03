import re

from src.detection import NUM_RE, NUM_PATTERN, parse_digits

SPACES = r"[ \u00a0\u202f]"

# currency symbol before the number ($200) or after it (200 €)
CUR_RE = re.compile(
    r"(?<!\d)(?:"
    r"(?P<sym1>[€$£])" + SPACES + r"?(?P<num1>" + NUM_PATTERN + r")"
    r"|(?P<num2>" + NUM_PATTERN + r")" + SPACES + r"?(?P<sym2>[€$£])"
    r")(?!\d)"
)

THIN = "\u202f"   # thousands separator in French
NBSP = "\u00a0"   # space before % and currency symbols in French


def _count_decimals(s, lang):
    """How many digits are written after the decimal separator."""
    s = re.sub(SPACES, "", s)
    if lang == "fr":
        if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", s):      # 1.500 = thousands
            return len(s.split(",")[1]) if "," in s else 0
        m = re.search(r"[.,](\d+)$", s)
        return len(m.group(1)) if m else 0
    m = re.search(r"\.(\d+)$", s)
    return len(m.group(1)) if m else 0


def _has_grouping(s, lang):
    """Does the original number use thousands separators?"""
    if lang == "fr":
        return bool(re.search(SPACES + r"\d{3}", s)
                    or re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", s))
    return "," in s


def format_number(value, lang, decimals=0, grouping=True):
    """1250000 -> '1 250 000' (fr) / '1,250,000' (en)"""
    s = f"{value:,.{decimals}f}" if grouping else f"{value:.{decimals}f}"
    if lang == "fr":
        s = s.replace(",", THIN).replace(".", ",")
    return s


def _convert_amount(num, from_lang, to_lang):
    plain = re.sub(SPACES, "", num)
    if re.match(r"0\d", plain):           # 02, 007: leave unchanged (dates, codes)
        return num
    try:
        value = parse_digits(num, from_lang)
    except ValueError:                    # not valid in this language: leave it
        return num
    return format_number(value, to_lang,
                         _count_decimals(num, from_lang),
                         _has_grouping(num, from_lang))


def convert_formats(text, from_lang, to_lang):
    """Rewrite every number, percentage and currency amount in the target format."""
    if from_lang == to_lang:
        return text

    spans = []   # (start, end, replacement)

    for m in CUR_RE.finditer(text):
        num = m.group("num1") or m.group("num2")
        sym = m.group("sym1") or m.group("sym2")
        amount = _convert_amount(num, from_lang, to_lang)
        new = f"{sym}{amount}" if to_lang == "en" else f"{amount}{NBSP}{sym}"
        spans.append((m.start(), m.end(), new))

    for m in NUM_RE.finditer(text):
        if any(s <= m.start() and m.end() <= e for s, e, _ in spans):
            continue                      # already handled as a currency amount
        new = _convert_amount(m.group("num"), from_lang, to_lang)
        if m.group("pct"):
            new += f"{NBSP}%" if to_lang == "fr" else "%"
        spans.append((m.start(), m.end(), new))

    for start, end, new in sorted(spans, reverse=True):   # right to left
        text = text[:start] + new + text[end:]
    return text


if __name__ == "__main__":
    demo = [
        ("La ville compte 1 250 000 habitants.", "fr", "en"),
        ("Le prix est de 3,14 euros.", "fr", "en"),
        ("Le taux est de 15 %.", "fr", "en"),
        ("Cela coûte 1 234,56 €.", "fr", "en"),
        ("The city has 1,250,000 inhabitants.", "en", "fr"),
        ("The rate is 15%.", "en", "fr"),
        ("It costs $3.50.", "en", "fr"),
        ("Le 02/11/2026, il y avait 1500 étudiants.", "fr", "en"),
    ]
    for text, a, b in demo:
        print(f"[{a}->{b}] {text}\n        {convert_formats(text, a, b)}")