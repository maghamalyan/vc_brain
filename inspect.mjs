import { chromium } from '@playwright/test';
const b = await chromium.launch(); const p = await b.newPage({viewport:{width:1440,height:900}});
await p.goto('http://127.0.0.1:8000/candidate/ada-lovelace-fixture', {waitUntil:'networkidle'});
const out = await p.evaluate(() => {
  const chip = document.querySelector('.record-breadcrumb > :last-child');
  const r = chip.getBoundingClientRect();
  const stack = document.elementsFromPoint(r.right - 12, r.top + r.height/2).slice(0,6)
    .map(e => `${e.tagName}.${(e.className?.toString?.()||'').split(' ')[0]} z=${getComputedStyle(e).zIndex} pos=${getComputedStyle(e).position}`);
  const circles = [...document.querySelectorAll('*')].filter(e => { const s = getComputedStyle(e); const b2 = e.getBoundingClientRect(); return s.borderRadius.includes('50%') && b2.width > 25 && b2.width < 50 && b2.top < 160 && b2.right > innerWidth - 300; }).map(e => `${e.tagName}.${(e.className?.toString?.()||'').split(' ')[0]} @${Math.round(e.getBoundingClientRect().x)},${Math.round(e.getBoundingClientRect().y)} aria=${e.getAttribute('aria-label')}`);
  return {chip: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width)}, stack, circles};
});
console.log(JSON.stringify(out, null, 1)); await b.close();
