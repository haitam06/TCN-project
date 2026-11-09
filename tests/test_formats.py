import pandas as pd
import pytest

from src.detection import detect_numbers
from src.formats import convert_formats, format_number

THIN, NBSP = "\u202f", "\u00a0"


# ----- thousands and decimals -----
def test_thousands_fr_to_en():
    assert convert_formats("La ville compte 1 250 000 habitants.", "fr", "en") == \
        "La ville compte 1,250,000 habitants."

def test_thousands_en_to_fr():
    assert convert_formats("The city has 1,250,000 inhabitants.", "en", "fr") == \
        f"The city has 1{THIN}250{THIN}000 inhabitants."

def test_decimal_fr_to_en():
    assert convert_formats("Le prix est de 3,14 euros.", "fr", "en") == \
        "Le prix est de 3.14 euros."

def test_decimal_en_to_fr():
    assert convert_formats("The price is 3.14 dollars.", "en", "fr") == \
        "The price is 3,14 dollars."

def test_thousands_and_decimals():
    assert convert_formats("Total : 1 234,56", "fr", "en") == "Total : 1,234.56"
    assert convert_formats("Total: 1,234.56", "en", "fr") == f"Total: 1{THIN}234,56"


# ----- things that must NOT change -----
def test_no_grouping_stays_without_grouping():
    assert convert_formats("Il y a 1500 étudiants.", "fr", "en") == "Il y a 1500 étudiants."

def test_year_unchanged():
    assert convert_formats("En 2026, il y avait 12 filles.", "fr", "en") == \
        "En 2026, il y avait 12 filles."

def test_date_unchanged():
    assert convert_formats("Le 02/11/2026 à 14h30.", "fr", "en") == "Le 02/11/2026 à 14h30."

def test_same_language_unchanged():
    assert convert_formats("Il y a 1 250 000 habitants.", "fr", "fr") == \
        "Il y a 1 250 000 habitants."


# ----- percentages -----
def test_percent_fr_to_en():
    assert convert_formats("Le taux est de 15 %.", "fr", "en") == "Le taux est de 15%."

def test_percent_en_to_fr():
    assert convert_formats("The rate is 15%.", "en", "fr") == f"The rate is 15{NBSP}%."


# ----- currencies -----
def test_currency_fr_to_en():
    assert convert_formats("Cela coûte 1 234,56 €.", "fr", "en") == "Cela coûte €1,234.56."

def test_currency_en_to_fr():
    assert convert_formats("It costs $3.50.", "en", "fr") == f"It costs 3,50{NBSP}$."

def test_currency_integer_en_to_fr():
    assert convert_formats("It costs $200.", "en", "fr") == f"It costs 200{NBSP}$."


# ----- format_number -----
def test_format_number():
    assert format_number(1250000, "fr") == f"1{THIN}250{THIN}000"
    assert format_number(1250000, "en") == "1,250,000"
    assert format_number(3.5, "fr", decimals=2) == "3,50"


# ----- the value must never change (whole corpus) -----
df = pd.read_csv("data/corpus.csv", encoding="utf-8")

@pytest.mark.parametrize("row", df.to_dict("records"), ids=lambda r: f"corpus-{r['id']}")
def test_corpus_values_preserved(row):
    src = row["lang"]
    dst = "en" if src == "fr" else "fr"
    before = [r["value"] for r in detect_numbers(row["text"], src) if r["kind"] != "word"]
    converted = convert_formats(row["text"], src, dst)
    after = [r["value"] for r in detect_numbers(converted, dst) if r["kind"] != "word"]
    assert before == after, f"{row['text']!r} -> {converted!r}"