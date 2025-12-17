# Test Sequence Design: Playwright E2E & Visual Regression

이 문서는 **Agentic Insight Dashboard**의 안정성과 디자인 품질을 보장하기 위한 Playwright 기반의 E2E 테스트 시나리오 및 시퀀스를 정의합니다.

## 1. Testing Strategy

-   **Framework**: Playwright (TypeScript)
-   **Scope**:
    -   **Functional E2E**: 채팅 흐름, 그래프 상태 변화, 에러 처리 검증.
    -   **Visual Regression**: "Trendy"한 디자인 유지를 위한 스냅샷 테스트 (픽셀 단위 비교).
    -   **Wormhole Pattern**: 백엔드 API를 모킹(Mocking)하여 프론트엔드 로직과 UI만 독립적으로 빠르게 검증.

## 2. Test Scenarios (Sequences)

### Scenario A: Initial Dashboard Load
**Goal**: 사용자가 처음 접속했을 때 빈 상태(Empty State)와 레이아웃이 깨짐 없이 로드되는지 확인.

1.  **Navigation**: `http://localhost:5173` 접속.
2.  **Visualization Check**:
    -   Header ("Agentic Insight Dashboard") 존재 확인.
    -   Left Panel: Chat Interface (Empty State Placeholder "Ask me to research...") 표시 확인.
    -   Right Panel: Mermaid Graph Canvas (`START`, `Supervisor` 노드 등) 렌더링 확인.
3.  **Visual Snapshot**: `dashboard-initial-load.png` 캡처 및 비교.

### Scenario B: Happy Path - Research Request
**Goal**: 사용자가 질문을 던지고, 에이전트가 생각하고 답변하는 전 과정이 매끄러운지 검증.

1.  **User Action**:
    -   Input 필드에 "Research AI trends" 입력.
    -   Send 버튼 클릭.
2.  **Immediate Feedback**:
    -   Input 필드 비활성화 (Loading State).
    -   User Message Chat Bubble 즉시 등장.
    -   Header Status Indicator가 "Processing..."으로 변경.
3.  **Streaming & Graph Interaction** (Mocked SSE Events):
    -   **Event 1**: `node_start: Supervisor` -> 그래프의 `Supervisor` 노드 하이라이트 (Class `active` 적용 확인).
    -   **Event 2**: `node_start: Researcher` -> 그래프 `Researcher` 노드 하이라이트.
    -   **Event 3**: `token` 스트림 수신 -> AI Message Bubble 생성 및 텍스트 점진적 렌더링 확인.
    -   **Event 4**: `node_end` -> 그래프 하이라이트 제거.
4.  **Completion**:
    -   Input 필드 활성화.
    -   Header Status Idle로 복귀.

### Scenario C: Thinking Process Accordion UI
**Goal**: "Trendy"하지 않다는 피드백을 개선하기 위해 추가된 Thinking UI가 정상 동작하는지 검증.

1.  **Pre-condition**: AI 응답 메시지에 `thoughts` 데이터가 포함됨.
2.  **Action**: "Thinking Process" 아코디언 토글 클릭.
3.  **Verification**:
    -   내부 로그 (`Researcher...`, `Writer...`)가 펼쳐져서 보이는지 확인.
    -   애니메이션(부드러운 확장/축소) 스냅샷 검증.

### Scenario D: Error Handling
**Goal**: 백엔드 에러 발생 시 UI가 멈추지 않고 적절한 피드백을 주는지 확인.

1.  **Mocking**: API Endpoint `/chat/stream`이 500 에러 또는 SSE 에러 이벤트 반환.
2.  **Action**: 메시지 전송.
3.  **Verification**:
    -   빨간색 Error Badge 또는 Error Toast 표시.
    -   Input 필드가 다시 활성화되어 재시도 가능한 상태가 되는지 확인.

## 3. Visual Regression Configuration

-   **Viewports**:
    -   Desktop: 1920x1080
    -   Laptop: 1366x768
    -   Mobile: 375x667 (iPhone SE) - *반응형 레이아웃 깨짐 방지*
-   **Threshold**: 0.2% (미세한 디자인 변경 허용, 큰 레이아웃 시프트 감지)

## 4. Playwright Setup Plan

1.  `npm init playwright@latest`
2.  `playwright.config.ts` 설정 (Base URL, Trace Viewer 활성화).
3.  `tests/e2e/dashboard.spec.ts` 작성.
