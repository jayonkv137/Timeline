const { chromium } = require('playwright');
const path = require('node:path');
const fs = require('node:fs');
const { pathToFileURL } = require('node:url');

function getChromePath() {
  if (process.env.CHROME_PATH) return process.env.CHROME_PATH;
  const macChrome = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  if (fs.existsSync(macChrome)) return macChrome;
  return undefined;
}

function quantile(arr, q) {
  if (arr.length === 0) return 0;
  const sorted = [...arr].sort((a, b) => a - b);
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  if (sorted[base + 1] !== undefined) {
    return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
  }
  return sorted[base];
}

(async () => {
  const chromePath = getChromePath();
  const launchOptions = {
    executablePath: chromePath,
    args: chromePath ? ['--no-sandbox', '--headless=new', '--use-gl=angle'] : ['--no-sandbox', '--use-angle=swiftshader'],
  };

  const browser = await chromium.launch(launchOptions);
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const url = process.env.WORKSPACE_URL || pathToFileURL(path.resolve('web/cotrace-workspace.html')).href;

  // 1. Measure First Load Time
  const loadStart = performance.now();
  await page.goto(url);
  await page.waitForSelector('.conversation-scroll');
  await page.waitForSelector('.context-panel .obsidian-graph canvas');
  const firstLoadMs = performance.now() - loadStart;

  // Allow layout and initial state to stabilize
  await page.waitForTimeout(200);

  // 2. Measure Chat Switch Latency (repeat 6 times between open tabs)
  const switchTimes = [];
  const tabs = ['Human–AI interaction design', 'AI creativity · paper research'];
  for (let i = 0; i < 6; i++) {
    const target = tabs[i % 2];
    const t0 = performance.now();
    await page.getByRole('tab', { name: target, exact: true }).click();
    await page.waitForSelector('.conversation-scroll');
    const elapsed = performance.now() - t0;
    switchTimes.push(elapsed);
    await page.waitForTimeout(60);
  }

  // 3. Measure Brain FPS
  await page.getByRole('tab', { name: 'Brain', exact: true }).click();
  await page.waitForTimeout(1500);
  const frame = page.frames().find(f => f !== page.mainFrame());
  let brainFps = 0;
  if (frame) {
    const sample1 = await frame.evaluate(() => ({
      frames: window.cotraceBrain?.getState()?.frames || 0,
      t: performance.now(),
    }));
    await page.waitForTimeout(1200);
    const sample2 = await frame.evaluate(() => ({
      frames: window.cotraceBrain?.getState()?.frames || 0,
      t: performance.now(),
    }));
    const dt = (sample2.t - sample1.t) / 1000;
    const df = sample2.frames - sample1.frames;
    brainFps = dt > 0 ? df / dt : 0;
  }

  await browser.close();

  const result = {
    firstLoadMs: Math.round(firstLoadMs * 10) / 10,
    chatOpenMs: {
      samples: switchTimes.map(t => Math.round(t * 10) / 10),
      mean: Math.round((switchTimes.reduce((a, b) => a + b, 0) / switchTimes.length) * 10) / 10,
      p50: Math.round(quantile(switchTimes, 0.5) * 10) / 10,
      p95: Math.round(quantile(switchTimes, 0.95) * 10) / 10,
    },
    brainFps: Math.round(brainFps * 10) / 10,
  };

  console.log(JSON.stringify(result));
})().catch(err => {
  console.error(err);
  process.exit(1);
});
