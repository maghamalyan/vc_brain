import { expect, test, type Page } from '@playwright/test';

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
  await expect(page.locator('.step-feed li')).toHaveCount(5);
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
  await expect(page).toHaveURL(/\/candidate\/ada-lovelace-fixture$/);
  await expect(page.getByRole('heading', { name: 'Ada Lovelace' })).toBeVisible();
  expect(external).toEqual([]);
});

test('candidate record renders claim provenance and prominent gaps', async ({ page }) => {
  const external = enforceOffline(page);
  await page.goto('/candidate/ada-lovelace-fixture');
  await expect(page.locator('.claim-chip')).toHaveCount(9);
  await page.locator('.claim-chip').first().focus();
  await expect(page.getByRole('dialog', { name: /Evidence for claim/ })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Not observed' })).toBeVisible();
  await expect(page.locator('.gaps-box li')).toHaveCount(2);
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
