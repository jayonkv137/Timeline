// Evidence linking e2e (docs/EVIDENCE_SPEC.md §8): click a requirement or question → exact words highlighted in the
// right speaker's message → step sources → Back to reading → Escape. The graph never moves while inspecting.
// Uses the keyboard path (the graph's requirement list), so it works on production builds too.
// WORKSPACE_URL: the running workspace (server URL, or a dev/packaged page with ?offline=1).
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH || undefined, args: ['--no-sandbox', '--use-angle=swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  const url = process.env.WORKSPACE_URL || pathToFileURL(path.join(__dirname, '../../web/cotrace-workspace.html')).href + '?offline=1';
  await page.goto(url); await page.waitForSelector('.chat-list-item');
  await page.locator('.chat-list-item', { hasText: 'AI creativity' }).click();
  await page.waitForSelector('.og-atom-list button');
  const graphPair = () => page.locator('.context-panel .obsidian-graph').getAttribute('data-pair');
  const strip = () => page.locator('.evidence-strip').innerText();
  const highlights = name => page.evaluate(n => { const h = CSS.highlights.get(n); return h ? [...h].map(r => r.toString()) : []; }, name);
  const scrollTop = () => page.locator('.conversation-scroll').evaluate(el => el.scrollTop);
  assert.equal(await graphPair(), '7', 'opens at the latest exchange');
  const reading = await scrollTop();

  // 1. A requirement you revised: the default source is the revision that supports the version shown at exchange 7.
  await page.locator('.og-atom-list button', { hasText: 'The search for research papers must target papers related to AI creativity' }).first().focus();
  await page.keyboard.press('Enter');
  await page.waitForSelector('.evidence-strip');
  assert.match(await strip(), /Revised[\s\S]*by you · exchange 3/);
  const revised = await highlights('evidence-human');
  assert.equal(revised.length, 1); assert.match(revised[0], /also siilar to the desklling/, 'the exact (typo-preserving) words are highlighted');
  assert.equal(await graphPair(), '7', 'inspecting never changes the graph');

  // 2. Step to the first source: the engine quote is not in the message → honest state, no highlight.
  await page.getByRole('button', { name: 'Previous source' }).click();
  assert.match(await strip(), /Introduced[\s\S]*Exact passage unavailable/);
  assert.equal((await highlights('evidence-human')).length + (await highlights('evidence-ai')).length, 0, 'nothing is painted when the passage cannot be found');

  // 3. Back to reading restores the reading position and clears everything.
  await page.getByRole('button', { name: /Back to reading/ }).click();
  assert.equal(await page.locator('.evidence-strip').count(), 0);
  assert.ok(Math.abs((await scrollTop()) - reading) < 4, 'returns to where you were reading');
  assert.equal(await page.evaluate(() => CSS.highlights.size), 0);

  // 4. An answered question shows both halves at once: asked by the AI (orange) → answered by you (blue).
  await page.locator('.og-atom-list button', { hasText: /^Answered by you/ }).first().focus();
  await page.keyboard.press('Enter');
  await page.waitForSelector('.evidence-strip');
  assert.match(await strip(), /Asked[\s\S]*by the AI · exchange 1[\s\S]*Answered by you · exchange 2/);
  assert.ok((await highlights('evidence-ai')).some(t => t.includes("Pick those two and I'll go find actual papers")));
  assert.ok((await highlights('evidence-human')).some(t => t.includes('Both — I want the presentation to bridge them')));
  assert.equal(await graphPair(), '7');

  // 5. Escape closes and leaves you where you are.
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('.evidence-strip').count(), 0);
  assert.equal(await page.evaluate(() => CSS.highlights.size), 0);

  assert.deepEqual(errors, []);
  console.log('PASS evidence: revised source, honest unavailable state, back to reading, asked→answered pair, escape, graph never moves, no errors.');
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
