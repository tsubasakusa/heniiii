from app.utils.crossword import grade, mask_cells, solution_map

GRID = {
    "rows": 2,
    "cols": 2,
    "cells": [
        {"r": 0, "c": 0, "answer": "C", "number": 1},
        {"r": 0, "c": 1, "answer": "A"},
        {"r": 1, "c": 0, "answer": "T"},
    ],
}


def test_mask_cells_hides_answers():
    masked = mask_cells(GRID)
    assert masked == [
        {"r": 0, "c": 0, "number": 1},
        {"r": 0, "c": 1},
        {"r": 1, "c": 0},
    ]
    assert all("answer" not in cell for cell in masked)


def test_solution_map():
    assert solution_map(GRID) == {"0,0": "C", "0,1": "A", "1,0": "T"}


def test_grade_perfect_gets_time_bonus():
    result = grade(GRID, {"0,0": "c", "0,1": "A", "1,0": "t"}, time_spent_seconds=100)
    assert result["is_perfect"] is True
    assert result["correct_cells"] == 3
    assert result["base_score"] == 1000
    assert result["time_bonus"] == 500  # 600 - 100
    assert result["score"] == 1500


def test_grade_faster_scores_higher():
    fast = grade(GRID, {"0,0": "C", "0,1": "A", "1,0": "T"}, 30)
    slow = grade(GRID, {"0,0": "C", "0,1": "A", "1,0": "T"}, 300)
    assert fast["score"] > slow["score"]


def test_grade_partial_no_time_bonus():
    result = grade(GRID, {"0,0": "C", "0,1": "X", "1,0": "T"}, 10)
    assert result["is_perfect"] is False
    assert result["correct_cells"] == 2
    assert result["base_score"] == round(1000 * 2 / 3)
    assert result["time_bonus"] == 0
    assert result["per_cell"] == {"0,0": True, "0,1": False, "1,0": True}


def test_grade_blank_is_incorrect():
    result = grade(GRID, {}, 5)
    assert result["correct_cells"] == 0
    assert result["score"] == 0
