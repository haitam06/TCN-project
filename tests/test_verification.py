import pandas as pd
import pytest

from src.verification import (
    check_conservation,
    compare_values,
    normalize_value,
    summarize,
    verify_corpus,
)


# ---------- Tests purs (sans detection) ----------

def test_normalize_value():
    assert normalize_value(12.0) == 12
    assert normalize_value("3.14") == 3.14
    assert normalize_value(0.1 + 0.2) == 0.3


def test_all_conserved():
    r = compare_values([12, 3.14], [3.14, 12])  # ordre ignore
    assert r["conserved"] and r["score"] == 1.0
    assert r["omitted"] == r["modified"] == r["added"] == []


def test_omitted():
    r = compare_values([12, 15], [12])
    assert r["omitted"] == [15]
    assert r["score"] == 0.5
    assert not r["conserved"]


def test_added():
    r = compare_values([12], [12, 7])
    assert r["added"] == [7]
    assert r["score"] == 0.5


def test_modified():
    r = compare_values([12], [13])
    assert r["modified"] == [(12, 13)]
    assert r["omitted"] == [] and r["added"] == []
    assert r["score"] == 0.0


def test_duplicates_are_counted():
    r = compare_values([5, 5], [5])
    assert r["omitted"] == [5]


def test_no_numbers():
    r = compare_values([], [])
    assert r["conserved"] and r["score"] == 1.0


# ---------- Tests avec la detection de Haytham ----------

def test_documented_example_fr_en():
    r = check_conservation(
        "Il y a 1 250 000 habitants.", "There are 1,250,000 inhabitants.", "fr", "en"
    )
    assert r["source_values"] == [1250000]
    assert r["conserved"]


def test_number_in_words_vs_digits():
    r = check_conservation("Il a quatre-vingt-dix-sept ans.", "He is 97 years old.", "fr", "en")
    assert r["conserved"]


def test_detects_modified_number():
    r = check_conservation("J'ai 12 pommes.", "I have 13 apples.", "fr", "en")
    assert r["modified"] == [(12, 13)]


def test_detects_omitted_number():
    r = check_conservation("J'ai 12 pommes et 7 poires.", "I have 12 apples.", "fr", "en")
    assert r["omitted"] == [7]


# ---------- Test sur un fichier ----------

def test_verify_corpus(tmp_path):
    df = pd.DataFrame(
        {
            "id": ["1", "2"],
            "lang": ["fr", "en"],
            "target_lang": ["en", "fr"],
            "text": ["J'ai 12 pommes.", "I have 12 apples."],
            "translation": ["I have 13 apples.", "J'ai 12 pommes."],
        }
    )
    src = tmp_path / "t.csv"
    out = tmp_path / "v.csv"
    df.to_csv(src, index=False, encoding="utf-8")

    res = verify_corpus(src, out)
    assert out.exists()
    assert res.loc[0, "modified"] == "12->13"
    assert str(res.loc[1, "conserved"]) == "True"

    s = summarize(res)
    assert s["phrases"] == 2 and s["phrases_conservees"] == 1