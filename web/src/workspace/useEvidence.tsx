// Evidence inspection (docs/EVIDENCE_SPEC.md §5): click a requirement or question → the chat reveals the exact
// words that support it, in the right speaker's message → step through every source → Back to reading.
// Inspection never changes the graph's viewed exchange; chat→graph following pauses while it is open.
import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react';
import type { MutableRefObject } from 'react';
import { ChevronLeft, ChevronRight, CornerDownLeft, X } from 'lucide-react';
import type { Atom, Chat, Evidence } from './types';
import { clearPaint, companions, defaultEvidence, paint, resolveOnPage, roleLabel, who } from './evidence';
import './evidence.css';

export interface Inspect { chatId: string; atomId: string; index: number; nonce: number }
type ReturnPoint = { chatId: string; scrollTop: number };
export type Resolution = { found: number; total: number; occurrences: number; companionFound: boolean };

export function useEvidence(opts: {
  chat: Chat | undefined;
  viewPair: number;
  scroll: MutableRefObject<HTMLDivElement | null>;
  lockUntil: MutableRefObject<number>;
}) {
  const { chat, viewPair, scroll, lockUntil } = opts;
  const [inspect, setInspect] = useState<Inspect | null>(null);
  const [resolution, setResolution] = useState<Resolution | null>(null);
  const returnTo = useRef<ReturnPoint | null>(null);
  const outlined = useRef<HTMLElement[]>([]);

  const atom: Atom | undefined = inspect && chat && inspect.chatId === chat.id ? chat.atoms.find(a => a.id === inspect.atomId) : undefined;
  const evidence: Evidence[] = atom?.evidence || [];
  const current = inspect ? evidence[inspect.index] : undefined;

  /** Select an item and reveal its source. Keeps the first reading position so Back to reading returns there. */
  const open = useCallback((chatId: string, atomId: string, a?: Atom, pair?: number) => {
    if (!returnTo.current || returnTo.current.chatId !== chatId) returnTo.current = { chatId, scrollTop: scroll.current?.scrollTop ?? 0 };
    setInspect(prev => {
      if (prev && prev.chatId === chatId && prev.atomId === atomId) return { ...prev, nonce: prev.nonce + 1 }; // same item again: bring it back into view
      const idx = a ? defaultEvidence(a, pair ?? viewPair) : 0;
      return { chatId, atomId, index: Math.max(0, idx), nonce: 0 };
    });
  }, [scroll, viewPair]);

  const clearOutline = () => { outlined.current.forEach(el => el.classList.remove('evidence-message', 'evidence-arrive')); outlined.current = []; };

  /** ✕ / Escape: stop inspecting, stay where you are. */
  const close = useCallback(() => {
    setInspect(null); setResolution(null); clearPaint(); clearOutline();
    returnTo.current = null; lockUntil.current = 0;
  }, [lockUntil]);

  /** Back to reading: restore where you were before the first click. */
  const back = useCallback(() => {
    const r = returnTo.current;
    setInspect(null); setResolution(null); clearPaint(); clearOutline();
    returnTo.current = null;
    if (r && scroll.current) {
      lockUntil.current = performance.now() + 400; // the graph stays put while we restore
      scroll.current.scrollTo({ top: r.scrollTop, behavior: 'instant' as ScrollBehavior });
    }
  }, [lockUntil, scroll]);

  const step = useCallback((d: number) => setInspect(p => {
    if (!p) return p;
    const n = evidence.length;
    return n ? { ...p, index: (p.index + d + n) % n, nonce: p.nonce + 1 } : p;
  }), [evidence.length]);

  // Switching chats ends inspection.
  useEffect(() => { if (inspect && chat && inspect.chatId !== chat.id) close(); }, [chat, inspect, close]);

  // Escape closes; arrows step when the strip is in use.
  useEffect(() => {
    if (!inspect) return;
    const key = (e: KeyboardEvent) => { if (e.key === 'Escape') { e.stopPropagation(); close(); } };
    window.addEventListener('keydown', key, true);
    return () => window.removeEventListener('keydown', key, true);
  }, [inspect, close]);

  // Resolve on the page, paint, scroll only when needed.
  useLayoutEffect(() => {
    clearPaint(); clearOutline();
    const doc = scroll.current;
    if (!inspect || !atom || !current || !doc) { if (!inspect) setResolution(null); return; }
    lockUntil.current = 1e12; // pause chat→graph following while inspecting
    const shown = [inspect.index, ...companions(atom, inspect.index)];
    const human: Range[] = [], ai: Range[] = [];
    let main = { message: null as HTMLElement | null, ranges: [] as Range[], found: 0, occurrences: 0 }, companionFound = false;
    for (const i of shown) {
      const e = evidence[i];
      const res = resolveOnPage(doc, e);
      (e.speaker === 'human' ? human : ai).push(...res.ranges);
      if (res.message) { res.message.classList.add('evidence-message'); outlined.current.push(res.message); }
      if (i === inspect.index) main = res; else if (res.found) companionFound = true;
    }
    paint({ human, ai }, doc.querySelector<HTMLElement>('.conversation-document'));
    setResolution({ found: main.found, total: current.fragments.length, occurrences: main.occurrences, companionFound });
    // Scroll to the passage (or its message when the exact words are unavailable), only if it is not comfortably in view.
    const target = main.ranges[0] ?? main.message;
    if (!target) return;
    const box = target.getBoundingClientRect(), view = doc.getBoundingClientRect();
    const top = box.top - view.top, comfortable = top >= view.height * 0.1 && top + Math.min(box.height, view.height * 0.5) <= view.height * 0.82;
    if (!comfortable || inspect.nonce > 0) {
      const dest = doc.scrollTop + top - view.height * 0.28;
      const far = Math.abs(dest - doc.scrollTop) > view.height * 2.5;
      const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
      doc.scrollTo({ top: Math.max(0, dest), behavior: (reduced || far ? 'instant' : 'smooth') as ScrollBehavior });
    }
    if (main.message && !matchMedia('(prefers-reduced-motion: reduce)').matches) {
      main.message.classList.add('evidence-arrive');
      const m = main.message; setTimeout(() => m.classList.remove('evidence-arrive'), 900);
    }
  }, [inspect, atom, current, evidence, scroll, lockUntil]);

  useEffect(() => () => { clearPaint(); }, []);

  return { inspect, atom, evidence, current, resolution, open, close, back, step };
}

/** The temporary strip above the composer while a source is shown (spec §5.4, §5.5). */
export function EvidenceStrip({ atom, evidence, index, resolution, onStep, onBack, onClose }: {
  atom: Atom; evidence: Evidence[]; index: number; resolution: Resolution | null;
  onStep: (d: number) => void; onBack: () => void; onClose: () => void;
}) {
  const e = evidence[index];
  if (!e) {
    return <div className="evidence-strip" role="status"><span className="evidence-state">Source not linked yet</span>
      <span className="evidence-actions"><button className="text-button" onClick={onBack}><CornerDownLeft size={13} />Back to reading</button><button className="icon-button" aria-label="Close evidence" onClick={onClose}><X size={14} /></button></span></div>;
  }
  const pairWith = companions(atom, index).map(i => evidence[i]).filter(Boolean);
  const kind = e.speaker === 'human' ? 'human' : e.speaker === 'ai' ? 'ai' : 'none';
  let state = '';
  if (e.match === 'missing') state = 'Source not linked yet';
  else if (e.match === 'message') state = 'Exact passage unavailable · showing the message' + (e.note ? ` · ${e.note}` : '');
  else if (resolution && resolution.found === 0) state = 'Exact passage not found on screen · showing the message';
  else if (resolution && resolution.found < resolution.total) state = `${resolution.found} of ${resolution.total} parts found`;
  const extras: string[] = [];
  if (e.match === 'multipart' && !state) extras.push(`${e.fragments.length} parts`);
  if ((resolution?.occurrences ?? e.occurrences ?? 0) > 1) extras.push(`phrase appears ${resolution?.occurrences ?? e.occurrences}× here`);
  if (atom.kind !== 'question' && evidence.filter(x => x.role === 'introduced' || x.role === 'answered').length > 1 && (e.role === 'introduced' || e.role === 'answered')) extras.push(`based on ${evidence.filter(x => x.role === e.role).length} passages`);
  const qState = atom.kind === 'question' ? (atom.state === 'open' ? 'Still open' : atom.state === 'dropped' ? `Dropped at exchange ${atom.droppedAt ?? '?'}, no answer` : '') : '';
  return <div className={'evidence-strip ' + kind} role="status" aria-live="polite">
    <span className="evidence-what">
      <b className={'evidence-chip ' + kind}>{roleLabel(e, atom)}</b>
      <span>{who(e)}{e.pair != null ? ` · exchange ${e.pair}` : ''}</span>
      {pairWith.length > 0 && <span className="evidence-pair">→ {roleLabel(pairWith[0], atom)} {who(pairWith[0])}{pairWith[0].pair != null ? ` · exchange ${pairWith[0].pair}` : ''}</span>}
      {qState && <span className="evidence-state">{qState}</span>}
      {state && <span className="evidence-state">{state}</span>}
      {extras.length > 0 && <span className="evidence-extra">{extras.join(' · ')}</span>}
    </span>
    <span className="evidence-actions">
      {evidence.length > 1 && <><button className="icon-button" aria-label="Previous source" onClick={() => onStep(-1)}><ChevronLeft size={15} /></button>
        <span className="evidence-count">{index + 1} of {evidence.length}</span>
        <button className="icon-button" aria-label="Next source" onClick={() => onStep(1)}><ChevronRight size={15} /></button></>}
      <button className="text-button" onClick={onBack}><CornerDownLeft size={13} />Back to reading</button>
      <button className="icon-button" aria-label="Close evidence (Escape)" onClick={onClose}><X size={14} /></button>
    </span>
  </div>;
}
