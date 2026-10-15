const { chromium } = require('playwright');
const path = require('node:path');

(async () => {
  console.log('Launching browser...');
  const browser = await chromium.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--enable-webgl', '--use-gl=angle']
  });

  // Target viewport: 1600x960 at deviceScaleFactor: 2 creates a 3200x1920 crisp Retina image
  const context = await browser.newContext({
    viewport: { width: 1600, height: 960 },
    deviceScaleFactor: 2,
    colorScheme: 'dark'
  });

  const page = await context.newPage();
  console.log('Navigating to http://localhost:8766...');
  await page.goto('http://localhost:8766', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  // 1. Close extra tabs so only the Brain tab is in the tab bar
  console.log('Closing chat tabs...');
  const closeTabs = page.locator('.close-tab');
  while (await closeTabs.count() > 0) {
    await closeTabs.first().click();
    await page.waitForTimeout(100);
  }

  // 2. Ensure sidebar is CLOSED
  const closeSidebarBtn = page.locator('button[aria-label="Close sidebar"]');
  if (await closeSidebarBtn.isVisible()) {
    console.log('Closing sidebar...');
    await closeSidebarBtn.click();
    await page.waitForTimeout(500);
  }

  // 3. Switch to Brain tab
  console.log('Switching to Brain tab...');
  const brainTab = page.locator('button.workspace-tab.brain-tab, button[role="tab"]:has-text("Brain")');
  if (await brainTab.isVisible()) {
    await brainTab.click();
  }
  await page.waitForTimeout(1500);

  // 4. In right panel, select "AI creativity · paper research"
  console.log('Selecting "AI creativity · paper research" from brain list...');
  const brainListItem = page.locator('.brain-conversation-list button').filter({ hasText: 'AI creativity · paper research' });
  if (await brainListItem.count() > 0) {
    await brainListItem.first().click();
  } else {
    const listBtn = page.locator('.context-panel button').filter({ hasText: 'AI creativity' });
    if (await listBtn.count() > 0) {
      await listBtn.first().click();
    }
  }
  await page.waitForTimeout(1500);

  // 5. Select P4 in graph scrubber
  console.log('Selecting Pair 4 in graph scrubber...');
  const p4Notch = page.locator('.og-notch').filter({ hasText: 'P4' });
  if (await p4Notch.count() > 0) {
    await p4Notch.first().click();
  }
  await page.waitForTimeout(1000);

  // 6. Reset 3D camera to home (Three-quarter) view and keep c05_research_medium selected
  const frame = page.frames().find(f => f !== page.mainFrame());
  if (frame) {
    console.log('Setting brain camera to home view...');
    await frame.evaluate(() => {
      if (window.cotraceBrain) {
        window.cotraceBrain.selectNode('c05_research_medium', { focus: false });
        window.cotraceBrain.setView('home');
      }
    });
  }

  // 7. Wait for 3D camera tween to finish smoothly
  console.log('Waiting for camera and animations to settle...');
  await page.waitForTimeout(3000);

  const outPng = path.resolve('docs/symbiot/website/jkv-symbiot-01-highres.png');
  await page.screenshot({ path: outPng, fullPage: false });
  console.log(`Saved screenshot to: ${outPng}`);

  await browser.close();
  console.log('Done!');
})().catch(err => {
  console.error('Capture failed:', err);
  process.exit(1);
});
