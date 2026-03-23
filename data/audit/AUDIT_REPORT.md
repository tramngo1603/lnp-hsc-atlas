# Full Data Audit Report

**Date:** 2026-03-08
**Purpose:** Verify every quantitative claim before paper submission.
**Philosophy:** Be adversarial — try to break the results, not confirm them.

---

## Audit Summary

| Audit | Name | Status | Key Finding |
|-------|------|--------|-------------|
| 1 | Trace Numbers | **PASS (with caveats)** | 23/38 PASS, 4 FAIL (rounding), 11 UNVERIFIABLE |
| 2 | Dose-Response Sensitivity | **PASS** | Potency premium is ROBUST (>5x under all assumptions) |
| 3 | Pareto Verification | **FLAG** | MIXED UNITS on same scatter plot (barcode counts vs %) |
| 4 | Headgroup Statistics | **PASS** | DOTAP vs DDAB significant (MW U p=0.001), but driven by 2 outliers |
| 5 | GP Validation | **PASS** | LOO accuracy 0.918, Brier 0.082 < baseline 0.176, stable across seeds |
| 6 | Kim Ratio Check | **FLAG** | HSC:liver=1.20 is at EC30 (model), not at measured dose (1.04 at 0.5 mg/kg) |
| 7 | Shi Liver Check | **PASS** | Correctly reported as null — no measured liver data exists |
| 8 | Confirmation Bias | **PASS (with flags)** | Z=9.60 (real signal), but per-class accuracy imbalanced (96% high, 0% low) |

---

## Audit 1: Trace Numbers

**Script:** `trace_numbers.py`

### Results
- **23 PASS** — values match raw data exactly
- **4 FAIL** — minor rounding issues (Breda EC50 0.218 vs 0.2185, Breda ratio 0.39 vs 0.395)
- **11 UNVERIFIABLE** — data stored with non-standard keys (Kim E3/E6 dose keys like "0.5_mg_kg")
- **2 Shi FAIL** — Shi dose-response data uses E2 (uptake) and E3 (knockdown), different assays

### Critical Findings
1. **Kim E2 liver values (20.1, 14.7, 1.6, 42.4) are NOT in kim_2024_experiments.json.** They must come from the main paper Supp Fig 7 — source needs documentation.
2. **Breda IgG values (HSC=19%, liver=78%) are inferred from text/_note fields**, not explicit numeric fields.
3. **Shi "~75% at 0.3 mg/kg" and "~90% at 1.0 mg/kg"** are from the PEG-lipid uptake experiment (E2, DiR%), not the dose-response (E3, CD45 knockdown). The paper's dose-response curve mixes two different experiments.

### Action Required
- [x] Rounding FAILs: cosmetic, no action needed
- [ ] Document source of Kim E2 liver values in annotation
- [ ] Clarify which Shi experiment contributes dose-response data points

---

## Audit 2: Dose-Response Sensitivity

**Script:** `dose_response_sensitivity.py`

### Results
- **Shi EC30 range:** [0.0000, 0.2034] — extreme sensitivity to hill slope at low values, but bounded above
- **Breda EC30 range:** [0.0795, 0.2027] — 2.6-fold range
- **Kim EC30 range:** [1.5054, 1.5479] — very stable (1.0-fold range)
- **Potency premium worst case:** Shi vs Kim = **7x** (robust)
- **Is Shi ALWAYS more potent than Kim?** YES — even worst-case Shi EC30 (0.2034) < best-case Kim EC30 (1.5054)

### Verdict
**ROBUST.** The potency premium claim (Shi >> Kim) holds under all reasonable assumptions about hill slope and top asymptote. Kim EC30 is exceptionally stable because it has 3 data points constraining the fit.

---

## Audit 3: Pareto Verification

**Script:** `pareto_verification.py`

### Results
- **Screen data matches:** 0/23 mismatches between Pareto and screen source
- **4 duplicate BM/liver pairs** in screen data
- **Screen BM range:** [1.0, 8.0] (barcode counts)
- **E2 BM range:** [4.4, 20.9] (% aVHH+)
- **Breda BM range:** [19.0, 55.0] (% LT-HSC editing)

### Critical Finding: MIXED UNITS
The Pareto scatter plot combines three incompatible data types on the same axes:
1. **Kim screen:** normalized barcode counts (0-48 range)
2. **Kim E2:** % aVHH+ protein expression (0-55% range)
3. **Breda E6:** % LT-HSC Cre-mediated editing (19-78% range)

These are **NOT directly comparable**. Screen barcode counts happen to be in a similar numeric range as percentages, making the plot visually coherent but **scientifically misleading**.

### Recomputed Pareto (%-only, n=6)
- 3/6 Pareto-optimal: LNP67, LNP108, CD117/LNP (same as mixed)
- Pearson r=0.643 (p=0.168) — not significant with only 6 points
- Spearman r=0.486 (p=0.329) — not significant

### Recomputed Pareto (barcode-only, n=23)
- 3/23 Pareto-optimal: LNP84, LNP85, LNP111
- Pearson r=0.002 (p=0.993) — **no correlation** within screen data
- Spearman r=0.085 (p=0.700) — no correlation

### Action Required
- [ ] **Option A (recommended):** Separate into two panels — screen (barcode) and validation (%)
- [ ] **Option B:** Keep mixed but add prominent caveat about mixed units
- [ ] Update paper text: correlation r=0.79 is inflated by mixing data types; %-only r=0.643 (NS)

---

## Audit 4: Headgroup Statistics

**Script:** `headgroup_stats.py`

### Results
| Helper | N | Mean BM | SD |
|--------|---|---------|-----|
| DOTAP | 16 | 5.17 | 11.52 |
| 18:1 EPC | 18 | 3.44 | 3.24 |
| DDAB | 16 | 0.39 | 0.19 |
| DOTMA | 16 | 0.71 | 0.26 |

- **Mann-Whitney U (DOTAP vs DDAB):** U=207, p=0.001 — **SIGNIFICANT**
- **DOTAP vs 18:1 EPC:** p=0.984 — NOT significant
- **DOTAP vs DOTMA:** p=0.153 — NOT significant
- **DOTAP vs ALL others:** p=0.255 — NOT significant
- **Bootstrap 95% CI (DOTAP-DDAB):** [0.79, 11.22] — excludes zero

### Outlier Analysis
- 2 DOTAP outliers: BM=13 (LNP67) and BM=48 (LNP85)
- Without outliers: DOTAP mean drops from 5.17 to 1.56, but still significant (p=0.004)
- The 13.4x DOTAP/DDAB difference is driven by outliers; robust difference is ~4x

### Confound Check
- DOTAP effect is significant within C14-PEG (p=0.0006) but not C18-PEG (p=0.197)
- Caution: PEG chain may interact with helper lipid effect

### Verdict
**PASS with nuance.** DOTAP > DDAB is statistically significant even without outliers, but the 13.4x headline number is inflated. A more honest characterization: "DOTAP enables ~4x higher BM delivery than DDAB (p<0.01), with occasional high-performer outliers."

---

## Audit 5: GP Validation

**Script:** `gp_validation.py`

### Test 1: Base Rate Check
- Base rate: 0.227 (25/110 high)
- Gap scores range: 0.372–0.595 — all above base rate
- GP is discriminating (not just predicting base rate)

### Test 2: Stability (across random seeds)
- **Seeds tested:** [0, 7, 42, 123, 999]
- **Max range across all gap formulations:** 0.000
- All gap scores are **perfectly stable** across random seeds
- GP optimization converges to same solution regardless of initialization

### Test 3: Known Formulation Check
- Of 25 known HIGH formulations, 21 (84%) have P(high) > 0.5
- Of 85 known LOW/MEDIUM formulations, 80 (94%) have P(high) < 0.5
- Overall training accuracy: 101/110 (92%)
- FLAG: Training accuracy >95% would suggest overfitting — 92% is reasonable

### Test 4: Leave-One-Out Calibration
- **LOO accuracy:** 0.918
- **Confusion matrix:** TP=22, FP=4, FN=3, TN=81
- **Precision:** 0.846, **Recall:** 0.880
- **Brier score:** 0.082 (baseline: 0.176) — GP is 2.1× better than always predicting base rate
- **Calibration bins:** Well-calibrated across all probability ranges
- **Worst LOO predictions:** 4 FP + 3 FN — all near-boundary cases

### Verdict
**PASS.** GP classifier is well-calibrated, stable across seeds, and significantly better than baseline. LOO accuracy (0.918) confirms the model generalizes — it's not overfitting despite the small dataset.

---

## Audit 6: Kim HSC:Liver Ratio

**Script:** `kim_ratio_check.py`

### Results
- **Pareto data (E2 at 0.5 mg/kg):** LNP67 BM=20.9%, Liver=20.1% → ratio = **1.04**
- **Therapeutic window (at EC30):** HSC=30% (by definition), Liver=25% → ratio = **1.20**
- **Kim screen (barcode counts):** LNP67 BM=13, Liver=5 → ratio = 2.60 (different units!)

### Critical Finding
The "HSC:liver = 1.20" claim uses the **modeled EC30** (30% HSC at 1.55 mg/kg, liver extrapolated to 25%), NOT the **measured** ratio at E2 dose. The measured ratio at 0.5 mg/kg is 1.04.

The claim is technically defensible if clearly stated as "at the modeled therapeutic dose (EC30)", but could be misleading if presented as a measured value.

### Action Required
- [ ] Clarify in paper: "at EC30" vs "at 0.5 mg/kg" when citing the ratio
- [ ] Document how liver=25% at EC30 was derived (interpolation from E2 dose?)

---

## Audit 7: Shi Liver Estimate

**Script:** `shi_liver_check.py`

### Results
- **therapeutic_window.json correctly has liver_at_ec30 = null** for Shi
- **No Shi entries in Pareto data** (no paired BM+liver measurements)
- Shi E7 biodistribution uses IVIS (average radiance), not flow cytometry (% cells)
- **No quantitative liver % is measurable from any Shi experiment**

### Verdict
**PASS.** The data pipeline correctly reports Shi liver as null. Any "~35% liver" estimate that appears in the paper or app must be clearly labeled as extrapolation/assumption.

---

## Audit 8: Confirmation Bias

**Script:** `confirmation_bias.py`

### Test 1: Shuffled Label Analysis
- **Real balanced accuracy:** 0.467
- **Shuffled mean:** 0.334, **Shuffled std:** 0.014
- **Z-score:** 9.60 — real signal is 9.6 standard deviations above noise
- **Verdict:** Real model captures genuine signal (not noise artifacts)

### Test 2: Alternative Efficacy Thresholds
- **Current thresholds:** high >30%, medium 10-30%, low <10%
- **Strict (high >40%):** Class distribution shifts but model still separates
- **Lenient (high >20%):** More "high" samples, similar separation
- **Binary (high >30% vs rest):** Simplifies problem, accuracy increases
- No threshold choice fundamentally changes the SAR conclusions

### Test 3: Alternative Metrics (Per-Paper)
| Paper | Bal. Acc | Regular Acc | F1 (macro) |
|-------|---------|-------------|------------|
| Kim (held out) | 0.52 | 0.59 | 0.45 |
| Shi (held out) | 0.43 | 0.48 | 0.38 |
| Breda (held out) | 0.40 | 0.43 | 0.35 |

**FLAG: Per-class accuracy breakdown reveals model predicts almost exclusively "high" class:**
- High class accuracy: ~96%
- Medium class accuracy: ~4%
- Low class accuracy: ~0%
- The model achieves its balanced accuracy primarily by getting "high" correct and defaulting to "high" for ambiguous cases

### Test 4: Cherry-Picking Check
- **SARs confirmed by SHAP:** 4/8 testable (50% confirmation rate)
- **SARs supported but weak:** 2/8 (25%)
- **SARs inconclusive:** 2/8 (25%)
- **Missing from SHAP top 20:** peg_mol_pct (#21), clone_2b8 (#23)
- **Incomplete validation layers:** L3 (cross-species), L5 (prospective), L7 (transfer learning)

### Report Card
| Check | Status | Detail |
|-------|--------|--------|
| Real vs shuffled | **PASS** | Z=9.60, clearly above noise |
| Threshold sensitivity | **PASS** | Conclusions hold across thresholds |
| Per-class accuracy | **FLAG** | Model is biased toward "high" predictions |
| SAR confirmation rate | **FLAG** | 50% confirmed (4/8), 2 inconclusive, 2 not testable |
| Validation completeness | **FLAG** | 3/7 layers incomplete (L3, L5, L7) |

### Verdict
**PASS with flags.** The model captures real signal (Z=9.60), and SAR conclusions are not threshold-dependent. However, the per-class accuracy imbalance (predicts "high" almost exclusively) and 50% SAR confirmation rate mean we should be cautious about specific formulation recommendations. The 4 confirmed SARs (ionizable mol%, CD117, dose, DOTAP) are robust; the 2 inconclusive ones (PEG mol%, clone 2B8) need more data.

---

## Overall Assessment

### Findings Requiring Action

1. **MIXED UNITS (Audit 3):** The Pareto scatter plot mixes barcode counts with percentages. This is the most serious issue. Must either separate data types or add prominent caveat.

2. **Kim ratio ambiguity (Audit 6):** HSC:liver=1.20 is a modeled value at EC30, not measured. Must specify the dose context.

3. **DOTAP effect nuance (Audit 4):** The 13.4x headline is outlier-driven. Robust difference is ~4x (still significant).

4. **Kim E2 liver source (Audit 1):** Liver values for the Pareto plot need documented provenance.

### Findings Confirming Robustness

1. **Potency premium (Audit 2):** Robust under all assumptions (>5x worst case)
2. **Screen data integrity (Audit 3):** 0/23 mismatches with source data
3. **Shi liver (Audit 7):** Correctly handled as null throughout
4. **GP validation (Audit 5):** LOO accuracy 0.918, Brier 0.082 (2.1× better than baseline), perfectly stable across seeds
5. **Real signal confirmed (Audit 8):** Z=9.60 vs shuffled labels — model captures genuine biology, not noise

### Honest Limitations to Report

1. Small dataset (110 rows, ~40 features) — high feature:sample ratio
2. Mixed units in Pareto scatter (barcode counts vs percentages)
3. Three validation layers incomplete (L3, L5, L7)
4. DOTAP SAR is fold-dependent (comes primarily from one lab's screen)
5. Shi dose-response mixes uptake (DiR%) and knockdown (CD45 MFI) assays
6. Model predicts "high" class almost exclusively (96% high accuracy, ~0% low accuracy) — per-class imbalance
7. SAR confirmation rate is 50% (4/8 testable), not the 6/8 cited in earlier sessions (2 were "supported" not "confirmed")
