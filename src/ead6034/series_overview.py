"""Six-panel visual inspection of the exact return series used in the analysis.

Reads the local pipeline frames and verifies their return hashes against the
published manifest. Every observation is drawn, without smoothing, clipping or
subsampling. Only the figure is published; local parquet files remain private.
Rasterized traces keep the PDF compact without embedding vector return paths.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator
import numpy as np
import pandas as pd

from .forecast_figures import GRAY, LABELS, NAVY, SCALES, STYLE, TEAL, _pt_number


FIGURE_NAME = "00_complete_return_series_slide.pdf"


def make_series_overview(output: str | Path) -> Path:
    """Plot all six training/test series without fitting or changing a model."""
    out = Path(output)
    metadata = json.loads((out / "analysis_summary.json").read_text())
    expected = {row["scale"]: row for row in metadata["scales"]}
    dates = pd.to_datetime(["2024-01-01", "2024-07-01", "2025-01-01", "2025-07-01"])
    with plt.rc_context({**STYLE, "path.simplify": False}):
        fig, axes = plt.subplots(2, 3, figsize=(12.5, 4.7))
        for index, (ax, scale) in enumerate(zip(axes.flat, SCALES)):
            frame = pd.read_parquet(
                out / "private" / f"frames_{scale}.parquet",
                columns=["timestamp", "return_pct", "sample"],
            )
            values = frame.return_pct.to_numpy(dtype="<f8")
            train = frame["sample"].eq("train").to_numpy()
            test = frame["sample"].eq("test").to_numpy()
            if not np.isfinite(values).all() or not (train | test).all():
                raise ValueError(f"{scale}: invalid plotted observations")
            for name, subset in [("full_sequence", values), ("train", values[train])]:
                digest = hashlib.sha256(subset.tobytes()).hexdigest()
                if digest != expected[scale][f"{name}_sha256"]:
                    raise ValueError(f"{scale}: plotted {name} differs from the analysis")
            if (int(train.sum()), int(test.sum())) != (
                expected[scale]["n_train"], expected[scale]["n_test"]
            ):
                raise ValueError(f"{scale}: sample sizes differ from the analysis")
            timestamps = pd.to_datetime(frame.timestamp).dt.tz_localize(None)
            if not timestamps.is_monotonic_increasing:
                raise ValueError(f"{scale}: timestamps are not ordered")
            ax.axhline(0, color=GRAY, linewidth=.55, zorder=0)
            ax.axvline(pd.Timestamp("2025-01-01"), color=GRAY,
                       linewidth=.85, linestyle="--", zorder=1)
            for mask, color in [(train, NAVY), (test, TEAL)]:
                ax.plot(timestamps[mask], values[mask], color=color,
                        linewidth=.45, rasterized=True, zorder=2)
            # Independent, symmetric axes retain every observed extreme.
            limit = float(np.max(np.abs(values))) * 1.08
            ax.set_ylim(-limit, limit)
            ax.set_xlim(pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-01"))
            ax.set_xticks(dates)
            ax.set_xticklabels(["jan/24", "jul/24", "jan/25", "jul/25"])
            ax.set_title(LABELS[scale], fontsize=16, pad=4)
            ax.set_ylabel("Retorno (%)" if index % 3 == 0 else "", fontsize=13)
            ax.yaxis.set_major_locator(MaxNLocator(nbins=3, symmetric=True))
            ax.yaxis.set_major_formatter(FuncFormatter(_pt_number))
            ax.tick_params(axis="both", labelsize=12, pad=2)
            ax.grid(axis="x", visible=False)
        handles = [
            Line2D([], [], color=NAVY, label="Treino: 2024"),
            Line2D([], [], color=TEAL, label="Teste: 2025"),
            Line2D([], [], color=GRAY, linestyle="--", label="Separação treino/teste"),
        ]
        fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(.52, 1.025),
                   ncol=3, frameon=False, fontsize=13, columnspacing=2,
                   handlelength=1.8, borderaxespad=.3)
        fig.subplots_adjust(left=.075, right=.99, bottom=.09, top=.83,
                            hspace=.65, wspace=.34)
        path = out / "figures" / FIGURE_NAME
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=220, facecolor="white",
                    metadata={"Title": "Séries completas de retornos do WIN: 2024 e 2025",
                              "Author": "Renan de Luca Avila"})
        plt.close(fig)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="results/entrega_21_09")
    args = parser.parse_args()
    print(make_series_overview(args.output))


if __name__ == "__main__":
    main()
