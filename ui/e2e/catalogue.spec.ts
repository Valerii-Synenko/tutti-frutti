import { test, expect } from '@playwright/test';

test.describe('Catalogue', () => {
  test('shows the hero and a grid of fruit cards', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByTestId('hero-title')).toBeVisible();
    await expect(page.getByTestId('fruit-grid')).toBeVisible();

    const cards = page.getByTestId('fruit-card');
    await expect(cards.first()).toBeVisible();
    expect(await cards.count()).toBeGreaterThan(0);
  });

  test('filters fruit by search term', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('search-input').fill('mango');

    await expect(page.getByTestId('fruit-grid')).toContainText(/mango/i);
  });

  test('adding a fruit updates the cart badge', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('add-to-cart-button').first().click();

    await expect(page.getByTestId('cart-count')).toHaveText('1');
  });
});

test.describe('Fruit assistant chat', () => {
  test('can open the widget and send a message', async ({ page }) => {
    await page.goto('/');

    await page.getByTestId('chat-toggle-button').click();
    await expect(page.getByTestId('chat-panel')).toBeVisible();

    await page.getByTestId('chat-input').fill('What fruit is in season now?');
    await page.getByTestId('chat-send-button').click();

    await expect(page.getByTestId('chat-message-assistant').last()).toBeVisible({ timeout: 15000 });
  });
});
