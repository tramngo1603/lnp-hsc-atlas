import { useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, ReferenceLine, ReferenceArea, Label } from "recharts";

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
  { title: "The potency-selectivity tradeoff", text: "Antibody-conjugated LNPs achieve 12\u201344\u00d7 higher potency but deliver 76% of cargo to liver. Untargeted LNPs show better selectivity at lower absolute potency. Confirmed across all four labs in the dataset." },
  { title: "Cholesterol as a liver predictor", text: "Cholesterol mol% varies from 38\u201348% across formulations in the dataset. The model identifies this variation as the 3rd\u20134th most important feature driving organ tropism. Three independent wet-lab studies confirm the mechanism: glycolipid substitution (Gentry 2025), cholesterol removal (Su 2024), and bile acid replacement (Patel 2024) each de-target liver through the cholesterol axis." },
  { title: "PEG architecture, not chain length", text: "C18PEG2000 abolishes BM delivery (0.3 barcode counts). ALC-0159, also C18 chain but different architecture, enables the highest BM delivery in the screen (barcode 48). A 160-fold divergence formally disproving the chain-length hypothesis." },
  { title: "Cargo optimization matters equally", text: "Tessera\u2019s NHP HBB editing improved 24% \u2192 40% through Gene Writer optimization alone \u2014 same LNP. A second dose pushed to 60%. The therapeutic outcome is the product of delivery efficiency \u00d7 editing efficiency." },
  { title: "The 20% therapeutic threshold", text: "Newby et al. (2021) established via secondary transplant that \u226520% sickle-to-Makassar editing rescues SCD in mice. This threshold defines what \u2018therapeutically relevant\u2019 means for the field." },
  { title: "No LNP in the ideal zone", text: "Only Ensoma\u2019s VLP platform (31% editing, ~0% liver) occupies the ideal zone. Whether LNPs can match VLP-level selectivity while retaining manufacturing simplicity remains the central open question." },
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
  { id: "Sago 2018", journal: "JACS", title: "Nanoparticles that deliver RNA to bone marrow identified by directed evolution", role: "Landscape", lnps: 100, url: "https://doi.org/10.1021/jacs.8b08976" },
  { id: "Loughrey 2025", journal: "Chem. Commun.", title: "The time course of in vivo cellular responses to LNPs", role: "Landscape", lnps: null, url: "https://doi.org/10.1039/D4CC06659F" },
  { id: "Cullis 2025", journal: "Nature Communications", title: "Liposomal lipid nanoparticles for extrahepatic delivery of mRNA", role: "Landscape", lnps: 10, url: "https://doi.org/10.1038/s41467-025-58523-w" },
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

const tabs = ["Pareto", "Features", "Timeline", "BM Coverage", "Papers", "Findings"];
const NUM = "'Space Mono', 'Courier New', monospace";

export default function Explorer() {
  const [activeTab, setActiveTab] = useState("Pareto");

  return (
    <div style={{ background: "#fff", minHeight: "100vh", color: "#000", fontFamily: "'DM Sans', -apple-system, sans-serif" }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Space+Mono:wght@400;700&display=swap');*{box-sizing:border-box;margin:0;padding:0;}`}</style>

      <header style={{ padding: "48px 48px 40px", borderBottom: "1px solid #000" }}>
        <div style={{ maxWidth: 960, margin: "0 auto" }}>
          <p style={{ fontSize: 11, letterSpacing: 3, textTransform: "uppercase", color: "#999", marginBottom: 16, fontFamily: "'DM Mono', monospace" }}>HSC-LNP Atlas</p>
          <h1 style={{ fontSize: 32, fontWeight: 300, lineHeight: 1.3, letterSpacing: -0.5 }}>
            Potency–Selectivity Tradeoff in<br /><span style={{ fontWeight: 700 }}>HSC-Targeted LNP Delivery</span>
          </h1>
          <p style={{ fontSize: 13, color: "#666", marginTop: 16 }}>135 formulations · 4 labs · 21 papers reviewed</p>
          <p style={{ fontSize: 12, color: "#999", marginTop: 4 }}>Tram Ngo · <a href="https://github.com/tramngo1603/lnp-hsc-atlas" style={{ color: "#000", textDecoration: "underline", textUnderlineOffset: 2 }}>github.com/tramngo1603/lnp-hsc-atlas</a></p>
        </div>
      </header>

      <nav style={{ borderBottom: "1px solid #e0e0e0", position: "sticky", top: 0, background: "#fff", zIndex: 10 }}>
        <div style={{ maxWidth: 960, margin: "0 auto", display: "flex", padding: "0 48px", overflowX: "auto" }}>
          {tabs.map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)} style={{
              background: "none", border: "none", cursor: "pointer", whiteSpace: "nowrap",
              padding: "16px 20px", fontSize: 12, fontWeight: activeTab === tab ? 600 : 400,
              color: activeTab === tab ? "#000" : "#999",
              borderBottom: activeTab === tab ? "2px solid #000" : "2px solid transparent",
              fontFamily: "'DM Sans', sans-serif", letterSpacing: 0.5,
            }}>{tab}</button>
          ))}
        </div>
      </nav>

      <main style={{ maxWidth: 960, margin: "0 auto", padding: "40px 48px 80px" }}>

        {activeTab === "Pareto" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>BM Delivery vs Liver Off-Target</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 12, lineHeight: 1.6 }}>
            <span style={{ color: INK, fontWeight: 600 }}>● Untargeted LNP</span>{" · "}
            <span style={{ color: RUST, fontWeight: 600 }}>▲ Targeted LNP</span>{" · "}
            <span style={{ color: OCHRE, fontWeight: 600 }}>■ VLP</span>
            {" — Filled = editing. Open = reporter."}
          </p>
          <p style={{ fontSize: 12, color: "#999", marginBottom: 32 }}>Hover any point for details. Shaded region = ideal zone (>20% BM, &lt;5% liver).</p>
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
              { label: "Cargo \u2260 delivery", desc: "Tessera 24\u219240\u219260%: cargo optimization, then dose escalation", accent: RUST },
            ].map(c => (
              <div key={c.label} style={{ background: "#fff", padding: "20px 24px", borderTop: `3px solid ${c.accent}` }}>
                <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8, color: c.accent }}>{c.label}</div>
                <div style={{ fontSize: 12, color: "#666", lineHeight: 1.5 }}>{c.desc}</div>
              </div>
            ))}
          </div>
          <p style={{ fontSize: 11, color: "#999", marginTop: 16, lineHeight: 1.5 }}>Tessera liver values estimated from reported 3:1 BM:liver ratio. Editas 58% NHP editing omitted — quantitative liver data not disclosed.</p>
        </div>)}

        {activeTab === "Features" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Feature Importance</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 32, lineHeight: 1.6 }}>LightGBM, leave-one-paper-out CV, balanced accuracy 0.484. All five known SARs confirmed in the top 9. IL molecular weight enters rank 7 after PPZ-A10 SMILES confirmation.</p>
          <div style={{ border: "1px solid #e0e0e0", padding: "24px 12px 12px 4px" }}>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={shapData} layout="vertical" margin={{ top: 8, right: 40, bottom: 8, left: 120 }}>
                <CartesianGrid stroke="#f0f0f0" horizontal={false} />
                <XAxis type="number" domain={[0, 1.2]} tick={{ fontSize: 11, fill: "#999" }} stroke="#ddd" tickLine={false}>
                  <Label value="Mean |SHAP value|" position="bottom" offset={0} style={{ fontSize: 12, fill: "#666" }} />
                </XAxis>
                <YAxis type="category" dataKey="feature" tick={{ fontSize: 12, fill: "#333" }} stroke="none" width={120} />
                <Tooltip contentStyle={{ background: "#fff", border: "1px solid #ccc", fontSize: 12 }} formatter={(val) => [val.toFixed(3), "|SHAP|"]} />
                <Bar dataKey="shap" radius={[0, 2, 2, 0]}>
                  {shapData.map((entry, i) => (<Cell key={i} fill={entry.type === "known" ? INK : entry.type === "new" ? OCHRE : "#d4d4d4"} />))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div style={{ display: "flex", gap: 32, marginTop: 24, fontSize: 12, color: "#666" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ display: "inline-block", width: 12, height: 12, background: INK, borderRadius: 1 }} /> Known SAR — confirmed</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ display: "inline-block", width: 12, height: 12, background: OCHRE, borderRadius: 1 }} /> Cholesterol — see below</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ display: "inline-block", width: 12, height: 12, background: "#d4d4d4", borderRadius: 1 }} /> Other detected</span>
          </div>
          <div style={{ marginTop: 32, border: `1px solid ${OCHRE}40`, borderLeft: `3px solid ${OCHRE}`, padding: "20px 24px", background: `${OCHRE}06` }}>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: 1, textTransform: "uppercase", marginBottom: 8, color: OCHRE }}>Why cholesterol ranks 3rd–4th</div>
            <p style={{ fontSize: 13, color: "#444", lineHeight: 1.7 }}>Cholesterol mol% varies from 38–48% across formulations in the dataset. Formulations at the lower end use a 5th lipid component that proportionally displaces cholesterol, creating variation the model can learn from. The model identifies this as the 3rd most important predictor of organ tropism.</p>
            <p style={{ fontSize: 13, color: "#444", lineHeight: 1.7, marginTop: 8 }}>This finding converges with three independent wet-lab studies that each de-target liver through the cholesterol axis: glycolipid substitution for DSPC (Gentry, PNAS 2025), complete cholesterol removal (Su, Nat. Commun. 2024), and bile acid replacement (Patel, Theranostics 2024). The computational and experimental evidence point in the same direction.</p>
          </div>
        </div>)}

        {activeTab === "Timeline" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>In Vivo HSC Delivery Milestones</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 32 }}>From the first BM-targeting nanoparticle to 60% NHP HSC editing in seven years.</p>
          <div style={{ borderLeft: "2px solid #e0e0e0", marginLeft: 48 }}>
            {timelineData.map((item, i) => {
              const c = platformColor(item.platform);
              return (<div key={i} style={{ display: "flex", position: "relative" }}>
                <div style={{ width: 10, height: 10, borderRadius: item.platform === "VLP" ? 0 : "50%", background: c, border: `2px solid ${c}`, position: "absolute", left: -6, top: 5 }} />
                <div style={{ width: 48, flexShrink: 0, fontSize: 11, fontFamily: NUM, color: "#999", paddingTop: 4, marginLeft: -64 }}>{item.year}</div>
                <div style={{ paddingLeft: 24, paddingBottom: 28 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: c }}>{item.label}</div>
                  <div style={{ fontSize: 12, color: "#666", marginTop: 2, lineHeight: 1.5 }}>{item.detail}</div>
                </div>
              </div>);
            })}
          </div>
          <div style={{ display: "flex", gap: 24, marginTop: 16, fontSize: 12, color: "#666" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 8, height: 8, borderRadius: "50%", background: INK, display: "inline-block" }} /> Untargeted LNP</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 8, height: 8, borderRadius: "50%", background: RUST, display: "inline-block" }} /> Targeted LNP</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 8, height: 8, background: OCHRE, display: "inline-block" }} /> VLP</span>
          </div>
        </div>)}

        {activeTab === "BM Coverage" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Bone Marrow in the Organ Panel</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 32, lineHeight: 1.6 }}>Number of LNP formulations screened per study, and whether bone marrow was included in the biodistribution panel.</p>
          <div style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 12, paddingBottom: 8, borderBottom: "1px solid #e0e0e0" }}>
            <div style={{ width: 160, fontSize: 11, color: "#999", flexShrink: 0, textAlign: "right", textTransform: "uppercase", letterSpacing: 1 }}>Study</div>
            <div style={{ flex: 1, fontSize: 11, color: "#999", textTransform: "uppercase", letterSpacing: 1 }}>Formulations screened</div>
            <div style={{ width: 64, fontSize: 11, color: "#999", flexShrink: 0, textTransform: "uppercase", letterSpacing: 1 }}>Count</div>
          </div>
          {bmGapData.map((item, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 16, marginBottom: 14 }}>
              <div style={{ width: 160, fontSize: 12, color: item.measured ? "#000" : "#bbb", flexShrink: 0, textAlign: "right", fontWeight: item.measured ? 600 : 400 }}>{item.study}</div>
              <div style={{ flex: 1, height: 24, background: item.measured ? "#f8f8f8" : "#fafafa", position: "relative", border: item.measured ? `1px solid ${INK}20` : "1px solid #f0f0f0" }}>
                <div style={{ height: "100%", width: `${(item.lnps / 200) * 100}%`, background: item.measured ? INK : "#eeebe8" }} />
              </div>
              <div style={{ width: 64, fontSize: 12, fontFamily: NUM, color: item.measured ? "#000" : "#ccc", flexShrink: 0, fontWeight: item.measured ? 700 : 400 }}>{item.lnps}</div>
            </div>
          ))}
          <div style={{ display: "flex", gap: 32, marginTop: 28, fontSize: 12, color: "#666" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 14, height: 14, background: INK, display: "inline-block", borderRadius: 1 }} /> BM in organ panel</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 14, height: 14, background: "#eeebe8", display: "inline-block", borderRadius: 1 }} /> BM not measured</span>
          </div>
        </div>)}

        {activeTab === "Papers" && (<div>
          <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>Annotated Papers</h2>
          <p style={{ fontSize: 13, color: "#666", marginBottom: 12, lineHeight: 1.6 }}>21 papers curated for the atlas. Each assigned a role based on data availability. Click any title to view the source.</p>
          <div style={{ display: "flex", gap: 20, marginBottom: 32, fontSize: 12 }}>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 10, background: INK, display: "inline-block", borderRadius: 1 }} /> ML training</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 10, background: RUST, display: "inline-block", borderRadius: 1 }} /> Pareto comparator</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 10, background: OCHRE, display: "inline-block", borderRadius: 1 }} /> Threshold reference</span>
            <span style={{ display: "flex", alignItems: "center", gap: 6 }}><span style={{ width: 10, height: 10, background: "#d4d4d4", display: "inline-block", borderRadius: 1 }} /> Landscape</span>
          </div>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #000", textAlign: "left" }}>
                <th style={{ padding: "8px 12px 8px 0", fontWeight: 600, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Reference</th>
                <th style={{ padding: "8px 12px", fontWeight: 600, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Journal</th>
                <th style={{ padding: "8px 12px", fontWeight: 600, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Title</th>
                <th style={{ padding: "8px 12px", fontWeight: 600, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: "#999", textAlign: "right" }}>LNPs</th>
                <th style={{ padding: "8px 0 8px 12px", fontWeight: 600, fontSize: 11, letterSpacing: 0.5, textTransform: "uppercase", color: "#999" }}>Role</th>
              </tr>
            </thead>
            <tbody>
              {papers.map((p, i) => (
                <tr key={i} style={{ borderBottom: "1px solid #f0f0f0" }}>
                  <td style={{ padding: "10px 12px 10px 0", fontWeight: 600, whiteSpace: "nowrap", fontSize: 12 }}>{p.id}</td>
                  <td style={{ padding: "10px 12px", color: "#666", whiteSpace: "nowrap" }}>{p.journal}</td>
                  <td style={{ padding: "10px 12px", lineHeight: 1.4 }}>
                    {p.url ? (
                      <a href={p.url} target="_blank" rel="noopener noreferrer" style={{ color: "#333", textDecoration: "underline", textUnderlineOffset: 2, textDecorationColor: "#ccc" }}>{p.title}</a>
                    ) : (
                      <span style={{ color: "#666" }}>{p.title}</span>
                    )}
                  </td>
                  <td style={{ padding: "10px 12px", textAlign: "right", fontFamily: NUM, color: p.lnps ? "#000" : "#ccc" }}>{p.lnps || "\u2014"}</td>
                  <td style={{ padding: "10px 0 10px 12px" }}>
                    <span style={{
                      display: "inline-block", fontSize: 10, fontWeight: 600, letterSpacing: 0.5,
                      padding: "2px 8px", borderRadius: 2,
                      background: `${roleColor(p.role)}10`, color: roleColor(p.role), border: `1px solid ${roleColor(p.role)}30`,
                    }}>{p.role}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>)}

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
        </div>)}
      </main>

      <footer style={{ borderTop: "1px solid #e0e0e0", padding: "24px 48px" }}>
        <div style={{ maxWidth: 960, margin: "0 auto", display: "flex", justifyContent: "space-between" }}>
          <span style={{ fontSize: 11, color: "#999" }}>HSC-LNP Atlas · Open source</span>
          <a href="https://github.com/tramngo1603/lnp-hsc-atlas" style={{ fontSize: 11, color: "#000", textDecoration: "none", fontFamily: "'DM Mono', monospace" }}>GitHub \u2192</a>
        </div>
      </footer>
    </div>
  );
}