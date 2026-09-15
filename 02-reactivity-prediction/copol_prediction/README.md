# `02-reactivity-prediction/copol_prediction/` — Pipeline 2: reactions → model + API

This is **Pipeline 2** of the repo (see the [top-level README](../../README.md) for the conceptual map). It takes the curated dataset produced by `01-data-extraction/`, computes per-monomer descriptors, trains the architecture-classification model, and serves predictions via a FastAPI service.

## Data flow

```
                processed_data.csv             ← dataset (4,969 measurement rows,
                  ▲                              3,791 unique reactions, 1,206 papers)
                  │
                  │ ↓ monomer_feature_calculation.py          (XTB descriptors)
                  │ ↓ create_data_split.py                    (grouped by reaction ID)
                  ▼
       artifacts/data_splits/{train,val,test}.csv
                  │
                  │ ↓ train_final_model.py                    (XGBoost + calibration)
                  ▼
       artifacts/model_bundle/                                ← the released model
                  │
                  │ ↓ api/app.py                              (FastAPI service)
                  ▼
       POST /predict, /preprocess_all, /optimize_reaction,  ← what powers
            /find_architecture_switch, /paper_metrics, ...     polycarp.cheminfo.org

       artifacts/model_bundle/  +  artifacts/data_splits/
                  │
                  │ ↓ reproduce_paper_metrics.py              ← regression check
                  ▼
       checked performance table + REPRODUCED on stdout
```

## Classes

The classifier predicts `0 = alternating`, `1 = random`, or `2 = gradient`.
Labels are assigned from the geometry of the Mayo–Lewis composition curve using
both reactivity ratios, rather than thresholds on their product. The
`r_product_class` column name is retained for compatibility.

See [the model card](../../MODEL_CARD.md#prediction-target) for the exact rules
and [`mayo_lewis_classification.py`](mayo_lewis_classification.py) for their
implementation. [`api/class_labels.py`](api/class_labels.py) maps class IDs to names.

## Voting model

Two architecture-prediction models cooperate:

- **XGBoost** on the XTB-derived feature vector — the classifier proper.
- **Lookup**: the architecture of the top-1 nearest-neighbour literature reaction (Tanimoto on Morgan fingerprints of the monomer pair + solvent).

The **voting** layer keeps only predictions where the two agree (the "coverage" metric in the paper). Disagreement is exposed on every `/preprocess_all` response so the web UI can flag low-confidence cases.

## Layout

```
02-reactivity-prediction/copol_prediction/
├── processed_data.csv                   ← live dataset (the API reads this for the
│                                          nearest-neighbour lookup pool)
│
├── create_data_split.py                 ← reaction-ID-grouped 70/10/20 split
├── train_final_model.py                 ← XGBoost training + calibration
├── monomer_feature_calculation.py       ← XTB descriptor pipeline
├── mayo_lewis_classification.py         ← Mayo–Lewis curve → class assignment
├── reproduce_paper_metrics.py           ← canonical regression check
├── preprocess_splits_full_features.py   ← splits with full feature set (perm. importance)
├── REPRODUCE.md                         ← reproduction recipe details
│
├── analysis/                            ← paper figures (plot_model_figure, plot_class_curves)
├── api/                                 ← FastAPI service deployed at polycarp.cheminfo.org
├── filter/                              ← curation + augmented-negatives pool
├── utils/                               ← load_data_split helpers
│
└── artifacts/
    ├── model_bundle/                    ← XGBoost model + calibration + metadata
    ├── data_splits/                     ← train/val/test (6,774 rows / 3,387 reactions)
    ├── data_splits_full_features/       ← splits with descriptors for permutation analysis
    └── paper_metrics.json               ← output of reproduce_paper_metrics.py --json
                                           served unmodified by GET /paper_metrics
```

### First-time evaluation

Install the locked environment using the [reviewer guide](../../REPRODUCIBILITY.md),
then run the following from this directory with that environment activated:

```bash
python reproduce_paper_metrics.py
```

The released splits and descriptors are already included. This evaluates the
bundled XGBoost and voting models and checks the paper table to tolerance 0.005.
The re-splitting and training commands below are for developing a new model.

### Re-split the dataset

```bash
python create_data_split.py
```

Reads `processed_data.csv`, removes invalid/missing reactivity-ratio products and
rows with missing model features, and groups by **`reaction_id`**. Existing test
and validation group IDs are reused; otherwise `GroupShuffleSplit` creates
approximately 70/10/20 train/validation/test groups (seeds 42 and 43).
Mirrored monomer orderings stay together. Monomer pairs and publications can
occur in more than one split. This tests held-out reactions, not strictly unseen
monomer pairs or publications. The committed split files define the released
results; running this script rewrites them.

### Retrain the model

```bash
python train_final_model.py

# Or test all filter combinations (~3 hours)
cd ../../03-experiments/filter_comparison && python sweep_filters.py
```

Reads the splits and searches 100 hyperparameter configurations using five-fold
cross-validation grouped by `reaction_id` within the training set. It fits the
final XGBoost model on the training set and fits isotonic calibration on the
validation voting subset. The test set is reserved for evaluation. See the
[model card](../../MODEL_CARD.md#training) for the released configuration.
Retraining overwrites the model bundle and may change results; evaluating the
released bundle with `reproduce_paper_metrics.py` does not require retraining.

### Compute monomer descriptors

```bash
python monomer_feature_calculation.py
```

Runs XTB for each unique monomer SMILES that doesn't yet have a cached descriptor file under [`api/molecule_properties/`](api/molecule_properties/). First-time computation per monomer takes ~1–5 min; subsequent runs are cached.

### Serve the API locally

See [`api/README.md`](api/README.md). One-liner with Docker:

```bash
cd api && docker compose up
```

## Library entry point

```python
from copolpredictor.inference import CopolymerPredictor

predictor = CopolymerPredictor("artifacts/model_bundle")
result = predictor.predict_with_confidence(features)
```

See [`src/copolpredictor/`](../../src/copolpredictor/) for module docs.

## Central Data Split

All scripts use a **central train/validation/test split** (created once, reused everywhere):

```bash
python create_data_split.py [--remove-specialized]
```

Creates:
- `artifacts/data_splits/train.csv` (2,369 reactions; 4,738 mirrored rows)
- `artifacts/data_splits/val.csv` (339 reactions; 678 mirrored rows)
- `artifacts/data_splits/test.csv` (679 reactions; 1,358 mirrored rows)
- `artifacts/data_splits/split_info.json`

**Scope:** Reaction IDs are disjoint across splits. This does not enforce disjoint monomer pairs or publications.

**Usage in code:**
```python
from copol_prediction.utils import load_data_split
df_train, df_test = load_data_split.load_train_test_split()
```

## Scripts

The timings below are legacy estimates without a recorded reference machine.
For measured installation and demo timings, see the [reviewer guide](../../REPRODUCIBILITY.md).

| Script | Purpose | Time |
|--------|---------|------|
| `train_final_model.py` | Train production model + analysis | ~20 min |
| `analysis/analyze_model.py` | Generate analysis plots | < 1 min |
| `../../03-experiments/filter_comparison/sweep_filters.py` | Test 16 filter combinations | ~3 hours |
| `create_data_split.py` | Create central split | < 1 min |
| `monomer_feature_calculation.py` | Calculate molecular features | 1-5 min/monomer |
| `api/app.py` | REST API server | Instant |

### train_final_model.py

Trains model with hyperparameter optimization and **automatically runs analysis**.

```bash
python train_final_model.py [options]

Options:
  --output-dir DIR         Model directory (default: artifacts/model_bundle)
  --hyperparam-iter N      Search iterations (default: 100)
  --augmentation-samples N Augmentation samples (default: 5)
  --random-state N         Random seed (default: 42)
```

**Released configuration** (see `main()` and artifact `meta.json`):
```python
config = {
    'add_negative_data': False,    # Add synthetic negatives
    'use_augmentation': False,    # Gaussian augmentation
}
```

### analysis/analyze_model.py

Generate analysis plots (automatically runs after training).

```bash
python analysis/analyze_model.py --all [--compare-holdout]

Key options:
  --compare-holdout        Generate plots for all data + holdout
  --holdout-only          Only holdout set
  --filtering             Dynamic confidence filtering
  --min-retention N       Min retention rate (default: 0.7)
```

**Generated plots:**
- Confusion matrices (absolute & normalized)
- Confidence distributions (correct vs incorrect)
- Feature importance
- Calibration curves per class
- Error analysis by class
- Confidence vs r-product
- Confidence filtering analysis

### ../../03-experiments/filter_comparison/sweep_filters.py

Tests all 16 filter combinations (4×4 matrix) on same holdout set.

```bash
cd ../../03-experiments/filter_comparison
python sweep_filters.py [--n-iter N]
```

**Combinations tested:**
- Rows: `remove_specialized` × `add_negative_data` (4 combos)
- Cols: `use_augmentation` × `apply_polymerization_filter` (4 combos)

Results saved to `artifacts/experiments_holdout/` with heatmap visualizations.

## Python API

```python
from copolpredictor.inference import CopolymerPredictor, batch_predict

# Single prediction
predictor = CopolymerPredictor("artifacts/model_bundle")
result = predictor.predict_with_confidence(features)
# Returns: {'predictions': [1], 'probabilities': [...], 'confidence': [0.85]}

# Batch prediction
batch_predict("input.csv", "output.csv")
```

## REST API

```bash
cd api && python app.py  # Runs at http://localhost:8000
```

**See [`api/README.md`](api/README.md) for full API documentation.**

**Endpoints:**
- `GET /health` - Health check
- `GET /model/info` - Model metadata
- `POST /predict` - Single prediction
- `POST /predict/batch` - Batch predictions
- `GET /docs` - Interactive API documentation (Swagger UI)

**Example:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"features": {...}}'
```

## Data Format

**Required columns:**
- `monomer1_smiles`, `monomer2_smiles` - SMILES strings
- `constant_1`, `constant_2` - Reactivity ratios (r₁, r₂)
- `temperature`, `solvent_smiles`, `polymerization_type`, `method`
- `reaction_id` - Unique group identifier

## Features

~15 features used:
- **Molecular:** Fukui indices, HOMO/LUMO, orbital interactions
- **Conditions:** Temperature, solvent properties (logP, TPSA, HBD, FractionCSP3)
- **Embeddings:** Method and polymerization type (PCA-reduced)

## Model Pipeline

1. Load central train/validation/test split (group-based, ~20% test)
2. Optional: Add negative data, augmentation
3. Hyperparameter search (RandomizedSearchCV, 5-fold GroupKFold)
4. Train final model on full training set
5. Evaluate on holdout
6. Save model bundle + metadata
7. Generate analysis plots

## Performance

Typical holdout results:
- **Accuracy:** 75-85%
- **F1 (weighted):** 0.75-0.85

**Confidence interpretation:**
- \> 0.8: High confidence
- 0.6-0.8: Medium confidence
- < 0.6: Low confidence (validate experimentally)

## Project Structure

```
02-reactivity-prediction/copol_prediction/
├── train_final_model.py       # Main training script
├── monomer_feature_calculation.py
├── utils/                      # Utility functions
│   ├── __init__.py
│   └── load_data_split.py     # Load central split utility
├── api/                        # REST API
│   ├── app.py                  # FastAPI application
│   ├── README.md               # API documentation
│   ├── baseline_lookup.py      # Nearest-neighbor lookup
│   ├── reaction_optimization.py # Solvent / temperature grid search
│   ├── morfeus_patch.py        # XTB compatibility patch
│   ├── requirements.txt
│   ├── Dockerfile              # Docker deployment
│   ├── compose.yaml            # Docker Compose config
│   ├── data/                   # PCA embeddings
│   └── molecule_properties/    # Precomputed monomer features
├── analysis/                   # Analysis tools
│   ├── analyze_model.py       # Main analysis script
│   ├── plot_config.py          # Plot styling
│   └── lamalab.mplstyle        # Plot style file
├── artifacts/
│   ├── data_splits/            # Central train/test split
│   ├── model_bundle/           # Trained model
│   └── experiments_holdout/    # Sweep results
└── output/
    ├── analysis/               # Generated plots
    └── processed_data.csv      # Processed dataset

src/copolpredictor/             # Core library
├── data_processing.py
├── model_training.py
├── evaluation.py
├── inference.py                # CopolymerPredictor
└── ...
```

## Modules (src/copolpredictor/)

| Module | Purpose |
|--------|---------|
| `data_processing.py` | Data loading & preprocessing |
| `data_augmentation.py` | Gaussian augmentation |
| `model_training.py` | Training, CV, model saving |
| `evaluation.py` | Metrics & evaluation |
| `calibration.py` | Model calibration |
| `holdout_utils.py` | Holdout set management |
| `inference.py` | CopolymerPredictor class |
| `prediction_utils.py` | Feature definitions |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Model not found | `python train_final_model.py` |
| Missing features | `python monomer_feature_calculation.py` |
| No train/test split | `python create_data_split.py` |
| API port in use | `lsof -ti:8000 \| xargs kill` |
| Quick test | `python train_final_model.py --hyperparam-iter 5` |

## Common Commands

```bash
# Quick test (fewer iterations)
python train_final_model.py --hyperparam-iter 5

# Manual analysis (if needed)
python analysis/analyze_model.py --all --compare-holdout

# Recreate data split
python create_data_split.py

# Kill API
lsof -ti:8000 | xargs kill

# Run specific analysis
cd analysis && python analyze_model.py --confusion --confidence --features
```

## Notes

- **Plot Styling:** All plots use LamaLab matplotlib style from `analysis/plot_config.py`
- **Confidence Filtering:** Dynamic thresholding per class to improve accuracy
- **Reproducibility:** Fixed random seed (42), central split ensures consistency
- **Legacy:** Old `classification.py` kept for reference, use new modular scripts

## Migration from classification.py

Old monolithic script → New modular system:
- `classification.py::main()` → `train_final_model.py`
- `classification.py::sweep_filters_and_plot()` → `../../03-experiments/sweep_filters.py`
- Manual model loading → `CopolymerPredictor` class

All functionality preserved in new modules under `src/copolpredictor/`.
