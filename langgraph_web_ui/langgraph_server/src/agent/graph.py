"""
graph.py - Deep Research 그래프 정의 (Phase 9: Supervisor 패턴)
=====================================

Phase 9 아키텍처: Supervisor + Research Subgraph

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
  ┌────────────┐
  │ Supervisor │ ← [Phase 9] 쿼리 복잡도 분석, 동적 전략 결정
  └──────┬─────┘
         │
         ▼
  ┌──────────────────────────────────────────┐
  │         RESEARCH SUBGRAPH (Phase 8)      │
  │  Searcher → ContentReader → Analyzer     │
  │       ↑              │                   │
  │       └──────────────┘ (loop)            │
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
    supervisor_node,   # Phase 9: 동적 전략 결정
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
    """
    
    research_workflow = StateGraph(DeepResearchState)
    
    research_workflow.add_node("Searcher", searcher_node)
    research_workflow.add_node("ContentReader", content_reader_node)
    research_workflow.add_node("Analyzer", analyzer_node)
    
    research_workflow.set_entry_point("Searcher")
    
    research_workflow.add_edge("Searcher", "ContentReader")
    research_workflow.add_edge("ContentReader", "Analyzer")
    
    research_workflow.add_conditional_edges(
        "Analyzer",
        should_continue_research,
        {
            "continue": "Searcher",
            "finish": END
        }
    )
    
    return research_workflow.compile()


research_subgraph = build_research_subgraph()


# ================================================================
# Research Subgraph 래퍼 노드
# ================================================================

def research_subgraph_node(state: DeepResearchState) -> dict:
    """
    Research Subgraph를 실행하는 래퍼 노드 (Phase 8)
    """
    # Supervisor가 결정한 설정 확인
    complexity = state.get("supervisor_complexity", "MEDIUM")
    max_iter = state.get("max_research_iterations", 3)
    strategy = state.get("supervisor_strategy", "targeted")
    
    print(f"\n🔬 Research Subgraph: Starting research loop...")
    print(f"   └─ Supervisor config: {complexity}, max {max_iter} iterations, {strategy} strategy")
    
    # 서브그래프 실행
    result = research_subgraph.invoke(state)
    
    # 실행 횟수 추적
    executions = state.get("subgraph_executions", 0) + 1
    
    print(f"   └─ ✅ Research Subgraph completed (execution #{executions})")
    print(f"   └─ Findings: {len(result.get('findings', []))} items")
    print(f"   └─ Contents: {len(result.get('read_contents', []))} URLs read")
    
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


# ================================================================
# 메인 그래프 빌드 (Phase 9: Supervisor 추가)
# ================================================================

def build_graph():
    """Deep Research 그래프 빌드 (Phase 9: Supervisor 패턴)"""
    
    workflow = StateGraph(DeepResearchState)
    
    # ========================================
    # 노드 추가
    # ========================================
    
    workflow.add_node("Clarify", clarify_node)       # Phase 3
    workflow.add_node("Planner", planner_node)
    workflow.add_node("Supervisor", supervisor_node) # Phase 9: 동적 전략 결정
    workflow.add_node("Research", research_subgraph_node)  # Phase 8: 서브그래프
    workflow.add_node("Compress", compress_node)
    workflow.add_node("Writer", writer_node)
    workflow.add_node("Critique", critique_node)     # Phase 5
    
    # ========================================
    # 엣지 정의 (흐름)
    # ========================================
    
    # 시작점: Clarify
    workflow.set_entry_point("Clarify")
    
    # Clarify → Planner
    workflow.add_edge("Clarify", "Planner")
    
    # Planner → Supervisor (Phase 9)
    workflow.add_edge("Planner", "Supervisor")
    
    # Supervisor → Research Subgraph
    workflow.add_edge("Supervisor", "Research")
    
    # Research → Compress
    workflow.add_edge("Research", "Compress")
    
    # Compress → Writer
    workflow.add_edge("Compress", "Writer")
    
    # Writer → Critique
    workflow.add_edge("Writer", "Critique")
    
    # Critique → 종료
    workflow.add_edge("Critique", END)
    
    return workflow


# 그래프 컴파일
graph = build_graph().compile()
