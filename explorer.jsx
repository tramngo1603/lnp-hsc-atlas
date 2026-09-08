import { useState, useMemo } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, ReferenceLine, ReferenceArea, Label, LineChart, Line } from "recharts";

const INK = "#2B4162";
const RUST = "#A63D40";
const OCHRE = "#B08836";
const platformColor = (p) => p === "VLP" ? OCHRE : p === "tLNP" ? RUST : INK;

// DATA:paretoData
const paretoData = [
  {
    "name": "Breda CD117",
    "bm": 55,
    "liver": 76,
    "metric": "editing",
    "platform": "tLNP",
    "species": "Mouse",
    "detail": "Cre editing in LSK, CD117 antibody, 0.25 mg/kg",
    "n": 3
  },
  {
    "name": "Kim LNP67",
    "bm": 20.9,
    "liver": 20.1,
    "metric": "reporter",
    "platform": "LNP",
    "species": "Mouse",
    "detail": "aVHH protein expression, 0.5 mg/kg",
    "n": 3
  },
  {
    "name": "Kim LNP108",
    "bm": 8.8,
    "liver": 1.6,
    "metric": "reporter",
    "platform": "LNP",
    "species": "Mouse",
    "detail": "Best selectivity in Kim screen (BM:liver = 5.5)",
    "n": 3
  },
  {
    "name": "Lian AA11 Cas9",
    "bm": 5.2,
    "liver": 7.5,
    "metric": "editing",
    "platform": "LNP",
    "species": "Mouse",
    "detail": "BCL11A editing, covalent lipid approach, Townes mice",
    "n": 3
  },
  {
    "name": "Lian AA11 ABE",
    "bm": 2.4,
    "liver": 3.0,
    "metric": "editing",
    "platform": "LNP",
    "species": "Mouse",
    "detail": "Sickle to Makassar base editing, Townes mice",
    "n": 3
  },
  {
    "name": "Ensoma VLP",
    "bm": 31,
    "liver": 0.5,
    "metric": "editing",
    "platform": "VLP",
    "species": "Hum. mouse",
    "detail": "B2M editing, 8 wk, near-zero liver transduction",
    "n": 3
  },
  {
    "name": "Tessera 24%",
    "bm": 24,
    "liver": 8,
    "metric": "editing",
    "platform": "tLNP",
    "species": "NHP",
    "detail": "HBB Makassar, single dose, liver estimated",
    "n": null
  },
  {
    "name": "Tessera 40%",
    "bm": 40,
    "liver": 13.3,
    "metric": "editing",
    "platform": "tLNP",
    "species": "NHP",
    "detail": "Optimized Gene Writer cargo, same LNP platform",
    "n": null
  },
  {
    "name": "Tessera 60%",
    "bm": 60,
    "liver": 20,
    "metric": "editing",
    "platform": "tLNP",
    "species": "NHP",
    "detail": "Two doses, liver estimated from 3:1 BM:liver ratio",
    "n": null
  },
  {
    "name": "Kim LNP95",
    "bm": 48,
    "liver": 18.8,
    "metric": "reporter",
    "platform": "LNP",
    "species": "Mouse",
    "detail": "ALC-0159 PEG lipid, highest barcode in screen (30% DOTAP)",
    "n": 1
  },
  {
    "name": "Breda IgG control",
    "bm": 19,
    "liver": 78,
    "metric": "editing",
    "platform": "tLNP",
    "species": "Mouse",
    "detail": "Isotype control, liver comparable to CD117 LNP",
    "n": 3
  },
  {
    "name": "Kim E2 avg",
    "bm": 5.2,
    "liver": 44,
    "metric": "reporter",
    "platform": "LNP",
    "species": "Mouse",
    "detail": "4-LNP validation average, 0.5 mg/kg",
    "n": 4
  }
];
// END:paretoData

// DATA:shapData
const shapData = [
  {
    "feature": "Dose (mg/kg)",
    "shap": 0.6,
    "type": "known"
  },
  {
    "feature": "IL molecular weight",
    "shap": 0.38,
    "type": "literature"
  },
  {
    "feature": "Helper lipid %",
    "shap": 0.28,
    "type": "known"
  },
  {
    "feature": "Cholesterol %",
    "shap": 0.21,
    "type": "literature"
  },
  {
    "feature": "Ionizable lipid %",
    "shap": 0.18,
    "type": "known"
  },
  {
    "feature": "Editing assay",
    "shap": 0.17,
    "type": "other"
  },
  {
    "feature": "il_to_helper_ratio",
    "shap": 0.17,
    "type": "other"
  },
  {
    "feature": "Cationic helper",
    "shap": 0.14,
    "type": "other"
  },
  {
    "feature": "CD117 targeting",
    "shap": 0.13,
    "type": "known"
  },
  {
    "feature": "peg_chain_numeric",
    "shap": 0.12,
    "type": "other"
  }
];
// END:shapData

// DATA:timelineData
const timelineData = [
  { year: "2018", label: "Sago BM1", detail: "First BM-targeting LNP, endothelial cells not HSCs", platform: "LNP" },
  { year: "2020", label: "SORT", detail: "Charge-dependent organ targeting framework established", platform: "LNP" },
  { year: "2023", label: "Breda", detail: "55% Cre editing in mouse LSK cells via CD117 tLNP", platform: "tLNP" },
  { year: "2023", label: "Shi / Anderson", detail: "~90% HSPC uptake, ionizable-lipid-agnostic CD117 system", platform: "tLNP" },
  { year: "2024", label: "Kim LNP67", detail: "First untargeted BM-homing LNP with NHP delivery", platform: "LNP" },
  { year: "2024", label: "Lian", detail: "Covalent lipid approach, 14 BM cell types, base editing in SCD mice", platform: "LNP" },
  { year: "2024", label: "Tessera", detail: "24% HBB in NHP, 52x BM enhancement, 11x liver reduction", platform: "tLNP" },
  { year: "2025", label: "Editas", detail: "58% NHP HSC editing, field highest reported", platform: "tLNP" },
  { year: "2025", label: "Ensoma", detail: "31% HSC editing with near-zero liver, first in ideal zone", platform: "VLP" },
  { year: "2025", label: "Tessera", detail: "40% HBB (1-dose) / 60% (2-dose) NHP, 15-month durability", platform: "tLNP" },
  { year: "2025", label: "Kim ASH", detail: "37% human HSPC delivery in humanized mice at 2 mg/kg", platform: "LNP" },
];
// END:timelineData

// DATA:bmGapData
const bmGapData = [
  {
    "study": "Radmand 2024",
    "lnps": 196,
    "measured": false
  },
  {
    "study": "Radmand 2023",
    "lnps": 137,
    "measured": false
  },
  {
    "study": "Kim 2024",
    "lnps": 128,
    "measured": true
  },
  {
    "study": "Gentry 2025",
    "lnps": 109,
    "measured": false
  },
  {
    "study": "Sago 2018",
    "lnps": 160,
    "measured": true
  },
  {
    "study": "Da Silva Sanchez 2022",
    "lnps": 98,
    "measured": false
  },
  {
    "study": "Shi 2023",
    "lnps": 37,
    "measured": true
  },
  {
    "study": "Lian 2024",
    "lnps": 21,
    "measured": true
  },
  {
    "study": "SORT 2020",
    "lnps": 20,
    "measured": false
  },
  {
    "study": "Breda 2023",
    "lnps": 14,
    "measured": true
  },
  {
    "study": "Cullis 2025",
    "lnps": 10,
    "measured": true
  }
];
// END:bmGapData

// DATA:findings
const findings = [
  {
    "title": "Atlas scope",
    "text": "The atlas contains 333 evidence rows from 19 matrix sources. The largest sources are Xu 2026 (148), Kim 2024 (80), and Lian 2024 (25)."
  },
  {
    "title": "Label distribution",
    "text": "Low efficacy accounts for 184/315 labeled rows (58.4%). The large Xu screen contributes many repeated-assay observations, so formulation-grouped validation is primary."
  },
  {
    "title": "Coverage is uneven",
    "text": "30 of 48 matrix columns are complete. Ionizable-lipid descriptors cover 154/333 rows, while detailed toxicity evidence covers 13/198 rich records. Missing values are not inferred."
  },
  {
    "title": "Formulation leakage matters",
    "text": "Row-random LightGBM balanced accuracy is 0.5975, versus 0.5375 when each formulation token is confined to one fold. The grouped result is primary."
  },
  {
    "title": "The 30% boundary is explicit",
    "text": "The current rule uses high >30% strictly. Four Lian 2024 rows at exactly 30% retain their established high labels and carry the boundary marker. They are boundary cases, not errors."
  },
  {
    "title": "Pareto scope",
    "text": "The corrected Pareto analysis includes only standardized same-record absolute bone-marrow and liver percentage pairs. Relative and qualitative values are not converted into the Pareto axes."
  }
];
// END:findings

// DATA:papers
const papers = [
  {
    "id": "Breda 2023",
    "paperId": "breda_2023",
    "journal": "Science",
    "title": "In vivo hematopoietic stem cell modification by mRNA delivery",
    "role": "Atlas source",
    "records": 9,
    "status": "curated",
    "paperType": "research",
    "url": "https://doi.org/10.1126/science.ade6967"
  },
  {
    "id": "Kim 2024",
    "paperId": "kim_2024",
    "journal": "Nature Biotechnology",
    "title": "Lipid nanoparticle-mediated mRNA delivery to CD34+ cells in rhesus monkeys",
    "role": "Atlas source",
    "records": 80,
    "status": "curated",
    "paperType": "research_article",
    "url": "https://doi.org/10.1038/s41587-024-02470-2"
  },
  {
    "id": "Shi 2023",
    "paperId": "shi_2023",
    "journal": "Nano Letters",
    "title": "In Vivo RNA Delivery to Hematopoietic Stem and Progenitor Cells via Targeted Lipid Nanoparticles",
    "role": "Atlas source",
    "records": 21,
    "status": "curated",
    "paperType": "research_article",
    "url": "https://doi.org/10.1021/acs.nanolett.3c00304"
  },
  {
    "id": "Lian 2024",
    "paperId": "lian_2024",
    "journal": "Nature Nanotechnology",
    "title": "Bone-marrow-homing lipid nanoparticles for genome editing in diseased and malignant haematopoietic stem cells",
    "role": "Atlas source",
    "records": 25,
    "status": "curated",
    "paperType": "peer_reviewed",
    "url": "https://www.nature.com/articles/s41565-024-01680-8"
  },
  {
    "id": "Hofstraat 2025",
    "paperId": "hofstraat_2025",
    "journal": "Nature Nanotechnology",
    "title": "Nature-inspired platform nanotechnology for RNA delivery to myeloid cells and their bone marrow progenitors",
    "role": "Atlas source",
    "records": 9,
    "status": "extracted",
    "paperType": "research",
    "url": "https://doi.org/10.1038/s41565-024-01847-3"
  },
  {
    "id": "Shi thesis 2025",
    "paperId": "shi_2025_thesis",
    "journal": "MIT (PhD thesis, Anderson lab)",
    "title": "Development of a targeted lipid nanoparticle platform for in vivo RNA delivery to hematopoietic stem and progenitor cells",
    "role": "Atlas source",
    "records": 4,
    "status": "extracted",
    "paperType": "phd_thesis",
    "url": "https://dspace.mit.edu/handle/1721.1/165136"
  },
  {
    "id": "Swart 2023",
    "paperId": "swart_2023",
    "journal": "Pharmaceutics",
    "title": "Increased Bone Marrow Uptake and Accumulation of Very-Late Antigen-4 Targeted Lipid Nanoparticles",
    "role": "Atlas source",
    "records": 2,
    "status": "extracted",
    "paperType": "research",
    "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10304323/"
  },
  {
    "id": "Chander 2023",
    "paperId": "chander_2023",
    "journal": "Molecular Therapy Methods & Clinical Development",
    "title": "Lipid nanoparticle mRNA systems containing high levels of sphingomyelin engender higher protein expression in hepatic and extra-hepatic tissues",
    "role": "Atlas source",
    "records": 3,
    "status": "extracted",
    "paperType": "research",
    "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10410000/"
  },
  {
    "id": "Tarab-Ravski 2023",
    "paperId": "tarab_ravski_2023",
    "journal": "Advanced Science",
    "title": "Delivery of Therapeutic RNA to the Bone Marrow in Multiple Myeloma Using CD38-Targeted Lipid Nanoparticles",
    "role": "Atlas source",
    "records": 2,
    "status": "extracted",
    "paperType": "research",
    "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC10375190/"
  },
  {
    "id": "Peng 2026",
    "paperId": "peng_2026",
    "journal": "Journal of Hematology & Oncology",
    "title": "CXCR4-antagonistic peptide-decorated lipid nanoparticles for co-delivery of AML1-ETO siRNA to enhance chemotherapy",
    "role": "Atlas source",
    "records": 2,
    "status": "extracted",
    "paperType": "correspondence",
    "url": "https://doi.org/10.1186/s13045-026-01785-8"
  },
  {
    "id": "Zhao 2026",
    "paperId": "zhao_2026",
    "journal": "Nature Communications",
    "title": "CAR-CD34+ hematopoietic stem/progenitor cells produced in vivo protect against aortic aneurysm",
    "role": "Atlas source",
    "records": 2,
    "status": "extracted",
    "paperType": "research",
    "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC13315708/"
  },
  {
    "id": "Jyotsana 2019",
    "paperId": "jyotsana_2019",
    "journal": "Annals of Hematology",
    "title": "Lipid nanoparticle-mediated siRNA delivery for safe targeting of human CML in vivo",
    "role": "Atlas source",
    "records": 2,
    "status": "extracted",
    "paperType": "research",
    "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC7116733/"
  },
  {
    "id": "Dahlman 2014",
    "paperId": "dahlman_2014",
    "journal": "Nature Nanotechnology",
    "title": "In vivo endothelial siRNA delivery using polymeric nanoparticles with low molecular weight",
    "role": "Atlas source",
    "records": 1,
    "status": "extracted",
    "paperType": "research",
    "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC4207430/"
  },
  {
    "id": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "journal": "Advanced Functional Materials",
    "title": "PRELIVE: A Framework for Predicting Lipid Nanoparticles In Vivo Efficacy and Reducing Reliance on Animal Testing",
    "role": "Atlas source",
    "records": 14,
    "status": "extracted",
    "paperType": "research",
    "url": "https://doi.org/10.1002/adfm.202525076"
  },
  {
    "id": "Chappell 2024",
    "paperId": "chappell_2024",
    "journal": "Blood",
    "title": "Use of HSC-targeted LNP to generate a mouse model of lethal alpha-thalassemia and treatment via lentiviral gene therapy",
    "role": "Atlas source",
    "records": 2,
    "status": "extracted",
    "paperType": "research",
    "url": "https://doi.org/10.1182/blood.2023023349"
  },
  {
    "id": "Palchaudhuri 2025",
    "paperId": "palchaudhuri_2025",
    "journal": "Blood 146 (Supplement 1): 4318",
    "title": "In Vivo RNA delivery by targeted lipid nanoparticles enable gene editing in hematopoietic stem cells and T cells",
    "role": "Atlas source",
    "records": 3,
    "status": "extracted_abstract_only",
    "paperType": "conference_abstract",
    "url": "https://doi.org/10.1182/blood-2025-4318"
  },
  {
    "id": "Xue 2022",
    "paperId": "xue_2022",
    "journal": "Journal of the American Chemical Society",
    "title": "Rational Design of Bisphosphonate Lipid-like Materials for mRNA Delivery to the Bone Microenvironment",
    "role": "Atlas source",
    "records": 2,
    "status": "partial_pending_main_text",
    "paperType": "research",
    "url": "https://doi.org/10.1021/jacs.2c02706"
  },
  {
    "id": "Xu 2026",
    "paperId": "xu_2026",
    "journal": "Nature Biomedical Engineering",
    "title": "In vivo genome editing of human haematopoietic stem cells for treatment of blood disorders using mRNA delivery",
    "role": "Atlas source",
    "records": 148,
    "status": "extracted",
    "paperType": "research",
    "url": "https://doi.org/10.1038/s41551-025-01480-y"
  },
  {
    "id": "Iida 2022",
    "paperId": "iida_2022",
    "journal": "Experimental Hematology",
    "title": "RUNX1 Inhibition Using Lipid Nanoparticle-Mediated Silencing RNA Delivery as an Effective Treatment for Acute Leukemias",
    "role": "Atlas source",
    "records": 2,
    "status": "extracted",
    "paperType": "brief_communication",
    "url": "https://doi.org/10.1016/j.exphem.2022.05.001"
  }
];
// END:papers

// DATA:stats
const stats = {
  "rows": 333,
  "sources": 19,
  "columns": 48,
  "labeled": 315,
  "modelFeatures": 37,
  "descriptorRows": 154
};
// END:stats

// DATA:coverageStats
const coverageStats = {
  "completeColumns": 30,
  "totalColumns": 48,
  "reportPath": "docs/COVERAGE_REPORT.md",
  "blocks": [
    {
      "label": "Efficacy label",
      "filled": 315,
      "total": 333,
      "percent": 94.6,
      "note": "18 unlabeled"
    },
    {
      "label": "Core composition",
      "filled": 250,
      "total": 333,
      "percent": 75.1,
      "note": "IL, helper, cholesterol"
    },
    {
      "label": "Dose",
      "filled": 246,
      "total": 333,
      "percent": 73.9,
      "note": "mg/kg only"
    },
    {
      "label": "IL descriptors",
      "filled": 154,
      "total": 333,
      "percent": 46.2,
      "note": "8 descriptor columns"
    },
    {
      "label": "Detailed toxicity",
      "filled": 13,
      "total": 198,
      "percent": 6.6,
      "note": "normalized rich records"
    }
  ]
};
// END:coverageStats

// DATA:labelDistribution
const labelDistribution = {
  "rows": 333,
  "labeled": 315,
  "low": 184,
  "medium": 73,
  "high": 58,
  "unlabeled": 18,
  "lowShare": 58.4
};
// END:labelDistribution

// DATA:sourceSummary
const sourceSummary = {
  "sources": [
    {
      "id": "xu_2026",
      "label": "Xu 2026",
      "rows": 148
    },
    {
      "id": "kim_2024",
      "label": "Kim 2024",
      "rows": 80
    },
    {
      "id": "lian_2024",
      "label": "Lian 2024",
      "rows": 25
    },
    {
      "id": "shi_2023",
      "label": "Shi 2023",
      "rows": 21
    },
    {
      "id": "hanafy_2025",
      "label": "Hanafy 2025",
      "rows": 14
    },
    {
      "id": "breda_2023",
      "label": "Breda 2023",
      "rows": 9
    },
    {
      "id": "hofstraat_2025",
      "label": "Hofstraat 2025",
      "rows": 9
    },
    {
      "id": "shi_2025_thesis",
      "label": "Shi thesis 2025",
      "rows": 4
    },
    {
      "id": "chander_2023",
      "label": "Chander 2023",
      "rows": 3
    },
    {
      "id": "palchaudhuri_2025",
      "label": "Palchaudhuri 2025",
      "rows": 3
    },
    {
      "id": "xue_2022",
      "label": "Xue 2022",
      "rows": 2
    },
    {
      "id": "chappell_2024",
      "label": "Chappell 2024",
      "rows": 2
    },
    {
      "id": "peng_2026",
      "label": "Peng 2026",
      "rows": 2
    },
    {
      "id": "jyotsana_2019",
      "label": "Jyotsana 2019",
      "rows": 2
    },
    {
      "id": "zhao_2026",
      "label": "Zhao 2026",
      "rows": 2
    },
    {
      "id": "tarab_ravski_2023",
      "label": "Tarab-Ravski 2023",
      "rows": 2
    },
    {
      "id": "swart_2023",
      "label": "Swart 2023",
      "rows": 2
    },
    {
      "id": "iida_2022",
      "label": "Iida 2022",
      "rows": 2
    },
    {
      "id": "dahlman_2014",
      "label": "Dahlman 2014",
      "rows": 1
    }
  ],
  "recordTypes": {
    "abstract-only": 3,
    "detailed": 186,
    "partial": 2,
    "screen": 142
  }
};
// END:sourceSummary

// DATA:validationSummary
const validationSummary = {
  "evaluatedRows": 311,
  "formulationTokens": 265,
  "rowRandom": {
    "balancedAccuracy": 0.5975,
    "balancedAccuracyStd": 0.0392,
    "macroF1": 0.5963,
    "formulationDisjoint": false,
    "overlapRange": [
      7,
      12
    ]
  },
  "formulationGrouped": {
    "balancedAccuracy": 0.5375,
    "balancedAccuracyStd": 0.063,
    "macroF1": 0.4813,
    "formulationDisjoint": true,
    "overlapRange": [
      0,
      0
    ]
  },
  "leaveOnePaperOut": {
    "balancedAccuracy": 0.2568,
    "folds": 12
  }
};
// END:validationSummary

// DATA:formulations
const formulations = [
  {
    "p": "Breda 2023",
    "paperId": "breda_2023",
    "id": "CD117/LNP",
    "experiment": "3_in_vitro_Cre_LSK",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Breda 2023",
    "paperId": "breda_2023",
    "id": "CD117/LNP",
    "experiment": "4_ex_vivo_Cre_transplant",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Breda 2023",
    "paperId": "breda_2023",
    "id": "CD117/LNP",
    "experiment": "6_in_vivo_Cre_5ug",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.25,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Breda 2023",
    "paperId": "breda_2023",
    "id": "CD117/LNP",
    "experiment": "7_in_vivo_Cre_1ug",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.05,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Breda 2023",
    "paperId": "breda_2023",
    "id": "hCD117/LNP (anti-human CD117)",
    "experiment": "8_ex_vivo_SCD_base_editing",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Breda 2023",
    "paperId": "breda_2023",
    "id": "IgG/LNP",
    "experiment": "4_ex_vivo_Cre_transplant_IgG_0.1ug",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "Active",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Breda 2023",
    "paperId": "breda_2023",
    "id": "IgG/LNP",
    "experiment": "4_ex_vivo_Cre_transplant_IgG_1ug",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "Active",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Breda 2023",
    "paperId": "breda_2023",
    "id": "IgG/LNP",
    "experiment": "6_in_vivo_Cre_5ug_IgG_control",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.25,
    "tgt": "Active",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Breda 2023",
    "paperId": "breda_2023",
    "id": "CD117/LNP",
    "experiment": "10_in_vivo_PUMA_conditioning_LSK_decrease",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.05,
    "tgt": "CD117",
    "mt": "depletion",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F1_LNP67",
    "experiment": "E2_individual_validation_F1_LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "hlPct": 15.0,
    "chol": 47.5,
    "peg": 2.5,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F2_LNP95",
    "experiment": "E2_individual_validation_F2_LNP95",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F3_LNP108",
    "experiment": "E2_individual_validation_F3_LNP108",
    "il": null,
    "hl": "DSPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F4_LP01",
    "experiment": "E2_individual_validation_F4_LP01",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F1_LNP67",
    "experiment": "E3_dose_response_mouse_0.5_mg_kg",
    "il": 35.0,
    "hl": "DOTAP",
    "hlPct": 15.0,
    "chol": 47.5,
    "peg": 2.5,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F1_LNP67",
    "experiment": "E3_dose_response_mouse_1.0_mg_kg",
    "il": 35.0,
    "hl": "DOTAP",
    "hlPct": 15.0,
    "chol": 47.5,
    "peg": 2.5,
    "dose": 1.0,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F1_LNP67",
    "experiment": "E3_dose_response_mouse_2.0_mg_kg",
    "il": 35.0,
    "hl": "DOTAP",
    "hlPct": 15.0,
    "chol": 47.5,
    "peg": 2.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F1_LNP67",
    "experiment": "E6_human_ex_vivo_0.25_ug_ml",
    "il": 35.0,
    "hl": "DOTAP",
    "hlPct": 15.0,
    "chol": 47.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F1_LNP67",
    "experiment": "E6_human_ex_vivo_0.5_ug_ml",
    "il": 35.0,
    "hl": "DOTAP",
    "hlPct": 15.0,
    "chol": 47.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F1_LNP67",
    "experiment": "E6_human_ex_vivo_1.0_ug_ml",
    "il": 35.0,
    "hl": "DOTAP",
    "hlPct": 15.0,
    "chol": 47.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F1_LNP67",
    "experiment": "E6_human_ex_vivo_2.0_ug_ml",
    "il": 35.0,
    "hl": "DOTAP",
    "hlPct": 15.0,
    "chol": 47.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F1_LNP67",
    "experiment": "E6_human_ex_vivo_4.0_ug_ml",
    "il": 35.0,
    "hl": "DOTAP",
    "hlPct": 15.0,
    "chol": 47.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F1_LNP67",
    "experiment": "E8_freeze_thaw_fresh",
    "il": 35.0,
    "hl": "DOTAP",
    "hlPct": 15.0,
    "chol": 47.5,
    "peg": 2.5,
    "dose": 1.0,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "F1_LNP67",
    "experiment": "E8_freeze_thaw_freeze_thaw",
    "il": 35.0,
    "hl": "DOTAP",
    "hlPct": 15.0,
    "chol": 47.5,
    "peg": 2.5,
    "dose": 1.0,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F5_ALC0315_C14PEG",
    "experiment": "E2_in_vivo_PEG_lipid_uptake_screen_DMG_PEG_C14",
    "il": null,
    "hl": "DSPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E2_in_vivo_PEG_lipid_uptake_screen_DSG_PEG_C18",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F5_ALC0315_C14PEG",
    "experiment": "E2b_in_vivo_PEG_lipid_mRNA_screen_DMG_PEG_C14",
    "il": null,
    "hl": "DSPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": 0.3,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F6_ALC0315_C16PEG",
    "experiment": "E2b_in_vivo_PEG_lipid_mRNA_screen_DPG_PEG_C16",
    "il": null,
    "hl": "DSPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": 0.3,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E2b_in_vivo_PEG_lipid_mRNA_screen_DSG_PEG_C18",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 0.3,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "PBS_control",
    "experiment": "E2b_in_vivo_PEG_lipid_mRNA_screen_PBS",
    "il": null,
    "hl": "N/R",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": 0.3,
    "tgt": "Active",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "LOW"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F9_IgG_isotype",
    "experiment": "E4_in_vivo_receptor_and_clone_screen_Isotype",
    "il": null,
    "hl": "DSPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": 1.0,
    "tgt": "Active",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F10_unconjugated",
    "experiment": "E4_in_vivo_receptor_and_clone_screen_Free_Ab_plus_LNP",
    "il": null,
    "hl": "DSPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": 1.0,
    "tgt": "None",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E5_in_vivo_Cre_dose_response_0.3_mg_kg_HSPC",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 0.3,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E5_in_vivo_Cre_dose_response_0.3_mg_kg_LT_HSC",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 0.3,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E5_in_vivo_Cre_dose_response_1.0_mg_kg_HSPC",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E5_in_vivo_Cre_dose_response_1.0_mg_kg_LT_HSC",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E5_in_vivo_Cre_dose_response_1.0_mg_kg_unconjugated",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E6_peripheral_blood_lineage_tracking_2wk_myeloid_CD11b",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E6_peripheral_blood_lineage_tracking_2wk_B_cells_B220",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E6_peripheral_blood_lineage_tracking_2wk_T_cells_CD3e",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E6_peripheral_blood_lineage_tracking_14wk_myeloid",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E6_peripheral_blood_lineage_tracking_14wk_B_cells",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E6_peripheral_blood_lineage_tracking_14wk_T_cells",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "F7_ALC0315_C18PEG",
    "experiment": "E6_peripheral_blood_lineage_tracking_14wk_erythrocytes_TER119",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Shi 2023",
    "paperId": "shi_2023",
    "id": "PBS_control",
    "experiment": "E8_ligand_density_optimization_PBS",
    "il": null,
    "hl": "N/R",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": 0.3,
    "tgt": "Active",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "LOW"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP1",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP5",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP6",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP7",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP9",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP11",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP14",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP17",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP19",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP20",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP21",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP22",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP25",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP27",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP30",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP31",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DDAB",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP33",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP35",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP38",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP39",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP42",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP44",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP47",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP51",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP53",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP54",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP57",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP59",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP60",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP61",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP62",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP63",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTMA",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP67",
    "experiment": "barcoded_screen",
    "il": 35.0,
    "hl": "DOTAP",
    "hlPct": 15.0,
    "chol": 47.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP68",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP69",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP71",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP73",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP76",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP77",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP79",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP81",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP82",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP84",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP85",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP87",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP89",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP91",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "DOTAP",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP95",
    "experiment": "barcoded_screen",
    "il": 50.0,
    "hl": "DOTAP",
    "hlPct": 30.0,
    "chol": 17.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP98",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP99",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP101",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP102",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP103",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP105",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP107",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP108",
    "experiment": "barcoded_screen",
    "il": 45.0,
    "hl": "EPC",
    "hlPct": 15.0,
    "chol": 37.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP109",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP111",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP113",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP115",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP116",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP118",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP122",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP125",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP126",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Kim 2024",
    "paperId": "kim_2024",
    "id": "LNP127",
    "experiment": "barcoded_screen",
    "il": null,
    "hl": "EPC",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "PARTIAL"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_A5",
    "experiment": "Lian_A5_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_A7",
    "experiment": "Lian_A7_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": true,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_A8",
    "experiment": "Lian_A8_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_A8",
    "experiment": "Lian_A8_validated_n3",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_A9",
    "experiment": "Lian_A9_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_A10",
    "experiment": "Lian_A10_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_A11_original_discovery",
    "experiment": "Lian_A11_original_discovery_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_A12",
    "experiment": "Lian_A12_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_A13",
    "experiment": "Lian_A13_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_A13",
    "experiment": "Lian_A13_validated_n3",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": true,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_C6",
    "experiment": "Lian_C6_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_C6",
    "experiment": "Lian_C6_validated_n3",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": true,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_C7",
    "experiment": "Lian_C7_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_C8",
    "experiment": "Lian_C8_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_C9",
    "experiment": "Lian_C9_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": true,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_C10",
    "experiment": "Lian_C10_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_AT4",
    "experiment": "Lian_AT4_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_AT5",
    "experiment": "Lian_AT5_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_AT6",
    "experiment": "Lian_AT6_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_AT7",
    "experiment": "Lian_AT7_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_TC",
    "experiment": "Lian_TC_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_CC",
    "experiment": "Lian_CC_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_AA10",
    "experiment": "Lian_AA10_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_AA11",
    "experiment": "Lian_AA11_screen_n1",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "MEDIUM"
  },
  {
    "p": "Lian 2024",
    "paperId": "lian_2024",
    "id": "Lian_AA11",
    "experiment": "Lian_AA11_validated_n3",
    "il": 19.0,
    "hl": "DOPE",
    "hlPct": 19.0,
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 20.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "curated",
    "confidence": "HIGH"
  },
  {
    "p": "Hofstraat 2025",
    "paperId": "hofstraat_2025",
    "id": "aNP8-siLAMP1",
    "experiment": "invivo_LAMP1_knockdown_4x0.5mpk",
    "il": 46.0,
    "hl": "POPC",
    "hlPct": 26.0,
    "chol": 28.0,
    "peg": null,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hofstraat 2025",
    "paperId": "hofstraat_2025",
    "id": "aNP15-siLAMP1",
    "experiment": "invivo_LAMP1_knockdown_4x0.5mpk",
    "il": 14.0,
    "hl": "DMPC",
    "hlPct": 26.0,
    "chol": 61.0,
    "peg": null,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hofstraat 2025",
    "paperId": "hofstraat_2025",
    "id": "aNP18-siLAMP1",
    "experiment": "invivo_LAMP1_knockdown_4x0.5mpk",
    "il": 24.0,
    "hl": "DMPC",
    "hlPct": 23.0,
    "chol": 53.0,
    "peg": null,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hofstraat 2025",
    "paperId": "hofstraat_2025",
    "id": "aNP27-siLAMP1",
    "experiment": "invivo_LAMP1_knockdown_4x0.5mpk",
    "il": 8.0,
    "hl": "POPC",
    "hlPct": 13.0,
    "chol": 35.0,
    "peg": null,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hofstraat 2025",
    "paperId": "hofstraat_2025",
    "id": "aNP29-siLAMP1",
    "experiment": "invivo_LAMP1_knockdown_4x0.5mpk",
    "il": 18.0,
    "hl": "POPC",
    "hlPct": 15.0,
    "chol": 16.0,
    "peg": null,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hofstraat 2025",
    "paperId": "hofstraat_2025",
    "id": "aNP42-siLAMP1",
    "experiment": "invivo_LAMP1_knockdown_4x0.5mpk",
    "il": 14.0,
    "hl": "DMPC",
    "hlPct": 14.0,
    "chol": 32.0,
    "peg": null,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hofstraat 2025",
    "paperId": "hofstraat_2025",
    "id": "aNP67-siLAMP1",
    "experiment": "invivo_LAMP1_knockdown_4x0.5mpk",
    "il": 18.0,
    "hl": "DMPC",
    "hlPct": 11.0,
    "chol": 4.0,
    "peg": null,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hofstraat 2025",
    "paperId": "hofstraat_2025",
    "id": "aNP72-siLAMP1",
    "experiment": "invivo_LAMP1_knockdown_4x0.5mpk",
    "il": 19.0,
    "hl": "DMPC",
    "hlPct": 9.0,
    "chol": 21.0,
    "peg": null,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hofstraat 2025",
    "paperId": "hofstraat_2025",
    "id": "LNP-siLAMP1 (Onpattro-type control)",
    "experiment": "invivo_LAMP1_knockdown_4x0.5mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.5,
    "tgt": "None",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Shi thesis 2025",
    "paperId": "shi_2025_thesis",
    "id": "anti-CD117 LNP (FL-S, 20 mol% DSPC, clone 2B8)",
    "experiment": "invivo_base_editing_CD45_2.5mpk",
    "il": 44.5,
    "hl": "DSPC",
    "hlPct": 20.0,
    "chol": 33.5,
    "peg": 1.5,
    "dose": 2.5,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0.5,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Shi thesis 2025",
    "paperId": "shi_2025_thesis",
    "id": "anti-CD117 LNP formulation A (ALC-0315, 10 mol% DSPC, clone 2B8)",
    "experiment": "invivo_mCherry_screen_0.3mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.0,
    "peg": 1.5,
    "dose": 0.3,
    "tgt": "CD117",
    "mt": "protein_expression",
    "cv": 0.5,
    "cls": null,
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Shi thesis 2025",
    "paperId": "shi_2025_thesis",
    "id": "anti-CD117 LNP formulation D (ALC-0315, 20 mol% DSPC, clone QA19A91)",
    "experiment": "invivo_mCherry_screen_0.3mpk",
    "il": 44.5,
    "hl": "DSPC",
    "hlPct": 20.0,
    "chol": 33.5,
    "peg": 1.5,
    "dose": 0.3,
    "tgt": "CD117",
    "mt": "protein_expression",
    "cv": 0.5,
    "cls": null,
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Shi thesis 2025",
    "paperId": "shi_2025_thesis",
    "id": "EC-LNP (FUJIFILM proprietary)",
    "experiment": "invivo_siKit1_CD117_knockdown_0.4mpk",
    "il": null,
    "hl": "N/R",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": 0.4,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Swart 2023",
    "paperId": "swart_2023",
    "id": "LNP (MC3/DSPC/Chol/DMG-PEG2000)",
    "experiment": "invivo_biodistribution_BM_uptake",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "None",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Swart 2023",
    "paperId": "swart_2023",
    "id": "LDV-LNP (VLA-4 targeted)",
    "experiment": "invivo_biodistribution_BM_uptake",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "VLA-4 (CD49D/CD29 INTEGRIN)",
    "mt": "barcode_delivery",
    "cv": 0.1,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Chander 2023",
    "paperId": "chander_2023",
    "id": "LNP GFP mRNA 10 mol% DSPC (Onpattro-type)",
    "experiment": "invivo_GFP_expression_BM_3mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 3.0,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Chander 2023",
    "paperId": "chander_2023",
    "id": "lcLNP GFP mRNA 40 mol% ESM",
    "experiment": "invivo_GFP_expression_BM_3mpk",
    "il": 33.0,
    "hl": "egg sphingomyelin (ESM)",
    "hlPct": 40.0,
    "chol": 25.5,
    "peg": 1.5,
    "dose": 3.0,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Chander 2023",
    "paperId": "chander_2023",
    "id": "LNP GFP mRNA 10 mol% ESM",
    "experiment": "invivo_GFP_expression_BM_3mpk",
    "il": 50.0,
    "hl": "egg sphingomyelin (ESM)",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 3.0,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Tarab-Ravski 2023",
    "paperId": "tarab_ravski_2023",
    "id": "alphaCD38-L10-tLNP",
    "experiment": "invivo_MM_efficacy_siCKAP5_5x1mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD38",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Tarab-Ravski 2023",
    "paperId": "tarab_ravski_2023",
    "id": "alphaCD38-L10-tLNP",
    "experiment": "invivo_MM_control_siNC_5x1mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD38",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Peng 2026",
    "paperId": "peng_2026",
    "id": "E5-LNP@siAE",
    "experiment": "invivo_AML_efficacy_0.6mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.6,
    "tgt": "CXCR4",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Peng 2026",
    "paperId": "peng_2026",
    "id": "LNP@siAE (no E5 peptide)",
    "experiment": "invivo_AML_efficacy_0.6mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.6,
    "tgt": "None",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Zhao 2026",
    "paperId": "zhao_2026",
    "id": "CD34/LNP-CAR mRNA",
    "experiment": "invivo_CAR_CD34_generation_10ug",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "CD34",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Zhao 2026",
    "paperId": "zhao_2026",
    "id": "LNP-CAR mRNA (no anti-CD34)",
    "experiment": "invivo_CAR_CD34_generation_10ug",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "None",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Jyotsana 2019",
    "paperId": "jyotsana_2019",
    "id": "LNP-siBCR-ABL",
    "experiment": "invivo_CML_xenograft_5mpk_x3",
    "il": null,
    "hl": "N/R",
    "hlPct": null,
    "chol": null,
    "peg": 1.5,
    "dose": 5.0,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Jyotsana 2019",
    "paperId": "jyotsana_2019",
    "id": "LNP-CTRL siRNA (AHA1)",
    "experiment": "invivo_biodistribution_safety_healthy_NSG",
    "il": null,
    "hl": "N/R",
    "hlPct": null,
    "chol": null,
    "peg": 1.5,
    "dose": 5.0,
    "tgt": "Intrinsic",
    "mt": "barcode_delivery",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Dahlman 2014",
    "paperId": "dahlman_2014",
    "id": "7C1 + C14PEG2000",
    "experiment": "invivo_endothelial_silencing_dose_response",
    "il": null,
    "hl": "N/R",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": 0.6,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 1",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 41.9,
    "hl": "DSPC",
    "hlPct": 34.6,
    "chol": 22.7,
    "peg": 0.75,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 2",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 41.7,
    "hl": "DSPC",
    "hlPct": 6.1,
    "chol": 51.5,
    "peg": 0.76,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 3",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 52.8,
    "hl": "DSPC",
    "hlPct": 13.7,
    "chol": 32.1,
    "peg": 1.5,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 4",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 27.2,
    "hl": "DSPC",
    "hlPct": 32.3,
    "chol": 38.9,
    "peg": 1.5,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 5",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 60.0,
    "hl": "DSPC",
    "hlPct": 14.8,
    "chol": 24.7,
    "peg": 0.5,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 6",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 40.0,
    "hl": "DSPC",
    "hlPct": 14.5,
    "chol": 45.0,
    "peg": 0.5,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 7",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 23.4,
    "hl": "DSPC",
    "hlPct": 46.1,
    "chol": 29.8,
    "peg": 0.75,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 8",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 41.7,
    "hl": "DSPC",
    "hlPct": 6.1,
    "chol": 51.5,
    "peg": 0.76,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 9",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 35.9,
    "hl": "DSPC",
    "hlPct": 41.0,
    "chol": 20.8,
    "peg": 2.25,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 10",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 31.0,
    "hl": "DSPC",
    "hlPct": 18.5,
    "chol": 49.3,
    "peg": 1.25,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 11",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 12",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 24.5,
    "hl": "DSPC",
    "hlPct": 45.9,
    "chol": 28.3,
    "peg": 1.25,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 13",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 20.0,
    "hl": "DSPC",
    "hlPct": 42.9,
    "chol": 34.1,
    "peg": 3.0,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Hanafy 2025",
    "paperId": "hanafy_2025",
    "id": "PRELIVE LNP 14",
    "experiment": "invivo_luciferase_organ_panel_0.3mpk",
    "il": 40.0,
    "hl": "DSPC",
    "hlPct": 14.5,
    "chol": 45.0,
    "peg": 0.5,
    "dose": 0.3,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Chappell 2024",
    "paperId": "chappell_2024",
    "id": "mRNACre-LNP-CD117",
    "experiment": "exvivo_Cre_deletion_Hba_lin_cells",
    "il": null,
    "hl": "N/R",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "CD117 (MURINE, MCD117)",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Chappell 2024",
    "paperId": "chappell_2024",
    "id": "mRNACre-LNP-CD117",
    "experiment": "posttransplant_BM_alpha_globin_deletion_ddPCR",
    "il": null,
    "hl": "N/R",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "CD117 (MURINE)",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Palchaudhuri 2025",
    "paperId": "palchaudhuri_2025",
    "id": "HSC-LNP (Tessera, proprietary)",
    "experiment": "invivo_B2M_gene_writing_LT-HSC",
    "il": null,
    "hl": "N/R",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "OTHER",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "abstract-only",
    "status": "extracted_abstract_only",
    "confidence": "LOW"
  },
  {
    "p": "Palchaudhuri 2025",
    "paperId": "palchaudhuri_2025",
    "id": "HSC-LNP (Tessera, proprietary)",
    "experiment": "invivo_HBB_Makassar_installation_LT-HSC",
    "il": null,
    "hl": "N/R",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "OTHER",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "abstract-only",
    "status": "extracted_abstract_only",
    "confidence": "LOW"
  },
  {
    "p": "Palchaudhuri 2025",
    "paperId": "palchaudhuri_2025",
    "id": "HSC-LNP (Tessera, proprietary)",
    "experiment": "invivo_GFP_reporter_delivery_LT-HSC",
    "il": null,
    "hl": "N/R",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "OTHER",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "abstract-only",
    "status": "extracted_abstract_only",
    "confidence": "LOW"
  },
  {
    "p": "Xue 2022",
    "paperId": "xue_2022",
    "id": "490BP-C14 LNP",
    "experiment": "invivo_luciferase_bone_delivery_0.5mpk",
    "il": 35.0,
    "hl": "DOPE",
    "hlPct": 16.0,
    "chol": 46.5,
    "peg": 2.5,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "partial",
    "status": "partial_pending_main_text",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xue 2022",
    "paperId": "xue_2022",
    "id": "490-C14 LNP (BP-free control)",
    "experiment": "invivo_luciferase_bone_delivery_0.5mpk",
    "il": 35.0,
    "hl": "DOPE",
    "hlPct": 16.0,
    "chol": 46.5,
    "peg": 2.5,
    "dose": 0.5,
    "tgt": "Intrinsic",
    "mt": "protein_expression",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "partial",
    "status": "partial_pending_main_text",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-028-ABE8e-PCSK9 (Library A lead)",
    "experiment": "invivo_PCSK9_editing_C57_2mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-217-ABE8e-PCSK9 (Library B lead)",
    "experiment": "invivo_PCSK9_editing_C57_2mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-306-ABE8e-PCSK9 (Library C lead)",
    "experiment": "invivo_PCSK9_editing_C57_2mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-168-ABE8e-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_2mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-028-ABE8e-HBG (ABE8e + sgRNA-25)",
    "experiment": "invivo_HBG_editing_humanized_NCGX_2mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-168-ABE8e-HBG (ABE8e + sgRNA-25)",
    "experiment": "invivo_HBG_editing_TDT_humanized_NCGX_1mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-168-Cre-miR-122T",
    "experiment": "invivo_Cre_Ai14_HSPC_subsets_1mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "high",
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "HIGH"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-MC3-Cre-miR-122T (liver-tropic control)",
    "experiment": "invivo_Cre_Ai14_HSPC_subsets_1mpk",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-151-ABE8e-PCSK9 (secondary screen, Library A)",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-163-ABE8e-PCSK9 (secondary screen, Library A)",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-164-ABE8e-PCSK9 (secondary screen, Library A)",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-165-ABE8e-PCSK9 (secondary screen, Library A)",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-167-ABE8e-PCSK9 (secondary screen, Library A)",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-169-ABE8e-PCSK9 (secondary screen, Library A)",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Iida 2022",
    "paperId": "iida_2022",
    "id": "LNP-43 (tumor-tropic, Bayesian-optimized for Jurkat)",
    "experiment": "invivo_NONE_invitro_RUNX1_knockdown_panel",
    "il": null,
    "hl": "DOPE",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Iida 2022",
    "paperId": "iida_2022",
    "id": "LNP-79 (tumor-tropic, Bayesian-optimized for Jurkat)",
    "experiment": "invivo_NONE_invitro_RUNX1_knockdown_panel",
    "il": null,
    "hl": "DOPE",
    "hlPct": null,
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "Intrinsic",
    "mt": "knockdown",
    "cv": 0.0,
    "cls": null,
    "boundary": false,
    "recordType": "detailed",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-001-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-002-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-003-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-004-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-005-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-006-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-007-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-008-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-009-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-010-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-011-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-012-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-013-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-014-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-015-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-016-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-017-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-018-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-019-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-020-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-021-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-022-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-023-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-024-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-025-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-026-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-027-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-028-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-029-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-030-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-031-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-032-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-033-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-034-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-035-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryA_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-200-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-201-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-202-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-203-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-204-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-205-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-206-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-207-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-208-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-209-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-210-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-211-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-212-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-213-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-214-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-215-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-216-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-217-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-218-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-219-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-220-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-221-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-222-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-223-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-224-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-225-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-226-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-227-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-228-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-229-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-230-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-231-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryB_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-300-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-301-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-302-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-303-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-304-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-305-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-306-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-307-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-308-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-309-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-310-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-311-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-312-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-313-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-314-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-315-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-316-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-317-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-318-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-319-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-320-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-321-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-322-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-323-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-324-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_libraryC_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-121-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-122-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-123-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-124-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-125-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-126-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-127-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-128-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-129-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-140-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-141-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-142-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-143-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-144-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-145-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-146-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-147-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-148-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-149-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-150-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-152-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-153-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-154-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-155-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-156-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-157-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-158-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-159-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-160-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-161-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-162-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-166-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-180-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-181-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-182-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-183-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-184-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "medium",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-185-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-186-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-187-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-188-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  },
  {
    "p": "Xu 2026",
    "paperId": "xu_2026",
    "id": "LNP-189-ABE8e/sgRNA-PCSK9",
    "experiment": "invivo_PCSK9_editing_C57_secondary_screen",
    "il": 50.0,
    "hl": "DSPC",
    "hlPct": 10.0,
    "chol": 38.5,
    "peg": 1.5,
    "dose": 2.0,
    "tgt": "Intrinsic",
    "mt": "editing",
    "cv": 0.0,
    "cls": "low",
    "boundary": false,
    "recordType": "screen",
    "status": "extracted",
    "confidence": "MEDIUM"
  }
];
// END:formulations

const pegComparison = [
  { peg: "ALC-0159", n: 3, mean: 18.83, max: 48, formulations: [{id:"LNP89",bm:5},{id:"LNP91",bm:3.5},{id:"LNP95",bm:48}] },
  { peg: "C14PEG2000", n: 4, mean: 3.88, max: 13, formulations: [{id:"LNP67",bm:13},{id:"LNP68",bm:1},{id:"LNP69",bm:0.5},{id:"LNP71",bm:1}] },
  { peg: "DMG-PEG", n: 5, mean: 1.9, max: 6, formulations: [{id:"LNP81",bm:0.5},{id:"LNP82",bm:0.5},{id:"LNP84",bm:1.5},{id:"LNP85",bm:6},{id:"LNP87",bm:1}] },
  { peg: "C18PEG2000", n: 4, mean: 0.32, max: 0.5, formulations: [{id:"LNP73",bm:0.3},{id:"LNP76",bm:0.2},{id:"LNP77",bm:0.3},{id:"LNP79",bm:0.5}] },
];

const helperPegInteraction = [
  {helper:"DOTAP",peg:"ALC-0159",bm:18.8},{helper:"DOTAP",peg:"C14PEG2000",bm:3.9},{helper:"DOTAP",peg:"DMG-PEG",bm:1.9},{helper:"DOTAP",peg:"C18PEG2000",bm:0.3},
  {helper:"18:1 EPC",peg:"C18PEG2000",bm:5.9},{helper:"18:1 EPC",peg:"DMG-PEG",bm:2.8},{helper:"18:1 EPC",peg:"C14PEG2000",bm:2.7},{helper:"18:1 EPC",peg:"ALC-0159",bm:2.0},
  {helper:"DOTMA",peg:"DMG-PEG",bm:0.8},{helper:"DOTMA",peg:"ALC-0159",bm:0.7},{helper:"DOTMA",peg:"C18PEG2000",bm:0.7},{helper:"DOTMA",peg:"C14PEG2000",bm:0.6},
  {helper:"DDAB",peg:"ALC-0159",bm:0.6},{helper:"DDAB",peg:"C14PEG2000",bm:0.4},{helper:"DDAB",peg:"C18PEG2000",bm:0.3},{helper:"DDAB",peg:"DMG-PEG",bm:0.3},
];

const headgroupData = [
  { helper: "DOTAP", n: 16, mean: 5.18, std: 11.52, median: 1.0, max: 48, values: [48,13,6,5,3.5,1.5,1,1,1,0.5,0.5,0.5,0.5,0.3,0.3,0.2] },
  { helper: "18:1 EPC", n: 18, mean: 3.44, std: 3.24, median: 2.25, max: 15, values: [15,8,5.5,4,3,3,3,2.5,2.5,2,2,2,2,1.5,1.5,1.5,1.5,1.5] },
  { helper: "DOTMA", n: 16, mean: 0.71, std: 0.26, median: 0.5, max: 1, values: [1,1,1,1,1,1,1,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.5,0.3] },
  { helper: "DDAB", n: 16, mean: 0.39, std: 0.19, median: 0.3, max: 1, values: [1,0.5,0.5,0.5,0.5,0.5,0.3,0.3,0.3,0.3,0.3,0.3,0.3,0.2,0.2,0.2] },
];
const headgroupStats = { u: 207, p: 0.0024, fold: 13.4 };

const doseResponse = [
  { system: "Shi CD117/C18 (uptake)", points: [{d:0.3,r:75},{d:1.0,r:90}], ec30: 0.036, ec50: 0.09, species: "Mouse", platform: "tLNP", note: "DiR uptake %, not editing" },
  { system: "Breda CD117", points: [{d:0.05,r:10},{d:0.25,r:55}], ec30: 0.124, ec50: 0.218, species: "Mouse", platform: "tLNP" },
  { system: "Kim LNP67 (mouse)", points: [{d:0.5,r:12},{d:1.0,r:23},{d:2.0,r:35}], ec30: 1.548, ec50: 3.77, species: "Mouse", platform: "LNP" },
  { system: "Kim LNP67 (human ex vivo)", points: [{d:0.25,r:15},{d:0.5,r:22},{d:1.0,r:25},{d:2.0,r:38},{d:4.0,r:72}], ec30: 1.548, ec50: 3.77, species: "Human", platform: "LNP" },
  { system: "Lian AA11", points: [{d:0.6,r:5.2}], ec30: null, ec50: null, species: "Mouse", platform: "LNP", note: "Single dose, no curve fit" },
];

const lianCellTypes = ["LT_HSC","LSK","LMPP","MPP","CMP","GMP","MEP","B","T_total","T_CD4","T_CD8","macrophage","monocyte","neutrophil"];
const lianFormulations = [
  {id:"C8",lthsc:40,validated:false,cells:[40,41,37,53,44,29,20,2,14,24,29,26,6,23]},
  {id:"AA11",lthsc:40,validated:true,cells:[40,45,46,58,66,28,17,7,13,27,24,32,8,23]},
  {id:"AA10",lthsc:37,validated:false,cells:[37,38,37,55,46,27,14,4,13,23,14,25,5,22]},
  {id:"A8",lthsc:35,validated:true,cells:[35,44,33,63,59,37,19,5,15,24,14,30,6,21]},
  {id:"A10",lthsc:35,validated:false,cells:[35,23,17,34,38,23,8,2,10,17,13,21,2,12]},
  {id:"A11",lthsc:35,validated:false,cells:[35,40,43,58,54,33,19,4,19,28,21,22,5,21]},
  {id:"A12",lthsc:35,validated:false,cells:[35,36,33,54,42,19,12,4,12,25,13,23,4,15]},
  {id:"CC",lthsc:34,validated:false,cells:[34,33,31,50,40,23,14,4,13,26,15,21,5,21]},
  {id:"C10",lthsc:33,validated:false,cells:[33,34,23,45,23,24,20,5,5,23,20,21,4,14]},
  {id:"AT5",lthsc:32,validated:false,cells:[32,34,29,48,37,31,15,5,16,23,11,26,5,21]},
  {id:"C6",lthsc:31,validated:true,cells:[31,34,34,49,47,28,13,5,13,19,11,28,3,21]},
  {id:"A7",lthsc:30,validated:false,cells:[30,23,16,31,23,15,11,2,10,21,10,16,2,11]},
  {id:"C9",lthsc:30,validated:false,cells:[30,34,32,53,40,27,20,7,7,11,16,24,5,18]},
  {id:"AT6",lthsc:29,validated:false,cells:[29,35,20,38,28,17,10,29,12,25,18,18,3,17]},
  {id:"AT4",lthsc:28,validated:false,cells:[28,34,37,43,44,24,10,22,15,28,33,24,11,16]},
  {id:"AT7",lthsc:27,validated:false,cells:[27,29,23,46,33,20,9,8,10,20,11,13,6,13]},
  {id:"TC",lthsc:27,validated:false,cells:[27,28,20,38,33,23,13,3,11,17,18,18,9,13]},
  {id:"A9",lthsc:24,validated:false,cells:[24,31,29,42,30,20,13,4,17,25,24,21,3,16]},
  {id:"A13",lthsc:24,validated:true,cells:[24,23,17,34,46,23,8,2,10,17,13,22,5,25]},
  {id:"A5",lthsc:13,validated:false,cells:[13,17,13,26,19,10,6,3,9,15,8,11,3,9]},
  {id:"C7",lthsc:13,validated:false,cells:[13,18,14,33,22,13,7,5,13,14,13,14,3,12]},
];

// DATA:lopocvFolds
const lopocvFolds = [
  {
    "paper": "xu_2026",
    "n": 147,
    "lgbm": 0.333
  },
  {
    "paper": "kim_2024",
    "n": 80,
    "lgbm": 0.605
  },
  {
    "paper": "shi_2023",
    "n": 21,
    "lgbm": 0.31
  },
  {
    "paper": "lian_2024",
    "n": 21,
    "lgbm": 0.0
  },
  {
    "paper": "hanafy_2025",
    "n": 14,
    "lgbm": 0.5
  },
  {
    "paper": "hofstraat_2025",
    "n": 9,
    "lgbm": 0.333
  },
  {
    "paper": "breda_2023",
    "n": 9,
    "lgbm": 0.5
  },
  {
    "paper": "palchaudhuri_2025",
    "n": 3,
    "lgbm": 0.0
  },
  {
    "paper": "tarab_ravski_2023",
    "n": 2,
    "lgbm": 0.0
  },
  {
    "paper": "swart_2023",
    "n": 2,
    "lgbm": 0.5
  },
  {
    "paper": "chappell_2024",
    "n": 2,
    "lgbm": 0.0
  },
  {
    "paper": "shi_2025_thesis",
    "n": 1,
    "lgbm": 0.0
  }
];
// END:lopocvFolds

const roleColor = () => INK;

const ParetoTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const c = platformColor(d.platform);
  return (
    <div style={{ background: "#fff", border: `1.5px solid ${c}`, padding: "12px 16px", maxWidth: 280, fontSize: 14, lineHeight: 1.5 }}>
      <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4, color: c }}>{d.name}</div>
      <div style={{ color: "#666", marginBottom: 8 }}>{d.detail}</div>
      <div style={{ display: "flex", gap: 16 }}>
        <span>BM: <strong>{d.bm}%</strong></span>
        <span>Liver: <strong>{d.liver !== null ? `${d.liver}%` : "N/R"}</strong></span>
      </div>
      <div style={{ color: "#999", marginTop: 4, fontSize: 13 }}>
        {d.platform} · {d.metric === "editing" ? "Editing" : "Reporter"} · {d.species}{d.n ? ` · n=${d.n}` : ""}
      </div>
    </div>
  );
};

const CustomDot = (props) => {
  const { cx, cy, payload } = props;
  if (!cx || !cy) return null;
  const c = platformColor(payload.platform);
  const filled = payload.metric === "editing";
  const size = payload.n >= 3 ? 6 : 4;
  if (payload.platform === "VLP") return <rect x={cx-size} y={cy-size} width={size*2} height={size*2} fill={filled?c:"#fff"} stroke={c} strokeWidth={2} />;
  if (payload.platform === "tLNP") { const s=size+1; return <polygon points={`${cx},${cy-s} ${cx-s},${cy+s} ${cx+s},${cy+s}`} fill={filled?c:"#fff"} stroke={c} strokeWidth={2} />; }
  return <circle cx={cx} cy={cy} r={size} fill={filled?c:"#fff"} stroke={c} strokeWidth={2} />;
};

const tabs = ["Atlas","Pareto","Compare (beta)","Formulations","PEG Architecture","Headgroup","Dose-Response","Lian Heatmap","Features","Papers","Findings"];

// DATA:shapContext
const shapContext = {
  "il": {
    "rank": 5,
    "shap": 0.18,
    "direction": "Atlas-wide feature importance is descriptive; paper, assay, and repeated formulations can contribute to this rank."
  },
  "cd117": {
    "rank": 9,
    "shap": 0.13,
    "direction": "Atlas-wide feature importance is descriptive; paper, assay, and repeated formulations can contribute to this rank."
  },
  "chol": {
    "rank": 4,
    "shap": 0.21,
    "direction": "Atlas-wide feature importance is descriptive; paper, assay, and repeated formulations can contribute to this rank."
  },
  "dose": {
    "rank": 1,
    "shap": 0.6,
    "direction": "Atlas-wide feature importance is descriptive; paper, assay, and repeated formulations can contribute to this rank."
  },
  "il_mw": {
    "rank": 2,
    "shap": 0.38,
    "direction": "Atlas-wide feature importance is descriptive; paper, assay, and repeated formulations can contribute to this rank."
  },
  "dotap": {
    "rank": 15,
    "shap": 0.09,
    "direction": "Atlas-wide feature importance is descriptive; paper, assay, and repeated formulations can contribute to this rank."
  },
  "helper_pct": {
    "rank": 3,
    "shap": 0.28,
    "direction": "Atlas-wide feature importance is descriptive; paper, assay, and repeated formulations can contribute to this rank."
  }
};
// END:shapContext
const NUM = "'Space Mono', 'Courier New', monospace";

export default function Explorer() {
  const [activeTab, setActiveTab] = useState("Atlas");
  const [sortCol, setSortCol] = useState("p");
  const [sortDir, setSortDir] = useState(1);
  const [filterPaper, setFilterPaper] = useState("all");

  // Compare tab state
  const [cmpIl, setCmpIl] = useState(35);
  const [cmpHl, setCmpHl] = useState("DOTAP");
  const [cmpHlPct, setCmpHlPct] = useState(15);
  const [cmpChol, setCmpChol] = useState(47);
  const [cmpPeg, setCmpPeg] = useState(1.5);
  const [cmpCv, setCmpCv] = useState(0);
  const [cmpDose, setCmpDose] = useState(0.5);
  const [cmpTgt, setCmpTgt] = useState("None");

  // Precompute feature stats for distance calculation
  const featureStats = useMemo(() => {
    const cols = ["il", "hlPct", "chol", "peg", "cv", "dose"];
    const stats = {};
    for (const col of cols) {
      const vals = formulations.map(f => f[col]).filter(v => v != null);
      const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
      const std = Math.sqrt(vals.reduce((a, b) => a + (b - mean) ** 2, 0) / vals.length) || 1;
      stats[col] = { mean, std };
    }
    return stats;
  }, []);

  // Find nearest neighbors
  const neighbors = useMemo(() => {
    const stdVal = (v, col) => v != null ? (v - featureStats[col].mean) / featureStats[col].std : 0;

    return formulations
      .filter(f => f.cls != null)
      .map(f => {
        let dist = 0;
        dist += (stdVal(cmpIl, "il") - stdVal(f.il, "il")) ** 2;
        dist += (stdVal(cmpHlPct, "hlPct") - stdVal(f.hlPct, "hlPct")) ** 2;
        dist += (stdVal(cmpChol, "chol") - stdVal(f.chol, "chol")) ** 2;
        dist += (stdVal(cmpPeg, "peg") - stdVal(f.peg, "peg")) ** 2;
        dist += (stdVal(cmpCv, "cv") - stdVal(f.cv, "cv")) ** 2;
        dist += (stdVal(cmpDose, "dose") - stdVal(f.dose, "dose")) ** 2;
        // Categorical: helper lipid match
        dist += f.hl === cmpHl ? 0 : 1;
        // Categorical: targeting match
        const fTgt = f.tgt === "CD117" ? "CD117" : "None";
        dist += fTgt === cmpTgt ? 0 : 1;
        return { ...f, dist: Math.sqrt(dist) };
      })
      .sort((a, b) => a.dist - b.dist)
      .slice(0, 5);
  }, [cmpIl, cmpHl, cmpHlPct, cmpChol, cmpPeg, cmpCv, cmpDose, cmpTgt, featureStats]);

  const sortedFormulations = useMemo(() => {
    let data = [...formulations];
    if (filterPaper !== "all") data = data.filter(r => r.p === filterPaper);
    data.sort((a, b) => {
      const av = a[sortCol], bv = b[sortCol];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === "string") return av.localeCompare(bv) * sortDir;
      return (av - bv) * sortDir;
    });
    return data;
  }, [sortCol, sortDir, filterPaper]);

  const handleSort = (col) => {
    if (sortCol === col) setSortDir(d => d * -1);
    else { setSortCol(col); setSortDir(1); }
  };

  const Th = ({col, label, w}) => (
    <th onClick={() => handleSort(col)} style={{ padding: "6px 8px", fontWeight: 600, fontSize: 12, letterSpacing: 0.5, textTransform: "uppercase", color: "#999", cursor: "pointer", width: w, textAlign: typeof (formulations[0]||{})[col] === "number" ? "right" : "left", userSelect: "none", whiteSpace: "nowrap" }}>
      {label}{sortCol === col ? (sortDir === 1 ? " ▲" : " ▼") : ""}
    </th>
  );

  return (
    <div style={{ background: "#fff", minHeight: "100vh", color: "#000", fontFamily: "'DM Sans', -apple-system, sans-serif" }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Space+Mono:wght@400;700&display=swap');*{box-sizing:border-box;margin:0;padding:0;}`}</style>

      <header style={{ padding: "48px 48px 40px", borderBottom: "1px solid #000", background: "#f2f0ec" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <p style={{ fontSize: 13, letterSpacing: 3, textTransform: "uppercase", color: "#999", marginBottom: 16, fontFamily: "'DM Mono', monospace" }}>HSC-LNP Atlas</p>
          <h1 style={{ fontSize: 34, fontWeight: 300, lineHeight: 1.3, letterSpacing: -0.5 }}>
            Potency–Selectivity Tradeoff in<br /><span style={{ fontWeight: 700 }}>HSC-Targeted LNP Delivery</span>
          </h1>
          <p style={{ fontSize: 15, color: "#666", marginTop: 16 }}>{stats.rows} evidence rows {"·"} {stats.sources} matrix sources {"·"} {stats.columns} columns</p>
          <p style={{ fontSize: 14, color: "#999", marginTop: 4 }}>Tram Ngo · <a href="https://github.com/tramngo1603/lnp-hsc-atlas" style={{ color: "#000", textDecoration: "underline", textUnderlineOffset: 2 }}>github.com/tramngo1603/lnp-hsc-atlas</a></p>
        </div>
      </header>

      <nav style={{ borderBottom: "1px solid #e0e0e0", position: "sticky", top: 0, background: "#fff", zIndex: 10 }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", padding: "0 48px", overflowX: "auto" }}>
          {tabs.map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{
              background: "none", border: "none", cursor: "pointer", whiteSpace: "nowrap",
              padding: "14px 16px", fontSize: 13, fontWeight: activeTab === tab ? 600 : 400,
              color: activeTab === tab ? "#000" : "#999",
              borderBottom: activeTab === tab ? "2px solid #000" : "2px solid transparent",
              fontFamily: "'DM Sans', sans-serif", letterSpacing: 0.3,
            }}>{tab}</button>
          ))}
        </div>
      </nav>

      <main style={{ maxWidth: 1100, margin: "0 auto", padding: "40px 48px 80px" }}>

        {/* ATLAS */}
        {activeTab === "Atlas" && (<div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>Atlas Overview</h2>
          <p style={{ fontSize: 15, color: "#666", marginBottom: 28, lineHeight: 1.6 }}>
            The dataset contains {stats.rows} curated evidence rows from {stats.sources} sources. Unsupported fields remain null.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 1, background: "#e0e0e0", border: "1px solid #e0e0e0", marginBottom: 32 }}>
            {[
              { n: stats.rows, label: "Evidence rows", note: "Formulation-experiment units" },
              { n: stats.sources, label: "Matrix sources", note: "Published sources" },
              { n: stats.labeled, label: "Labeled rows", note: `${stats.rows - stats.labeled} unlabeled` },
              { n: `${coverageStats.completeColumns}/${coverageStats.totalColumns}`, label: "Complete columns", note: "Non-null in every row" },
              { n: stats.descriptorRows, label: "Rows with IL descriptors", note: `${(stats.descriptorRows / stats.rows * 100).toFixed(1)}% coverage` },
            ].map(item => (
              <div key={item.label} style={{ background: "#fff", padding: "18px 16px", textAlign: "center" }}>
                <div style={{ fontSize: 26, fontWeight: 700, fontFamily: NUM }}>{item.n}</div>
                <div style={{ fontSize: 12, fontWeight: 600, marginTop: 4 }}>{item.label}</div>
                <div style={{ fontSize: 11, color: "#999", marginTop: 3 }}>{item.note}</div>
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.3fr) minmax(260px, 0.7fr)", gap: 28, marginBottom: 36 }}>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 12 }}>Matrix sources</div>
              <div style={{ border: "1px solid #e0e0e0", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
                {sourceSummary.sources.map((source, index) => (
                  <div key={source.id} style={{ display: "flex", justifyContent: "space-between", gap: 12, padding: "9px 12px", borderBottom: "1px solid #f0f0f0", borderRight: index % 2 === 0 ? "1px solid #f0f0f0" : "none", fontSize: 12 }}>
                    <span>{source.label}</span>
                    <strong style={{ fontFamily: NUM }}>{source.rows}</strong>
                  </div>
                ))}
              </div>
              <p style={{ fontSize: 12, color: "#999", marginTop: 8 }}>Largest sources: Xu 2026 (148), Kim 2024 (80), and Lian 2024 (25).</p>
            </div>
            <div>
              <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 12 }}>Evidence row types</div>
              <div style={{ border: "1px solid #e0e0e0" }}>
                {Object.entries(sourceSummary.recordTypes).map(([type, count]) => (
                  <div key={type} style={{ display: "flex", justifyContent: "space-between", padding: "9px 12px", borderBottom: "1px solid #f0f0f0", fontSize: 12 }}>
                    <span style={{ textTransform: "capitalize" }}>{type.replaceAll("-", " ")}</span>
                    <strong style={{ fontFamily: NUM }}>{count}</strong>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div style={{ marginBottom: 36 }}>
            <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 12 }}>Coverage</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(175px, 1fr))", gap: 8 }}>
              {coverageStats.blocks.map(block => (
                <div key={block.label} style={{ border: "1px solid #e0e0e0", padding: "14px 16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                    <span style={{ fontSize: 12, fontWeight: 600 }}>{block.label}</span>
                    <span style={{ fontFamily: NUM, fontSize: 13, fontWeight: 700 }}>{block.percent}%</span>
                  </div>
                  <div style={{ height: 5, background: "#f0f0f0", margin: "10px 0 7px" }}>
                    <div style={{ width: `${block.percent}%`, height: "100%", background: block.percent < 50 ? RUST : INK }} />
                  </div>
                  <div style={{ fontSize: 11, color: "#999" }}>{block.filled}/{block.total} {"·"} {block.note}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 28 }}>
            <div style={{ border: "1px solid #e0e0e0", padding: "20px 22px" }}>
              <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 16 }}>Low-efficacy share</div>
              {[
                { label: "Low", value: labelDistribution.low, percent: labelDistribution.lowShare },
                { label: "Medium", value: labelDistribution.medium, percent: (labelDistribution.medium / labelDistribution.labeled * 100).toFixed(1) },
                { label: "High", value: labelDistribution.high, percent: (labelDistribution.high / labelDistribution.labeled * 100).toFixed(1) },
              ].map(item => (
                <div key={item.label} style={{ marginBottom: 14 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 5 }}><span>{item.label}</span><strong>{item.value} ({item.percent}%)</strong></div>
                  <div style={{ height: 8, background: "#f0f0f0" }}><div style={{ height: "100%", width: `${item.percent}%`, background: RUST }} /></div>
                </div>
              ))}
              <p style={{ fontSize: 12, color: "#666", lineHeight: 1.5 }}>{labelDistribution.labeled} labeled rows; {labelDistribution.unlabeled} unlabeled rows.</p>
            </div>
            <div style={{ border: "1px solid #e0e0e0", padding: "20px 22px" }}>
              <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 16 }}>Leakage-aware validation</div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10, fontSize: 13 }}><span>Row-random BA</span><strong style={{ fontFamily: NUM }}>{validationSummary.rowRandom.balancedAccuracy.toFixed(4)}</strong></div>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 10, fontSize: 13 }}><span>Formulation-grouped BA</span><strong style={{ fontFamily: NUM }}>{validationSummary.formulationGrouped.balancedAccuracy.toFixed(4)}</strong></div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}><span>Grouped overlap</span><strong style={{ fontFamily: NUM }}>0 tokens</strong></div>
              <p style={{ fontSize: 12, color: "#666", lineHeight: 1.5, marginTop: 14 }}>The grouped five-fold result is primary. Row-random folds leak 7 to 12 formulation tokens.</p>
            </div>
          </div>

          <div style={{ padding: "16px 20px", border: `1px solid ${OCHRE}60`, borderLeft: `3px solid ${OCHRE}`, background: `${OCHRE}08`, fontSize: 13, lineHeight: 1.6 }}>
            <strong>30% label boundary:</strong> The current rule uses high {">"}30% strictly. Four Lian rows at exactly 30% retain their established high labels and carry <code>label_boundary_case = 1</code>. These are documented boundary cases, not errors.
          </div>
        </div>)}

        {/* PARETO */}
        {activeTab === "Pareto" && (<div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>BM Delivery vs Liver Off-Target</h2>
          <p style={{ fontSize: 15, color: "#666", marginBottom: 12, lineHeight: 1.6 }}>
            <span style={{ color: INK, fontWeight: 600 }}>{"●"} Untargeted LNP</span>{" · "}
            <span style={{ color: RUST, fontWeight: 600 }}>{"▲"} Targeted LNP</span>{" · "}
            <span style={{ color: OCHRE, fontWeight: 600 }}>{"■"} VLP</span>
            {" - Filled = editing. Open = reporter."}
          </p>
          <p style={{ fontSize: 14, color: "#999", marginBottom: 32 }}>Hover any point for details. Shaded region = ideal zone ({">"}20% BM, {"<"}5% liver).</p>
          <div style={{ border: "1px solid #e0e0e0", padding: "24px 12px 12px 4px" }}>
            <ResponsiveContainer width="100%" height={500}>
              <ScatterChart margin={{ top: 20, right: 40, bottom: 32, left: 24 }}>
                <CartesianGrid stroke="#f0f0f0" />
                <XAxis type="number" dataKey="liver" domain={[0, 100]} tick={{ fontSize: 13, fill: "#999" }} stroke="#ddd" tickLine={false}>
                  <Label value="Liver signal (%)" position="bottom" offset={8} style={{ fontSize: 14, fill: "#666" }} />
                </XAxis>
                <YAxis type="number" dataKey="bm" domain={[0, 105]} tick={{ fontSize: 13, fill: "#999" }} stroke="#ddd" tickLine={false}>
                  <Label value="BM / HSC signal (%)" angle={-90} position="insideLeft" offset={8} style={{ fontSize: 14, fill: "#666" }} />
                </YAxis>
                <ReferenceArea x1={0} x2={5} y1={20} y2={105} fill={`${INK}06`} stroke={`${INK}25`} strokeDasharray="4 4" />
                <ReferenceLine y={20} stroke="#999" strokeDasharray="6 3" strokeWidth={1}>
                  <Label value="20% efficacy threshold (Newby 2021)" position="insideTopRight" offset={8} style={{ fontSize: 12, fill: "#999" }} />
                </ReferenceLine>
                <Tooltip content={<ParetoTooltip />} />
                <Scatter data={paretoData.filter(d => d.liver !== null)} shape={<CustomDot />} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 1, marginTop: 32, background: "#e0e0e0", border: "1px solid #e0e0e0" }}>
            {[
              { label: "Ideal zone", desc: "Only Ensoma VLP occupies >20% BM with <5% liver", accent: OCHRE },
              { label: "Design target", desc: "High selectivity at therapeutic potency - the central gap", accent: "#000" },
              { label: "Cargo ≠ delivery", desc: "Tessera 24→40→60%: cargo optimization, then dose escalation", accent: RUST },
            ].map(c => (
              <div key={c.label} style={{ background: "#fff", padding: "20px 24px", borderTop: `3px solid ${c.accent}` }}>
                <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8, color: c.accent }}>{c.label}</div>
                <div style={{ fontSize: 14, color: "#666", lineHeight: 1.5 }}>{c.desc}</div>
              </div>
            ))}
          </div>
          <p style={{ fontSize: 13, color: "#999", marginTop: 16 }}>Tessera liver values estimated from 3:1 BM:liver ratio. Editas 58% NHP omitted - quantitative liver data not disclosed.</p>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 14, color: "#444", lineHeight: 1.6 }}><strong>What the data shows:</strong> Across all published LNP platforms, higher BM delivery correlates with higher liver exposure. The only data point in the ideal zone ({">"}20% BM, {"<"}5% liver) comes from a VLP, not an LNP. No published LNP formulation has achieved both simultaneously.</p>
          </div>
        </div>)}

        {/* COMPARE TAB */}
        {activeTab === "Compare (beta)" && (<div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>Compare: How does your candidate relate to tested formulations?</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 24, lineHeight: 1.6, borderLeft: `3px solid ${OCHRE}`, paddingLeft: 16, background: `${OCHRE}08`, padding: "12px 16px" }}>
            This tool finds the closest tested formulations to your candidate and shows what the model learned about the features you{"'"}re varying. It does not predict delivery outcomes - it provides context from the existing dataset.
          </p>

          {/* Section A: Input Form */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 32, marginBottom: 32 }}>
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 16, color: "#999" }}>Candidate composition</div>
              {[
                { label: "Ionizable lipid mol%", value: cmpIl, set: setCmpIl, min: 15, max: 60, step: 1 },
                { label: "Helper lipid mol%", value: cmpHlPct, set: setCmpHlPct, min: 5, max: 45, step: 1 },
                { label: "Cholesterol mol%", value: cmpChol, set: setCmpChol, min: 15, max: 55, step: 0.5 },
                { label: "PEG mol%", value: cmpPeg, set: setCmpPeg, min: 0.5, max: 5, step: 0.5 },
                { label: "Covalent lipid mol%", value: cmpCv, set: setCmpCv, min: 0, max: 25, step: 1 },
                { label: "Dose (mg/kg)", value: cmpDose, set: setCmpDose, min: 0.1, max: 5, step: 0.1 },
              ].map(s => (
                <div key={s.label} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
                  <div style={{ width: 150, fontSize: 12, color: "#333", textAlign: "right" }}>{s.label}</div>
                  <input type="range" min={s.min} max={s.max} step={s.step} value={s.value}
                    onChange={e => s.set(Number(e.target.value))}
                    style={{ flex: 1, accentColor: INK }} />
                  <div style={{ width: 45, fontSize: 12, fontFamily: NUM, fontWeight: 700, textAlign: "right" }}>{s.value}</div>
                </div>
              ))}

              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
                <div style={{ width: 150, fontSize: 12, color: "#333", textAlign: "right" }}>Helper lipid</div>
                <select value={cmpHl} onChange={e => setCmpHl(e.target.value)}
                  style={{ flex: 1, padding: "4px 8px", fontSize: 12, border: "1px solid #ddd", borderRadius: 3 }}>
                  {["DOTAP","DDAB","DOTMA","EPC","DSPC","DOPE"].map(h => <option key={h} value={h}>{h}</option>)}
                </select>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10 }}>
                <div style={{ width: 150, fontSize: 12, color: "#333", textAlign: "right" }}>Targeting</div>
                <select value={cmpTgt} onChange={e => setCmpTgt(e.target.value)}
                  style={{ flex: 1, padding: "4px 8px", fontSize: 12, border: "1px solid #ddd", borderRadius: 3 }}>
                  {["None","CD117"].map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>

              {/* Mol% sum indicator */}
              {(() => {
                const sum = cmpIl + cmpHlPct + cmpChol + cmpPeg + cmpCv;
                const ok = sum >= 90 && sum <= 110;
                return (
                  <div style={{ marginTop: 12, padding: "8px 12px", fontSize: 12, borderRadius: 3,
                    background: ok ? "#f0fdf4" : "#fef2f2", color: ok ? "#166534" : "#991b1b",
                    border: `1px solid ${ok ? "#bbf7d0" : "#fecaca"}` }}>
                    Mol% sum: <strong>{sum.toFixed(1)}%</strong> {ok ? "" : " - should be ~100%"}
                  </div>
                );
              })()}
            </div>

            {/* Section B: Nearest Neighbors */}
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 16, color: "#999" }}>
                5 nearest tested formulations
              </div>

              {neighbors[0]?.dist > 2.0 && (
                <div style={{ padding: "8px 12px", fontSize: 12, background: "#fef2f2", color: "#991b1b",
                  border: "1px solid #fecaca", borderRadius: 3, marginBottom: 12 }}>
                  Your candidate is far from any tested formulation (distance {neighbors[0]?.dist.toFixed(1)} SD) - comparisons may not be informative.
                </div>
              )}

              {neighbors.map((n, i) => (
                <div key={i} style={{ padding: "12px 16px", marginBottom: 8, border: "1px solid #e0e0e0", borderRadius: 4,
                  borderLeft: `3px solid ${n.cls === "high" ? INK : n.cls === "medium" ? OCHRE : "#ccc"}` }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                    <div>
                      <span style={{ fontSize: 13, fontWeight: 600 }}>{n.id}</span>
                      <span style={{ fontSize: 11, color: "#999", marginLeft: 8 }}>{n.p}</span>
                    </div>
                    <span style={{ fontSize: 11, fontFamily: NUM, color: "#999" }}>d={n.dist.toFixed(2)}</span>
                  </div>
                  <div style={{ fontSize: 11, color: "#666", marginTop: 4 }}>
                    {n.hl} {n.il != null ? `${n.il}% IL` : ""} {n.chol != null ? `· ${n.chol}% chol` : ""} {n.tgt !== "None" && n.tgt ? `· ${n.tgt}` : ""}
                    {n.dose != null ? ` · ${n.dose} mg/kg` : ""}
                  </div>
                  <div style={{ display: "flex", gap: 16, marginTop: 4, fontSize: 11 }}>
                    <span style={{ fontWeight: 600, color: n.cls === "high" ? INK : n.cls === "medium" ? OCHRE : "#999" }}>
                      {n.cls.toUpperCase()}
                    </span>
                    <span style={{ color: "#999" }}>{n.mt}</span>
                  </div>
                  {/* Differences */}
                  {(() => {
                    const diffs = [];
                    if (n.il != null && Math.abs(n.il - cmpIl) > 1) diffs.push(`IL ${cmpIl}% vs ${n.il}%`);
                    if (n.hl !== cmpHl) diffs.push(`${cmpHl} vs ${n.hl}`);
                    if (n.chol != null && Math.abs(n.chol - cmpChol) > 1) diffs.push(`Chol ${cmpChol}% vs ${n.chol}%`);
                    if (n.dose != null && Math.abs(n.dose - cmpDose) > 0.2) diffs.push(`Dose ${cmpDose} vs ${n.dose}`);
                    if (diffs.length === 0) return null;
                    return <div style={{ fontSize: 10, color: RUST, marginTop: 4 }}>Differs: {diffs.join(" · ")}</div>;
                  })()}
                </div>
              ))}

              {/* Neighbor class summary */}
              <div style={{ marginTop: 12, padding: "8px 12px", fontSize: 12, background: "#f8f8f8", borderRadius: 3 }}>
                Of 5 nearest: <strong>{neighbors.filter(n => n.cls === "high").length} high</strong>,{" "}
                <strong>{neighbors.filter(n => n.cls === "medium").length} medium</strong>,{" "}
                <strong>{neighbors.filter(n => n.cls === "low").length} low</strong>
              </div>
            </div>
          </div>

          {/* Section C: Feature Context */}
          <div style={{ marginBottom: 32 }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 16, color: "#999" }}>
              What the model learned about these features
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
              {[
                { key: "il", label: `Ionizable lipid at ${cmpIl}%`, ctx: shapContext.il },
                { key: "chol", label: `Cholesterol at ${cmpChol}%`, ctx: shapContext.chol },
                { key: "dose", label: `Dose at ${cmpDose} mg/kg`, ctx: shapContext.dose },
                ...(cmpHl === "DOTAP" ? [{ key: "dotap", label: "DOTAP helper", ctx: shapContext.dotap }] : []),
                ...(cmpTgt === "CD117" ? [{ key: "cd117", label: "CD117 targeting", ctx: shapContext.cd117 }] : []),
                { key: "helper_pct", label: `Helper at ${cmpHlPct}%`, ctx: shapContext.helper_pct },
              ].map(item => (
                <div key={item.key} style={{ padding: "10px 14px", border: "1px solid #e8e8e8", borderRadius: 4, fontSize: 12 }}>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{item.label}
                    <span style={{ fontWeight: 400, color: "#999", marginLeft: 8 }}>SHAP rank {item.ctx.rank} ({item.ctx.shap})</span>
                  </div>
                  <div style={{ color: "#666", lineHeight: 1.5 }}>{item.ctx.direction}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Takeaway */}
          <div style={{ padding: "20px 24px", borderTop: "1px solid #e0e0e0", fontSize: 12, color: "#666", lineHeight: 1.6 }}>
            <strong>What the data shows:</strong> The 5 nearest labeled rows provide empirical context for your candidate, not a prediction. The model{"'"}s SHAP analysis summarizes feature importance across {validationSummary.evaluatedRows} threshold-comparable labeled rows, but outcomes for untested compositions remain uncertain.
          </div>
        </div>)}

        {/* FORMULATIONS TABLE */}
        {activeTab === "Formulations" && (<div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>Feature Matrix: {stats.rows} Evidence Rows</h2>
          <p style={{ fontSize: 15, color: "#666", marginBottom: 16, lineHeight: 1.6 }}>Click any column header to sort. Filter across all {stats.sources} matrix sources.</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 20 }}>
            {["all", ...new Set(formulations.map(row => row.p))].map(p => (
              <button key={p} onClick={() => setFilterPaper(p)} style={{
                padding: "6px 14px", fontSize: 13, border: filterPaper === p ? "1.5px solid #000" : "1px solid #ddd",
                background: filterPaper === p ? "#000" : "#fff", color: filterPaper === p ? "#fff" : "#666",
                borderRadius: 2, cursor: "pointer", fontFamily: "'DM Sans', sans-serif",
              }}>{p === "all" ? "All papers" : p}</button>
            ))}
          </div>
          <div style={{ overflowX: "auto", border: "1px solid #e0e0e0" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, minWidth: 1120 }}>
              <thead><tr style={{ borderBottom: "2px solid #000" }}>
                <Th col="p" label="Paper" w={80} />
                <Th col="id" label="ID" w={120} />
                <Th col="il" label="IL%" w={50} />
                <Th col="hl" label="Helper" w={70} />
                <Th col="hlPct" label="Helper%" w={55} />
                <Th col="chol" label="Chol%" w={50} />
                <Th col="peg" label="PEG%" w={50} />
                <Th col="cv" label="Cov%" w={50} />
                <Th col="dose" label="Dose" w={50} />
                <Th col="tgt" label="Target" w={60} />
                <Th col="mt" label="Metric" w={70} />
                <Th col="cls" label="HSC Level" w={60} />
                <Th col="recordType" label="Evidence" w={80} />
              </tr></thead>
              <tbody>
                {sortedFormulations.map((r, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #f5f5f5", background: r.cls === "high" ? `${INK}05` : "transparent" }}>
                    <td style={{ padding: "5px 8px", fontSize: 12, color: "#999" }}>{r.p}</td>
                    <td title={r.experiment} style={{ padding: "5px 8px", fontWeight: 500, fontSize: 13 }}>{r.id}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: NUM, fontSize: 12 }}>{r.il ?? "-"}</td>
                    <td style={{ padding: "5px 8px", fontSize: 12 }}>{r.hl}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: NUM, fontSize: 12 }}>{r.hlPct ?? "-"}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: NUM, fontSize: 12 }}>{r.chol ?? "-"}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: NUM, fontSize: 12 }}>{r.peg ?? "-"}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: NUM, fontSize: 12, color: r.cv > 0 ? OCHRE : "#999" }}>{r.cv ?? "-"}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: NUM, fontSize: 12 }}>{r.dose ?? "-"}</td>
                    <td style={{ padding: "5px 8px", fontSize: 12, color: r.tgt !== "None" ? RUST : "#ccc" }}>{r.tgt}</td>
                    <td style={{ padding: "5px 8px", fontSize: 12 }}>{r.mt}</td>
                    <td style={{ padding: "5px 8px" }}>
                      <span style={{ fontSize: 11, fontWeight: 600, padding: "1px 6px", borderRadius: 2,
                        background: r.cls === "high" ? `${INK}15` : r.cls === "medium" ? `${OCHRE}15` : "#f5f5f5",
                        color: r.cls === "high" ? INK : r.cls === "medium" ? OCHRE : "#999" }}>{r.cls || "unlabeled"}{r.boundary ? " *" : ""}</span>
                    </td>
                    <td style={{ padding: "5px 8px", fontSize: 11, color: r.recordType === "partial" ? RUST : "#666" }}>{r.recordType}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p style={{ fontSize: 13, color: "#999", marginTop: 12 }}>Showing {sortedFormulations.length} of {stats.rows} records. Current rule: high ({">"}30% strictly), medium (10-30%), low ({"<"}10%). Four Lian 30% boundary labels are marked *.</p>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 14, color: "#444", lineHeight: 1.6 }}><strong>Evidence scope:</strong> Rows are formulation-experiment evidence units, not guaranteed unique chemical formulations. Screen, detailed, abstract-only, and partial records remain distinguishable in the Evidence column. Null values mean the source did not support a defensible value.</p>
          </div>
        </div>)}

        {/* PEG ARCHITECTURE */}
        {activeTab === "PEG Architecture" && (<div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>PEG Lipid Architecture Determines BM Tropism</h2>
          <p style={{ fontSize: 15, color: "#666", marginBottom: 32, lineHeight: 1.6 }}>
            Within DOTAP formulations from the Kim screen, PEG lipid identity drives a 160-fold divergence in BM delivery.
            Both ALC-0159 and C18PEG2000 have C18 chains - the difference is headgroup and linker architecture.
          </p>
          <div style={{ border: "1px solid #e0e0e0", padding: "24px 16px 16px 8px" }}>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={pegComparison} margin={{ top: 8, right: 30, bottom: 8, left: 20 }}>
                <CartesianGrid stroke="#f0f0f0" vertical={false} />
                <XAxis dataKey="peg" tick={{ fontSize: 13, fill: "#333" }} stroke="#ddd" tickLine={false} />
                <YAxis tick={{ fontSize: 13, fill: "#999" }} stroke="#ddd" tickLine={false}>
                  <Label value="Mean BM barcode (DOTAP only)" angle={-90} position="insideLeft" offset={5} style={{ fontSize: 14, fill: "#666" }} />
                </YAxis>
                <Tooltip contentStyle={{ background: "#fff", border: "1px solid #ccc", fontSize: 14 }} formatter={(v) => [v.toFixed(1), "Mean BM"]} />
                <Bar dataKey="mean" radius={[2, 2, 0, 0]}>
                  {pegComparison.map((e, i) => <Cell key={i} fill={e.peg === "C18PEG2000" ? "#ddd" : e.peg === "ALC-0159" ? INK : "#999"} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          {/* Individual formulation dots */}
          <div style={{ marginTop: 24, display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 1, background: "#e0e0e0", border: "1px solid #e0e0e0" }}>
            {pegComparison.map(pg => (
              <div key={pg.peg} style={{ background: "#fff", padding: "16px 20px" }}>
                <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 8, color: pg.peg === "ALC-0159" ? INK : pg.peg === "C18PEG2000" ? "#aaa" : "#666" }}>{pg.peg}</div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {pg.formulations.map(f => (
                    <span key={f.id} style={{ fontSize: 12, fontFamily: NUM, padding: "2px 6px", background: f.bm > 10 ? `${INK}15` : "#f5f5f5", borderRadius: 2, color: f.bm > 10 ? INK : "#666" }}>
                      {f.id}: {f.bm}
                    </span>
                  ))}
                </div>
                <div style={{ fontSize: 12, color: "#999", marginTop: 6 }}>n={pg.n}, mean={pg.mean.toFixed(1)}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 24, padding: "16px 20px", border: "1px solid #e0e0e0", borderLeft: `3px solid ${INK}` }}>
            <p style={{ fontSize: 14, color: "#444", lineHeight: 1.6 }}>
              <strong>Key finding:</strong> ALC-0159 (C18 chain) enables 18.8x mean BM delivery vs C18PEG2000 (also C18 chain) at 0.3x.
              The PEG effect is also DOTAP-specific: the helper{"×"}PEG interaction matrix shows C18PEG2000 boosts 18:1 EPC (5.9) but abolishes DOTAP (0.3).
            </p>
          </div>
          <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 14, color: "#444", lineHeight: 1.6 }}><strong>What the data shows:</strong> Two PEG lipids sharing the same C18 chain length produce a 160-fold divergence in BM delivery within the same helper lipid context. The effect is also DOTAP-specific - C18PEG2000 boosts BM delivery for 18:1 EPC (5.9) but abolishes it for DOTAP (0.3). Chain length alone does not explain these patterns.</p>
          </div>
        </div>)}

        {/* HEADGROUP */}
        {activeTab === "Headgroup" && (<div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>Helper Lipid Headgroup Determines Organ Tropism</h2>
          <p style={{ fontSize: 15, color: "#666", marginBottom: 32, lineHeight: 1.6 }}>
            Kim screen: 66 LNPs with 4 helper lipids (n=16-18 each). DOTAP enables ~13x higher BM delivery than DDAB (p=0.002), despite both being cationic with C18 chains.
          </p>
          <div style={{ border: "1px solid #e0e0e0", padding: "24px" }}>
            {headgroupData.map(h => (
              <div key={h.helper} style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
                <div style={{ width: 80, fontSize: 14, fontWeight: 600, textAlign: "right", color: h.helper === "DOTAP" ? INK : "#666" }}>{h.helper}</div>
                <div style={{ flex: 1, position: "relative", height: 32 }}>
                  {/* Strip plot of individual values */}
                  {h.values.map((v, i) => (
                    <div key={i} style={{
                      position: "absolute", left: `${Math.min(v / 50 * 100, 100)}%`, top: 8 + (i % 3) * 6,
                      width: 6, height: 6, borderRadius: "50%",
                      background: h.helper === "DOTAP" ? INK : h.helper === "DDAB" ? RUST : "#999",
                      opacity: v > 10 ? 0.9 : 0.5,
                    }} title={`${v}`} />
                  ))}
                  {/* Axis line */}
                  <div style={{ position: "absolute", bottom: 0, left: 0, right: 0, height: 1, background: "#e0e0e0" }} />
                </div>
                <div style={{ width: 100, fontSize: 12, fontFamily: NUM, color: "#999", textAlign: "right" }}>
                  mean={h.mean.toFixed(1)} max={h.max}
                </div>
              </div>
            ))}
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 4, marginTop: 8 }}>
              {[0, 10, 20, 30, 40, 50].map(v => (
                <span key={v} style={{ fontSize: 11, color: "#ccc", width: `${100/6}%`, textAlign: "center" }}>{v}</span>
              ))}
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1, marginTop: 24, background: "#e0e0e0", border: "1px solid #e0e0e0" }}>
            <div style={{ background: "#fff", padding: "16px 20px", borderTop: `3px solid ${INK}` }}>
              <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", color: INK, marginBottom: 4 }}>DOTAP {"→"} BM</div>
              <div style={{ fontSize: 14, color: "#666" }}>Glycerol ester + cationic headgroup. 13.4x fold change over DDAB (Mann-Whitney U=207, p=0.002).</div>
            </div>
            <div style={{ background: "#fff", padding: "16px 20px", borderTop: `3px solid ${RUST}` }}>
              <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", color: RUST, marginBottom: 4 }}>DDAB {"→"} Lung</div>
              <div style={{ fontSize: 14, color: "#666" }}>No glycerol, cationic. Independently identified as lung-enriched in Radmand 2023.</div>
            </div>
          </div>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 14, color: "#444", lineHeight: 1.6 }}><strong>What the data shows:</strong> DOTAP and DDAB are both cationic with C18 chains, yet diverge 13× in BM delivery (p=0.002). The structural difference is the glycerol ester backbone present in DOTAP but absent in DDAB. Radmand 2023 independently identified DDAB as lung-enriched in a separate screen, consistent with the pattern observed here.</p>
          </div>
        </div>)}

        {/* DOSE-RESPONSE */}
        {activeTab === "Dose-Response" && (<div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>Dose-Response: 12{"–"}44{"×"} Potency Gap</h2>
          <p style={{ fontSize: 15, color: "#666", marginBottom: 32, lineHeight: 1.6 }}>
            4PL fits where data permits. Antibody-conjugated systems (Shi, Breda) achieve EC30 below patisiran dose (0.3 mg/kg).
            Kim's untargeted LNP67 requires ~40x higher dose. Note: Shi's Y-axis is DiR uptake (%), not editing - different assay from Breda and Kim.
          </p>
          <div style={{ border: "1px solid #e0e0e0", padding: "24px 12px 12px 4px" }}>
            <ResponsiveContainer width="100%" height={400}>
              <ScatterChart margin={{ top: 16, right: 30, bottom: 24, left: 20 }}>
                <CartesianGrid stroke="#f0f0f0" />
                <XAxis type="number" dataKey="d" domain={[0.01, 5]} scale="log" tick={{ fontSize: 13, fill: "#999" }} stroke="#ddd" tickLine={false} ticks={[0.01, 0.1, 1, 5]}>
                  <Label value="Dose (mg/kg, log scale)" position="bottom" offset={8} style={{ fontSize: 14, fill: "#666" }} />
                </XAxis>
                <YAxis type="number" dataKey="r" domain={[0, 100]} tick={{ fontSize: 13, fill: "#999" }} stroke="#ddd" tickLine={false}>
                  <Label value="HSC efficacy (%)" angle={-90} position="insideLeft" offset={8} style={{ fontSize: 14, fill: "#666" }} />
                </YAxis>
                <ReferenceLine x={0.3} stroke="#999" strokeDasharray="4 4" strokeWidth={0.75}>
                  <Label value="Patisiran dose" position="top" style={{ fontSize: 11, fill: "#999" }} />
                </ReferenceLine>
                <ReferenceLine y={30} stroke="#999" strokeDasharray="4 4" strokeWidth={0.75} />
                {doseResponse.map((sys, i) => (
                  <Scatter key={sys.system} data={sys.points.map(p => ({d: p.d, r: p.r}))} name={sys.system}>
                    {sys.points.map((p, j) => (
                      <Cell key={j} fill={sys.platform === "tLNP" ? RUST : INK} r={5} />
                    ))}
                  </Scatter>
                ))}
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14, marginTop: 24 }}>
            <thead><tr style={{ borderBottom: "2px solid #000" }}>
              <th style={{ padding: "8px 12px 8px 0", textAlign: "left", fontSize: 13, color: "#999", textTransform: "uppercase", letterSpacing: 0.5 }}>System</th>
              <th style={{ padding: "8px 12px", textAlign: "right", fontSize: 13, color: "#999" }}>EC30</th>
              <th style={{ padding: "8px 12px", textAlign: "right", fontSize: 13, color: "#999" }}>EC50</th>
              <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 13, color: "#999" }}>Species</th>
              <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 13, color: "#999" }}>Platform</th>
            </tr></thead>
            <tbody>
              {doseResponse.map((sys, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #f0f0f0" }}>
                  <td style={{ padding: "8px 12px 8px 0", fontWeight: 600 }}>{sys.system}</td>
                  <td style={{ padding: "8px 12px", textAlign: "right", fontFamily: NUM }}>{sys.ec30 ? `${sys.ec30} mg/kg` : "-"}</td>
                  <td style={{ padding: "8px 12px", textAlign: "right", fontFamily: NUM }}>{sys.ec50 ? `${sys.ec50} mg/kg` : "-"}</td>
                  <td style={{ padding: "8px 12px", color: "#666" }}>{sys.species}</td>
                  <td style={{ padding: "8px 12px" }}><span style={{ color: sys.platform === "tLNP" ? RUST : INK, fontWeight: 600, fontSize: 13 }}>{sys.platform}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 14, color: "#444", lineHeight: 1.6 }}><strong>What the data shows:</strong> Antibody-conjugated systems (Shi, Breda) achieve EC30 values 12–44× lower than untargeted LNP67. Shi's EC30 of 0.036 mg/kg falls below the patisiran clinical dose (0.3 mg/kg). Lian's single data point at 0.6 mg/kg → 5.2% editing sits well below the fitted curves for the other systems.</p>
          </div>
        </div>)}

        {/* LIAN HEATMAP */}
        {activeTab === "Lian Heatmap" && (<div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>Lian 2024: 21 Covalent Lipid Formulations {"×"} 14 BM Cell Types</h2>
          <p style={{ fontSize: 15, color: "#666", marginBottom: 24, lineHeight: 1.6 }}>
            tdTomato expression (%) at 0.6 mg/kg Cre mRNA, n=1 screen. Red border = n=3 validated. Sorted by LT-HSC delivery.
          </p>
          <div style={{ overflowX: "auto", border: "1px solid #e0e0e0" }}>
            <table style={{ borderCollapse: "collapse", fontSize: 12, minWidth: 800 }}>
              <thead><tr>
                <th style={{ padding: "4px 8px", fontSize: 11, color: "#999", textAlign: "left", borderBottom: "2px solid #000", position: "sticky", left: 0, background: "#fff", zIndex: 1 }}>ID</th>
                {lianCellTypes.map(ct => (
                  <th key={ct} style={{ padding: "4px 6px", fontSize: 10, color: "#999", textTransform: "uppercase", letterSpacing: 0.3, borderBottom: "2px solid #000", whiteSpace: "nowrap", textAlign: "center", minWidth: 42 }}>
                    {ct.replace("_"," ")}
                  </th>
                ))}
              </tr></thead>
              <tbody>
                {lianFormulations.map((f, fi) => (
                  <tr key={f.id} style={{ borderBottom: "1px solid #f5f5f5" }}>
                    <td style={{ padding: "4px 8px", fontWeight: 600, fontSize: 13, whiteSpace: "nowrap", position: "sticky", left: 0, background: "#fff", zIndex: 1, borderRight: "1px solid #e0e0e0" }}>
                      <span style={{ color: f.validated ? RUST : "#333" }}>{f.id}</span>
                      {f.validated && <span style={{ fontSize: 10, color: RUST, marginLeft: 4 }}>{"✓"}</span>}
                    </td>
                    {f.cells.map((v, ci) => {
                      const intensity = Math.min(v / 66, 1);
                      const bg = v > 40 ? `rgba(43,65,98,${0.15 + intensity * 0.55})` : v > 20 ? `rgba(43,65,98,${intensity * 0.3})` : v > 10 ? `rgba(43,65,98,${intensity * 0.15})` : "#fafafa";
                      const fg = v > 35 ? "#fff" : "#333";
                      return (
                        <td key={ci} style={{ padding: "3px 4px", textAlign: "center", fontFamily: NUM, fontSize: 11, background: bg, color: fg, fontWeight: v > 40 ? 700 : 400 }}>
                          {v}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ display: "flex", gap: 24, marginTop: 16, fontSize: 13, color: "#666" }}>
            <span><span style={{ color: RUST, fontWeight: 600 }}>{"✓"}</span> Validated (n=3): AA11, A8, C6, A13</span>
            <span>Scale: 0% (white) {"→"} 66% (deep blue)</span>
          </div>
          <div style={{ marginTop: 20, padding: "16px 20px", border: "1px solid #e0e0e0", borderLeft: `3px solid ${INK}` }}>
            <p style={{ fontSize: 14, color: "#444", lineHeight: 1.6 }}>
              MPP and CMP show the highest delivery across most formulations (up to 66%). LT-HSC delivery ranges from 13{"–"}40%.
              B cells and monocytes consistently show lowest uptake ({"<"}10%), suggesting corona-mediated selectivity within BM.
            </p>
          </div>
          <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 14, color: "#444", lineHeight: 1.6 }}><strong>What the data shows:</strong> Delivery varies substantially across cell types - MPP and CMP reach up to 66%, while B cells and monocytes stay below 10% across nearly all formulations. The validated lead AA11 shows 45% LT-HSC delivery by tdTomato reporter but 5.2% by Cas9 editing, a pattern consistent with the reporter-to-editing gap observed in other systems.</p>
          </div>
        </div>)}

        {/* FEATURES */}
        {activeTab === "Features" && (<div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>Atlas Model Diagnostics</h2>
          <p style={{ fontSize: 15, color: "#666", marginBottom: 24, lineHeight: 1.6 }}>LightGBM uses {validationSummary.evaluatedRows} labeled, threshold-comparable rows and {stats.modelFeatures} predictor features. Formulation-grouped validation is primary because random row splits leak repeated formulations.</p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(190px, 1fr))", gap: 8, marginBottom: 32 }}>
            {[
              { label: "Row-random 5-fold", value: validationSummary.rowRandom.balancedAccuracy, note: "7-12 overlapping tokens", accent: RUST },
              { label: "Formulation-grouped 5-fold", value: validationSummary.formulationGrouped.balancedAccuracy, note: "0 overlapping tokens", accent: INK },
              { label: "Leave-one-paper-out", value: validationSummary.leaveOnePaperOut.balancedAccuracy, note: `${validationSummary.leaveOnePaperOut.folds} source folds`, accent: OCHRE },
            ].map(metric => (
              <div key={metric.label} style={{ border: "1px solid #e0e0e0", borderTop: `3px solid ${metric.accent}`, padding: "16px 18px" }}>
                <div style={{ fontSize: 12, fontWeight: 600 }}>{metric.label}</div>
                <div style={{ fontSize: 26, fontWeight: 700, fontFamily: NUM, margin: "6px 0 2px" }}>{metric.value.toFixed(4)}</div>
                <div style={{ fontSize: 11, color: "#999" }}>balanced accuracy {"·"} {metric.note}</div>
              </div>
            ))}
          </div>
          <h3 style={{ fontSize: 14, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 12 }}>Mean absolute SHAP values</h3>
          <div style={{ border: "1px solid #e0e0e0", padding: "24px 12px 12px 4px" }}>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={shapData} layout="vertical" margin={{ top: 8, right: 40, bottom: 8, left: 130 }}>
                <CartesianGrid stroke="#f0f0f0" horizontal={false} />
                <XAxis type="number" domain={[0, 1.1]} tick={{ fontSize: 13, fill: "#999" }} stroke="#ddd" tickLine={false}>
                  <Label value="Mean |SHAP value|" position="bottom" offset={0} style={{ fontSize: 14, fill: "#666" }} />
                </XAxis>
                <YAxis type="category" dataKey="feature" tick={{ fontSize: 14, fill: "#333" }} stroke="none" width={130} />
                <Tooltip contentStyle={{ background: "#fff", border: "1px solid #ccc", fontSize: 14 }} formatter={(val) => [val.toFixed(3), "|SHAP|"]} />
                <Bar dataKey="shap" radius={[0, 2, 2, 0]}>
                  {shapData.map((entry, i) => (<Cell key={i} fill={entry.type === "known" ? INK : entry.type === "literature" ? OCHRE : "#d4d4d4"} />))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: "flex", gap: 32, marginTop: 24, fontSize: 14, color: "#666" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ display: "inline-block", width: 12, height: 12, background: INK, borderRadius: 1 }} /> Known SAR</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ display: "inline-block", width: 12, height: 12, background: OCHRE, borderRadius: 1 }} /> Literature-supported</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ display: "inline-block", width: 12, height: 12, background: "#d4d4d4", borderRadius: 1 }} /> Other</span>
          </div>
          <div style={{ marginTop: 32, border: `1px solid ${OCHRE}40`, borderLeft: `3px solid ${OCHRE}`, padding: "20px 24px", background: `${OCHRE}06` }}>
            <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8, color: OCHRE }}>Interpretation boundary</div>
            <p style={{ fontSize: 15, color: "#444", lineHeight: 1.7 }}>Feature importance is descriptive. The matrix is clustered by paper, assay, protocol, and formulation, and ionizable-lipid descriptors cover only {stats.descriptorRows}/{stats.rows} rows. SHAP rank is not evidence of a causal effect.</p>
          </div>
          {/* LOPOCV breakdown */}
          <div style={{ marginTop: 32 }}>
            <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 12 }}>Leave-one-paper-out CV</div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: 1, background: "#e0e0e0", border: "1px solid #e0e0e0" }}>
              {lopocvFolds.map(f => (
                <div key={f.paper} style={{ background: "#fff", padding: "16px 20px", textAlign: "center" }}>
                  <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{f.paper}</div>
                  <div style={{ fontSize: 22, fontWeight: 700, fontFamily: NUM, color: f.lgbm >= 0.5 ? INK : "#999" }}>{f.lgbm.toFixed(2)}</div>
                  <div style={{ fontSize: 12, color: "#999" }}>n={f.n}</div>
                </div>
              ))}
            </div>
            <p style={{ fontSize: 13, color: "#999", marginTop: 8 }}>LightGBM balanced accuracy per source fold. Source-level stress tests can contain only one or two outcome classes.</p>
          </div>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 14, color: "#444", lineHeight: 1.6 }}><strong>What the validation shows:</strong> Row-random performance is optimistic because repeated formulation identities can cross partitions. The formulation-grouped split confines all {validationSummary.formulationTokens} tokens to one fold and is the appropriate within-literature held-out result.</p>
          </div>
        </div>)}

        {/* PAPERS */}
        {activeTab === "Papers" && (<div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>Matrix Sources</h2>
          <p style={{ fontSize: 15, color: "#666", marginBottom: 12, lineHeight: 1.6 }}>{papers.length} sources contribute the {stats.rows} matrix rows. Click a title to view its source record.</p>
          <div style={{ display: "flex", gap: 20, marginBottom: 32, fontSize: 14 }}>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 10, background: INK, display: "inline-block", borderRadius: 1 }} /> Atlas source</span>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <thead><tr style={{ borderBottom: "2px solid #000", textAlign: "left" }}>
              <th style={{ padding: "8px 12px 8px 0", fontWeight: 600, fontSize: 13, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Reference</th>
              <th style={{ padding: "8px 12px", fontWeight: 600, fontSize: 13, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Journal</th>
              <th style={{ padding: "8px 12px", fontWeight: 600, fontSize: 13, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Title</th>
              <th style={{ padding: "8px 12px", fontWeight: 600, fontSize: 13, letterSpacing: 0.5, textTransform: "uppercase", color: "#999", textAlign: "right" }}>Records</th>
              <th style={{ padding: "8px 0 8px 12px", fontWeight: 600, fontSize: 13, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Role</th>
              <th style={{ padding: "8px 0 8px 12px", fontWeight: 600, fontSize: 13, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Status</th>
            </tr></thead>
            <tbody>
              {papers.map((p, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #f0f0f0" }}>
                  <td style={{ padding: "10px 12px 10px 0", fontWeight: 600, whiteSpace: "nowrap", fontSize: 14 }}>{p.id}</td>
                  <td style={{ padding: "10px 12px", color: "#666", whiteSpace: "nowrap" }}>{p.journal}</td>
                  <td style={{ padding: "10px 12px", lineHeight: 1.4 }}>
                    {p.url ? (<a href={p.url} target="_blank" rel="noopener noreferrer" style={{ color: "#333", textDecoration: "underline", textUnderlineOffset: 2, textDecorationColor: "#ccc" }}>{p.title}</a>) : (<span style={{ color: "#666" }}>{p.title}</span>)}
                  </td>
                  <td style={{ padding: "10px 12px", textAlign: "right", fontFamily: NUM }}>{p.records}</td>
                  <td style={{ padding: "10px 0 10px 12px" }}>
                    <span style={{ display: "inline-block", fontSize: 12, fontWeight: 600, letterSpacing: 0.5, padding: "2px 8px", borderRadius: 2,
                      background: `${roleColor(p.role)}10`, color: roleColor(p.role), border: `1px solid ${roleColor(p.role)}30` }}>{p.role}</span>
                  </td>
                  <td style={{ padding: "10px 0 10px 12px", fontSize: 12, color: p.status.includes("partial") ? RUST : "#666" }}>{p.status.replaceAll("_", " ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>)}

        {/* FINDINGS */}
        {activeTab === "Findings" && (<div>
          <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 32 }}>Key Findings</h2>
          {findings.map((f, i) => (
            <div key={i} style={{ marginBottom: 32, paddingBottom: 32, borderBottom: i < findings.length - 1 ? "1px solid #f0f0f0" : "none" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 8 }}>
                <span style={{ fontSize: 15, fontFamily: NUM, fontWeight: 700, color: "#000", minWidth: 24 }}>{String(i + 1).padStart(2, "0")}</span>
                <h3 style={{ fontSize: 17, fontWeight: 600 }}>{f.title}</h3>
              </div>
              <p style={{ fontSize: 15, color: "#555", lineHeight: 1.7, marginLeft: 36 }}>{f.text}</p>
            </div>
          ))}
          <div style={{ marginTop: 48, padding: "32px 0", borderTop: "1px solid #000", display: "flex", justifyContent: "space-between" }}>
            {[
              { n: stats.rows, label: "Evidence rows" },
              { n: stats.sources, label: "Matrix sources" },
              { n: stats.columns, label: "Matrix columns" },
              { n: stats.labeled, label: "Labeled rows" },
            ].map(s => (
              <div key={s.label} style={{ textAlign: "center" }}>
                <div style={{ fontSize: 30, fontWeight: 700, fontFamily: NUM, letterSpacing: -1 }}>{s.n}</div>
                <div style={{ fontSize: 13, color: "#999", marginTop: 4 }}>{s.label}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 14, color: "#444", lineHeight: 1.6 }}><strong>Open evidence:</strong> Two Xue 2022 rows remain partial pending main text. Ramishetti 2020, Zhu 2026, and Dacoba 2025 remain paywalled source stubs and do not contribute matrix rows. Unsupported values stay null.</p>
            <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 1, background: "#e0e0e0", border: "1px solid #e0e0e0" }}>
              <div style={{ background: "#fff", padding: "16px 20px" }}>
                <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 6, color: INK }}>Queryable evidence</div>
                <div style={{ fontSize: 13, color: "#666", lineHeight: 1.5 }}>Screen, detailed, abstract-only, and partial rows remain distinguishable in the explorer.</div>
              </div>
              <div style={{ background: "#fff", padding: "16px 20px" }}>
                <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 6, color: OCHRE }}>Boundary-safe labels</div>
                <div style={{ fontSize: 13, color: "#666", lineHeight: 1.5 }}>The four retained 30% Lian boundary labels can be separated with the marker column.</div>
              </div>
              <div style={{ background: "#fff", padding: "16px 20px" }}>
                <div style={{ fontSize: 13, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 6, color: "#999" }}>Coverage gap</div>
                <div style={{ fontSize: 13, color: "#666", lineHeight: 1.5 }}>Ionizable-lipid descriptors cover 154/333 rows and detailed toxicity covers 13/198 rich records.</div>
              </div>
            </div>
          </div>
        </div>)}
      </main>

      <footer style={{ borderTop: "1px solid #e0e0e0", padding: "24px 48px" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", justifyContent: "space-between" }}>
          <span style={{ fontSize: 13, color: "#999" }}>HSC-LNP Atlas {"·"} Open source</span>
          <a href="https://github.com/tramngo1603/lnp-hsc-atlas" style={{ fontSize: 13, color: "#000", textDecoration: "none", fontFamily: "'DM Mono', monospace" }}>GitHub {"→"}</a>
        </div>
      </footer>
    </div>
  );
}
