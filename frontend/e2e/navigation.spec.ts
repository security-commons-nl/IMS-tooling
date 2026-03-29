import { test, expect } from '@playwright/test';

async function login(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  await page.getByRole('button', { name: 'Inloggen' }).click();
  await page.waitForURL(/\/inrichten/, { timeout: 15_000, waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Fase 0')).toBeVisible({ timeout: 10_000 });
}

test.describe('Navigatie', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('overzicht toont Fase 0 met stappen', async ({ page }) => {
    await expect(page.getByText('Fase 0 -- Fundament')).toBeVisible();
    await expect(page.getByText('Bestuurlijk commitment')).toBeVisible();
  });

  test('fases 1-3 zijn standaard dichtgeklapt', async ({ page }) => {
    await expect(page.getByText('Fase 1 -- Lijnmanagement doet risicoanalyse')).toBeVisible();
    // Content of Fase 1 should NOT be visible (collapsed)
    await expect(page.getByText('Onboarding & awareness lijnmanagement')).not.toBeVisible();

    // Expand it
    await page.getByText('Fase 1 -- Lijnmanagement doet risicoanalyse').click();
    await expect(page.getByText('Onboarding & awareness lijnmanagement')).toBeVisible();
  });

  test('sidebar navigatie naar beheer', async ({ page }) => {
    await page.getByRole('link', { name: 'Dashboard' }).click();
    await expect(page).toHaveURL(/\/beheer/);
  });

  test('stap-detail terug-knop werkt', async ({ page }) => {
    await page.getByText('Bestuurlijk commitment').click();
    await expect(page.getByText('Stap 1')).toBeVisible({ timeout: 5_000 });
    await page.getByRole('button', { name: 'Overzicht' }).click();
    await expect(page.getByText('Fase 0 -- Fundament')).toBeVisible({ timeout: 5_000 });
  });
});
