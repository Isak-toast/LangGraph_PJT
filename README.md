# Deep Research Agent

> LangGraph 기반 AI 에이전트 - 복잡한 질문에 대해 다단계 연구를 수행하고 인용이 포함된 보고서를 생성

---

## 📁 프로젝트 구조

```
LangGraph_PJT/
├── docs/                   # 보고서 및 개발 문서 (28개)
├── langgraph_server/       # Deep Research Agent 서버 코드
├── _learning_materials/    # 튜토리얼, 예제, 학습 자료
├── .env                    # 환경 변수
└── README.md               # 이 문서
```

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 활성화
cd langgraph_server
source .venv/bin/activate

# 환경 변수 로드
export $(grep -v '^#' .env | xargs)
```

### 2. 서버 실행

```bash
# LangGraph 서버 실행
langgraph up

# 또는 개발 모드
python run_benchmark.py --phase "Test" --query "What is AI?"
```

---

## 📖 주요 문서

| 문서 | 설명 |
|------|------|
| [docs/TEMPLATE_deep_research_agent_description.md](./docs/TEMPLATE_deep_research_agent_description.md) | 에이전트 설명 문서 |
| [docs/2025_12_21-deep_research_roadmap_v2.md](./docs/2025_12_21-deep_research_roadmap_v2.md) | 개발 로드맵 |
| [docs/2025_12_21-phase11_mcp_report.md](./docs/2025_12_21-phase11_mcp_report.md) | 최신 보고서 |

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 🔍 다중 검색 | Tavily API로 여러 쿼리 동시 검색 |
| 📖 병렬 URL 읽기 | 웹페이지 내용 병렬 수집 |
| 🧠 Think Tool | 추론 과정 명시화 |
| 📝 인용 포함 보고서 | 출처 표시된 구조화 보고서 |
| ⭐ CARC 품질 평가 | 완성도, 정확도, 관련성, 명확성 평가 |
| 🔌 MCP 도구 | 외부 도구 확장 (7개) |
| 💾 연구 결과 저장 | 최종 보고서 자동 저장 |

---

## 📊 성능 지표

| 지표 | 값 |
|------|------|
| 평균 처리 시간 | 29.69s |
| CARC 품질 | 16.2/20 (Good) |
| 인용률 | 100% |
| 병렬 Speedup | 2.4x~2.7x |

---

## 📚 학습 자료

튜토리얼 및 예제는 `_learning_materials/` 폴더에서 확인하세요:

```
_learning_materials/
├── tutorials/          # 01~06 단계별 튜토리얼
├── examples/           # 에이전트 예제들
└── LEARNING_GUIDE.md   # 학습 가이드
```

---

## ⚙️ 환경 변수

```bash
# .env 파일
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
MCP_ENABLED=true  # MCP 도구 활성화
```

---

*작성자: 김이삭*
