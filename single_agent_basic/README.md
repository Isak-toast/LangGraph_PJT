# 단일 에이전트 (Basic Single Agent)

가장 기본적인 형태의 **ReAct(Reason-Act) 에이전트**입니다. 도구(웹 검색)를 사용하여 질문에 답하는 단일 그래프 구조입니다.

## LangGraph란?

LangGraph는 LangChain 팀에서 개발한 라이브러리로, **상태 기반의 순환 그래프 구조**를 통해 복잡한 AI 에이전트 시스템을 구축할 수 있게 해줍니다. 이 예제는 LangGraph의 가장 기초적인 사용법을 보여줍니다.

## 이 예제에서 배우는 것

- **ReAct 패턴**: 추론(Reason) → 행동(Act) → 관찰(Observe)의 반복 사이클
- **create_react_agent**: LangGraph의 고수준 API로 에이전트를 쉽게 생성하는 방법
- **도구 호출**: LLM이 필요에 따라 외부 도구(웹 검색)를 호출하는 구조

## 아키텍처 (Architecture)

```mermaid
graph TD
    Start((Start)) --> Agent

    subgraph "Single Agent Graph"
        Agent[Agent Node<br/>(LLM + Tool calling)] <--> Tools[Tools Node<br/>(Tavily Search)]
    end

    Agent -- "Answer (End)" --> End((End))
```

---

## 📝 코드 상세 분석

### 1. 환경 설정 및 임포트

```python
import os
import dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# Load env vars from root or current dir
dotenv.load_dotenv()
```

**필요한 환경 변수**:
- `GOOGLE_API_KEY`: Gemini API 키
- `TAVILY_API_KEY`: Tavily 검색 API 키

---

### 2. LLM 및 도구 설정

```python
# 1. Setup LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# 2. Setup Tools
# Note: explicit max_results helps keep context size manageable
tavily_tool = TavilySearchResults(max_results=3)
tools = [tavily_tool]
```

**설명**:
- `temperature=0`: 결정론적 응답 (항상 같은 입력에 같은 출력)
- `max_results=3`: 검색 결과를 3개로 제한하여 컨텍스트 크기 관리

---

### 3. 에이전트 생성 (핵심!)

```python
# 3. Create Agent (LangGraph Prebuilt)
# create_react_agent creates a graph with a message state and tool calling node
agent = create_react_agent(
    llm, 
    tools, 
    prompt="You are a helpful AI assistant. Use tools to find up-to-date information."
)
```

**`create_react_agent`가 자동으로 만드는 것**:
- 메시지 상태를 관리하는 `State`
- LLM을 호출하는 `agent` 노드
- 도구를 실행하는 `tools` 노드
- 도구 호출 여부에 따른 조건부 라우팅

> 💡 `01_quickstart_calculator`에서 수동으로 정의한 모든 것이 이 한 줄로 자동 생성됩니다!

---

### 4. 그래프 시각화 (선택)

```python
# 4. Generate Visualization (Optional)
try:
    png_bytes = agent.get_graph().draw_mermaid_png()
    with open("agent_graph.png", "wb") as f:
        f.write(png_bytes)
    print("Graph visualization saved to 'agent_graph.png'")
except Exception as e:
    print(f"Skipping visualization: {e}")
```

**설명**: `get_graph().draw_mermaid_png()`로 그래프를 PNG 이미지로 저장

---

### 5. 스트리밍 실행

```python
# 5. Run
user_input = "Who won the World Series in 2024? If not played yet, who won in 2023?"
messages = [HumanMessage(content=user_input)]

print("--- Streaming Execution ---")
for step in agent.stream({"messages": messages}, stream_mode="values"):
    # The stream returns the current state (list of messages)
    current_messages = step["messages"]
    last_message = current_messages[-1]
    
    # Determine strict type for cleaner printing
    msg_type = last_message.type
    content = last_message.content
    
    print(f"\n[{msg_type.upper()}]: {content}")
```

**실행 흐름**:
1. 사용자 질문 입력
2. Agent가 정보가 필요하다고 판단 → Tavily 검색 호출
3. 검색 결과를 받아옴
4. 검색 결과를 바탕으로 최종 답변 생성

---

## 활용 사례

1. **질문 답변 시스템**: 웹 검색을 통해 최신 정보를 기반으로 답변
2. **챗봇의 기초**: 도구를 사용하는 대화형 AI의 기본 구조
3. **정보 검색 자동화**: 사용자 질문에 맞춰 자동으로 검색하고 요약

## `create_react_agent` vs 직접 구현 비교

| 항목 | create_react_agent | 직접 구현 |
|------|--------------------|----------|
| 코드량 | 1줄 | 30줄+ |
| 유연성 | 제한적 | 완전한 제어 |
| 학습곡선 | 낮음 | 높음 |
| 사용 시기 | 빠른 프로토타이핑 | 세밀한 제어 필요시 |

## 빠른 시작 (Quick Start)

### 설치 및 실행

1.  폴더 이동:

    ```bash
    cd single_agent_basic
    ```

2.  의존성 설치:

    ```bash
    pip install -r requirements.txt
    ```

3.  환경 변수 (`.env`) 설정 (필요시 루트의 .env 복사):

    ```bash
    cp ../multi_agent_supervisor/.env .
    ```

4.  실행:
    ```bash
    python main.py
    ```

## 실행 예시

> "Who won the World Series in 2024? If not played yet, who won in 2023?"

**예상 출력**:
```
[HUMAN]: Who won the World Series in 2024?...
[AI]: (searching web...)
[TOOL]: Search results about World Series...
[AI]: The Los Angeles Dodgers won the 2024 World Series...
```

---

*LangGraph 튜토리얼 프로젝트의 일부입니다.*
