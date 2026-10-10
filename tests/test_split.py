from pathlib import Path

import pandas as pd
import pytest

PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "clean_split.csv"

# The data is not in Git, so skip on machines (and CI) that don't have it.
pytestmark = pytest.mark.skipif(
    not PATH.exists(), reason="clean_split.csv not found (data is not in Git)"
)


def load():
    return pd.read_csv(PATH)


def test_each_problem_is_in_exactly_one_split():
    df = load()
    assert df.groupby("problem_id")["split"].nunique().max() == 1


def test_all_three_splits_exist():
    assert set(load()["split"]) == {"train", "val", "test"}


def test_every_split_has_both_classes():
    df = load()
    for name, g in df.groupby("split"):
        assert set(g["status"]) == {"Accepted", "Time Limit Exceeded"}, name