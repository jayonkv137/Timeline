// Evidence anchoring in the rendered transcript (docs/EVIDENCE_SPEC.md §4, §6).
// The engine already anchored every quote on the raw message text. The transcript renders markdown (bold, code,
// headings are stripped), so we re-find each fragment in the text the user actually sees, using the SAME
// normalisation as engine/evidence.py `norm_map` (keep the two identical), then disambiguate repeats with the
// W3C prefix/suffix context. Highlights use the CSS Custom Highlight API (no DOM mutation); a positioned overlay
// is the fallback. Nothing fuzzy is ever painted as exact: a fragment we cannot find is reported, not guessed.
import type { Atom, Evidence, EvidenceFragment } from './types';

const REPLACE: Record<string, string> = { '’': "'", '‘': "'", '“': '"', '”': '"', '—': '-', '–': '-', ' ': ' ' };
const SKIP = new Set(['*', '_', '`', '#', '>']);

type Pos = { node: Text; offset: number } | null;
export interface TextMap { norm: string; at: Pos[] }

function push(norm: string[], at: Pos[], raw: string, pos: Pos, state: { space: boolean }) {
  let ch = REPLACE[raw] ?? raw;
  if (SKIP.has(ch)) return;
  if (/\s/.test(ch)) {
    if (state.space || !norm.length) return;
    ch = ' '; state.space = true;
  } else state.space = false;
  for (const low of ch.toLowerCase()) { norm.push(low); at.push(pos); }
}

/** Same algorithm as engine/evidence.py norm_map, on a plain string. */
export function normalize(text: string): string {
  const norm: string[] = [], at: Pos[] = [], st = { space: false };
  for (const ch of text) push(norm, at, ch, null, st);
  while (norm.length && norm[norm.length - 1] === ' ') norm.pop();
  return norm.join('');
}

/** Visible text of one rendered message, normalised, with every character mapped back to its DOM text node. */
export function buildTextMap(root: HTMLElement): TextMap {
  const norm: string[] = [], at: Pos[] = [], st = { space: false };
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let lastBlock: Element | null = null;
  for (let n = walker.nextNode() as Text | null; n; n = walker.nextNode() as Text | null) {
    const block = n.parentElement?.closest('p,h1,h2,h3,h4,pre,li,blockquote,td') ?? null;
    if (lastBlock && block !== lastBlock) push(norm, at, ' ', null, st); // paragraph breaks read as a space, as in the raw text
    lastBlock = block;
    const t = n.data;
    for (let i = 0; i < t.length; i++) push(norm, at, t[i], { node: n, offset: i }, st);
  }
  while (norm.length && norm[norm.length - 1] === ' ') { norm.pop(); at.pop(); }
  return { norm: norm.join(''), at };
}

function contextScore(map: TextMap, start: number, end: number, prefix: string, suffix: string): number {
  let s = 0;
  for (let i = 1; i <= prefix.length && start - i >= 0 && map.norm[start - i] === prefix[prefix.length - i]; i++) s++;
  for (let i = 0; i < suffix.length && end + i < map.norm.length && map.norm[end + i] === suffix[i]; i++) s++;
  return s;
}

/** Locate one engine fragment in the rendered text; returns normalised [start, end) or null (never a guess). */
export function locate(map: TextMap, frag: EvidenceFragment): { start: number; end: number; occurrences: number } | null {
  const q = normalize(frag.exact);
  if (!q) return null;
  const hits: number[] = [];
  for (let i = map.norm.indexOf(q); i >= 0; i = map.norm.indexOf(q, i + 1)) hits.push(i);
  if (!hits.length) return null;
  const pre = normalize(frag.prefix), suf = normalize(frag.suffix);
  let best = hits[0], bestScore = -1;
  for (const h of hits) { const sc = contextScore(map, h, h + q.length, pre, suf); if (sc > bestScore) { best = h; bestScore = sc; } }
  return { start: best, end: best + q.length, occurrences: hits.length };
}

export function toRange(map: TextMap, start: number, end: number): Range | null {
  let s = start, e = end - 1;
  while (s < end && !map.at[s]) s++;
  while (e >= s && !map.at[e]) e--;
  const a = map.at[s], b = map.at[e];
  if (!a || !b) return null;
  const r = document.createRange();
  r.setStart(a.node, a.offset);
  r.setEnd(b.node, b.offset + 1);
  return r;
}

// ---- which source opens first (spec §5.2) ------------------------------------------------------------------

/** Index of the evidence that supports the version of `atom` shown at exchange `pair`. */
export function defaultEvidence(atom: Atom, pair: number): number {
  const ev = atom.evidence || [];
  if (!ev.length) return -1;
  if (atom.kind !== 'question') {
    let rev = -1;
    ev.forEach((e, i) => { if (e.role === 'revised' && e.pair != null && e.pair <= pair) rev = i; });
    if (rev >= 0) return rev;
  }
  const first = ev.findIndex(e => e.role === 'asked' || e.role === 'introduced' || e.role === 'answered');
  return first >= 0 ? first : 0;
}

/** For an answered question, the other half of the pair (asked ↔ answered), shown together with it. */
export function companions(atom: Atom, index: number): number[] {
  const ev = atom.evidence || [], cur = ev[index];
  if (!cur || (cur.role !== 'asked' && cur.role !== 'answered')) return [];
  const other = cur.role === 'asked' ? 'answered' : 'asked';
  return ev.map((e, i) => (e.role === other ? i : -1)).filter(i => i >= 0);
}

// ---- wording (spec §5.1, §5.5) ---------------------------------------------------------------------------

const ROLE: Record<string, string> = { introduced: 'Introduced', revised: 'Revised', 'carried-out': 'Carried out', asked: 'Asked', answered: 'Answered' };
export function roleLabel(e: Evidence, atom: Atom): string {
  if (e.role === 'answered' && atom.kind !== 'question' && atom.kind !== 'resolved') return 'Introduced';
  return ROLE[e.role] || e.role;
}
export function who(e: Evidence): string { return e.speaker === 'human' ? 'by you' : e.speaker === 'ai' ? 'by the AI' : 'source unknown'; }

// ---- painting --------------------------------------------------------------------------------------------

const HL = typeof CSS !== 'undefined' && 'highlights' in CSS && typeof (window as any).Highlight === 'function';
let overlayLayer: HTMLElement | null = null;

export function paint(groups: { human: Range[]; ai: Range[] }, host: HTMLElement | null) {
  clearPaint();
  if (HL) {
    const reg = (CSS as any).highlights as Map<string, unknown>;
    const H = (window as any).Highlight;
    if (groups.human.length) reg.set('evidence-human', new H(...groups.human));
    if (groups.ai.length) reg.set('evidence-ai', new H(...groups.ai));
    return;
  }
  // Fallback: tint boxes positioned inside the scrolling document, under the text.
  if (!host) return;
  overlayLayer = document.createElement('div');
  overlayLayer.className = 'evidence-overlay-layer';
  const base = host.getBoundingClientRect();
  for (const [kind, ranges] of [['human', groups.human], ['ai', groups.ai]] as const) {
    for (const r of ranges) for (const rect of Array.from(r.getClientRects())) {
      const box = document.createElement('i');
      box.className = 'evidence-overlay ' + kind;
      Object.assign(box.style, { left: rect.left - base.left + 'px', top: rect.top - base.top + 'px', width: rect.width + 'px', height: rect.height + 'px' });
      overlayLayer.appendChild(box);
    }
  }
  host.appendChild(overlayLayer);
}

export function clearPaint() {
  if (HL) { const reg = (CSS as any).highlights as Map<string, unknown>; reg.delete('evidence-human'); reg.delete('evidence-ai'); }
  overlayLayer?.remove(); overlayLayer = null;
}

/** Find a message element and resolve every fragment of one evidence item on it. */
export function resolveOnPage(doc: HTMLElement, e: Evidence): { message: HTMLElement | null; ranges: Range[]; found: number; occurrences: number } {
  if (e.pair == null || !e.speaker) return { message: null, ranges: [], found: 0, occurrences: 0 };
  const message = doc.querySelector<HTMLElement>(`[data-pair="${e.pair}"] [data-speaker="${e.speaker === 'human' ? 'user' : 'ai'}"]`);
  const textEl = message?.querySelector<HTMLElement>('.message-text');
  if (!message || !textEl || !e.fragments.length) return { message, ranges: [], found: 0, occurrences: 0 };
  const map = buildTextMap(textEl);
  const ranges: Range[] = []; let occurrences = 0;
  for (const f of e.fragments) {
    const hit = locate(map, f);
    if (!hit) continue;
    occurrences = Math.max(occurrences, hit.occurrences);
    const r = toRange(map, hit.start, hit.end);
    if (r) ranges.push(r);
  }
  return { message, ranges, found: ranges.length, occurrences };
}
