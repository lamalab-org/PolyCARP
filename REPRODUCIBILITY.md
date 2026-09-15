# Reviewer guide: installation, demo, and reporting evidence

This guide provides a self-contained route to evaluate the released PolyCARP
model and reproduce the paper's train/test performance table. It uses committed
data, descriptors, and model weights; no API key, external prediction service,
GPU, or new quantum-chemistry calculations are needed for this demo.

## System requirements and tested environment

The package requires Python >=3.11. The offline reproduction was verified on
2026-09-15 with macOS 26.5.1 (build 25F80), Apple M4 Max (arm64, 16 CPU cores),
64 GiB RAM, Python 3.12.11, and uv 0.8.16. It ran on the CPU. These describe a
tested machine, not minimum hardware requirements. Windows has not been
verified by this check. The repository also contains Ubuntu CI for tests and
for the table-reproduction command.

Dependencies and platform-specific distributions are pinned in [`uv.lock`](uv.lock).
The `reproduction` extra includes the plotting imports required by the analysis
helpers. The verified environment used NumPy 2.4.6, pandas 3.0.3, scikit-learn
1.8.0, XGBoost 3.2.0, RDKit 2026.3.2, matplotlib 3.10.9, and seaborn 0.13.2.
The full installed package list, artifact hashes, and measurements are in
[`verification.json`](docs/reproducibility/verification.json).

## Installation

Install Git and [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
git clone https://github.com/lamalab-org/PolyCARP.git
cd PolyCARP
uv sync --locked --python 3.12.11 --extra reproduction
```

This creates `.venv` and installs the package and locked dependencies. Internet
access is needed for cloning and dependency installation. Keep the checkout
at the commit associated with the submission. `git rev-parse HEAD` records it.

The measured installation took **17.4 seconds** with a fresh virtual environment
and empty uv package cache on the machine above. Python and uv were already
installed. This excludes downloading the repository or Python; network speed
and the availability of prebuilt packages affect total setup time.

## Demo and expected output

Run from the repository root:

```bash
uv run --locked --extra reproduction python 02-reactivity-prediction/copol_prediction/reproduce_paper_metrics.py
```

The test data are the bundled `artifacts/data_splits/test.csv` (1,358 rows,
679 reaction IDs). The command also evaluates the training partition and
constructs the nearest-neighbour lookup using training rows only. It does not
retrain or alter the released model or partitions.

Expected test output:

```text
Test — voting model (retained 1045/1358, coverage 0.770)
Class             Acc    Prec      F1
Alternating     0.788   0.667   0.722
Random          0.781   0.812   0.796
Gradient        0.845   0.827   0.836
Macro           0.805   0.768   0.785
coverage        0.770
REPRODUCED: all values within ±0.005 of the paper table.
```

The measured demo took **101.4 seconds** in a first run after installation,
including imports and an initially empty matplotlib configuration cache.
`MPLBACKEND=Agg` and a writable `MPLCONFIGDIR` were used in this headless check.
The complete standard output is in [`demo-output.txt`](docs/reproducibility/demo-output.txt).
RDKit can additionally print deprecation warnings; success is determined by
the metric comparisons and exit code 0. These are single-machine measurements,
not a benchmark over multiple desktop configurations.

The existing 100-test suite also passed in this environment after installing
`--extra testing`; some chemical-name tests require public resolver access.
Loading the historical serialized artifacts produces scikit-learn/XGBoost
version warnings (the isotonic estimator records scikit-learn 1.6.1). The checks
verify released class predictions and the reported table under the documented
versions; they do not establish general serialization compatibility or exact
probability equivalence across arbitrary library versions.

The script exits nonzero on a metric discrepancy greater than 0.005. The
dedicated [CI workflow](.github/workflows/reproduce-paper.yml) runs this check
against the locked environment. `--json PATH` exports metrics and individual
predictions but bypasses the failure exit on table drift, so use the default
command above for validation.

## Apply the model to your own data

### From reaction recipes

Use the [web tool](https://polycarp.cheminfo.org), or the documented
[local API](02-reactivity-prediction/copol_prediction/api/README.md). Supply the
two monomer structures as SMILES, solvent, temperature in degrees Celsius, and
polymerization type. The API computes the required descriptors and returns
predictions and literature analogues. The local API's Docker environment also
provides XTB; this is a separate installation from the offline demo above.
Computing descriptors for uncached monomers takes additional time that is not
included in the offline demo measurement.

### From precomputed features

For numerical features generated using the same preprocessing as the released
model, save the following as `predict_features.py` in the repository root:

```python
import sys
import numpy as np
import pandas as pd
from copolpredictor.inference import CopolymerPredictor

model = CopolymerPredictor(
    "02-reactivity-prediction/copol_prediction/artifacts/model_bundle"
)
data = pd.read_csv(sys.argv[1])
missing = sorted(set(model.features) - set(data.columns))
if missing:
    raise ValueError(f"Missing required feature columns: {missing}")
features = data[model.features].apply(pd.to_numeric, errors="raise")
if not np.isfinite(features.to_numpy()).all():
    raise ValueError("Features must be finite; generate missing descriptors first.")
labels = {0: "alternating", 1: "random", 2: "gradient"}
data["predicted_class"] = model.predict(features)
data["predicted_architecture"] = data["predicted_class"].map(labels)
data.to_csv(sys.argv[2], index=False)
```

Run `uv run --locked --extra reproduction python predict_features.py features.csv predictions.csv`.
For a bundled example, use
`02-reactivity-prediction/copol_prediction/artifacts/data_splits/test.csv`
as the input. This produces plain XGBoost class predictions. Voting additionally
requires the fingerprint lookup used by the reproduction script or API.
The feature list is in `meta.json`; arbitrary descriptors with matching names
are not interchangeable with the original preprocessing.

## Where the reporting evidence lives

| Item | Evidence |
|---|---|
| Source and license | This repository; [MIT license](LICENSE) |
| Model card, intended use, biases, limitations | [MODEL_CARD.md](MODEL_CARD.md) |
| Released model, parameters, calibration | `02-reactivity-prediction/copol_prediction/artifacts/model_bundle/` |
| Training, validation, and test data | `02-reactivity-prediction/copol_prediction/artifacts/data_splits/` |
| Split implementation | `create_data_split.py`; `src/copolpredictor/holdout_utils.py` |
| Hyperparameter search and training | `train_final_model.py`; `src/copolpredictor/model_training.py` |
| Extraction and curation | [Extraction README](01-data-extraction/README.md); `src/copolextractor/` |
| Performance-table reproduction | [REPRODUCE.md](02-reactivity-prediction/copol_prediction/REPRODUCE.md) |
| New installation/runtime/resource measurements | [verification.json](docs/reproducibility/verification.json) |

### Historical facts still requiring author records

This guide addresses the repository requirements in the Nature Portfolio
[code/software checklist](https://www.nature.com/documents/nr-software-policy.pdf)
and [machine-learning checklist](https://www.nature.com/documents/machine-learning-checklist.pdf).
It does not certify facts absent from the archived records:

- The exact dated GPT-4o snapshot used for original extraction is not established
  by the mutable `chatgpt-4o-latest` default in `src/copolextractor/prompter.py`.
  The curated data can be reused without repeating extraction.
- Original training/extraction hardware and measured runtime must come from
  the original runs. The measurements above describe this later inference check.
- Training supports an optional CV-pruning file and the released metadata stores
  its historical path. Presence of a path alone does not establish whether a
  file was present and applied during the original run. Clarify that provenance
  before claiming exact retraining equivalence.
- Independent testing by a colleague unfamiliar with the software has not been
  established by this verification. Author declarations and laboratory replicate
  information also require author confirmation.

These items should be resolved in the manuscript/checklist with the authors'
records. Neither a software fix nor an altered train/test split can retrospectively
establish an unrecorded historical fact. The released partitions and predictions
remain the reference for the reported results.
