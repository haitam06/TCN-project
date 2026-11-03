# TCN-project
Traduction et conservation des nombres

## About

Project TCN: translation and conservation of numbers (French / English). Team R&R.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 -m pytest -v
```

## Project structure

```
data/    test corpus (corpus.csv)
src/     detection.py, conversion.py, formats.py
tests/   pytest tests
docs/    documentation and report
```

## Number tools (`src/`)

| Function | File | What it does |
|---|---|---|
| `detect_numbers(text, lang)` | `detection.py` | Finds all numbers (digits, %, words). Returns a list of dicts: `text`, `value`, `start`, `end`, `kind` |
| `number_to_words(value, lang)` | `conversion.py` | `97` -> `quatre-vingt-dix-sept` |
| `words_to_digits(text, lang)` | `conversion.py` | `ninety-seven` -> `97` |
| `digits_to_words_in_text(text, lang)` | `conversion.py` | Replaces digits by words in a sentence |
| `words_to_digits_in_text(text, lang)` | `conversion.py` | Replaces words by digits in a sentence |
| `convert_formats(text, from_lang, to_lang)` | `formats.py` | `1 234,56 €` -> `€1,234.56` (fr <-> en) |

Languages: `"fr"` and `"en"`.

## Example

```python
from src.detection import detect_numbers

source = detect_numbers("Il y a 1 250 000 habitants.", "fr")
target = detect_numbers("There are 1,250,000 inhabitants.", "en")
print([r["value"] for r in source] == [r["value"] for r in target])   # True
```

## Limits

- Arabic is not supported yet.
- Dates and units are left unchanged.
- Currencies are reformatted but not converted (no exchange rates).
- `1.500` in French is read as 1500 (ambiguous by nature).