```
"""
LangGraph Multi-Agent: Network (Mesh) Pattern
==============================================
이 예제는 중앙 감독자 없이 에이전트끼리 서로 작업을 넘기는(Handoff) 네트워크(Mesh) 패턴입니다.
각 에이전트는 자신의 tools 목록에 "다른 에이전트로 이동하는 도구"를 가지고 있습니다.

핵심 개념:
1. Handoff Tool (이관 도구):
   - "Researcher에게 전달", "Writer에게 전달"과 같은 특수 도구
   - 이 도구가 호출되면 라우터가 이를 감지하여 해당 에이전트 노드로 실행 흐름을 옮깁니다.

2. Decentralized Logic (탈중앙화 로직):
   - 중앙 관리자 없이, 각 에이전트(LLM)가 스스로 판단하여 다음 작업을 누구에게 넘길지 결정합니다.

실행 흐름:
[User] -> [Researcher] --(정보 부족)--> [Search Tool] -> [Researcher]
              |
         (정보 충분, 작성 요청)
              ↓
           [Writer] --(작성 완료)--> [END]
"""

import os
import dotenv
from typing import Annotated, List, Literal, TypedDict, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import ToolNode
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
# 1. 설정 및 도구 (Configs & Tools)
# =============================================================================
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# --- Handoff Tools (이관 도구) ---
# 이 도구들은 실제 작업을 수행하기보다는, 그래프의 상태(다음 노드)를 변경하는 신호 역할을 합니다.

def transfer_to_writer():
    """Transfer control to the Writer agent."""
    return "Transferred to Writer"

def transfer_to_researcher():
    """Transfer control to the Researcher agent."""
    return "Transferred to Researcher"

# 검색 도구
search_tool = TavilySearchResults(k=2)

# --- 에이전트별 사용할 도구 정의 ---
# Researcher: 검색 가능 + Writer에게 넘기기 가능
researcher_tools = [search_tool, transfer_to_writer]

# Writer: 검색 불가(제한) + Researcher에게 (재)요청 가능
writer_tools = [transfer_to_researcher] 

# LLM에 도구 바인딩
researcher_model = llm.bind_tools(researcher_tools)
writer_model = llm.bind_tools(writer_tools)


# --- 시스템 프롬프트 (각 에이전트의 역할 정의) ---
detailed_researcher_prompt = """You are a Researcher. 
1. Search for information requested by the user. 
2. If you have found enough info, transfer to the Writer to draft the response.
3. If you need the Writer to explain something or format it, transfer to them."""

detailed_writer_prompt = """You are a Writer. 
1. Write a high-quality response based on the research provided.
2. If you need more information, transfer back to the Researcher.
3. If you are done, just output the final answer."""


# =============================================================================
# 2. 상태(State) 및 노드(Nodes) 정의
# =============================================================================
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    sender: str # 마지막으로 메시지를 보낸 에이전트 (선택사항)

def researcher(state: AgentState):
    """Researcher 에이전트 노드"""
    print("---[Node] Researcher 동작---")
    res = researcher_model.invoke([SystemMessage(content=detailed_researcher_prompt)] + state["messages"])
    return {"messages": [res], "sender": "researcher"}

def writer(state: AgentState):
    """Writer 에이전트 노드"""
    print("---[Node] Writer 동작---")
    res = writer_model.invoke([SystemMessage(content=detailed_writer_prompt)] + state["messages"])
    return {"messages": [res], "sender": "writer"}

# 일반 도구 실행 노드 (검색 등)
# Handoff 도구는 조건부 엣지에서 처리되므로 여기서는 실제 도구만 실행하면 됩니다.
tool_node = ToolNode([search_tool])


# =============================================================================
# 3. 라우팅 로직 (Routing Logic)
# =============================================================================
def router(state: AgentState) -> Literal["call_tool", "enter_writer", "enter_researcher", "__end__"]:
    """
    마지막 메시지의 tool_calls를 분석하여 다음 이동 경로를 결정합니다.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        # 도구 호출이 있는 경우
        tool_name = last_message.tool_calls[0]["name"]
        
        # Handoff 도구인지 확인
        if tool_name == "transfer_to_writer":
            return "enter_writer"
        elif tool_name == "transfer_to_researcher":
            return "enter_researcher"
        else:
            return "call_tool" # 일반 도구(검색 등)는 ToolNode로 보냄
            
    return "__end__" # 도구 호출이 없으면 최종 답변으로 간주하고 종료


# =============================================================================
# 4. 그래프(Graph) 구축
# =============================================================================
workflow = StateGraph(AgentState)

workflow.add_node("researcher", researcher)
workflow.add_node("writer", writer)
workflow.add_node("tools", tool_node)

# 시작점: Researcher부터 시작
workflow.add_edge(START, "researcher")

# Researcher의 출력에 따른 분기
workflow.add_conditional_edges(
    "researcher",
    router,
    {
        "enter_writer": "writer",
        "enter_researcher": "researcher", # 자기 자신에게 돌아오는 경우 (드묾)
        "call_tool": "tools",
        "__end__": END
    }
)

# Writer의 출력에 따른 분기
workflow.add_conditional_edges(
    "writer",
    router,
    {
        "enter_writer": "writer",
        "enter_researcher": "researcher",
        "call_tool": "tools",
        "__end__": END
    }
)

# 도구 실행 후에는, 도구를 호출했던 에이전트(여기선 편의상 Researcher)로 돌아감
# (더 복잡한 구조에서는 sender 필드를 보고 동적으로 돌아갈 곳을 정할 수도 있음)
workflow.add_edge("tools", "researcher")

app = workflow.compile()


# =============================================================================
# 5. 실행(Execution)
# =============================================================================
def main():
    print("Initializing Multi-Agent Network (Mesh)...")
    try:
        with open("network_graph.png", "wb") as f:
            f.write(app.get_graph().draw_mermaid_png())
        print("Graph saved to 'network_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    user_input = "Find a short summary of the philosophy of Stoicism and write a haiku about it."
    print(f"\n--- User Query: {user_input} ---\n")
    
    events = app.stream(
        {"messages": [HumanMessage(content=user_input)]},
        {"recursion_limit": 20} # 무한 루프 방지용 제한
    )
    
    for event in events:
        for k, v in event.items():
            if "messages" in v:
                last_msg = v["messages"][-1]
                
                # 메시지 출력 (누가 보냈는지와 내용)
                sender = v.get("sender", "Tool")
                print(f"[{sender}]: {last_msg.content}")
                
                # 도구 호출이 있으면 표시
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                     for tc in last_msg.tool_calls:
                        print(f"  └─ 🚀 Action: {tc['name']}")

    print("\n--- Final Sequence Completed ---")
    
if __name__ == "__main__":
    main()
```
