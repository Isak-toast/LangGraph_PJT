
"""
LangGraph 05: Hierarchical Subgraphs
=====================================
이 예제는 복잡한 작업을 작은 단위로 나누어 처리하는 계층적(Hierarchical) 그래프 구조를 보여줍니다.

핵심 개념:
1. Subgraph (하위 그래프): 특정 작업을 전담하는 독립적인 그래프 (예: 리서치 팀)
   - 메인 그래프와 다른 별도의 State를 가질 수 있습니다.
   
2. Encapsulation (캡슐화): 메인 그래프는 하위 그래프의 내부 동작을 알 필요가 없습니다.
   - 단지 입력(Input)을 주고 결과(Output)를 받을 뿐입니다.

3. State Mapping: 서로 다른 State 스키마를 가진 그래프 간에 데이터를 전달할 때 매핑이 필요합니다.
   - Main State -> Subgraph State (입력 매핑)
   - Subgraph State -> Main State (출력 매핑)

구조:
[Manager (Main)] --> [Research Team (Subgraph)] --> [Manager]
                           ↓
                   [Search] -> [Summarize]

"""

import os
import dotenv
from typing import Annotated, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
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


# --- Shared Resources ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)


# =============================================================================
# 1. 하위 그래프 정의 (The "Research Team")
# =============================================================================

# 하위 그래프 전용 상태
class ResearchState(TypedDict):
    # 메인 그래프와 동일하게 messages를 쓰지만, 여기서는 독립적으로 관리된다고 가정
    messages: Annotated[list, add_messages]
    research_summary: str

def basic_search(state: ResearchState):
    """검색을 수행하는 노드 (시뮬레이션)"""
    return {"messages": [AIMessage(content="[SearchBot] LangGraph에 대한 정보를 찾았습니다.")]}

def summarizer(state: ResearchState):
    """검색 결과를 요약하는 노드"""
    return {"research_summary": "LangGraph는 LLM을 이용한 상태 기반 멀티 액터 애플리케이션 라이브러리입니다."}

# 하위 그래프 빌드
research_builder = StateGraph(ResearchState)
research_builder.add_node("search", basic_search)
research_builder.add_node("summarize", summarizer)

research_builder.add_edge(START, "search")
research_builder.add_edge("search", "summarize")
research_builder.add_edge("summarize", END)

# 하위 그래프 컴파일 (이 자체가 하나의 실행 가능한 '노드'처럼 동작)
research_graph = research_builder.compile()


# =============================================================================
# 2. 상위 그래프 정의 (The "Company")
# =============================================================================

# 상위 그래프 전용 상태
class CorporateState(TypedDict):
    messages: Annotated[list, add_messages]
    final_report: str

def manager(state: CorporateState):
    """작업을 할당하는 매니저 노드"""
    return {"messages": [AIMessage(content="[Manager] 리서치 팀에게 조사를 요청합니다.")]}

# 하위 그래프를 호출하는 래퍼 함수 (State Mapping 역할)
def call_research_team(state: CorporateState):
    """
    상위 그래프의 상태를 하위 그래프의 입력으로 변환하고,
    하위 그래프의 결과를 다시 상위 그래프의 상태로 변환합니다.
    """
    print("   >>> [Main] Research Team 서브그래프 호출 시작")
    
    # [입력 매핑] CorporateState -> ResearchState (필요한 데이터만 전달)
    # 여기서는 messages를 그대로 전달
    subgraph_input = {"messages": state["messages"]}
    
    # 하위 그래프 실행 (blocking call)
    result = research_graph.invoke(subgraph_input)
    
    print(f"   <<< [Main] Research Team 완료. 요약: {result['research_summary']}")
    
    # [출력 매핑] ResearchState -> CorporateState
    return {
        "messages": [AIMessage(content=f"[Manager] 보고를 받았습니다. 요약: {result['research_summary']}")],
        "final_report": result['research_summary']
    }

builder = StateGraph(CorporateState)
builder.add_node("manager", manager)
builder.add_node("research_team", call_research_team)

builder.add_edge(START, "manager")
builder.add_edge("manager", "research_team")
builder.add_edge("research_team", END)

graph = builder.compile()


# =============================================================================
# 3. 실행(Execution)
# =============================================================================
def main():
    print("Initializing Hierarchical Agent...\n")
    
    # 시각화
    try:
        with open("hierarchical_graph.png", "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        print("Graph saved to 'hierarchical_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")
    
    user_input = "Learn about LangGraph."
    print(f"--- User Request: {user_input} ---")
    
    # 메인 그래프 실행
    events = graph.stream(
        {"messages": [HumanMessage(content=user_input)]},
        stream_mode="values"
    )
    
    for event in events:
        if "messages" in event:
            last_msg = event["messages"][-1]
            print(f"[{last_msg.type}]: {last_msg.content}")

if __name__ == "__main__":
    main()
