from pathlib import Path
import pandas as pd


BASE = Path.home() / "trojan_ml/data/processed"

features_file = BASE / "features_s35932_T100.csv"
output_file = BASE / "trojan_net_labels.csv"

features = pd.read_csv(features_file)

# Existing clean-design signals that feed the Trojan trigger logic.
trigger_taps = {
    "WX742",
    "WX7249",
    "WX5922",
    "WX5960",
    "WX4697",
    "WX9032",
    "WX8298",
    "WX10846",
    "WX3340",
    "WX6476",
    "WX9819",
    "WX1813",
    "WX5710",
    "WX3458",
    "WX9060",
    "WX7749",
}

# Original signals whose connections are modified by the Trojan.
victim_nets = {
    "test_se",
    "WX11155",
}

rows = []

for net in features["net"]:
    if net in trigger_taps:
        role = "trigger_tap"
        label = 1

    elif net in victim_nets:
        role = "victim_control"
        label = 1

    else:
        role = "benign_or_unconfirmed"
        label = 0

    rows.append({
        "net": net,
        "role": role,
        "label": label
    })

labels = pd.DataFrame(rows)

labels.to_csv(output_file, index=False)

print("Created:", output_file)
print("\nRole counts:")
print(labels["role"].value_counts())

print("\nPositive labels:")
print(labels[labels["label"] == 1].to_string(index=False))
