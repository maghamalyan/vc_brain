import { chromium } from '@playwright/test';

const outDir = process.env.SHOT_DIR || '/tmp/shots';
const base = 'http://127.0.0.1:8000';
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

await page.goto(base + '/candidate/ada-lovelace-fixture', { waitUntil: 'networkidle' });
await page.waitForTimeout(600);
await page.screenshot({ path: `${outDir}/record-full.png`, fullPage: true });
const timeline = page.locator('.timeline-panel');
if (await timeline.count()) await timeline.screenshot({ path: `${outDir}/record-timeline.png` });

await page.goto(base + '/', { waitUntil: 'networkidle' });
await page.waitForTimeout(600);
await page.screenshot({ path: `${outDir}/radar-full.png`, fullPage: true });

await browser.close();
console.log('done');
