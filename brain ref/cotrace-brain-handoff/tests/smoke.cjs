const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROME_PATH || undefined,
    headless: true,
    args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'],
  });
  const page = await browser.newPage({ viewport: { width: 1024, height: 800 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  const url = pathToFileURL(path.join(__dirname, '../cotrace-brain-prototype.html')).href;
  await page.goto(url);
  await page.waitForFunction(() => window.cotraceBrain?.getState().frames > 8);
  assert.equal(await page.evaluate(() => cotraceBrain.getState().mode), 'base');
  await page.screenshot({ path: path.join(__dirname, '../docs/base.png'), fullPage: true });
  await page.click('[data-mode="map"]');
  await page.selectOption('.palette', 'rose');
  await page.waitForTimeout(300);
  const nodes = await page.evaluate(() => cotraceBrain.getProjectedNodes());
  assert(nodes.some(n => n.visible) && nodes.some(n => !n.visible), 'Front and back occlusion');
  const hit = nodes.find(n => n.id === 'visual');
  const box = await page.locator('canvas').boundingBox();
  await page.mouse.click(box.x + hit.x, box.y + hit.y);
  assert.equal(await page.evaluate(() => cotraceBrain.getState().selectedId), 'visual');
  await page.waitForTimeout(1100);
  await page.evaluate(() => cotraceBrain.setPair(3));
  assert.match(await page.locator('.atom-list').innerText(), /Open AI question/);
  assert.equal(await page.locator('.contributions').innerText(), 'Human 5\nAI 3');
  await page.evaluate(() => cotraceBrain.setPair(5));
  assert.match(await page.locator('.atom-list').innerText(), /Human-resolved/);
  await page.evaluate(() => {
    window.sourceEvents = [];
    document.getElementById('cotrace-brain').addEventListener('cotrace:open-source', e => sourceEvents.push(e.detail));
  });
  await page.locator('.atom-list button').first().click();
  await page.click('.source-button');
  const events = await page.evaluate(() => sourceEvents);
  assert.equal(events[0].atomId, 'a-neutral');
  assert.equal(events[1].source.turnId, 'turn-2');
  await page.evaluate(() => cotraceBrain.setPair(6));
  await page.screenshot({ path: path.join(__dirname, '../docs/selected.png'), fullPage: true });
  await page.selectOption('.node-list', 'test');
  await page.waitForTimeout(1700);
  assert.equal(await page.evaluate(() => cotraceBrain.getProjectedNodes().find(n => n.id === 'test').visible), true, 'Backside selection rotates into view');
  await page.evaluate(() => cotraceBrain.setPair(1));
  assert.equal(await page.locator('.node-list option').count(), 3, 'Only two born nodes plus prompt');
  assert.equal(await page.evaluate(() => cotraceBrain.getState().selectedId), null);
  assert.equal(await page.evaluate(() => cotraceBrain.selectNode('test')), false);
  assert.equal(await page.evaluate(() => {
    const before = cotraceBrain.getState().nodeCount;
    try { cotraceBrain.loadGraph({ version: 1, maxPair: 1, nodes: [{ id: 'broken' }], links: [] }); } catch {}
    return cotraceBrain.getState().nodeCount === before;
  }), true, 'Invalid replacement preserves existing graph');
  await page.click('.reset');
  assert.equal(await page.evaluate(() => cotraceBrain.getState().palette), 'neutral');
  assert.equal(await page.evaluate(() => cotraceBrain.getState().mode), 'base');
  for (const width of [390, 320]) {
    await page.setViewportSize({ width, height: 844 });
    await page.waitForTimeout(150);
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `No horizontal overflow at ${width}`);
  }
  await page.screenshot({ path: path.join(__dirname, '../docs/mobile.png'), fullPage: true });
  const reduced = await browser.newPage({ reducedMotion: 'reduce' });
  await reduced.goto(url);
  assert.equal(await reduced.evaluate(() => cotraceBrain.getState().surfaceMotion), false);
  await reduced.close();
  const beforeDispose = await page.evaluate(() => { cotraceBrain.dispose(); return cotraceBrain.getState().frames; });
  await page.waitForTimeout(180);
  assert.equal(await page.evaluate(() => cotraceBrain.getState().frames), beforeDispose, 'Dispose stops rendering');
  assert.deepEqual(errors, []);
  console.log('PASS: rendering, pointer selection, occlusion, backside focus, pair history, source events, invalid data, reset, responsive widths, reduced motion, cleanup.');
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
