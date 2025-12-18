"""
graph.py - LangGraph 그래프 정의
==================================

이 파일은 노드들을 연결하여 실행 가능한 그래프를 만듭니다.
그래프는 노드(Node)와 엣지(Edge)로 구성됩니다.

그래프 구조:
┌─────────────────────────────────────────────────┐
│                                                 │
│   START                                         │
│     │                                           │
│     ▼                                           │
│ ┌───────────┐                                   │
│ │ Supervisor│◄────────────┬────────────┐        │
│ └─────┬─────┘             │            │        │
│       │                   │            │        │
│   조건부 분기              │            │        │
│   ┌───┴───┐              │            │        │
│   ▼       ▼              │            │        │
│ Researcher Writer        │            │        │
│   │         │            │            │        │
│   └─────────┴────────────┘            │        │
│                                       │        │
│   FINISH ────────────────────────────►END      │
│                                                 │
└─────────────────────────────────────────────────┘

핵심 개념:
- StateGraph: 상태 기반 그래프 (상태가 노드를 거치며 변형됨)
- add_node: 노드(함수) 등록
- add_edge: 무조건 연결 (A 다음에 항상 B)
- add_conditional_edges: 조건부 연결 (상태에 따라 다른 곳으로)
"""

from langgraph.graph import StateGraph, START, END
from src.agent.state import AgentState
from src.agent.nodes import research_node, writer_node, supervisor_node, members


# ================================================================
# 라우팅 함수 (조건부 엣지에서 사용)
# ================================================================

def route_supervisor(state: AgentState) -> str:
    """
    Supervisor의 결정에 따라 다음 노드를 반환
    
    이 함수는 add_conditional_edges에서 사용됩니다.
    state["next"] 값을 읽어서 해당 노드로 라우팅합니다.
    
    Args:
        state: 현재 그래프 상태
    
    Returns:
        다음 노드 이름 ("Researcher", "Writer", "FINISH")
    
    예시:
        state["next"] = "Researcher" → 반환: "Researcher"
        state["next"] = "FINISH"     → 반환: "FINISH"
    """
    next_node = state["next"]
    
    if next_node == "FINISH":
        return "FINISH"  # 이 값은 아래 매핑에서 END로 변환됨
    
    return next_node


# ================================================================
# 그래프 생성
# ================================================================

# StateGraph 인스턴스 생성
# AgentState를 타입으로 지정하여 상태 구조를 정의
workflow = StateGraph(AgentState)


# ================================================================
# 노드 추가 (add_node)
# ================================================================
# 
# workflow.add_node("노드이름", 노드함수)
# 
# 노드 이름은 라우팅에 사용되므로 중요함!
# 예: state["next"] = "Researcher" → Researcher 노드 실행

workflow.add_node("Supervisor", supervisor_node)   # 라우터 노드
workflow.add_node("Researcher", research_node)     # 검색 노드
workflow.add_node("Writer", writer_node)           # 글쓰기 노드


# ================================================================
# 엣지 추가 - 기본 연결 (add_edge)
# ================================================================
# 
# workflow.add_edge(A, B): A 노드 실행 후 항상 B 노드로 이동
# 
# START: 그래프 시작점 (첫 번째로 실행할 노드 지정)
# END: 그래프 종료점 (여기로 가면 실행 완료)

# 시작점 → Supervisor (모든 요청은 Supervisor가 먼저 봄)
workflow.add_edge(START, "Supervisor")

# Worker → Supervisor (Worker 실행 후 다시 Supervisor로)
# 이렇게 해야 Supervisor가 "다 됐는지" 확인하고 FINISH 결정 가능
for member in members:
    workflow.add_edge(member, "Supervisor")


# ================================================================
# 조건부 엣지 추가 (add_conditional_edges)
# ================================================================
# 
# add_conditional_edges(
#     source_node,      # 출발 노드
#     routing_function, # 라우팅 결정 함수
#     path_map          # 반환값 → 목적지 노드 매핑
# )
#
# 작동 방식:
# 1. Supervisor 실행 완료
# 2. route_supervisor(state) 호출 → "Researcher" 반환
# 3. path_map에서 "Researcher" → "Researcher" 노드로 이동

workflow.add_conditional_edges(
    "Supervisor",           # 출발 노드
    route_supervisor,       # 라우팅 함수: state["next"] 반환
    {
        # 반환값: 목적지 노드
        "Researcher": "Researcher",  # "Researcher" → Researcher 노드
        "Writer": "Writer",          # "Writer" → Writer 노드
        "FINISH": END,               # "FINISH" → 그래프 종료
    }
)


# ================================================================
# 그래프 컴파일 (compile)
# ================================================================
# 
# 정의된 노드와 엣지를 실행 가능한 형태로 변환
# 컴파일 후 graph.invoke(), graph.stream() 등으로 실행 가능
#
# checkpointer 옵션:
#   - 상태를 저장하여 중단/재개 가능하게 함
#   - 예: MemorySaver(), SqliteSaver() 등

graph = workflow.compile()


# ================================================================
# 사용 예시 (직접 실행 시)
# ================================================================
# 
# from langchain_core.messages import HumanMessage
# 
# result = graph.invoke({
#     "messages": [HumanMessage(content="AI 트렌드 알려줘")]
# })
# 
# 실행 흐름:
# 1. START → Supervisor
# 2. Supervisor: "Researcher 호출!" → {"next": "Researcher"}
# 3. Supervisor → Researcher
# 4. Researcher: Tavily 검색 후 결과 반환
# 5. Researcher → Supervisor
# 6. Supervisor: "완료!" → {"next": "FINISH"}
# 7. Supervisor → END
# 8. 결과 반환
