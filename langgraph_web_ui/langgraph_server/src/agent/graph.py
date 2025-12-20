"""
graph.py - Deep Research 그래프 정의 (Phase 8: 서브그래프 분리)
=====================================

Phase 8 아키텍처: Research Subgraph 분리

  ┌─────────┐
  │ Clarify │ ← 질문 분석 (Phase 3)
  └────┬────┘
       │
       ▼
  ┌─────────┐
  │ Planner │ ← 리서치 계획 수립
  └────┬────┘
       │
       ▼
  ┌──────────────────────────────────────────┐
  │         RESEARCH SUBGRAPH (Phase 8)      │
  │  ┌──────────┐                             │
  │  │ Searcher │ ← 웹 검색 (Tavily)         │
  │  └────┬─────┘                             │
  │       │                                   │
  │       ▼                                   │
  │  ┌──────────────┐                         │
  │  │ContentReader │ ← URL 내용 읽기 (병렬)  │
  │  └──────┬───────┘                         │
  │         │                                 │
  │         ▼                                 │
  │  ┌──────────┐                             │
  │  │ Analyzer │ ← 분석 + 추가 검색 결정     │
  │  └────┬─────┘                             │
  │       │  ↑                                │
  │       │  └─── (needs_more_research)       │
  │       ▼                                   │
  └──────────────────────────────────────────┘
       │
       ▼
  ┌──────────┐
  │ Compress │ ← 연구 결과 압축 + 인용
  └────┬─────┘
       │
       ▼
  ┌────────┐
  │ Writer │ ← 최종 응답 작성
  └────┬───┘
       │
       ▼
  ┌──────────┐
  │ Critique │ ← CARC 품질 평가 (Phase 5)
  └────┬─────┘
       │
       ▼
     [END]
"""

from langgraph.graph import StateGraph, END
from src.agent.state import DeepResearchState
from src.agent.nodes import (
    clarify_node,      # Phase 3
    planner_node,
    searcher_node, 
    content_reader_node,
    analyzer_node,
    compress_node,
    writer_node,
    critique_node,     # Phase 5
    should_continue_research
)


# ================================================================
# Phase 8: Research Subgraph 빌드
# ================================================================

def build_research_subgraph():
    """
    연구 서브그래프 빌드 (Phase 8)
    
    Searcher → ContentReader → Analyzer 루프를 캡슐화합니다.
    이 서브그래프는 독립적으로 테스트 가능하며, 향후 병렬 실행의 기반이 됩니다.
    """
    
    # 서브그래프는 메인 State를 공유 (DeepResearchState)
    research_workflow = StateGraph(DeepResearchState)
    
    # 노드 추가
    research_workflow.add_node("Searcher", searcher_node)
    research_workflow.add_node("ContentReader", content_reader_node)
    research_workflow.add_node("Analyzer", analyzer_node)
    
    # 시작점: Searcher
    research_workflow.set_entry_point("Searcher")
    
    # 순차 흐름
    research_workflow.add_edge("Searcher", "ContentReader")
    research_workflow.add_edge("ContentReader", "Analyzer")
    
    # 조건부 엣지: Analyzer → 루프 또는 종료
    research_workflow.add_conditional_edges(
        "Analyzer",
        should_continue_research,
        {
            "continue": "Searcher",    # 추가 검색 필요 → 루프
            "finish": END              # 서브그래프 종료
        }
    )
    
    return research_workflow.compile()


# 서브그래프 컴파일 (재사용)
research_subgraph = build_research_subgraph()


# ================================================================
# 메인 그래프 빌드 (서브그래프 사용)
# ================================================================

def research_subgraph_node(state: DeepResearchState) -> dict:
    """
    Research Subgraph를 실행하는 래퍼 노드 (Phase 8)
    
    이 노드는 research_subgraph를 실행하고 결과를 메인 상태에 반영합니다.
    """
    print("\n🔬 Research Subgraph: Starting research loop...")
    
    # 서브그래프 실행
    result = research_subgraph.invoke(state)
    
    # 서브그래프 실행 횟수 추적
    executions = state.get("subgraph_executions", 0) + 1
    
    print(f"   └─ ✅ Research Subgraph completed (execution #{executions})")
    print(f"   └─ Findings: {len(result.get('findings', []))} items")
    print(f"   └─ Contents: {len(result.get('read_contents', []))} URLs read")
    
    # 결과 반환 (서브그래프 결과 + 실행 횟수)
    return {
        "search_results": result.get("search_results", []),
        "urls_to_read": result.get("urls_to_read", []),
        "read_contents": result.get("read_contents", []),
        "findings": result.get("findings", []),
        "needs_more_research": result.get("needs_more_research", False),
        "next_search_query": result.get("next_search_query"),
        "research_iteration": result.get("research_iteration", 0),
        "subgraph_executions": executions
    }


def build_graph():
    """Deep Research 그래프 빌드 (Phase 8: 서브그래프 분리)"""
    
    # 그래프 생성
    workflow = StateGraph(DeepResearchState)
    
    # ========================================
    # 노드 추가
    # ========================================
    
    workflow.add_node("Clarify", clarify_node)   # Phase 3
    workflow.add_node("Planner", planner_node)
    workflow.add_node("Research", research_subgraph_node)  # Phase 8: 서브그래프
    workflow.add_node("Compress", compress_node)
    workflow.add_node("Writer", writer_node)
    workflow.add_node("Critique", critique_node)  # Phase 5
    
    # ========================================
    # 엣지 정의 (흐름)
    # ========================================
    
    # 시작점: Clarify (Phase 3)
    workflow.set_entry_point("Clarify")
    
    # Clarify → Planner
    workflow.add_edge("Clarify", "Planner")
    
    # Planner → Research Subgraph (Phase 8)
    workflow.add_edge("Planner", "Research")
    
    # Research → Compress (서브그래프 완료 후)
    workflow.add_edge("Research", "Compress")
    
    # Compress → Writer
    workflow.add_edge("Compress", "Writer")
    
    # Writer → Critique (Phase 5)
    workflow.add_edge("Writer", "Critique")
    
    # Critique → 종료
    workflow.add_edge("Critique", END)
    
    return workflow


# 그래프 컴파일
graph = build_graph().compile()
