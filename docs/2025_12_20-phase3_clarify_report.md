# Phase 3 Clarify 벤치마크 보고서

> 측정일: 2025-12-20
> 변경: Clarify 노드 추가 (질문 분석 + 명확화 필요 판단)

---

## 1. Phase 3 변경 사항

| 항목 | 변경 내용 |
|------|----------|
| **State 확장** | `needs_clarification`, `clarification_question`, `query_analysis` 필드 |
| **Clarify 노드** | 질문 분석 + 명확화 필요 여부 판단 |
| **Graph 변경** | Entry Point: `Clarify` → `Planner` |

---

## 2. Clarify 노드 동작 확인 ✅

### 로그에서 확인된 호출

```
🔎 Clarify: Analyzing query...
   └─ Query: LangGraph와 CrewAI의 멀티 에이전트 아키텍처를 비교하고...
   └─ Status: 🟢 Clear
   └─ Analysis: The query asks for a comparison of multi-agent architectures...
   └─ Topics: LangGraph, CrewAI, Multi-agent architecture, Comparison

🔎 Clarify: Analyzing query...
   └─ Query: 2024년 발표된 LLM 기반 에이전트 시스템 관련 논문들을...
   └─ Status: 🟢 Clear
   └─ Analysis: The query is specific, providing both the timeframe and topic.

🔎 Clarify: Analyzing query...
   └─ Query: RAG와 Agent 기반 접근법의 차이점과...
   └─ Status: 🟢 Clear
   └─ Analysis: The intent is clear: explanation and comparison.
```

### 호출 통계

| 테스트 | 판정 | 분석 품질 |
|--------|------|----------|
| 비교형 | 🟢 Clear | 토픽 정확히 감지 |
| 학술형 | 🟢 Clear | 시간/범위 특정됨 |
| 기술형 | 🟢 Clear | 의도 명확 |

### 질문 명확화 분석 비교표

| 원본 질문 | Clarify 분석 결과 | 감지된 토픽 | 명확화 필요 |
|----------|------------------|------------|-----------|
| LangGraph와 CrewAI의 멀티 에이전트 아키텍처를 비교하고 장단점을 분석해줘 | 비교 요청, 구체적 대상 명시 | `LangGraph`, `CrewAI`, `Multi-agent architecture` | ❌ 불필요 |
| 2024년 발표된 LLM 기반 에이전트 시스템 관련 논문들을 분석하고 주요 트렌드를 설명해줘 | 시간/범위 특정됨, 명확한 의도 | `LLM-based agent systems`, `2024 publications`, `research trends` | ❌ 불필요 |
| RAG와 Agent 기반 접근법의 차이점과 언제 사용하면 좋은지 설명해줘 | 비교+설명 의도, 기술 용어 풀어서 인식 | `RAG`, `Agent-based approach`, `comparison` | ❌ 불필요 |

> **분석**: 테스트 질문들은 모두 구체적이고 명확한 의도를 가지고 있어 명확화가 불필요했음. 
> 모호한 질문(예: "AI 좀 알려줘", "LLM 뭐야?") 입력 시 명확화 질문이 생성될 것으로 예상.

---

## 3. 성능 비교

### Phase 2 → Phase 3 비교

| 지표 | Phase 2 | Phase 3 | 변화 |
|------|---------|---------|------|
| **평균 시간** | 30.44s | 36.97s | +21.5% ⚠️ |
| **평균 토큰** | 1,099 | 1,272 | +15.7% |
| **인용률** | 100% | 100% | 유지 ✅ |
| **평균 응답** | 2,783자 | 3,350자 | +20.4% |

> ⚠️ 시간 증가는 Clarify 노드의 LLM 호출 오버헤드 (약 1-2초) + 모델 변동

### Phase 0 → Phase 3 누적 비교

| 지표 | Phase 0 | Phase 3 | 누적 변화 |
|------|---------|---------|----------|
| **시간** | 32.54s | 36.97s | +13.6% |
| **토큰** | 1,369 | 1,272 | **-7.1%** ⬇️ |
| **인용** | 0% | 100% | **+100%** 🎉 |

---

## 4. Clarify 노드 분석

### 프롬프트 설계

```xml
<Task>
Analyze the user query for:
1. Ambiguous terms or acronyms (multiple meanings)
2. Missing context (time period, scope)
3. Unclear intent (comparison vs explanation)
</Task>

<Decision Criteria>
NEEDS_CLARIFICATION when:
- Contains acronyms without context
- Timeframe unclear for trending topics
- Very broad topics without focus

CLEAR when:
- Query is specific and well-defined
- Context is sufficient for research
</Decision Criteria>
```

### 출력 예시

```json
{
  "needs_clarification": false,
  "clarification_question": null,
  "analysis": "The query is specific, providing timeframe and topic.",
  "detected_topics": ["LLM-based agent systems", "2024 publications"]
}
```

---

## 5. 개별 테스트 결과

| 테스트 | 시간 | 검색 | URL | 반복 | 토큰 | 응답 | 인용 |
|--------|------|------|-----|------|------|------|------|
| 비교형 | 24.87s | 2 | 6 | 2 | 1,095 | 2,646자 | ✅ |
| 학술형 | 37.24s | 3 | 9 | 3 | 1,141 | 2,895자 | ✅ |
| 기술형 | 48.80s | 3 | 9 | 3 | 1,581 | 4,506자 | ✅ |

---

## 6. 다음 단계 (Phase 4)

| 항목 | 내용 |
|------|------|
| **목표** | 프롬프트 XML 구조화 |
| **기대 효과** | 형식 일관성 +40%, 불필요 출력 -50% |

---

## 부록: 원시 데이터

- `benchmark_results/phase_3_20251220_223228.json`
- `benchmark_logs/phase_3_verbose_20251220_223036.log`
