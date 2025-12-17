# Gemini UI Clone: Design Specification & Test Plan

이 문서는 **Google Gemini Web App**의 UI를 철저히 분석하여, **Agentic Insight Dashboard**에 적용할 디자인 명세와 Playwright 테스트 케이스를 정의합니다.

> **참고 이미지:**
> - [Gemini 초기 상태](file:///home/isak/.gemini/antigravity/brain/0c829271-f4b7-4576-998f-c51ab0dd9a23/gemini_initial_state_1766009537409.png)
> - [Gemini 채팅 인터페이스](file:///home/isak/.gemini/antigravity/brain/0c829271-f4b7-4576-998f-c51ab0dd9a23/gemini_chat_interface_1766009593808.png)

---

## 1. Layout Structure

```
+---------------------------------------------------------------------+
| [ ≡ ] Sidebar Toggle                        [ Profile Avatar ]      |  <-- Header (64px, sticky)
+---------------------------------------------------------------------+
|         |                                                           |
| Sidebar |                  Main Chat Container                      |
| (280px) |              (max-width: 768px, centered)                 |
|         |                                                           |
| - Chat  |   +-------------------------------------------+           |
|   History|   |  >>> User Message (Right-aligned, Bubble) |          |
|         |   +-------------------------------------------+           |
|         |                                                           |
|         |   [AI Avatar]                                             |
|         |   AI Response (Left-aligned, No Bubble)                   |
|         |   ...multi-line text...                                   |
|         |                                                           |
+---------+-----------------------------------------------------------+
|                                                                     |
|          [ ··· Input Field (Pill Shape, Full Width) ⬆️ ]            |  <-- Fixed Bottom
+---------------------------------------------------------------------+
```

| 요소 | 너비/높이 | 위치 |
|---|---|---|
| Sidebar | `280px` (collapsed: `0px`) | Left, Fixed |
| Main Content | `flex-1` | Center |
| Chat Container | `max-width: 768px` | Centered in Main |
| Input Area | Full width of Chat Container | Fixed Bottom (`bottom: 0`) |
| Header | `64px` height | Sticky Top |

---

## 2. Color Palette (Dark Mode)

| 역할 | HEX/HSL | Tailwind Equivalent | 비고 |
|---|---|---|---|
| Background | `#131314` (HSL 240, 6%, 7%) | `zinc-950` | 매우 어두운 거의 검정 |
| Card/Surface | `#1e1e1f` (HSL 240, 3%, 12%) | `zinc-900` | 사이드바, 입력 영역 배경 |
| User Bubble | `#303134` (HSL 220, 5%, 19%) | `zinc-800` | 유저 메시지 배경 |
| AI Text | `#e3e3e8` (HSL 240, 10%, 90%) | `zinc-200` | AI 응답 텍스트 |
| Muted Text | `#8e8e93` (HSL 240, 3%, 57%) | `zinc-500` | 보조 텍스트, 타임스탬프 |
| Primary Accent | `#8ab4f8` (HSL 213, 89%, 75%) | `blue-300` | 링크, 활성 상태 |
| Gemini Gradient | `linear-gradient(135deg, #4285f4, #a66ff0, #ea4335)` | Custom | 로고, 강조 애니메이션 |

---

## 3. Typography

| 요소 | Font Family | Size | Weight | Line Height |
|---|---|---|---|---|
| Logo/Brand | `Google Sans`, sans-serif | `20px` | `500` | `1.2` |
| Body Text (AI) | `Google Sans`, sans-serif | `16px` | `400` | `1.75` |
| User Message | `Google Sans`, sans-serif | `16px` | `400` | `1.5` |
| Input Placeholder | `Google Sans`, sans-serif | `16px` | `400` | `1.5` |
| Sidebar Item | `Google Sans`, sans-serif | `14px` | `500` | `1.4` |
| Timestamp/Meta | `Google Sans`, sans-serif | `12px` | `400` | `1.3` |

> **참고**: `Google Sans`는 Closed Font이므로, 대안으로 `Inter` 또는 `Roboto`를 사용합니다.

---

## 4. Chat Message Styling

### 4.1 User Message
```css
.user-message {
  display: flex;
  justify-content: flex-end; /* Right-aligned */
  margin-bottom: 16px;
}
.user-message-bubble {
  background-color: #303134; /* zinc-800 */
  color: #e3e3e8;
  padding: 12px 16px;
  border-radius: 20px;
  border-top-right-radius: 4px; /* Tail effect */
  max-width: 80%;
}
```

### 4.2 AI Message
```css
.ai-message {
  display: flex;
  align-items: flex-start; /* Left-aligned */
  gap: 12px;
  margin-bottom: 24px;
}
.ai-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #4285f4, #a66ff0, #ea4335);
  border-radius: 50%;
  flex-shrink: 0;
}
.ai-message-content {
  /* NO background bubble */
  color: #e3e3e8;
  line-height: 1.75;
}
```

---

## 5. Input Field Design

| 속성 | 값 | 비고 |
|---|---|---|
| Shape | Pill (`border-radius: 28px`) | 둥근 모서리 |
| Background | `#1e1e1f` | `zinc-900` |
| Border | `1px solid #3c4043` (hover: `#5f6368`) | 미세한 테두리 |
| Height | `56px` | 여유로운 높이 |
| Padding | `0 16px 0 20px` | 좌우 패딩 |
| Send Button | 아이콘 (⬆️), `32px`, 오른쪽 끝 | 원형, 비활성 시 회색 |

---

## 6. Playwright Test Cases (Pixel-Accurate)

### TC-001: Initial Empty State Layout
```typescript
test('Initial layout matches Gemini spec', async ({ page }) => {
  await page.goto('/');
  
  // Sidebar visible and correct width
  const sidebar = page.locator('aside');
  await expect(sidebar).toBeVisible();
  await expect(sidebar).toHaveCSS('width', '280px');
  
  // Background color
  const body = page.locator('body');
  await expect(body).toHaveCSS('background-color', 'rgb(19, 19, 20)'); // #131314
  
  // Input field pill shape
  const input = page.locator('input[type="text"]').or(page.locator('[contenteditable="true"]'));
  await expect(input).toHaveCSS('border-radius', '28px');
});
```

### TC-002: User Message Styling
```typescript
test('User message has dark bubble style', async ({ page }) => {
  await page.goto('/');
  await page.locator('input').fill('Test message');
  await page.locator('button[type="submit"]').click();
  
  const userBubble = page.locator('[data-testid="user-message"]');
  await expect(userBubble).toHaveCSS('background-color', 'rgb(48, 49, 52)'); // #303134
  await expect(userBubble).toHaveCSS('border-radius', /20px.*4px/); // asymmetric
  await expect(userBubble).toHaveCSS('justify-content', 'flex-end');
});
```

### TC-003: AI Message Styling (No Bubble)
```typescript
test('AI message has no bubble, left-aligned with avatar', async ({ page }) => {
  // ... trigger AI response ...
  
  const aiMessage = page.locator('[data-testid="ai-message"]');
  await expect(aiMessage).toHaveCSS('background-color', 'rgba(0, 0, 0, 0)'); // transparent
  
  const avatar = page.locator('[data-testid="ai-avatar"]');
  await expect(avatar).toBeVisible();
  await expect(avatar).toHaveCSS('width', '32px');
  await expect(avatar).toHaveCSS('border-radius', '50%');
});
```

### TC-004: Visual Snapshot Baseline
```typescript
test('Visual regression check', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  
  await expect(page).toHaveScreenshot('gemini-clone-initial.png', {
    maxDiffPixelRatio: 0.02, // Stricter threshold
  });
});
```

---

## 7. Implementation Checklist

- [ ] `style.css`: 새 색상 변수 적용 (`--background: #131314`, etc.)
- [ ] `App.vue`: 레이아웃 재구성 (Sidebar 280px, Main Centered 768px)
- [ ] `ChatMessage.vue`:
    - [ ] User: Right-aligned bubble (`bg-zinc-800`, `rounded-2xl rounded-tr-sm`)
    - [ ] AI: Left-aligned, NO bubble, avatar with gradient
- [ ] `Input.vue`: Pill shape (`rounded-3xl`), `h-14`, gradient border on focus
- [ ] Playwright: `dashboard.spec.ts` 업데이트
