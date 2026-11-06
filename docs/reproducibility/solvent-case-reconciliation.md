# Solvent case: reproduction failure and suggested correction

Status: proposed correction for scientific review, 6 November 2026. The code
changes prevent silent substitution of old predictions. They do not establish
new experimental ground truth or repair the model's solvent sensitivity.

## Supplied experimental ratios (6 November 2026)

The user supplied the following ratios for the nine existing solvent rows.
They are stored as `r1` (acrylamide) and `r2` (styrene) in
`case_study_features.csv`; this monomer order is an assumption, and the values
have not been independently checked against the original source table.
The plot now derives reference classes from these ratios using
`classify_reactivity_curve` with the same defaults as training. The CSV's
`minsk_class`, model outputs and agreement flags remain historical artifacts;
the old reference labels are no longer used for plot correctness.

| Solvent | r1 | r2 | Current curve class |
|---|---:|---:|---|
| Benzene | 12.5 | 0.25 | gradient |
| o-Dichlorobenzene | 12.5 | 0.25 | gradient |
| Benzonitrile | 2.4 | 1.35 | random |
| Dioxane | 1.38 | 1.27 | random |
| Bis(2-methoxyethyl) ether | 1.09 | 1.40 | random |
| Ethanol | 0.30 | 1.44 | gradient |
| 2-(2-Methoxyethoxy)ethanol | 0.27 | 1.66 | gradient |
| DMSO | 0.16 | 2.01 | gradient |
| Methanol | 0.20 | 1.05 | gradient |

These produce six gradient and three random references, with no alternating
references. Against the current model/lookup outcomes recorded below, all six
retained voting predictions match these supplied references, and the three
random cases abstain. This comparison does not resolve source identity,
concentration or training overlap. The missing model descriptors still prevent
regenerating the plot, and the historical paper-claim regression expectations
remain unchanged pending scientific reconciliation.

## What reproduces, and what does not

The released aggregate train/test table reproduces within its existing ±0.005
tolerance in the locked Python 3.12 environment. Test voting macro-F1 is 0.785
and coverage is 0.770. This finding concerns the separate historical solvent
case; it does not invalidate that aggregate reproduction or audit the
prospective laboratory experiments.

The solvent CSV contains the old saved `model_class`, `minsk_class` and
`agreement` values, but only six of the released model's 19 required feature
columns. The previous plotting script caught the resulting error and reused
`model_class` from that CSV. A newly generated figure could therefore look
current without having recomputed its predictions.

The new local regression runs preprocessing, the released model and the real
lookup using cached monomer descriptors. No production API or new XTB run is
used. Both monomer orders give the same classes and voting outcomes:

| Solvent input in case-study code | Paper/saved voting claim | Current XGBoost | Current lookup | Current voting |
|---|---|---|---|---|
| Benzene | random | gradient | gradient | gradient |
| o-Dichlorobenzene | random | gradient | gradient | gradient |
| Benzonitrile | random | gradient | random | abstain |
| Dioxane | random | gradient | random | abstain |
| Bis(2-methoxyethyl) ether | abstain | gradient | random | abstain |
| Ethanol | alternating | gradient | gradient | gradient |
| 2-(2-Methoxyethoxy)ethanol | alternating | gradient | gradient | gradient |
| DMSO | abstain | gradient | gradient | gradient |
| Methanol | alternating | gradient | gradient | gradient |

Thus eight of nine historical voting outcomes differ. This is **not** a new
experimental accuracy score: the original experimental ratios have not yet
been independently re-extracted and assigned with the current curve rules.
The fixture retains the manuscript/saved claims as a regression target rather
than silently making the model's current output the new truth.

## Minsk context: distinguish the two publications

- [Minsk, Kotlarchik and Darlak, February 1973](https://doi.org/10.1002/pol.1973.170110204),
  *Effect of solvents upon the copolymerization of acrylamide and styrene*,
  is the source cited for the solvent series. Its abstract links solvent effects
  to hydrogen bonding/dipolar interactions and infrared changes, with large
  changes in acrylamide incorporation and reactivity ratios. It supports the
  importance of solvent conditions, but does not independently verify our
  three-class assignments or model accuracy.
- [Minsk, Kotlarchik and Meyer, December 1973](https://doi.org/10.1002/pol.1973.170111201),
  *Copolymerization of acrylamide and styrene. II. Reactivity ratios with
  unperturbed acrylamide*, deliberately used high dilution in benzene to reduce
  amide–amide interactions. Its abstract reports acrylamide-first ratios
  9.14 ± 0.27 and 0.67 ± 0.08. This is the publication behind training reaction
  443, not an independent extraction of the February solvent table.

The second record has the same **encoded inputs** as the benzene/90 °C query;
all 19 model features agree to numerical precision. It does not follow that
the physical experiments are duplicates. Concentration/dilution is absent from
the feature vector and can distinguish the experiments. Describe this as
input-space overlap and a possible omitted-condition limitation, rather than
asserting experimental duplication or proven leakage. The claim that this
monomer pair was excluded from training is nevertheless incorrect.

There is also a solvent-identity ambiguity: the manuscript text names
2-methoxyethanol, whereas the code names 2-(2-methoxyethoxy)ethanol and uses
`COCCOCCO`. The tests explicitly retain the code's input identity; the source
table must settle which input belongs in the final scientific evaluation.

For the **December** ratio pair, the current curve classifier gives integral
deviation approximately 0.23149 with no interior diagonal crossing: gradient.
Its product, approximately 6.1238, belonged to the older middle product bin.
This illustrates why historical class indices cannot simply be relabelled
under the new definition. It does not determine the February series' classes.

## Suggested manuscript correction

Pending source-level reconciliation, remove the solvent figure and the
seven-correct/two-abstention statement from the validated-performance claims.
If retaining a transparent limitation paragraph, proposed wording is:

> The historical acrylamide–styrene solvent case requires reanalysis under the
> final curve-based class definitions and released model. Its archived
> predictions could not be reproduced with the current preprocessing and model
> artifacts, so we exclude this case from our validated-performance claims
> pending reconciliation. Related measurements for the same monomer pair occur
> in training; matching encoded conditions can conceal differences in dilution
> that are not represented by the model.

Avoid retaining the old figure with only its caption changed: its predictions,
reference classes and abstention flags all need a consistent regeneration.

## Resolution needed before this draft becomes mergeable

### Diagnostic sequence for the predominantly gradient predictions

First determine the reference classes from the original experimental ratios.
Nine solvent conditions for one pair are not nine independent monomer-pair
tests. Substantial changes in a composition curve may remain within one broad
class; if the final reference classes are all gradient, this is unsuitable as
a demonstration of class switching rather than evidence of model collapse.

If verified reference classes differ, trace the complete input vectors and
class-probability changes before modifying the model. The released 19-feature
model represents solvent only through logP and fraction of sp³ carbons. Its
remaining 17 features stay fixed in this solvent sweep. Hydrogen-bonding and
polarity descriptors, concentration and interaction features are therefore
candidates to evaluate, not established fixes. Check their benefit on separate
condition/solvent groups and preserve an untouched final test set. Avoid tuning
class weights simply to force diverse labels on this one series.

The aggregate results rule out a classifier that always predicts gradient
across the full test set, but do not guarantee solvent sensitivity within this
particular monomer pair. Inspect actual probability changes as well as the
winning class.

A follow-up local API diagnostic confirms that all 19 required descriptors
are present and finite for these nine inputs. Only `solvent_logp` and
`solvent_FractionCSP3` vary; the other 17 inputs remain fixed. The API's returned
probabilities form four groups (percentages rounded here):

| Solvents | Alternating | Random | Gradient |
|---|---:|---:|---:|
| Benzene, o-dichlorobenzene, benzonitrile | 0.97 | 17.09 | 81.93 |
| Dioxane, bis(2-methoxyethyl) ether | 3.91 | 16.59 | 79.50 |
| Ethanol, 2-(2-methoxyethoxy)ethanol, DMSO | 1.46 | 17.01 | 81.53 |
| Methanol | 1.55 | 19.99 | 78.46 |

This is a weak output response to the solvent sweep, not a frozen API result:
some probabilities change, but none changes the winning class. Identical
probability vectors for chemically distinct solvents strengthen the reason to
audit the learned solvent response. They do not prove a feature-computation
bug, determine the correct reference classes, or establish that richer
descriptors will improve generalization. These measurements used the same
locked local environment, released bundle and cached descriptors as the new
paper-case checks; they are diagnostic observations, not new regression targets
that require future models to retain the all-gradient outcome.

### Scientific reconciliation

1. Read the original February table and record each solvent's identity,
   temperature, concentrations, ratio values, uncertainties and monomer order.
   Keep the December high-dilution measurements as a distinct source.
2. Recompute reference classes from those ratios with the final Mayo–Lewis
   classification code. Do not reuse `minsk_class` from the old product bins.
3. Rebuild complete descriptors and recompute model, lookup and voting results
   using one recorded model bundle, preprocessing version and lookup pool.
   Assess concentration as an omitted input; do not infer equivalence from
   identical current descriptors.
4. Regenerate the figure and revise the manuscript to the verified result.
   Update the reference fixture only alongside that documented scientific
   correction, not simply to copy current model predictions.
5. Require the paper-case checks and aggregate reproduction to pass. The new
   case checks deliberately remain failures while the published/artifact
   inconsistency is unresolved; they are not skipped or marked `xfail`.
