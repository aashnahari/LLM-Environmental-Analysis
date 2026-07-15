import argparse
import csv
import json
import sys
from pathlib import Path

from adapters import (
    normalize_azure_export,
    normalize_codex_export,
    normalize_bedrock_export,
    normalize_chatgpt_export,
)
from aggregate import Totals, by_model, by_source, total

SOURCE_LOADERS = {
    "azure": normalize_azure_export,
    "codex": normalize_codex_export,
    "bedrock": normalize_bedrock_export,
    "chatgpt": normalize_chatgpt_export,
}


def load_records(source: str, path: Path) -> list:
    # each file is a JSON list of row-dicts matching that source's adapter kwargs
    rows = json.loads(path.read_text())
    return SOURCE_LOADERS[source](rows)


def print_totals(label: str, t: Totals) -> None:
    print(
        f"{label:<24} energy={t.energy_wh:>12,.1f} Wh   "
        f"water={t.water_l:>10,.2f} L   carbon={t.carbon_kg:>10,.3f} kg   "
        f"requests={t.n_requests:>10,.0f}   estimated={t.n_estimated}/{t.n_records}"
    )


def write_csv(path: Path, buckets: dict) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["bucket", "energy_wh", "water_l", "carbon_kg", "n_requests", "n_records", "n_estimated"]
        )
        for key, t in buckets.items():
            label = getattr(key, "value", key)
            writer.writerow([label, t.energy_wh, t.water_l, t.carbon_kg, t.n_requests, t.n_records, t.n_estimated])


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate the energy, water, and carbon footprint of LLM usage "
            "across Azure OpenAI, Codex, Bedrock, and ChatGPT."
        )
    )
    parser.add_argument("--azure", type=Path, help="JSON file of rows for adapters.normalize_azure_export")
    parser.add_argument("--codex", type=Path, help="JSON file of rows for adapters.normalize_codex_export")
    parser.add_argument("--bedrock", type=Path, help="JSON file of rows for adapters.normalize_bedrock_export")
    parser.add_argument("--chatgpt", type=Path, help="JSON file of rows for adapters.normalize_chatgpt_export")
    parser.add_argument("--out", type=Path, help="write the by-source breakdown to this CSV path")
    args = parser.parse_args(argv)

    records = []
    for source, path in [
        ("azure", args.azure),
        ("codex", args.codex),
        ("bedrock", args.bedrock),
        ("chatgpt", args.chatgpt),
    ]:
        if path is None:
            continue
        records.extend(load_records(source, path))

    if not records:
        parser.error("no input given -- pass at least one of --azure/--codex/--bedrock/--chatgpt")

    print_totals("TOTAL", total(records))

    print("\nBy source:")
    for source, t in by_source(records).items():
        print_totals(f"  {source.value}", t)

    print("\nBy model:")
    for model, t in by_model(records).items():
        print_totals(f"  {model}", t)

    if args.out:
        write_csv(args.out, by_source(records))
        print(f"\nWrote by-source breakdown to {args.out}")

    print(
        "\nCaveat: this is a modeled, order-of-magnitude estimate, not a bill. "
        "energy_model coefficients are fit from third-party benchmark data "
        "(Jegham et al. 2025), not vendor-measured, and several inputs above "
        "('estimated') rest on documented placeholder assumptions in "
        "assumptions.py rather than real measurement -- see each adapter's "
        "module for what's measured vs. guessed for your data."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
