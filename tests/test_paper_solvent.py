"""Fail visibly if the solvent figure cannot be reproduced from its artifacts.

The committed historical table currently lacks 13 of the model's 19 features.
That is a genuine reproduction failure, not an expected failure to skip/xfail.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from copolpredictor.case_studies import case_study_features

ROOT = Path(__file__).resolve().parents[1]
MODEL_META = ROOT / "02-reactivity-prediction/copol_prediction/artifacts/model_bundle/meta.json"
SOLVENT_TABLE = ROOT / "03-experiments/case_studies/solvent/case_study_features.csv"


def test_paper_solvent_saved_plot_outcomes_match_the_reference():
    """Keep saved classes and abstention flags tied to the independent claim fixture."""
    reference = json.loads((ROOT / "tests/fixtures/paper_solvent_cases.json").read_text())
    table = pd.read_csv(SOLVENT_TABLE).set_index("solvent_name")
    assert table.index.is_unique
    assert set(table.index) == {case["solvent_name"] for case in reference["cases"]}
    labels = {0: "alternating", 1: "random", 2: "gradient"}
    for case in reference["cases"]:
        row = table.loc[case["solvent_name"]]
        assert row["agreement"] in (True, False)
        saved = labels[int(row["model_class"])] if row["agreement"] else None
        assert saved == case["expected_voting_class"], case["solvent_name"]


def test_paper_solvent_table_supplies_every_model_feature():
    """A figure must not fall back to historical outputs after a schema change."""
    metadata = json.loads(MODEL_META.read_text())
    case_study_features(pd.read_csv(SOLVENT_TABLE), metadata["feature_columns"])


def test_missing_descriptor_is_rejected_even_when_saved_predictions_exist():
    frame = pd.DataFrame({"temperature": [90.0], "model_class": [1]})
    with pytest.raises(ValueError, match="missing 1 of 2 required columns: homo_1"):
        case_study_features(frame, ["temperature", "homo_1"])


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf")])
def test_missing_or_nonfinite_descriptor_is_not_zero_filled(invalid):
    frame = pd.DataFrame({"temperature": [90.0], "homo_1": [invalid]})
    with pytest.raises(ValueError, match="non-finite values.*homo_1"):
        case_study_features(frame, ["temperature", "homo_1"])


def test_valid_descriptors_are_ordered_without_using_saved_outputs():
    frame = pd.DataFrame({"temperature": [90.0], "homo_1": [-0.38], "model_class": [1]})
    features = case_study_features(frame, ["homo_1", "temperature"])
    assert features.columns.tolist() == ["homo_1", "temperature"]
    assert features.iloc[0].tolist() == [-0.38, 90.0]


def test_empty_case_study_is_rejected():
    with pytest.raises(ValueError, match="empty"):
        case_study_features(pd.DataFrame(columns=["temperature"]), ["temperature"])
