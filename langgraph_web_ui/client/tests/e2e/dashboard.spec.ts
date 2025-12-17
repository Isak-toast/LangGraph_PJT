import { test, expect } from '@playwright/test';

test.describe('Agentic Insight Dashboard - Gemini UI Clone', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('has correct title and Gemini-style layout', async ({ page }) => {
        // Title check
        await expect(page).toHaveTitle(/Agentic/);

        // Sidebar check (uses gemini-sidebar class)
        const sidebar = page.locator('.gemini-sidebar');
        await expect(sidebar).toBeVisible();

        // Welcome message with gradient text
        await expect(page.locator('.gemini-gradient-text')).toBeVisible();
        await expect(page.getByText('안녕하세요')).toBeVisible();

        // Pill-shaped input field at bottom
        const inputContainer = page.locator('.gemini-input-container');
        await expect(inputContainer).toBeVisible();

        // Suggestion chips
        const chips = page.locator('.gemini-chip');
        await expect(chips).toHaveCount(3);
    });

    test('can send a message and see Gemini-style response', async ({ page }) => {
        const input = page.locator('.gemini-input');
        const sendBtn = page.locator('.gemini-send-button');

        // Type and send
        await input.fill('안녕하세요 테스트입니다');
        await sendBtn.click();

        // User message should appear with bubble style
        await expect(page.locator('.gemini-user-bubble').first()).toBeVisible({ timeout: 5000 });
        await expect(page.getByText('안녕하세요 테스트입니다')).toBeVisible();

        // Wait for AI response (requires running backend)
        // AI message should have avatar but NO bubble background
        await expect(page.locator('.gemini-ai-message').first()).toBeVisible({ timeout: 15000 });
        await expect(page.locator('.gemini-ai-avatar').first()).toBeVisible();
    });

    test('sidebar can be toggled', async ({ page }) => {
        const sidebar = page.locator('.gemini-sidebar');
        const menuButton = page.locator('button').filter({ has: page.locator('[class*="MenuIcon"]') }).first();

        // Sidebar should be visible initially
        await expect(sidebar).toBeVisible();

        // Click sidebar close button (inside sidebar)
        const closeButton = sidebar.locator('button').first();
        await closeButton.click();

        // Sidebar should be hidden
        await expect(sidebar).toHaveClass(/translate-x-full/);
    });

    test('visual regression - Gemini clone initial state', async ({ page }) => {
        await page.waitForLoadState('networkidle');

        // Allow some variance for font rendering differences
        await expect(page).toHaveScreenshot('gemini-clone-landing.png', {
            maxDiffPixelRatio: 0.05,
        });
    });

    test('color palette matches Gemini spec', async ({ page }) => {
        // Background color should be #131314 (rgb 19, 19, 20)
        const body = page.locator('body');
        await expect(body).toHaveCSS('background-color', 'rgb(19, 19, 20)');

        // User bubble should be #303134 when present
        await page.locator('.gemini-input').fill('Test');
        await page.locator('.gemini-send-button').click();
        await page.waitForTimeout(500);

        const userBubble = page.locator('.gemini-user-bubble').first();
        if (await userBubble.isVisible()) {
            await expect(userBubble).toHaveCSS('background-color', 'rgb(48, 49, 52)');
        }
    });
});
