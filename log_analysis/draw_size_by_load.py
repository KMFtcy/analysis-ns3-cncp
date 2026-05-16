#!/usr/bin/env python3
"""Draw a grouped bar chart of flow size across load levels.

Input directory should contain txt files such as:
*_40.txt, *_50.txt, *_60.txt, *_70.txt, *_80.txt

Each txt file should contain columns:
CC    Flow Count    Size(bytes)
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


DEFAULT_LOADS = [40, 50, 60, 70, 80]
CC_DISPLAY_NAME = {
    "cc_1_fct": "DCQCN",
    "cc_3_fct": "HPCC",
    "cc_7_fct": "TIMELY",
    "cc_8_fct": "DCTCP",
    "cc_11_fct": "DC-CNCP",
    "cc_12_fct": "CNCP",
    "cc_11_large_scale_OQ_validation_fct": "DC-CNCP-noOQ"
}
CC_ORDER = ["cc_1_fct", "cc_3_fct", "cc_7_fct", "cc_8_fct", "cc_12_fct", "cc_11_large_scale_OQ_validation_fct","cc_11_fct"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Draw one grouped bar chart with all load levels from one txt directory."
    )
    parser.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing txt files for different load levels.",
    )
    parser.add_argument(
        "-l",
        "--loads",
        type=int,
        nargs="+",
        default=DEFAULT_LOADS,
        help="Load levels to include. Default: 40 50 60 70 80",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Output image DPI. Default: 200",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Chart title suffix. Default uses input directory name.",
    )
    return parser.parse_args()


def detect_file(input_dir: Path, load: int) -> Path:
    matches = sorted(input_dir.glob(f"*_{load}.txt"))
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise FileNotFoundError(
            f"Cannot find input file for load {load} in {input_dir}"
        )
    raise RuntimeError(
        f"Found multiple candidates for load {load} in {input_dir}: {matches}"
    )


def read_size_table(input_dir: Path, loads: list[int]) -> pd.DataFrame:
    records: list[dict[str, int | str]] = []

    for load in loads:
        txt_file = detect_file(input_dir, load)
        with txt_file.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        if not lines:
            raise ValueError(f"{txt_file} is empty")

        # Skip header and parse remaining rows by generic whitespace.
        bad_rows: list[str] = []
        for idx, line in enumerate(lines[1:], start=2):
            raw = line.strip()
            if not raw:
                continue

            parts = raw.split()
            if len(parts) < 3:
                bad_rows.append(f"line {idx}: {raw}")
                continue

            cc = parts[0]
            size_str = parts[-1]

            try:
                size = int(float(size_str))
            except ValueError:
                bad_rows.append(f"line {idx}: {raw}")
                continue

            records.append({"load": load, "cc": cc, "size": size})

        if bad_rows:
            print(f"[WARN] {txt_file} ignored malformed rows:")
            for row in bad_rows:
                print(f"  - {row}")

    return pd.DataFrame(records)


def plot_grouped_bars(
    title_name: str,
    data: pd.DataFrame,
    loads: list[int],
    dpi: int,
    output_dir: Path,
) -> Path:
    present = set(data["cc"].unique().tolist())
    cc_order = [cc for cc in CC_ORDER if cc in present] + sorted(present - set(CC_ORDER))
    x_labels = [f"{ld}%" for ld in loads]

    # Keep deterministic bar width and spacing regardless of number of CCs.
    x = list(range(len(loads)))
    total_width = 0.8
    bar_width = total_width / len(cc_order)

    fig, ax = plt.subplots(figsize=(11, 5.5))

    for i, cc in enumerate(cc_order):
        cc_df = data[data["cc"] == cc]
        size_by_load = {
            int(r["load"]): int(r["size"]) for _, r in cc_df[["load", "size"]].iterrows()
        }
        y = [size_by_load.get(ld, 0) for ld in loads]
        offset = -total_width / 2 + (i + 0.5) * bar_width
        x_pos = [v + offset for v in x]

        ax.bar(x_pos, y, width=bar_width, label=CC_DISPLAY_NAME.get(cc, cc))

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.set_xlabel("Load Level")
    ax.set_ylabel("Size (bytes)")
    ax.set_title(f"Flow Size by Load - {title_name}")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=3, frameon=False)

    fig.tight_layout()
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"flow_size_bar_{title_name}_{timestamp}.png"
    fig.savefig(output_file, dpi=dpi)
    plt.close(fig)
    return output_file


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.expanduser().resolve()

    if not input_dir.exists() or not input_dir.is_dir():
        raise NotADirectoryError(f"Invalid input directory: {input_dir}")

    title_name = args.title if args.title else input_dir.name
    data = read_size_table(input_dir, args.loads)
    out = plot_grouped_bars(title_name, data, args.loads, args.dpi, input_dir)
    print(f"[OK] Saved: {out}")


if __name__ == "__main__":
    main()
