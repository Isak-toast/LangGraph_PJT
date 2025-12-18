# Agentic Insight Dashboard - Design Plan

## 1. Project Overview
**Agentic Insight Dashboard**는 LangGraph의 강력한 멀티 에이전트 기능을 웹 인터페이스로 시각화하고 제어할 수 있는 애플리케이션입니다.
사용자는 복잡한 리서치 작업을 요청하고, 여러 AI 에이전트(Reseacher, Chart Generator, Writer)가 협업하는 과정을 실시간으로 지켜볼 수 있습니다.

### 핵심 목표
- **LangGraph 시각화**: 현재 실행 중인 에이전트와 노드를 다이어그램으로 실시간 표시
- **스트리밍 UX**: 에이전트의 생각(Thought)과 행동(Action)을 타이핑 효과로 제공
- **멀티 에이전트 경험**: 중앙 Supervisor가 작업을 분배하는 과정을 명확히 보여줌

## 2. Tech Stack

### Frontend
- **Framework**: Vue 3 (via Vite)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + **shadcn-vue** (Modern, Accessible Components)
- **Visualization**: `mermaid` (for dynamic graph rendering)
- **State Management**: Pinia

### Backend
- **Framework**: FastAPI (Python)
- **Core Engine**: LangGraph, LangChain
- **Communication**: Server-Sent Events (SSE) for real-time streaming
- **LLM**: Google Gemini (via `langchain-google-genai`)

## 3. Architecture

```mermaid
graph TD
    User[User (Browser)] <-->|HTTP/SSE| API[FastAPI Server]
    API <-->|Run| LG[LangGraph Supervisor]
    
    subgraph "LangGraph Cloud (Local)"
        LG -->|Route| RES[Researcher Agent]
        LG -->|Route| WRT[Writer Agent]
        LG -->|Route| CHT[Chart Agent]
        RES -->|Result| LG
        WRT -->|Result| LG
        CHT -->|Result| LG
    end
```

## 4. Feature Specification

### 4.1 Chat Interface
- 사용자가 질문을 입력하는 채팅창
- 에이전트의 응답을 Markdown으로 렌더링
- 에이전트별 아이콘/색상 구분 (예: Supervisor=Bot, Researcher=Blue, Writer=Green)

### 4.2 Live Graph View
- LangGraph의 현재 상태를 Mermaid 다이어그램으로 렌더링
- 현재 활성화(Active)된 노드를 하이라이트 애니메이션으로 표시

### 4.3 Agent Activity Log
- 내부적으로 오고 가는 메시지(Tool Calls, Intermediate Thoughts)를 사이드바 로그로 표시
- "무슨 일을 하고 있는지" 투명하게 공개

## 5. Project Structure

```
langgraph_web_ui/
├── client/                 # Vue Frontend
│   ├── src/
│   │   ├── components/     # Chat, Graph, Sidebar (shadcn components)
│   │   ├── stores/         # Pinia Stores
│   │   ├── views/          # Page Views
│   │   ├── App.vue
│   │   └── main.ts
│   ├── index.html
│   ├── vite.config.ts
│   └── tailwind.config.js
├── server/                 # FastAPI Backend
│   ├── agent/              # LangGraph Definition
│   │   ├── graph.py        # Graph Construction
│   │   └── tools.py        # Tavily, etc.
│   ├── app.py              # API Endpoints
│   └── requirements.txt
└── README.md
```

## 6. Implementation Steps
1.  **Backend Setup**: FastAPI + LangGraph Supervisor 기본 구조 구현
2.  **Frontend Setup**: Vite + React + TS 초기화
3.  **UI Design**: CSS 변수 설정 및 기본 레이아웃 (Chat + Graph Split View)
4.  **Integration**: SSE 스트리밍 연동 및 Mermaid 시각화
5.  **Refinement**: 디자인 폴리싱 및 에이전트 기능 고도화
