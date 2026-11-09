"""Traduction automatique FR <-> EN avec MarianMT (Hugging Face).

Ce module ne modifie pas le code de detection/conversion/formats : il se
contente de traduire des textes et de traduire le corpus.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

# Evite l'avertissement sur les liens symboliques sous Windows
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

MODELS = {
    ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
}
TARGET = {"fr": "en", "en": "fr"}

_cache: dict = {}


def _load(src: str, tgt: str):
    """Charge (une seule fois) le tokenizer et le modele pour src -> tgt."""
    key = (src, tgt)
    if key not in MODELS:
        raise ValueError(f"Paire de langues non supportee : {src} -> {tgt}")
    if key not in _cache:
        from transformers import MarianMTModel, MarianTokenizer

        name = MODELS[key]
        tokenizer = MarianTokenizer.from_pretrained(name)
        model = MarianMTModel.from_pretrained(name)
        model.eval()
        _cache[key] = (tokenizer, model)
    return _cache[key]


def translate_texts(
    texts: list[str],
    src: str,
    tgt: str,
    batch_size: int = 16,
    num_beams: int = 4,
    max_length: int = 256,
) -> list[str]:
    """Traduit une liste de phrases de `src` vers `tgt`."""
    import torch

    tokenizer, model = _load(src, tgt)
    results: list[str] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        enc = tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=max_length,
        )
        with torch.no_grad():
            generated = model.generate(
                **enc, num_beams=num_beams, max_length=max_length
            )
        results.extend(tokenizer.batch_decode(generated, skip_special_tokens=True))
    return results


def translate_text(text: str, src: str, tgt: str) -> str:
    """Traduit une seule phrase."""
    return translate_texts([text], src, tgt)[0]


def translate_corpus(
    corpus_path,
    output_path,
    mode: str = "raw",
    translate_fn=translate_texts,
) -> pd.DataFrame:
    """Traduit chaque phrase du corpus vers l'autre langue (fr <-> en).

    mode = "raw"     : on traduit le texte tel quel (sans le module de Haytham)
    mode = "formats" : on applique d'abord convert_formats() de Haytham
                       pour mettre les nombres au format de la langue cible,
                       puis on traduit.

    Colonnes ajoutees : target_lang, input_text, translation.
    """
    if mode not in ("raw", "formats"):
        raise ValueError("mode doit etre 'raw' ou 'formats'")

    df = pd.read_csv(corpus_path, encoding="utf-8", dtype=str, keep_default_na=False)
    df["target_lang"] = df["lang"].map(TARGET).fillna("")
    df["input_text"] = df["text"]

    if mode == "formats":
        from src.formats import convert_formats

        df["input_text"] = [
            convert_formats(t, l, tl) if tl else t
            for t, l, tl in zip(df["text"], df["lang"], df["target_lang"])
        ]

    df["translation"] = ""
    for lang, tgt in TARGET.items():
        mask = df["lang"] == lang
        if mask.any():
            df.loc[mask, "translation"] = translate_fn(
                df.loc[mask, "input_text"].tolist(), lang, tgt
            )

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8")
    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="Traduit le corpus (fr <-> en).")
    parser.add_argument("--mode", choices=["raw", "formats"], default="raw")
    parser.add_argument("--corpus", default="data/corpus.csv")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    output = args.output or f"data/translations_{args.mode}.csv"
    df = translate_corpus(args.corpus, output, mode=args.mode)
    print(f"{len(df)} phrases traduites -> {output}")


if __name__ == "__main__":
    main()