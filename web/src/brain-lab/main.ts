// Brain Lab (dev only): the neuron brain on the real corpus, with a variant switcher per design session and an
// evidence inspector that shows the engine numbers behind every mark. See BRAIN_NEURON_SPEC.md and BRAIN_REGIONS_SPEC.md.
import frame from '../workspace/brain-frame.html?raw';
import engine from '../workspace/brain-engine.js?raw';
import tokensCss from '../design-system/tokens/tokens.css?raw';
import '../design-system/tokens/tokens.css';
import './lab.css';
import { tokens } from '../design-system/tokens/tokens';
import seed from '../workspace/data.generated.json';
import type { Chat } from '../workspace/types';
// Where each chat lives (BRAIN_REGIONS_SPEC): `python -m engine brainmap data/corpus --engine-root data/chats -o src/brain-lab/brain_map.generated.json`
import brainMapJson from './brain_map.generated.json';

type Placed = { title: string; taskType: string; area: string; region: string | null; side: number; direction: number[]; mass: number };
type Group = { name: string; keywords: string[]; members: string[]; side: number; direction: number[]; solitary?: boolean; regions?: string[] };
type ChatLink = { a: string; b: string; type: string; score: number; evidence: Record<string, unknown> };
const brainMap = brainMapJson as unknown as { chats: Record<string, Placed>; areas: Record<string, Group>; regions: Record<string, Group>; links: ChatLink[] };
const placeOf = (id: string) => {
  const p = brainMap.chats[id]; if (!p) return undefined;
  const region = p.region ? brainMap.regions[p.region] : undefined, area = brainMap.areas[p.area];
  return { areaName: area && !area.solitary ? area.name : 'solitary', regionName: region?.name, regionKeywords: region?.keywords || [] };
};

const B = tokens.component.brain;
const brainTokens = {
  stage: B.stage, dust: B.dust, fiber: B.fiber, link: B.link, linkRelated: B['link-related'], dendrite: B.dendrite,
  human: B.human, ai: B.ai, balanced: tokens.semantic.color.text.strong,
  cortex: Object.fromEntries(Object.entries(B.cortex).filter(([k]) => !k.startsWith('$'))),
  brainMode: 'neuron', lab: true,
};
const REGION_CSS = `#cotrace-brain .region-label{position:absolute;z-index:2;pointer-events:none;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font:500 10px/1.3 system-ui,sans-serif;letter-spacing:.14em;text-transform:uppercase;color:var(--color-text-secondary);text-shadow:0 1px 6px #000,0 0 14px #000}#cotrace-brain .region-label.area{font-size:11px;letter-spacing:.2em;color:var(--color-text-primary)}`;
const source = frame.replace('<head>', `<head><style>${tokensCss}${REGION_CSS}</style>`)
  .split('/* COTRACE_ENGINE */').join(`window.COTRACE_TOKENS=${JSON.stringify(brainTokens)};` + engine);

// Same placement inputs as Brain.tsx (topic lobes are provisional until Session 11 clustering).
const LOBES: Record<string, { side: number; direction: number[] }> = {
  Research: { side: 1, direction: [-.68, .38, .72] }, Coding: { side: 1, direction: [.56, -.35, .75] },
  Creative: { side: -1, direction: [.48, .48, .72] }, Writing: { side: -1, direction: [-.62, -.42, .69] },
  Planning: { side: 1, direction: [0, .82, .57] }, Learning: { side: -1, direction: [.05, -.72, .69] },
};
const lobeCount = new Map<string, number>();
function anchor(category: string, index: number) {
  const lobe = LOBES[category] || { side: index % 2 ? 1 : -1, direction: [0, 0, 1] };
  const i = lobeCount.get(category) || 0; lobeCount.set(category, i + 1);
  const a = i * 2.39996323, r = i ? .2 + .09 * Math.sqrt(i) : 0, [x, y, z] = lobe.direction;
  const d = [x + r * Math.cos(a), y + r * Math.sin(a), z], len = Math.hypot(...d);
  return { side: lobe.side, direction: d.map(c => c / len) };
}
const chats = (seed as unknown as { chats: Chat[] }).chats.filter(c => c.totalPairs);
const graph = {
  version: 1, maxPair: 1, links: [], atoms: [],
  nodes: chats.map((c, i) => {
    const final = c.snapshots.at(-1)?.mass || {}, mass = Object.values(final);
    return {
      id: c.id, title: c.title, category: c.category, born: 1, since: c.dialogue[0]?.ts || '', place: placeOf(c.id),
      anchor: brainMap.chats[c.id] ? { side: brainMap.chats[c.id].side, direction: brainMap.chats[c.id].direction } : anchor(c.category, i),
      outcomes: c.nodes.map(o => ({ id: o.id, title: o.title, parent: o.parent, related: o.related, x: o.x, y: o.y, root: o.root, human: final[o.id]?.human || 0, ai: final[o.id]?.ai || 0,
        atoms: c.atoms.filter(a => a.nodeId === o.id).map(a => ({ kind: a.kind, origin: a.origin, resolver: a.resolver })) })),
      ledger: [{ pair: 1, human: mass.reduce((s, m) => s + m.human, 0), ai: mass.reduce((s, m) => s + m.ai, 0) }],
    };
  }),
};
// Corpus chats the engine has not processed yet: placed by their text, shown as faint cell bodies (no invented mass).
for (const [id, p] of Object.entries(brainMap.chats)) {
  if (graph.nodes.some(n => n.id === id)) continue;
  graph.nodes.push({ id, title: p.title, category: p.taskType, born: 1, since: '~' + id, place: placeOf(id), unmapped: true,
    anchor: { side: p.side, direction: p.direction }, outcomes: [], ledger: [{ pair: 1, human: 0, ai: 0 }] } as never);
}
Object.assign(graph, {
  chatLinks: brainMap.links,
  regions: [
    ...Object.values(brainMap.areas).filter(a => !a.solitary).map(a => ({ kind: 'area', name: a.name, side: a.side, direction: a.direction })),
    ...Object.values(brainMap.regions).map(r => ({ kind: 'region', name: r.name, side: r.side, direction: r.direction })),
  ],
});
const mapSummary = (() => {
  const types = brainMap.links.reduce((m, l) => ({ ...m, [l.type]: (m[l.type] || 0) + 1 }), {} as Record<string, number>);
  const areas = Object.values(brainMap.areas).filter(a => !a.solitary).length, unmapped = graph.nodes.filter(n => (n as { unmapped?: boolean }).unmapped).length;
  return `${graph.nodes.length} chats · ${areas} areas · ${Object.keys(brainMap.regions).length} regions · ${brainMap.links.length} connections (${types.continued || 0} continued, ${types.reused || 0} reused, ${types.similar || 0} similar) · ${unmapped} not yet mapped`;
})();

type Option = { value: string; label: string; note: string };
const BRAIN: Option[] = [
  { value: 'slate', label: 'Dark slate', note: 'Neutral dark glass so the light carries the meaning.' },
  { value: 'white', label: 'White glass', note: 'A pale, brighter cortex.' },
];
const SIZE: Option[] = [
  { value: 'cbrt', label: 'Volume-true (∛)', note: 'The cell body’s volume grows with the work: 8× the work = 2× as wide. The whole archive fits in about 10×.' },
  { value: 'sqrt', label: 'Area-true (√)', note: 'The body’s on-screen area grows with the work. The archive would span about 30×, so the biggest chats must be capped.' },
  { value: 'log', label: 'Steps (log)', note: 'Every doubling of the work adds the same step. Most compact (about 5×), but sizes no longer compare as amounts.' },
];
const state = { place: 'B', brain: 'slate', hybrid: true, etch: true, twigs: true, bloom: true, axon: true, footprint: 'off', size: 'cbrt', regionNames: true, axons: true, showUnmapped: true };

const root = document.getElementById('lab')!;
root.innerHTML = `
<div class="lab">
  <iframe class="lab-frame" title="Neuron brain on 10 real chats"></iframe>
  <aside class="lab-panel" aria-label="Lab controls">
    <header>
      <span class="lab-eyebrow">Brain Lab · Sessions 11–12 (B1.2)</span>
      <h1>Where each chat lives</h1>
      <p>Chats are placed by what they are about, read from their own text (BRAIN_REGIONS_SPEC): related chats form regions, regions sit inside areas, and connections come only from evidence. Click any chat to see its area, region and connections.</p>
      <p class="lab-formula">${mapSummary}</p>
    </header>
    <label class="lab-check"><input type="checkbox" data-key="regionNames" checked> Area and region names (areas when far, regions when you zoom in)</label>
    <label class="lab-check"><input type="checkbox" data-key="axons" checked> Connections: continued (thick), reused, similar (thin); 3 strongest per chat until one is opened</label>
    <label class="lab-check"><input type="checkbox" data-key="showUnmapped" checked> Corpus chats not yet mapped (faint cell bodies)</label>
    <h2 class="lab-sub">Session 3 · size</h2>
    <header>
      <span class="lab-eyebrow">Brain Lab · Session 3</span>
      <h1>How big is each neuron?</h1>
      <p>One absolute scale for every chat, driven by its measured mass, never relative to the biggest chat, so adding a chat never shrinks the others. The smallest measured chat sets a readable floor. Switch the rule and compare.</p>
    </header>
    <fieldset><legend>Size rule <span class="lab-tag">Session 3 candidates</span></legend><div class="lab-options" data-key="size"></div></fieldset>
    <section class="lab-scale" aria-live="polite"></section>
    <h2 class="lab-sub">Look (fix pass 2)</h2>
    <fieldset><legend>Brain surface <span class="lab-tag">art direction</span></legend><div class="lab-options" data-key="brain"></div></fieldset>
    <label class="lab-check"><input type="checkbox" data-key="hybrid" checked> Hybrid membrane: organic (blue) and circuitry (orange) in proportion to who did the work</label>
    <label class="lab-check"><input type="checkbox" data-key="etch" checked> Cortex etching: circuit traces on the brain where the AI did the work, blue nerve light where you did</label>
    <label class="lab-check"><input type="checkbox" data-key="twigs" checked> Requirement twigs (who made each decision)</label>
    <label class="lab-check"><input type="checkbox" data-key="bloom" checked> Bloom (light spilling into the dark)</label>
    <label class="lab-check"><input type="checkbox" data-key="axon" checked> Axon (where links to other chats will leave)</label>
    <label class="lab-check"><input type="checkbox" data-key="cells"> Cell footprint under each neuron</label>
    <section class="lab-evidence" aria-live="polite"><h2>Evidence</h2><p class="lab-empty">Click a neuron to see the engine numbers behind it.</p></section>
    <p class="lab-note">Provisional, not decided yet: glow strength (Session 4), texture by work mode (Session 5), the brain surface (art direction), titles (Session 9).</p>
  </aside>
</div>`;
const iframe = root.querySelector<HTMLIFrameElement>('.lab-frame')!;
function renderOptions(key: 'brain' | 'size', opts: Option[]) {
  const box = root.querySelector(`[data-key="${key}"]`)!;
  box.innerHTML = opts.map(o => `<button type="button" class="lab-option" aria-pressed="${state[key] === o.value}" data-value="${o.value}"><b>${o.label}</b><span>${o.note}</span></button>`).join('');
  box.querySelectorAll<HTMLButtonElement>('button').forEach(b => b.onclick = () => { state[key] = b.dataset.value!; renderOptions(key, opts); push(); });
}
function push() { iframe.contentWindow?.postMessage({ type: 'cotrace-lab-set', lab: { ...state } }, '*'); }
renderOptions('brain', BRAIN); renderOptions('size', SIZE);
for (const key of ['hybrid', 'etch', 'twigs', 'bloom', 'axon', 'regionNames', 'axons', 'showUnmapped'] as const) root.querySelector<HTMLInputElement>(`[data-key="${key}"]`)!.onchange = e => { state[key] = (e.target as HTMLInputElement).checked; push(); };
root.querySelector<HTMLInputElement>('[data-key="cells"]')!.onchange = e => { state.footprint = (e.target as HTMLInputElement).checked ? 'cells' : 'off'; push(); };

const evidenceBox = root.querySelector('.lab-evidence')!;
type Evidence = { kind: string; title: string; rows: [string, string | number, string][] };
function showEvidence(ev: Evidence | null) {
  if (!ev) { evidenceBox.innerHTML = '<h2>Evidence</h2><p class="lab-empty">Click a neuron to see the engine numbers behind it.</p>'; return; }
  const esc = (s: unknown) => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]!));
  evidenceBox.innerHTML = `<h2>Evidence · ${ev.kind === 'chat' ? 'chat (soma)' : 'outcome (terminal head)'}</h2><h3>${esc(ev.title)}</h3>
    <dl>${ev.rows.map(([k, v, how]) => `<div><dt>${esc(k)}</dt><dd><b>${esc(v)}</b><small>${esc(how)}</small></dd></div>`).join('')}</dl>`;
}
const scaleBox = root.querySelector('.lab-scale')!;
type ScaleRow = { label: string; mass: number; R: number; px: number; note: string; ref: boolean };
function showScale(d: { label: string; rows: ScaleRow[] }) {
  const esc = (s: unknown) => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]!));
  const max = Math.max(...d.rows.map(r => r.px), 1);
  scaleBox.innerHTML = `<h2>Scale</h2><p class="lab-formula">${esc(d.label)}</p><table><thead><tr><th>Chat</th><th>Mass</th><th>R</th><th>Size at overview</th></tr></thead><tbody>${d.rows.map(r => `<tr class="${r.ref ? 'ref' : ''}"><td>${esc(r.label)}${r.note ? `<small>${esc(r.note)}</small>` : ''}</td><td>${r.mass.toLocaleString()}</td><td>${r.R.toFixed(3)}</td><td><span class="lab-bar" style="width:${Math.max(2, 100 * r.px / max)}%"></span>${r.px} px</td></tr>`).join('')}</tbody></table>`;
}
addEventListener('message', e => {
  if (e.source !== iframe.contentWindow) return;
  if (e.data?.type === 'cotrace-brain-ready') { iframe.contentWindow!.postMessage({ type: 'cotrace-brain-data', graph }, '*'); push(); }
  if (e.data?.type === 'cotrace-lab-inspect') showEvidence(e.data.evidence);
  if (e.data?.type === 'cotrace-lab-scale') showScale(e.data);
  if (e.data?.type === 'cotrace-brain-select' && !e.data.id) showEvidence(null);
});
iframe.srcdoc = source;
