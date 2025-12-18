# 🧪 Agentic Insight Dashboard - 테스트 가이드

## 빠른 시작

```bash
# 프로젝트 루트에서 실행
cd /home/isak/LangGraph_PJT/langgraph_web_ui

# 모든 테스트 실행
./run_tests.sh

# 또는 개별 테스트
./run_tests.sh --unit      # Unit 테스트만
./run_tests.sh --e2e       # E2E 테스트만
./run_tests.sh --backend   # 백엔드 테스트만
```

---

## 테스트 종류

### 1. Frontend Unit Tests (Vitest)
컴포넌트 단위 테스트

```bash
cd client
npx vitest run              # 한번 실행
npx vitest                  # 워치 모드 (파일 변경 감지)
npx vitest run --coverage   # 커버리지 리포트
```

**테스트 파일:**
- `src/components/ChatMessage.test.ts`

### 2. E2E Tests (Playwright)
전체 UI 통합 테스트

```bash
cd client

# ⚠️ 먼저 개발 서버 실행 필요!
npm run dev &

# E2E 테스트 실행
npx playwright test                      # CLI 모드
npx playwright test --ui                 # UI 모드 (권장)
npx playwright test --headed             # 브라우저 보이기
npx playwright test --update-snapshots   # 스냅샷 갱신
```

**테스트 파일:**
- `tests/e2e/dashboard.spec.ts`

### 3. Backend Tests (pytest)
API 및 LangGraph 로직 테스트

```bash
cd server
source venv/bin/activate  # venv 활성화

python -m pytest tests/ -v           # 상세 출력
python -m pytest tests/ --cov=app    # 커버리지
```

**테스트 파일:**
- `tests/test_graph.py`

---

## 주요 명령어 모음

| 명령어 | 설명 |
|--------|------|
| `./run_tests.sh` | 모든 테스트 실행 |
| `./run_tests.sh -u` | Unit 테스트만 |
| `./run_tests.sh -e` | E2E 테스트만 |
| `./run_tests.sh -e -s` | E2E + 스냅샷 갱신 |
| `npx playwright test --ui` | Playwright UI 모드 |

---

## 트러블슈팅

### E2E 테스트 실패: "Connection refused"
```bash
# 개발 서버가 실행 중인지 확인
npm run dev
# 그 후 다른 터미널에서 테스트 실행
```

### Visual Snapshot 불일치
```bash
# 새 스냅샷으로 업데이트
npx playwright test --update-snapshots
```

### Playwright 브라우저 설치
```bash
npx playwright install
```
