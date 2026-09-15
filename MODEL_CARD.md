# PolyCARP model card

## Purpose

PolyCARP helps chemists choose copolymerization recipes. Given two monomers and
reaction conditions, it predicts an alternating, random, or gradient regime and
retrieves similar literature experiments. It combines XGBoost with a
nearest-neighbour lookup, retaining predictions when the two agree. These are
coarse architecture classes, not exact chain sequences or guarantees of synthesis
success.

**Authors:** Mara Schilling-Wilhelmi, Boris Bulgakov, Luc Patiny, Sarthak Kapoor,
and Kevin Maik Jablonka. **Contact:** kevin.jablonka@uni-jena.de.
[Paper](https://doi.org/10.26434/chemrxiv.15004102/v2) · [MIT license](LICENSE) ·
[Installation and demo](REPRODUCIBILITY.md).

The [released bundle](02-reactivity-prediction/copol_prediction/artifacts/model_bundle/)
was created on 2026-04-28. Its `meta.json` lists the 19 features, selected
hyperparameters, class weights, and calibration settings. Identify a release by
its repository commit; the live service may change.

## Prediction target

Labels come from the [Mayo–Lewis composition curve](02-reactivity-prediction/copol_prediction/mayo_lewis_classification.py),
using both reactivity ratios. The column name `r_product_class` is historical.
Let `I_rand` be the integrated absolute deviation from the diagonal and `d` the
distance of the nearest interior diagonal crossing from feed fraction 0.5.
Apply these rules in order:

1. Random (`1`): `I_rand < 0.02`.
2. Alternating (`0`): `I_rand >= 0.14` and an interior crossing with `d <= 0.06`.
3. Gradient (`2`): `I_rand >= 0.08` and no interior crossing or `d >= 0.3`.
4. Random (`1`): all remaining cases, including weak deviations from randomness.

## Data and splits

The [curated dataset](01-data-extraction/README.md) contains 3,791 reactions from
1,206 publications. Records in `processed_data.csv` retain source provenance.
After removing invalid or missing reactivity-ratio products and missing
required descriptors, the modelling dataset contains 3,387 reactions, each
represented in both monomer orderings. Inputs describe monomer electronics,
frontier-orbital differences, temperature, polymerization type, and solvent.

| Split | Reactions | Mirrored rows | Alternating / random / gradient rows |
|---|---:|---:|---:|
| Training | 2,369 | 4,738 | 230 / 2,044 / 2,464 |
| Validation | 339 | 678 | 46 / 240 / 392 |
| Test | 679 | 1,358 | 68 / 620 / 670 |

Use the committed [split files](02-reactivity-prediction/copol_prediction/artifacts/data_splits/)
to reproduce results. `create_data_split.py` reuses saved reaction IDs or uses
`GroupShuffleSplit` (seeds 42 and 43) for approximately 70/10/20 partitions.
Mirrored rows stay together and are not independent replicates. Monomer pairs
and publications can cross partitions: the test measures performance on held-out
reactions, not wholly unseen pairs or publications.

## Training

[Training](02-reactivity-prediction/copol_prediction/train_final_model.py) searches
100 configurations with five-fold `GroupKFold` by reaction ID within the training
set. It optimizes weighted F1, uses inverse-frequency class weights and seed 42,
and runs the search with `n_jobs=-1`. The final classifier uses the training set;
isotonic calibration uses the validation voting subset. The test set is reserved
for evaluation. Released metadata reports no Gaussian augmentation or synthetic
negative data. Search ranges are in the script; selected values are in `meta.json`.

## Evaluation

| Test model | Coverage | Accuracy | Macro F1 |
|---|---:|---:|---:|
| XGBoost | 1.000 | 0.740 | 0.708 |
| Voting | 0.770 (1,045/1,358 rows) | — | 0.785 |

Voting metrics describe retained predictions; report them with coverage.
Retained macro recall is 0.805 and precision is 0.768. Class F1 scores are
0.722 (alternating), 0.796 (random), and 0.836 (gradient).
[Reproduction](02-reactivity-prediction/copol_prediction/REPRODUCE.md) uses a
train-only lookup pool; the deployed API may search a larger literature pool.

The paper also reports feature-importance analyses, condition-feature ablations,
a nine-solvent case study (seven correct, two abstentions), and three prospective
syntheses (two matching predictions). Three syntheses give limited evidence of
laboratory utility.

## Limits

Literature selection, extraction errors, and uneven chemical coverage can bias
predictions. Quality filtering, class weighting, and source retrieval help,
but agreement between predictors does not establish reliability for an unfamiliar
recipe. Inspect the precedents and test new monomer families and unusual
conditions experimentally. Alternating is especially underrepresented: the test
set contains only 68 mirrored rows.

[Unresolved provenance](REPRODUCIBILITY.md#records-still-needed) includes the
historical extraction-model snapshot, training resources, and optional training
pruning. Released data and weights allow the demo to run without repeating
extraction or training.
