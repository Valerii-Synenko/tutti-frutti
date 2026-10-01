import { test, expect, type Page } from '@playwright/test';

async function registerAndFillBasket(page: Page) {
  await page.goto('/register');
  await page.getByTestId('register-name-input').fill('Checkout Tester');
  await page.getByTestId('register-email-input').fill(`checkout-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`);
  await page.getByTestId('register-password-input').fill('S3curePass!');
  await page.getByTestId('register-submit-button').click();
  await expect(page.getByTestId('nav-user-name')).toHaveText('Checkout Tester');

  await page.getByTestId('add-to-cart-button').first().click();
  await expect(page.getByTestId('cart-count')).toHaveText('1');
  await page.getByTestId('nav-cart-link').click();
}

async function fillCheckout(page: Page, cardNumber: string) {
  await page.getByTestId('checkout-phone-input').fill('+385 91 234 5678');
  await page.getByTestId('checkout-street-input').fill('Ilica 1');
  await page.getByTestId('checkout-city-input').fill('Zagreb');
  await page.getByTestId('checkout-postal-code-input').fill('10000');
  await page.getByTestId('checkout-country-input').fill('Croatia');
  await page.getByTestId('checkout-card-number-input').fill(cardNumber);
  await page.getByTestId('checkout-expiry-input').fill('1230');
  await page.getByTestId('checkout-cvc-input').fill('123');
}

test.describe('Checkout', () => {
  test('places a paid order and returns to the market', async ({ page }) => {
    await registerAndFillBasket(page);

    // Name fields are prefilled from the account.
    await expect(page.getByTestId('checkout-full-name-input')).toHaveValue('Checkout Tester');

    await fillCheckout(page, '4242424242424242');
    await expect(page.getByTestId('checkout-card-number-input')).toHaveValue('4242 4242 4242 4242');
    await expect(page.getByTestId('checkout-expiry-input')).toHaveValue('12/30');

    await page.getByTestId('checkout-button').click();

    await expect(page.getByTestId('order-success-title')).toHaveText(/placed and paid/i);
    await expect(page.getByTestId('order-success-message')).toContainText('Zagreb');
    await expect(page.getByTestId('order-success-card')).toHaveText('•••• 4242');
    await expect(page.getByTestId('cart-count')).toHaveCount(0);

    await page.getByTestId('continue-shopping-button').click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByTestId('fruit-grid')).toBeVisible();
  });

  test('shows an error and keeps the basket when the card is declined', async ({ page }) => {
    await registerAndFillBasket(page);
    await fillCheckout(page, '4000000000000002');

    await page.getByTestId('checkout-button').click();

    await expect(page.getByTestId('checkout-error')).toHaveText(/declined/i);
    await expect(page.getByTestId('order-success')).toHaveCount(0);
    await expect(page.getByTestId('cart-line')).toHaveCount(1);
  });
});
