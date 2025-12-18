# LangGraph Multi-Agent 시스템 문제 해결 가이드

> 작성일: 2025-12-19
> 프로젝트: LangGraph Web UI (`langgraph_server`)

이 문서는 LangGraph 멀티 에이전트 시스템 개발 중 발생한 문제들과 해결 과정을 상세히 기록합니다.

---

## 목차
1. [Import 에러 (상대 경로)](#1-import-에러-상대-경로)
2. [Supervisor 무한 루프 (Recursion Limit)](#2-supervisor-무한-루프-recursion-limit)
3. [Researcher 검색 미수행](#3-researcher-검색-미수행)
4. [멀티턴 대화 시 즉시 FINISH](#4-멀티턴-대화-시-즉시-finish)

---

## 1. Import 에러 (상대 경로)

### 🔴 문제 상황
```
ImportError: attempted relative import with no known parent package
```

`langgraph dev` 실행 시 상대 import (`from .state import AgentState`)가 동작하지 않음.

### 🔍 원인 분석
LangGraph CLI는 모듈을 직접 실행하기 때문에, 상대 import가 작동하지 않음.
`langgraph.json`에서 `./src/agent/graph.py:graph` 형태의 파일 경로를 사용하면 Python이 해당 파일을 스크립트로 인식.

### ✅ 해결 방법

**1단계: `langgraph.json` 수정**
```json
{
    "graphs": {
        "agent": "src.agent.graph:graph"  // 파일 경로 → 모듈 경로
    }
}
```

**2단계: 절대 import로 변경**
```python
# Before (상대 import)
from .state import AgentState
from .nodes import research_node

# After (절대 import)
from src.agent.state import AgentState
from src.agent.nodes import research_node
```

**3단계: `__init__.py` 추가**
```
src/
├── __init__.py          ← 추가
└── agent/
    ├── __init__.py
    └── ...
```

---

## 2. Supervisor 무한 루프 (Recursion Limit)

### 🔴 문제 상황
```
Error: Recursion limit of 25 reached without hitting a stop condition
```

사용자 질문 시 Supervisor가 계속 `Researcher`로 라우팅하며 무한 반복.

### 🔍 원인 분석
Supervisor의 프롬프트가 너무 간단하여 LLM이 `FINISH` 조건을 제대로 판단하지 못함.

```python
# 기존 프롬프트 (너무 모호함)
"Given the user request, respond with the worker to act next."
```

### ✅ 해결 방법

**1단계: Supervisor 프롬프트 개선**
```python
supervisor_prompt = f"""You are a supervisor managing workers: {members}.

RULES:
1. If user asks a QUESTION that needs research -> route to "Researcher"
2. If you need content written/summarized -> route to "Writer"  
3. If a worker has ALREADY responded -> route to "FINISH"
4. NEVER route to the same worker twice in a row

Worker already responded this turn: {worker_responded_this_turn}
"""
```

**2단계: 안전 장치 추가**
```python
# Worker가 이미 응답했으면 강제 FINISH
if worker_responded_this_turn and next_agent in members:
    print("⚠️ Forcing FINISH: worker already responded")
    next_agent = "FINISH"
```

---

## 3. Researcher 검색 미수행

### 🔴 문제 상황
Researcher가 실제 검색을 수행하지 않고 "구체적으로 질문해주세요"라고만 응답.

```
사용자: "비전 AI 모델 알려줘"
Researcher: "어떤 점이 궁금하신가요? 특정 분야에 관심이 있으신가요?"
```

### 🔍 원인 분석
`create_react_agent`에 시스템 프롬프트가 없어서 LLM이 도구 사용 대신 질문 회피를 선택.

### ✅ 해결 방법

**시스템 메시지 주입**
```python
RESEARCHER_PROMPT = """You are a professional researcher agent.

YOUR TASK:
1. ALWAYS use the tavily_search tool to find information
2. NEVER ask for clarification - just search for what the user asked
3. Search in English for better results, then respond in Korean

IMPORTANT: You MUST use the search tool. Do NOT respond without searching first.
"""

def research_node(state: AgentState) -> dict:
    from langchain_core.messages import SystemMessage
    
    # 시스템 메시지를 맨 앞에 추가
    messages_with_prompt = [
        SystemMessage(content=RESEARCHER_PROMPT)
    ] + list(state["messages"])
    
    modified_state = {"messages": messages_with_prompt}
    result = research_agent.invoke(modified_state)
    ...
```

**참고**: `create_react_agent`의 최신 버전은 `state_modifier` 파라미터를 지원하지 않으므로, 노드 함수 내에서 직접 SystemMessage를 주입해야 함.

---

## 4. 멀티턴 대화 시 즉시 FINISH

### 🔴 문제 상황
첫 번째 질문은 정상 작동하지만, 두 번째 질문에서 Supervisor가 즉시 FINISH로 라우팅.

```
Turn 1: 질문 → Researcher → 응답 → FINISH ✅
Turn 2: 질문 → FINISH (Researcher 미호출!) ❌
```

### 🔍 원인 분석
`worker_responded` 체크 로직이 **전체 대화 히스토리**를 확인함.
Turn 1에서 Researcher가 응답했으므로, Turn 2에서도 "이미 응답했다"고 판단.

```python
# 잘못된 로직
for msg in reversed(messages):  # 전체 히스토리 확인
    if msg.name in members:
        worker_responded = True  # Turn 1의 응답도 감지됨!
```

### ✅ 해결 방법

**"마지막 Human 메시지 이후"만 확인하도록 수정**

```python
worker_responded_this_turn = False
last_human_idx = -1

# 마지막 Human 메시지 위치 찾기
for i, msg in enumerate(messages):
    if isinstance(msg, HumanMessage):
        last_human_idx = i

# 마지막 Human 메시지 "이후"의 Worker 응답만 확인
if last_human_idx >= 0:
    for msg in messages[last_human_idx + 1:]:
        if hasattr(msg, 'name') and msg.name in members:
            worker_responded_this_turn = True
            break
```

**개선된 흐름:**
```
Turn 1: 질문 → Researcher → 응답 → FINISH ✅
Turn 2: 질문 → (last_human_idx 갱신) → Researcher 호출 ✅
```

---

## 📋 최종 체크리스트

| 문제 | 해결 파일 | 핵심 수정 |
|------|----------|----------|
| Import 에러 | `langgraph.json`, 모든 `.py` | 상대 → 절대 import |
| 무한 루프 | `nodes.py` (supervisor_node) | 프롬프트 + 강제 FINISH |
| 검색 미수행 | `nodes.py` (research_node) | SystemMessage 주입 |
| 멀티턴 FINISH | `nodes.py` (supervisor_node) | `worker_responded_this_turn` |

---

## 🔗 관련 파일

- [`src/agent/nodes.py`](../langgraph_web_ui/langgraph_server/src/agent/nodes.py) - 노드 구현
- [`src/agent/graph.py`](../langgraph_web_ui/langgraph_server/src/agent/graph.py) - 그래프 정의
- [`langgraph.json`](../langgraph_web_ui/langgraph_server/langgraph.json) - CLI 설정
