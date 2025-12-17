# LangGraph Web UI - Refactoring & Enhancement Plan

## 1. Objectives

- **UI/UX Overhaul**: "구린 디자인" 개선. Tailwind + shadcn-vue를 적극 활용하여 Professional한 Dashboard 룩앤필 구현.
- **Stability**: `TypeError` 등 런타임 에러 방지. 방어적 코딩 및 타입 안정성 강화.
- **Observability**: 에이전트의 "생각(Thinking)"과 "답변(Answer)"을 명확히 구분하여 UI에 표시.

## 2. API & Data Contract (Backend <-> Frontend)

### 2.1 SSE Event Schema
Backend는 다음 포맷을 엄격히 준수합니다.

```typescript
type SSEEvent = 
  | { type: "token"; content: string }              // LLM 스트리밍 토큰
  | { type: "node_start"; node: string }            // 노드 진입 (예: Researcher)
  | { type: "node_end"; node: string }              // 노드 종료
  | { type: "tool_call"; tool: string; input: any } // 도구 호출 (옵션)
  | { type: "tool_result"; output: any }            // 도구 결과 (옵션)
  | { type: "end" }                                 // 스트림 종료
  | { type: "error"; content: string }              // 에러 발생
```

### 2.2 Backend Changes (`server/app.py`)
- **JSON Serialization**: `json.dumps` 시 `ensure_ascii=False` 사용하여 한글 깨짐 방지.
- **Robust Generator**: `try-finally` 블록으로 에러 발생 시에도 반드시 `error` 또는 `end` 이벤트를 전송하여 프론트엔드 무한 대기 방지.

## 3. Frontend Architecture Changes (`client/`)

### 3.1 Component Restructuring (shadcn-vue style)
기존의 단순한 컴포넌트를 shadcn 스타일로 고도화합니다.

- `src/components/ui/`: shadcn 기본 컴포넌트 (Button, Card, Input, ScrollArea, Avatar, Skeleton)
- `src/components/chat/`:
    - `ChatMessage.vue`: 메시지 버블. User/AI 구분, Avatar, Timestamp 포함.
    - `ChatInput.vue`: 입력창, 전송 버튼, Loading Spinner.
    - `AgentStatus.vue`: 현재 실행 중인 에이전트 상태 표시 (Thinking Accordion).
- `src/components/graph/`:
    - `DynamicGraph.vue`: Mermaid 렌더링 최적화 (Zoom/Pan 기능 추가 고려).

### 3.2 State Management (`stores/chat.ts`)
- **Reactive Map**: `messages` 배열 인덱스 접근(`messages[index]`)은 위험하므로, `Map`이나 안정적인 ID 기반 업데이트 로직으로 변경.
- **Thinking State**: AI 메시지 내부에 `thoughts: string[]` 필드를 추가하여, "생각하는 과정(노드 전환)"을 별도로 UI에 표시.

## 4. Design Specification (Visuals)

- **Color Palette**: Deep Dark Theme (Zinc/Slate 계열).
- **Typography**: Inter 또는 Pretendard (한글 최적화).
- **Effects**:
    - 메시지 도착 시 부드러운 Fade-in.
    - 활성 노드에 "Pulse" 애니메이션.
    - 스트리밍 텍스트 뒤에 "Cursor" 깜빡임 효과.

## 5. Implementation Roadmap

1.  **Backend Stabilization**:
    -   API 응답 포맷 정규화 test code 작성.
    -   `supervisor` 라우팅 로직 재검증.
2.  **Frontend Component Library**:
    -   `shadcn-vue` 컴포넌트 (Accordion, Alert, Avatar 등) 추가 설치.
3.  **Chat UI Refactoring**:
    -   `ChatMessage` 컴포넌트 재작성 (Thinking 섹션 분리).
    -   `useChatStore` 로직 개선 (TypeError 방지).
4.  **Visual Polish**:
    -   Graph Canvas 디자인 개선 (Card 감싸기, 헤더 추가).
    -   전체 레이아웃 Grid 시스템 적용.
