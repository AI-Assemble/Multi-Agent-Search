import csv
import re
import threading
from pathlib import Path


CSV_FIELDS = [
    "attempt_display",
    "attempt_number",
    "total_attempts",
    "window_title",
    "status",
    "return_code",
    "started_at",
    "finished_at",
    "duration_seconds",
    "agent",
    "layout",
    "ghosts",
    "parallel",
    "score",
    "average_score",
    "result",
    "wins",
    "games_reported",
    "win_rate",
    "record",
]


def _extract_attempt_metrics(stdout_text: str) -> dict[str, str]:
    metrics = {
        "score": "",
        "average_score": "",
        "result": "",
        "wins": "",
        "games_reported": "",
        "win_rate": "",
        "record": "",
    }

    final_score_match = re.search(
        r"Pacman (?:emerges victorious!|died!) Score:\s*(-?\d+(?:\.\d+)?)",
        stdout_text,
    )
    if final_score_match:
        metrics["score"] = final_score_match.group(1)
    else:
        score_matches = re.findall(r"(?m)^Score:\s*(-?\d+(?:\.\d+)?)\s*$", stdout_text)
        if score_matches:
            metrics["score"] = score_matches[-1]

    average_score_match = re.search(r"Average Score:\s*(-?\d+(?:\.\d+)?)", stdout_text)
    if average_score_match:
        metrics["average_score"] = average_score_match.group(1)
    elif metrics["score"]:
        metrics["average_score"] = metrics["score"]

    win_rate_match = re.search(r"Win Rate:\s*(\d+)/(\d+)\s+\(([^)]+)\)", stdout_text)
    if win_rate_match:
        metrics["wins"] = win_rate_match.group(1)
        metrics["games_reported"] = win_rate_match.group(2)
        metrics["win_rate"] = win_rate_match.group(3)

    record_match = re.search(r"Record:\s*(.+)", stdout_text)
    if record_match:
        metrics["record"] = record_match.group(1).strip()

    if "Pacman emerges victorious!" in stdout_text:
        metrics["result"] = "win"
    elif "Pacman died!" in stdout_text:
        metrics["result"] = "loss"

    return metrics


def _upsert_csv_row(
    csv_path: Path,
    csv_lock: threading.Lock,
    csv_rows: dict[int, dict[str, object]],
    attempt_number: int,
    row: dict[str, object],
) -> None:
    with csv_lock:
        merged_row = dict(csv_rows.get(attempt_number, {}))
        merged_row.update(row)
        csv_rows[attempt_number] = merged_row
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for ordered_attempt in sorted(csv_rows):
                writer.writerow(
                    {
                        field: csv_rows[ordered_attempt].get(field, "")
                        for field in CSV_FIELDS
                    }
                )
            handle.flush()
