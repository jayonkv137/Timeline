// The simple brain (BRAIN_V2_SPEC). One dot = one chat. Size = how much happened. Colour = who led.
// Where = what it is about: 8 universal lobes (the same for everyone) holding the person's own regions.
// The chat's own graph shows as small dots around it; lines between chats only where the engine found evidence.
import frame from '../workspace/brain-frame.html?raw';
import '../design-system/tokens/tokens.css';
import './v2.css';
import { tokens } from '../design-system/tokens/tokens';
import dataJson from './brain_v2.generated.json';

type Outcome = { id: string; title: string; parent: string | null; root: boolean; x: number; y: number; human: number; ai: number };
type Chat = { title: string; domain: string; domainSource: string; region: string | null; side: number; direction: number[]; mapped: boolean; pairs: number;
  human: number | null; ai: number | null; share: number | null; outcomes: Outcome[]; decisions: { human: number; ai: number } | null };
type Link = { a: string; b: string; type: string; score: number; evidence: { keywords?: string[]; reason?: string } };
const data = dataJson as unknown as { domains: { id: string; name: string; direction: number[] }[]; regions: Record<string, { name: string; keywords: string[] }>;
  chats: Record<string, Chat>; links: Link[]; balance: { human: number; ai: number; mappedChats: number; chats: number } };

// three.js ships inside the brain frame; load the same build once.
const start = frame.indexOf('<script>console.warn(');
const three = frame.slice(start + 8, frame.indexOf('</script>', start));
const tag = document.createElement('script'); tag.textContent = three; document.head.appendChild(tag);
const T = (window as unknown as { THREE: any }).THREE;

// ---------------------------------------------------------------- encodings (spec §3)
const PALETTES: Record<string, { human: string; ai: string; label: string }> = {
  amber: { human: tokens.component.brain.human as string, ai: tokens.component.brain.ai as string, label: 'Blue / amber (current tokens)' },
  violet: { human: '#2fd0f0', ai: '#b483ff', label: 'Cyan / violet' },
};
const CO = '#eef2f7', UNMAPPED = '#6b7a8c';
const TOPIC: Record<string, string> = { work: '#f2a65a', research: '#a98bfa', tech: '#3fd69b', creative: '#f472b6', health: '#fb7185', learning: '#5aa9fa', writing: '#f5cf4a', life: '#2dd4bf', other: '#94a3b8' };
let palette = 'amber', lens: 'who' | 'topics' = 'who';
function whoColor(share: number | null) {
  if (share === null) return new T.Color(UNMAPPED);
  const p = PALETTES[palette];
  // Three states only, always at full colour: the eye reads hue in one glance, tints wash out.
  if (share >= 0.6) return new T.Color(p.human);
  if (share <= 0.4) return new T.Color(p.ai);
  return new T.Color(CO);
}
const whoLabel = (s: number | null) => s === null ? 'not mapped yet' : s >= 0.6 ? 'human-led' : s <= 0.4 ? 'AI-led' : 'co-created';
const somaRadius = (mass: number) => 0.028 * Math.cbrt(Math.max(1, mass / 25)); // Session 3 candidate (volume-true)

// ---------------------------------------------------------------- page
const root = document.getElementById('v2')!;
const P = PALETTES[palette], bal = data.balance, youPct = Math.round(100 * bal.human / (bal.human + bal.ai));
root.innerHTML = `
<canvas class="v2-canvas" aria-label="Your chats as a brain. Drag to rotate, scroll to zoom, click a chat."></canvas>
<div class="v2-labels"></div>
<section class="v2-hud" aria-label="Brain summary">
  <span class="v2-eyebrow">Your brain · ${bal.mappedChats} of ${bal.chats} chats mapped</span>
  <h1>How much of it is you?</h1>
  <div class="v2-balance" role="img" aria-label="You did ${youPct} percent of the measured work, AI ${100 - youPct} percent">
    <span class="you" style="flex:${bal.human}"></span><span class="ai" style="flex:${bal.ai}"></span>
  </div>
  <div class="v2-balance-text"><b class="you-text">You ${youPct}%</b><b class="ai-text">AI ${100 - youPct}%</b></div>
  <p class="v2-note">of the measured work across mapped chats (who shaped each outcome, from the engine's ledger)</p>
  <div class="v2-switch" role="group" aria-label="Lens"><button data-lens="who" aria-pressed="true">Who led</button><button data-lens="topics" aria-pressed="false">Topics</button></div>
  <ul class="v2-legend"></ul>
  <label class="v2-check"><input type="checkbox" data-opt="outcomes" checked> Each chat's outcomes</label>
  <label class="v2-check"><input type="checkbox" data-opt="links" checked> Connections between chats</label>
  <label class="v2-select">AI colour <select data-opt="palette">${Object.entries(PALETTES).map(([k, v]) => `<option value="${k}">${v.label}</option>`).join('')}</select></label>
</section>
<aside class="v2-card" hidden></aside>
<div class="v2-tip" hidden></div>
<p class="v2-hint">Drag to rotate · scroll to zoom · click a chat</p>`;
void P;

const canvas = root.querySelector<HTMLCanvasElement>('.v2-canvas')!, labelsEl = root.querySelector<HTMLDivElement>('.v2-labels')!;
const renderer = new T.WebGLRenderer({ canvas, antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2)); renderer.setClearColor('#05070b', 1);
const scene = new T.Scene(), camera = new T.PerspectiveCamera(36, 1, 0.05, 60);
const view = { theta: -0.35, phi: 1.34, radius: 8.6, target: new T.Vector3(0, -0.12, 0) }, goal = { ...view, target: view.target.clone() };

// ---------------------------------------------------------------- brain silhouette (quiet: points + a faint mesh + rim)
function brainPoint(n: any, side: number, lift = 0) {
  const x = n.x, y = n.y, z = n.z, f = Math.sin(7.5 * x + 1.8 * Math.sin(3.5 * y + 1.4 * z)) + .62 * Math.sin(8 * y + 1.7 * Math.sin(3.8 * z - 1.7 * x)) + .23 * Math.sin(12 * z + 3 * x);
  const groove = Math.exp(-f * f * 9), r = 1.015 - .105 * groove + .019 * Math.sin(15 * x + 9 * y + 4 * z);
  const p = new T.Vector3(2.02 * x * r, 1.29 * y * r + .13 * (1 - x * x) - .075 * x, side * (.64 + .60 * z * r));
  if (y < -.35 && x < -.25) p.y += .13 * (-y - .35) * (-x);
  return p.addScaledVector(new T.Vector3(x / 2.02, y / 1.29, side * z / .60).normalize(), lift);
}
const dir = (v: number[]) => new T.Vector3(v[0], v[1], v[2]).normalize();
const glowTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 128; const g = c.getContext('2d')!, r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  r.addColorStop(0, 'rgba(255,255,255,1)'); r.addColorStop(.18, 'rgba(255,255,255,.85)'); r.addColorStop(.42, 'rgba(255,255,255,.22)'); r.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = r; g.fillRect(0, 0, 128, 128); return new T.CanvasTexture(c); })();
const ringTex = (() => { const c = document.createElement('canvas'); c.width = c.height = 64; const g = c.getContext('2d')!; g.strokeStyle = '#fff'; g.lineWidth = 6; g.beginPath(); g.arc(32, 32, 22, 0, Math.PI * 2); g.stroke(); return new T.CanvasTexture(c); })();
const sprite = (color: any, scale: number, opacity = 1, tex = glowTex) => { const s = new T.Sprite(new T.SpriteMaterial({ map: tex, color, transparent: true, opacity, depthWrite: false, blending: T.AdditiveBlending })); s.scale.setScalar(scale); return s; };

const shell = new T.Group(); scene.add(shell);
for (const side of [-1, 1]) {
  const pts: number[] = [], nodes: any[] = [], N = 2200;
  for (let i = 0; i < N; i++) { const y = 1 - 2 * (i + .5) / N, r = Math.sqrt(1 - y * y), a = i * 2.399963; const p = brainPoint(new T.Vector3(r * Math.cos(a), y, r * Math.sin(a)), side, .01); pts.push(p.x, p.y, p.z); if (i % 4 === 0) nodes.push(p) }
  const pg = new T.BufferGeometry(); pg.setAttribute('position', new T.Float32BufferAttribute(pts, 3));
  shell.add(new T.Points(pg, new T.PointsMaterial({ color: '#8da2b8', size: .016, transparent: true, opacity: .45, depthWrite: false, blending: T.AdditiveBlending })));
  const seg: number[] = [];
  for (const a of nodes) { const near = nodes.map(b => [a.distanceTo(b), b]).filter(([d]) => d > 1e-6 && d < .32).sort((p, q) => p[0] - q[0]).slice(0, 2); for (const [, b] of near) seg.push(a.x, a.y, a.z, b.x, b.y, b.z) }
  const lg = new T.BufferGeometry(); lg.setAttribute('position', new T.Float32BufferAttribute(seg, 3));
  shell.add(new T.LineSegments(lg, new T.LineBasicMaterial({ color: '#6c8197', transparent: true, opacity: .16, depthWrite: false, blending: T.AdditiveBlending })));
  // a dark body so the far side does not shine through, with a soft rim
  const g = new T.SphereGeometry(1, 96, 64), pos = g.attributes.position, v = new T.Vector3();
  for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i); const p = brainPoint(v.clone().normalize(), side, -.012); pos.setXYZ(i, p.x, p.y, p.z) }
  g.computeVertexNormals();
  shell.add(new T.Mesh(g, new T.ShaderMaterial({ transparent: false, depthWrite: true, side: T.DoubleSide, uniforms: {}, // mirrored hemisphere flips winding
    vertexShader: 'varying vec3 n;varying vec3 v;void main(){n=normalize(normalMatrix*normal);vec4 mv=modelViewMatrix*vec4(position,1.);v=-mv.xyz;gl_Position=projectionMatrix*mv;}',
    fragmentShader: 'varying vec3 n;varying vec3 v;void main(){float r=pow(1.-abs(dot(normalize(n),normalize(v))),3.);gl_FragColor=vec4(vec3(.035,.045,.065)+vec3(.30,.40,.52)*r*.5,1.);}' })));
}

// ---------------------------------------------------------------- chats, outcomes, lobes, links
type Node = { id: string; chat: Chat; pos: any; core: any; halo: any; mass: number; outs: { o: Outcome; pos: any; s: any }[]; lines: any };
const nodes: Node[] = [], lobeGlows: { domain: string; s: any; pos: any }[] = [], linkLines: { a: string; b: string; line: any; link: Link }[] = [];
const world = new T.Group(); scene.add(world);
for (const [id, chat] of Object.entries(data.chats)) {
  const d = dir(chat.direction), pos = brainPoint(d, chat.side, .03), mass = chat.mapped ? (chat.human || 0) + (chat.ai || 0) : 0;
  const R = chat.mapped ? somaRadius(mass) : .02, core = chat.mapped ? sprite(new T.Color(), R * 3.2) : sprite(new T.Color(UNMAPPED), .05, .5, ringTex), halo = sprite(new T.Color(), R * 8, chat.mapped ? .34 : 0);
  core.position.copy(pos); halo.position.copy(pos); world.add(halo, core);
  // the chat's own graph: outcomes on its tangent plane, linked to their parent
  const outs: Node['outs'] = [], seg: number[] = [], up = Math.abs(d.y) > .95 ? new T.Vector3(1, 0, 0) : new T.Vector3(0, 1, 0), u = up.clone().sub(d.clone().multiplyScalar(up.dot(d))).normalize(), w = new T.Vector3().crossVectors(d, u);
  const rootO = chat.outcomes.find(o => o.root), kids = chat.outcomes.filter(o => !o.root), ext = Math.max(1, ...kids.map(o => Math.hypot(o.x - (rootO?.x || 0), o.y - (rootO?.y || 0))));
  const reach = .07 + .05 * Math.cbrt(Math.max(1, mass / 100)), at = new Map<string, any>(); if (rootO) at.set(rootO.id, pos);
  for (const o of kids) { const dx = (o.x - (rootO?.x || 0)) / ext * reach, dy = -(o.y - (rootO?.y || 0)) / ext * reach, od = d.clone().addScaledVector(w, -chat.side * dx).addScaledVector(u, dy).normalize(), op = brainPoint(od, chat.side, .028); at.set(o.id, op);
    const m = o.human + o.ai, s = sprite(new T.Color(), .022 + .03 * Math.sqrt(m / Math.max(1, mass)), .95); s.position.copy(op); world.add(s); outs.push({ o, pos: op, s }) }
  for (const { o, pos: op } of outs) { const from = at.get(o.parent || '') || pos; seg.push(from.x, from.y, from.z, op.x, op.y, op.z) }
  const lg = new T.BufferGeometry(); lg.setAttribute('position', new T.Float32BufferAttribute(seg, 3));
  const lines = new T.LineSegments(lg, new T.LineBasicMaterial({ color: '#cfd9e4', transparent: true, opacity: .32, depthWrite: false, blending: T.AdditiveBlending })); world.add(lines);
  nodes.push({ id, chat, pos, core, halo, mass, outs, lines });
}
for (const dm of data.domains) for (const side of [-1, 1]) { const pos = brainPoint(dir(dm.direction), side, .05), s = sprite(new T.Color(), 1, 0); s.position.copy(pos); world.add(s); lobeGlows.push({ domain: dm.id, s, pos }) }
const byId = new Map(nodes.map(n => [n.id, n]));
for (const l of data.links) { const A = byId.get(l.a), B = byId.get(l.b); if (!A || !B) continue;
  const mid = A.pos.clone().add(B.pos).multiplyScalar(.5), lift = mid.clone().normalize().multiplyScalar(mid.length() + .22 + .35 * A.pos.distanceTo(B.pos));
  const pts = new T.QuadraticBezierCurve3(A.pos, lift, B.pos).getPoints(40), g = new T.BufferGeometry().setFromPoints(pts);
  const line = new T.Line(g, new T.LineBasicMaterial({ color: l.type === 'continued' ? '#ffffff' : l.type === 'reused' ? '#dbe4ee' : '#9fb2c6', transparent: true, opacity: l.type === 'continued' ? .55 : l.type === 'reused' ? .42 : .3, depthWrite: false, blending: T.AdditiveBlending }));
  world.add(line); linkLines.push({ a: l.a, b: l.b, line, link: l }) }

// Lobe labels (always): the 8 universal domains, named the same for everyone.
const domainStats = new Map<string, { chats: number; human: number; ai: number }>();
for (const n of nodes) { const s = domainStats.get(n.chat.domain) || { chats: 0, human: 0, ai: 0 }; s.chats++; s.human += n.chat.human || 0; s.ai += n.chat.ai || 0; domainStats.set(n.chat.domain, s) }
const lobeLabels = data.domains.filter(dm => domainStats.get(dm.id)).map(dm => { const el = document.createElement('div'); el.className = 'v2-lobe'; labelsEl.appendChild(el); return { dm, el } });

function paint() {
  const maxMass = Math.max(1, ...[...domainStats.values()].map(s => s.human + s.ai));
  for (const n of nodes) {
    const c = lens === 'who' ? whoColor(n.chat.mapped ? n.chat.share : null) : new T.Color(TOPIC[n.chat.domain] || TOPIC.other);
    n.core.material.color.copy(n.chat.mapped || lens === 'topics' ? c : new T.Color(UNMAPPED)); n.halo.material.color.copy(c);
    n.halo.material.opacity = n.chat.mapped ? .5 : lens === 'topics' ? .25 : 0; if (!n.chat.mapped) n.halo.scale.setScalar(.12);
    for (const { o, s } of n.outs) { const m = o.human + o.ai; s.material.color.copy(lens === 'who' ? whoColor(m ? o.human / m : null) : new T.Color(TOPIC[n.chat.domain])) }
  }
  for (const g of lobeGlows) { const st = domainStats.get(g.domain);
    if (!st) { g.s.material.opacity = 0; continue }
    const mass = st.human + st.ai, share = mass ? st.human / mass : null;
    g.s.material.color.copy(lens === 'who' ? whoColor(share) : new T.Color(TOPIC[g.domain])); g.s.scale.setScalar(1.3 + 1.3 * Math.sqrt(Math.max(st.chats / 14, mass / maxMass)));
    g.s.material.opacity = lens === 'who' ? (share === null ? 0 : .2 + .14 * Math.sqrt(mass / maxMass)) : .22 }
  for (const { dm, el } of lobeLabels) { const st = domainStats.get(dm.id)!, mass = st.human + st.ai;
    el.innerHTML = `<b>${dm.name}</b><span>${st.chats} chat${st.chats === 1 ? '' : 's'}${lens === 'who' && mass ? ' · ' + whoLabel(st.human / mass) : ''}</span>`;
    el.style.setProperty('--lobe', lens === 'topics' ? TOPIC[dm.id] : 'var(--color-text-secondary)') }
  const legend = root.querySelector('.v2-legend')!, p = PALETTES[palette];
  legend.innerHTML = lens === 'who'
    ? [[p.human, 'Human-led (you did ≥ 60%)'], [CO, 'Co-created (40–60%)'], [p.ai, 'AI-led (AI did ≥ 60%)'], [UNMAPPED, 'Not mapped yet']].map(([c, t]) => `<li><i style="background:${c}"></i>${t}</li>`).join('')
    : data.domains.filter(dm => domainStats.get(dm.id)).map(dm => `<li><i style="background:${TOPIC[dm.id]}"></i>${dm.name}</li>`).join('');
  root.querySelector<HTMLElement>('.v2-balance .you')!.style.background = p.human; root.querySelector<HTMLElement>('.v2-balance .ai')!.style.background = p.ai;
  root.querySelector<HTMLElement>('.you-text')!.style.color = p.human; root.querySelector<HTMLElement>('.ai-text')!.style.color = p.ai;
}

// ---------------------------------------------------------------- interaction
let selected: Node | null = null, hovered: Node | null = null, dragging = false, moved = false, last = { x: 0, y: 0 };
const opts = { outcomes: true, links: true };
const project = (p: any) => { const v = p.clone().project(camera); return { x: (v.x + 1) * canvas.clientWidth / 2, y: (1 - v.y) * canvas.clientHeight / 2, front: v.z < 1 } };
const facing = (p: any, min = -.05) => p.clone().sub(view.target).normalize().dot(camera.position.clone().sub(view.target).normalize()) > min;
function pick(x: number, y: number) { let best: Node | null = null, bd = 16; for (const n of nodes) { if (!facing(n.pos)) continue; const s = project(n.pos), d = Math.hypot(s.x - x, s.y - y); if (d < bd) { bd = d; best = n } } return best }
const esc = (s: unknown) => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]!));
const domainName = (id: string) => data.domains.find(d => d.id === id)?.name || 'Other';
function card(n: Node | null) {
  const el = root.querySelector<HTMLElement>('.v2-card')!; el.hidden = !n; if (!n) return;
  const c = n.chat, p = PALETTES[palette], you = c.share === null ? null : Math.round(c.share * 100), own = data.links.filter(l => l.a === n.id || l.b === n.id);
  el.innerHTML = `<button class="v2-close" aria-label="Close">×</button><span class="v2-eyebrow">${esc(domainName(c.domain))}${c.region ? ' · ' + esc(data.regions[c.region]?.name || '') : ''}</span><h2>${esc(c.title)}</h2>
   ${you === null ? `<p class="v2-note">Not mapped yet: the engine has not processed this chat. It is placed by its text; its colour and size come once it is mapped.</p>` :
    `<div class="v2-balance small"><span style="flex:${c.human};background:${p.human}"></span><span style="flex:${c.ai};background:${p.ai}"></span></div>
     <p class="v2-row"><b style="color:${p.human}">You ${you}%</b> · <b style="color:${p.ai}">AI ${100 - you}%</b> of the work · ${whoLabel(c.share)}</p>
     <p class="v2-row">${c.outcomes.filter(o => !o.root).length} outcomes · decisions: you ${c.decisions?.human ?? 0}, AI ${c.decisions?.ai ?? 0} · ${c.pairs} exchanges</p>`}
   <p class="v2-row muted">Topic: ${esc(domainName(c.domain))} (${esc(c.domainSource)}, keyword baseline: you can correct it)</p>
   <h3>Connections</h3>${own.length ? `<ul>${own.map(l => `<li><b>${esc(l.type)}</b> → ${esc(data.chats[l.a === n.id ? l.b : l.a].title)} <small>${esc(l.evidence.reason || (l.evidence.keywords || []).slice(0, 3).join(', '))}</small></li>`).join('')}</ul>` : '<p class="v2-note">None with evidence.</p>'}`;
  el.querySelector<HTMLButtonElement>('.v2-close')!.onclick = () => select(null);
}
function select(n: Node | null) { selected = n; card(n);
  if (n) { goal.target = n.pos.clone().multiplyScalar(.82); goal.radius = 4.4; const d = n.pos.clone().normalize(); goal.theta = Math.atan2(d.x, d.z); goal.phi = Math.acos(Math.max(-.85, Math.min(.85, d.y))) }
  else { goal.target = new T.Vector3(0, -.12, 0); goal.radius = 8.6 } }
canvas.addEventListener('pointerdown', e => { dragging = true; moved = false; last = { x: e.clientX, y: e.clientY }; canvas.setPointerCapture(e.pointerId) });
canvas.addEventListener('pointermove', e => {
  const r = canvas.getBoundingClientRect(), tip = root.querySelector<HTMLElement>('.v2-tip')!;
  if (dragging) { const dx = e.clientX - last.x, dy = e.clientY - last.y; if (Math.hypot(dx, dy) > 2) moved = true; goal.theta -= dx * .006; goal.phi = Math.max(.25, Math.min(Math.PI - .25, goal.phi - dy * .005)); last = { x: e.clientX, y: e.clientY }; tip.hidden = true; return }
  hovered = pick(e.clientX - r.left, e.clientY - r.top); canvas.style.cursor = hovered ? 'pointer' : 'grab'; tip.hidden = !hovered;
  if (hovered) { const c = hovered.chat, you = c.share === null ? null : Math.round(c.share * 100); tip.innerHTML = `<b>${esc(c.title)}</b><span>${you === null ? 'not mapped yet' : `you ${you}% · AI ${100 - you}% · ${whoLabel(c.share)}`}</span>`; tip.style.left = Math.min(r.width - 260, e.clientX - r.left + 14) + 'px'; tip.style.top = (e.clientY - r.top + 14) + 'px' } });
canvas.addEventListener('pointerup', e => { dragging = false; if (!moved) { const r = canvas.getBoundingClientRect(); select(pick(e.clientX - r.left, e.clientY - r.top)) } });
canvas.addEventListener('wheel', e => { e.preventDefault(); goal.radius = Math.max(2.4, Math.min(13, goal.radius * Math.exp(e.deltaY * .0011))) }, { passive: false });
root.querySelectorAll<HTMLButtonElement>('[data-lens]').forEach(b => b.onclick = () => { lens = b.dataset.lens as 'who' | 'topics'; root.querySelectorAll('[data-lens]').forEach(x => x.setAttribute('aria-pressed', String(x === b))); paint() });
root.querySelector<HTMLInputElement>('[data-opt="outcomes"]')!.onchange = e => { opts.outcomes = (e.target as HTMLInputElement).checked };
root.querySelector<HTMLInputElement>('[data-opt="links"]')!.onchange = e => { opts.links = (e.target as HTMLInputElement).checked };
root.querySelector<HTMLSelectElement>('[data-opt="palette"]')!.onchange = e => { palette = (e.target as HTMLSelectElement).value; paint(); card(selected) };
addEventListener('keydown', e => { if (e.key === 'Escape') select(null) });

// ---------------------------------------------------------------- loop
function resize() { const w = canvas.clientWidth, h = canvas.clientHeight; renderer.setSize(w, h, false); camera.aspect = w / Math.max(1, h); camera.updateProjectionMatrix() }
addEventListener('resize', resize); resize(); paint();
let frames = 0;
function frame_(t: number) {
  requestAnimationFrame(frame_); frames++;
  const k = .12; view.theta += (goal.theta - view.theta) * k; view.phi += (goal.phi - view.phi) * k; view.radius += (goal.radius - view.radius) * k; view.target.lerp(goal.target, k);
  camera.position.set(view.radius * Math.sin(view.phi) * Math.sin(view.theta), view.radius * Math.cos(view.phi), view.radius * Math.sin(view.phi) * Math.cos(view.theta)).add(view.target); camera.lookAt(view.target);
  const pulse = .5 + .5 * Math.sin(t / 900);
  for (const n of nodes) { const focus = !selected || selected === n, show = opts.outcomes && n.chat.mapped;
    n.core.material.opacity = focus ? 1 : .35; n.halo.material.opacity = n.chat.mapped ? (focus ? (selected === n ? .42 + .18 * pulse : .34) : .1) : n.halo.material.opacity;
    for (const { s } of n.outs) { s.visible = show; s.material.opacity = focus ? .95 : .25 } n.lines.visible = show; n.lines.material.opacity = focus ? (selected === n ? .6 : .3) : .08 }
  for (const l of linkLines) { l.line.visible = opts.links && (!selected || l.a === selected.id || l.b === selected.id) }
  for (const { dm, el } of lobeLabels) { const sides = [-1, 1].map(s => brainPoint(dir(dm.direction), s, .16)), best = sides.find(p => facing(p, .3)); if (!best || selected) { el.hidden = true; continue }
    const s = project(best); el.hidden = false; el.style.left = s.x + 'px'; el.style.top = s.y + 'px' }
  renderer.render(scene, camera);
}
requestAnimationFrame(frame_);
(window as unknown as { brainV2: unknown }).brainV2 = { select: (id: string | null) => select(id ? byId.get(id) || null : null), setLens: (l: 'who' | 'topics') => (root.querySelector(`[data-lens="${l}"]`) as HTMLButtonElement)?.click(), frames: () => frames,
  view: (theta: number, phi: number, radius: number) => Object.assign(goal, { theta, phi, radius }) };
