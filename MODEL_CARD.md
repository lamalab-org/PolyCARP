# PolyCARP model card

## Model and intended use

PolyCARP supports experimental planning by predicting an alternating, random,
or gradient copolymerization regime from monomer structures and reaction
conditions. It combines a three-class XGBoost classifier with a nearest-neighbour
literature lookup. The voting prediction is retained when the two agree.
Researchers can inspect the retrieved experimental precedents before choosing
a recipe. The model does not predict an exact chain sequence, self-assembly,
yield, or the success of a synthesis.

Authors: Mara Schilling-Wilhelmi, Boris Bulgakov, Luc Patiny, Sarthak Kapoor,
and Kevin Maik Jablonka. Contact: kevin.jablonka@uni-jena.de.
Code license: [MIT](LICENSE). Paper: [Condition-aware prediction of copolymer
architecture](https://doi.org/10.26434/chemrxiv.15004102/v2).

The released bundle is in
[`artifacts/model_bundle/`](02-reactivity-prediction/copol_prediction/artifacts/model_bundle/).
Its `meta.json` records the creation timestamp as 2026-04-28 and defines the
19 input features, hyperparameters, class weights, and calibration settings.
Use the repository commit together with the bundle to identify a version;
the live service may evolve independently.

## Prediction target

Labels are derived from both reactivity ratios through the Mayo–Lewis
composition curve, using
[`mayo_lewis_classification.py`](02-reactivity-prediction/copol_prediction/mayo_lewis_classification.py).
The name `r_product_class` is historical: product thresholds alone do not
define the current labels. Let `I_rand` be the integrated absolute deviation
from the diagonal and `d` the distance of the nearest interior diagonal
crossing from feed fraction 0.5. Rules are applied in this order:

1. Random (`1`) if `I_rand < 0.02`.
2. Alternating (`0`) if `I_rand >= 0.14` and an interior crossing has `d <= 0.06`.
3. Gradient (`2`) if `I_rand >= 0.08` and there is no interior crossing or `d >= 0.3`.
4. Random (`1`) otherwise, including weak deviations from ideal randomness.

These are operational, coarse labels inferred from reactivity ratios; they
are not direct measurements of every synthesized chain's sequence.

## Data and preprocessing

The curated literature resource contains 3,791 reactions from 1,206 publications.
Source provenance accompanies the records in `processed_data.csv`. The pipeline
combines literature measurements, standardized chemical structures and conditions,
and calculated monomer descriptors. See
[`01-data-extraction/`](01-data-extraction/README.md) for extraction and curation.

The released modelling splits contain 3,387 reaction IDs represented in both
monomer orderings (6,774 rows). Invalid/missing reactivity-ratio products and
rows with missing required descriptors are removed. The 19 inputs comprise
monomer electronic descriptors, cross-monomer frontier-orbital differences,
temperature, polymerization-type embeddings, and solvent descriptors. Their
exact names and order are in the bundle's `meta.json`.

### Split and scope of generalization

| Split | Reaction IDs | Mirrored rows | Alternating / random / gradient rows |
|---|---:|---:|---:|
| Training | 2,369 | 4,738 | 230 / 2,044 / 2,464 |
| Validation | 339 | 678 | 46 / 240 / 392 |
| Test | 679 | 1,358 | 68 / 620 / 670 |

The committed [`data_splits/`](02-reactivity-prediction/copol_prediction/artifacts/data_splits/)
files are the reference partitions. `create_data_split.py` groups by
`reaction_id`, reuses saved group IDs, or creates new approximately 70/10/20
partitions with `GroupShuffleSplit` (seeds 42 and 43). It is not a class-stratified,
chronological, or monomer-pair-disjoint split. Mirrored rows of a reaction stay
together. Monomer pairs and publications can occur across partitions, so these
results assess held-out reactions within the literature domain; they do not
establish performance on wholly unseen monomer pairs or publications. Mirrored
rows must not be treated as independent experimental replicates.

## Training

[`train_final_model.py`](02-reactivity-prediction/copol_prediction/train_final_model.py)
searches 100 configurations using five-fold `GroupKFold` by reaction ID within
the training partition, optimizing weighted F1 with inverse-frequency class
weights. The final classifier is fitted on the training partition. Isotonic
probability calibration is fitted on the validation voting subset; the test
partition is reserved for evaluation. The random seed is 42. Released metadata
reports no Gaussian augmentation or synthetic negative data.

Selected parameters: 500 boosting rounds, depth 6, learning rate 0.06,
subsample 0.85, column subsample 0.9, minimum child weight 2, gamma 0.3,
L1 regularization 0.3, and L2 regularization 2.0. Full search ranges are in the
training script. Search uses `n_jobs=-1`; historical training hardware and
wall-clock runtime have not been established from the released metadata.

## Evaluation

The released plain classifier has test accuracy 0.740 and macro F1 0.708.
The voting model retains 1,045 of 1,358 test rows (coverage 0.770), with
macro recall 0.805, precision 0.768, and F1 0.785 on retained predictions.
These conditional metrics should always be reported together with coverage.
Alternating is the minority class (68 test rows) and has lower retained F1
(0.722) than random (0.796) or gradient (0.836).

[`reproduce_paper_metrics.py`](02-reactivity-prediction/copol_prediction/reproduce_paper_metrics.py)
recomputes the train/test table using the bundled classifier and a train-only
fingerprint lookup pool, checking published values to tolerance 0.005. The API
can use a larger literature lookup pool; that is distinct from the evaluation
pool. See [REPRODUCE.md](02-reactivity-prediction/copol_prediction/REPRODUCE.md).

The manuscript additionally reports a nine-solvent historical case study
(seven correct predictions and two abstentions), three prospective laboratory
copolymerizations (two matching predictions), feature-importance analyses, and
condition-feature ablations. Three prospective experiments provide limited
evidence of laboratory utility, not a precise estimate of general success rate.

## Limitations and responsible interpretation

- Literature selection, publication practices, extraction errors, and uneven
  coverage of monomers, mechanisms, and conditions can bias predictions.
  Quality filtering and access to source precedents support review of a
  prediction but do not eliminate these biases.
- Class balancing addresses training imbalance; macro metrics expose differences
  between classes. Neither ensures equal reliability across chemical subdomains.
- Agreement between two predictors is an abstention rule, not proof of correctness
  or a guarantee that a new recipe lies within the training domain.
- Evaluate genuinely new monomer families, unusual conditions, and extrapolated
  recipes experimentally. Interpret the output alongside retrieved precedents.
- The original literature-extraction code uses the mutable model alias
  `chatgpt-4o-latest`. A dated historical snapshot is not established by that
  alias. Released curated data support downstream reproduction without replaying
  extraction; exact historical API replay is not guaranteed.

## Reproduction and reporting

The [reviewer guide](REPRODUCIBILITY.md) supplies installation, demo, own-data
instructions, measured resources, and links to evidence for journal reporting.
It distinguishes newly measured inference resources from historical training
and extraction resources.
