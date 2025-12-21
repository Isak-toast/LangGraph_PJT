"""
graph.py - Deep Research 그래프 정의 (Phase 10: 병렬 연구)
=====================================

Phase 10 아키텍처: Parallel Research (병렬 연구)

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
  │ Supervisor │ ← [Phase 9] 쿼리 복잡도 분석, 병렬 수 결정
  └──────┬─────┘
         │
         ▼
  ┌──────────────────────────────────────────────┐
  │      PARALLEL RESEARCHER [Phase 10]           │
  │  Query1 ─┐                                    │
  │  Query2 ─┼─→ 병렬 검색+읽기 → 결과 병합       │
  │  Query3 ─┘                                    │
  └──────────────────────────────────────────────┘
         │
         ▼
  ┌──────────┐
  │ Compress │ ← 병렬 결과 압축 (깊이 생성!)
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
    parallel_researcher_node,  # Phase 10: 병렬 연구
    compress_node,
    writer_node,
    critique_node,     # Phase 5
)


# ================================================================
# 메인 그래프 빌드 (Phase 10: 병렬 연구)
# ================================================================

def build_graph():
    """Deep Research 그래프 빌드 (Phase 10: 병렬 연구)"""
    
    workflow = StateGraph(DeepResearchState)
    
    # ========================================
    # 노드 추가
    # ========================================
    
    workflow.add_node("Clarify", clarify_node)       # Phase 3
    workflow.add_node("Planner", planner_node)
    workflow.add_node("Supervisor", supervisor_node) # Phase 9: 동적 전략 결정
    workflow.add_node("ParallelResearch", parallel_researcher_node)  # Phase 10
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
    
    # Planner → Supervisor
    workflow.add_edge("Planner", "Supervisor")
    
    # Supervisor → ParallelResearch (Phase 10)
    workflow.add_edge("Supervisor", "ParallelResearch")
    
    # ParallelResearch → Compress (병렬 결과 압축으로 깊이 생성)
    workflow.add_edge("ParallelResearch", "Compress")
    
    # Compress → Writer
    workflow.add_edge("Compress", "Writer")
    
    # Writer → Critique
    workflow.add_edge("Writer", "Critique")
    
    # Critique → 종료
    workflow.add_edge("Critique", END)
    
    return workflow


# 그래프 컴파일
graph = build_graph().compile()
