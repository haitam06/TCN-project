import pandas as pd

from src.evaluation import (
    compare_by_type,
    compare_global,
    error_details,
    frequent_errors,
    metrics,
    metrics_by,
    to_markdown,
)


def make_df():
    return pd.DataFrame(
        [
            # phrase 1 : tout est conserve
            dict(id="1", lang="fr", type="entier", text="a", translation="b",
                 n_source="1", n_target="1", n_matched="1",
                 omitted="", modified="", added="", conserved="True"),
            # phrase 2 : 12 devenu 13
            dict(id="2", lang="fr", type="entier", text="a", translation="b",
                 n_source="1", n_target="1", n_matched="0",
                 omitted="", modified="12->13", added="", conserved="False"),
            # phrase 3 : un nombre omis
            dict(id="3", lang="en", type="decimal", text="a", translation="b",
                 n_source="2", n_target="1", n_matched="1",
                 omitted="7", modified="", added="", conserved="False"),
        ]
    )


def test_metrics():
    m = metrics(make_df())
    assert m["phrases"] == 3 and m["phrases_correctes"] == 1
    assert m["nombres_source"] == 4 and m["nombres_traduction"] == 3
    assert m["vrais"] == 2 and m["omis"] == 1 and m["modifies"] == 1 and m["ajoutes"] == 0
    assert m["precision"] == 0.6667
    assert m["rappel"] == 0.5
    assert m["taux_erreur_nombres"] == 0.5


def test_metrics_by_type():
    t = metrics_by(make_df(), "type").set_index("type")
    assert t.loc["entier", "phrases"] == 2
    assert t.loc["decimal", "omis"] == 1


def test_compare_global_and_type():
    df = make_df()
    g = compare_global(df, df).set_index("metrique")
    assert g.loc["rappel", "difference"] == 0
    c = compare_by_type(df, df)
    assert set(c["type"]) == {"entier", "decimal"}


def test_error_details_and_frequency():
    df = make_df()
    err = error_details(df)
    assert len(err) == 2 and "cause" in err.columns
    freq = frequent_errors(df)
    assert {"categorie", "valeur", "occurrences"} <= set(freq.columns)
    assert len(freq) == 2


def test_empty_corpus_does_not_crash():
    empty = make_df().iloc[0:0]
    m = metrics(empty)
    assert m["phrases"] == 0 and m["rappel"] == 1.0


def test_markdown():
    md = to_markdown(pd.DataFrame({"a": [1], "b": [2]}))
    assert md.startswith("| a | b |")