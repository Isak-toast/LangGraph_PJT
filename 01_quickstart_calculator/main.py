"""
LangGraph 01: Quickstart Calculator Agent
==========================================
이 예제는 LangGraph의 기본 개념을 설명하는 계산기 에이전트입니다.

핵심 개념:
1. Tool (도구): LLM이 호출할 수 있는 함수 (add, multiply, divide)
2. State (상태): 그래프 전체에서 공유되는 데이터 (메시지 히스토리)
3. Node (노드): 상태를 변경하는 함수 (chatbot, tool_node)
4. Edge (엣지): 노드 간의 연결 관계 (조건부/무조건부)
5. Graph (그래프): 노드와 엣지로 구성된 워크플로우

실행 흐름 (ReAct 패턴):
┌─────────┐    도구 호출 필요    ┌─────────┐
│ chatbot │ ─────────────────→ │  tools  │
│  (LLM)  │ ←───────────────── │ (실행)  │
└─────────┘    결과 반환        └─────────┘
     │
     │ 도구 호출 불필요 (최종 답변)
     ▼
   [END]
"""

import os
import dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage, HumanMessage
from langchain_core.tools import tool

# 환경 변수 로드 (.env 파일에서 GOOGLE_API_KEY 등을 읽어옴)
dotenv.load_dotenv()

# =============================================================================
# LangSmith 추적 설정 (선택사항)
# =============================================================================
# LangSmith: LangChain의 관측성(Observability) 플랫폼
# - 그래프 실행 흐름을 시각적으로 추적
# - 각 노드의 입력/출력 확인
# - 성능 모니터링 및 디버깅
#
# 설정 방법:
# 1. https://smith.langchain.com 에서 계정 생성
# 2. Settings > API Keys에서 API 키 발급
# 3. .env 파일에 아래 환경변수 추가:
#    LANGCHAIN_TRACING_V2=true
#    LANGCHAIN_API_KEY=your_api_key
#    LANGCHAIN_PROJECT=langgraph-calculator (프로젝트 이름)
#
# 환경변수가 설정되면 자동으로 추적이 활성화됩니다.
import os
if os.getenv("LANGCHAIN_TRACING_V2") == "true":
    print("📊 LangSmith 추적이 활성화되었습니다.")
    print(f"   프로젝트: {os.getenv('LANGCHAIN_PROJECT', 'default')}")


# =============================================================================
# 1. 도구(Tool) 정의
# =============================================================================
# @tool 데코레이터: 함수를 LLM이 호출할 수 있는 도구로 변환
# - docstring은 LLM에게 도구 설명으로 전달됨 (영어로 작성 권장)
# - 타입 힌트는 LLM에게 파라미터 정보로 전달됨

@tool
def add(a: int, b: int) -> int:
    """Adds a and b."""  # LLM이 이 설명을 보고 언제 이 도구를 쓸지 결정
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b."""
    return a * b

@tool
def divide(a: int, b: int) -> float:
    """Divides a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

# 도구 리스트와 이름으로 접근할 수 있는 딕셔너리 생성
tools = [add, multiply, divide]
tools_by_name = {t.name: t for t in tools}  # {"add": add, "multiply": multiply, ...}


# =============================================================================
# 2. 상태(State) 정의
# =============================================================================
# State: 그래프 실행 동안 공유되는 데이터 구조
# - TypedDict를 사용하여 타입 안전성 확보
# - Annotated와 add_messages를 사용하여 메시지 자동 누적

class State(TypedDict):
    # add_messages: 새 메시지를 기존 리스트에 자동으로 추가하는 리듀서 함수
    # 예: state["messages"] = [msg1] 상태에서 {"messages": [msg2]} 반환하면
    #     결과는 [msg1, msg2]가 됨 (덮어쓰기가 아닌 누적)
    messages: Annotated[list, add_messages]


# =============================================================================
# 3. 노드(Node) 정의
# =============================================================================
# 노드: 상태를 받아서 상태 업데이트를 반환하는 함수
# - 각 노드는 state를 파라미터로 받음
# - 딕셔너리를 반환하여 상태의 일부를 업데이트

# LLM 초기화 (temperature=0: 결정론적 출력)
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# bind_tools: LLM에게 사용 가능한 도구들을 알려줌
# → LLM은 도구 호출이 필요하면 tool_calls를 포함한 AIMessage를 반환
llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    """
    챗봇 노드: LLM을 호출하여 응답 생성
    
    동작:
    1. 현재 메시지 히스토리를 LLM에게 전달
    2. LLM이 응답 생성 (텍스트 또는 도구 호출 요청)
    3. 응답을 messages에 추가
    
    반환값 예시:
    - 일반 응답: AIMessage(content="답변 텍스트", tool_calls=[])
    - 도구 호출: AIMessage(content="", tool_calls=[{name: "add", args: {a:1, b:2}}])
      ※ 도구 호출 시 content가 비어있음! (이것이 [ai]: 가 빈 이유)
    """
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def tool_node(state: State):
    """
    도구 노드: LLM이 요청한 도구를 실제로 실행
    
    동작:
    1. 마지막 AIMessage에서 tool_calls 추출
    2. 각 도구 호출을 실행
    3. 결과를 ToolMessage로 래핑하여 반환
    
    ToolMessage 구조:
    - content: 도구 실행 결과 (문자열)
    - name: 도구 이름
    - tool_call_id: 어떤 호출에 대한 응답인지 식별 (LLM이 생성한 ID)
    """
    outputs = []
    last_message = state["messages"][-1]  # 가장 최근 메시지 (AIMessage)
    
    # AIMessage.tool_calls: LLM이 요청한 도구 호출 목록
    # 예: [{"name": "multiply", "args": {"a": 50, "b": 25}, "id": "xxx"}]
    for tool_call in last_message.tool_calls:
        try:
            # 도구 이름으로 실제 함수 찾아서 실행
            tool_result = tools_by_name[tool_call["name"]].invoke(tool_call)
            outputs.append(
                ToolMessage(
                    content=str(tool_result),  # 결과를 문자열로 변환
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],  # 호출 ID 매칭 필수!
                )
            )
        except Exception as e:
            # 도구 실행 실패 시 에러 메시지 반환
            outputs.append(
                ToolMessage(
                    content=f"Error: {e}",
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
            
    return {"messages": outputs}


# =============================================================================
# 4. 라우팅(Routing) 정의
# =============================================================================
# 조건부 엣지에서 사용할 라우팅 함수
# - 상태를 보고 다음에 어떤 노드로 갈지 결정

def should_continue(state: State):
    """
    chatbot 노드 이후 어디로 갈지 결정
    
    - tool_calls가 있으면 → "tools" 노드로 이동 (도구 실행)
    - tool_calls가 없으면 → END (실행 종료, 최종 답변)
    """
    last_message = state["messages"][-1]
    
    # AIMessage.tool_calls: 리스트 (비어있으면 도구 호출 없음)
    if last_message.tool_calls:
        return "tools"
    return END


# =============================================================================
# 5. 그래프(Graph) 구축
# =============================================================================
# StateGraph: 상태 기반 그래프 생성기
graph_builder = StateGraph(State)

# 노드 추가: (노드 이름, 노드 함수)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

# 엣지 추가
# 1) START → chatbot: 그래프 시작 시 chatbot 노드부터 실행
graph_builder.add_edge(START, "chatbot")

# 2) chatbot → (조건부): should_continue 함수로 분기 결정
#    - "tools"로 가거나 END로 종료
graph_builder.add_conditional_edges("chatbot", should_continue, ["tools", END])

# 3) tools → chatbot: 도구 실행 후 다시 chatbot으로 (루프)
#    → LLM이 도구 결과를 보고 추가 도구 호출 또는 최종 답변 생성
graph_builder.add_edge("tools", "chatbot")

# 그래프 컴파일: 실행 가능한 상태로 변환
graph = graph_builder.compile()


# =============================================================================
# 6. 실행(Execution)
# =============================================================================
def main():
    print("Initializing Calculator Agent...")
    
    # 그래프 시각화 (PNG 이미지로 저장)
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        with open("calculator_graph.png", "wb") as f:
            f.write(png_bytes)
        print("Graph saved to 'calculator_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    # 사용자 입력
    user_input = "Calculate (50 * 25) + 100"
    print(f"\n--- User Query: {user_input} ---")
    
    # graph.stream(): 실시간으로 각 노드 실행 결과를 스트리밍
    # - stream_mode="values": 각 단계의 전체 상태를 반환
    # - stream_mode="updates": 변경된 부분만 반환 (기본값)
    events = graph.stream(
        {"messages": [HumanMessage(content=user_input)]},  # 초기 상태
        stream_mode="values"
    )
    
    # 각 이벤트(상태 변화)를 순회하며 출력
    for event in events:
        last_msg = event["messages"][-1]
        
        # 메시지 타입별로 다르게 출력
        if last_msg.type == "human":
            print(f"[human]: {last_msg.content}")
        
        elif last_msg.type == "ai":
            # AI 메시지: content 또는 tool_calls 출력
            if last_msg.content:
                print(f"[ai]: {last_msg.content}")
            
            # 도구 호출 요청이 있으면 상세 정보 출력
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                for tc in last_msg.tool_calls:
                    args_str = ", ".join(f"{k}={v}" for k, v in tc['args'].items())
                    print(f"  └─ 🔧 도구 호출: {tc['name']}({args_str})")
        
        elif last_msg.type == "tool":
            # 도구 결과: 이름과 결과값 출력
            print(f"[tool] {last_msg.name}: {last_msg.content}")


if __name__ == "__main__":
    main()
