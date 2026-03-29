import { test, expect } from '@playwright/test';

async function login(page: import('@playwright/test').Page, role = 'admin') {
  await page.goto('/login');
  await page.waitForLoadState('networkidle');
  if (role !== 'admin') {
    await page.locator('select#rol').selectOption(role);
  }
  await page.getByRole('button', { name: 'Inloggen' }).click();
  // Wait for navigation away from /login
  await page.waitForURL(/\/inrichten/, { timeout: 15_000, waitUntil: 'domcontentloaded' });
}

test.describe('Authenticatie', () => {
  test('login als admin redirects naar inrichten', async ({ page }) => {
    await login(page);
    await expect(page).toHaveURL(/\/inrichten/);
    // Page should show step overview
    await expect(page.getByText('Fase 0')).toBeVisible({ timeout: 10_000 });
  });

  test('login als viewer kan pagina lezen', async ({ page }) => {
    await login(page, 'viewer');
    await expect(page.getByText('Fase 0')).toBeVisible({ timeout: 10_000 });
  });

  test('uitloggen redirects naar login', async ({ page }) => {
    await login(page);
    await expect(page.getByText('Fase 0')).toBeVisible({ timeout: 10_000 });

    await page.getByRole('button', { name: 'Uitloggen' }).click();
    await expect(page.getByRole('button', { name: 'Inloggen' })).toBeVisible({ timeout: 10_000 });
  });
});
