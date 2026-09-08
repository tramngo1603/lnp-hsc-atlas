# HANDOFF: LNP-HSC Atlas expansion, state after Pass 1

Date: 2026-09-05. This repo copy contains the original 135-record atlas (untouched)
plus the Pass 1 expansion output. Git history: baseline import commit + 6 Pass 1
commits, all atomic.

## Current state

- 135 original records (untouched, per project rules)
- 198 new records in `data/new_records_pass1.json` (196 full + 2 partial pending
  Xue 2022 main text)
- 15 of 18 planned sources mined; 3 stubs remain (`pending_paywall`: Ramishetti
  2020 Adv Mater, Zhu 2026 J Control Release, Dacoba 2025 ACS Nano)
- Per-paper metadata and extraction logs: `annotations/new_paper_annotations.json`
- What was mined/skipped/why, and all caveats: `MINING_MANIFEST.md`

## Record schema (new records)

Flat JSON per formulation-experiment: record_id, source_paper, tier, status,
formulation_id, experiment_id, assay_category, payload, composition,
physicochemical, manufacturing, targeting, delivery, efficacy, toxicity,
evidence_strength, extraction_method (extracted_from_table / extracted_from_text /
estimated_from_figure), provenance (per-field citations), null_fields (every null
has an explicit reason), confidence, notes. Screen records also carry label_for_ml
(high >30%, medium 10-30%, low <10% on the assay's primary metric).

## Hard rules for the next passes

1. Never modify the original 135 records except documented enrichment in Pass 2
   (`data/enrichment_pass2.json`).
2. No fabricated values. Figure-only magnitudes stay null with null_reason unless
   the user approves estimated_from_figure extraction.
3. No em dashes in any written file.
4. Facts from paywalled papers are fine (facts are not copyrightable); never copy
   figures/tables/verbatim text into the repo, and never commit source PDFs.
5. Atomic, well-messaged commits per pass. Pass 3 ends with tag v2.0-atlas-expansion.

## Known flags to resolve in Pass 2 (validation_flags_pass2.json candidates)

- Xu screen records: plotted bar vs replicate-mean mismatches in the Fig 4a source
  file (documented per record); LNP-123 has an impossible 116% replicate.
- Xu text vs figure: text 48.5% vs source-data bar 46% for LNP-168 second dose
  (text kept as primary, delta documented).
- Hanafy: efficacy values are estimated_from_figure (Fig 2B BM panel, user-confirmed
  readings for LNP 6/8/10/11/14; Fig S19 classification user-confirmed; Fig 2A row 9
  EE 43.3% user-confirmed). Main text vs Fig S19 discrepancy resolved in favor of S19.
- Palchaudhuri: abstract-only, all records confidence LOW; cross-check against
  existing tessera_* annotations to avoid duplication.
- Chappell: composition analog-supported via breda_2023 (same lab platform);
  ex vivo assay, not in vivo.
- Shi thesis: strain for the base editing experiment not stated (null,
  unclear_in_source); Table 4-3 physicochemicals measured on mCherry formulation
  applied to the ABE record by composition identity.
- Iida: in vitro only, no in vivo data exists in the paper.
- Swart/Zhao doses reported per mouse (50 ug, 10 ug), not mg/kg.
- Figure-only efficacy left null: Chander (Fig 8), Peng (Fig 1H), Zhao (Fig 4g-h),
  Iida, Xu library B/C leads.

## Open decisions for the user

1. Buy or skip: Ramishetti 2020, Zhu 2026, Dacoba 2025 (Zhu is the best value).
2. Xue 2022 main text: completes the 2 partial records (efficacy + ALT/AST values).
3. Figure-only magnitudes: leave null or extract with estimated_from_figure.
4. Iida supplement arrived empty; re-send if siRNA sequences are wanted.

## Pass 2 checklist (from the original protocol)

- Run existing audit/test suite against NEW records only.
- Cross-reference 5-10 critical records against source text (suggested: Xu TDT 42.6%,
  Hofstraat aNP18 knockdown, Shi 12.5% ABE, Swart Table 1 pair, Hanafy Fig 2A row).
- Unit harmonization (nm, mg/kg, 0-100%), assay separation, evidence corrections.
- Write data/validation_flags_pass2.json for non-auto-fixable records.
- Enrichment of existing 135 where new papers supply missing data (documented in
  data/enrichment_pass2.json); candidate: PRELIVE-style physicochemicals exist for
  Xu leads now; PPZ-A10 SMILES via CAS 2941268-67-1 noted in original gaps.
- Regenerate consolidated feature matrix (old + new). Target: audit passes with
  <= 3 minor warnings.

## Pass 3 checklist

- Load 135 + 198, dedupe (check Palchaudhuri vs tessera_*, Chappell vs breda_2023
  platform records), logical contradiction scan.
- Coverage report across the 47 columns, docs/COVERAGE_REPORT.md.
- Full test suite on combined data; no regressions on original 135.
- Rerun analysis scripts (Pareto, correlation) on combined data.
- README update; final commit; tag v2.0-atlas-expansion.

## Notes on sources used

- Hofstraat, Swart, Chander, Tarab-Ravski, Peng, Zhao, Jyotsana, Dahlman: mined from
  open-access PMC full texts and supplementary source data.
- Xu (main text + Supp Tables 1-15 + figure source data), Hanafy (scanned main text,
  OCR'd at 300 dpi, + SI), Chappell (PMC author manuscript + SI), Palchaudhuri
  (ASH abstract), Xue (SI only), Iida (main text): user-provided files.
- Shi thesis: MIT DSpace (https://dspace.mit.edu/handle/1721.1/165136), Chapters 3-4
  only (Chapter 2 overlaps existing shi_2023).
- anchors.py is referenced in the original protocol but does not exist in the repo;
  sgRNA-25 (AGGCAAGGCTGGCCAACCCA) was verified against GRCh38 via Ensembl directly
  (HBG2 chr11:5,249,976-5,249,995 and HBG1 chr11:5,254,900-5,254,919, 4,924 bp apart).
