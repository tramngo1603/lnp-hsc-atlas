# Literature Source Manifest

Curation manifest for the LNP-HSC Atlas literature sources reviewed on 2026-09-05.

## Summary

| Outcome | Count |
| --- | --- |
| Sources mined (full or partial text accessible) | 15 |
| Sources stubbed (paywall) | 3 |
| Formulation-experiment records | 198 (196 full + 2 partial pending Xue main text) |
| Records from Tier 1 sources | 174 |
| Records from Tier 2 sources | 6 |
| Records from Tier 3 sources | 10 |

Deliverables: `data/literature_records.json` (198 records + 3 stubs),
`annotations/new_paper_annotations.json` (per-paper metadata and extraction logs).

## Source details

| # | Source | Access route | Records |
| --- | --- | --- | --- |
| T1-2 | Hofstraat 2025, Nat Nanotechnol (PMC12014499) | PMC OA + supplementary source data | 9 |
| T1-6 | Shi 2025, MIT PhD thesis (DSpace 1721.1/165136) | Open PDF | 4 |
| T2-1 | Swart 2023, Pharmaceutics (PMC10304323) | PMC OA (fullTextXML) | 2 |
| T2-3 | Chander 2023, Mol Ther Methods Clin Dev (PMC10410000) | PMC OA + supplement | 3 |
| T2-4 | Dahlman 2014, Nat Nanotechnol (PMC4207430) | PMC full text | 1 |
| T3-1 | Tarab-Ravski 2023, Adv Sci (PMC10375190) | PMC OA | 2 |
| T3-3 | Jyotsana 2019, Ann Hematol (PMC7116733) | PMC full text | 2 |
| T3-5 | Peng 2026, J Hematol Oncol (PMC13041086) | PMC OA + supplement | 2 |
| T3-7 | Zhao 2026, Nat Commun (PMC13315708) | PMC OA | 2 |
| T1-3 | Hanafy 2025, Adv Funct Mater (DOI 10.1002/adfm.202525076) | User-provided PDFs (OCR) | 14 |

### Notes on mined sources

- Hofstraat 2025: compositions from Supplementary Table 1 (image table, transcribed at
  200 dpi), in vivo LAMP1 knockdown computed from Fig. 3 source data spreadsheets
  ((1 - mean normalized siLAMP1 gMFI) x 100, per formulation, LSK and LT-HSC subsets).
  aNP18 physicochemicals from Fig. 4 source data. This source includes 3 low/medium
  efficacy records that improve label balance.
- Shi 2025 thesis: Chapters 3 and 4 are represented. Chapter 2 overlaps with the
  Science Advances paper and is not duplicated.
- Chander 2023, Peng 2026, Zhao 2026, Jyotsana 2019: several efficacy magnitudes exist
  only in figures. Those values are null with null_reason "figure_only" rather than
  estimated, per the no-fabrication rule.
- Chappell 2024: LNP use is ex vivo Cre deletion in lin- HSCs, not in vivo editing (mining
  report mischaracterized the title). Composition analog-supported by breda_2023.
- Palchaudhuri 2025: abstract-only, all records confidence LOW; quantitative claims
  recorded from abstract text with explicit value_basis.
- Xue 2022: composition/protocol mined from SI; efficacy pending main paper.
- Hanafy 2025 (PRELIVE): curated from user-provided PDFs. 14 DoE-selected LNPs
  with full Fig 2A compositions and physicochemicals. BM efficacy recorded at two levels:
  Fig S19 good/poor class (good = LNP 6, 10, 11, 14) and Fig 2B mean radiance estimates
  (estimated_from_figure, flagged for user confirmation). Text vs Fig S19 discrepancy on
  BM top performers resolved: user confirmed Fig S19 (good = 6, 10, 11, 14; 8 poor),
  Fig 2A row 9 EE (43.3%), and Fig 2B BM readings for LNP 6, 8, 11 (2026-09-05).
  ICL identities are AstraZeneca proprietary, so all ionizable SMILES are null.
- Dahlman 2014 is endothelial (lung), not bone marrow. Retained as the 7C1 ancestor of
  the Sago 2018 HSC line, flagged low BM relevance.

## Stubbed sources, status: pending_paywall

| # | Source | Why skipped | Unblock path |
| --- | --- | --- | --- |
| T3-2 | Ramishetti et al., Adv Mater (PMID 31999380) | Wiley paywall | Institutional access |
| T3-6 | Zhu et al., J Control Release (PMID 41905408) | Elsevier paywall, very recent | Institutional access |
| T3-8 | Dacoba et al., ACS Nano (PMID 40080677) | ACS paywall | Institutional access or author manuscript |

All 3 remaining stubs were verified to exist (PubMed/Crossref checks) and carry full citation
metadata in `data/literature_records.json`. Remaining stubs: T3-2 (Ramishetti), T3-6 (Zhu), T3-8 (Dacoba), all Tier 3. Iida mined from user-provided file (note: in vitro only, no in vivo data). T1 is now fully mined (Xu unblocked by user-provided main text; Supp Tables 1-15 still pending). Xue awaits its main text.

## Verification and integrity notes

- Every numeric value in the curated records traces to a named table, figure, source-data
  spreadsheet, or text passage (see per-record `provenance` and per-paper
  `extraction_log`). No value was invented. Figure-only magnitudes are null with
  explicit `null_reason`, not estimated.
- Evidence-strength hierarchy applied: extracted_from_table (Hofstraat, Swart) >
  extracted_from_text (all others). No estimated_from_figure values were admitted.
- One record (shi_2025_thesis formulation D, 2.3x normalized MFI) uses a text-stated
  ratio and is marked confidence MEDIUM.
- Existence check results: all 18 sources verified via Europe PMC / PubMed / Crossref.
  No phantom citations in the mining report. Note: Xu et al. is indexed as 2026
  (online 2025); Hanafy et al. is 2025 (Crossref 2025-11-26).
- External databases (LNPDB, AGILE, LANCE, LiON) deliberately not imported, per scope.

## Open review items

1. Xu et al.: fully mined, 148 records. Full 92-lipid primary screen and 50-formulation
   secondary screen imported per user decision (2026-09-05). Screen records carry
   bar-vs-replicate-mean caveat and per-record labels (110 low, 24 medium).
   Xue main text remains pending.
   Ramishetti, Zhu, and Dacoba remain paywalled.
2. Figure-only magnitudes in Chander Fig. 8, Peng Fig. 1H, and Zhao Fig. 4g-h remain
   null under the source-value policy.
3. Shi thesis strain ambiguity for the base editing experiment (null, unclear_in_source).
4. Chander Table S1 (image-only) size/PDI transcription remains deferred.
5. Palchaudhuri abstract values: replace with figure/table-provenanced values when the
   full paper is published.
