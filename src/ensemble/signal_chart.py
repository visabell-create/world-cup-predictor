"""Visual signal contrast chart — replaces verbose comparison logs."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def save_signal_contrast_chart(
    contrasts: list[dict[str, Any]],
    match_id: str,
    home: str,
    away: str,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    chart_path = output_dir / f"{match_id}_contrast.png"

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        labels = [c["signal"].replace("_", "\n")[:18] for c in contrasts]
        internal = [c["internal"] for c in contrasts]
        google = [c["google"] for c in contrasts]
        y = range(len(labels))

        fig, ax = plt.subplots(figsize=(10, max(6, len(labels) * 0.35)))
        ax.barh([i - 0.15 for i in y], internal, height=0.3, label="Internal", color="#2563eb")
        ax.barh([i + 0.15 for i in y], google, height=0.3, label="Google", color="#16a34a")
        ax.set_yticks(list(y))
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlim(0, 1)
        ax.set_xlabel("Signal strength (0–1)")
        ax.set_title(f"{home} vs {away} — Internal vs Google ({match_id})")
        ax.legend(loc="lower right")
        fig.tight_layout()
        fig.savefig(chart_path, dpi=120)
        plt.close(fig)
    except Exception:
        chart_path.write_text(
            "\n".join(
                f"{c['signal']}: internal={c['internal']} google={c['google']} delta={c['delta']}"
                for c in contrasts
            ),
            encoding="utf-8",
        )
    return chart_path
