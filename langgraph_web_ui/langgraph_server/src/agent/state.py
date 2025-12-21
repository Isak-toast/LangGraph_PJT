"""
state.py - Deep Research 상태 정의
=====================================

이 파일은 Deep Research 아키텍처를 위한 확장된 상태를 정의합니다.

노드 구조:
  Planner → Searcher → ContentReader → Analyzer → Writer
                 ↑                          │
                 └──────────────────────────┘
                      (추가 검색 필요시)
"""

from typing import Annotated, Sequence, Optional, List
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import operator  # Phase 10: 병렬 연구 결과 병합용


class ResearchPlan(TypedDict):
    """리서치 계획"""
    search_queries: List[str]     # 검색할 쿼리 목록
    depth_level: int              # 리서치 깊이 (1-3)
    focus_areas: List[str]        # 집중할 영역


class ReadContent(TypedDict):
    """읽은 URL 내용"""
    url: str
    content: str
    title: Optional[str]


class DeepResearchState(TypedDict):
    """
    Deep Research 시스템 상태
    
    이 상태는 5개 노드(Planner, Searcher, ContentReader, Analyzer, Writer)가
    공유하며, 깊이 있는 리서치를 수행하기 위한 모든 정보를 담습니다.
    """
    
    # ========================================
    # 기본 필드 (기존)
    # ========================================
    
    # 메시지 히스토리
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # 다음 노드 결정
    next: str
    
    # ========================================
    # Research Planning (Planner)
    # ========================================
    
    # 리서치 계획 (Planner가 생성)
    research_plan: Optional[ResearchPlan]
    
    # 현재 처리 중인 검색 쿼리 인덱스
    current_query_index: int
    
    # ========================================
    # Search Results (Searcher)
    # ========================================
    
    # 검색 결과 목록
    search_results: List[dict]
    
    # 읽어야 할 URL 목록
    urls_to_read: List[str]
    
    # ========================================
    # Content Reading (ContentReader)
    # ========================================
    
    # 읽은 URL 내용들
    read_contents: List[ReadContent]
    
    # ========================================
    # Analysis (Analyzer)
    # ========================================
    
    # 발견된 주요 사실들
    findings: List[str]
    
    # 추가 검색 필요 여부
    needs_more_research: bool
    
    # 추가 검색 쿼리 (필요시)
    next_search_query: Optional[str]
    
    # 리서치 반복 횟수 (최대 3회)
    research_iteration: int
    
    # ========================================
    # Compression (Compress) - Phase 1
    # ========================================
    
    # 압축된 연구 노트 (중복 제거, 정리된 findings)
    compressed_notes: Optional[str]

    # ========================================
    # Clarification (Clarify) - Phase 3
    # ========================================
    
    # 명확화 필요 여부
    needs_clarification: bool
    
    # 명확화 질문 (사용자에게 물어볼 질문)
    clarification_question: Optional[str]
    
    # 원본 질문의 분석 결과
    query_analysis: Optional[str]

    # ========================================
    # Self-Critique (Critique) - Phase 5 + CARC Framework
    # ========================================
    
    # CARC 다차원 품질 평가 (각 1.0-5.0점, 소수점 1자리)
    quality_completeness: Optional[float]   # 완전성: 질문의 모든 부분에 답변했는가?
    quality_accuracy: Optional[float]       # 정확성: 인용된 정보가 정확한가?
    quality_relevance: Optional[float]      # 관련성: 응답이 질문과 직접 관련있는가?
    quality_clarity: Optional[float]        # 명확성: 구조가 잘 정리되었는가?
    quality_total: Optional[float]          # 총점 (4.0-20.0)
    
    # 비평 피드백
    critique_feedback: Optional[str]
    
    # 개선 필요 여부 (총점 < 14일 때)
    needs_improvement: bool
    
    # 개선된 응답 (필요시)
    improved_response: Optional[str]

    # ========================================
    # Supervisor (Phase 9)
    # ========================================
    
    # 쿼리 복잡도 (SIMPLE, MEDIUM, COMPLEX)
    supervisor_complexity: Optional[str]
    
    # 권장 반복 횟수 (1-3)
    supervisor_iterations: Optional[int]
    
    # 쿼리당 읽을 URL 수 (2-5)
    supervisor_urls_per_query: Optional[int]
    
    # 연구 전략 (broad, targeted, deep)
    supervisor_strategy: Optional[str]
    
    # 동적 최대 반복 횟수
    max_research_iterations: Optional[int]

    # ========================================
    # Phase 10: Parallel Research (병렬 연구)
    # ========================================
    
    # 병렬 연구 결과들 (각 쿼리별 결과를 리스트로 축적)
    parallel_findings: Annotated[List[str], operator.add]
    
    # 병렬로 읽은 URL 내용들
    parallel_contents: Annotated[List[dict], operator.add]
    
    # 병렬 연구 실행 수
    parallel_research_count: Optional[int]
    
    # 병렬 연구 완료 수
    parallel_research_completed: Optional[int]


# 초기 상태 생성 헬퍼
def create_initial_state() -> dict:
    """새 대화 시작 시 초기 상태 생성"""
    return {
        "messages": [],
        "next": "",
        "research_plan": None,
        "current_query_index": 0,
        "search_results": [],
        "urls_to_read": [],
        "read_contents": [],
        "findings": [],
        "needs_more_research": False,
        "next_search_query": None,
        "research_iteration": 0,
        # Phase 8: 서브그래프 실행 추적
        "subgraph_executions": 0,
    }


# ========================================
# Phase 8: Research Subgraph State
# ========================================

class ResearchSubgraphState(TypedDict):
    """
    Research Subgraph 전용 상태 (Phase 8)
    
    이 상태는 Searcher → ContentReader → Analyzer 루프 내에서만 사용됩니다.
    메인 그래프와 독립적으로 연구를 수행하고 결과를 반환합니다.
    """
    
    # 입력: 검색할 쿼리
    query: str
    
    # 연구 반복 횟수 (서브그래프 내)
    iteration: int
    
    # 최대 반복 횟수
    max_iterations: int
    
    # 검색 결과
    search_results: List[dict]
    
    # 읽어야 할 URL 목록
    urls_to_read: List[str]
    
    # 읽은 URL 내용들
    read_contents: List[ReadContent]
    
    # 발견된 주요 사실들
    findings: List[str]
    
    # 추가 검색 필요 여부
    needs_more_research: bool
    
    # 추가 검색 쿼리
    next_search_query: Optional[str]
    
    # 연구 완료 여부
    research_complete: bool

