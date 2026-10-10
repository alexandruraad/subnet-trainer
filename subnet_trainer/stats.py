"""Per-topic accuracy saved between sessions, so `stats` can show your weak spots."""

from __future__ import annotations

import json
import os
from pathlib import Path


def stats_path() -> Path:
    override = os.environ.get("SUBNET_TRAINER_STATS")
    if override:
        return Path(override)
    return Path.home() / ".subnet-trainer" / "stats.json"


def load(path: Path | None = None) -> dict[str, dict[str, int]]:
    path = path or stats_path()
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def record(results: list[tuple[str, bool]], path: Path | None = None) -> None:
    path = path or stats_path()
    data = load(path)
    for topic, correct in results:
        entry = data.setdefault(topic, {"correct": 0, "total": 0})
        entry["total"] += 1
        entry["correct"] += int(correct)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True))


def report(data: dict[str, dict[str, int]]) -> str:
    if not data:
        return "No stats yet. Run `subnet-trainer quiz` first."
    rows = sorted(data.items(), key=lambda kv: kv[1]["correct"] / kv[1]["total"])
    lines = [f"{'topic':<12} {'score':>9}  {'accuracy':>8}"]
    for topic, s in rows:
        pct = 100 * s["correct"] / s["total"]
        bar = "#" * round(pct / 10)
        lines.append(f"{topic:<12} {s['correct']:>4}/{s['total']:<4} {pct:>7.0f}%  {bar}")
    weakest = rows[0][0]
    lines.append("")
    lines.append(f"Weakest topic: {weakest}. Drill it with: subnet-trainer quiz --topics {weakest}")
    return "\n".join(lines)
