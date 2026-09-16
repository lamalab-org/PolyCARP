# Reproduce the paper's performance table

The demo evaluates the released model on the committed train/test splits.
Follow the [installation guide](../../REPRODUCIBILITY.md), then run from the
repository root:

```bash
uv run --locked --extra reproduction python 02-reactivity-prediction/copol_prediction/reproduce_paper_metrics.py
```

It checks every cell of `tab:train_test_voting_performance` to a tolerance of
0.005 and exits nonzero on a mismatch. The guide includes expected output,
measured runtimes, and tested software versions;
[full verification output](../../docs/reproducibility/demo-output.txt) is also saved.

## Metrics

The table and script label per-class recall as `Recall`. Saved JSON retains the
legacy key `acc` for compatibility. All voting metrics below are calculated
**after abstentions are removed**.

The voting model retains predictions when XGBoost and the nearest-neighbour
lookup agree. Lookup uses training rows only, keeping evaluation separate from
the API's potentially larger literature pool.

| Quantity | Definition |
|---|---|
| `Recall` (per class) | correct predictions of class c / retained rows whose true class is c |
| `Prec` (per class) | Precision: correct predictions of class c / retained rows predicted as c |
| `F1` | Harmonic mean of precision and recall |
| `coverage` | Retained predictions divided by all samples in the split |
| `Macro` | Unweighted mean of each metric across the three classes; macro recall is balanced accuracy |

For example, the saved test confusion matrix has 33 retained alternating rows,
26 predicted correctly: recall is `26 / 33 = 0.788`. Overall voting accuracy is
`851 / 1045 = 0.814`; macro recall is `0.805`. These have different denominators.
See [the metric calculation](reproduce_paper_metrics.py) and
[saved confusion matrices](artifacts/paper_metrics.json).

Report voting metrics together with coverage. Plain-XGBoost accuracy is 0.9217
on training data and 0.7401 on test data. The voting model's test macro F1 is
0.785 at coverage 0.770. Artifact metrics are saved in
[all_metrics.txt](artifacts/model_bundle/all_metrics.txt) and
[voting_test_metrics.json](artifacts/model_bundle/voting_test_metrics.json).

## Compare a running API

With the environment activated, run from this directory:

```bash
python reproduce_paper_metrics.py --api http://localhost:8000
```

This calls `POST /predict/batch` for XGBoost predictions and computes the
train-only lookup locally, so both modes use the same evaluation protocol.
See [API setup](api/README.md).

To export predictions, add `--json PATH`. This option skips the nonzero exit on
metric drift; use the default command for the reproducibility check.
