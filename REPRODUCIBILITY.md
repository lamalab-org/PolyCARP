# Reproduce PolyCARP

Run the released model on the bundled data to reproduce the paper's train/test
table. The demo runs locally on a CPU with cached descriptors and model weights.
It needs no API key or new quantum-chemistry calculations.

## Install and run

Install Git and [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```bash
git clone https://github.com/lamalab-org/PolyCARP.git
cd PolyCARP
uv sync --locked --python 3.12.11 --extra reproduction
uv run --locked --extra reproduction python 02-reactivity-prediction/copol_prediction/reproduce_paper_metrics.py
```

Installation requires internet access and creates `.venv` with versions pinned
in [uv.lock](uv.lock). Record the submission's commit with `git rev-parse HEAD`.
The package requires Python >=3.11; the environment below was tested.

## Expected result and measured runtime

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

The demo evaluates the saved training and test sets, using training rows for
lookup. It leaves data and weights unchanged and exits nonzero if a table value
differs by more than 0.005. [CI](.github/workflows/reproduce-paper.yml) runs the
same check. `--json PATH` exports predictions but bypasses that failure exit.
See [REPRODUCE.md](02-reactivity-prediction/copol_prediction/REPRODUCE.md) for metric
definitions and API comparison.

| Verification on 15 September 2026 | Result |
|---|---|
| Machine | Apple M4 Max, arm64, 16 CPU cores, 64 GiB RAM; CPU only |
| Software | macOS 26.5.1 (25F80), Python 3.12.11, uv 0.8.16 |
| Clean installation | 17.4 s; empty package cache; excludes Git clone and Python/uv installation |
| First demo run | 101.4 s, including imports and an empty matplotlib cache |
| Existing tests | 100 passed after adding `--extra testing`; chemical-name tests need internet |

These measurements describe one machine, not minimum requirements or historical
training costs. Windows was not tested. The headless run used `MPLBACKEND=Agg`
and a writable `MPLCONFIGDIR`. [Verification data](docs/reproducibility/verification.json)
record every package version and artifact hash; [demo output](docs/reproducibility/demo-output.txt)
records the results.

The historical model files produce scikit-learn/XGBoost version warnings
(the isotonic estimator records scikit-learn 1.6.1); RDKit emits deprecation
warnings. The tests verify the reported table and class predictions, not exact
probability equivalence across library versions.

## Use your own data

For recipes, use the [web tool](https://polycarp.cheminfo.org) or
[local API](02-reactivity-prediction/copol_prediction/api/README.md). Enter two
monomer SMILES, solvent, temperature in °C, and polymerization type. The API
returns predictions and literature analogues. Its Docker environment includes
XTB; calculating descriptors for new monomers adds time beyond the demo above.

For features generated with the model's preprocessing, save this as
`predict_features.py` in the repository root:

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
Try the bundled `02-reactivity-prediction/copol_prediction/artifacts/data_splits/test.csv`
as input. This returns XGBoost predictions; voting also needs the lookup in the
API or reproduction script. Required feature names are in the bundle's `meta.json`.

## Records still needed

The [model card](MODEL_CARD.md) covers data, splits, training, evaluation, and
limitations. For the Nature Portfolio [software](https://www.nature.com/documents/nr-software-policy.pdf)
and [ML](https://www.nature.com/documents/machine-learning-checklist.pdf) checklists,
authors still need to establish:

- The dated extraction-model snapshot: the code's `chatgpt-4o-latest` alias changes over time.
- Original training/extraction hardware and runtime.
- Whether the optional CV-pruning file recorded in model metadata was present and used.
- Whether a colleague unfamiliar with the software tested it; author declarations and laboratory replicate counts.

The measurements above document this later verification run.
