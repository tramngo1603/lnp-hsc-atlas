import { useState, useMemo } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, ReferenceLine, ReferenceArea, Label, LineChart, Line } from "recharts";

const INK = "#2B4162";
const RUST = "#A63D40";
const OCHRE = "#B08836";
const platformColor = (p) => p === "VLP" ? OCHRE : p === "tLNP" ? RUST : INK;

const paretoData = [
  { name: "Breda CD117", bm: 55, liver: 76, metric: "editing", platform: "tLNP", species: "Mouse", detail: "Cre editing in LSK, CD117 antibody, 0.25 mg/kg", n: 3 },
  { name: "Kim LNP67", bm: 20.9, liver: 20.1, metric: "reporter", platform: "LNP", species: "Mouse", detail: "aVHH protein expression, 0.5 mg/kg", n: 3 },
  { name: "Kim LNP108", bm: 8.8, liver: 1.6, metric: "reporter", platform: "LNP", species: "Mouse", detail: "Best selectivity in Kim screen (BM:liver = 5.5)", n: 3 },
  { name: "Lian AA11 Cas9", bm: 5.2, liver: 7.5, metric: "editing", platform: "LNP", species: "Mouse", detail: "BCL11A editing, covalent lipid approach, Townes mice", n: 3 },
  { name: "Lian AA11 ABE", bm: 2.4, liver: 3.0, metric: "editing", platform: "LNP", species: "Mouse", detail: "Sickle to Makassar base editing, Townes mice", n: 3 },
  { name: "Ensoma VLP", bm: 31, liver: 0.5, metric: "editing", platform: "VLP", species: "Hum. mouse", detail: "B2M editing, 8 wk, near-zero liver transduction", n: 3 },
  { name: "Tessera 24%", bm: 24, liver: 8, metric: "editing", platform: "tLNP", species: "NHP", detail: "HBB Makassar, single dose, liver estimated", n: null },
  { name: "Tessera 40%", bm: 40, liver: 13.3, metric: "editing", platform: "tLNP", species: "NHP", detail: "Optimized Gene Writer cargo, same LNP platform", n: null },
  { name: "Tessera 60%", bm: 60, liver: 20, metric: "editing", platform: "tLNP", species: "NHP", detail: "Two doses, liver estimated from 3:1 BM:liver ratio", n: null },
  { name: "Kim LNP95", bm: 48, liver: 18.8, metric: "reporter", platform: "LNP", species: "Mouse", detail: "ALC-0159 PEG lipid, highest barcode in screen (30% DOTAP)", n: 1 },
  { name: "Breda IgG control", bm: 19, liver: 78, metric: "editing", platform: "tLNP", species: "Mouse", detail: "Isotype control, liver comparable to CD117 LNP", n: 3 },
  { name: "Kim E2 avg", bm: 5.2, liver: 44, metric: "reporter", platform: "LNP", species: "Mouse", detail: "4-LNP validation average, 0.5 mg/kg", n: 4 },
];

const shapData = [
  { feature: "Ionizable lipid %", shap: 0.97, type: "known" },
  { feature: "CD117 targeting", shap: 0.47, type: "known" },
  { feature: "Chol:helper ratio", shap: 0.42, type: "new" },
  { feature: "Cholesterol %", shap: 0.34, type: "new" },
  { feature: "Dose (mg/kg)", shap: 0.27, type: "known" },
  { feature: "Editing assay", shap: 0.25, type: "other" },
  { feature: "IL molecular weight", shap: 0.24, type: "new" },
  { feature: "DOTAP helper", shap: 0.23, type: "known" },
  { feature: "Helper lipid %", shap: 0.21, type: "known" },
  { feature: "Cationic helper", shap: 0.18, type: "other" },
];

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

const bmGapData = [
  { study: "Radmand 2024", lnps: 196, measured: false },
  { study: "Radmand 2023", lnps: 137, measured: false },
  { study: "Kim 2024", lnps: 128, measured: true },
  { study: "Gentry 2025", lnps: 109, measured: false },
  { study: "Sago 2018", lnps: 160, measured: true },
  { study: "Da Silva Sanchez 2022", lnps: 98, measured: false },
  { study: "Shi 2023", lnps: 37, measured: true },
  { study: "Lian 2024", lnps: 21, measured: true },
  { study: "SORT 2020", lnps: 20, measured: false },
  { study: "Breda 2023", lnps: 14, measured: true },
  { study: "Cullis 2025", lnps: 10, measured: true },
];

const findings = [
  { title: "The potency-selectivity tradeoff", text: "Antibody-conjugated LNPs achieve 12–44× higher potency but deliver 76% of cargo to liver. Untargeted LNPs show better selectivity at lower absolute potency. Observed across all four labs in the dataset." },
  { title: "Cholesterol as a liver predictor", text: "Cholesterol mol% varies from 38–48% across formulations in the dataset. The model identifies this variation as the 3rd–4th most important feature driving organ tropism. Three independent wet-lab studies confirm the mechanism: glycolipid substitution (Gentry 2025), cholesterol removal (Su 2024), and bile acid replacement (Patel 2024) each de-target liver through the cholesterol axis." },
  { title: "PEG architecture, not chain length", text: "C18PEG2000 abolishes BM delivery (0.3 barcode counts). ALC-0159, also C18 chain but different architecture, enables the highest BM delivery in the screen (barcode 48). A 160-fold divergence formally disproving the chain-length hypothesis." },
  { title: "Cargo optimization matters equally", text: "Tessera’s NHP HBB editing improved 24% → 40% through Gene Writer optimization alone — same LNP. A second dose pushed to 60%. The therapeutic outcome is the product of delivery efficiency × editing efficiency." },
  { title: "The 20% therapeutic threshold", text: "Newby et al. (2021) established via secondary transplant that ≥20% sickle-to-Makassar editing rescues SCD in mice. This threshold defines what therapeutically relevant means for the field." },
  { title: "No LNP in the ideal zone", text: "Only Ensoma’s VLP platform (31% editing, ~0% liver) occupies the ideal zone. Whether LNPs can match VLP-level selectivity while retaining manufacturing simplicity remains the central open question." },
];

const papers = [
  { id: "Breda 2023", journal: "Science", title: "In vivo hematopoietic stem cell modification by mRNA delivery", role: "ML training", lnps: 14, url: "https://doi.org/10.1126/science.ade6967" },
  { id: "Shi 2023", journal: "Nano Letters", title: "In vivo RNA delivery to hematopoietic stem and progenitor cells via targeted lipid nanoparticles", role: "ML training", lnps: 37, url: "https://doi.org/10.1021/acs.nanolett.3c00304" },
  { id: "Kim 2024", journal: "Nature Biotechnology", title: "Lipid nanoparticle-mediated mRNA delivery to CD34+ cells in rhesus monkeys", role: "ML training", lnps: 128, url: "https://doi.org/10.1038/s41587-024-02470-2" },
  { id: "Lian 2024", journal: "Nature Nanotechnology", title: "Bone-marrow-homing LNPs for genome editing in diseased and malignant HSCs", role: "ML training", lnps: 21, url: "https://doi.org/10.1038/s41565-024-01680-8" },
  { id: "Kim 2025", journal: "Blood (ASH)", title: "Scalable antibody-free LNP achieves human HSPC-selective mRNA delivery in vivo", role: "Pareto comparator", lnps: null, url: "https://ashpublications.org/blood/article/146/Supplement%201/1067/551288/" },
  { id: "Tessera ASH 2024", journal: "Blood (ASH)", title: "Delivery of Gene Writers in vivo to HSCs and T cells using targeted LNPs", role: "Pareto comparator", lnps: null, url: "https://ashpublications.org/blood/article/144/Supplement%201/2197/532661/" },
  { id: "Tessera ASH 2025", journal: "Blood (ASH)", title: "In vivo RNA delivery by targeted LNPs enables gene editing in HSCs and T cells", role: "Pareto comparator", lnps: null, url: "https://ashpublications.org/blood/article/146/Supplement%201/4318/550528/" },
  { id: "Tessera PR Dec 2025", journal: "Press release", title: "Tessera showcases new preclinical data at 67th ASH Annual Meeting", role: "Pareto comparator", lnps: null, url: "https://www.tesseratherapeutics.com/news/tessera-therapeutics-showcases-new-preclinical-data-demonstrating-progress-of-in-vivo-programs-for-sickle-cell-disease-and-t-cell-therapies-at-the-67th-american-society-of-hematology-annual-meeting" },
  { id: "Tessera ESGCT 2024", journal: "Press release", title: "Tessera presents preclinical data at ESGCT 2024", role: "Pareto comparator", lnps: null, url: "https://www.globenewswire.com/news-release/2024/10/24/2968505/0/en/" },
  { id: "Tessera ASGCT 2025", journal: "Press release", title: "Tessera features preclinical data at ASGCT 28th Annual Meeting", role: "Pareto comparator", lnps: null, url: "https://www.globenewswire.com/news-release/2025/05/17/3083480/0/en/" },
  { id: "Editas EHA 2025", journal: "EHA Congress", title: "Targeted LNP delivery in NHPs enables in vivo HBG1/2 promoter editing", role: "Pareto comparator", lnps: null, url: null },
  { id: "Ensoma 2025", journal: "Nature Biotechnology", title: "In vivo gene editing of human HSPCs using virus-like particles", role: "Pareto comparator", lnps: null, url: null },
  { id: "Newby 2021", journal: "Nature", title: "Base editing of haematopoietic stem cells rescues sickle cell disease in mice", role: "Threshold reference", lnps: null, url: "https://doi.org/10.1038/s41586-021-03609-w" },
  { id: "Cheng 2020 (SORT)", journal: "Nature Nanotechnology", title: "Selective organ targeting (SORT) nanoparticles", role: "Landscape", lnps: 20, url: "https://doi.org/10.1038/s41565-019-0631-3" },
  { id: "Radmand 2024", journal: "PNAS", title: "Cationic cholesterol-dependent LNP delivery to lung stem cells, liver, and heart", role: "Landscape", lnps: 196, url: "https://doi.org/10.1073/pnas.2307801120" },
  { id: "Radmand 2023", journal: "Nano Letters", title: "Transcriptomic response to LNP delivery varies by helper lipid headgroup", role: "Landscape", lnps: 137, url: "https://doi.org/10.1021/acs.nanolett.2c04479" },
  { id: "Gentry 2025", journal: "PNAS", title: "Glycolipid nanoparticles target spleen and detarget liver without charge", role: "Landscape", lnps: 109, url: "https://doi.org/10.1073/pnas.2409569122" },
  { id: "Da Silva Sanchez 2022", journal: "Nano Letters", title: "Universal barcoding predicts in vivo ApoE-independent LNP delivery", role: "Landscape", lnps: 98, url: "https://doi.org/10.1021/acs.nanolett.2c01133" },
  { id: "Sago 2018", journal: "JACS", title: "Nanoparticles that deliver RNA to bone marrow identified by directed evolution", role: "Landscape", lnps: 160, url: "https://doi.org/10.1021/jacs.8b08976" },
  { id: "Loughrey 2025", journal: "Chem. Commun.", title: "The time course of in vivo cellular responses to LNPs", role: "Landscape", lnps: null, url: "https://doi.org/10.1039/D4CC06659F" },
  { id: "Cullis 2025", journal: "Nature Communications", title: "Liposomal lipid nanoparticles for extrahepatic delivery of mRNA", role: "Landscape", lnps: 10, url: "https://doi.org/10.1038/s41467-025-58523-w" },
];
const formulations = [
  {
    "p": "breda '23",
    "id": "CD117/LNP",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "breda '23",
    "id": "CD117/LNP",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "breda '23",
    "id": "CD117/LNP",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.25,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "breda '23",
    "id": "CD117/LNP",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.05,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "breda '23",
    "id": "hCD117/LNP (anti-human CD",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "breda '23",
    "id": "IgG/LNP",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "None",
    "mt": "editing",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "breda '23",
    "id": "IgG/LNP",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.5,
    "peg": 1.5,
    "dose": null,
    "tgt": "None",
    "mt": "editing",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "breda '23",
    "id": "IgG/LNP",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.25,
    "tgt": "None",
    "mt": "editing",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "breda '23",
    "id": "CD117/LNP",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.05,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "kim '24",
    "id": "F1_LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "chol": 47.5,
    "peg": 2.5,
    "dose": 0.5,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "F2_LNP95",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": 0.5,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "F3_LNP108",
    "il": null,
    "hl": "DSPC",
    "chol": null,
    "peg": null,
    "dose": 0.5,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "F4_LP01",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.5,
    "peg": 1.5,
    "dose": 0.5,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "F1_LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "chol": 47.5,
    "peg": 2.5,
    "dose": 0.5,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "F1_LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "chol": 47.5,
    "peg": 2.5,
    "dose": 1.0,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "F1_LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "chol": 47.5,
    "peg": 2.5,
    "dose": 2.0,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "kim '24",
    "id": "F1_LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "chol": 47.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "F1_LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "chol": 47.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "F1_LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "chol": 47.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "F1_LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "chol": 47.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "kim '24",
    "id": "F1_LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "chol": 47.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "kim '24",
    "id": "F1_LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "chol": 47.5,
    "peg": 2.5,
    "dose": 1.0,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "F1_LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "chol": 47.5,
    "peg": 2.5,
    "dose": 1.0,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "shi '23",
    "id": "F5_ALC0315_C14PEG",
    "il": null,
    "hl": "DSPC",
    "chol": null,
    "peg": null,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "reporter",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "reporter",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "F5_ALC0315_C14PEG",
    "il": null,
    "hl": "DSPC",
    "chol": null,
    "peg": null,
    "dose": 0.3,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "F6_ALC0315_C16PEG",
    "il": null,
    "hl": "DSPC",
    "chol": null,
    "peg": null,
    "dose": 0.3,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 0.3,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "PBS_control",
    "il": null,
    "hl": "Unknown",
    "chol": null,
    "peg": null,
    "dose": 0.3,
    "tgt": "None",
    "mt": "editing",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "shi '23",
    "id": "F9_IgG_isotype",
    "il": null,
    "hl": "DSPC",
    "chol": null,
    "peg": null,
    "dose": 1.0,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "shi '23",
    "id": "F10_unconjugated",
    "il": null,
    "hl": "DSPC",
    "chol": null,
    "peg": null,
    "dose": 1.0,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 0.3,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 0.3,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "F7_ALC0315_C18PEG",
    "il": 50.0,
    "hl": "DSPC",
    "chol": 38.0,
    "peg": 1.5,
    "dose": 1.0,
    "tgt": "CD117",
    "mt": "editing",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "shi '23",
    "id": "PBS_control",
    "il": null,
    "hl": "Unknown",
    "chol": null,
    "peg": null,
    "dose": 0.3,
    "tgt": "None",
    "mt": "reporter",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP1",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP5",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP6",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP7",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP9",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP11",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP14",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP17",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP19",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP20",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP21",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP22",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP25",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP27",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP30",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP31",
    "il": null,
    "hl": "DDAB",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP33",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP35",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP38",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP39",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP42",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP44",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP47",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP51",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP53",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP54",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP57",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP59",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP60",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP61",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP62",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP63",
    "il": null,
    "hl": "DOTMA",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP67",
    "il": 35.0,
    "hl": "DOTAP",
    "chol": 47.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "kim '24",
    "id": "LNP68",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP69",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP71",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP73",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP76",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP77",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP79",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP81",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP82",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP84",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP85",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "LNP87",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP89",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "LNP91",
    "il": null,
    "hl": "DOTAP",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "LNP95",
    "il": 50.0,
    "hl": "DOTAP",
    "chol": 17.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "kim '24",
    "id": "LNP98",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP99",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "LNP101",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP102",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "LNP103",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP105",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP107",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "LNP108",
    "il": 45.0,
    "hl": "EPC",
    "chol": 37.5,
    "peg": 2.5,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "high"
  },
  {
    "p": "kim '24",
    "id": "LNP109",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP111",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "LNP113",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "LNP115",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "medium"
  },
  {
    "p": "kim '24",
    "id": "LNP116",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP118",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP122",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP125",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP126",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "kim '24",
    "id": "LNP127",
    "il": null,
    "hl": "EPC",
    "chol": null,
    "peg": null,
    "dose": null,
    "tgt": "None",
    "mt": "barcode",
    "cv": 0,
    "cls": "low"
  },
  {
    "p": "lian '24",
    "id": "Lian_A5",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "medium"
  },
  {
    "p": "lian '24",
    "id": "Lian_A7",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_A8",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_A8",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_A9",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "medium"
  },
  {
    "p": "lian '24",
    "id": "Lian_A10",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_A11_original_discove",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_A12",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_A13",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "medium"
  },
  {
    "p": "lian '24",
    "id": "Lian_A13",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_C6",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_C6",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_C7",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "medium"
  },
  {
    "p": "lian '24",
    "id": "Lian_C8",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_C9",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_C10",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_AT4",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "medium"
  },
  {
    "p": "lian '24",
    "id": "Lian_AT5",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_AT6",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "medium"
  },
  {
    "p": "lian '24",
    "id": "Lian_AT7",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "medium"
  },
  {
    "p": "lian '24",
    "id": "Lian_TC",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "medium"
  },
  {
    "p": "lian '24",
    "id": "Lian_CC",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_AA10",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_AA11",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  },
  {
    "p": "lian '24",
    "id": "Lian_AA11",
    "il": 19.0,
    "hl": "DOPE",
    "chol": 38.1,
    "peg": 3.8,
    "dose": 0.6,
    "tgt": "None",
    "mt": "reporter",
    "cv": 20.0,
    "cls": "high"
  }
];

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

const lopocvFolds = [
  { paper: "Kim '24", n: 80, lgbm: 0.59, xgb: 0.484 },
  { paper: "Lian '24", n: 25, lgbm: 0.5, xgb: 0.5 },
  { paper: "Shi '23", n: 21, lgbm: 0.348, xgb: 0.552 },
  { paper: "Breda '23", n: 9, lgbm: 0.5, xgb: 0.0 },
];

const roleColor = (r) => r === "ML training" ? INK : r === "Pareto comparator" ? RUST : r === "Threshold reference" ? OCHRE : "#999";

const ParetoTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  const c = platformColor(d.platform);
  return (
    <div style={{ background: "#fff", border: `1.5px solid ${c}`, padding: "12px 16px", maxWidth: 280, fontSize: 12, lineHeight: 1.5 }}>
      <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 4, color: c }}>{d.name}</div>
      <div style={{ color: "#666", marginBottom: 8 }}>{d.detail}</div>
      <div style={{ display: "flex", gap: 16 }}>
        <span>BM: <strong>{d.bm}%</strong></span>
        <span>Liver: <strong>{d.liver !== null ? `${d.liver}%` : "N/R"}</strong></span>
      </div>
      <div style={{ color: "#999", marginTop: 4, fontSize: 11 }}>
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

const tabs = ["Pareto","Formulations","PEG Architecture","Headgroup","Dose-Response","Lian Heatmap","Features","Papers","Findings"];
const NUM = "'Space Mono', 'Courier New', monospace";

export default function Explorer() {
  const [activeTab, setActiveTab] = useState("Pareto");
  const [sortCol, setSortCol] = useState("p");
  const [sortDir, setSortDir] = useState(1);
  const [filterPaper, setFilterPaper] = useState("all");

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
    <th onClick={() => handleSort(col)} style={{ padding: "6px 8px", fontWeight: 600, fontSize: 10, letterSpacing: 0.5, textTransform: "uppercase", color: "#999", cursor: "pointer", width: w, textAlign: typeof (formulations[0]||{})[col] === "number" ? "right" : "left", userSelect: "none", whiteSpace: "nowrap" }}>
      {label}{sortCol === col ? (sortDir === 1 ? " ▲" : " ▼") : ""}
    </th>
  );

  return (
    <div style={{ background: "#fff", minHeight: "100vh", color: "#000", fontFamily: "'DM Sans', -apple-system, sans-serif" }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Space+Mono:wght@400;700&display=swap');*{box-sizing:border-box;margin:0;padding:0;}`}</style>

      <header style={{ padding: "48px 48px 40px", borderBottom: "1px solid #000" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <p style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#999", marginBottom: 16, fontFamily: "'DM Mono', monospace" }}>HSC-LNP Atlas</p>
          <h1 style={{ fontSize: 32, fontWeight: 300, lineHeight: 1.3, letterSpacing: -0.5 }}>
            Potency–Selectivity Tradeoff in<br /><span style={{ fontWeight: 700 }}>HSC-Targeted LNP Delivery</span>
          </h1>
          <p style={{ fontSize: 13, color: "#666", marginTop: 16 }}>135 formulations · 4 labs · 21 papers reviewed</p>
          <p style={{ fontSize: 12, color: "#999", marginTop: 4 }}>Tram Ngo · <a href="https://github.com/tramngo1603/lnp-hsc-atlas" style={{ color: "#000", textDecoration: "underline", textUnderlineOffset: 2 }}>github.com/tramngo1603/lnp-hsc-atlas</a></p>
        </div>
      </header>

      <nav style={{ borderBottom: "1px solid #e0e0e0", position: "sticky", top: 0, background: "#fff", zIndex: 10 }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", padding: "0 48px", overflowX: "auto" }}>
          {tabs.map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{
              background: "none", border: "none", cursor: "pointer", whiteSpace: "nowrap",
              padding: "14px 16px", fontSize: 11, fontWeight: activeTab === tab ? 600 : 400,
              color: activeTab === tab ? "#000" : "#999",
              borderBottom: activeTab === tab ? "2px solid #000" : "2px solid transparent",
              fontFamily: "'DM Sans', sans-serif", letterSpacing: 0.3,
            }}>{tab}</button>
          ))}
        </div>
      </nav>

      <main style={{ maxWidth: 1100, margin: "0 auto", padding: "40px 48px 80px" }}>

        {/* PARETO */}
        {activeTab === "Pareto" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>BM Delivery vs Liver Off-Target</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 12, lineHeight: 1.6 }}>
            <span style={{ color: INK, fontWeight: 600 }}>{"●"} Untargeted LNP</span>{" · "}
            <span style={{ color: RUST, fontWeight: 600 }}>{"▲"} Targeted LNP</span>{" · "}
            <span style={{ color: OCHRE, fontWeight: 600 }}>{"■"} VLP</span>
            {" — Filled = editing. Open = reporter."}
          </p>
          <p style={{ fontSize: 12, color: "#999", marginBottom: 32 }}>Hover any point for details. Shaded region = ideal zone ({">"}20% BM, {"<"}5% liver).</p>
          <div style={{ border: "1px solid #e0e0e0", padding: "24px 12px 12px 4px" }}>
            <ResponsiveContainer width="100%" height={500}>
              <ScatterChart margin={{ top: 20, right: 40, bottom: 32, left: 24 }}>
                <CartesianGrid stroke="#f0f0f0" />
                <XAxis type="number" dataKey="liver" domain={[0, 100]} tick={{ fontSize: 11, fill: "#999" }} stroke="#ddd" tickLine={false}>
                  <Label value="Liver signal (%)" position="bottom" offset={8} style={{ fontSize: 12, fill: "#666" }} />
                </XAxis>
                <YAxis type="number" dataKey="bm" domain={[0, 105]} tick={{ fontSize: 11, fill: "#999" }} stroke="#ddd" tickLine={false}>
                  <Label value="BM / HSC signal (%)" angle={-90} position="insideLeft" offset={8} style={{ fontSize: 12, fill: "#666" }} />
                </YAxis>
                <ReferenceArea x1={0} x2={5} y1={20} y2={105} fill={`${INK}06`} stroke={`${INK}25`} strokeDasharray="4 4" />
                <ReferenceLine y={20} stroke="#999" strokeDasharray="6 3" strokeWidth={1}>
                  <Label value="20% efficacy threshold (Newby 2021)" position="insideTopRight" offset={8} style={{ fontSize: 10, fill: "#999" }} />
                </ReferenceLine>
                <Tooltip content={<ParetoTooltip />} />
                <Scatter data={paretoData.filter(d => d.liver !== null)} shape={<CustomDot />} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 1, marginTop: 32, background: "#e0e0e0", border: "1px solid #e0e0e0" }}>
            {[
              { label: "Ideal zone", desc: "Only Ensoma VLP occupies >20% BM with <5% liver", accent: OCHRE },
              { label: "Design target", desc: "High selectivity at therapeutic potency — the central gap", accent: "#000" },
              { label: "Cargo ≠ delivery", desc: "Tessera 24→40→60%: cargo optimization, then dose escalation", accent: RUST },
            ].map(c => (
              <div key={c.label} style={{ background: "#fff", padding: "20px 24px", borderTop: `3px solid ${c.accent}` }}>
                <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8, color: c.accent }}>{c.label}</div>
                <div style={{ fontSize: 12, color: "#666", lineHeight: 1.5 }}>{c.desc}</div>
              </div>
            ))}
          </div>
          <p style={{ fontSize: 11, color: "#999", marginTop: 16 }}>Tessera liver values estimated from 3:1 BM:liver ratio. Editas 58% NHP omitted — quantitative liver data not disclosed.</p>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}><strong>What the data shows:</strong> Across all published LNP platforms, higher BM delivery correlates with higher liver exposure. The only data point in the ideal zone ({">"}20% BM, {"<"}5% liver) comes from a VLP, not an LNP. No published LNP formulation has achieved both simultaneously.</p>
          </div>
        </div>)}

        {/* FORMULATIONS TABLE */}
        {activeTab === "Formulations" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Feature Matrix: 135 Formulations</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 16, lineHeight: 1.6 }}>Click any column header to sort. Filter by paper below.</p>
          <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
            {["all","breda '23","shi '23","kim '24","lian '24"].map(p => (
              <button key={p} onClick={() => setFilterPaper(p)} style={{
                padding: "6px 14px", fontSize: 11, border: filterPaper === p ? "1.5px solid #000" : "1px solid #ddd",
                background: filterPaper === p ? "#000" : "#fff", color: filterPaper === p ? "#fff" : "#666",
                borderRadius: 2, cursor: "pointer", fontFamily: "'DM Sans', sans-serif",
              }}>{p === "all" ? "All papers" : p}</button>
            ))}
          </div>
          <div style={{ overflowX: "auto", border: "1px solid #e0e0e0" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11, minWidth: 900 }}>
              <thead><tr style={{ borderBottom: "2px solid #000" }}>
                <Th col="p" label="Paper" w={80} />
                <Th col="id" label="ID" w={120} />
                <Th col="il" label="IL%" w={50} />
                <Th col="hl" label="Helper" w={70} />
                <Th col="chol" label="Chol%" w={50} />
                <Th col="peg" label="PEG%" w={50} />
                <Th col="cv" label="Cov%" w={50} />
                <Th col="dose" label="Dose" w={50} />
                <Th col="tgt" label="Target" w={60} />
                <Th col="mt" label="Metric" w={70} />
                <Th col="cls" label="HSC Level" w={60} />
              </tr></thead>
              <tbody>
                {sortedFormulations.map((r, i) => (
                  <tr key={i} style={{ borderBottom: "1px solid #f5f5f5", background: r.cls === "high" ? `${INK}05` : "transparent" }}>
                    <td style={{ padding: "5px 8px", fontSize: 10, color: "#999" }}>{r.p}</td>
                    <td style={{ padding: "5px 8px", fontWeight: 500, fontSize: 11 }}>{r.id}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: NUM, fontSize: 10 }}>{r.il ?? "—"}</td>
                    <td style={{ padding: "5px 8px", fontSize: 10 }}>{r.hl}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: NUM, fontSize: 10 }}>{r.chol ?? "—"}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: NUM, fontSize: 10 }}>{r.peg ?? "—"}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: NUM, fontSize: 10, color: r.cv > 0 ? OCHRE : "#ccc" }}>{r.cv || "—"}</td>
                    <td style={{ padding: "5px 8px", textAlign: "right", fontFamily: NUM, fontSize: 10 }}>{r.dose ?? "—"}</td>
                    <td style={{ padding: "5px 8px", fontSize: 10, color: r.tgt !== "None" ? RUST : "#ccc" }}>{r.tgt}</td>
                    <td style={{ padding: "5px 8px", fontSize: 10 }}>{r.mt}</td>
                    <td style={{ padding: "5px 8px" }}>
                      <span style={{ fontSize: 9, fontWeight: 600, padding: "1px 6px", borderRadius: 2,
                        background: r.cls === "high" ? `${INK}15` : r.cls === "medium" ? `${OCHRE}15` : "#f5f5f5",
                        color: r.cls === "high" ? INK : r.cls === "medium" ? OCHRE : "#999" }}>{r.cls}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p style={{ fontSize: 11, color: "#999", marginTop: 12 }}>Showing {sortedFormulations.length} of 135 records. HSC Level: high ({">"}30%), medium (10–30%), low ({"<"}10%) BM delivery.</p>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            {filterPaper === "all" && (
              <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}><strong>What the data shows:</strong> Cholesterol mol% ranges from 38–48% across the dataset. DOTAP-containing formulations are overrepresented in the "high" HSC delivery class. Lian's 25 records are the only ones with a non-zero covalent lipid component, introducing a formulation axis not present in the other three labs.</p>
            )}
            {filterPaper === "breda '23" && (
              <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}><strong>Breda 2023 (9 records):</strong> All formulations use the same base LNP (ALC-0315 / DSPC / 38.5% cholesterol) with CD117 antibody conjugation. The variation comes from dose (0.05–0.25 mg/kg) and antibody clone (CD117 vs IgG isotype). Liver editing (~76%) is comparable between CD117 and isotype control — antibody targeting adds BM delivery without subtracting liver.</p>
            )}
            {filterPaper === "shi '23" && (
              <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}><strong>Shi 2023 (21 records):</strong> Systematic optimization of PEG lipid, ionizable lipid, and antibody clone for CD117-targeted delivery. The key finding: switching from C14-PEG to C18-PEG (DSG-PEG2000) improved HSPC uptake ~3×. Multiple ionizable lipids tested (ALC-0315, SM-102, cKK-E12, DLin-MC3-DMA, Lipid 5), demonstrating the system is ionizable-lipid-agnostic.</p>
            )}
            {filterPaper === "kim '24" && (
              <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}><strong>Kim 2024 (80 records):</strong> 128-LNP barcoded screen using proprietary PPZ-A10 ionizable lipid (SMILES unknown). 4 helper lipids × 4 IL mol% × 2 PEG types × 4 PEG concentrations. 80 of 128 had classifiable BM delivery. DOTAP + ALC-0159 formulations dominate the "high" class. This is the largest single systematic screen of BM-homing LNPs published to date.</p>
            )}
            {filterPaper === "lian '24" && (
              <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}><strong>Lian 2024 (25 records):</strong> 21 covalent lipid/crosslinker formulations at 20 mol% as a 5th component, plus 4 validated leads. All use 5A2-SC8 ionizable lipid (known SMILES — the only bridge to external databases). Cholesterol reduced to 38.1% to accommodate the 5th component. This is the dataset that elevated cholesterol to SHAP rank 3–4.</p>
            )}
          </div>
        </div>)}

        {/* PEG ARCHITECTURE */}
        {activeTab === "PEG Architecture" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>PEG Lipid Architecture Determines BM Tropism</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 32, lineHeight: 1.6 }}>
            Within DOTAP formulations from the Kim screen, PEG lipid identity drives a 160-fold divergence in BM delivery.
            Both ALC-0159 and C18PEG2000 have C18 chains — the difference is headgroup and linker architecture.
          </p>
          <div style={{ border: "1px solid #e0e0e0", padding: "24px 16px 16px 8px" }}>
            <ResponsiveContainer width="100%" height={350}>
              <BarChart data={pegComparison} margin={{ top: 8, right: 30, bottom: 8, left: 20 }}>
                <CartesianGrid stroke="#f0f0f0" vertical={false} />
                <XAxis dataKey="peg" tick={{ fontSize: 11, fill: "#333" }} stroke="#ddd" tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#999" }} stroke="#ddd" tickLine={false}>
                  <Label value="Mean BM barcode (DOTAP only)" angle={-90} position="insideLeft" offset={5} style={{ fontSize: 12, fill: "#666" }} />
                </YAxis>
                <Tooltip contentStyle={{ background: "#fff", border: "1px solid #ccc", fontSize: 12 }} formatter={(v) => [v.toFixed(1), "Mean BM"]} />
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
                <div style={{ fontSize: 11, fontWeight: 700, marginBottom: 8, color: pg.peg === "ALC-0159" ? INK : pg.peg === "C18PEG2000" ? "#aaa" : "#666" }}>{pg.peg}</div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                  {pg.formulations.map(f => (
                    <span key={f.id} style={{ fontSize: 10, fontFamily: NUM, padding: "2px 6px", background: f.bm > 10 ? `${INK}15` : "#f5f5f5", borderRadius: 2, color: f.bm > 10 ? INK : "#666" }}>
                      {f.id}: {f.bm}
                    </span>
                  ))}
                </div>
                <div style={{ fontSize: 10, color: "#999", marginTop: 6 }}>n={pg.n}, mean={pg.mean.toFixed(1)}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 24, padding: "16px 20px", border: "1px solid #e0e0e0", borderLeft: `3px solid ${INK}` }}>
            <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}>
              <strong>Key finding:</strong> ALC-0159 (C18 chain) enables 18.8x mean BM delivery vs C18PEG2000 (also C18 chain) at 0.3x.
              The PEG effect is also DOTAP-specific: the helper{"×"}PEG interaction matrix shows C18PEG2000 boosts 18:1 EPC (5.9) but abolishes DOTAP (0.3).
            </p>
          </div>
          <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}><strong>What the data shows:</strong> Two PEG lipids sharing the same C18 chain length produce a 160-fold divergence in BM delivery within the same helper lipid context. The effect is also DOTAP-specific — C18PEG2000 boosts BM delivery for 18:1 EPC (5.9) but abolishes it for DOTAP (0.3). Chain length alone does not explain these patterns.</p>
          </div>
        </div>)}

        {/* HEADGROUP */}
        {activeTab === "Headgroup" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Helper Lipid Headgroup Determines Organ Tropism</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 32, lineHeight: 1.6 }}>
            Kim screen: 66 LNPs with 4 helper lipids (n=16-18 each). DOTAP enables ~13x higher BM delivery than DDAB (p=0.002), despite both being cationic with C18 chains.
          </p>
          <div style={{ border: "1px solid #e0e0e0", padding: "24px" }}>
            {headgroupData.map(h => (
              <div key={h.helper} style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 20 }}>
                <div style={{ width: 80, fontSize: 12, fontWeight: 600, textAlign: "right", color: h.helper === "DOTAP" ? INK : "#666" }}>{h.helper}</div>
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
                <div style={{ width: 100, fontSize: 10, fontFamily: NUM, color: "#999", textAlign: "right" }}>
                  mean={h.mean.toFixed(1)} max={h.max}
                </div>
              </div>
            ))}
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 4, marginTop: 8 }}>
              {[0, 10, 20, 30, 40, 50].map(v => (
                <span key={v} style={{ fontSize: 9, color: "#ccc", width: `${100/6}%`, textAlign: "center" }}>{v}</span>
              ))}
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 1, marginTop: 24, background: "#e0e0e0", border: "1px solid #e0e0e0" }}>
            <div style={{ background: "#fff", padding: "16px 20px", borderTop: `3px solid ${INK}` }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", color: INK, marginBottom: 4 }}>DOTAP {"→"} BM</div>
              <div style={{ fontSize: 12, color: "#666" }}>Glycerol ester + cationic headgroup. 13.4x fold change over DDAB (Mann-Whitney U=207, p=0.002).</div>
            </div>
            <div style={{ background: "#fff", padding: "16px 20px", borderTop: `3px solid ${RUST}` }}>
              <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", color: RUST, marginBottom: 4 }}>DDAB {"→"} Lung</div>
              <div style={{ fontSize: 12, color: "#666" }}>No glycerol, cationic. Independently identified as lung-enriched in Radmand 2023.</div>
            </div>
          </div>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}><strong>What the data shows:</strong> DOTAP and DDAB are both cationic with C18 chains, yet diverge 13× in BM delivery (p=0.002). The structural difference is the glycerol ester backbone present in DOTAP but absent in DDAB. Radmand 2023 independently identified DDAB as lung-enriched in a separate screen, consistent with the pattern observed here.</p>
          </div>
        </div>)}

        {/* DOSE-RESPONSE */}
        {activeTab === "Dose-Response" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Dose-Response: 12{"–"}44{"×"} Potency Gap</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 32, lineHeight: 1.6 }}>
            4PL fits where data permits. Antibody-conjugated systems (Shi, Breda) achieve EC30 below patisiran dose (0.3 mg/kg).
            Kim's untargeted LNP67 requires ~40x higher dose. Note: Shi's Y-axis is DiR uptake (%), not editing — different assay from Breda and Kim.
          </p>
          <div style={{ border: "1px solid #e0e0e0", padding: "24px 12px 12px 4px" }}>
            <ResponsiveContainer width="100%" height={400}>
              <ScatterChart margin={{ top: 16, right: 30, bottom: 24, left: 20 }}>
                <CartesianGrid stroke="#f0f0f0" />
                <XAxis type="number" dataKey="d" domain={[0.01, 5]} scale="log" tick={{ fontSize: 11, fill: "#999" }} stroke="#ddd" tickLine={false} ticks={[0.01, 0.1, 1, 5]}>
                  <Label value="Dose (mg/kg, log scale)" position="bottom" offset={8} style={{ fontSize: 12, fill: "#666" }} />
                </XAxis>
                <YAxis type="number" dataKey="r" domain={[0, 100]} tick={{ fontSize: 11, fill: "#999" }} stroke="#ddd" tickLine={false}>
                  <Label value="HSC efficacy (%)" angle={-90} position="insideLeft" offset={8} style={{ fontSize: 12, fill: "#666" }} />
                </YAxis>
                <ReferenceLine x={0.3} stroke="#999" strokeDasharray="4 4" strokeWidth={0.75}>
                  <Label value="Patisiran dose" position="top" style={{ fontSize: 9, fill: "#999" }} />
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
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12, marginTop: 24 }}>
            <thead><tr style={{ borderBottom: "2px solid #000" }}>
              <th style={{ padding: "8px 12px 8px 0", textAlign: "left", fontSize: 11, color: "#999", textTransform: "uppercase", letterSpacing: 0.5 }}>System</th>
              <th style={{ padding: "8px 12px", textAlign: "right", fontSize: 11, color: "#999" }}>EC30</th>
              <th style={{ padding: "8px 12px", textAlign: "right", fontSize: 11, color: "#999" }}>EC50</th>
              <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 11, color: "#999" }}>Species</th>
              <th style={{ padding: "8px 12px", textAlign: "left", fontSize: 11, color: "#999" }}>Platform</th>
            </tr></thead>
            <tbody>
              {doseResponse.map((sys, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #f0f0f0" }}>
                  <td style={{ padding: "8px 12px 8px 0", fontWeight: 600 }}>{sys.system}</td>
                  <td style={{ padding: "8px 12px", textAlign: "right", fontFamily: NUM }}>{sys.ec30 ? `${sys.ec30} mg/kg` : "—"}</td>
                  <td style={{ padding: "8px 12px", textAlign: "right", fontFamily: NUM }}>{sys.ec50 ? `${sys.ec50} mg/kg` : "—"}</td>
                  <td style={{ padding: "8px 12px", color: "#666" }}>{sys.species}</td>
                  <td style={{ padding: "8px 12px" }}><span style={{ color: sys.platform === "tLNP" ? RUST : INK, fontWeight: 600, fontSize: 11 }}>{sys.platform}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}><strong>What the data shows:</strong> Antibody-conjugated systems (Shi, Breda) achieve EC30 values 12–44× lower than untargeted LNP67. Shi's EC30 of 0.036 mg/kg falls below the patisiran clinical dose (0.3 mg/kg). Lian's single data point at 0.6 mg/kg → 5.2% editing sits well below the fitted curves for the other systems.</p>
          </div>
        </div>)}

        {/* LIAN HEATMAP */}
        {activeTab === "Lian Heatmap" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Lian 2024: 21 Covalent Lipid Formulations {"×"} 14 BM Cell Types</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 24, lineHeight: 1.6 }}>
            tdTomato expression (%) at 0.6 mg/kg Cre mRNA, n=1 screen. Red border = n=3 validated. Sorted by LT-HSC delivery.
          </p>
          <div style={{ overflowX: "auto", border: "1px solid #e0e0e0" }}>
            <table style={{ borderCollapse: "collapse", fontSize: 10, minWidth: 800 }}>
              <thead><tr>
                <th style={{ padding: "4px 8px", fontSize: 9, color: "#999", textAlign: "left", borderBottom: "2px solid #000", position: "sticky", left: 0, background: "#fff", zIndex: 1 }}>ID</th>
                {lianCellTypes.map(ct => (
                  <th key={ct} style={{ padding: "4px 6px", fontSize: 8, color: "#999", textTransform: "uppercase", letterSpacing: 0.3, borderBottom: "2px solid #000", whiteSpace: "nowrap", textAlign: "center", minWidth: 42 }}>
                    {ct.replace("_"," ")}
                  </th>
                ))}
              </tr></thead>
              <tbody>
                {lianFormulations.map((f, fi) => (
                  <tr key={f.id} style={{ borderBottom: "1px solid #f5f5f5" }}>
                    <td style={{ padding: "4px 8px", fontWeight: 600, fontSize: 11, whiteSpace: "nowrap", position: "sticky", left: 0, background: "#fff", zIndex: 1, borderRight: "1px solid #e0e0e0" }}>
                      <span style={{ color: f.validated ? RUST : "#333" }}>{f.id}</span>
                      {f.validated && <span style={{ fontSize: 8, color: RUST, marginLeft: 4 }}>{"✓"}</span>}
                    </td>
                    {f.cells.map((v, ci) => {
                      const intensity = Math.min(v / 66, 1);
                      const bg = v > 40 ? `rgba(43,65,98,${0.15 + intensity * 0.55})` : v > 20 ? `rgba(43,65,98,${intensity * 0.3})` : v > 10 ? `rgba(43,65,98,${intensity * 0.15})` : "#fafafa";
                      const fg = v > 35 ? "#fff" : "#333";
                      return (
                        <td key={ci} style={{ padding: "3px 4px", textAlign: "center", fontFamily: NUM, fontSize: 9, background: bg, color: fg, fontWeight: v > 40 ? 700 : 400 }}>
                          {v}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ display: "flex", gap: 24, marginTop: 16, fontSize: 11, color: "#666" }}>
            <span><span style={{ color: RUST, fontWeight: 600 }}>{"✓"}</span> Validated (n=3): AA11, A8, C6, A13</span>
            <span>Scale: 0% (white) {"→"} 66% (deep blue)</span>
          </div>
          <div style={{ marginTop: 20, padding: "16px 20px", border: "1px solid #e0e0e0", borderLeft: `3px solid ${INK}` }}>
            <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}>
              MPP and CMP show the highest delivery across most formulations (up to 66%). LT-HSC delivery ranges from 13{"–"}40%.
              B cells and monocytes consistently show lowest uptake ({"<"}10%), suggesting corona-mediated selectivity within BM.
            </p>
          </div>
          <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}><strong>What the data shows:</strong> Delivery varies substantially across cell types — MPP and CMP reach up to 66%, while B cells and monocytes stay below 10% across nearly all formulations. The validated lead AA11 shows 45% LT-HSC delivery by tdTomato reporter but 5.2% by Cas9 editing, a pattern consistent with the reporter-to-editing gap observed in other systems.</p>
          </div>
        </div>)}

        {/* FEATURES */}
        {activeTab === "Features" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Feature Importance</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 32, lineHeight: 1.6 }}>LightGBM, leave-one-paper-out CV, balanced accuracy 0.484. All five known SARs recovered in the top 9 features with expected directional effects.</p>
          <div style={{ border: "1px solid #e0e0e0", padding: "24px 12px 12px 4px" }}>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={shapData} layout="vertical" margin={{ top: 8, right: 40, bottom: 8, left: 130 }}>
                <CartesianGrid stroke="#f0f0f0" horizontal={false} />
                <XAxis type="number" domain={[0, 1.1]} tick={{ fontSize: 11, fill: "#999" }} stroke="#ddd" tickLine={false}>
                  <Label value="Mean |SHAP value|" position="bottom" offset={0} style={{ fontSize: 12, fill: "#666" }} />
                </XAxis>
                <YAxis type="category" dataKey="feature" tick={{ fontSize: 12, fill: "#333" }} stroke="none" width={130} />
                <Tooltip contentStyle={{ background: "#fff", border: "1px solid #ccc", fontSize: 12 }} formatter={(val) => [val.toFixed(3), "|SHAP|"]} />
                <Bar dataKey="shap" radius={[0, 2, 2, 0]}>
                  {shapData.map((entry, i) => (<Cell key={i} fill={entry.type === "known" ? INK : entry.type === "new" ? OCHRE : "#d4d4d4"} />))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: "flex", gap: 32, marginTop: 24, fontSize: 12, color: "#666" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ display: "inline-block", width: 12, height: 12, background: INK, borderRadius: 1 }} /> Known SAR</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ display: "inline-block", width: 12, height: 12, background: OCHRE, borderRadius: 1 }} /> Newly significant</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ display: "inline-block", width: 12, height: 12, background: "#d4d4d4", borderRadius: 1 }} /> Other</span>
          </div>
          <div style={{ marginTop: 32, border: `1px solid ${OCHRE}40`, borderLeft: `3px solid ${OCHRE}`, padding: "20px 24px", background: `${OCHRE}06` }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8, color: OCHRE }}>Why cholesterol ranks 3rd{"–"}4th</div>
            <p style={{ fontSize: 13, color: "#444", lineHeight: 1.7 }}>Cholesterol mol% varies from 38{"–"}48% across formulations. Formulations at the lower end use a 5th lipid component that proportionally displaces cholesterol, creating variation the model can learn from. Three independent wet-lab studies confirm the mechanism through the cholesterol axis.</p>
          </div>
          {/* LOPOCV breakdown */}
          <div style={{ marginTop: 32 }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 12 }}>Leave-one-paper-out CV</div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 1, background: "#e0e0e0", border: "1px solid #e0e0e0" }}>
              {lopocvFolds.map(f => (
                <div key={f.paper} style={{ background: "#fff", padding: "16px 20px", textAlign: "center" }}>
                  <div style={{ fontSize: 11, fontWeight: 600, marginBottom: 4 }}>{f.paper}</div>
                  <div style={{ fontSize: 20, fontWeight: 700, fontFamily: NUM, color: f.lgbm >= 0.5 ? INK : "#999" }}>{f.lgbm.toFixed(2)}</div>
                  <div style={{ fontSize: 10, color: "#999" }}>n={f.n}</div>
                </div>
              ))}
            </div>
            <p style={{ fontSize: 11, color: "#999", marginTop: 8 }}>LightGBM balanced accuracy per fold. XGBoost collapses on the 9-row Breda fold (BA=0.0).</p>
          </div>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}><strong>What the data shows:</strong> All 5 previously identified structure-activity relationships appear in the top 9 features with expected directional effects. Cholesterol-related features rank 3rd–4th, consistent with independent wet-lab findings from three other groups. Per-fold accuracy ranges from 0.35 (Shi) to 0.59 (Kim), reflecting variation in fold size and class balance. Note: the model predicts the "high" delivery class most accurately; "medium" and "low" classifications are less reliable and should be interpreted with caution.</p>
          </div>
        </div>)}

        {/* PAPERS */}
        {activeTab === "Papers" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Annotated Papers</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 12, lineHeight: 1.6 }}>21 papers curated for the atlas. Click any title to view the source.</p>
          <div style={{ display: "flex", gap: 20, marginBottom: 32, fontSize: 12 }}>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 10, background: INK, display: "inline-block", borderRadius: 1 }} /> ML training</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 10, background: RUST, display: "inline-block", borderRadius: 1 }} /> Pareto comparator</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 10, background: OCHRE, display: "inline-block", borderRadius: 1 }} /> Threshold reference</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 10, background: "#d4d4d4", display: "inline-block", borderRadius: 1 }} /> Landscape</span>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead><tr style={{ borderBottom: "2px solid #000", textAlign: "left" }}>
              <th style={{ padding: "8px 12px 8px 0", fontWeight: 600, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Reference</th>
              <th style={{ padding: "8px 12px", fontWeight: 600, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Journal</th>
              <th style={{ padding: "8px 12px", fontWeight: 600, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Title</th>
              <th style={{ padding: "8px 12px", fontWeight: 600, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: "#999", textAlign: "right" }}>LNPs</th>
              <th style={{ padding: "8px 0 8px 12px", fontWeight: 600, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Role</th>
            </tr></thead>
            <tbody>
              {papers.map((p, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #f0f0f0" }}>
                  <td style={{ padding: "10px 12px 10px 0", fontWeight: 600, whiteSpace: "nowrap", fontSize: 12 }}>{p.id}</td>
                  <td style={{ padding: "10px 12px", color: "#666", whiteSpace: "nowrap" }}>{p.journal}</td>
                  <td style={{ padding: "10px 12px", lineHeight: 1.4 }}>
                    {p.url ? (<a href={p.url} target="_blank" rel="noopener noreferrer" style={{ color: "#333", textDecoration: "underline", textUnderlineOffset: 2, textDecorationColor: "#ccc" }}>{p.title}</a>) : (<span style={{ color: "#666" }}>{p.title}</span>)}
                  </td>
                  <td style={{ padding: "10px 12px", textAlign: "right", fontFamily: NUM, color: p.lnps ? "#000" : "#ccc" }}>{p.lnps || "—"}</td>
                  <td style={{ padding: "10px 0 10px 12px" }}>
                    <span style={{ display: "inline-block", fontSize: 10, fontWeight: 600, letterSpacing: 0.5, padding: "2px 8px", borderRadius: 2,
                      background: `${roleColor(p.role)}10`, color: roleColor(p.role), border: `1px solid ${roleColor(p.role)}30` }}>{p.role}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>)}

        {/* FINDINGS */}
        {activeTab === "Findings" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 32 }}>Key Findings</h2>
          {findings.map((f, i) => (
            <div key={i} style={{ marginBottom: 32, paddingBottom: 32, borderBottom: i < findings.length - 1 ? "1px solid #f0f0f0" : "none" }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 8 }}>
                <span style={{ fontSize: 13, fontFamily: NUM, fontWeight: 700, color: "#000", minWidth: 24 }}>{String(i + 1).padStart(2, "0")}</span>
                <h3 style={{ fontSize: 15, fontWeight: 600 }}>{f.title}</h3>
              </div>
              <p style={{ fontSize: 13, color: "#555", lineHeight: 1.7, marginLeft: 36 }}>{f.text}</p>
            </div>
          ))}
          <div style={{ marginTop: 48, padding: "32px 0", borderTop: "1px solid #000", display: "flex", justifyContent: "space-between" }}>
            {[
              { n: "135", label: "Formulation records" },
              { n: "4", label: "Independent labs" },
              { n: "21", label: "Papers reviewed" },
              { n: "37", label: "Model features" },
            ].map(s => (
              <div key={s.label} style={{ textAlign: "center" }}>
                <div style={{ fontSize: 28, fontWeight: 700, fontFamily: NUM, letterSpacing: -1 }}>{s.n}</div>
                <div style={{ fontSize: 11, color: "#999", marginTop: 4 }}>{s.label}</div>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid #e0e0e0" }}>
            <p style={{ fontSize: 12, color: "#444", lineHeight: 1.6 }}><strong>What's next:</strong> The atlas updates as new data becomes available. Archived BM measurements from existing screens would be the single highest-impact addition — several hundred LNPs have been screened without BM in the organ panel. All code, data, and models are open source at the GitHub link above.</p>
            <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 1, background: "#e0e0e0", border: "1px solid #e0e0e0" }}>
              <div style={{ background: "#fff", padding: "16px 20px" }}>
                <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 6, color: INK }}>In progress</div>
                <div style={{ fontSize: 11, color: "#666", lineHeight: 1.5 }}>Automated update pipeline: new paper annotation → model retrain → figures → explorer update in one command</div>
              </div>
              <div style={{ background: "#fff", padding: "16px 20px" }}>
                <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 6, color: OCHRE }}>Coming soon</div>
                <div style={{ fontSize: 11, color: "#666", lineHeight: 1.5 }}>Additional paper annotations (targeting 200+ rows) and nearest-neighbor lookup tool for comparing candidate formulations against the dataset</div>
              </div>
              <div style={{ background: "#fff", padding: "16px 20px" }}>
                <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 6, color: "#999" }}>Investigating</div>
                <div style={{ fontSize: 11, color: "#666", lineHeight: 1.5 }}>Whether molecular descriptors and external LNP datasets can improve the model beyond feature-importance analysis — depends on resolving ionizable lipid structures</div>
              </div>
            </div>
          </div>
        </div>)}
      </main>

      <footer style={{ borderTop: "1px solid #e0e0e0", padding: "24px 48px" }}>
        <div style={{ maxWidth: 1100, margin: "0 auto", display: "flex", justifyContent: "space-between" }}>
          <span style={{ fontSize: 11, color: "#999" }}>HSC-LNP Atlas {"·"} Open source</span>
          <a href="https://github.com/tramngo1603/lnp-hsc-atlas" style={{ fontSize: 11, color: "#000", textDecoration: "none", fontFamily: "'DM Mono', monospace" }}>GitHub {"→"}</a>
        </div>
      </footer>
    </div>
  );
}