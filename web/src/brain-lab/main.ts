// Brain Lab (dev only): the neuron brain on the 10 real chats, with a variant switcher per design session
// and an evidence inspector that shows the engine numbers behind every mark. See BRAIN_NEURON_SPEC.md.
import frame from '../workspace/brain-frame.html?raw';
import engine from '../workspace/brain-engine.js?raw';
import tokensCss from '../design-system/tokens/tokens.css?raw';
import '../design-system/tokens/tokens.css';
import './lab.css';
import { tokens } from '../design-system/tokens/tokens';
import seed from '../workspace/data.generated.json';
import type { Chat } from '../workspace/types';

const B = tokens.component.brain;
const brainTokens = {
  stage: B.stage, dust: B.dust, fiber: B.fiber, link: B.link, linkRelated: B['link-related'], dendrite: B.dendrite,
  human: B.human, ai: B.ai, balanced: tokens.semantic.color.text.strong,
  cortex: Object.fromEntries(Object.entries(B.cortex).filter(([k]) => !k.startsWith('$'))),
  brainMode: 'neuron', lab: true,
};
const source = frame.replace('<head>', `<head><style>${tokensCss}</style>`)
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
      id: c.id, title: c.title, category: c.category, born: 1, anchor: anchor(c.category, i), since: c.dialogue[0]?.ts || '',
      outcomes: c.nodes.map(o => ({ id: o.id, title: o.title, parent: o.parent, related: o.related, x: o.x, y: o.y, root: o.root, human: final[o.id]?.human || 0, ai: final[o.id]?.ai || 0,
        atoms: c.atoms.filter(a => a.nodeId === o.id).map(a => ({ kind: a.kind, origin: a.origin, resolver: a.resolver })) })),
      ledger: [{ pair: 1, human: mass.reduce((s, m) => s + m.human, 0), ai: mass.reduce((s, m) => s + m.ai, 0) }],
    };
  }),
};

type Option = { value: string; label: string; note: string };
const GLOW: Option[] = [
  { value: 'on', label: 'Self-glow', note: 'Each part emits its own light: the cell body for the chat, each branch and end for its outcome.' },
  { value: 'off', label: 'Off', note: 'The bare membrane, to judge form and texture.' },
];
const FOOT: Option[] = [
  { value: 'off', label: 'Off', note: 'Only the neuron.' },
  { value: 'cells', label: 'Cells', note: 'Last round’s blue / amber cell patch under each neuron (for the far-zoom read, Session 13).' },
];
const state = { place: 'B', glow: 'on', footprint: 'off', axon: true, sparks: true, dim: true };

const root = document.getElementById('lab')!;
root.innerHTML = `
<div class="lab">
  <iframe class="lab-frame" title="Neuron brain on 10 real chats"></iframe>
  <aside class="lab-panel" aria-label="Lab controls">
    <header>
      <span class="lab-eyebrow">Brain Lab · Session 2b</span>
      <h1>One neuron template</h1>
      <p>Placement B (decided). Every chat is built from the same neuron form; only size, branches and glow come from its data. Orbit, then click a chat and its outcome ends.</p>
    </header>
    <fieldset><legend>Glow</legend><div class="lab-options" data-key="glow"></div></fieldset>
    <fieldset><legend>Surface footprint</legend><div class="lab-options" data-key="footprint"></div></fieldset>
    <label class="lab-check"><input type="checkbox" data-key="dim" checked> Dimmed brain surface, so the emitted light can be judged (art-direction preview)</label>
    <label class="lab-check"><input type="checkbox" data-key="sparks" checked> Requirement sparks: one light per requirement or question, coloured by who made it (Session 7 preview)</label>
    <label class="lab-check"><input type="checkbox" data-key="axon" checked> Axon: where links to other chats will leave (no data yet)</label>
    <section class="lab-evidence" aria-live="polite"><h2>Evidence</h2><p class="lab-empty">Click a neuron to see the engine numbers behind it.</p></section>
    <p class="lab-note">Provisional, not decided yet: sizes (Session 3), glow colour (Session 4), texture by work mode (Session 5), endings (Session 7), the brain surface (art direction).</p>
  </aside>
</div>`;
const iframe = root.querySelector<HTMLIFrameElement>('.lab-frame')!;
function renderOptions(key: 'glow' | 'footprint', opts: Option[]) {
  const box = root.querySelector(`[data-key="${key}"]`)!;
  box.innerHTML = opts.map(o => `<button type="button" class="lab-option" aria-pressed="${state[key] === o.value}" data-value="${o.value}"><b>${o.label}</b><span>${o.note}</span></button>`).join('');
  box.querySelectorAll<HTMLButtonElement>('button').forEach(b => b.onclick = () => { state[key] = b.dataset.value!; renderOptions(key, opts); push(); });
}
function push() { iframe.contentWindow?.postMessage({ type: 'cotrace-lab-set', lab: { ...state, glow: state.glow === 'on' } }, '*'); }
renderOptions('glow', GLOW); renderOptions('footprint', FOOT);
root.querySelector<HTMLInputElement>('[data-key="axon"]')!.onchange = e => { state.axon = (e.target as HTMLInputElement).checked; push(); };
root.querySelector<HTMLInputElement>('[data-key="dim"]')!.onchange = e => { state.dim = (e.target as HTMLInputElement).checked; push(); };
root.querySelector<HTMLInputElement>('[data-key="sparks"]')!.onchange = e => { state.sparks = (e.target as HTMLInputElement).checked; push(); };

const evidenceBox = root.querySelector('.lab-evidence')!;
type Evidence = { kind: string; title: string; rows: [string, string | number, string][] };
function showEvidence(ev: Evidence | null) {
  if (!ev) { evidenceBox.innerHTML = '<h2>Evidence</h2><p class="lab-empty">Click a neuron to see the engine numbers behind it.</p>'; return; }
  const esc = (s: unknown) => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]!));
  evidenceBox.innerHTML = `<h2>Evidence · ${ev.kind === 'chat' ? 'chat (soma)' : 'outcome (terminal head)'}</h2><h3>${esc(ev.title)}</h3>
    <dl>${ev.rows.map(([k, v, how]) => `<div><dt>${esc(k)}</dt><dd><b>${esc(v)}</b><small>${esc(how)}</small></dd></div>`).join('')}</dl>`;
}
addEventListener('message', e => {
  if (e.source !== iframe.contentWindow) return;
  if (e.data?.type === 'cotrace-brain-ready') { iframe.contentWindow!.postMessage({ type: 'cotrace-brain-data', graph }, '*'); push(); }
  if (e.data?.type === 'cotrace-lab-inspect') showEvidence(e.data.evidence);
  if (e.data?.type === 'cotrace-brain-select' && !e.data.id) showEvidence(null);
});
iframe.srcdoc = source;
