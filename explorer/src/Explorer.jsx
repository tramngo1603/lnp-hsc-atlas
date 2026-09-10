import { useEffect, useMemo, useState } from 'react';
import { Bar, BarChart, CartesianGrid, Cell, Label, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis } from 'recharts';
import './styles.css';

const INK = '#2b4162';
const COLORS = [INK, '#a46950', '#8b854a', '#738e9b', '#a5aeba'];
const FINDINGS_INTRO = 'Lipid nanoparticles (LNPs) are tiny packages for RNA. What matters is where the RNA acts and whether it does its intended job.';
const TABS = [
  ['overview', 'Overview'], ['pareto', 'Pareto'], ['compare', 'Compare'],
  ['formulations', 'Formulations'], ['peg', 'PEG lipids'], ['helper', 'Helper lipids'],
  ['dose', 'Dose and response'], ['features', 'Feature importance'],
  ['sources', 'Sources'], ['findings', 'Findings'],
];
const fmt = (value) => value == null ? 'Not reported' : Number(value).toLocaleString('en-US', { maximumFractionDigits: 2 });
const axisFmt = (value) => Math.abs(value) >= 1000 ? Number(value).toLocaleString('en-US', { notation: 'compact', maximumFractionDigits: 1 }) : fmt(value);
const short = (value, limit = 36) => String(value || '').length > limit ? String(value).slice(0, limit - 1) + '…' : value;
const readTab = () => TABS.some(([key]) => key === window.location.hash.slice(1)) ? window.location.hash.slice(1) : 'overview';
const resultLabel = (value) => value ? value[0].toUpperCase() + value.slice(1) : 'Not rated';

function Heading({ title, children }) {
  return <><h2>{title}</h2>{children && <p className="intro">{children}</p>}</>;
}

function ResultTag({ value }) {
  return <span className={'result-tag ' + (value || '')}>{resultLabel(value)}</span>;
}

function PointTooltip({ active, payload, unit, paired = false }) {
  if (!active || !payload?.length) return null;
  const point = payload[0].payload;
  return <div className="chart-tooltip">
    <strong>{point.name || point.label}</strong>
    {point.source && <div>{point.source}</div>}
    {paired ? <><div>Bone marrow: {fmt(point.bm)} {unit}</div><div>Liver: {fmt(point.liver)} {unit}</div></> : <div>{point.n ? 'Mean result: ' : 'Result: '}{fmt(point.mean ?? point.value)} {unit}</div>}
    {point.n && <div>{point.n} records · range {fmt(point.min)}–{fmt(point.max)}</div>}
    {point.dose != null && <div>Dose: {fmt(point.dose)} mg/kg</div>}
    {point.schedule && <div>{point.schedule}</div>}
    {point.estimated && <div className="muted">Approximate value from the source</div>}
    {point.reference && <div className="muted">{short(point.reference, 170)}</div>}
  </div>;
}

function StudySelector({ groups, group, setGroup }) {
  const sources = [...new Map(groups.map(g => [g.paperId, g.source])).entries()];
  const options = groups.filter(g => g.paperId === group.paperId);
  return <div className="filters">
    <label className="field">Source
      <select aria-label="Chart source" value={group.paperId} onChange={e => setGroup(groups.filter(g => g.paperId === e.target.value).sort((a, b) => b.points.length - a.points.length)[0].id)}>
        {sources.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
      </select>
    </label>
    <label className="field">Measurement
      <select aria-label="Chart measurement" value={group.id} onChange={e => setGroup(e.target.value)}>
        {options.map(g => <option key={g.id} value={g.id}>{g.measurement} · {short(g.target, 52)} ({g.points.length})</option>)}
      </select>
    </label>
  </div>;
}

function MeasurementDetails({ points, unit, paired = false }) {
  return <details className="result-details">
    <summary>View {points.length} reported results</summary>
    <div className="table-scroll"><table>
      <thead><tr><th>Formulation</th><th className="numeric">{paired ? 'Bone marrow' : 'Result'} ({unit})</th>{paired && <th className="numeric">Liver ({unit})</th>}<th className="numeric">Dose (mg/kg)</th><th>Study details</th></tr></thead>
      <tbody>{points.map(p => <tr key={p.id}>
        <td><strong>{p.name}</strong><small>{p.source}</small></td>
        <td className="numeric">{fmt(paired ? p.bm : p.value)}</td>
        {paired && <td className="numeric">{fmt(p.liver)}</td>}
        <td className="numeric">{p.dose == null ? '—' : fmt(p.dose)}</td>
        <td>{p.detail || p.measurement}{p.schedule && <small>{p.schedule}</small>}<small>{p.reference}</small></td>
      </tr>)}</tbody>
    </table></div>
  </details>;
}

function ParetoPage({ data }) {
  const groups = data.analysisData.pareto;
  const [groupId, setGroup] = useState(groups[0]?.id);
  const group = groups.find(g => g.id === groupId) || groups[0];
  if (!group) return <div className="empty">No records report both bone-marrow and liver results in comparable units yet.</div>;
  const frontier = group.points.filter(p => p.frontier);
  return <>
    <Heading title="Bone-marrow and liver delivery">Compare higher bone-marrow delivery with lower liver delivery within the same study and measurement.</Heading>
    <StudySelector groups={groups} group={group} setGroup={setGroup} />
    <div className="chart-frame">
      <div className="chart-meta"><strong>{group.points.length} paired results</strong><span>{group.measurement} · {group.unit}</span></div>
      <ResponsiveContainer width="100%" height={440}>
        <ScatterChart margin={{ top: 15, right: 28, bottom: 35, left: 20 }}>
          <CartesianGrid stroke="#edf0f3" />
          <XAxis type="number" dataKey="liver" domain={[0, group.unit === '%' ? 100 : 'auto']} tick={{ fontSize: 14, fill: '#66717c' }} tickFormatter={axisFmt} tickLine={false} stroke="#aab3bd">
            <Label value={'Liver (' + group.unit + ')'} position="bottom" offset={15} style={{ fontSize: 15, fill: '#5e6872' }} />
          </XAxis>
          <YAxis type="number" dataKey="bm" domain={[0, group.unit === '%' ? 100 : 'auto']} tick={{ fontSize: 14, fill: '#66717c' }} tickFormatter={axisFmt} tickLine={false} stroke="#aab3bd">
            <Label value={'Bone marrow (' + group.unit + ')'} angle={-90} position="insideLeft" offset={-8} style={{ fontSize: 15, fill: '#5e6872' }} />
          </YAxis>
          <Tooltip content={<PointTooltip paired unit={group.unit} />} />
          <Scatter data={group.points} isAnimationActive={false}>{group.points.map(p => <Cell key={p.id} fill={p.frontier ? INK : '#a7b3c3'} stroke="#fff" strokeWidth={1} />)}</Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
    <div className="legend"><span><i className="highlight" />Best trade-offs in this group</span><span><i />Other results</span></div>
    <div className="takeaway"><strong>{frontier.map(p => p.name).join(', ')}</strong>{frontier.length === 1 ? ' offers' : ' offer'} the best observed trade-off{frontier.length > 1 ? 's' : ''} in this group. No other point has both higher bone-marrow delivery and lower liver delivery.</div>
    <p className="page-note">{data.analysisData.coverage.newPairs} of the {data.analysisData.coverage.literatureRecords} added literature records report both numeric percentages from the same experiment. Records with only one result, relative changes, or a different measurement stay off these axes.</p>
    <MeasurementDetails paired points={group.points} unit={group.unit} />
  </>;
}

function CompositionPage({ data, kind }) {
  const groups = data.analysisData[kind];
  const defaultGroup = groups.find(g => g.paperId === 'kim_2024' && g.unit === 'barcode counts') || groups[0];
  const [groupId, setGroupId] = useState(defaultGroup?.id);
  const [helper, setHelper] = useState(kind === 'peg' ? 'DOTAP' : 'all');
  const group = groups.find(g => g.id === groupId) || groups[0];
  if (!group) return <div className="empty">No results include the composition details needed for this chart yet.</div>;
  const helperOptions = [...new Set(group.points.map(p => p.helper).filter(Boolean))];
  const activeHelper = helperOptions.includes(helper) ? helper : 'all';
  const points = group.points.filter(p => kind !== 'peg' || activeHelper === 'all' || p.helper === activeHelper);
  const summaries = [...new Set(points.map(p => p[kind]))].map(label => {
    const values = points.filter(p => p[kind] === label).map(p => p.value);
    return { label, n: values.length, mean: values.reduce((a, b) => a + b, 0) / values.length, min: Math.min(...values), max: Math.max(...values) };
  }).sort((a, b) => b.mean - a.mean);
  const title = kind === 'peg' ? 'PEG lipids and bone-marrow delivery' : 'Helper lipids and bone-marrow delivery';
  return <>
    <Heading title={title}>Explore reported results by lipid. Each source keeps its own measurement scale.</Heading>
    <StudySelector groups={groups} group={group} setGroup={id => { setGroupId(id); setHelper('all'); }} />
    {kind === 'peg' && helperOptions.length > 1 && <div className="filters"><label className="field">Helper lipid<select aria-label="Helper lipid filter" value={activeHelper} onChange={e => setHelper(e.target.value)}><option value="all">All helper lipids</option>{helperOptions.map(h => <option key={h}>{h}</option>)}</select></label></div>}
    <div className="chart-frame">
      <div className="chart-meta"><strong>{points.length} reported results · {summaries.length} lipid{summaries.length !== 1 ? 's' : ''}</strong><span>{group.measurement} · {group.unit}</span></div>
      <ResponsiveContainer width="100%" height={Math.max(300, summaries.length * 57 + 90)}>
        <BarChart data={summaries} layout="vertical" margin={{ top: 10, right: 32, bottom: 33, left: 5 }}>
          <CartesianGrid stroke="#edf0f3" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 14, fill: '#66717c' }} stroke="#aab3bd" tickLine={false} tickFormatter={axisFmt}>
            <Label value={'Mean result (' + group.unit + ')'} position="bottom" offset={15} style={{ fontSize: 15, fill: '#5e6872' }} />
          </XAxis>
          <YAxis type="category" dataKey="label" width={145} tick={{ fontSize: 14, fill: '#33465b' }} tickLine={false} axisLine={false} tickFormatter={v => short(v, 23)} />
          <Tooltip content={<PointTooltip unit={group.unit} />} />
          <Bar dataKey="mean" maxBarSize={31} radius={[0, 3, 3, 0]} isAnimationActive={false}>{summaries.map((row, i) => <Cell key={row.label} fill={COLORS[i % COLORS.length]} />)}</Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
    <div className="takeaway">{summaries.length > 1 ? <><strong>{summaries[0].label}</strong> has the highest mean result in the selected records: {fmt(summaries[0].mean)} {group.unit}, from {summaries[0].n} records.</> : <>All selected records use <strong>{summaries[0]?.label}</strong>. This source does not compare multiple {kind === 'peg' ? 'PEG' : 'helper'} lipids for this measurement.</>}</div>
    <p className="page-note">Other ingredients, doses, and study conditions may also differ. These comparisons do not isolate the effect of one lipid.</p>
    <MeasurementDetails points={points} unit={group.unit} />
  </>;
}

function DosePage({ data }) {
  const groups = data.analysisData.dose;
  const defaultGroup = groups.find(g => new Set(g.points.map(p => p.dose)).size > 1) || groups[0];
  const [groupId, setGroup] = useState(defaultGroup?.id);
  const group = groups.find(g => g.id === groupId) || groups[0];
  if (!group) return <div className="empty">No results include both a numeric response and a dose in mg/kg yet.</div>;
  const doses = [...new Set(group.points.map(p => p.dose))].sort((a, b) => a - b);
  return <>
    <Heading title="Dose and response">Reported results at each dose. Select a source to explore its measurements.</Heading>
    <StudySelector groups={groups} group={group} setGroup={setGroup} />
    <div className="chart-frame">
      <div className="chart-meta"><strong>{group.points.length} reported results · {doses.length} dose{doses.length !== 1 ? 's' : ''}</strong><span>{group.measurement} · {group.unit}</span></div>
      <ResponsiveContainer width="100%" height={410}>
        <ScatterChart margin={{ top: 18, right: 28, bottom: 35, left: 20 }}>
          <CartesianGrid stroke="#edf0f3" />
          <XAxis type="number" dataKey="dose" domain={[0, 'auto']} tick={{ fontSize: 14, fill: '#66717c' }} tickLine={false} stroke="#aab3bd"><Label value="Dose per injection (mg/kg)" position="bottom" offset={15} style={{ fontSize: 15, fill: '#5e6872' }} /></XAxis>
          <YAxis type="number" dataKey="value" domain={[0, group.unit === '%' ? 100 : 'auto']} tick={{ fontSize: 14, fill: '#66717c' }} tickLine={false} stroke="#aab3bd" tickFormatter={axisFmt}><Label value={'Result (' + group.unit + ')'} angle={-90} position="insideLeft" offset={-8} style={{ fontSize: 15, fill: '#5e6872' }} /></YAxis>
          <Tooltip content={<PointTooltip unit={group.unit} />} />
          <Scatter data={group.points} fill={INK} fillOpacity={0.7} isAnimationActive={false} />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
    <div className="takeaway">{doses.length === 1 ? <>These records all use <strong>{fmt(doses[0])} mg/kg per injection</strong>. They show differences between experiments, not how response changes with dose.</> : <>The selected records cover <strong>{fmt(doses[0])} to {fmt(doses.at(-1))} mg/kg per injection</strong>. Compare formulation and dosing schedule before attributing a difference to dose.</>}</div>
    <p className="page-note">Points show reported measurements. Formulations and repeat-dose schedules may differ; no response curve is fitted.</p>
    <MeasurementDetails points={group.points} unit={group.unit} />
  </>;
}

function ComparePage({ data }) {
  const [candidate, setCandidate] = useState({ il: 35, hlPct: 15, chol: 47, peg: 1.5, cv: 0, dose: 0.5, hl: 'DOTAP', tgt: 'None' });
  const fields = [
    ['il', 'Ionizable lipid (%)', 15, 60, 1], ['hlPct', 'Helper lipid (%)', 5, 45, 1],
    ['chol', 'Cholesterol (%)', 15, 55, 0.5], ['peg', 'PEG lipid (%)', 0.5, 5, 0.5],
    ['cv', 'Covalent lipid (%)', 0, 25, 1], ['dose', 'Dose (mg/kg)', 0.1, 5, 0.1],
  ];
  const neighbors = useMemo(() => {
    const cols = ['il', 'hlPct', 'chol', 'peg', 'cv', 'dose'];
    const stats = Object.fromEntries(cols.map(col => {
      const vals = data.formulations.map(f => f[col]).filter(v => v != null);
      const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
      const std = Math.sqrt(vals.reduce((a, b) => a + (b - mean) ** 2, 0) / vals.length) || 1;
      return [col, { mean, std }];
    }));
    const ranked = data.formulations.filter(f => f.cls != null).map(f => {
      const distance = cols.reduce((sum, col) => sum + ((candidate[col] - (f[col] ?? stats[col].mean)) / stats[col].std) ** 2, 0)
        + (f.hl === candidate.hl ? 0 : 1) + ((f.tgt === 'CD117' ? 'CD117' : 'None') === candidate.tgt ? 0 : 1);
      return { ...f, distance: Math.sqrt(distance) };
    }).sort((a, b) => a.distance - b.distance);
    const seen = new Set();
    return ranked.filter(f => {
      const key = JSON.stringify([f.paperId, f.id]);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    }).slice(0, 5);
  }, [candidate, data.formulations]);
  const total = candidate.il + candidate.hlPct + candidate.chol + candidate.peg + candidate.cv;
  const update = (key, value) => setCandidate(old => ({ ...old, [key]: value }));
  return <>
    <Heading title="Compare a formulation">Adjust the composition to find similar tested records. Matches provide context; they do not predict a new formulation's outcome.</Heading>
    <div className="compare-grid">
      <section className="candidate-panel" aria-labelledby="candidate-title">
        <h3 id="candidate-title">Candidate composition</h3>
        {fields.map(([key, label, min, max, step]) => <label className="slider-field" key={key}>
          <span>{label}</span><input type="range" aria-label={label} min={min} max={max} step={step} value={candidate[key]} onChange={e => update(key, Number(e.target.value))} /><output>{fmt(candidate[key])}</output>
        </label>)}
        <div className="candidate-selects">
          <label className="field">Helper lipid<select value={candidate.hl} onChange={e => update('hl', e.target.value)}>{['DOTAP', 'DDAB', 'DOTMA', 'EPC', 'DSPC', 'DOPE'].map(h => <option key={h}>{h}</option>)}</select></label>
          <label className="field">Targeting<select value={candidate.tgt} onChange={e => update('tgt', e.target.value)}>{['None', 'CD117'].map(t => <option key={t}>{t}</option>)}</select></label>
        </div>
        <p className={'composition-total' + (total < 90 || total > 110 ? ' warning' : '')}>Total composition: <strong>{fmt(total)} mol%</strong>{total < 90 || total > 110 ? ' · Aim for about 100%.' : ''}</p>
      </section>
      <aside className="matches-panel" aria-labelledby="matches-title">
        <h3 id="matches-title">5 closest tested formulations</h3>
        {neighbors[0]?.distance > 2 && <p className="page-note">The closest records still differ substantially from this candidate.</p>}
        {neighbors.map((n, i) => <article className="match" key={n.paperId + n.id + n.experiment}>
          <div className="source">{i + 1}. {n.p}</div>
          <div className="match-head"><strong>{n.id}</strong><ResultTag value={n.cls} /></div>
          <p>{n.hl} {n.il != null && '· ' + fmt(n.il) + '% ionizable lipid'}{n.dose != null && ' · ' + fmt(n.dose) + ' mg/kg'}</p>
        </article>)}
      </aside>
    </div>
    <h3 className="section-title">Mean absolute SHAP values</h3>
    <div className="feature-chips">{data.shapData.slice(0, 5).map(f => <div className="feature-chip" key={f.feature}>{f.feature}<strong>{fmt(f.shap)}</strong></div>)}</div>
    <p className="page-note">These values describe the fitted model across the dataset, not this candidate. Similar records may use different assays, and missing composition values limit the comparison.</p>
  </>;
}

function FormulationsPage({ data }) {
  const [paper, setPaper] = useState('all');
  const [search, setSearch] = useState('');
  const [sort, setSort] = useState({ key: 'p', direction: 1 });
  const rows = data.formulations.filter(f => (paper === 'all' || f.paperId === paper) && (f.id + ' ' + f.p + ' ' + f.hl).toLowerCase().includes(search.toLowerCase())).sort((a, b) => {
    if (a[sort.key] == null) return 1;
    if (b[sort.key] == null) return -1;
    return (typeof a[sort.key] === 'number' ? a[sort.key] - b[sort.key] : String(a[sort.key]).localeCompare(String(b[sort.key]))) * sort.direction;
  });
  const cols = [['p', 'Source'], ['id', 'Formulation'], ['hl', 'Helper lipid'], ['il', 'Ionizable %'], ['chol', 'Cholesterol %'], ['peg', 'PEG %'], ['dose', 'Dose (mg/kg)'], ['tgt', 'Target'], ['cls', 'Result']];
  return <>
    <Heading title="Reported formulations">Browse {data.stats.rows} records from {data.stats.sources} sources. A formulation may appear in more than one experiment.</Heading>
    <div className="filters"><label className="field">Source<select value={paper} onChange={e => setPaper(e.target.value)}><option value="all">All sources</option>{data.papers.map(p => <option key={p.paperId} value={p.paperId}>{p.id}</option>)}</select></label><label className="field search">Search<input type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Formulation, source, or helper lipid" /></label></div>
    <div className="table-scroll"><table className="records-table"><thead><tr>{cols.map(([key, label]) => <th key={key}><button className="sort-button" onClick={() => setSort(s => ({ key, direction: s.key === key ? -s.direction : 1 }))}>{label}{sort.key === key ? (sort.direction === 1 ? ' ↑' : ' ↓') : ''}</button></th>)}</tr></thead><tbody>
      {rows.map(f => <tr key={f.paperId + f.id + f.experiment}>{cols.map(([key]) => <td key={key} className={['il', 'chol', 'peg', 'dose'].includes(key) ? 'numeric' : ''}>{key === 'cls' ? <ResultTag value={f.cls} /> : key === 'id' ? <strong title={f.experiment}>{f.id}</strong> : f[key] == null || f[key] === 'N/R' ? '—' : typeof f[key] === 'number' ? fmt(f[key]) : f[key]}</td>)}</tr>)}
    </tbody></table>{rows.length === 0 && <div className="empty">No matching records.</div>}</div>
    <p className="page-note">{rows.length} records shown. A dash means the value was not reported. Results reflect each study's assay and are not a universal ranking.</p>
  </>;
}

function FeaturesPage({ data }) {
  return <>
    <Heading title="Feature importance">Mean absolute SHAP values show how strongly each feature contributes to the fitted model's output.</Heading>
    <div className="chart-frame">
      <ResponsiveContainer width="100%" height={500}>
        <BarChart data={data.shapData} layout="vertical" margin={{ top: 10, right: 38, bottom: 35, left: 5 }}>
          <CartesianGrid stroke="#edf0f3" horizontal={false} />
          <XAxis type="number" tick={{ fontSize: 14, fill: '#66717c' }} stroke="#aab3bd" tickLine={false}><Label value="Mean absolute SHAP value" position="bottom" offset={15} style={{ fontSize: 15, fill: '#5e6872' }} /></XAxis>
          <YAxis type="category" dataKey="feature" width={155} tick={{ fontSize: 14, fill: '#33465b' }} axisLine={false} tickLine={false} />
          <Tooltip contentStyle={{ fontSize: 15, borderRadius: 5, border: '1px solid #cbd3db' }} formatter={v => [fmt(v), 'Mean absolute SHAP']} />
          <Bar dataKey="shap" fill={INK} radius={[0, 3, 3, 0]} maxBarSize={27} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
    </div>
    <p className="page-note">Exploratory model associations, not proof of cause or a prediction for a new formulation. Differences between studies and incomplete data can affect the ranking.</p>
  </>;
}

function Finding({ finding, papers, compact = false }) {
  const sources = finding.sources.map(id => papers.find(p => p.paperId === id)).filter(Boolean);
  return <article className={compact ? 'finding-card' : 'finding'}>
    <h3>{finding.title}</h3>
    <p>{finding.text}</p>
    <div className="finding-meaning"><strong>Why it matters</strong><p>{finding.meaning}</p></div>
    <details className="finding-evidence">
      <summary>See the evidence</summary>
      {finding.evidence.map((text, index) => <p key={index}>{text}</p>)}
      <div className="finding-sources"><span>Sources:</span>{sources.map(source => source.url ? <a key={source.paperId} href={source.url} target="_blank" rel="noopener noreferrer">{source.id} ↗</a> : <span key={source.paperId}>{source.id}</span>)}</div>
    </details>
  </article>;
}

function SourcesPage({ data }) {
  return <>
    <Heading title="Sources">{data.papers.length} sources contribute to the atlas. Open a title to read the original source.</Heading>
    <div className="table-scroll"><table className="sources-table"><thead><tr><th>Source</th><th>Publication</th><th>Title</th><th className="numeric">Records</th></tr></thead><tbody>
      {data.papers.map(p => <tr key={p.paperId}><td><strong>{p.id}</strong></td><td>{p.journal}</td><td>{p.url ? <a href={p.url} target="_blank" rel="noopener noreferrer">{p.title}</a> : p.title}{p.status.includes('abstract') && <small>Abstract only</small>}{p.status.includes('partial') && <small>Partially reviewed</small>}</td><td className="numeric">{p.records}</td></tr>)}
    </tbody></table></div>
  </>;
}

export default function ExplorerView({ data }) {
  const [tab, setTab] = useState(readTab);
  useEffect(() => { const handler = () => setTab(readTab()); window.addEventListener('hashchange', handler); return () => window.removeEventListener('hashchange', handler); }, []);
  const navigate = (key) => { window.location.hash = key; setTab(key); };
  return <>
    <header className="site-header"><div className="shell"><div className="brand">HSC–LNP Atlas</div><h1>LNP Delivery to Blood Stem Cells</h1><p>Explore tested formulations, delivery results, and key findings.</p><div className="byline">Tram Ngo · <a href="https://github.com/tramngo1603/lnp-hsc-atlas">Project on GitHub</a></div></div></header>
    <nav className="site-nav" aria-label="Explorer"><div className="shell nav-inner">{TABS.map(([key, label]) => <button key={key} className={tab === key ? 'active' : ''} aria-current={tab === key ? 'page' : undefined} onClick={() => navigate(key)}>{label}</button>)}</div></nav>
    <main className="shell" id="main-content">
      {tab === 'overview' && <>
        <Heading title="Overview">A view of the reported evidence for bone-marrow delivery.</Heading>
        <div className="metric-row"><div className="metric"><strong>{fmt(data.stats.rows)}</strong><span>Records</span></div><div className="metric"><strong>{fmt(data.stats.sources)}</strong><span>Sources</span></div><div className="metric"><strong>{fmt(data.analysisData.coverage.responseRecords)}</strong><span>Numeric results</span></div></div>
        <h3 className="section-title">Key findings</h3><p className="findings-intro">{FINDINGS_INTRO}</p><div className="finding-grid">{data.findings.slice(0, 2).map(f => <Finding key={f.id} finding={f} papers={data.papers} compact />)}</div>
        <div style={{ marginTop: 18 }}><button className="button" onClick={() => navigate('findings')}>Explore all findings →</button></div>
        <h3 className="section-title">Sources</h3><div className="source-counts">{data.sourceSummary.sources.map(s => <div className="source-count" key={s.id}><span>{s.label}</span><strong>{s.rows}</strong></div>)}</div>
        <button className="button" onClick={() => navigate('sources')}>Read the sources →</button>
      </>}
      {tab === 'pareto' && <ParetoPage data={data} />}
      {tab === 'compare' && <ComparePage data={data} />}
      {tab === 'formulations' && <FormulationsPage data={data} />}
      {(tab === 'peg' || tab === 'helper') && <CompositionPage key={tab} data={data} kind={tab} />}
      {tab === 'dose' && <DosePage data={data} />}
      {tab === 'features' && <FeaturesPage data={data} />}
      {tab === 'sources' && <SourcesPage data={data} />}
      {tab === 'findings' && <><Heading title="Key findings">{FINDINGS_INTRO}</Heading><div className="findings-list">{data.findings.map(f => <Finding key={f.id} finding={f} papers={data.papers} />)}</div></>}
    </main>
    <footer className="site-footer"><div className="shell"><span>HSC–LNP Atlas · {data.stats.rows} records · {data.stats.sources} sources</span><a href="https://github.com/tramngo1603/lnp-hsc-atlas">Data and methods ↗</a></div></footer>
  </>;
}
