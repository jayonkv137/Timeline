import { useId } from 'react';

/** Symbiot mark: a human ring and an AI ring, interlocked like chain links (AI over at the top,
 *  human over at the bottom), with one shared brain between them.
 *  Rings use the party tokens; the brain uses currentColor so it follows the theme. */
const BRAIN = 'M32 9.2C28.6 8.6 25.6 9.6 24.4 12C21.4 12.4 19.8 15 20.4 17.8C18.6 19.6 18.4 22.6 19.8 24.6C18.8 27 19.4 30 21.6 31.4C21.8 34.4 24.2 36.6 27.2 36.6C28.6 38.4 30.4 38.9 32 38.6ZM32 9.2C35.4 8.6 38.4 9.6 39.6 12C42.6 12.4 44.2 15 43.6 17.8C45.4 19.6 45.6 22.6 44.2 24.6C45.2 27 44.6 30 42.4 31.4C42.2 34.4 39.8 36.6 36.8 36.6C35.4 38.4 33.6 38.9 32 38.6Z';
const FISSURE = 'M32 9.6C31.1 13.6 32.9 17.8 32 22C31.1 26.2 32.9 30.4 32 38.4';
const SULCI = [
  'M30 12.6C27 12.8 25 15 26.9 17.4', 'M22.9 20.4C25.6 20 28.1 21.6 27.5 24.4C27.1 26.3 28.4 27.8 30.3 27.9', 'M23.9 31.2C26.3 30.4 28.8 32 28.5 34.6',
  'M34 12.6C37 12.8 39 15 37.1 17.4', 'M41.1 20.4C38.4 20 35.9 21.6 36.5 24.4C36.9 26.3 35.6 27.8 33.7 27.9', 'M40.1 31.2C37.7 30.4 35.2 32 35.5 34.6',
];
const SCALE = 'translate(32 24) scale(0.84) translate(-32 -24)';

export function SymbiotMark({ className, title }: { className?: string; title?: string }) {
  const id = useId().replace(/:/g, '');
  return <svg className={className} viewBox="0 0 64 48" role={title ? 'img' : undefined} aria-hidden={title ? undefined : true} aria-label={title}>
    <defs>
      <mask id={`${id}-folds`} maskUnits="userSpaceOnUse" x="0" y="0" width="64" height="48">
        <rect width="64" height="48" fill="#fff"/>
        <g fill="none" stroke="#000" strokeWidth="1.25" strokeLinecap="round">
          <path d={FISSURE} strokeWidth="1.56"/>
          {SULCI.map(d => <path key={d} d={d}/>)}
        </g>
      </mask>
      <mask id={`${id}-halo`} maskUnits="userSpaceOnUse" x="0" y="0" width="64" height="48">
        <rect width="64" height="48" fill="#fff"/>
        <path d={BRAIN} transform={SCALE} fill="#000" stroke="#000" strokeWidth="4.29" strokeLinejoin="round"/>
      </mask>
      <clipPath id={`${id}-lock`}><circle cx="32" cy="39.73" r="5.4"/></clipPath>
    </defs>
    <g mask={`url(#${id}-halo)`} fill="none" strokeWidth="3.6">
      <circle cx="23.25" cy="24" r="18" style={{ stroke: 'var(--human)' }}/>
      <circle cx="40.75" cy="24" r="18" style={{ stroke: 'var(--ai)' }}/>
      <circle cx="23.25" cy="24" r="18" style={{ stroke: 'var(--human)' }} clipPath={`url(#${id}-lock)`}/>
    </g>
    <path d={BRAIN} transform={SCALE} fill="currentColor" mask={`url(#${id}-folds)`}/>
  </svg>;
}
