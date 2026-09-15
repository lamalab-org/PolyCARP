# PolyCARP

PolyCARP predicts copolymer architecture from two monomers and a reaction recipe.
It combines machine learning with literature lookup to distinguish alternating,
random, and gradient regimes. The underlying dataset contains **3,791 reactions
from 1,206 publications**.

**[Use the web tool](https://polycarp.cheminfo.org)** ·
[Model card](MODEL_CARD.md) · [Installation and demo](REPRODUCIBILITY.md)

## Reproduce the paper

With Git and [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:

```bash
git clone https://github.com/lamalab-org/PolyCARP.git
cd PolyCARP
uv sync --locked --python 3.12.11 --extra reproduction
uv run --locked --extra reproduction python 02-reactivity-prediction/copol_prediction/reproduce_paper_metrics.py
```

The demo uses bundled data, descriptors, and weights. It checks the paper's
train/test table to a tolerance of 0.005 and exits nonzero on a mismatch.
See the [reproduction guide](REPRODUCIBILITY.md) for tested versions, hardware,
measured install and demo times, expected output, and use with your own data.

## Repository guide

The extraction pipeline turns literature into measurements. The prediction
pipeline uses those measurements to train the model and serve recipe predictions.

| Directory | Contents |
|---|---|
| [01-data-extraction](01-data-extraction/README.md) | Literature search, PDF extraction, and curation |
| [02-reactivity-prediction/copol_prediction](02-reactivity-prediction/copol_prediction/README.md) | Descriptors, training, evaluation, and analysis |
| [api](02-reactivity-prediction/copol_prediction/api/README.md) | Local API and Docker setup; [web interface source](https://github.com/cheminfo-py/polycarp.cheminfo.org) |
| [artifacts](02-reactivity-prediction/copol_prediction/artifacts/) | Released model, train/validation/test splits, and metrics |
| [paper_dataset](02-reactivity-prediction/copol_prediction/paper_dataset/README.md) | Frozen dataset used in the paper |
| [03-experiments](03-experiments/README.md) | Baselines, ablations, and laboratory and solvent case studies |
| [04-NOMAD-database](04-NOMAD-database/README.md) | Dataset-summary figures |
| [src](src/) | `copolpredictor` and `copolextractor` Python libraries |

## Development

Install optional dependencies with `uv sync --locked --extra NAME`, where `NAME`
is `extraction`, `training`, `testing`, or `database`. Combine extras as needed.
Run scripts with the same extras, for example:

```bash
uv run --locked --extra testing pytest tests
```

## Citation

```bibtex
@article{SchillingWilhelmi2026,
  title = {Condition-aware prediction of copolymer architecture},
  url = {http://dx.doi.org/10.26434/chemrxiv.15004102/v2},
  DOI = {10.26434/chemrxiv.15004102/v2},
  publisher = {ChemRxiv},
  author = {Schilling-Wilhelmi,  Mara and Bulgakov,  Boris and Patiny,  Luc and Kapoor,  Sarthak and Jablonka,  Kevin Maik},
  year = {2026},
  month = June
}
```



## License

MIT — see [LICENSE](LICENSE).
