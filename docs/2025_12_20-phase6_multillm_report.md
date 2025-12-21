# Phase 6 Multi-LLM 벤치마크 보고서

> 측정일: 2025-12-20
> 변경: ResearchConfig 도입 (역할별 LLM 설정)

---

## 1. Multi-LLM이란?

**Multi-LLM**은 에이전트 역할에 따라 **최적화된 모델을 선택**하여 사용하는 기법입니다.

| 역할 | 특성 | Temperature |
|------|------|-------------|
| **Planner** | 일관된 계획 수립 필요 | 0.3 (낮음) |
| **Searcher** | 균형 잡힌 검색 | 0.5 (중간) |
| **Analyzer** | 객관적 분석 | 0.3 (낮음) |
| **Writer** | 창의적 글쓰기 | 0.7 (높음) |
| **Critic** | 객관적 비평 | 0.2 (매우 낮음) |

---

## 2. Phase 6 구현 내용

### 2.1 ResearchConfig 클래스

**신규 파일**: `src/agent/config.py`

```python
@dataclass
class ResearchConfig:
    # 역할별 모델 설정
    planner: ModelConfig   # temp=0.3
    searcher: ModelConfig  # temp=0.5
    analyzer: ModelConfig  # temp=0.3
    writer: ModelConfig    # temp=0.7
    critic: ModelConfig    # temp=0.2
    
    def get_llm(self, role: str) -> ChatGoogleGenerativeAI:
        """역할에 맞는 LLM 인스턴스 반환"""
```

### 2.2 노드별 LLM 분리

| 노드 | Before | After |
|------|--------|-------|
| **Planner** | `llm` | `planner_llm` |
| **Analyzer** | `llm` | `llm` (기본) |
| **Writer** | `llm` | `writer_llm` |
| **Critique** | `llm` | `critic_llm` |

### 2.3 환경변수 지원

향후 다양한 모델을 쉽게 설정할 수 있도록 환경변수 지원:

```bash
# .env에 추가 가능
PLANNER_MODEL=gemini-2.0-flash
WRITER_MODEL=gemini-1.5-pro
CRITIC_MODEL=gemini-2.0-flash
```

---

## 3. 벤치마크 결과

### Phase 5 → Phase 6 비교

| 지표 | Phase 5 | Phase 6 | 변화 |
|------|---------|---------|------|
| **평균 시간** | 31.29s | 31.59s | +1.0% |
| **평균 토큰** | 1,273 | 1,297 | +1.9% |
| **인용률** | 100% | 100% | 유지 ✅ |
| **평균 응답** | 3,300자 | 3,342자 | +1.3% |

> 📊 **성능 유지**: 역할별 LLM 분리로 인한 성능 저하 없음

### Phase 0 → Phase 6 누적 비교

| 지표 | Phase 0 | Phase 6 | 누적 변화 |
|------|---------|---------|----------|
| **시간** | 32.54s | 31.59s | **-2.9%** ⬇️ |
| **토큰** | 1,369 | 1,297 | **-5.3%** ⬇️ |
| **인용** | 0% | 100% | **+100%** 🎉 |

---

## 4. 개별 테스트 결과

| 테스트 | 시간 | 검색 | URL | 반복 | 토큰 | 응답 | 인용 |
|--------|------|------|-----|------|------|------|------|
| 비교형 | 26.50s | 2 | 6 | 2 | 1,294 | 3,319자 | ✅ |
| 학술형 | 40.39s | 3 | 9 | 3 | 1,362 | 3,512자 | ✅ |
| 기술형 | 27.89s | 2 | 6 | 2 | 1,234 | 3,194자 | ✅ |

---

## 5. Temperature 설정 효과

### 역할별 Temperature 설계 근거

| 역할 | Temperature | 근거 |
|------|-------------|------|
| **Planner (0.3)** | 낮음 | 일관된 검색 쿼리 생성, 예측 가능한 계획 |
| **Searcher (0.5)** | 중간 | 균형 잡힌 정보 수집 |
| **Analyzer (0.3)** | 낮음 | 객관적 분석, 정확한 판단 |
| **Writer (0.7)** | 높음 | 창의적 표현, 다양한 문체 |
| **Critic (0.2)** | 매우 낮음 | 일관된 평가 기준, 객관적 점수 |

---

## 6. 향후 확장

### 6.1 다중 모델 지원

현재 모든 역할에 Gemini 2.0 Flash를 사용하지만, 향후 다양한 모델 조합 가능:

```python
# 예시: 고품질 응답을 위해 Writer에 Pro 모델 사용
WRITER_MODEL=gemini-1.5-pro

# 예시: 비용 절감을 위해 Planner에 저렴한 모델 사용
PLANNER_MODEL=gemini-1.5-flash
```

### 6.2 모델별 비용 예측

| 모델 | 입력 가격 | 출력 가격 | 권장 역할 |
|------|----------|----------|----------|
| gemini-2.0-flash | 저렴 | 저렴 | 전체 |
| gemini-1.5-pro | 중간 | 중간 | Writer |
| gpt-4o | 높음 | 높음 | Critic |

---

## 7. 결론

| 항목 | 결과 |
|------|------|
| **ResearchConfig** | ✅ 구현 완료 |
| **역할별 LLM 분리** | ✅ 4개 역할 적용 |
| **환경변수 지원** | ✅ 확장 가능 |
| **성능 유지** | ✅ 변화 없음 |
| **유연성 향상** | ✅ 다중 모델 준비 완료 |

---

## 부록: 원시 데이터

- `benchmark_results/phase_6_20251220_235744.json`
- `benchmark_logs/phase_6_verbose_*.log`
- `src/agent/config.py` (신규)
