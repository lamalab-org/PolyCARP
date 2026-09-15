# Experiments

These studies evaluate the model and produce the paper's figures.
For the released performance table, start with the
[reproduction guide](../REPRODUCIBILITY.md).

| Study | Purpose |
|---|---|
| [permutation_importance](permutation_importance/) | Permutation importance and per-class SHAP analysis |
| [baseline](baseline/README.md) | Literature lookup and model comparisons |
| [reaction_conditions_comparison](reaction_conditions_comparison/) | Ablation with and without reaction conditions |
| [case_studies/solvent](case_studies/solvent/) | Historical nine-solvent series |
| [case_studies/lab_experiments](case_studies/lab_experiments/) | Prospective experiments: kinetics, GC, NMR, and SEC |
| [feature_comparison](feature_comparison/) | Quantum descriptors versus Morgan fingerprints |
| [filter_comparison](filter_comparison/) | Data-filter and augmentation combinations |
| [case_studies/negative_data](case_studies/negative_data/) | Exploratory negative-data study |

## Run a study

Install the `training` extra, activate the environment, and run the relevant
script. For example, from the repository root:

```bash
python 03-experiments/permutation_importance/run_permutation_importance.py
python 03-experiments/reaction_conditions_comparison/run_comparison.py
python 03-experiments/case_studies/solvent/solvent_case_study.py
```

Check each study's scripts and documentation for its inputs, options, and output
paths. Model comparisons use the central saved splits where applicable; keep
those splits fixed when reproducing published comparisons. Retraining and plot
scripts may replace existing artifacts. `archive/` contains earlier experiments.
