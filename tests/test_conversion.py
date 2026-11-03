import pytest

from src.conversion import (
    number_to_words,
    words_to_digits,
    digits_to_words_in_text,
    words_to_digits_in_text,
)


# ----- number -> words -----
@pytest.mark.parametrize("value,expected", [
    (97, "quatre-vingt-dix-sept"),
    (70, "soixante-dix"),
    (21, "vingt et un"),
    (200, "deux cents"),
])
def test_number_to_words_fr(value, expected):
    assert number_to_words(value, "fr") == expected


@pytest.mark.parametrize("value,expected", [
    (97, "ninety-seven"),
    (70, "seventy"),
    (12, "twelve"),
])
def test_number_to_words_en(value, expected):
    assert number_to_words(value, "en") == expected


def test_unsupported_language():
    with pytest.raises(ValueError):
        number_to_words(5, "de")


# ----- words -> number -----
@pytest.mark.parametrize("text,lang,expected", [
    ("quatre-vingt-dix-sept", "fr", 97),
    ("soixante et onze", "fr", 71),
    ("deux mille trois cent vingt", "fr", 2320),
    ("ninety-seven", "en", 97),
    ("one hundred and twenty-three thousand", "en", 123000),
    ("one million, two hundred and fifty thousand", "en", 1250000),
])
def test_words_to_digits(text, lang, expected):
    assert words_to_digits(text, lang) == expected


def test_words_to_digits_invalid():
    with pytest.raises(ValueError):
        words_to_digits("bonjour", "fr")


# ----- round trip: number -> words -> number must give the same number -----
@pytest.mark.parametrize("lang", ["fr", "en"])
def test_round_trip(lang):
    values = list(range(0, 1000)) + [1000, 1001, 1100, 2320, 12345, 80000,
                                     1250000, 3000000, 1000000000]
    for n in values:
        words = number_to_words(n, lang)
        assert words_to_digits(words, lang) == n, f"{n} -> {words!r}"


# ----- inside sentences -----
def test_sentence_digits_to_words_fr():
    assert digits_to_words_in_text("Il y a 12 filles et 18 garçons.", "fr") == \
        "Il y a douze filles et dix-huit garçons."

def test_sentence_digits_to_words_en():
    assert digits_to_words_in_text("There are 12 girls and 18 boys.", "en") == \
        "There are twelve girls and eighteen boys."

def test_sentence_words_to_digits_fr():
    assert words_to_digits_in_text("Il a quatre-vingt-dix-sept ans.", "fr") == \
        "Il a 97 ans."

def test_sentence_words_to_digits_en():
    assert words_to_digits_in_text("He is ninety-seven years old.", "en") == \
        "He is 97 years old."