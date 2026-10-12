import { useEffect, useRef, useState } from 'react';
import { Maximize2, Minimize2, LocateFixed } from 'lucide-react';
import type { Atom, Chat, ChatView, Outcome } from './types';
import './obsidian-graph.css';
import { tokens } from '../design-system/tokens/tokens';

/*
 * Right-panel conversation graph: a port of design_pack/playground_obsidian.html
 * (spring physics, draggable spheres, cursor-anchored zoom, dual-light spheres,
 * upper-canopy atoms, floating scrubber capsule, legend, chat-jump toast) fed by
 * the workspace Chat projection instead of all_chats_data.js. The top bar of the
 * playground is intentionally omitted.
 */

interface Props { chat:Chat; view:ChatView; expanded?:boolean; patch:(v:Partial<ChatView>)=>void; jump:(pair:number,speaker?:string,keepGraph?:boolean)=>void; expand:()=>void; locate:()=>void; inspect?:boolean; onAtom?:(atomId:string)=>void; activeAtom?:string|null; isMapping?:boolean; activeJob?:any; onTriggerMap?:()=>void; }

// Colours and geometry come from the design system (web/src/design-system/tokens). Canvas code reads
// resolved values from tokens.ts; stylesheets use the CSS variables.
const G = tokens.component.graph;
const USER = tokens.semantic.color.party.human.solid;
const AI = tokens.semantic.color.party.ai.solid;
const UNLINKED = tokens.semantic.color.text.muted; // no source action: shown as missing, never as a party
const BG = G.stage;
const WHITE = tokens.primitive.color.white;
const BLACK = tokens.primitive.color.black;
/** A token colour (#rrggbb) at the given alpha, for canvas gradients and glows. */
function rgbaOf(hex:string, alpha:number){
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${Math.max(0, Math.min(1, alpha)).toFixed(3)})`;
}

interface Sat { atom:Atom; group:'human'|'ai'|'question'; color:string; isHollowRing:boolean; isResolvedSlot:boolean; hidden?:boolean; currentX?:number; currentY?:number; currentR?:number }

/*
 * Bead rules (atoms around an outcome sphere)
 *  1. Screen-size marks: beads keep the same on-screen size at every zoom. Core 7px, open-question ring
 *     9px, resolved 10px ring with 5px core. Hit target is always at least 24px (WCAG 2.2 target size).
 *  2. One orbit, no spokes: beads sit on a faint track 7px outside the sphere; no line per bead.
 *  3. Even spacing: fixed 5px gap between beads, centred on 12 o'clock, growing left and right.
 *  4. Grouped by who: your beads on the left, AI beads on the right, open questions last, each group
 *     separated by a wider gap. The row itself reads as a who-did-what strip.
 *  5. Bounded: one row up to ~200 degrees, then a second orbit; anything beyond two rows collapses into
 *     a "+N" count. Hovering a bead enlarges it; dormant outcomes dim their beads.
 */
const BEAD = { core:G.bead.core, ring:G.bead.ring, resolvedOuter:G.bead['resolved-outer'], resolvedCore:G.bead['resolved-core'], gap:G.bead.gap, groupGap:G.bead['group-gap'], track:G.bead.track, rowGap:G.bead['row-gap'], maxArc:G.bead['max-arc-deg'] * Math.PI / 180 };
const MIX = new URLSearchParams(location.search).get('mix') === 'legacy' ? 'legacy' : 'ring';
interface SimNode { edgeR?:number; id:string; text:string; isRoot:boolean; x:number; y:number; vx:number; vy:number; radius:number; userScore:number; aiScore:number; isDormant:boolean; isTerminalActive:boolean; pinned:boolean; outcome:Outcome; satellites:Sat[] }
interface SimLink { source:string; target:string; type:'parent_child'|'related'; isDormant:boolean; length:number }
interface Tip { sat:Sat; x:number; y:number }
interface Toast { kind:'user'|'ai'|'neutral'; text:string; key:number }

// Node positions survive pair changes, tab switches and remounts within a session,
// so scrubbing never throws the layout around and a dragged node stays where it was put.
const positionMemory = new Map<string, Map<string, { x:number; y:number }>>();

function atomsAt(chat:Chat, nodeId:string, pair:number){
  return chat.atoms.filter(a => a.nodeId === nodeId && a.born <= pair && a.end > pair);
}

function buildFrame(chat:Chat, pair:number, spread:number){
  const snap = chat.snapshots[pair - 1];
  const memory = positionMemory.get(chat.id) || new Map<string, { x:number; y:number }>();
  positionMemory.set(chat.id, memory);
  const shown = chat.nodes.filter(n => n.born <= pair);
  const nodes:SimNode[] = shown.map(n => {
    const m = snap?.mass[n.id] || { human:0, ai:0, delta:0 };
    const total = m.human + m.ai;
    const remembered = memory.get(n.id);
    const seed = remembered || { x:n.root ? 0 : n.x * 1.6 * spread, y:n.root ? 0 : n.y * 1.6 * spread };
    const radius = n.root ? G.node['root-radius'] : G.node['radius-min'] + G.node['radius-range'] * Math.sqrt(Math.min(1, Math.max(total, 10) / G.node['mass-norm']));
    // Grouped by who decided it: yours, then the AI's, then open questions (rule 4).
    const canopy = atomsAt(chat, n.id, pair);
    const owner = (a:Atom) => a.kind === 'question' ? 'question' : (a.kind === 'resolved' ? a.resolver : a.origin) === 'human' ? 'human' : 'ai';
    const rank = { human:0, ai:1, question:2 } as const;
    const ordered = [...canopy].sort((a, b) => rank[owner(a)] - rank[owner(b)] || (a.kind === 'resolved' ? 1 : 0) - (b.kind === 'resolved' ? 1 : 0) || a.born - b.born);
    const satellites:Sat[] = n.root ? [] : ordered.map(atom => ({
      atom,
      group:owner(atom),
      // An item whose source the engine never linked is grey, never painted as anyone's (EVIDENCE_SPEC T3).
      color:(() => { const w = atom.kind === 'resolved' ? atom.resolver : atom.origin; return w === 'human' ? USER : w === 'ai' ? AI : UNLINKED; })(),
      isHollowRing:atom.kind === 'question',
      isResolvedSlot:atom.kind === 'resolved',
    }));
    return {
      id:n.id, text:n.title, isRoot:n.root, x:seed.x, y:seed.y, vx:0, vy:0, radius,
      userScore:m.human, aiScore:m.ai, isDormant:!n.root && m.delta === 0,
      isTerminalActive:!n.root && snap?.terminal === n.id, pinned:n.root, outcome:n, satellites,
    };
  });
  const byId = new Map(nodes.map(n => [n.id, n]));
  const links:SimLink[] = [];
  const seen = new Set<string>();
  for (const n of nodes) {
    const parent = n.outcome.parent ? byId.get(n.outcome.parent) : undefined;
    if (parent) links.push({ source:parent.id, target:n.id, type:'parent_child', isDormant:n.isDormant, length:G.physics['link-length'] * spread });
    for (const rid of n.outcome.related) {
      const other = byId.get(rid);
      const key = [rid, n.id].sort().join('|');
      if (other && !seen.has(key)) {
        seen.add(key);
        links.push({ source:n.id, target:rid, type:'related', isDormant:n.isDormant && other.isDormant, length:G.physics['related-length'] * spread });
      }
    }
  }
  return { nodes, links };
}

function badgeFor(chat:Chat, pair:number){
  const snap = chat.snapshots[pair - 1];
  const prev = chat.snapshots[pair - 2];
  if (!snap) return chat.status === 'processing' ? `Pair ${pair} · Mapping…` : `Pair ${pair} · Pending`;
  const children = chat.nodes.filter(n => !n.root && n.born <= pair);
  const massOf = (id:string, s = snap) => { const m = s?.mass[id]; return m ? m.human + m.ai : 0; };
  const childMass = children.reduce((sum, n) => sum + massOf(n.id), 0);
  const root = chat.nodes.find(n => n.root);
  const total = childMass > 0 ? childMass : (root ? massOf(root.id) : 0);
  let tag = 'Active Progression';
  if (pair === 1) tag = 'Genesis';
  else {
    const born = children.filter(n => n.born === pair);
    const reactivated = children.filter(n => n.born < pair && (snap.mass[n.id]?.delta || 0) > 0 && (prev?.mass[n.id]?.delta || 0) === 0);
    if (born.length) tag = `${born[0].id} Born`;
    else if (reactivated.length) tag = `${reactivated[0].id} Reactivated`;
    else if (snap.terminal) tag = `${snap.terminal} Surge`;
  }
  return `Pair ${pair} · Mass ${Math.round(total)} (${tag})`;
}

function tipHeader(s:Sat){
  const a = s.atom;
  if ((a.kind === 'resolved' ? a.resolver : a.origin) == null) return { title:'Source not linked', color:UNLINKED };
  if (a.kind === 'resolved') return { title:a.resolver === 'human' ? 'Human-Resolved' : 'AI-Resolved', color:a.resolver === 'human' ? USER : AI };
  if (a.kind === 'question') return { title:a.origin === 'human' ? 'Human Open Question' : 'AI Open Question', color:a.origin === 'human' ? USER : AI };
  return { title:a.origin === 'human' ? 'User Requirement' : 'AI Requirement', color:a.origin === 'human' ? USER : AI };
}

export function LocalGraph({ chat, view, expanded, patch, jump, expand, inspect, onAtom, activeAtom, isMapping, activeJob, onTriggerMap }:Props){
  const activeAtomRef = useRef<string|null|undefined>(activeAtom);
  activeAtomRef.current = activeAtom; // the requirement whose evidence is shown (EVIDENCE_SPEC §5.1): white ring, never a party colour
  const stageRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const sim = useRef<{ nodes:SimNode[]; links:SimLink[] }>({ nodes:[], links:[] });
  const cam = useRef({ zoom:view.zoom || 1, panX:view.pan.x, panY:view.pan.y });
  const pointer = useRef<{ dragNode:SimNode|null; panning:boolean; startX:number; startY:number; downX:number; downY:number; moved:boolean }>({ dragNode:null, panning:false, startX:0, startY:0, downX:0, downY:0, moved:false });
  const [size, setSize] = useState({ w:340, h:700 });
  const [tip, setTip] = useState<Tip|null>(null);
  const [toast, setToast] = useState<Toast|null>(null);
  const [cursor, setCursor] = useState('grab');
  const hoverSat = useRef<Sat|null>(null);
  const ghostNodeRef = useRef<{ x:number; y:number; r:number; nextPair:number }|null>(null);
  const latest = useRef({ view, patch, jump, inspect, chat, isMapping, activeJob, onTriggerMap });
  latest.current = { view, patch, jump, inspect, chat, isMapping, activeJob, onTriggerMap };

  const wide = size.w >= 1500; // room for the legend beside the centered capsule, as in the full-screen original
  const compact = size.w < 560;
  // Original spring lengths everywhere; narrow panels get a slightly smaller camera scale and a
  // boundary force (below) so the graph uses the panel's height instead of overflowing its width.
  const spread = 1;
  const wrap = compact ? 112 : 165;
  const rootWrap = compact ? 140 : 180;
  const reserve = compact ? 150 : wide ? 70 : 112; // space kept clear for legend, capsule and badge
  const geometry = useRef({ spread, wrap, rootWrap, w:size.w, h:size.h, reserve, top:52 });
  geometry.current = { spread, wrap, rootWrap, w:size.w, h:size.h, reserve, top:52 };
  // Camera: screen = C + pan + s * (world - B), with s = fit * zoom (fit depends on panel width).
  const view3 = useRef({ fit:1, bx:0, by:0 });

  function transform(){
    const g = geometry.current, v = view3.current;
    const s = v.fit * cam.current.zoom;
    return { s, bx:v.bx, by:v.by, cx:g.w / 2, cy:g.top + (g.h - g.top - g.reserve - 48) / 2 };
  }

  // Rebuild the frame when the pair or conversation changes, keeping remembered positions.
  useEffect(() => {
    const curDialogueMax = chat.dialogue?.length ? Math.max(...chat.dialogue.map(t => t.pair)) : 0;
    const curTotal = Math.max(chat.totalPairs || 0, curDialogueMax);
    if (!curTotal) { sim.current = { nodes:[], links:[] }; return; }
    const memory = positionMemory.get(chat.id);
    if (memory) for (const n of sim.current.nodes) memory.set(n.id, { x:n.x, y:n.y });
    sim.current = buildFrame(chat, Math.max(1, Math.min(curTotal, view.pair)), geometry.current.spread);
    setTip(null);
  }, [chat, view.pair]);

  useEffect(() => { setToast(null); cam.current = { zoom:view.zoom || 1, panX:view.pan.x, panY:view.pan.y }; }, [chat.id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const el = stageRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setSize({ w:el.clientWidth, h:el.clientHeight }));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 5000);
    return () => clearTimeout(t);
  }, [toast]);

  // Canvas sizing at device pixel ratio.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.round(size.w * dpr));
    canvas.height = Math.max(1, Math.round(size.h * dpr));
  }, [size]);

  // Physics + render loop (authentic playground mechanics).
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let frame = 0;
    const getNode = (id:string) => sim.current.nodes.find(n => n.id === id);

    function updatePhysics(){
      const { nodes, links } = sim.current;
      const springK = G.physics.spring;
      const repulsionK = G.physics.repulsion * geometry.current.spread * geometry.current.spread;
      const damping = G.physics.damping;
      const drag = pointer.current.dragNode;
      for (const link of links) {
        const u = getNode(link.source), v = getNode(link.target);
        if (!u || !v) continue;
        const dx = v.x - u.x, dy = v.y - u.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = (dist - link.length) * (link.type === 'parent_child' ? springK : springK * 0.5);
        const fx = (dx / dist) * force, fy = (dy / dist) * force;
        if (!u.pinned && u !== drag) { u.vx += fx; u.vy += fy; }
        if (!v.pinned && v !== drag) { v.vx -= fx; v.vy -= fy; }
      }
      for (let i = 0; i < nodes.length; i++) {
        for (let j = i + 1; j < nodes.length; j++) {
          const a = nodes[i], b = nodes[j];
          const dx = b.x - a.x, dy = b.y - a.y;
          const distSq = dx * dx + dy * dy || 1;
          const dist = Math.sqrt(distSq);
          const force = repulsionK / (distSq + 400);
          const fx = (dx / dist) * force, fy = (dy / dist) * force;
          if (!a.pinned && a !== drag) { a.vx -= fx; a.vy -= fy; }
          if (!b.pinned && b !== drag) { b.vx += fx; b.vy += fy; }
        }
      }
      // Keep nodes inside the visible panel area (world units, independent of user pan/zoom).
      const g = geometry.current, sc = view3.current.fit;
      const hx = Math.max(60, (g.w - 2 * (g.wrap / 2 + 8)) / 2 / sc);
      const hy = Math.max(80, (g.h - g.top - g.reserve - 48) / 2 / sc);
      for (const n of nodes) {
        if (n.pinned || n === drag) continue;
        const lx = hx - n.radius, ly = hy - n.radius - 20;
        if (n.x > lx) n.vx -= (n.x - lx) * 0.02; else if (n.x < -lx) n.vx += (-lx - n.x) * 0.02;
        if (n.y > ly) n.vy -= (n.y - ly) * 0.02; else if (n.y < -ly) n.vy += (-ly - n.y) * 0.02;
      }
      for (const n of nodes) {
        if (n.pinned || n === drag) { n.vx = 0; n.vy = 0; continue; }
        if (!Number.isNaN(n.vx)) n.x += n.vx;
        if (!Number.isNaN(n.vy)) n.y += n.vy;
        n.vx *= damping; n.vy *= damping;
      }
    }

    function updateFit(){
      const v = view3.current;
      v.fit = Math.max(0.72, Math.min(1, geometry.current.w / 560));
      v.bx = 0; v.by = 0;
    }

    function drawClippedLine(x1:number, y1:number, r1:number, x2:number, y2:number, r2:number, dashed:boolean, stroke:string, width:number){
      const dx = x2 - x1, dy = y2 - y1;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (Number.isNaN(dist) || dist <= r1 + r2 || dist === 0) return;
      const ux = dx / dist, uy = dy / dist;
      ctx!.beginPath();
      ctx!.setLineDash(dashed ? [5, 5] : []);
      ctx!.moveTo(x1 + ux * r1, y1 + uy * r1);
      ctx!.lineTo(x2 - ux * r2, y2 - uy * r2);
      ctx!.strokeStyle = stroke;
      ctx!.lineWidth = width;
      ctx!.stroke();
      ctx!.setLineDash([]);
    }

    const labels:{ text:string; wx:number; wy:number; dy:number; maxWidth:number; lineHeight:number; opacity:number; isRoot:boolean }[] = [];
    function drawWrappedText(text:string, x:number, y:number, maxWidth:number, lineHeight:number, opacity:number, isRoot:boolean){
      if (opacity <= 0.05 && !isRoot) return;
      ctx!.font = `${isRoot ? '500 12.5px' : '400 11.5px'} -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif`;
      ctx!.textAlign = 'center';
      ctx!.textBaseline = 'top';
      ctx!.fillStyle = isRoot ? G.node['label-root'] : rgbaOf(G.node.label, opacity);
      ctx!.shadowColor = rgbaOf(BLACK, 0.95);
      ctx!.shadowBlur = 5;
      const words = text.split(' ');
      const lines:string[] = [];
      let line = words[0] || '';
      for (let i = 1; i < words.length; i++) {
        if (ctx!.measureText(line + ' ' + words[i]).width < maxWidth) line += ' ' + words[i];
        else { lines.push(line); line = words[i]; }
      }
      lines.push(line);
      lines.forEach((l, i) => ctx!.fillText(l, x, y + i * lineHeight));
      ctx!.shadowBlur = 0;
    }

    function drawRootNode(node:SimNode){
      const grad = ctx!.createRadialGradient(node.x, node.y, node.radius * 0.5, node.x, node.y, node.radius * 2.4);
      grad.addColorStop(0, rgbaOf(WHITE, 0.9));
      grad.addColorStop(0.5, rgbaOf(WHITE, 0.25));
      grad.addColorStop(1, rgbaOf(WHITE, 0));
      ctx!.fillStyle = grad;
      ctx!.beginPath(); ctx!.arc(node.x, node.y, node.radius * 2.4, 0, Math.PI * 2); ctx!.fill();
      ctx!.beginPath(); ctx!.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
      ctx!.fillStyle = WHITE; ctx!.shadowColor = rgbaOf(WHITE, 0.85); ctx!.shadowBlur = 14; ctx!.fill(); ctx!.shadowBlur = 0;
      ctx!.strokeStyle = rgbaOf(WHITE, 0.45); ctx!.lineWidth = 1;
      ctx!.beginPath(); ctx!.arc(node.x, node.y, node.radius * 1.55, 0, Math.PI * 2); ctx!.stroke();
      ctx!.strokeStyle = rgbaOf(WHITE, 0.22);
      ctx!.beginPath(); ctx!.arc(node.x, node.y, node.radius * 2.1, 0, Math.PI * 2); ctx!.stroke();
      labels.push({ text:node.text, wx:node.x, wy:node.y + node.radius * 2.1, dy:8, maxWidth:geometry.current.rootWrap, lineHeight:16, opacity:1, isRoot:true });
    }

    function drawChild(node:SimNode, now:number){
      const r = node.radius;
      const px = 1 / transform().s; // one screen pixel in world units
      const total = node.userScore + node.aiScore;
      const userRatio = total > 0 ? node.userScore / total : 0.5;
      const dim = node.isDormant ? 0.55 : 1;

      if (MIX === 'legacy') {
        const aiRatio = 1 - userRatio;
        const blue = ctx!.createRadialGradient(node.x - r * 0.4, node.y, 0, node.x, node.y, r * 1.9);
        blue.addColorStop(0, `rgba(56, 189, 248, ${(0.75 + userRatio * 0.25).toFixed(2)})`); blue.addColorStop(0.5, 'rgba(56, 189, 248, 0.32)'); blue.addColorStop(1, 'rgba(56, 189, 248, 0)');
        ctx!.fillStyle = blue; ctx!.beginPath(); ctx!.arc(node.x, node.y, r * 1.9, 0, Math.PI * 2); ctx!.fill();
        const orange = ctx!.createRadialGradient(node.x + r * 0.4, node.y, 0, node.x, node.y, r * 2.0);
        orange.addColorStop(0, `rgba(251, 146, 60, ${(0.80 + aiRatio * 0.25).toFixed(2)})`); orange.addColorStop(0.5, 'rgba(251, 146, 60, 0.38)'); orange.addColorStop(1, 'rgba(251, 146, 60, 0)');
        ctx!.fillStyle = orange; ctx!.beginPath(); ctx!.arc(node.x, node.y, r * 2.0, 0, Math.PI * 2); ctx!.fill();
        const body = ctx!.createLinearGradient(node.x - r, node.y, node.x + r, node.y);
        body.addColorStop(0, '#7dd3fc'); body.addColorStop(0.48, '#ffffff'); body.addColorStop(1, '#fdba74');
        ctx!.beginPath(); ctx!.arc(node.x, node.y, r, 0, Math.PI * 2);
        ctx!.fillStyle = body; ctx!.shadowColor = 'rgba(255, 255, 255, 0.5)'; ctx!.shadowBlur = 8; ctx!.fill(); ctx!.shadowBlur = 0;
        ctx!.strokeStyle = 'rgba(255, 255, 255, 0.55)'; ctx!.lineWidth = 1; ctx!.stroke();
      } else {
        // Frosted neutral sphere: identity and size only. A soft halo leans toward whoever carried more.
        const lean = Math.abs(userRatio - 0.5) * 2; // 0 = even, 1 = one party only
        const tint = userRatio >= 0.5 ? USER : AI;
        const halo = ctx!.createRadialGradient(node.x, node.y, r * 0.8, node.x, node.y, r * 1.9);
        halo.addColorStop(0, rgbaOf(tint, (0.10 + 0.22 * lean) * dim)); halo.addColorStop(1, rgbaOf(tint, 0));
        ctx!.fillStyle = halo; ctx!.beginPath(); ctx!.arc(node.x, node.y, r * 1.9, 0, Math.PI * 2); ctx!.fill();
        const body = ctx!.createRadialGradient(node.x - r * 0.35, node.y - r * 0.4, r * 0.1, node.x, node.y, r);
        body.addColorStop(0, rgbaOf(G.node['body-light'], 0.98 * dim + 0.02)); body.addColorStop(0.7, rgbaOf(G.node['body-mid'], 0.9 * dim + 0.05)); body.addColorStop(1, rgbaOf(G.node['body-edge'], 0.85 * dim + 0.05));
        ctx!.beginPath(); ctx!.arc(node.x, node.y, r, 0, Math.PI * 2); ctx!.fillStyle = body; ctx!.fill();
        // Contribution ring: arc length = share of measured influence. You clockwise from 12 o'clock, then the AI.
        const ring = G['share-ring'];
        const ringR = r + ring.offset * px, lw = ring.width * px, top = -Math.PI / 2, gapA = total > 0 && userRatio > 0 && userRatio < 1 ? Math.min(0.06, ring.gap * px / ringR) : 0;
        ctx!.lineCap = 'butt'; ctx!.lineWidth = lw;
        if (total > 0) {
          const split = top + Math.PI * 2 * userRatio;
          if (userRatio > 0) { ctx!.strokeStyle = USER; ctx!.globalAlpha = dim; ctx!.beginPath(); ctx!.arc(node.x, node.y, ringR, top + gapA, split - gapA); ctx!.stroke(); }
          if (userRatio < 1) { ctx!.strokeStyle = AI; ctx!.globalAlpha = dim; ctx!.beginPath(); ctx!.arc(node.x, node.y, ringR, split + gapA, top + Math.PI * 2 - gapA); ctx!.stroke(); }
          ctx!.globalAlpha = 1;
        } else {
          ctx!.strokeStyle = ring.unmeasured; ctx!.setLineDash([3 * px, 3 * px]);
          ctx!.beginPath(); ctx!.arc(node.x, node.y, ringR, 0, Math.PI * 2); ctx!.stroke(); ctx!.setLineDash([]);
        }
      }

      if (node.isTerminalActive) {
        // Focus is not a party, so it is drawn in white rather than borrowing the human or AI colour.
        const pulse = reduceMotion ? 0.5 : (Math.sin(now * 0.004) + 1) * 0.5;
        const beacon = r + (MIX === 'legacy' ? 4 : 7 * px) + pulse * 5 * px;
        ctx!.strokeStyle = MIX === 'legacy' ? `rgba(56, 189, 248, ${(0.6 - pulse * 0.4).toFixed(2)})` : rgbaOf(WHITE, 0.55 - pulse * 0.35);
        ctx!.lineWidth = 1.5 * px;
        ctx!.beginPath(); ctx!.arc(node.x, node.y, beacon, 0, Math.PI * 2); ctx!.stroke();
      }

      // Beads (rules 1-5): laid out in screen units so they never shrink into specks.
      const sats = node.satellites;
      let ringOuter = r + 4 * px;
      if (sats.length) {
        const sizeOf = (sat:Sat) => sat.isResolvedSlot ? BEAD.resolvedOuter : sat.isHollowRing ? BEAD.ring : BEAD.core;
        const rows:Sat[][] = [[]];
        let orbit = r / px + BEAD.track + BEAD.resolvedOuter + 3, used = 0, rowIndex = 0;
        sats.forEach(sat => { sat.hidden = false; });
        for (let i = 0; i < sats.length; i++) {
          const sat = sats[i], prev = sats[i - 1];
          const step = (sizeOf(sat) * 2 + (prev ? (prev.group !== sat.group ? BEAD.groupGap : BEAD.gap) : 0)) / orbit;
          if (used + step > BEAD.maxArc) {
            if (rowIndex === 1) { for (let j = i; j < sats.length; j++) sats[j].hidden = true; break; }
            rowIndex = 1; rows.push([]); used = 0; orbit += BEAD.rowGap;
          }
          rows[rowIndex].push(sat); used += step;
        }
        const hiddenCount = sats.filter(sat => sat.hidden).length;
        ringOuter = r + (BEAD.track + BEAD.resolvedOuter * 2 + 3 + (rows.length - 1) * BEAD.rowGap) * px;
        rows.forEach((row, ri) => {
          if (!row.length) return;
          const rowOrbit = (r / px + BEAD.track + BEAD.resolvedOuter + 3 + ri * BEAD.rowGap);
          const angles:number[] = []; let acc = 0;
          row.forEach((sat, i) => {
            const prev = row[i - 1];
            if (prev) acc += (sizeOf(prev) + sizeOf(sat) + (prev.group !== sat.group ? BEAD.groupGap : BEAD.gap)) / rowOrbit;
            angles.push(acc);
          });
          const spanA = acc, a0 = -Math.PI / 2 - spanA / 2, wr = rowOrbit * px;
          // faint track under the row
          ctx!.strokeStyle = G.bead['track-color']; ctx!.globalAlpha = dim; ctx!.lineWidth = 1 * px;
          ctx!.beginPath(); ctx!.arc(node.x, node.y, wr, a0 - 6 / rowOrbit, a0 + spanA + 6 / rowOrbit); ctx!.stroke(); ctx!.globalAlpha = 1;
          row.forEach((sat, i) => {
            const ang = a0 + angles[i];
            const sx = node.x + Math.cos(ang) * wr, sy = node.y + Math.sin(ang) * wr;
            const hovered = hoverSat.current === sat;
            const k = (hovered ? G.bead['hover-scale'] : 1) * px;
            sat.currentX = sx; sat.currentY = sy; sat.currentR = sizeOf(sat) * px;
            ctx!.globalAlpha = dim;
            if (sat.isHollowRing) {
              const breathe = reduceMotion ? 0 : (Math.sin(now * 0.004) + 1) * 0.35;
              ctx!.fillStyle = BG; ctx!.beginPath(); ctx!.arc(sx, sy, BEAD.ring * k, 0, Math.PI * 2); ctx!.fill();
              ctx!.strokeStyle = sat.color; ctx!.lineWidth = 1.75 * px;
              ctx!.beginPath(); ctx!.arc(sx, sy, (BEAD.ring + breathe) * k, 0, Math.PI * 2); ctx!.stroke();
            } else if (sat.isResolvedSlot) {
              ctx!.fillStyle = BG; ctx!.beginPath(); ctx!.arc(sx, sy, BEAD.resolvedOuter * k, 0, Math.PI * 2); ctx!.fill();
              ctx!.strokeStyle = AI; ctx!.lineWidth = 1.5 * px;
              ctx!.beginPath(); ctx!.arc(sx, sy, BEAD.resolvedOuter * k, 0, Math.PI * 2); ctx!.stroke();
              ctx!.fillStyle = sat.color; ctx!.beginPath(); ctx!.arc(sx, sy, BEAD.resolvedCore * k, 0, Math.PI * 2); ctx!.fill();
            } else {
              ctx!.fillStyle = sat.color; ctx!.beginPath(); ctx!.arc(sx, sy, BEAD.core * k, 0, Math.PI * 2); ctx!.fill();
            }
            if (activeAtomRef.current && sat.atom.id === activeAtomRef.current) {
              ctx!.globalAlpha = 1; ctx!.strokeStyle = WHITE; ctx!.lineWidth = 1.5 * px;
              ctx!.beginPath(); ctx!.arc(sx, sy, (BEAD.resolvedOuter + 3.5) * k, 0, Math.PI * 2); ctx!.stroke();
            }
            ctx!.globalAlpha = 1;
          });
          if (ri === rows.length - 1 && hiddenCount > 0) {
            const ang = a0 + spanA + (BEAD.gap + 10) / rowOrbit;
            labels.push({ text:`+${hiddenCount}`, wx:node.x + Math.cos(ang) * wr, wy:node.y + Math.sin(ang) * wr, dy:-6, maxWidth:40, lineHeight:12, opacity:0.75, isRoot:false });
          }
        });
      }

      // Tethers stop at the outermost visible ring so they never cut through the bead row.
      node.edgeR = MIX === 'legacy' ? r : ringOuter;
      const base = Math.min(Math.max((cam.current.zoom - 0.45) / 0.4, 0), 1);
      labels.push({ text:node.text, wx:node.x, wy:node.y + r, dy:MIX === 'legacy' ? 11 : 13, maxWidth:geometry.current.wrap, lineHeight:15, opacity:node.isDormant ? base * 0.6 : base, isRoot:false });
    }

    function render(now:number){
      const { w, h } = geometry.current;
      const dpr = window.devicePixelRatio || 1;
      const t = transform();
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx!.fillStyle = BG; ctx!.fillRect(0, 0, w, h);
      labels.length = 0;
      ctx!.save();
      ctx!.translate(t.cx + cam.current.panX, t.cy + cam.current.panY);
      ctx!.scale(t.s, t.s);
      ctx!.translate(-t.bx, -t.by);
      for (const link of sim.current.links) {
        const u = getNode(link.source), v = getNode(link.target);
        if (!u || !v) continue;
        const ur = u.edgeR || u.radius, vr = v.edgeR || v.radius;
        if (link.type === 'parent_child') {
          if (link.isDormant) drawClippedLine(u.x, u.y, ur, v.x, v.y, vr, false, G.link.dormant, G.link['width-dormant']);
          else drawClippedLine(u.x, u.y, ur, v.x, v.y, vr, false, G.link.active, G.link.width);
        } else {
          if (link.isDormant) drawClippedLine(u.x, u.y, ur, v.x, v.y, vr, true, G.link['related-dormant'], G.link['width-dormant']);
          else drawClippedLine(u.x, u.y, ur, v.x, v.y, vr, true, G.link.related, 1.2);
        }
      }
      for (const n of sim.current.nodes) { if (n.isRoot) drawRootNode(n); else drawChild(n, now); }

      // Synaptogenesis: when a new exchange turn exists or is mapping while an existing graph is visible
      const curChat = latest.current.chat;
      const curIsMapping = Boolean(latest.current.isMapping);
      const maxMapped = curChat.snapshots && curChat.snapshots.length > 0
        ? curChat.snapshots.length
        : (curChat.nodes && curChat.nodes.length > 0 ? Math.max(...curChat.nodes.map(n => n.born || 1)) : 0);
      const curDialogueMax = curChat.dialogue && curChat.dialogue.length > 0
        ? Math.max(...curChat.dialogue.map(t => t.pair))
        : 0;
      const curTotal = Math.max(curChat.totalPairs || 0, curDialogueMax);
      const isNascent = (curTotal > maxMapped || curIsMapping) && sim.current.nodes.length > 0;

      if (isNascent) {
        // Form directly branching from the centre root node
        const anchor = sim.current.nodes.find(n => n.isRoot) || sim.current.nodes[0];

        let targetAngle = 0.55;
        if (sim.current.nodes.length > 1) {
          const angles = sim.current.nodes
            .filter(n => !n.isRoot)
            .map(n => Math.atan2(n.y - anchor.y, n.x - anchor.x));
          if (angles.length > 0) {
            const maxAngle = Math.max(...angles);
            targetAngle = maxAngle + 0.65;
          }
        }
        const dist = 135;
        const floatY = Math.sin(now * 0.0022) * 5;
        const floatX = Math.cos(now * 0.0018) * 3;
        const gx = anchor.x + Math.cos(targetAngle) * dist + floatX;
        const gy = anchor.y + Math.sin(targetAngle) * dist + floatY;
        const gr = 15;
        const nextPairNum = maxMapped + 1;
        ghostNodeRef.current = { x: gx, y: gy, r: gr, nextPair: nextPairNum };

        // Animated flowing synaptic tether from centre node
        ctx!.save();
        ctx!.setLineDash([5, 5]);
        ctx!.lineDashOffset = -now * 0.016;
        const tetherGrad = ctx!.createLinearGradient(anchor.x, anchor.y, gx, gy);
        tetherGrad.addColorStop(0, rgbaOf(WHITE, 0.75));
        tetherGrad.addColorStop(1, rgbaOf(curIsMapping ? AI : USER, 0.65));
        ctx!.strokeStyle = tetherGrad;
        ctx!.lineWidth = 1.5;
        ctx!.beginPath();
        const midX = (anchor.x + gx) / 2;
        const midY = (anchor.y + gy) / 2 - 14;
        ctx!.moveTo(anchor.x, anchor.y);
        ctx!.quadraticCurveTo(midX, midY, gx, gy);
        ctx!.stroke();
        ctx!.restore();

        // Pulsing synaptic aura glow
        const breathe = Math.sin(now * 0.0035) * 3;
        const aura = ctx!.createRadialGradient(gx, gy, 2, gx, gy, gr + 12 + breathe);
        aura.addColorStop(0, rgbaOf(curIsMapping ? AI : USER, curIsMapping ? 0.25 : 0.12));
        aura.addColorStop(0.6, rgbaOf(curIsMapping ? AI : USER, curIsMapping ? 0.10 : 0.04));
        aura.addColorStop(1, 'rgba(0,0,0,0)');
        ctx!.fillStyle = aura;
        ctx!.beginPath();
        ctx!.arc(gx, gy, gr + 12 + breathe, 0, Math.PI * 2);
        ctx!.fill();

        // Frosted glass dark orb base
        ctx!.fillStyle = rgbaOf('#0f172a', 0.88);
        ctx!.beginPath();
        ctx!.arc(gx, gy, gr, 0, Math.PI * 2);
        ctx!.fill();

        // Perimeter dashed ring
        ctx!.save();
        ctx!.strokeStyle = curIsMapping ? rgbaOf(AI, 0.85) : rgbaOf(WHITE, 0.45);
        ctx!.lineWidth = 1.4;
        ctx!.setLineDash([3, 3]);
        ctx!.beginPath();
        ctx!.arc(gx, gy, gr, 0, Math.PI * 2);
        ctx!.stroke();
        ctx!.restore();

        // Dual orbiting particles (the circling thing: Sky = Human, Ember = AI)
        const orbitR = gr + 6.5;
        const ang = now * 0.003;
        const px1 = gx + Math.cos(ang) * orbitR;
        const py1 = gy + Math.sin(ang) * orbitR;
        ctx!.fillStyle = USER;
        ctx!.beginPath();
        ctx!.arc(px1, py1, 2.5, 0, Math.PI * 2);
        ctx!.fill();

        const px2 = gx + Math.cos(ang + Math.PI) * orbitR;
        const py2 = gy + Math.sin(ang + Math.PI) * orbitR;
        ctx!.fillStyle = AI;
        ctx!.beginPath();
        ctx!.arc(px2, py2, 2.5, 0, Math.PI * 2);
        ctx!.fill();

        // Core glowing spark
        ctx!.fillStyle = curIsMapping ? AI : rgbaOf(WHITE, 0.8);
        ctx!.beginPath();
        ctx!.arc(gx, gy, 2.5 + (curIsMapping ? Math.sin(now * 0.006) * 1 : 0), 0, Math.PI * 2);
        ctx!.fill();

        // Simple, clean label for nascent node
        const ghostLabelText = curIsMapping
          ? `✦ Synthesizing Pair ${nextPairNum}…`
          : `✦ Pair ${nextPairNum} Pending`;
        labels.push({
          text: ghostLabelText,
          wx: gx,
          wy: gy + gr,
          dy: 10,
          maxWidth: 140,
          lineHeight: 13,
          opacity: curIsMapping ? 0.9 : 0.7,
          isRoot: false
        });
      } else {
        ghostNodeRef.current = null;
      }
      ctx!.restore();
      // Labels at a constant, readable screen size.
      for (const l of labels) {
        const sx = t.cx + cam.current.panX + t.s * (l.wx - t.bx);
        const sy = t.cy + cam.current.panY + t.s * (l.wy - t.by) + l.dy;
        drawWrappedText(l.text, sx, sy, l.maxWidth, l.lineHeight, l.opacity, l.isRoot);
      }
    }

    const loop = (now:number) => {
      try { updatePhysics(); updateFit(); render(now); } catch (e) { console.error('Graph render error:', e); }
      frame = requestAnimationFrame(loop);
    };
    frame = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frame);
  }, []);

  // Wheel zoom anchored at the cursor (non-passive so the page doesn't scroll).
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let save:ReturnType<typeof setTimeout>|undefined;
    const onWheel = (e:WheelEvent) => {
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const factor = e.deltaY < 0 ? 1.08 : 0.92;
      const zoom = Math.min(Math.max(cam.current.zoom * factor, 0.4), 3.5);
      const t = transform();
      const mx = e.clientX - rect.left, my = e.clientY - rect.top;
      const wx = (mx - t.cx - cam.current.panX) / t.s + t.bx, wy = (my - t.cy - cam.current.panY) / t.s + t.by;
      const s2 = view3.current.fit * zoom;
      cam.current.panX = mx - t.cx - s2 * (wx - t.bx);
      cam.current.panY = my - t.cy - s2 * (wy - t.by);
      cam.current.zoom = zoom;
      clearTimeout(save);
      save = setTimeout(() => latest.current.patch({ zoom:cam.current.zoom, pan:{ x:cam.current.panX, y:cam.current.panY } }), 250);
    };
    canvas.addEventListener('wheel', onWheel, { passive:false });
    return () => { canvas.removeEventListener('wheel', onWheel); clearTimeout(save); };
  }, []);

  // Arrow keys scrub pairs, unless the user is typing or another graph instance is the visible one.
  useEffect(() => {
    const onKey = (e:KeyboardEvent) => {
      if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
      const t = e.target as HTMLElement | null;
      if (t && (t.closest('input, textarea, select, [contenteditable="true"]'))) return;
      if (!expanded && document.querySelector('.obsidian-graph.expanded')) return;
      if (!stageRef.current?.offsetParent) return;
      e.preventDefault();
      seek(latest.current.view.pair + (e.key === 'ArrowLeft' ? -1 : 1));
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [expanded]); // eslint-disable-line react-hooks/exhaustive-deps

  function seek(p:number){
    const { chat:c, patch:pt, jump:j, inspect:ins } = latest.current;
    const next = Math.max(1, Math.min(c.totalPairs, p));
    if (next === latest.current.view.pair) return;
    pt({ pair:next, selected:null });
    if (!ins) j(next);
  }

  function world(e:{ clientX:number; clientY:number }){
    const rect = canvasRef.current!.getBoundingClientRect();
    const t = transform();
    return {
      x:(e.clientX - rect.left - t.cx - cam.current.panX) / t.s + t.bx,
      y:(e.clientY - rect.top - t.cy - cam.current.panY) / t.s + t.by,
    };
  }
  function nodeAt(x:number, y:number){
    const s = transform().s;
    return sim.current.nodes.find(n => Math.hypot(n.x - x, n.y - y) <= n.radius + 8 / s) || null;
  }
  // Dev-only probe so the browser tests can click real beads (EVIDENCE_SPEC §8); never shipped in builds.
  useEffect(() => {
    if (!import.meta.env.DEV) return;
    (window as any).__cotraceBeads = () => {
      const rect = canvasRef.current?.getBoundingClientRect(); if (!rect) return [];
      const t = transform();
      return sim.current.nodes.flatMap(n => n.satellites.filter(s => !s.hidden && s.currentX !== undefined).map(s => ({
        id:s.atom.id, kind:s.atom.kind, x:rect.left + t.cx + cam.current.panX + (s.currentX! - t.bx) * t.s, y:rect.top + t.cy + cam.current.panY + (s.currentY! - t.by) * t.s })));
    };
  });

  function satAt(x:number, y:number){
    for (const n of sim.current.nodes) for (const s of n.satellites) {
      if (!s.hidden && s.currentX !== undefined && s.currentY !== undefined && Math.hypot(s.currentX - x, s.currentY - y) <= Math.max((s.currentR || 0), 12 / transform().s)) return s;
    }
    return null;
  }

  function onMouseDown(e:React.MouseEvent){
    const p = world(e);
    const node = nodeAt(p.x, p.y);
    const ptr = pointer.current;
    ptr.downX = e.clientX; ptr.downY = e.clientY; ptr.moved = false;
    if (node && !node.pinned) ptr.dragNode = node;
    else { ptr.panning = true; ptr.startX = e.clientX - cam.current.panX; ptr.startY = e.clientY - cam.current.panY; setCursor('grabbing'); }
  }

  useEffect(() => {
    const onMove = (e:MouseEvent) => {
      const ptr = pointer.current;
      if (!ptr.dragNode && !ptr.panning) return;
      if (Math.hypot(e.clientX - ptr.downX, e.clientY - ptr.downY) > 4) ptr.moved = true;
      if (ptr.dragNode) {
        const p = world(e);
        ptr.dragNode.x = p.x; ptr.dragNode.y = p.y; ptr.dragNode.vx = 0; ptr.dragNode.vy = 0;
      } else {
        cam.current.panX = e.clientX - ptr.startX;
        cam.current.panY = e.clientY - ptr.startY;
      }
    };
    const onUp = () => {
      const ptr = pointer.current;
      if (ptr.panning && ptr.moved) latest.current.patch({ zoom:cam.current.zoom, pan:{ x:cam.current.panX, y:cam.current.panY } });
      if (ptr.dragNode) {
        const memory = positionMemory.get(latest.current.chat.id);
        memory?.set(ptr.dragNode.id, { x:ptr.dragNode.x, y:ptr.dragNode.y });
      }
      ptr.dragNode = null; ptr.panning = false;
      setCursor('grab');
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
  }, []);

  function onHover(e:React.MouseEvent){
    if (pointer.current.dragNode || pointer.current.panning) return;
    const p = world(e);
    if (ghostNodeRef.current) {
      const g = ghostNodeRef.current;
      if (Math.hypot(p.x - g.x, p.y - g.y) <= g.r + 10) {
        setCursor('pointer');
        setTip(null);
        return;
      }
    }
    const s = satAt(p.x, p.y);
    const rect = stageRef.current!.getBoundingClientRect();
    hoverSat.current = s;
    if (s) { setTip({ sat:s, x:e.clientX - rect.left, y:e.clientY - rect.top }); setCursor('pointer'); return; }
    setTip(null);
    const n = nodeAt(p.x, p.y);
    setCursor(n ? (n.pinned ? 'pointer' : 'grab') : 'grab');
  }

  function onClick(e:React.MouseEvent){
    if (pointer.current.moved) return; // a drag or pan is not a click
    const p = world(e);
    if (ghostNodeRef.current) {
      const g = ghostNodeRef.current;
      if (Math.hypot(p.x - g.x, p.y - g.y) <= g.r + 10) {
        if (!isMapping && onTriggerMap) {
          onTriggerMap();
          setToast({ kind:'ai', text:`Mapping Pair ${g.nextPair}…`, key:Date.now() });
          return;
        }
      }
    }
    const s = satAt(p.x, p.y);
    if (s) {
      const a = s.atom;
      patch({ selected:a.nodeId });
      if (onAtom) onAtom(a.id); // evidence inspection: exact words in the chat, graph stays on this pair
      else if (!inspect) jump(a.sourcePair, a.sourceSpeaker ?? undefined, true); // plan B: chat moves, graph stays on this pair
      setToast({ kind:s.color === USER ? 'user' : 'ai', text:a.text, key:Date.now() });
      return;
    }
    const n = nodeAt(p.x, p.y);
    if (n) {
      patch({ selected:n.id });
      if (!inspect) jump(n.outcome.sourcePair, n.outcome.sourceSpeaker, true);
      setToast({ kind:'neutral', text:n.text, key:Date.now() });
    }
  }

  function fit(){
    cam.current = { zoom:1, panX:0, panY:0 };
    patch({ zoom:1, pan:{ x:0, y:0 } });
  }

  const curDialogueMax = chat.dialogue && chat.dialogue.length > 0
    ? Math.max(...chat.dialogue.map(t => t.pair))
    : 0;
  const total = Math.max(chat.totalPairs || 0, curDialogueMax);
  const maxMappedPair = chat.snapshots && chat.snapshots.length > 0
    ? chat.snapshots.length
    : (chat.nodes && chat.nodes.length > 0 ? Math.max(...chat.nodes.map(n => n.born || 1)) : 0);
  const pair = Math.max(1, Math.min(total || 1, view.pair));
  const fillPct = total <= 1 ? 100 : ((pair - 1) / (total - 1)) * 100;
  const trackWidth = Math.min(Math.max(140, Math.min(380, total * 54)), Math.max(120, size.w - (compact ? 110 : 330)));
  const badge = total ? badgeFor(chat, pair) : '';
  const accent = toast ? (toast.kind === 'user' ? USER : toast.kind === 'ai' ? AI : WHITE) : WHITE;
  const border = toast ? (toast.kind === 'user' ? rgbaOf(USER, 0.4) : toast.kind === 'ai' ? rgbaOf(AI, 0.45) : rgbaOf(WHITE, 0.25)) : '';

  // DOM-readable state for tests and assistive tech (the graph itself is a canvas).
  const shownCount = total ? chat.nodes.filter(n => n.born <= pair).length : 0;
  const atomKinds = total ? [...new Set(chat.atoms.filter(a => a.born <= pair && a.end > pair).map(a => a.kind))].join(',') : '';

  return <section className={'local-graph minimal-graph obsidian-graph theme-dark ' + (expanded ? 'expanded ' : '') + (wide ? 'og-wide' : compact ? 'og-compact' : 'og-medium')} aria-label="Conversation graph"
    data-pair={total ? pair : 0} data-node-count={shownCount} data-atom-kinds={atomKinds}>
    <div className="graph-stage og-stage" ref={stageRef} onMouseLeave={() => { setTip(null); hoverSat.current = null; }}>
      <canvas ref={canvasRef} className="og-canvas" style={{ cursor }} aria-label={total ? `Outcome graph at pair ${pair} of ${total}` : 'Outcome graph'}
        onMouseDown={onMouseDown} onMouseMove={onHover} onClick={onClick} />
      {onAtom && total > 0 && <div className="og-atom-list" role="group" aria-label={`Requirements and questions at pair ${pair}`}>
        {chat.atoms.filter(a => a.born <= pair && a.end > pair).map(a => {
          const w = a.kind === 'resolved' ? a.resolver : a.origin;
          const kind = a.kind === 'question' ? `${w === 'human' ? 'Your' : 'AI'} question` : a.kind === 'resolved' ? `Answered ${w === 'human' ? 'by you' : 'by AI'}` : `${w === 'human' ? 'Your' : w === 'ai' ? 'AI' : 'Unlinked'} requirement`;
          return <button key={a.id} type="button" aria-pressed={activeAtom === a.id} onClick={() => { patch({ selected:a.nodeId }); onAtom(a.id); }}>{kind}: {a.text}</button>;
        })}
      </div>}
      {!total && <div className="graph-empty"><p>{chat.status === 'processing' ? 'Mapping the first exchange…' : 'Your graph will appear after the first analyzed exchange.'}</p></div>}

      <div className="og-corner-tools">
        <button className="og-tool" aria-label="Recenter graph" title="Recenter graph" onClick={fit}><LocateFixed size={14} /></button>
        <button className="og-tool" aria-label={expanded ? 'Collapse graph' : 'Expand graph'} title={expanded ? 'Collapse graph' : 'Expand graph'} onClick={expand}>{expanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}</button>
      </div>

      {tip && (() => {
        const s = tip.sat, a = s.atom, head = tipHeader(s);
        const maxW = Math.min(320, size.w - 20);
        const left = Math.max(8, Math.min(tip.x + 14, size.w - maxW - 8));
        const isUser = a.kind === 'resolved' ? a.resolver === 'human' : a.origin === 'human';
        return <div className="og-tooltip" role="tooltip" style={{ left, top:Math.max(8, Math.min(tip.y + 10, size.h - 200)), maxWidth:maxW, borderColor:rgbaOf(isUser ? USER : AI, 0.4) }}>
          {a.kind === 'resolved' ? <>
            <div className="og-tip-row"><div className="og-tip-head" style={{ color:head.color }}>{head.title}</div><span className="og-tip-pill">{a.origin === 'human' ? 'From your question' : a.origin === 'ai' ? 'From AI question' : 'Question source not linked'}</span></div>
            {a.question && <div className="og-tip-question"><span>Question:</span> {a.question}</div>}
            {(a.quote || a.choices.length > 0) && <div className="og-tip-options">
              {a.quote && <div className="og-tip-chose" style={{ color:head.color }}>✓ {a.resolver === 'human' ? 'User Chose' : 'AI Chose'}: {a.quote}</div>}
              {a.choices.map((c, i) => <div key={i} className="og-tip-option">• {c}</div>)}
            </div>}
            <div className="og-tip-result">{a.text}</div>
          </> : <>
            <div className="og-tip-head" style={{ color:head.color }}>{head.title}</div>
            <div className={a.kind === 'question' ? 'og-tip-body strong' : 'og-tip-body'}>{a.text}</div>
            {a.kind === 'question' && a.choices.length > 0 && <div className="og-tip-choices">{a.choices.map((c, i) => <div key={i}>{c}</div>)}</div>}
          </>}
        </div>;
      })()}

      {toast && <div key={toast.key} className="og-toast" role="status" style={{ border:`1px solid ${border}`, boxShadow:`0 12px 32px ${rgbaOf(BLACK, 0.9)}, 0 0 20px ${rgbaOf(accent, 0.13)}` }}>
        <div className="og-toast-label"><div className="og-toast-dot" style={{ background:accent, boxShadow:`0 0 8px ${accent}` }} /><span style={{ color:accent }}>Chat Jump</span></div>
        <div className="og-toast-text">{toast.text}</div>
        <button className="og-toast-close" aria-label="Dismiss" onClick={() => setToast(null)}>✕</button>
      </div>}

      {total > 0 && <>
        {compact && <div className="og-badge og-badge-float"><div className="og-badge-dot" /><span>{badge}</span></div>}
        <div className="og-capsule">
          <button className="og-nav" disabled={pair <= 1} onClick={() => seek(pair - 1)} title="Previous Pair (Left Arrow)" aria-label="Previous pair">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="15 18 9 12 15 6" /></svg>
          </button>
          <div className="og-track" style={{ width:trackWidth }}>
            <div className="og-rail" />
            <div className="og-fill" style={{ transform:`scaleX(${fillPct / 100})` }} />
            <div className="og-notches">
              {Array.from({ length:total }, (_, i) => i + 1).map(i => {
                const isSynth = isMapping && i > maxMappedPair;
                const isUnmap = !isMapping && i > maxMappedPair;
                return (
                  <button
                    key={i}
                    type="button"
                    className={
                      'og-notch' +
                      (i <= pair ? ' active' : '') +
                      (i === pair ? ' current' : '') +
                      (isSynth ? ' synthesizing' : '') +
                      (isUnmap ? ' unmapped' : '')
                    }
                    onClick={() => seek(i)}
                    aria-label={`Pair ${i}`}
                    aria-current={i === pair ? 'step' : undefined}
                  >
                    <span className="og-notch-marker" />
                    <span className="og-notch-tag">P{i}</span>
                  </button>
                );
              })}
            </div>
          </div>
          <button className="og-nav" disabled={pair >= total} onClick={() => seek(pair + 1)} title="Next Pair (Right Arrow)" aria-label="Next pair">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"><polyline points="9 18 15 12 9 6" /></svg>
          </button>
          {!compact && <div className="og-badge"><div className="og-badge-dot" /><span>{badge}</span></div>}
        </div>

        {MIX === 'legacy' ? <div className="og-legend">
          <div className="og-hint"><div className="og-dot-u" /> User Req</div>
          <div className="og-hint"><div className="og-dot-a" /> AI Req</div>
          <div className="og-hint"><span className="og-ring-a" /> Open Question</div>
          <div className="og-hint"><span className="og-resolved"><span /></span> Resolved Slot</div>
          <div className="og-hint"><div className="og-line" /> Tether</div>
          <div className="og-hint"><span className="og-ring-u" /> Active Focus</div>
        </div> : <div className="og-legend">
          <div className="og-hint"><span className="og-share" /> Share ring</div>
          <div className="og-hint"><div className="og-dot-u" /> Your decision</div>
          <div className="og-hint"><div className="og-dot-a" /> AI decision</div>
          <div className="og-hint"><span className="og-ring-a" /> Open question</div>
          <div className="og-hint"><span className="og-resolved"><span /></span> Answered</div>
          <div className="og-hint"><span className="og-ring-w" /> Focus</div>
        </div>}
        {wide && <div className="og-controls-hint">Arrows (◀ / ▶) to scrub pairs &nbsp;|&nbsp; Drag canvas &nbsp;|&nbsp; Scroll zoom</div>}
      </>}
    </div>
  </section>;
}
