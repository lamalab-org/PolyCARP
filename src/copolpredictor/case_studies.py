"""Strict feature validation for reproducing scientific case studies."""

from collections.abc import Sequence

import numpy as np
import pandas as pd


def case_study_features(frame: pd.DataFrame, required: Sequence[str]) -> pd.DataFrame:
    """Reject stale or incomplete descriptors before inference can zero-fill them.

    Scientific figures must be recomputed with the selected model. A missing
    descriptor or failed prediction must not be replaced by a saved prediction.
    Extra columns (e.g. experimental labels) are allowed but never used as input.
    """
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise ValueError(
            f"Case-study features are incompatible with the model: missing {len(missing)} "
            f"of {len(required)} required columns: {', '.join(missing)}. "
            "Regenerate the descriptors; saved predictions are not a substitute."
        )
    if frame.empty:
        raise ValueError("Case-study feature table is empty.")
    features = frame[list(required)].apply(pd.to_numeric, errors="raise")
    invalid = ~np.isfinite(features.to_numpy(dtype=float))
    if invalid.any():
        columns = features.columns[invalid.any(axis=0)].tolist()
        raise ValueError(f"Case-study features contain missing or non-finite values: {columns}")
    return features
