import re
from pathlib import Path
import pandas as pd


CLEAN_FILE = Path.home() / "netlist/clean/s35932_clean.v"
TROJAN_FILE = Path.home() / "netlist/trojan/s35932_T100.v"

OUTPUT_DIR = Path.home() / "trojan_ml/data/processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Common gate-level Verilog primitives.
PRIMITIVES = {
    "and", "or", "xor", "xnor", "nand", "nor",
    "not", "buf", "andn", "orn"
}


def remove_comments(text):
    """Remove // and /* ... */ comments."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"//.*", "", text)
    return text


def extract_instances(filename):
    """
    Extract simple gate instances from a gate-level Verilog netlist.

    Supports both positional connections:
        AND2X1 U1 (a, b, out);

    and named connections:
        AND2X1 U1 (.A(a), .B(b), .Y(out));
    """

    text = Path(filename).read_text(errors="ignore")
    text = remove_comments(text)

    # Match: gate_type instance_name (...);
    pattern = re.compile(
        r"\b([A-Za-z_][A-Za-z0-9_$]*)\s+"
        r"([A-Za-z_][A-Za-z0-9_$]*)\s*"
        r"\((.*?)\)\s*;",
        flags=re.DOTALL
    )

    instances = []

    for match in pattern.finditer(text):
        gate_type = match.group(1)
        instance_name = match.group(2)
        connection_text = match.group(3)

        # Skip module declarations and non-gate constructs.
        if gate_type.lower() in {
            "module", "input", "output", "wire", "reg",
            "assign", "always", "if"
        }:
            continue

        # Extract nets from named connections such as .A(net123).
        named_nets = re.findall(
            r"\.\s*[A-Za-z_][A-Za-z0-9_$]*\s*"
            r"\(\s*([A-Za-z_][A-Za-z0-9_$]*)\s*\)",
            connection_text
        )

        if named_nets:
            nets = named_nets
        else:
            # Positional connections.
            nets = [
                token.strip()
                for token in connection_text.split(",")
                if re.fullmatch(
                    r"[A-Za-z_][A-Za-z0-9_$]*", token.strip()
                )
            ]

        if not nets:
            continue

        instances.append({
            "gate_type": gate_type,
            "instance": instance_name,
            "nets": tuple(nets)
        })

    return instances


def build_net_table(instances):
    """Create one row per net with basic structural features."""

    net_data = {}

    for gate in instances:
        gate_type = gate["gate_type"]
        instance = gate["instance"]
        nets = gate["nets"]

        if not nets:
            continue

        # For positional gate connections, the final net is
        # approximately treated as the output.
        output_net = nets[-1]
        input_nets = nets[:-1]

        for net in nets:
            if net not in net_data:
                net_data[net] = {
                    "net": net,
                    "fanin": 0,
                    "fanout": 0,
                    "gate_count": 0,
                    "gate_types": set(),
                    "instances": set()
                }

            net_data[net]["gate_count"] += 1
            net_data[net]["gate_types"].add(gate_type)
            net_data[net]["instances"].add(instance)

        for net in input_nets:
            net_data[net]["fanout"] += 1

        net_data[output_net]["fanin"] += len(input_nets)

    rows = []

    for net, data in net_data.items():
        rows.append({
            "net": net,
            "fanin": data["fanin"],
            "fanout": data["fanout"],
            "gate_count": data["gate_count"],
            "num_gate_types": len(data["gate_types"]),
            "num_instances": len(data["instances"])
        })

    return pd.DataFrame(rows)


def instance_signature(instance):
    return (
        instance["gate_type"],
        instance["instance"],
        instance["nets"]
    )


print("Reading clean netlist...")
clean_instances = extract_instances(CLEAN_FILE)

print("Reading Trojan-inserted netlist...")
trojan_instances = extract_instances(TROJAN_FILE)

print(f"Clean instances found: {len(clean_instances)}")
print(f"Trojan instances found: {len(trojan_instances)}")


# Save gate-level tables.
clean_gate_df = pd.DataFrame([
    {
        "gate_type": x["gate_type"],
        "instance": x["instance"],
        "nets": "|".join(x["nets"])
    }
    for x in clean_instances
])

trojan_gate_df = pd.DataFrame([
    {
        "gate_type": x["gate_type"],
        "instance": x["instance"],
        "nets": "|".join(x["nets"])
    }
    for x in trojan_instances
])

clean_gate_df.to_csv(OUTPUT_DIR / "clean_gates.csv", index=False)
trojan_gate_df.to_csv(OUTPUT_DIR / "trojan_gates.csv", index=False)


# Compare gate instances.
clean_map = {
    x["instance"]: instance_signature(x)
    for x in clean_instances
}

trojan_map = {
    x["instance"]: instance_signature(x)
    for x in trojan_instances
}

changed_instances = set()

all_instances = set(clean_map) | set(trojan_map)

for instance in all_instances:
    if clean_map.get(instance) != trojan_map.get(instance):
        changed_instances.add(instance)


# Identify nets involved in changed, added, or removed instances.
changed_nets = set()

for instance in changed_instances:
    if instance in clean_map:
        changed_nets.update(clean_map[instance][2])

    if instance in trojan_map:
        changed_nets.update(trojan_map[instance][2])


print(f"Changed instances: {len(changed_instances)}")
print(f"Preliminary changed nets: {len(changed_nets)}")


# Extract structural features from the CLEAN netlist only.
features_df = build_net_table(clean_instances)

# Preliminary binary label.
features_df["y_any"] = features_df["net"].apply(
    lambda net: int(net in changed_nets)
)

features_df["design"] = "s35932"
features_df["trojan"] = "T100"

# Save the preliminary ML dataset.
features_df.to_csv(
    OUTPUT_DIR / "features_s35932_T100.csv",
    index=False
)

# Save the changed-net report.
changed_df = pd.DataFrame({
    "net": sorted(changed_nets)
})

changed_df.to_csv(
    OUTPUT_DIR / "preliminary_changed_nets.csv",
    index=False
)

print("\nDataset preparation complete.")
print(f"Feature rows: {len(features_df)}")
print(
    "Preliminary positive labels:",
    int(features_df["y_any"].sum())
)

print("\nGenerated files:")
for file in sorted(OUTPUT_DIR.iterdir()):
    print(" -", file.name)