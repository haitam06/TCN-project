import os

import pandas as pd
import pytest

from src.translation import MODELS, TARGET, translate_corpus, translate_texts


def fake_translate(texts, src, tgt):
    """Faux traducteur : evite de charger le vrai modele dans les tests."""
    return [f"[{src}->{tgt}] {t}" for t in texts]


CORPUS = (
    "id,lang,type,text,numbers\n"
    "1,fr,decimal,Pi vaut 3,14.,3.14\n"
    "2,en,entier,I have 12 apples.,12\n"
)


def _write_corpus(tmp_path):
    path = tmp_path / "corpus.csv"
    path.write_text(CORPUS.replace("Pi vaut 3,14.", '"Pi vaut 3,14."'), encoding="utf-8")
    return path


def test_models_and_targets():
    assert ("fr", "en") in MODELS and ("en", "fr") in MODELS
    assert TARGET == {"fr": "en", "en": "fr"}


def test_translate_corpus_raw(tmp_path):
    out = tmp_path / "out.csv"
    df = translate_corpus(_write_corpus(tmp_path), out, mode="raw", translate_fn=fake_translate)
    assert list(df["target_lang"]) == ["en", "fr"]
    assert df.loc[0, "translation"] == "[fr->en] Pi vaut 3,14."
    assert df.loc[1, "translation"] == "[en->fr] I have 12 apples."
    assert out.exists()
    assert len(pd.read_csv(out, encoding="utf-8")) == 2


def test_translate_corpus_formats_mode(tmp_path):
    out = tmp_path / "out.csv"
    df = translate_corpus(_write_corpus(tmp_path), out, mode="formats", translate_fn=fake_translate)
    assert "3.14" in df.loc[0, "translation"]


def test_invalid_mode(tmp_path):
    with pytest.raises(ValueError):
        translate_corpus(_write_corpus(tmp_path), tmp_path / "o.csv", mode="autre")


@pytest.mark.skipif(not os.environ.get("RUN_MODEL_TESTS"), reason="test avec le vrai modele (lent)")
def test_real_model_keeps_simple_number():
    out = translate_texts(["Il y a 12 pommes."], "fr", "en")
    assert "12" in out[0]