"""Evaluation de la conservation des nombres sur tout le corpus.

Compare deux configurations :
  - raw     : traduction du texte tel quel (sans le module de Haytham)
  - formats : traduction apres convert_formats() de Haytham (avec le module)
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd


# ---------- Chargement et preparation ----------

def load_verification(path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8", dtype=str, keep_default_na=False)


def _count(cell) -> int:
    return len([x for x in str(cell).split("|") if x]) if cell else 0


def _prep(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for col in ("n_source", "n_target", "n_matched"):
        d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0).astype(int)
    d["n_omitted"] = d["omitted"].map(_count).astype(int)
    d["n_modified"] = d["modified"].map(_count).astype(int)
    d["n_added"] = d["added"].map(_count).astype(int)
    d["ok"] = d["conserved"].astype(str) == "True"
    return d

def _ratio(a: float, b: float) -> float:
    return round(a / b, 4) if b else 1.0


# ---------- Metriques ----------

def metrics(df: pd.DataFrame) -> dict:
    """Metriques globales d'un ensemble de lignes de verification."""
    if len(df) == 0:
        return {
            "phrases": 0,
            "phrases_correctes": 0,
            "taux_phrases_correctes": 1.0,
            "nombres_source": 0,
            "nombres_traduction": 0,
            "vrais": 0,
            "omis": 0,
            "modifies": 0,
            "ajoutes": 0,
            "precision": 1.0,
            "rappel": 1.0,
            "f1": 1.0,
            "taux_erreur_nombres": 0.0,
        }
    d = _prep(df)
    tp = int(d["n_matched"].sum())
    n_src = int(d["n_source"].sum())
    n_tgt = int(d["n_target"].sum())
    omitted = int(d["n_omitted"].sum())
    modified = int(d["n_modified"].sum())
    added = int(d["n_added"].sum())
    errors = omitted + modified + added

    precision = _ratio(tp, n_tgt)
    recall = _ratio(tp, n_src)
    f1 = round(2 * precision * recall / (precision + recall), 4) if (precision + recall) else 0.0
    return {
        "phrases": len(d),
        "phrases_correctes": int(d["ok"].sum()),
        "taux_phrases_correctes": _ratio(int(d["ok"].sum()), len(d)),
        "nombres_source": n_src,
        "nombres_traduction": n_tgt,
        "vrais": tp,
        "omis": omitted,
        "modifies": modified,
        "ajoutes": added,
        "precision": precision,
        "rappel": recall,
        "f1": f1,
        "taux_erreur_nombres": _ratio(errors, tp + errors),
    }


def metrics_by(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Metriques par valeur d'une colonne (type, lang...)."""
    rows = []
    for value, sub in df.groupby(column, sort=True):
        row = {column: value}
        row.update(metrics(sub))
        rows.append(row)
    return pd.DataFrame(rows)


def compare_global(raw: pd.DataFrame, fmt: pd.DataFrame) -> pd.DataFrame:
    """Tableau 'sans module' / 'avec module' / difference."""
    m_raw, m_fmt = metrics(raw), metrics(fmt)
    rows = []
    for key in m_raw:
        a, b = m_raw[key], m_fmt[key]
        diff = round(b - a, 4)
        rows.append({"metrique": key, "sans_module": a, "avec_module": b, "difference": diff})
    return pd.DataFrame(rows)


def compare_by_type(raw: pd.DataFrame, fmt: pd.DataFrame) -> pd.DataFrame:
    """Par type de nombre : phrases correctes, rappel et nombre d'erreurs, sans / avec."""
    types = sorted(set(raw["type"]) | set(fmt["type"]))
    rows = []
    for t in types:
        a = metrics(raw[raw["type"] == t])
        b = metrics(fmt[fmt["type"] == t])
        rows.append(
            {
                "type": t,
                "phrases": a["phrases"],
                "correctes_sans": a["phrases_correctes"],
                "correctes_avec": b["phrases_correctes"],
                "rappel_sans": a["rappel"],
                "rappel_avec": b["rappel"],
                "erreurs_sans": a["omis"] + a["modifies"] + a["ajoutes"],
                "erreurs_avec": b["omis"] + b["modifies"] + b["ajoutes"],
            }
        )
    return pd.DataFrame(rows)


# ---------- Analyse des erreurs ----------

def error_details(df: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par phrase en erreur ; la colonne 'cause' est a remplir a la main."""
    d = _prep(df)
    bad = d[~d["ok"]].copy()
    cols = ["id", "lang", "type", "text", "translation", "omitted", "modified", "added"]
    out = bad[cols].copy()
    out["cause"] = ""
    return out.reset_index(drop=True)


def frequent_errors(df: pd.DataFrame, top: int = 10) -> pd.DataFrame:
    """Erreurs les plus frequentes : categorie + valeur (ex. modifie 1500->15)."""
    counter: Counter = Counter()
    for _, r in df.iterrows():
        for cat, col in (("omis", "omitted"), ("modifie", "modified"), ("ajoute", "added")):
            for item in str(r[col]).split("|"):
                if item:
                    counter[(cat, item)] += 1
    rows = [{"categorie": c, "valeur": v, "occurrences": n} for (c, v), n in counter.most_common(top)]
    return pd.DataFrame(rows, columns=["categorie", "valeur", "occurrences"])


# ---------- Sortie ----------

def to_markdown(df: pd.DataFrame) -> str:
    """Tableau Markdown (sans dependance supplementaire)."""
    if df.empty:
        return "_(aucune donnee)_\n"
    cols = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(v).replace("|", "/") for v in row) + " |")
    return "\n".join(lines) + "\n"


def write_report(raw: pd.DataFrame, fmt: pd.DataFrame, path) -> None:
    parts = [
        "# Resultats de l'evaluation\n",
        "## Comparaison globale (sans / avec le module de formats)\n",
        to_markdown(compare_global(raw, fmt)),
        "## Par type de nombre\n",
        to_markdown(compare_by_type(raw, fmt)),
        "## Par direction de traduction (colonne lang = langue source)\n",
        "### Sans module\n",
        to_markdown(metrics_by(raw, "lang")),
        "### Avec module\n",
        to_markdown(metrics_by(fmt, "lang")),
        "## Erreurs les plus frequentes (sans module)\n",
        to_markdown(frequent_errors(raw)),
        "## Erreurs les plus frequentes (avec module)\n",
        to_markdown(frequent_errors(fmt)),
    ]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(parts), encoding="utf-8")


def main() -> None:
    raw = load_verification("data/verification_raw.csv")
    fmt = load_verification("data/verification_formats.csv")

    print("=== Comparaison globale ===")
    print(compare_global(raw, fmt).to_string(index=False))
    print("\n=== Par type ===")
    print(compare_by_type(raw, fmt).to_string(index=False))
    print("\n=== Erreurs frequentes (sans module) ===")
    print(frequent_errors(raw).to_string(index=False))

    error_details(raw).to_csv("data/errors_raw.csv", index=False, encoding="utf-8")
    error_details(fmt).to_csv("data/errors_formats.csv", index=False, encoding="utf-8")
    compare_global(raw, fmt).to_csv("data/results_summary.csv", index=False, encoding="utf-8")
    compare_by_type(raw, fmt).to_csv("data/results_by_type.csv", index=False, encoding="utf-8")
    write_report(raw, fmt, "docs/resultats.md")
    print("\nFichiers ecrits : data/results_summary.csv, data/results_by_type.csv,")
    print("data/errors_raw.csv, data/errors_formats.csv, docs/resultats.md")


if __name__ == "__main__":
    main()