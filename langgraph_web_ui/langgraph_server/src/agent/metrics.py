"""
metrics.py - Deep Research 성능 측정
=====================================

각 Phase별 성능을 측정하고 비교하기 위한 도구
"""

import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, List
import json
import os


@dataclass
class ResearchMetrics:
    """연구 성능 지표"""
    
    # 기본 정보
    phase: str                      # "Phase 0", "Phase 1", ...
    query: str                      # 테스트 질문
    timestamp: str                  # 측정 시간
    
    # 시간 지표
    total_time_sec: float           # 총 소요 시간
    
    # 호출 지표
    llm_calls: int                  # LLM 호출 횟수
    search_calls: int               # 검색 API 호출 횟수
    urls_read: int                  # 읽은 URL 수
    research_iterations: int        # 반복 검색 횟수
    
    # 토큰 지표
    estimated_tokens: int           # 추정 토큰 사용량
    
    # 품질 지표 (수동 평가)
    response_quality: Optional[int] = None  # 1-5점
    has_citations: bool = False             # 인용 포함 여부
    response_length: int = 0                # 응답 길이 (문자)


def estimate_tokens(text: str) -> int:
    """간단한 토큰 추정 (한글 2자 = 1토큰, 영어 4자 = 1토큰)"""
    korean_chars = sum(1 for c in text if '가' <= c <= '힣')
    other_chars = len(text) - korean_chars
    return (korean_chars // 2) + (other_chars // 4)


def has_citations(text: str) -> bool:
    """인용 포함 여부 확인"""
    import re
    # [1], [2] 또는 [출처] 패턴 검색
    return bool(re.search(r'\[\d+\]|\[출처\]|### (Sources|출처)', text))


class ResearchBenchmark:
    """연구 벤치마크 실행 및 기록"""
    
    RESULTS_DIR = "benchmark_results"
    
    def __init__(self, phase: str, verbose: bool = False):
        self.phase = phase
        self.verbose = verbose
        self.results: List[ResearchMetrics] = []
        
        # 결과 디렉토리 생성
        os.makedirs(self.RESULTS_DIR, exist_ok=True)
    
    def run_single(self, graph, query: str) -> ResearchMetrics:
        """단일 쿼리 벤치마크 실행"""
        from langchain_core.messages import HumanMessage
        
        print(f"\n📊 Running benchmark: {query[:50]}...")
        
        start = time.time()
        
        # 그래프 실행
        result = graph.invoke({
            "messages": [HumanMessage(content=query)]
        })
        
        elapsed = time.time() - start
        
        # 결과 분석
        messages = result.get("messages", [])
        final_response = messages[-1].content if messages else ""
        
        metrics = ResearchMetrics(
            phase=self.phase,
            query=query,
            timestamp=datetime.now().isoformat(),
            total_time_sec=round(elapsed, 2),
            llm_calls=self._count_ai_messages(messages),
            search_calls=result.get("current_query_index", 0),
            urls_read=len(result.get("read_contents", [])),
            research_iterations=result.get("research_iteration", 0),
            estimated_tokens=estimate_tokens(str(messages)),
            response_quality=None,  # 수동 평가 필요
            has_citations=has_citations(final_response),
            response_length=len(final_response)
        )
        
        self.results.append(metrics)
        self._print_metrics(metrics, final_response)
        
        return metrics
    
    def _count_ai_messages(self, messages) -> int:
        """AI 메시지 수 카운트"""
        count = 0
        for msg in messages:
            if hasattr(msg, 'name') or (hasattr(msg, 'type') and msg.type == 'ai'):
                count += 1
        return count
    
    def _print_metrics(self, m: ResearchMetrics, response: str = ""):
        """지표 출력"""
        
        print(f"""
┌════════════════════════════════════════════════════════════════
│ {m.phase} Benchmark Result
├────────────────────────────────────────────────────────────────
│ Query: {m.query[:60]}...
│ Time: {m.total_time_sec}s
│ LLM Calls: {m.llm_calls}
│ Search Calls: {m.search_calls}
│ URLs Read: {m.urls_read}
│ Iterations: {m.research_iterations}
│ Est. Tokens: {m.estimated_tokens}
│ Response Length: {m.response_length} chars
│ Has Citations: {'✅' if m.has_citations else '❌'}
└────────────────────────────────────────────────────────────────
""")
        
        # 응답 내용 출력
        if self.verbose:
            # Verbose 모드: 전체 응답 출력
            print("\n" + "="*70)
            print("📄 FULL RESPONSE:")
            print("="*70)
            print(response)
            print("="*70 + "\n")
        else:
            # 기본 모드: 500자 미리보기 (줄바꿈 유지)
            if response:
                preview = response[:500]
                if len(response) > 500:
                    preview += "\n... (truncated)\n"
                print("\n📝 Response Preview (500 chars):")
                print("-"*50)
                print(preview)
                print("-"*50 + "\n")
    
    def run_all(self, graph, queries: List[str]) -> List[ResearchMetrics]:
        """모든 쿼리 벤치마크 실행"""
        for query in queries:
            self.run_single(graph, query)
        return self.results
    
    def save_results(self):
        """결과 저장"""
        filename = f"{self.RESULTS_DIR}/{self.phase.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = [asdict(r) for r in self.results]
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"📁 Results saved to: {filename}")
        return filename
    
    def print_summary(self):
        """요약 출력"""
        if not self.results:
            print("No results yet")
            return
        
        avg_time = sum(r.total_time_sec for r in self.results) / len(self.results)
        avg_tokens = sum(r.estimated_tokens for r in self.results) / len(self.results)
        citations_rate = sum(1 for r in self.results if r.has_citations) / len(self.results) * 100
        
        print(f"""
╔═══════════════════════════════════════════
║  {self.phase} Summary ({len(self.results)} tests)
╠═══════════════════════════════════════════
║  Average Time: {avg_time:.2f}s
║  Average Tokens: {avg_tokens:.0f}
║  Citation Rate: {citations_rate:.0f}%
╚═══════════════════════════════════════════
""")


# 테스트 질문 세트
TEST_QUERIES = [
    "LangGraph와 CrewAI의 멀티 에이전트 아키텍처를 비교하고 장단점을 분석해줘",
    "2024년 발표된 LLM 기반 에이전트 시스템 관련 논문들을 분석하고 주요 트렌드를 설명해줘",
    "RAG(Retrieval-Augmented Generation)와 Agent 기반 접근법의 차이점과 각각 언제 사용하면 좋은지 설명해줘"
]


def run_phase_benchmark(graph, phase: str = "Phase 0", verbose: bool = False):
    """Phase 벤치마크 실행
    
    Args:
        graph: LangGraph 그래프 인스턴스
        phase: Phase 이름 (예: "Phase 0", "Phase 1")
        verbose: True면 전체 응답 출력, False면 500자 미리보기
    """
    benchmark = ResearchBenchmark(phase, verbose=verbose)
    benchmark.run_all(graph, TEST_QUERIES)
    benchmark.print_summary()
    benchmark.save_results()
    return benchmark.results
