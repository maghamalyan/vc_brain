import { expect, test, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';

const evidenceFixture = JSON.parse(readFileSync(new URL('../src/lib/mocks/events.json', import.meta.url), 'utf8')) as Array<{
  gh_login: string;
  ts: string;
  event_type: string;
}>;
const candidateFixture = JSON.parse(readFileSync(new URL('../src/lib/mocks/candidates.json', import.meta.url), 'utf8')) as Array<{
  gh_login: string;
  current_score: number;
  score_components: Array<{ contribution: number }>;
  first_detection_month: string | null;
  trajectory: Array<{ month: string; score: number }>;
}>;
const adaMemoFixture = JSON.parse(readFileSync(new URL('../src/lib/mocks/memos/ada-lovelace-fixture.json', import.meta.url), 'utf8')) as {
  sections: {
    company_snapshot: { claim_ids: string[] };
    investment_hypotheses: Array<{ claim_ids: string[] }>;
    problem_product: { claim_ids: string[] };
    traction_kpis: { claim_ids: string[] };
    swot: Record<string, Array<{ claim_ids: string[] }>>;
  };
};
function enforceOffline(page: Page): string[] {
  const externalRequests: string[] = [];
  page.on('request', (request) => {
    const url = new URL(request.url());
    if (!['127.0.0.1', 'localhost'].includes(url.hostname)) externalRequests.push(request.url());
  });
  return externalRequests;
}

test('mock app boots and all primary route shells render', async ({ page }) => {
  const external = enforceOffline(page);
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Founder radar' })).toBeVisible();
  await expect(page.locator('.candidate-row')).toHaveCount(12);

  await page.goto('/candidate/ada-lovelace-fixture');
  await expect(page.getByRole('heading', { name: 'Ada Lovelace' })).toBeVisible();

  await page.goto('/runs/mock-ada-lovelace-fixture');
  await expect(page.getByRole('heading', { name: 'Diligence steps' })).toBeVisible();
  const stepCount = await page.locator('.step-feed li').count();
  expect(stepCount).toBeGreaterThanOrEqual(5);
  expect(external).toEqual([]);
});

test('command palette opens, searches, and navigates by keyboard', async ({ page }) => {
  const external = enforceOffline(page);
  await page.goto('/');
  await page.keyboard.press('Control+k');
  const palette = page.getByRole('dialog', { name: 'Search and command palette' });
  await expect(palette).toBeVisible();
  const search = palette.getByRole('combobox');
  await search.fill('Ada');
  await expect(palette.getByRole('option', { name: /Deep dive on Ada Lovelace/ })).toBeVisible();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/\/runs\/mock-ada-lovelace-fixture$/);
  await expect(page.getByRole('heading', { name: 'Diligence steps' })).toBeVisible();
  expect(external).toEqual([]);
});

test('thesis sector selection persists and is shared with radar', async ({ page }) => {
  const external = enforceOffline(page);
  const sector = 'AI infrastructure';

  await page.goto('/thesis');
  await expect(page.getByRole('heading', { name: 'The lens behind the radar.' })).toBeVisible();
  const sectorChips = page.getByTestId('thesis-sector-chips');
  await expect(sectorChips.getByRole('button')).toHaveCount(5);
  const sectorChip = sectorChips.getByRole('button', { name: sector, exact: true });
  await expect(sectorChip).toHaveAttribute('aria-pressed', 'false');
  await sectorChip.click();
  await expect(sectorChip).toHaveAttribute('aria-pressed', 'true');
  await expect.poll(async () => page.evaluate(() => JSON.parse(localStorage.getItem('vc-brain:thesis-overlay') ?? '{}').sector)).toBe(sector);

  await page.reload();
  await expect(page.getByTestId('thesis-sector-chips').getByRole('button', { name: sector, exact: true })).toHaveAttribute('aria-pressed', 'true');

  await page.goto('/');
  await expect(page.locator('.candidate-row')).toHaveCount(12);
  await expect(page.locator('.thesis-controls').getByRole('button', { name: sector, exact: true })).toHaveAttribute('aria-pressed', 'true');
  expect(external).toEqual([]);
});

test('candidate record renders claim provenance and prominent gaps', async ({ page }) => {
  const external = enforceOffline(page);
  await page.goto('/candidate/ada-lovelace-fixture');
  await expect(page.locator('.memo-citation')).toHaveCount(9);
  await page.locator('.memo-citation').first().focus();
  await expect(page.getByRole('dialog', { name: /Evidence for claim/ })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Not observed' })).toBeVisible();
  await expect(page.locator('.gaps-box li')).toHaveCount(2);
  expect(external).toEqual([]);
});

test('score waterfall opens and mock contributions sum to the displayed score', async ({ page }) => {
  const external = enforceOffline(page);
  const candidate = candidateFixture.find((item) => item.gh_login === 'ada-lovelace-fixture');
  expect(candidate).toBeDefined();

  await page.goto('/candidate/ada-lovelace-fixture');
  await page.locator('.signal-score-toggle').click();
  const waterfall = page.getByTestId('score-waterfall');
  await expect(waterfall).toBeVisible();
  await expect(waterfall.locator('[data-score-component]')).toHaveCount(candidate?.score_components.length ?? 0);

  const displayedScore = Number(await waterfall.getAttribute('data-displayed-score'));
  const contributions = await waterfall.locator('[data-contribution]').evaluateAll((rows) => rows.map((row) => Number(row.getAttribute('data-contribution'))));
  const contributionSum = contributions.reduce((sum, contribution) => sum + contribution, 0);
  expect(Math.abs(contributionSum - displayedScore)).toBeLessThanOrEqual(0.01);
  expect(displayedScore).toBeCloseTo((candidate?.current_score ?? 0) * 100, 2);
  expect(external).toEqual([]);
});

test('memo sections render the fixture claim_ids as numbered inline citations', async ({ page }) => {
  const external = enforceOffline(page);
  const expectedCounts = [
    adaMemoFixture.sections.company_snapshot.claim_ids.length,
    ...adaMemoFixture.sections.investment_hypotheses.map((section) => section.claim_ids.length),
    adaMemoFixture.sections.problem_product.claim_ids.length,
    adaMemoFixture.sections.traction_kpis.claim_ids.length,
    ...Object.values(adaMemoFixture.sections.swot).flatMap((sections) => sections.map((section) => section.claim_ids.length))
  ];

  await page.goto('/candidate/ada-lovelace-fixture');
  const proseSections = page.getByTestId('memo-section-prose');
  await expect(proseSections).toHaveCount(expectedCounts.length);
  for (const [index, expectedCount] of expectedCounts.entries()) {
    await expect(proseSections.nth(index).locator('.memo-citation')).toHaveCount(expectedCount);
    await expect(proseSections.nth(index)).toHaveAttribute('data-claim-count', String(expectedCount));
  }
  const labels = await proseSections.locator('.memo-citation').allTextContents();
  expect(labels.every((label) => /^\[\d+\]$/.test(label))).toBe(true);
  expect(external).toEqual([]);
});

test('radar supports j/k selection and Enter navigation', async ({ page }) => {
  const external = enforceOffline(page);
  await page.goto('/');
  const radar = page.getByRole('grid', { name: 'Ranked founder candidates' });
  await expect(page.locator('.candidate-row')).toHaveCount(12);
  await radar.focus();
  await radar.press('j');
  const selected = page.locator('.candidate-row[aria-selected="true"]');
  await expect(selected).toHaveCount(1);
  await expect(selected.locator('.rank-number')).toHaveText('02');
  await radar.press('k');
  await expect(selected.locator('.rank-number')).toHaveText('01');
  await radar.press('j');
  await radar.press('Enter');
  await expect(page).toHaveURL(/\/candidate\/grace-hopper-fixture$/);
  await expect(page.getByRole('heading', { name: 'Grace Hopper' })).toBeVisible();
  expect(external).toEqual([]);
});

test('candidate timeline clusters fixture months and filters non-matching nodes', async ({ page }) => {
  const external = enforceOffline(page);
  const founderEvidence = evidenceFixture.filter((event) => event.gh_login === 'ada-lovelace-fixture');
  const expectedMonths = new Set(founderEvidence.map((event) => event.ts.slice(0, 7))).size;
  const commitMonths = new Set(founderEvidence.filter((event) => event.event_type === 'commit_burst').map((event) => event.ts.slice(0, 7))).size;

  await page.goto('/candidate/ada-lovelace-fixture');
  const nodes = page.getByTestId('timeline-month-node');
  await expect(nodes).toHaveCount(expectedMonths);

  await page.locator('[data-event-type="commit_burst"] button').click();
  await expect(nodes).toHaveCount(commitMonths);
  await expect(nodes.first()).toHaveAttribute('data-event-types', /commit_burst/);
  expect(external).toEqual([]);
});

test('radar ribbon renders month ticks and scrubs intelligence by pointer and keyboard', async ({ page }) => {
  const external = enforceOffline(page);
  await page.goto('/');

  await expect(page.locator('.candidate-row')).toHaveCount(12);
  const ticks = page.getByTestId('scrubber-month-tick');
  await expect(ticks).toHaveCount(24);
  await expect(ticks.first()).toBeVisible();
  const cutoff = page.locator('.scrubber-copy strong');
  const scrubber = page.getByTestId('radar-scrubber');
  await expect(cutoff).toHaveText('Jul 2026');

  await scrubber.focus();
  await scrubber.press('ArrowLeft');
  await expect(cutoff).toHaveText('Jun 2026');
  await expect(page.getByText('Future evidence hidden', { exact: true })).toBeVisible();

  const bounds = await scrubber.boundingBox();
  expect(bounds).not.toBeNull();
  if (bounds) {
    await page.mouse.move(bounds.x + bounds.width * .75, bounds.y + bounds.height / 2);
    await page.mouse.down();
    await page.mouse.move(bounds.x + bounds.width * .25, bounds.y + bounds.height / 2, { steps: 5 });
    await page.mouse.up();
  }
  await expect(cutoff).not.toHaveText('Jun 2026');
  expect(external).toEqual([]);
});

test('radar scrub uses fixture trajectory scores and dims candidates before detection', async ({ page }) => {
  const external = enforceOffline(page);
  const months = candidateFixture[0].trajectory.map((point) => point.month.slice(0, 7));
  const cutoffIndex = months.findIndex((month) => {
    const hasDetected = candidateFixture.some((candidate) => candidate.first_detection_month && candidate.first_detection_month.slice(0, 7) <= month);
    const hasUndetected = candidateFixture.some((candidate) => candidate.first_detection_month && candidate.first_detection_month.slice(0, 7) > month);
    return hasDetected && hasUndetected;
  });
  expect(cutoffIndex).toBeGreaterThanOrEqual(0);
  const cutoffMonth = months[cutoffIndex];
  const undetected = candidateFixture.find((candidate) => candidate.first_detection_month && candidate.first_detection_month.slice(0, 7) > cutoffMonth)!;
  const detected = candidateFixture.find((candidate) => candidate.first_detection_month && candidate.first_detection_month.slice(0, 7) <= cutoffMonth)!;
  const undetectedScore = undetected.trajectory.find((point) => point.month.slice(0, 7) === cutoffMonth)!.score;
  const detectedScore = detected.trajectory.find((point) => point.month.slice(0, 7) === cutoffMonth)!.score;

  await page.goto('/');
  const scrubber = page.getByTestId('radar-scrubber');
  await scrubber.evaluate((node, value) => {
    const input = node as HTMLInputElement;
    input.value = String(value);
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }, cutoffIndex);

  const undetectedRow = page.locator(`.candidate-row[data-login="${undetected.gh_login}"]`);
  await expect(undetectedRow).toHaveClass(/not-yet-detected/);
  await expect(undetectedRow.locator('.score-cell')).toHaveText(/Not yet detected/i);
  await expect.poll(async () => Number(await undetectedRow.getAttribute('data-trajectory-score'))).toBeCloseTo(undetectedScore, 6);

  const detectedRow = page.locator(`.candidate-row[data-login="${detected.gh_login}"]`);
  await expect(detectedRow.getByTestId('historical-score')).toHaveText(String(Math.round(detectedScore * 100)));
  expect(external).toEqual([]);
});
