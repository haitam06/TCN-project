"""Verification de la conservation des nombres entre un texte source et sa traduction.

Utilise detect_numbers() de src/detection.py (sans le modifier).
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd

from src.detection import detect_numbers


def normalize_value(value):
    """Rend 12, 12.0 et 12.0000001 comparables ; arrondit les decimaux."""
    v = float(value)
    if abs(v - round(v)) < 1e-9:
        return int(round(v))
    return round(v, 6)


def extract_values(text: str, lang: str) -> list:
    """Valeurs numeriques normalisees d'un texte, dans l'ordre d'apparition."""
    if not text:
        return []
    return [normalize_value(r["value"]) for r in detect_numbers(text, lang)]


def compare_values(source_values: list, target_values: list) -> dict:
    """Compare deux listes de valeurs (ordre ignore).

    Retourne : matched, modified [(src, tgt)], omitted, added,
    n_source, n_target, n_matched, score, conserved.
    """
    remaining = Counter(target_values)
    matched, unmatched_src = [], []
    for v in source_values:
        if remaining[v] > 0:
            remaining[v] -= 1
            matched.append(v)
        else:
            unmatched_src.append(v)

    used = Counter(matched)
    unmatched_tgt = []
    for v in target_values:
        if used[v] > 0:
            used[v] -= 1
        else:
            unmatched_tgt.append(v)

    # Les nombres restants sont apparies dans l'ordre : ce sont des "modifies".
    k = min(len(unmatched_src), len(unmatched_tgt))
    modified = list(zip(unmatched_src[:k], unmatched_tgt[:k]))
    omitted = unmatched_src[k:]
    added = unmatched_tgt[k:]

    n_source, n_target, n_matched = len(source_values), len(target_values), len(matched)
    biggest = max(n_source, n_target)
    score = n_matched / biggest if biggest else 1.0
    return {
        "matched": matched,
        "modified": modified,
        "omitted": omitted,
        "added": added,
        "n_source": n_source,
        "n_target": n_target,
        "n_matched": n_matched,
        "score": score,
        "conserved": not (modified or omitted or added),
    }


def check_conservation(source_text: str, target_text: str, source_lang: str, target_lang: str) -> dict:
    """Detecte les nombres des deux textes puis les compare."""
    src_values = extract_values(source_text, source_lang)
    tgt_values = extract_values(target_text, target_lang)
    result = compare_values(src_values, tgt_values)
    result["source_values"] = src_values
    result["target_values"] = tgt_values
    return result


def _join(items) -> str:
    """Liste -> texte separe par '|' ; les couples (a, b) deviennent 'a->b'."""
    return "|".join(f"{x[0]}->{x[1]}" if isinstance(x, tuple) else str(x) for x in items)


def verify_corpus(translations_path, output_path=None) -> pd.DataFrame:
    """Verifie chaque ligne d'un fichier de traductions (translations_*.csv)."""
    df = pd.read_csv(translations_path, encoding="utf-8", dtype=str, keep_default_na=False)
    rows = []
    for _, r in df.iterrows():
        res = check_conservation(r["text"], r["translation"], r["lang"], r["target_lang"])
        rows.append(
            {
                "source_numbers": _join(res["source_values"]),
                "target_numbers": _join(res["target_values"]),
                "n_source": res["n_source"],
                "n_target": res["n_target"],
                "n_matched": res["n_matched"],
                "omitted": _join(res["omitted"]),
                "modified": _join(res["modified"]),
                "added": _join(res["added"]),
                "score": round(res["score"], 4),
                "conserved": res["conserved"],
            }
        )
    out = pd.concat([df, pd.DataFrame(rows)], axis=1)
    if output_path is not None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(output_path, index=False, encoding="utf-8")
    return out


def summarize(df: pd.DataFrame) -> dict:
    """Resume rapide d'un resultat de verify_corpus."""
    conserved = df["conserved"].astype(str) == "True"
    return {
        "phrases": len(df),
        "phrases_conservees": int(conserved.sum()),
        "taux_phrases_conservees": round(float(conserved.mean()), 4),
        "score_moyen": round(float(df["score"].astype(float).mean()), 4),
        "nombres_source": int(df["n_source"].astype(int).sum()),
        "nombres_conserves": int(df["n_matched"].astype(int).sum()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Verifie la conservation des nombres.")
    parser.add_argument("--mode", choices=["raw", "formats"], default="raw")
    args = parser.parse_args()

    src_path = f"data/translations_{args.mode}.csv"
    out_path = f"data/verification_{args.mode}.csv"
    df = verify_corpus(src_path, out_path)
    print(f"Resultat ecrit dans {out_path}")
    for key, value in summarize(df).items():
        print(f"  {key} : {value}")


if __name__ == "__main__":
    main()