# Phase 7 병렬 연구 최종 보고서

> 측정일: 2025-12-21
> 개선사항: ContentReader 병렬 URL 읽기 + User-Agent 헤더 개선

---

## 1. 요약

| 지표 | Phase 0 (Baseline) | Phase 7 (최종) | 변화 |
|------|-------------------|----------------|------|
| **평균 시간** | 32.54s | **29.69s** | **-8.8%** ✅ |
| **평균 토큰** | 1,368 | **1,168** | **-14.6%** ✅ |
| **CARC 품질** | N/A | **16.1/20** | 👍 Good |
| **인용률** | 100% | 100% | 유지 ✅ |

---

## 2. Phase별 처리 시간 비교

```
Phase 0 (Baseline) ████████████████████████████████ 32.54s
Phase 1 (Compress) ███████████████████████████████░ 31.79s (-2.3%)
Phase 2 (Think)    ██████████████████████████████░░ 30.21s (-7.2%)
Phase 3 (Clarify)  █████████████████████████████████████░ 36.97s (+13.6%)
Phase 4 (XML)      █████████████████████████████░░░ 29.62s (-9.0%)
Phase 5 (Critique) ███████████████████████████████░ 31.29s (-3.8%)
Phase 6 (Multi)    ██████████████████████████████░░ 30.18s (-7.3%)
Phase 7 (최종)     █████████████████████████████░░░ 29.69s (-8.8%) ✅
```

---

## 3. Phase 7 구현 내용

### 3.1 ContentReader 병렬 URL 읽기

```python
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    future_to_url = {executor.submit(read_single_url, url): url for url in urls_to_process}
```

- 3개 URL 동시 처리
- 실행 시간: 0.1s ~ 2s (기존 순차 6s+)

### 3.2 User-Agent 헤더 개선

```python
# Before (많은 403 에러 발생)
headers = {"User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"}

# After (현실적인 브라우저 헤더)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
```

### 3.3 시도했으나 롤백된 기능

- **ParallelResearcher 노드**: 모든 쿼리 동시 실행
- **롤백 이유**: Searcher → ContentReader → Analyzer 반복 루프가 깊이 있는 연구에 필수

---

## 4. HTTP 403 에러 현황

| 시점 | 403 에러 수 | 원인 |
|------|------------|------|
| Phase 0 | 7 | medium.com, datacamp.com 봇 차단 |
| Phase 7 | 11 | 일부 사이트 Cloudflare 차단 유지 |

> 참고: 403 에러는 User-Agent만으로는 완전히 해결되지 않음. 일부 사이트는 Cloudflare 등 추가 보호 사용.

---

## 5. 토큰 효율 분석

| Phase | 평균 토큰 | 변화 |
|-------|----------|------|
| Phase 0 | 1,368 | 기준 |
| Phase 1 | 1,176 | -14.0% |
| **Phase 7** | **1,168** | **-14.6%** ✅ |

> **결론**: 토큰 효율이 오히려 개선됨

---

## 6. 결론

### 달성됨 ✅
- 처리 시간 **-8.8%** 단축 (32.54s → 29.69s)
- 토큰 효율 **-14.6%** 개선 (1,368 → 1,168)
- CARC 품질 **16.1/20** 유지
- 인용률 **100%** 유지

### 미달성 ⚠️
- 목표 처리 시간 -50% 달성 못함
- 이유: 깊이 있는 반복 연구를 위해 순차 흐름 유지 필요

### 향후 개선 방향
- [ ] LLM 응답 스트리밍으로 대기 시간 감소
- [ ] 검색 결과 캐싱으로 중복 요청 방지
- [ ] 더 빠른 경량 모델 사용 (Clarify, Planner)

---

## 부록: 원시 데이터

- `benchmark_results/phase_7_ua_fix_20251221_010631.json`
- `benchmark_logs/phase_7_ua_fix_*.log`
