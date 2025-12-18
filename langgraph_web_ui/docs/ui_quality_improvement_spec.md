# UI 품질 개선 설계서 (Phase 12)

## 문제점 분석 및 해결 방안

---

## 1. Live Graph - 애니메이션 없음 / 반응형 문제

### 현재 문제
- Mermaid 그래프가 **정적**으로 렌더링됨
- 노드 전환 시 **애니메이션 없음**
- 컨테이너 크기에 **반응하지 않음** (SVG 고정 크기)

### 근본 원인 (코드 분석)
```typescript
// GraphCanvas.vue
const { svg } = await mermaid.render('mermaid-graph', graphDef);
container.value.innerHTML = svg;  // 단순 교체, 애니메이션 없음
```

### 해결 방안
1. **CSS 트랜지션**: SVG에 CSS transition 적용
2. **반응형 SVG**: `viewBox` + `preserveAspectRatio` 사용
3. **노드 하이라이트 애니메이션**: 활성 노드에 pulse 효과

```css
.mermaid svg {
  width: 100%;
  height: 100%;
  transition: all 0.3s ease;
}
.node.active rect, .node.active circle {
  animation: pulse 1.5s infinite;
}
@keyframes pulse {
  0%, 100% { filter: drop-shadow(0 0 8px #8ab4f8); }
  50% { filter: drop-shadow(0 0 16px #8ab4f8); }
}
```

---

## 2. 사이드바 - 색상 대비 부족 / 디자인 문제

### 현재 문제
- 텍스트와 배경 **대비가 낮음** (접근성 문제)
- **shadcn 컴포넌트** 미사용
- 세션 항목 스타일이 **단순함**

### 근본 원인 (코드 분석)
```vue
<!-- App.vue -->
<div class="gemini-sidebar-item ... bg-[hsl(var(--gemini-bg-hover))]">
  <div class="text-sm truncate">{{ session.title }}</div>
  <div class="text-xs text-[hsl(var(--gemini-text-secondary))]">
```
- 인라인 HSL 색상 사용
- shadcn ScrollArea, Button 미사용

### 해결 방안
1. **shadcn 컴포넌트 활용**: `ScrollArea`, `Separator`, `Button`
2. **색상 대비 개선**: WCAG AA 기준 충족
3. **호버 효과 개선**: 더 명확한 시각적 피드백

```vue
<ScrollArea class="flex-1">
  <Button 
    variant="ghost" 
    class="w-full justify-start gap-3 h-12"
    :class="{ 'bg-accent': session.id === currentSessionId }"
  >
    <MessageSquareIcon class="w-4 h-4" />
    <span>{{ session.title }}</span>
  </Button>
</ScrollArea>
```

---

## 3. 사고 과정 - "..." 만 표시됨

### 현재 문제
```
Supervisor...
Researcher...
Supervisor...
```
→ 실제 사고 내용 없이 노드 이름 + "..." 만 표시

### 근본 원인 (코드 분석)
```typescript
// chat.ts:158
const updateMessageNode = (id: number, node: string, isStart: boolean) => {
    if (isStart) {
        msg.activeNode = node;
        msg.thoughts?.push(`${node}...`);  // ← 여기! 단순 문자열만 추가
    }
}
```

백엔드에서 실제 사고 내용을 보내지 않고, 프론트엔드에서 노드 이름만 저장

### 해결 방안
1. **백엔드 수정**: 각 노드의 실제 처리 내용 전송
2. **프론트엔드 수정**: 더 의미있는 사고 과정 표시

```typescript
// chat.ts - 개선된 버전
if (event.type === 'node_start') {
    updateMessageNode(aiMsgId, event.node, true, event.description);
} else if (event.type === 'thinking') {
    addThought(aiMsgId, event.content);  // 실제 사고 내용 추가
}
```

**임시 해결책** (백엔드 수정 없이):
- 노드별 설명 메시지 하드코딩
- 타임스탬프 추가로 진행 상황 시각화

---

## 4. 구현 체크리스트

### High Priority
- [ ] Live Graph 반응형 SVG 적용
- [ ] Live Graph 노드 하이라이트 애니메이션
- [ ] 사이드바 색상 대비 개선 (WCAG AA)
- [ ] 사고 과정 내용 개선 (노드 설명 추가)

### Medium Priority
- [ ] shadcn ScrollArea, Button 적용
- [ ] 세션 항목 호버/활성 상태 개선
- [ ] Playwright 테스트 케이스 추가

---

## 5. Playwright 테스트 케이스

```typescript
test.describe('UI Quality Tests', () => {
  test('Live Graph is responsive', async ({ page }) => {
    await page.goto('/');
    const graph = page.locator('.mermaid svg');
    await expect(graph).toHaveCSS('width', /100%/);
  });

  test('Sidebar has adequate color contrast', async ({ page }) => {
    await page.goto('/');
    const sessionText = page.locator('.sidebar-session-title');
    // Check contrast ratio is at least 4.5:1
  });

  test('Thinking process shows meaningful content', async ({ page }) => {
    // Send a message and check thinking process
    await page.getByText('사고 과정 보기').click();
    const thoughts = page.locator('.thought-item');
    await expect(thoughts.first()).not.toContainText(/^\.\.\./);
  });
});
```
