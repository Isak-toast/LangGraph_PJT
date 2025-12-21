# Phase 10 병렬 연구 벤치마크 보고서

> 측정일: 2025-12-21
> 변경: 순차 연구 → 병렬 연구 (ThreadPoolExecutor)

---

## 1. 요약

| 지표 | Phase 9 | Phase 10 | 변화 |
|------|---------|----------|------|
| **평균 시간** | 30.05s | **24.38s** | **-18.9%** ✅ |
| **평균 토큰** | 1,216 | 1,260 | +3.6% |
| **CARC 품질** | 16.1/20 | **16.2/20** | 유지 ✅ |
| **인용률** | 100% | 100% | 유지 ✅ |

---

## 2. Phase 0 → Phase 10 전체 진행

| Phase | 시간 | 변화 | 핵심 개선 |
|-------|------|------|----------|
| Phase 0 | 32.54s | 기준 | Baseline |
| Phase 8 | 28.39s | -12.8% | 서브그래프 |
| Phase 9 | 30.05s | -7.7% | Supervisor |
| **Phase 10** | **24.38s** | **-25.1%** | **병렬 연구** ✅ |

---

## 3. Phase 10 구현 내용

### 3.1 아키텍처 변경

**Before (Phase 9 - 순차 반복):**
```
Supervisor → [Research Subgraph] → Compress
                    │
            Searcher → ContentReader → Analyzer
                 ↑              │
                 └──────────────┘ (loop 2-3x)
```

**After (Phase 10 - 병렬 실행):**
```
Supervisor → [ParallelResearcher] → Compress
                    │
         ┌──────────┼──────────┐
         ▼          ▼          ▼
      Query1     Query2     Query3   ← 병렬 실행!
         │          │          │
         └──────────┼──────────┘
                    │
              [결과 병합]
```

### 3.2 핵심 코드

```python
def parallel_researcher_node(state: DeepResearchState) -> dict:
    """병렬 연구 노드 (Phase 10)"""
    
    MAX_PARALLEL = min(len(queries), supervisor_iterations + 1)
    queries_to_run = queries[:MAX_PARALLEL]
    
    # ThreadPoolExecutor로 병렬 실행
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_PARALLEL) as executor:
        futures = {
            executor.submit(parallel_single_query_research, query, idx): (query, idx)
            for idx, query in enumerate(queries_to_run)
        }
        # 결과 수집...
    
    return {
        "parallel_findings": all_findings,
        "parallel_contents": all_contents,
        "findings": all_findings,
        "read_contents": all_contents,
    }
```

---

## 4. 병렬 실행 결과

### 개별 테스트

| 테스트 | 순수 시간 | 연구 시간 | Speedup |
|--------|----------|----------|---------|
| 비교형 | 24.08s | 3.11s | **2.7x** |
| 학술형 | 24.55s | 5.06s | 2.0x |
| 기술형 | 24.50s | 4.77s | 2.0x |

### 병렬 연구 로그

```
🚀 ParallelResearcher [Phase 10]: Executing 3 queries in parallel
   └─ [1] LangGraph vs CrewAI comparison
   └─ [2] LangGraph multi-agent architecture
   └─ [3] CrewAI multi-agent framework
   ✓ Query 1 completed in 2.8s
   ✓ Query 2 completed in 3.1s
   ✓ Query 3 completed in 2.4s

   ⏱️ Parallel research completed: 3/3 in 3.11s
   └─ Speedup: 2.7x (sequential would take 8.3s)
```

---

## 5. 순차 vs 병렬 비교

| 방식 | 연구 시간 | 총 시간 | 장점 |
|------|----------|---------|------|
| **순차 (Phase 9)** | ~15s (5s × 3) | 30.05s | 맥락 유지, 깊이 |
| **병렬 (Phase 10)** | **~4s** (동시) | **24.38s** | **속도**, 넓은 범위 |

### 깊이 생성 방식

| 방식 | 깊이 생성 방법 |
|------|--------------|
| 순차 | Search → Analyze → Search → Analyze (반복) |
| **병렬** | 3개 병렬 검색 → **Compress에서 압축으로 깊이 생성** |

---

## 6. 품질 분석

### CARC 점수 비교

| 차원 | Phase 9 | Phase 10 | 변화 |
|------|---------|----------|------|
| Completeness | 4.0 | 4.0 | 유지 |
| Accuracy | 3.8 | 3.7 | -0.1 |
| Relevance | 4.2 | 4.5 | +0.3 |
| Clarity | 4.0 | 4.0 | 유지 |
| **Total** | 16.1 | **16.2** | **+0.1** ✅ |

> **품질 유지**: 병렬화로 속도 개선하면서 품질도 유지

---

## 7. 결론

| 항목 | 결과 |
|------|------|
| **병렬 연구 구현** | ✅ 완료 |
| **처리 시간** | **-25.1%** (32.54s → 24.38s) |
| **연구 단계 Speedup** | **2.0-2.7x** |
| **CARC 품질** | 16.2/20 (유지) |
| **인용률** | 100% (유지) |

> 💡 **결론**: Phase 10 병렬 연구로 **처리 시간 25% 단축**을 달성했습니다.
>
> ```
> Phase 0: 32.54s ████████████████████████████████
> Phase 10: 24.38s ████████████████████████      (-25%)
> ```
>
> Open Deep Research 스타일의 "넓게 수집 → 압축으로 깊이 생성" 패턴 구현 완료!

---

## 부록: 원시 데이터

- `benchmark_results/phase_10_parallel_20251221_131214.json`
- `benchmark_logs/phase_10_parallel_*.log`
