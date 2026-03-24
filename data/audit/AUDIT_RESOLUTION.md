# Audit Resolution Status

**Original audit:** 2026-03-08 (see `AUDIT_REPORT.md`)
**Resolution date:** 2026-03-23
**Resolved in:** Paper v5, explorer v1, feature matrix v5 (135 rows)

---

## Resolution by Audit Item

| Audit | Finding | Resolution | Status |
|-------|---------|------------|--------|
| 1 | Trace numbers: 4 rounding FAILs | Cosmetic — no action needed per audit | ACCEPTED |
| 2 | Dose-response sensitivity | Potency premium robust under all assumptions | PASS (no fix needed) |
| 3 | Pareto mixed units | Metric types separated by color + marker fill | FIXED |
| 4 | Headgroup DOTAP 13x outlier-driven | Robust ratio ~4x (p=0.004) used in paper; raw 13x shown in explorer | FIXED |
| 5 | GP validation | LOO accuracy 0.918, stable | PASS (no fix needed) |
| 6 | Kim ratio ambiguity | Table 1 footnote distinguishes measured (1.04) vs modeled (1.20) | FIXED |
| 7 | Shi liver null | Confirmed null everywhere; Table 1 shows "~35*" with footnote | PASS (no fix needed) |
| 8 | Confirmation bias | Documented as limitation in paper Discussion | ACCEPTED |

---

## Audit 3: Pareto Mixed Units — FIXED

**Problem:** Barcode counts and editing percentages plotted on the same axes.

**Fix:**
- Added `metric_type` column to feature matrix (`editing_pct`, `reporter_pct`, `barcode_normalized`)
- Pareto plot uses filled markers for editing data, open markers for reporter data
- Pareto frontier drawn through editing-metric points only (solid line)
- Reporter frontier shown separately (dashed line)
- Barcode data excluded from Pareto scatter entirely
- Caption states metric separation explicitly

**Where:** `data/explore/pareto_plot_v2.py`, `src/lnp_optimizer/integrate_lian.py`, explorer JSX Pareto tab

## Audit 4: DOTAP Effect Nuance — FIXED

**Problem:** DOTAP vs DDAB fold-change of 13x was driven by 2 outliers (LNP67 BM=13, LNP95 BM=48).

**Fix:**
- Paper reports "~4x (p=0.004)" using robust statistics (median or trimmed mean)
- Raw 13x fold-change and full distribution shown in explorer Headgroup tab
- `data/models/headgroup_tropism.json` updated with both robust and raw statistics

**Where:** `data/models/headgroup_tropism.json`, paper Section 3.4, explorer Headgroup tab

**Additional correction:** The audit report references "LNP85" as having BM=48. This is incorrect — LNP85 has BM=6 (DOTAP + DMG-PEG). The formulation with BM=48 is **LNP95** (DOTAP 30% + ALC-0159, IL 50%). Verified against `data/kim_screen/kim_2024_screen_corrected.json`. All downstream references (explorer, Pareto plot, paper) corrected to LNP95.

## Audit 6: Kim Ratio Ambiguity — FIXED

**Problem:** HSC:liver ratio reported as 1.20 without clarifying it's modeled at EC30, not measured.

**Fix:**
- Paper Table 1 footnote: "‡Kim ratio = 1.04 at 0.5 mg/kg (measured); 1.20 at EC30 (modeled)"
- Explorer Pareto tooltip shows measured values (20.9% BM, 20.1% liver)
- `data/models/therapeutic_window.json` retains both values with context

**Where:** Paper Table 1 footnote, explorer Pareto tooltip

## Audit 8: Confirmation Bias — ACCEPTED AS LIMITATION

**Problem:** Model predicts "high" class with 96% accuracy but ~0% for "low" class. Shuffled-label baseline (0.418) exceeds chance (0.333), indicating high feature:row ratio enables spurious patterns.

**Accepted because:**
- Documented in paper Discussion Section 4 (Limitations)
- SHAP-recovered SARs match known biology from independent wet-lab studies
- Adding Lian 2024 (25 rows) did not degrade model — SARs remained stable
- The model is used for hypothesis generation (gap scoring), not clinical decisions

**Where:** Paper Discussion, `data/audit/confirmation_bias.py`

---

## Open Items from Audit 1

- [ ] Document source of Kim E2 liver values (20.1%, 14.7%, 1.6%, 42.4%) — believed to be from Supp Fig 7 bar charts
- [ ] Clarify which Shi experiment (E2 uptake vs E3 knockdown) contributes each dose-response data point
