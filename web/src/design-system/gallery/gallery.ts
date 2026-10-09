// Living reference for the COTRACE design system (D8 gallery, v0.1).
// Everything on this page is generated from the token file, so it can't drift from the code.
import '../tokens/tokens.css';
import '../../workspace/obsidian-graph.css';
import './gallery.css';
import { tokens, lightTokens } from '../tokens/tokens';

type Tree = { [k: string]: unknown };
const P = tokens.primitive;
const S = tokens.semantic;
const G = tokens.component.graph;
const root = document.getElementById('gallery')!;

// ---------- helpers ----------
const h = (html: string) => html;
function lum(hex: string) {
  const n = parseInt(hex.slice(1), 16);
  const f = (c: number) => { c /= 255; return c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  return 0.2126 * f((n >> 16) & 255) + 0.7152 * f((n >> 8) & 255) + 0.0722 * f(n & 255);
}
function contrast(a: string, b: string) {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}
function rgbaOf(hex: string, a: number) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
}
function currentTree(): typeof tokens {
  return (document.documentElement.dataset.theme === 'light' ? lightTokens : tokens) as unknown as typeof tokens;
}

// ---------- sections ----------
const NEUTRAL_ROLES: Record<string, string> = {
  '1': 'canvas', '2': 'app root', '3': 'chrome', '4': 'panel', '5': 'raised', '6': 'hover · line', '7': 'strong line',
  '8': 'disabled', '9': 'faint', '10': 'muted text', '11': 'secondary', '12': 'primary text', '13': 'strongest',
};

function neutralScale() {
  const t = currentTree();
  const scale = (document.documentElement.dataset.theme === 'light' ? t.primitive.color['neutral-light'] : t.primitive.color['neutral-dark']) as unknown as Tree;
  const ground = String(t.semantic.color.bg.app);
  return Object.entries(scale).map(([k, v]) => h(`
    <div class="g-chip"><i style="background:${v}"></i><b>${k} · ${NEUTRAL_ROLES[k] ?? ''}</b><span>${v} · ${contrast(String(v), ground).toFixed(1)}:1</span></div>`)).join('');
}

function semanticCards(group: Tree, prefix: string) {
  return Object.entries(group).filter(([, v]) => typeof v === 'string').map(([k, v]) => h(`
    <div class="g-card"><div class="g-swatch" style="background:var(--color-${prefix}-${k})"></div><b>${prefix}.${k}</b><code>--color-${prefix}-${k}</code><br><small>${v}</small></div>`)).join('');
}

function textSamples() {
  const t = currentTree();
  const ground = String(t.semantic.color.surface.panel);
  return Object.entries(S.color.text).map(([k]) => {
    const v = String((t.semantic.color.text as unknown as Tree)[k]);
    return h(`<div class="g-card"><b style="color:var(--color-text-${k});font-size:var(--type-title-size)">The quick decision</b><code>--color-text-${k}</code><br><small>${v} · ${contrast(v, ground).toFixed(1)}:1 on panel</small></div>`);
  }).join('');
}

function partyColumn(who: 'human' | 'ai', label: string) {
  const rows = ['solid', 'text', 'soft', 'line'].map(r => h(`
    <div class="g-party-row"><i style="background:var(--color-party-${who}-${r})"></i><span><b>${r}</b> <span class="g-mono">--color-party-${who}-${r}</span></span></div>`)).join('');
  return h(`<div class="g-party-col"><h3 style="color:var(--color-party-${who}-text)">${label}</h3>${rows}</div>`);
}

function typeRoles() {
  return Object.keys(S.type).filter(k => !k.startsWith('$')).map(role => {
    const v = (S.type as unknown as Record<string, { fontSize: string; fontWeight: number; lineHeight: number }>)[role];
    const sample = role === 'overline' ? 'AI OPEN QUESTION' : role === 'metric' ? 'Pair 7 · Mass 1137' : role === 'body'
      ? 'You set the direction; the AI did the retrieval and synthesis. The map shows both, and every mark leads back to the exchange that made it.'
      : 'Reading strategy and presentation guide';
    return h(`<div class="g-type-row"><span>${role}<br>${v.fontSize} / ${v.fontWeight} / ${v.lineHeight}</span>
      <div class="type-${role}" style="${role === 'overline' ? 'text-transform:uppercase;' : ''}${role === 'metric' ? 'font-variant-numeric:tabular-nums;' : ''}">${sample}</div></div>`);
  }).join('');
}

function spaceScale() {
  return Object.entries(P.space).map(([k, v]) => h(`<div class="g-space-row"><span>space.${k}</span><i style="width:${v}"></i>${v}</div>`)).join('');
}
function radii() {
  return Object.entries(P.radius).map(([k, v]) => h(`<div class="g-shape"><i style="border-radius:${v}"></i>${k} · ${v}</div>`)).join('');
}
function elevations() {
  return Object.keys(S.elevation).filter(k => !k.startsWith('$')).map(k => h(`<div style="box-shadow:var(--elevation-${k})">elevation ${k}</div>`)).join('');
}

function components() {
  return h(`
  <div class="g-demo"><h3>Buttons</h3>
    <div class="g-row"><button class="g-btn">Open conversation</button><button class="g-btn ghost">Locate in Brain</button><button class="g-btn icon" aria-label="Expand">⤢</button><button class="g-btn" disabled>Disabled</button></div></div>
  <div class="g-demo"><h3>Tabs</h3><div class="g-tabs"><span>Brain</span><span class="on">AI creativity · paper research</span><span>Human–AI interaction</span></div></div>
  <div class="g-demo"><h3>Messages</h3>
    <div class="g-who h"><i>J</i>You</div><div class="g-msg">Can you give me a structure for presenting this paper today?</div>
    <div class="g-who a"><i>✳</i>Assistant</div><div>Let me build you a three-act structure that ties the paper to your own notes.</div></div>
  <div class="g-demo"><h3>Input and status</h3><div class="g-input">Continue the conversation…</div>
    <div class="g-status"><span><i class="dot" style="background:var(--color-status-warning)"></i>Chat backend not connected</span><b>6 outcomes · 7 exchanges</b></div></div>
  <div class="g-demo"><h3>Graph controls (on the dark stage)</h3><div class="g-darkstage theme-dark">
    <div class="og-badge"><div class="og-badge-dot"></div><span>Pair 4 · Mass 625 (outcome 5 Born)</span></div>
    <div class="og-capsule"><button class="og-nav" aria-label="Previous pair"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"/></svg></button>
      <div class="og-track" style="width:200px"><div class="og-rail"></div><div class="og-fill" style="transform:scaleX(0.5)"></div><div class="og-notches">
      ${[1, 2, 3, 4, 5, 6, 7].map(i => `<button class="og-notch${i <= 4 ? ' active' : ''}${i === 4 ? ' current' : ''}"><span class="og-notch-marker"></span><span class="og-notch-tag">P${i}</span></button>`).join('')}
      </div></div><button class="og-nav" aria-label="Next pair"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg></button></div>
    <div class="og-legend"><div class="og-hint"><span class="og-share"></span> Share ring</div><div class="og-hint"><div class="og-dot-u"></div> Your decision</div><div class="og-hint"><div class="og-dot-a"></div> AI decision</div><div class="og-hint"><span class="og-ring-a"></span> Open question</div><div class="og-hint"><span class="og-resolved"><span></span></span> Answered</div><div class="og-hint"><span class="og-ring-w"></span> Focus</div></div>
  </div></div>
  <div class="g-demo"><h3>Tooltip and toast</h3><div class="g-darkstage theme-dark">
    <div class="og-tooltip" style="border-color:${rgbaOf(S.color.party.human.solid, 0.4)}">
      <div class="og-tip-row"><div class="og-tip-head" style="color:var(--color-party-human-solid)">Human-Resolved</div><span class="og-tip-pill">From AI Question</span></div>
      <div class="og-tip-question"><span>Question:</span> Which two research directions should guide the search?</div>
      <div class="og-tip-options"><div class="og-tip-chose" style="color:var(--color-party-human-solid)">✓ User Chose: Both — bridge them</div></div>
      <div class="og-tip-result">The papers must bridge deskilling and creative autonomy.</div></div>
    <div class="og-toast" style="border:1px solid ${rgbaOf(S.color.party.ai.solid, 0.45)}"><div class="og-toast-label"><div class="og-toast-dot" style="background:var(--color-party-ai-solid)"></div><span style="color:var(--color-party-ai-solid)">Chat Jump</span></div><div class="og-toast-text">Expanded paper bank and recommendations</div></div>
  </div></div>`);
}

// ---------- page ----------
function render() {
  const theme = document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
  const C = currentTree().semantic.color;
  root.innerHTML = h(`<div class="g-wrap">
  <header class="g-head"><div><div class="g-sub" style="margin:0 0 var(--p-space-2)">COTRACE · design system v${'0.1.0'}</div>
    <h1>The Observatory of a Shared Mind</h1>
    <p>Every swatch, size and mark on this page is generated from <span class="g-mono">tokens.json</span>. Change a token, rebuild, and this page, the workspace and the graph all follow.</p></div>
    <div class="g-toggle" role="group" aria-label="Theme"><button data-theme="dark" aria-pressed="${theme === 'dark'}">Dark</button><button data-theme="light" aria-pressed="${theme === 'light'}">Light (provisional)</button></div></header>

  <section class="g-section"><h2>Neutral scale</h2><p>Twelve functional steps plus one, consolidating the prototype's 137 one-off greys. Contrast is measured against the app chrome.</p>
    <div class="g-scale">${neutralScale()}</div>
    <div class="g-sub">Grounds and surfaces</div><div class="g-grid">${semanticCards(C.bg as unknown as Tree, 'bg')}${semanticCards(C.surface as unknown as Tree, 'surface')}</div>
    <div class="g-sub">Borders</div><div class="g-grid">${semanticCards(C.border as unknown as Tree, 'border')}</div>
    <div class="g-sub">Text</div><div class="g-grid">${textSamples()}</div></section>

  <section class="g-section"><h2>The two parties</h2><p>One colour, one party, everywhere. Never decoration, focus, selection or status. Passes protan, deutan and tritan simulation (distance 24–30).</p>
    <div class="g-party">${partyColumn('human', 'Human')}${partyColumn('ai', 'AI')}</div>
    <div class="g-sub">System status (not for people's data)</div><div class="g-grid">${semanticCards(C.status as unknown as Tree, 'status')}<div class="g-card"><div class="g-swatch" style="background:var(--color-focus-ring)"></div><b>focus.ring</b><code>--color-focus-ring</code></div></div></section>

  <section class="g-section"><h2>Typography</h2><p>One family, fixed sizes, a 10px floor. Classes <span class="g-mono">.type-*</span> or variables <span class="g-mono">--type-*-size</span>.</p>${typeRoles()}</section>

  <section class="g-section"><h2>Space, shape and depth</h2><p>A 4px grid with 2px half-steps; tonal depth first, shadows only for floating layers.</p>
    <div class="g-sub">Space</div>${spaceScale()}
    <div class="g-sub">Radius</div><div class="g-shapes">${radii()}</div>
    <div class="g-sub">Elevation</div><div class="g-elev">${elevations()}</div></section>

  <section class="g-section"><h2>The visual grammar</h2><p>Size = accumulated mass. Share ring = who holds the measured influence (you clockwise from 12, then the AI). Beads on one orbit: your decisions, then the AI's, then open questions. White halo = focus. The stage stays dark in every theme.</p>
    <div class="g-stage theme-dark"><canvas id="grammar"></canvas><div class="g-stage-note">Drawn live from <span class="g-mono">component.graph.*</span> tokens: the same values the conversation map uses.</div></div></section>

  <section class="g-section"><h2>Components</h2><p>Baseline components from the workspace prototype, styled only with tokens.</p><div class="g-components">${components()}</div></section>

  <div class="g-foot">Source: web/src/design-system/tokens/tokens.json · Docs: docs/design-system/ · Rules for agents: docs/design-system/AGENT_GUIDE.md</div>
  </div>`);
  root.querySelectorAll<HTMLButtonElement>('.g-toggle button').forEach(b => b.addEventListener('click', () => {
    if (b.dataset.theme === 'light') document.documentElement.dataset.theme = 'light'; else delete document.documentElement.dataset.theme;
    render();
  }));
  drawGrammar();
}

// ---------- grammar canvas ----------
function drawGrammar() {
  const canvas = document.getElementById('grammar') as HTMLCanvasElement | null;
  if (!canvas) return;
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, hgt = canvas.clientHeight;
  canvas.width = w * dpr; canvas.height = hgt * dpr;
  const ctx = canvas.getContext('2d')!;
  ctx.scale(dpr, dpr);
  ctx.fillStyle = G.stage; ctx.fillRect(0, 0, w, hgt);
  const HUMAN = S.color.party.human.solid, AI = S.color.party.ai.solid;
  const label = (text: string, x: number, y: number) => {
    ctx.font = `500 11px ${P.font.family.sans.join(', ')}`; ctx.textAlign = 'center'; ctx.fillStyle = rgbaOf(G.node.label, 0.92);
    text.split('\n').forEach((l, i) => ctx.fillText(l, x, y + i * 14));
  };
  const sphere = (x: number, y: number, mass: number, human: number, opts: { dim?: boolean; focus?: boolean; beads?: ('h' | 'a' | 'q' | 'rh')[] } = {}) => {
    const r = G.node['radius-min'] + G.node['radius-range'] * Math.sqrt(Math.min(1, Math.max(mass, 10) / G.node['mass-norm']));
    const dim = opts.dim ? G.node['dormant-opacity'] : 1;
    const body = ctx.createRadialGradient(x - r * 0.35, y - r * 0.4, r * 0.1, x, y, r);
    body.addColorStop(0, rgbaOf(G.node['body-light'], 0.98 * dim)); body.addColorStop(0.7, rgbaOf(G.node['body-mid'], 0.9 * dim)); body.addColorStop(1, rgbaOf(G.node['body-edge'], 0.85 * dim));
    ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2); ctx.fillStyle = body; ctx.fill();
    const ring = G['share-ring'], rr = r + ring.offset, top = -Math.PI / 2;
    ctx.lineWidth = ring.width; ctx.globalAlpha = dim;
    if (human < 0) { ctx.setLineDash([3, 3]); ctx.strokeStyle = ring.unmeasured; ctx.beginPath(); ctx.arc(x, y, rr, 0, Math.PI * 2); ctx.stroke(); ctx.setLineDash([]); }
    else {
      const split = top + Math.PI * 2 * human, gap = human > 0 && human < 1 ? ring.gap / rr : 0;
      if (human > 0) { ctx.strokeStyle = HUMAN; ctx.beginPath(); ctx.arc(x, y, rr, top + gap, split - gap); ctx.stroke(); }
      if (human < 1) { ctx.strokeStyle = AI; ctx.beginPath(); ctx.arc(x, y, rr, split + gap, top + Math.PI * 2 - gap); ctx.stroke(); }
    }
    ctx.globalAlpha = 1;
    if (opts.focus) { ctx.strokeStyle = G['focus-halo']; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(x, y, r + 10, 0, Math.PI * 2); ctx.stroke(); }
    const beads = opts.beads || [];
    if (beads.length) {
      const B = G.bead, orbit = r + B.track + B['resolved-outer'] + 3;
      const size = (b: string) => b === 'q' ? B.ring : b === 'rh' ? B['resolved-outer'] : B.core;
      const grp = (b: string) => b === 'q' ? 2 : b === 'a' ? 1 : 0;
      const angles: number[] = []; let acc = 0;
      beads.forEach((b, i) => { if (i) acc += (size(beads[i - 1]) + size(b) + (grp(beads[i - 1]) !== grp(b) ? B['group-gap'] : B.gap)) / orbit; angles.push(acc); });
      const a0 = -Math.PI / 2 - acc / 2;
      ctx.strokeStyle = B['track-color']; ctx.lineWidth = 1; ctx.beginPath(); ctx.arc(x, y, orbit, a0 - 6 / orbit, a0 + acc + 6 / orbit); ctx.stroke();
      beads.forEach((b, i) => {
        const bx = x + Math.cos(a0 + angles[i]) * orbit, by = y + Math.sin(a0 + angles[i]) * orbit;
        ctx.globalAlpha = dim;
        if (b === 'q') { ctx.fillStyle = G.stage; ctx.beginPath(); ctx.arc(bx, by, B.ring, 0, Math.PI * 2); ctx.fill(); ctx.strokeStyle = AI; ctx.lineWidth = 1.75; ctx.stroke(); }
        else if (b === 'rh') { ctx.strokeStyle = AI; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(bx, by, B['resolved-outer'], 0, Math.PI * 2); ctx.stroke(); ctx.fillStyle = HUMAN; ctx.beginPath(); ctx.arc(bx, by, B['resolved-core'], 0, Math.PI * 2); ctx.fill(); }
        else { ctx.fillStyle = b === 'h' ? HUMAN : AI; ctx.beginPath(); ctx.arc(bx, by, B.core, 0, Math.PI * 2); ctx.fill(); }
        ctx.globalAlpha = 1;
      });
    }
    return r;
  };
  const cols = 5, step = w / cols, y = hgt * 0.52;
  const items: [number, number, string, Parameters<typeof sphere>[4]][] = [
    [450, 0.8, 'Mostly you\n80 / 20', { beads: ['h', 'h', 'h', 'rh', 'a'] }],
    [300, 0.5, 'Co-created\n50 / 50', { beads: ['h', 'h', 'a', 'a', 'q'], focus: true }],
    [507, 0.24, 'Mostly the AI\n24 / 76', { beads: ['h', 'a', 'a', 'a', 'a', 'a', 'q', 'q'] }],
    [44, 0.43, 'Dormant\nnot touched this pair', { beads: ['h', 'a'], dim: true }],
    [10, -1, 'Unmeasured\nno ledger rows yet', {}],
  ];
  const tetherFrom = { x: step * 2.5, y: hgt * 0.16 };
  items.forEach(([mass, human, text, opts], i) => {
    const x = step * (i + 0.5);
    ctx.strokeStyle = opts?.dim ? G.link.dormant : G.link.active; ctx.lineWidth = opts?.dim ? G.link['width-dormant'] : G.link.width;
    ctx.globalAlpha = 0.35; ctx.beginPath(); ctx.moveTo(tetherFrom.x, tetherFrom.y); ctx.lineTo(x, y - 46); ctx.stroke(); ctx.globalAlpha = 1;
    const r = sphere(x, y, mass, human, opts);
    label(text, x, y + r + 26);
  });
}

render();
window.addEventListener('resize', drawGrammar);
