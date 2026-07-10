"""Crossword grading and grid-masking helpers (pure, HTTP-agnostic)."""
from typing import Any

BASE_POINTS = 1000
MAX_TIME_BONUS = 600


def cell_key(r: int, c: int) -> str:
    return f"{r},{c}"


def mask_cells(grid_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the playable cells WITHOUT the answer letters (anti-cheat)."""
    masked = []
    for cell in grid_data.get("cells", []):
        item = {"r": cell["r"], "c": cell["c"]}
        if cell.get("number") is not None:
            item["number"] = cell["number"]
        masked.append(item)
    return masked


def solution_map(grid_data: dict[str, Any]) -> dict[str, str]:
    return {
        cell_key(cell["r"], cell["c"]): str(cell["answer"]).upper()
        for cell in grid_data.get("cells", [])
    }


def grade(
    grid_data: dict[str, Any], answers: dict[str, str], time_spent_seconds: int
) -> dict[str, Any]:
    """Grade a submission and compute score = base (by correct ratio) + time bonus.

    A time bonus is only awarded on a perfect grid, and shrinks the longer the
    solve takes — so a faster perfect finish scores higher.
    """
    cells = grid_data.get("cells", [])
    total = len(cells)
    per_cell: dict[str, bool] = {}
    correct = 0

    for cell in cells:
        key = cell_key(cell["r"], cell["c"])
        got = (answers.get(key) or "").strip().upper()
        ok = got == str(cell["answer"]).upper() and got != ""
        per_cell[key] = ok
        if ok:
            correct += 1

    ratio = correct / total if total else 0.0
    base_score = round(BASE_POINTS * ratio)
    is_perfect = total > 0 and correct == total
    time_bonus = max(0, MAX_TIME_BONUS - max(0, time_spent_seconds)) if is_perfect else 0

    return {
        "correct_cells": correct,
        "total_cells": total,
        "base_score": base_score,
        "time_bonus": time_bonus,
        "score": base_score + time_bonus,
        "is_perfect": is_perfect,
        "per_cell": per_cell,
    }
