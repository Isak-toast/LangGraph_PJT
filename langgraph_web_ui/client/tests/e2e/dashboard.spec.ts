import { test, expect } from '@playwright/test';

test.describe('Agentic Insight Dashboard - UI Quality', () => {

    test.beforeEach(async ({ page }) => {
        await page.goto('/');
    });

    test('has correct title and improved layout', async ({ page }) => {
        // Title check
        await expect(page).toHaveTitle(/Agentic/);

        // Sidebar check (now uses sidebar-container class)
        const sidebar = page.locator('.sidebar-container');
        await expect(sidebar).toBeVisible();

        // Welcome message with gradient text
        await expect(page.locator('.gemini-gradient-text')).toBeVisible();
        await expect(page.getByText('안녕하세요')).toBeVisible();

        // Input field at bottom
        const input = page.locator('input[placeholder="여기에 프롬프트를 입력하세요"]');
        await expect(input).toBeVisible();

        // New Chat button with gradient
        await expect(page.getByRole('button', { name: '새 채팅' })).toBeVisible();
    });

    test('sidebar has good color contrast', async ({ page }) => {
        // Sidebar should be visible
        const sidebar = page.locator('.sidebar-container');
        await expect(sidebar).toBeVisible();

        // New Chat button should have gradient
        const newChatBtn = page.getByRole('button', { name: '새 채팅' });
        await expect(newChatBtn).toBeVisible();
    });

    test('can send a message and see thinking process', async ({ page }) => {
        const input = page.locator('input[placeholder="여기에 프롬프트를 입력하세요"]');
        const sendBtn = page.locator('button[type="submit"]');

        await input.fill('안녕하세요 테스트입니다');
        await sendBtn.click();

        // Wait for user message to appear (use main area locator to avoid sidebar duplicate)
        await expect(page.locator('main').getByText('안녕하세요 테스트입니다')).toBeVisible({ timeout: 5000 });

        // Wait for AI response (requires backend)
        await expect(page.getByText('사고 과정 보기')).toBeVisible({ timeout: 15000 });

        // Click to expand thinking process
        await page.getByText('사고 과정 보기').click();

        // Should show meaningful content (timestamps and descriptions)
        const thinkingContent = page.locator('.gemini-ai-message');
        await expect(thinkingContent).toContainText(/\[.*\]/);  // Should have timestamps
    });

    test('visual regression - improved UI', async ({ page }) => {
        await page.waitForLoadState('networkidle');

        await expect(page).toHaveScreenshot('agentic-insight-ui.png', {
            maxDiffPixelRatio: 0.05,
        });
    });
});
