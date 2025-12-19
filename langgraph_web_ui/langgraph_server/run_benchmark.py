#!/usr/bin/env python3
"""
run_benchmark.py - Phase별 벤치마크 실행
========================================

사용법:
    python run_benchmark.py --phase "Phase 0"
    python run_benchmark.py --phase "Phase 1"
    python run_benchmark.py --phase "Phase 0" --verbose  # 전체 응답 출력
"""

import argparse
import sys
import os

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agent.graph import graph
from src.agent.metrics import run_phase_benchmark, TEST_QUERIES, ResearchBenchmark


def main():
    parser = argparse.ArgumentParser(description="Run Deep Research Benchmark")
    parser.add_argument("--phase", type=str, default="Phase 0", 
                       help="Phase name (e.g., 'Phase 0', 'Phase 1')")
    parser.add_argument("--query", type=str, default=None,
                       help="Single query to test (optional)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Show full response (not just 500 char preview)")
    
    args = parser.parse_args()
    
    print(f"""
╔═══════════════════════════════════════════════════════════════
║  Deep Research Benchmark - {args.phase}
╠═══════════════════════════════════════════════════════════════
║  Test Queries: {len(TEST_QUERIES) if not args.query else 1}
║  Verbose: {"ON (full response)" if args.verbose else "OFF (500 char preview)"}
╚═══════════════════════════════════════════════════════════════
""")
    
    if args.query:
        # 단일 쿼리 테스트
        benchmark = ResearchBenchmark(args.phase, verbose=args.verbose)
        benchmark.run_single(graph, args.query)
        benchmark.print_summary()
        benchmark.save_results()
    else:
        # 전체 테스트
        run_phase_benchmark(graph, args.phase, verbose=args.verbose)


if __name__ == "__main__":
    main()
