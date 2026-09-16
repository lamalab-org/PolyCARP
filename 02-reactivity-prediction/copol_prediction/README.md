# Copolymer prediction

This pipeline converts curated reactions into molecular descriptors, trains the
architecture classifier, and serves predictions through the
[API](api/README.md). The [model card](../../MODEL_CARD.md) describes the 19
features, label rules, data splits, training, and measured performance.

## Evaluate the released model

Follow the [installation guide](../../REPRODUCIBILITY.md), then run from the
repository root:

```bash
uv run --locked --extra reproduction python 02-reactivity-prediction/copol_prediction/reproduce_paper_metrics.py
```

The script evaluates the bundled weights and splits, then checks the paper table
to a tolerance of 0.005. [REPRODUCE.md](REPRODUCE.md) explains the metrics and API
comparison.

## Predictions

Labels are `0 = alternating`, `1 = random`, and `2 = gradient`. They come from
the Mayo–Lewis composition curve; `r_product_class` is the historical column name.

XGBoost predicts from monomer descriptors and reaction conditions. A separate
lookup finds the closest literature reaction using Morgan-fingerprint Tanimoto
similarity. The voting model retains predictions when the two agree; coverage
is the fraction retained. The API exposes their agreement and literature matches.

## Files

| Path | Purpose |
|---|---|
| [processed_data.csv](processed_data.csv) | Curated measurements; API lookup pool |
| [paper_dataset](paper_dataset/README.md) | Frozen paper dataset |
| [artifacts/data_splits](artifacts/data_splits/) | Released train, validation, and test sets |
| [artifacts/model_bundle](artifacts/model_bundle/) | Weights, calibration, feature list, and training metadata |
| [mayo_lewis_classification.py](mayo_lewis_classification.py) | Reactivity ratios to architecture labels |
| [analysis](analysis/) | Model evaluation and figures |
| [api](api/README.md) | Recipe preprocessing, literature lookup, and prediction endpoints |
| [src/copolpredictor](../../src/copolpredictor/) | Shared preprocessing, training, calibration, and inference |
| [03-experiments](../../03-experiments/README.md) | Baselines, ablations, and case studies |

## Train a new model

Install the `training` extra and activate the environment. Run these commands
from this directory as needed:

```bash
python create_data_split.py
python train_final_model.py --hyperparam-iter 100
```

These commands use the bundled data and descriptors. The split script reuses
saved validation/test reaction IDs when available; otherwise it creates a grouped
70/10/20 split. Mirrored monomer orderings stay in the same partition.

Training searches hyperparameters with five-fold cross-validation grouped by
reaction ID, fits XGBoost on the training set, and calibrates on the validation
voting subset. The test set supplies the final evaluation.

These commands rewrite splits or model artifacts. Use a separate
checkout when developing a model alongside the released results. Run
`python train_final_model.py --help` for training options.

## Calculate new descriptors

The API computes and caches descriptors in
[api/molecule_properties](api/molecule_properties/); its
[Docker setup](api/README.md) includes the quantum-chemistry dependencies.

The standalone `monomer_feature_calculation.py` has separate settings in `main()`:
its default input is `artificial_datapoints/augmented_temperature_only.csv` and
its output is `output/molecule_properties/`. Set these paths for your dataset
before running it. It requires Morfeus, XTB, QCEngine, geometric, and tqdm in
addition to the training dependencies; see the [API environment](api/requirements.txt).

## Predict new recipes

Use the [web tool](https://polycarp.cheminfo.org) or follow the
[local API instructions](api/README.md). For a CSV of precomputed features,
see the [Python example](../../REPRODUCIBILITY.md#use-your-own-data).
