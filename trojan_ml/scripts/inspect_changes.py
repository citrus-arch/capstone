import pandas as pd

clean = pd.read_csv(
    "/home/manjari/trojan_ml/data/processed/clean_gates.csv"
)

trojan = pd.read_csv(
    "/home/manjari/trojan_ml/data/processed/trojan_gates.csv"
)

clean_map = clean.set_index("instance").to_dict("index")
trojan_map = trojan.set_index("instance").to_dict("index")

all_instances = sorted(set(clean_map) | set(trojan_map))

changes = []

for instance in all_instances:
    c = clean_map.get(instance)
    t = trojan_map.get(instance)

    if c != t:
        changes.append({
            "instance": instance,
            "clean_gate_type": None if c is None else c["gate_type"],
            "trojan_gate_type": None if t is None else t["gate_type"],
            "clean_nets": None if c is None else c["nets"],
            "trojan_nets": None if t is None else t["nets"],
        })

result = pd.DataFrame(changes)

result.to_csv(
    "/home/manjari/trojan_ml/data/processed/changed_instances.csv",
    index=False
)

print(result.to_string(index=False))
print("\nTotal changed instances:", len(result))
