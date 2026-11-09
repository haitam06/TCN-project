import pandas as pd
import pytest

from src.detection import detect_numbers


def values(text, lang):
    return [r["value"] for r in detect_numbers(text, lang)]


# ----- digits -----
def test_integer():
    assert values("Il y a 1500 étudiants.", "fr") == [1500]

def test_french_thousands_space():
    assert values("La ville compte 1 250 000 habitants.", "fr") == [1250000]

def test_french_decimal():
    assert values("Le prix est de 3,14 euros.", "fr") == [3.14]

def test_english_thousands_comma():
    assert values("The city has 1,250,000 inhabitants.", "en") == [1250000]

def test_english_decimal():
    assert values("The price is 3.14 dollars.", "en") == [3.14]

def test_several_numbers():
    assert values("Il y a 12 filles et 18 garçons.", "fr") == [12, 18]

# ----- percentages -----
def test_percent_fr():
    result = detect_numbers("Le taux est de 15 %.", "fr")
    assert result[0]["value"] == 15 and result[0]["kind"] == "percent"

def test_percent_en():
    result = detect_numbers("The rate is 15%.", "en")
    assert result[0]["value"] == 15 and result[0]["kind"] == "percent"

# ----- words -----
@pytest.mark.parametrize("text,expected", [
    ("Il a quatre-vingt-dix-sept ans.", 97),
    ("Elle a acheté soixante-dix livres.", 70),
    ("Il y a deux cents élèves.", 200),
    ("Il a vingt et un ans.", 21),
    ("Il y a trois millions d'habitants.", 3000000),
    ("Il y a deux mille trois cent vingt places.", 2320),
])
def test_french_words(text, expected):
    assert values(text, "fr") == [expected]

@pytest.mark.parametrize("text,expected", [
    ("He is ninety-seven years old.", 97),
    ("She bought seventy books.", 70),
    ("There are two hundred students.", 200),
    ("One hundred and twenty-three thousand people came.", 123000),
])
def test_english_words(text, expected):
    assert values(text, "en") == [expected]

def test_article_un_is_not_a_number():
    assert values("Il a un livre.", "fr") == []

# ----- the whole corpus -----
df = pd.read_csv("data/corpus.csv", encoding="utf-8")

@pytest.mark.parametrize("row", df.to_dict("records"), ids=lambda r: f"corpus-{r['id']}")
def test_corpus(row):
    expected = sorted(float(x) for x in str(row["numbers"]).split("|"))
    found = sorted(float(v) for v in values(row["text"], row["lang"]))
    assert found == expected