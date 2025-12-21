# 데이터 영속성/메모리 (Persistence/Memory)

LangGraph의 **Checkpointer** 기능을 사용하여 대화 상태를 저장하고 불러오는 방법을 다룹니다.

## LangGraph란?

LangGraph는 LangChain 팀에서 개발한 라이브러리로, **상태 기반의 순환 그래프 구조**를 통해 복잡한 AI 에이전트 시스템을 구축할 수 있게 해줍니다. 영속성(Persistence)은 대화 맥락을 유지하는 핵심 기능입니다.

## 이 예제에서 배우는 것

- **Checkpointer**: 그래프 상태를 저장하고 복원하는 메커니즘
- **MemorySaver**: 테스트용 인메모리 저장소
- **thread_id**: 사용자 세션을 구분하는 고유 식별자

## 핵심 개념

| 컴포넌트 | 설명 |
|----------|------|
| **MemorySaver** | 인메모리 저장소 (테스트/개발용) |
| **SqliteSaver** | SQLite 기반 저장소 (경량 프로덕션) |
| **PostgresSaver** | PostgreSQL 기반 저장소 (대규모 프로덕션) |
| **thread_id** | 사용자 세션을 구분하는 고유 ID |

---

## 📝 코드 상세 분석

### 1. 그래프 정의 (기본)

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
```

---

### 2. Checkpointer 추가 (핵심!)

```python
from langgraph.checkpoint.memory import MemorySaver

# !!! ADD PERSISTENCE !!!
# SQLite, Postgres, etc. can be used. MemorySaver is in-memory for testing.
checkpointer = MemorySaver()

# Compile with checkpointer
graph = graph_builder.compile(checkpointer=checkpointer)
```

**핵심 코드**: `compile(checkpointer=checkpointer)`

**MemorySaver의 특징**:
- 메모리에 저장되므로 프로세스 종료 시 데이터 손실
- 테스트와 개발에 적합
- 프로덕션에서는 `SqliteSaver` 또는 `PostgresSaver` 사용

---

### 3. Thread ID로 세션 관리

```python
# Thread ID defines the "session"
config = {"configurable": {"thread_id": "thread-1"}}

# Turn 1
input_1 = "Hi, I'm Bob."
for event in graph.stream(
    {"messages": [HumanMessage(content=input_1)]},
    config=config,  # ← thread_id 포함
    stream_mode="values"
):
    last_msg = event["messages"][-1]
    print(f"[{last_msg.type}]: {last_msg.content}")
```

**중요**: `config`에 `thread_id`를 포함하여 세션을 식별

---

### 4. 이전 대화 이어가기

```python
print("\n... Simulating user returning later ...\n")

# Turn 2 (Same Thread ID)
input_2 = "What is my name?"

# We do NOT pass the previous history manually.
# LangGraph fetches it from the checkpointer using 'thread-1'.
for event in graph.stream(
    {"messages": [HumanMessage(content=input_2)]},
    config=config,  # ← 같은 thread_id 사용
    stream_mode="values"
):
    last_msg = event["messages"][-1]
    # We expect a content roughly like "Your name is Bob."
    print(f"[{last_msg.type}]: {last_msg.content}")
```

**마법이 일어나는 순간**:
- 두 번째 요청에서 이전 대화 내용을 **직접 전달하지 않음**
- LangGraph가 `thread_id`로 checkpointer에서 자동으로 불러옴
- AI가 "Bob"이라는 이름을 기억하고 답변

---

### 5. 상태 스냅샷 확인

```python
print("\n--- Checkpoint State Snapshot ---")
snapshot = graph.get_state(config)
print(f"Snapshot Created At: {snapshot.created_at}")
print(f"Snapshot Values (Messages Count): {len(snapshot.values['messages'])}")
```

**`get_state()`로 확인할 수 있는 것**:
- `created_at`: 마지막 체크포인트 생성 시간
- `values`: 현재 상태 (메시지 리스트 등)
- `next`: 다음에 실행될 노드들

---

## 동작 원리 다이어그램

```mermaid
sequenceDiagram
    participant User
    participant Graph
    participant Checkpointer

    Note over User,Checkpointer: Turn 1
    User->>Graph: "Hi, I'm Bob." (thread_id: thread-1)
    Graph->>Checkpointer: Load state for thread-1
    Checkpointer-->>Graph: (empty)
    Graph->>Graph: Process message
    Graph->>Checkpointer: Save state
    Graph-->>User: "Hello Bob!"

    Note over User,Checkpointer: Turn 2 (Later)
    User->>Graph: "What is my name?" (thread_id: thread-1)
    Graph->>Checkpointer: Load state for thread-1
    Checkpointer-->>Graph: [Previous messages]
    Graph->>Graph: Process with context
    Graph->>Checkpointer: Save updated state
    Graph-->>User: "Your name is Bob."
```

---

## 프로덕션 사용 예시

### SQLite 사용

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 파일 기반 저장
checkpointer = SqliteSaver.from_conn_string("./chat_history.db")
graph = graph_builder.compile(checkpointer=checkpointer)
```

### PostgreSQL 사용

```python
from langgraph.checkpoint.postgres import PostgresSaver

# 연결 문자열로 저장소 생성
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:password@localhost:5432/dbname"
)
graph = graph_builder.compile(checkpointer=checkpointer)
```

---

## 활용 사례

1. **대화형 챗봇**: 사용자가 이전 대화를 이어서 진행할 수 있는 챗봇
2. **장기 작업**: 중단된 작업을 나중에 다시 시작
3. **사용자별 맥락**: 여러 사용자의 독립적인 대화 맥락 관리
4. **세션 기반 서비스**: 로그인한 사용자별로 별도 대화 관리

## 빠른 시작

1.  폴더 이동:
    ```bash
    cd 03_persistence
    ```
2.  실행:
    ```bash
    # (최초 실행 시) cp ../multi_agent_supervisor/.env .
    python main.py
    ```

## 실행 예시

**예상 출력**:
```
--- User (Turn 1): Hi, I'm Bob. ---
[human]: Hi, I'm Bob.
[ai]: Hello Bob! Nice to meet you. How can I help you today?

... Simulating user returning later ...

--- User (Turn 2): What is my name? ---
[human]: What is my name?
[ai]: Your name is Bob.

--- Checkpoint State Snapshot ---
Snapshot Created At: 2024-01-15T10:30:45.123456
Snapshot Values (Messages Count): 4
```

---

*LangGraph 튜토리얼 프로젝트의 일부입니다.*
