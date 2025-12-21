# Phase 8 서브그래프 분리 벤치마크 보고서

> 측정일: 2025-12-21
> 변경: Research Subgraph 분리 (Searcher → ContentReader → Analyzer 캡슐화)

---

## 1. 요약

| 지표 | Phase 7 | Phase 8 | 변화 |
|------|---------|---------|------|
| **평균 시간** | 29.69s | **28.39s** | **-4.4%** ✅ |
| **평균 토큰** | 1,168 | **1,205** | +3.2% |
| **CARC 품질** | 16.1/20 | **16.0/20** | 유지 ✅ |
| **인용률** | 100% | 100% | 유지 ✅ |

---

## 2. Phase 8 구현 내용

### 2.1 아키텍처 변경

**Before (Phase 7 - 선형):**
```
Clarify → Planner → Searcher → ContentReader → Analyzer → Compress → Writer → Critique
                        ↑              │
                        └──────────────┘ (loop)
```

**After (Phase 8 - 서브그래프):**
```
Clarify → Planner → [Research Subgraph] → Compress → Writer → Critique
                          │
                    ┌─────┴─────┐
                    │ Searcher  │
                    │     ↓     │
                    │ContentReader│
                    │     ↓     │
                    │ Analyzer  │
                    │     ↓↑    │ ← (loop inside)
                    └───────────┘
```

### 2.2 핵심 코드 변경

**서브그래프 정의:**
```python
def build_research_subgraph():
    research_workflow = StateGraph(DeepResearchState)
    
    research_workflow.add_node("Searcher", searcher_node)
    research_workflow.add_node("ContentReader", content_reader_node)
    research_workflow.add_node("Analyzer", analyzer_node)
    
    research_workflow.set_entry_point("Searcher")
    research_workflow.add_edge("Searcher", "ContentReader")
    research_workflow.add_edge("ContentReader", "Analyzer")
    research_workflow.add_conditional_edges(
        "Analyzer", should_continue_research,
        {"continue": "Searcher", "finish": END}
    )
    
    return research_workflow.compile()
```

**메인 그래프에서 호출:**
```python
workflow.add_node("Research", research_subgraph_node)
workflow.add_edge("Planner", "Research")
workflow.add_edge("Research", "Compress")
```

### 2.3 새로운 추적 지표

| 지표 | 설명 |
|------|------|
| `subgraph_executions` | 서브그래프 실행 횟수 |
| `Findings` | 발견된 사실 수 |
| `Contents` | 읽은 URL 수 |

---

## 3. 벤치마크 결과 상세

### 개별 테스트

| 테스트 | 시간 | 토큰 | 반복 | Findings | CARC |
|--------|------|------|------|----------|------|
| 비교형 | **24.44s** | 1,011 | 2 | 16 | 16.5/20 |
| 학술형 | 35.37s | 1,352 | 3 | 19 | 15.0/20 |
| 기술형 | 25.37s | 1,251 | 2 | 12 | 16.5/20 |

### 서브그래프 실행 로그

```
🔬 Research Subgraph: Starting research loop...
   └─ ✅ Research Subgraph completed (execution #1)
   └─ Findings: 16 items
   └─ Contents: 6 URLs read
```

---

## 4. Phase 0 → Phase 8 전체 진행

| Phase | 시간 | 변화 | 핵심 개선 |
|-------|------|------|----------|
| Phase 0 | 32.54s | 기준 | Baseline |
| Phase 4 | 29.62s | -9.0% | XML 프롬프트 |
| Phase 7 | 29.69s | -8.8% | URL 병렬, UA 개선 |
| **Phase 8** | **28.39s** | **-12.8%** | **서브그래프 분리** ✅ |

---

## 5. 서브그래프 분리의 효과

### 5.1 달성된 목표

| 목표 | 상태 | 설명 |
|------|------|------|
| **모듈성** | ✅ 달성 | 연구 로직 캡슐화 |
| **재사용성** | ✅ 달성 | 서브그래프 독립 테스트 가능 |
| **확장 기반** | ✅ 달성 | 병렬 실행 준비 완료 |
| **성능 유지** | ✅ 달성 | 오히려 4.4% 개선 |

### 5.2 왜 시간이 줄었는가?

1. **그래프 구조 단순화**: 메인 그래프 노드 수 8 → 6
2. **서브그래프 최적화**: 내부 루프가 더 효율적으로 실행
3. **State 업데이트 감소**: 서브그래프 완료 후 한 번에 업데이트

---

## 6. Phase 9-10 준비 현황

Phase 8 서브그래프 분리로 다음 단계 준비 완료:

```
Phase 9: Supervisor 패턴
    ┌──────────────────────────────────────┐
    │          SUPERVISOR NODE             │
    │  - 쿼리 복잡도 분석                   │
    │  - 연구 수 동적 결정 (1-5개)          │
    └──────────────────────────────────────┘
                    │
                    ▼
         [Research Subgraph] ← Phase 8에서 완성!
         
Phase 10: 병렬 연구 (Send API)
    Supervisor → Send("Research", query1) ─┐
              → Send("Research", query2) ─┼→ 병렬 실행
              → Send("Research", query3) ─┘
```

---

## 7. 결론

| 항목 | 결과 |
|------|------|
| **서브그래프 분리** | ✅ 완료 |
| **처리 시간** | **-4.4%** (28.39s) |
| **전체 개선율** | **-12.8%** (Phase 0 대비) |
| **CARC 품질** | 16.0/20 유지 |
| **병렬 연구 기반** | ✅ 준비 완료 |

> 💡 **결론**: Phase 8 서브그래프 분리로 코드 모듈화와 성능 개선을 동시에 달성했습니다.
> 이제 Phase 9 (Supervisor) 및 Phase 10 (병렬 실행)을 위한 기반이 마련되었습니다.

---

## 부록: 원시 데이터

- `benchmark_results/phase_8_subgraph_20251221_014312.json`
- `benchmark_logs/phase_8_subgraph_*.log`
