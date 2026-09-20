from pathlib import Path
import pandas as pd


BASE = Path.home() / "trojan_ml/data/processed"

features = pd.read_csv(BASE / "features_s35932_T100.csv")
labels = pd.read_csv(BASE / "trojan_net_labels.csv")

dataset = features.drop(columns=["y_any"], errors="ignore")
dataset = dataset.drop(columns=["design", "trojan"], errors="ignore")

dataset = dataset.merge(labels, on="net", how="left")

dataset["label"] = dataset["label"].fillna(0).astype(int)
dataset["role"] = dataset["role"].fillna("unknown")

output = BASE / "ml_dataset_s35932_T100.csv"
dataset.to_csv(output, index=False)

print("Saved:", output)
print("\nDataset shape:", dataset.shape)
print("\nLabel distribution:")
print(dataset["label"].value_counts())

print("\nColumns:")
print(list(dataset.columns))
