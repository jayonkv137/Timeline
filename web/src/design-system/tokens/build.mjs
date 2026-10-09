#!/usr/bin/env node
/**
 * COTRACE token build (DDR-000c). No dependencies.
 *
 *   node web/src/design-system/tokens/build.mjs           build all outputs
 *   node web/src/design-system/tokens/build.mjs --check    fail if outputs are stale (for CI)
 *
 * Input:  tokens.json (W3C DTCG format, three tiers: primitive / semantic / component)
 * Output: tokens.css            CSS custom properties; dark default, [data-theme="light"] overrides
 *         tokens.ts             typed, resolved values for React and canvas code
 *         tokens.numeric.json   plain numbers and 0–1 RGB for WebGL / the 3D brain
 *         docs/DESIGN.md        agent-readable summary: generated frontmatter + DESIGN.body.md
 *
 * Naming: primitive.a.b → --p-a-b (discouraged in components) · semantic.a.b → --a-b · component.a.b → --a-b
 */
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../../../..');
const source = JSON.parse(readFileSync(join(here, 'tokens.json'), 'utf8'));
const check = process.argv.includes('--check');

// ---------- collect ----------
const tokens = new Map(); // path -> { type, value, light, description, status }
function walk(node, path, inheritedType, inheritedStatus) {
  if (!node || typeof node !== 'object') return;
  const type = node.$type || inheritedType;
  const status = node.$extensions?.['cotrace.status'] || inheritedStatus;
  if ('$value' in node) {
    tokens.set(path.join('.'), {
      type, value:node.$value, light:node.$extensions?.['cotrace.modes']?.light,
      description:node.$description || '', status:status || 'baseline',
    });
    return;
  }
  for (const [k, v] of Object.entries(node)) if (!k.startsWith('$')) walk(v, [...path, k], type, status);
}
for (const tier of ['primitive', 'semantic', 'component']) walk(source[tier], [tier], undefined, undefined);

// ---------- resolve aliases ----------
const ALIAS = /^\{([^}]+)\}$/;
function resolveValue(value, mode, seen = new Set()) {
  if (typeof value === 'string') {
    const m = value.match(ALIAS);
    if (!m) return value;
    const ref = m[1];
    if (seen.has(ref)) throw new Error(`Alias cycle at ${ref}`);
    const t = tokens.get(ref);
    if (!t) throw new Error(`Unknown alias {${ref}}`);
    const next = mode === 'light' && t.light !== undefined ? t.light : t.value;
    return resolveValue(next, mode, new Set([...seen, ref]));
  }
  if (Array.isArray(value)) return value.map(v => resolveValue(v, mode, seen));
  if (value && typeof value === 'object') return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, resolveValue(v, mode, seen)]));
  return value;
}
const resolved = new Map();
for (const [path, t] of tokens) {
  resolved.set(path, {
    ...t,
    dark:resolveValue(t.value, 'dark'),
    lightResolved:t.light !== undefined ? resolveValue(t.light, 'light') : undefined,
  });
}

// ---------- formatting ----------
const varName = path => {
  const [tier, ...rest] = path.split('.');
  return '--' + (tier === 'primitive' ? 'p-' : '') + rest.join('-');
};
const fontStack = arr => arr.map(f => (/\s/.test(f) && !f.includes('-apple') ? `"${f}"` : f)).join(', ');
function cssValue(type, v) {
  if (type === 'fontFamily') return fontStack(v);
  if (type === 'cubicBezier') return `cubic-bezier(${v.join(', ')})`;
  if (type === 'transition') return `${v.duration} ${cssValue('cubicBezier', v.timingFunction)}`;
  return String(v);
}

// ---------- tokens.css ----------
const darkLines = [], lightLines = [], forcedDarkLines = [], typeClasses = [];
for (const [path, t] of resolved) {
  if (t.type === 'typography') {
    const base = varName(path);
    const v = t.dark;
    darkLines.push(`  ${base}-family: ${fontStack(v.fontFamily)};`, `  ${base}-size: ${v.fontSize};`, `  ${base}-weight: ${v.fontWeight};`, `  ${base}-line-height: ${v.lineHeight};`, `  ${base}-tracking: ${v.letterSpacing};`);
    const cls = path.split('.').slice(1).join('-');
    typeClasses.push(`.${cls} { font-family: var(${base}-family); font-size: var(${base}-size); font-weight: var(${base}-weight); line-height: var(${base}-line-height); letter-spacing: var(${base}-tracking); }`);
    continue;
  }
  if (path.startsWith('primitive.color.candidate-pairs')) continue;
  darkLines.push(`  ${varName(path)}: ${cssValue(t.type, t.dark)};`);
  if (t.lightResolved !== undefined) {
    lightLines.push(`  ${varName(path)}: ${cssValue(t.type, t.lightResolved)};`);
    forcedDarkLines.push(`  ${varName(path)}: ${cssValue(t.type, t.dark)};`);
  }
}
// component tokens that alias semantic tokens must re-resolve in light mode too
for (const [path, t] of resolved) {
  if (t.type === 'typography' || t.lightResolved !== undefined || path.startsWith('primitive.')) continue;
  const lightValue = resolveValue(t.value, 'light');
  if (JSON.stringify(lightValue) !== JSON.stringify(t.dark)) {
    lightLines.push(`  ${varName(path)}: ${cssValue(t.type, lightValue)};`);
    forcedDarkLines.push(`  ${varName(path)}: ${cssValue(t.type, t.dark)};`);
  }
}
const header = `/* GENERATED by web/src/design-system/tokens/build.mjs from tokens.json — do not edit by hand.\n   COTRACE tokens v${source.$extensions['cotrace.version']}. Dark is the default theme; light is provisional. */\n`;
const css = `${header}
:root {
  color-scheme: dark;
${darkLines.join('\n')}
}

[data-theme="light"] {
  color-scheme: light;
${lightLines.join('\n')}
}

/* Scope class for surfaces that stay dark in every theme (graph stage, 3D brain). */
.theme-dark {
  color-scheme: dark;
${forcedDarkLines.join('\n')}
}

@media (prefers-reduced-motion: reduce) {
  :root { --p-duration-fast: 0ms; --p-duration-base: 0ms; --p-duration-slow: 0ms; --motion-feedback: 0ms linear; --motion-state: 0ms linear; --motion-arrive: 0ms linear; }
}

/* Text-role utility classes (semantic.type) */
${typeClasses.map(c => c.replace(/^\.type-/, '.type-')).join('\n')}
`;

// ---------- tokens.ts ----------
function nest(entries) {
  const root = {};
  for (const [path, value] of entries) {
    const parts = path.split('.');
    let o = root;
    for (let i = 0; i < parts.length - 1; i++) o = o[parts[i]] ??= {};
    o[parts[parts.length - 1]] = value;
  }
  return root;
}
const darkTree = nest([...resolved].map(([p, t]) => [p, t.dark]));
const lightTree = nest([...resolved].map(([p, t]) => [p, t.lightResolved !== undefined ? t.lightResolved : resolveValue(t.value, 'light')]));
const ts = `// GENERATED by web/src/design-system/tokens/build.mjs from tokens.json — do not edit by hand.
// COTRACE tokens v${source.$extensions['cotrace.version']}. Prefer CSS variables in stylesheets; use these in canvas/WebGL code.

export const tokens = ${JSON.stringify(darkTree, null, 2)} as const;

export const lightTokens = ${JSON.stringify(lightTree, null, 2)} as const;

export type Tokens = typeof tokens;

/** CSS variable for a token path, e.g. cssVar('semantic.color.text.primary') -> 'var(--color-text-primary)'. */
export function cssVar(path: string): string {
  const [tier, ...rest] = path.split('.');
  return \`var(--\${tier === 'primitive' ? 'p-' : ''}\${rest.join('-')})\`;
}

/** Resolved token tree for the active theme (reads [data-theme] on <html>). */
export function activeTokens(): typeof tokens {
  if (typeof document !== 'undefined' && document.documentElement.dataset.theme === 'light') return lightTokens as unknown as typeof tokens;
  return tokens;
}
`;

// ---------- tokens.numeric.json ----------
function toNumeric(type, v) {
  if (type === 'color' && typeof v === 'string') {
    let r, g, b, a = 1;
    const hex = v.match(/^#([0-9a-f]{6})$/i);
    const rgba = v.match(/^rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?\s*\)$/i);
    if (hex) { const n = parseInt(hex[1], 16); r = (n >> 16) & 255; g = (n >> 8) & 255; b = n & 255; }
    else if (rgba) { [r, g, b] = rgba.slice(1, 4).map(Number); a = rgba[4] !== undefined ? Number(rgba[4]) : 1; }
    else return v;
    return { hex:'#' + [r, g, b].map(x => Math.round(x).toString(16).padStart(2, '0')).join(''), rgb:[r / 255, g / 255, b / 255].map(x => +x.toFixed(4)), alpha:a };
  }
  if (typeof v === 'string' && /^-?[\d.]+px$/.test(v)) return parseFloat(v);
  if (typeof v === 'string' && /^-?[\d.]+ms$/.test(v)) return parseFloat(v);
  return v;
}
const numeric = nest([...resolved].filter(([, t]) => t.type !== 'typography').map(([p, t]) => [p, toNumeric(t.type, t.dark)]));
const numericJson = JSON.stringify({ version:source.$extensions['cotrace.version'], units:'px and ms as numbers; colours as hex + 0–1 rgb + alpha', tokens:numeric }, null, 2) + '\n';

// ---------- DESIGN.md (ui-craft / Stitch format: frontmatter + six sections) ----------
const pick = p => resolved.get(p)?.dark;
const hexOf = v => (typeof v === 'string' ? v : '');
const fm = [];
fm.push('---', `name: COTRACE`, `description: Human × AI co-creation map — design tokens v${source.$extensions['cotrace.version']} (generated; edit tokens.json)`, 'colors:');
const colorKeys = [
  ['canvas', 'semantic.color.bg.canvas'], ['app', 'semantic.color.bg.app'], ['graph-stage', 'semantic.color.bg.graph'],
  ['panel', 'semantic.color.surface.panel'], ['raised', 'semantic.color.surface.raised'], ['hover', 'semantic.color.surface.hover'],
  ['border', 'semantic.color.border.default'], ['border-subtle', 'semantic.color.border.subtle'],
  ['text', 'semantic.color.text.primary'], ['text-secondary', 'semantic.color.text.secondary'], ['text-muted', 'semantic.color.text.muted'],
  ['human', 'semantic.color.party.human.solid'], ['human-text', 'semantic.color.party.human.text'],
  ['ai', 'semantic.color.party.ai.solid'], ['ai-text', 'semantic.color.party.ai.text'], ['focus', 'semantic.color.focus.ring'],
];
for (const [k, p] of colorKeys) fm.push(`  ${k}: "${hexOf(pick(p))}"`);
fm.push('typography:');
for (const role of ['display', 'heading', 'title', 'body', 'ui', 'label', 'caption', 'overline']) {
  const v = pick(`semantic.type.${role}`);
  fm.push(`  ${role}:`, `    fontFamily: "${fontStack(v.fontFamily).replace(/"/g, "'")}"`, `    fontSize: "${v.fontSize}"`, `    fontWeight: ${v.fontWeight}`, `    lineHeight: ${v.lineHeight}`, `    letterSpacing: "${v.letterSpacing}"`);
}
fm.push('rounded:');
for (const k of ['xs', 'sm', 'md', 'lg', 'xl', 'pill']) fm.push(`  ${k}: "${pick(`primitive.radius.${k}`)}"`);
fm.push('spacing:');
for (const k of ['1', '2', '3', '4', '5', '6', '8', '10']) fm.push(`  s${k}: "${pick(`primitive.space.${k}`)}"`);
fm.push('components:',
  '  button-icon:', '    backgroundColor: "transparent"', '    textColor: "{colors.text-muted}"', '    rounded: "{rounded.sm}"', '    size: "28px"',
  '  button-icon-hover:', '    backgroundColor: "{colors.hover}"', '    textColor: "{colors.text}"',
  '  message-user:', '    backgroundColor: "{colors.raised}"', '    textColor: "{colors.text}"', '    rounded: "{rounded.lg}"',
  '  scrubber-capsule:', `    backgroundColor: "${pick('semantic.color.surface.overlay')}"`, '    rounded: "{rounded.pill}"', '    height: "40px"',
  '---', '');
const bodyPath = join(repo, 'docs/design-system/DESIGN.body.md');
const body = existsSync(bodyPath) ? readFileSync(bodyPath, 'utf8') : '# Design System: COTRACE\n';
const designMd = fm.join('\n') + '<!-- GENERATED frontmatter from web/src/design-system/tokens/tokens.json; body from docs/design-system/DESIGN.body.md. Run build.mjs; do not edit here. -->\n\n' + body;

// ---------- write / check ----------
const outputs = [
  [join(here, 'tokens.css'), css],
  [join(here, 'tokens.ts'), ts],
  [join(here, 'tokens.numeric.json'), numericJson],
  [join(repo, 'docs/DESIGN.md'), designMd],
];
let stale = 0;
for (const [file, content] of outputs) {
  if (check) {
    const current = existsSync(file) ? readFileSync(file, 'utf8') : '';
    if (current !== content) { stale++; console.error(`stale: ${file}`); }
  } else writeFileSync(file, content);
}
const counts = { primitive:0, semantic:0, component:0 };
for (const p of tokens.keys()) counts[p.split('.')[0]]++;
if (check) { if (stale) process.exit(1); console.log('tokens up to date'); }
else console.log(`built ${tokens.size} tokens (primitive ${counts.primitive}, semantic ${counts.semantic}, component ${counts.component}) → tokens.css, tokens.ts, tokens.numeric.json, docs/DESIGN.md`);
