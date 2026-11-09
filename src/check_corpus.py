import pandas as pd

df = pd.read_csv("data/corpus.csv", encoding="utf-8")
print(df.shape)
print(df["lang"].value_counts())
print(df["type"].value_counts())
print(df.head())