"""
graph.py - Deep Research 그래프 정의
=====================================

5노드 Deep Research 아키텍처 그래프:

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
    planner_node,
    searcher_node, 
    content_reader_node,
    analyzer_node,
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
    
    workflow.add_node("Planner", planner_node)
    workflow.add_node("Searcher", searcher_node)
    workflow.add_node("ContentReader", content_reader_node)
    workflow.add_node("Analyzer", analyzer_node)
    workflow.add_node("Writer", writer_node)
    
    # ========================================
    # 엣지 정의 (흐름)
    # ========================================
    
    # 시작점: Planner
    workflow.set_entry_point("Planner")
    
    # 순차 흐름
    workflow.add_edge("Planner", "Searcher")
    workflow.add_edge("Searcher", "ContentReader")
    workflow.add_edge("ContentReader", "Analyzer")
    
    # 조건부 엣지: Analyzer → Writer 또는 Searcher
    workflow.add_conditional_edges(
        "Analyzer",
        should_continue_research,
        {
            "continue": "Searcher",   # 추가 검색 필요
            "finish": "Writer"        # 작성 시작
        }
    )
    
    # Writer → 종료
    workflow.add_edge("Writer", END)
    
    return workflow


# 그래프 컴파일
graph = build_graph().compile()
