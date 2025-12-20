"""
graph.py - Deep Research 그래프 정의
=====================================

7노드 Deep Research 아키텍처 그래프 (Phase 3: Clarify 추가):

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
  ┌──────────┐
  │ Searcher │ ← 웹 검색 (Tavily)
  └────┬─────┘
       │
       ▼
  ┌──────────────┐
  │ContentReader │ ← URL 내용 읽기
  └──────┬───────┘
         │
         ▼
  ┌──────────┐    ┌──────────┐
  │ Analyzer │───▶│ Searcher │ (추가 검색 필요시)
  └────┬─────┘    └──────────┘
       │
       ▼ (충분하면)
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
    should_continue_research
)


def build_graph():
    """Deep Research 그래프 빌드"""
    
    # 그래프 생성
    workflow = StateGraph(DeepResearchState)
    
    # ========================================
    # 노드 추가
    # ========================================
    
    workflow.add_node("Clarify", clarify_node)   # Phase 3
    workflow.add_node("Planner", planner_node)
    workflow.add_node("Searcher", searcher_node)
    workflow.add_node("ContentReader", content_reader_node)
    workflow.add_node("Analyzer", analyzer_node)
    workflow.add_node("Compress", compress_node)
    workflow.add_node("Writer", writer_node)
    
    # ========================================
    # 엣지 정의 (흐름)
    # ========================================
    
    # 시작점: Clarify (Phase 3)
    workflow.set_entry_point("Clarify")
    
    # Clarify → Planner (현재는 항상 진행, 추후 Human-in-the-Loop 추가 가능)
    workflow.add_edge("Clarify", "Planner")
    
    # 순차 흐름
    workflow.add_edge("Planner", "Searcher")
    workflow.add_edge("Searcher", "ContentReader")
    workflow.add_edge("ContentReader", "Analyzer")
    
    # 조건부 엣지: Analyzer → Compress 또는 Searcher
    workflow.add_conditional_edges(
        "Analyzer",
        should_continue_research,
        {
            "continue": "Searcher",    # 추가 검색 필요
            "finish": "Compress"       # Compress로 이동
        }
    )
    
    # Compress → Writer
    workflow.add_edge("Compress", "Writer")
    
    # Writer → 종료
    workflow.add_edge("Writer", END)
    
    return workflow


# 그래프 컴파일
graph = build_graph().compile()

