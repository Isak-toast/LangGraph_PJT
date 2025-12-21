
"""
LangGraph 04: Human-in-the-loop (HITL)
=======================================
이 예제는 실행 중간에 사람의 개입(Human-in-the-loop)을 처리하는 방법을 보여줍니다.

핵심 개념:
1. interrupt_before=["node_name"]: 특정 노드 실행 직전에 그래프를 멈춥니다.
   - 용도: 민감한 작업(API 호출, 결제 등) 전 사용자 승인 대기
   
2. Checkpointer (필수): 실행 상태를 저장하고 멈추기 위해 반드시 필요합니다.

3. 승인/거부 흐름:
   - 그래프 중단 -> 사용자 입력(승인/거부) -> 그래프 재개(resume)
   - 재개 시 None을 입력으로 주면 멈췄던 지점부터 계속 실행됩니다.

실행 흐름:
[User Request] -> [chatbot] --(Tool Call)--> [PAUSE]
                                              ↓
                                        [Human Approval]
                                              ↓
                                          [tools] -> [chatbot] -> [END]
"""

import os
import dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool
from pathlib import Path

# 환경 변수 로드
script_dir = Path(__file__).parent
project_root = script_dir.parent
env_file = project_root / ".env"
if not env_file.exists():
    env_file = script_dir / ".env"
dotenv.load_dotenv(env_file)

# LangSmith 추적 설정
if os.getenv("LANGCHAIN_TRACING_V2") == "true":
    print("📊 LangSmith 추적이 활성화되었습니다.")
    print(f"   프로젝트: {os.getenv('LANGCHAIN_PROJECT', 'default')}")


# =============================================================================
# 1. 도구(Tool) 정의
# =============================================================================
@tool
def sensitive_action(data: str) -> str:
    """A tool that requires approval."""
    # 실제로 실행되면 안 되는 민감한 작업을 시뮬레이션
    return f"ACTION EXECUTED: Processed '{data}'"

tools = [sensitive_action]
tools_by_name = {t.name: t for t in tools}


# =============================================================================
# 2. 상태(State) 정의
# =============================================================================
class State(TypedDict):
    messages: Annotated[list, add_messages]


# =============================================================================
# 3. 노드(Node) 정의
# =============================================================================
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

def tool_node(state: State):
    outputs = []
    last_message = state["messages"][-1]
    
    for tool_call in last_message.tool_calls:
        # 도구 실행
        tool_result = tools_by_name[tool_call["name"]].invoke(tool_call)
        outputs.append(
            ToolMessage(
                content=str(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
            
    return {"messages": outputs}

def should_continue(state: State):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END


# =============================================================================
# 4. 그래프(Graph) 구축 (with HITL Config)
# =============================================================================
graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", should_continue, ["tools", END])
graph_builder.add_edge("tools", "chatbot")

# !!! HUMAN-IN-THE-LOOP 설정 !!!
# 1. 상태 저장을 위한 checkpointer
checkpointer = MemorySaver()

# 2. tools 노드 실행 전에 인터럽트(중단) 걸기
graph = graph_builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["tools"] 
)


# =============================================================================
# 5. 실행(Execution)
# =============================================================================
def main():
    print("Initializing Human-in-the-loop Agent...")
    
    # 시각화
    try:
        with open("human_loop_graph.png", "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        print("Graph saved to 'human_loop_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")
        
    config = {"configurable": {"thread_id": "thread-2"}}

    # -------------------------------------------------------------------------
    # 단계 1: 요청 시작 (도구 호출 직전까지 실행됨)
    # -------------------------------------------------------------------------
    user_input = "Please execute the sensitive action with data 'Secret123'."
    print(f"\n--- [Step 1] User Request: {user_input} ---")
    
    # 그래프 실행: interrupt_before="tools" 때문에 도구 실행 직전에 멈춤
    for event in graph.stream(
        {"messages": [HumanMessage(content=user_input)]},
        config=config, 
        stream_mode="values"
    ):
        last_msg = event["messages"][-1]
        print(f"[{last_msg.type}] {last_msg.content}")
        
    # -------------------------------------------------------------------------
    # 단계 2: 상태 확인 및 승인
    # -------------------------------------------------------------------------
    snapshot = graph.get_state(config)
    print(f"\n--- [Step 2] Graph Status (Next Node): {snapshot.next} ---")
    
    # snapshot.next에는 다음 실행될 노드 이름들이 들어있음 (여기서는 'tools')
    if "tools" in snapshot.next:
        print(">> 🛑 Graph paused before 'tools'. Waiting for approval...")
    
    # 사용자 승인 받기
    approval = input("\nDo you approve this action? (y/n): ")
    
    if approval.lower() == "y":
        # ---------------------------------------------------------------------
        # 단계 3: 실행 재개 (Approve)
        # ---------------------------------------------------------------------
        print(">> ✅ Action Approved. Resuming graph...")
        
        # None을 입력으로 넘기면 멈췄던 지점부터 계속 실행
        # (새로운 입력을 주지 않고, 기존 상태 그대로 진행)
        for event in graph.stream(None, config=config, stream_mode="values"):
            last_msg = event["messages"][-1]
            print(f"[{last_msg.type}] {last_msg.content}")
    else:
        # ---------------------------------------------------------------------
        # 단계 3: 거부 (Deny)
        # ---------------------------------------------------------------------
        print(">> ❌ Action Denied.")
        # 여기서 끝내면 도구는 실행되지 않음
        # 필요하다면 다른 경로로 우회하거나 취소 메시지를 추가할 수도 있음

if __name__ == "__main__":
    main()
