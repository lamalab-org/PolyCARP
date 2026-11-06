"""Fail visibly if the solvent figure cannot be reproduced from its artifacts.

The rebuilt table supplies complete features and ratio-derived references.
Historical saved output columns remain separately guarded for comparison.
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


def test_supplied_solvent_ratios_use_current_curve_classes():
    """User-supplied ratios replace historical class labels as reference inputs."""
    import sys

    sys.path.insert(0, str(ROOT / "02-reactivity-prediction"))
    from copol_prediction.mayo_lewis_classification import classify_reactivity_curve

    expected = {
        "Benzene": (12.5, 0.25, "gradient"),
        "o-Dichlorobenzene": (12.5, 0.25, "gradient"),
        "Benzonitrile": (2.4, 1.35, "random"),
        "Dioxane": (1.38, 1.27, "random"),
        "Bis(2-methoxyethyl) ether": (1.09, 1.40, "random"),
        "Ethanol": (0.30, 1.44, "gradient"),
        "2-(2-Methoxyethoxy)ethanol": (0.27, 1.66, "gradient"),
        "DMSO": (0.16, 2.01, "gradient"),
        "Methanol": (0.20, 1.05, "gradient"),
    }
    table = pd.read_csv(SOLVENT_TABLE).set_index("solvent_name")
    assert set(table.index) == set(expected)
    for solvent, (r1, r2, label) in expected.items():
        row = table.loc[solvent]
        assert (row["r1"], row["r2"]) == (r1, r2)
        assert classify_reactivity_curve(row["r1"], row["r2"])["class_name"] == label
        assert classify_reactivity_curve(row["r2"], row["r1"])["class_name"] == label


@pytest.mark.parametrize("split", ["train", "val", "test"])
def test_feature_selection_splits_use_the_same_target_definition(split):
    """A richer-feature model is not a valid ablation if its target labels differ."""
    artifacts = MODEL_META.parent.parent
    keys = ["reaction_id", "monomer1_smiles", "monomer2_smiles"]
    columns = keys + ["r_product_class"]
    # Identical monomers can produce duplicate swapped rows. Collapse only
    # identical key/label records; conflicting labels still fail the 1:1 merge.
    released = pd.read_csv(artifacts / "data_splits" / f"{split}.csv")[columns].drop_duplicates()
    full = pd.read_csv(artifacts / "data_splits_full_features" / f"{split}.csv")[
        columns
    ].drop_duplicates()
    compared = released.merge(
        full,
        on=keys,
        how="outer",
        suffixes=("_released", "_full"),
        indicator=True,
        validate="one_to_one",
    )
    assert (compared["_merge"] == "both").all(), "Feature ablation must use the same split records"
    mismatches = compared["r_product_class_released"] != compared["r_product_class_full"]
    assert not mismatches.any(), (
        f"{split}: {int(mismatches.sum())}/{len(compared)} records have different targets "
        "between released and full-feature splits. Regenerate targets consistently "
        "before comparing solvent sensitivity; old class indices are not equivalent."
    )


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
