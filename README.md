# Deep Research Agent

> **복잡한 질문에 대해 다단계 연구를 수행하고 인용이 포함된 보고서를 생성하는 AI 에이전트**

작성자: 김이삭  
작성일: 2025-12-21

---

## 프로젝트 소개

- LangGraph의 기본적인 아키텍처를 공부하면서 Open Deep Research Agent를 따라가고자 했고, 기본적인 아키텍처를 기반으로 개선점을 적용하며 실제 에이전트 개발 과정을 상세하게 기록하였습니다.
- 추후에는 Open Deep Research Agent의 발전 버전으로 개선하고자 합니다.

---

## 📁 프로젝트 구조

```
LangGraph_PJT/
├── docs/                   # 보고서 및 개발 문서
├── langgraph_server/       # Deep Research Agent 서버 코드
├── _learning_materials/    # 튜토리얼, 예제, 학습 자료
└── README.md
```

---

## 🚀 설치 및 실행

### 사전 요구사항

- **Python 3.11+**
- **API 키**: Google API Key, Tavily API Key

### Step 1: 저장소 클론

```bash
git clone https://github.com/Isak-toast/LangGraph_PJT.git
cd LangGraph_PJT
```

### Step 2: 자동 설치 (권장)

```bash
cd langgraph_server
chmod +x setup.sh
./setup.sh
```

이 스크립트가 다음을 자동으로 수행합니다:
- 가상환경 생성 (`.venv/`)
- pip 업그레이드
- LangGraph CLI 설치
- 프로젝트 의존성 설치

### Step 3: 환경 변수 설정

```bash
# .env 파일 편집
vim .env
```

```bash
# .env 내용
LANGSMITH_API_KEY=your_langsmith_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

MCP_ENABLED=true
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=agentic-insight
```

### Step 4: 서버 실행

```bash
# 가상환경 활성화
source .venv/bin/activate

# 환경 변수 로드
export $(grep -v '^#' .env | xargs)

# LangGraph 서버 실행
langgraph dev
```

## 🧪 테스트 실행

```bash
cd langgraph_server
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)

# 벤치마크 테스트
python run_benchmark.py --phase "Test" --query "What is LangGraph?" --verbose
```

---

## 🏗️ 아키텍처 발전 과정

### 초기 아키텍처 (Baseline)

```
User Query → Searcher → Reader → Writer → Response
```

**문제점**: 단일 검색으로 깊이 부족, 인용 없음, 품질 검증 없음

### 현재 아키텍처 (Phase 11)

```
                    ┌─────────────────────────────────────┐
                    │         Deep Research Graph         │
                    └─────────────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │           Clarify             │ ← 질문 명확화
                    └───────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │           Planner             │ ← 연구 계획 수립
                    └───────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │          Supervisor           │ ← 복잡도 분석
                    └───────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │     Parallel Researcher       │ ← 다중 쿼리 병렬 연구
                    │  ┌────┐ ┌────┐ ┌────┐         │
                    │  │ Q1 │ │ Q2 │ │ Q3 │         │
                    │  └────┘ └────┘ └────┘         │
                    └───────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │          Compress             │ ← 결과 압축 + MCP
                    └───────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │           Writer              │ ← 보고서 생성
                    └───────────────────────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │          Critique             │ ← CARC 품질 평가
                    └───────────────────────────────┘
```

### 개발 과정 (12 Phases)

| Phase | 개선 내용 | 결과 |
|-------|----------|------|
| 0 | Baseline 측정 | 32.54s |
| 1 | Compress 노드 | 토큰 -14% |
| 2 | Think Tool | 추론 명시화 |
| 3 | Clarify 노드 | 질문 명확화 |
| 4 | XML 프롬프트 | 9% 시간 단축 |
| 5 | Self-Critique (CARC) | 품질 16.3/20 |
| 6 | Multi-LLM | 비용 효율화 |
| 7 | 병렬 URL 읽기 | 8.8% 시간 단축 |
| 8 | Subgraph 반복 | 깊이 있는 연구 |
| 9 | Supervisor | 동적 전략 |
| 10 | 병렬 연구 | 2.4x Speedup |
| 11 | MCP 통합 | 외부 도구 확장 |

---

## ✨ 주요 기능

| 기능 | 설명 |
|------|------|
| 🔍 다중 검색 | Tavily API로 여러 쿼리 동시 검색 |
| 📖 병렬 URL 읽기 | 웹페이지 내용 병렬 수집 |
| 🧠 Think Tool | 추론 과정 명시화 |
| 📝 인용 포함 보고서 | 출처 표시된 구조화 보고서 |
| ⭐ CARC 품질 평가 | 완성도, 정확도, 관련성, 명확성 |
| 🔌 MCP 도구 | 외부 도구 7개 확장 |
| 💾 연구 결과 저장 | 최종 보고서 자동 저장 |
| 🎯 Supervisor 제어 | 쿼리 복잡도 기반 동적 전략 |

### MCP 도구 (7개)

| 도구 | 설명 |
|------|------|
| `summarize_text` | 긴 텍스트 요약 (개선 필요) |
| `extract_key_points` | 핵심 포인트 추출 (개선 필요) |
| `count_words` | 단어/문자 통계 |
| `read_file` | 파일 내용 읽기 |
| `list_files` | 디렉토리 목록 |
| `save_research` | 연구 결과 저장 |
| `search_wikipedia` | 위키피디아 검색 (현재 사용 못함) |

---

## 📊 성능 지표

| 지표 | Baseline | 현재 | 변화 |
|------|----------|------|------|
| 평균 시간 | 32.54s | 29.69s | **-8.8%** |
| 토큰 사용량 | 1,368 | 1,168 | **-14.6%** |
| CARC 품질 | N/A | 16.2/20 | 👍 Good |
| 인용률 | N/A | 100% | ✅ |
| 병렬 Speedup | 1x | 2.4x | **+140%** |

---

## 🛠 기술 스택

| 카테고리 | 기술 |
|---------|------|
| 프레임워크 | LangGraph, LangChain |
| LLM | Google Gemini |
| 검색 API | Tavily Search |
| 프로토콜 | MCP (Model Context Protocol) |
| 언어 | Python 3.11+ |

---

## 📚 문서

- [docs](./docs) 폴더 확인

---

## 🔮 향후 계획

### 고급 기능 Phase (12+)

| Phase | 기능 | 설명 |
|-------|------|------|
| 12 | **Human-in-the-Loop** | 모호한 질문 시 명확화 요청, 연구 중간 확인/수정 |
| 13 | **멀티모달 연구** | 이미지 분석, PDF 파싱, Gemini Vision API |
| 14 | **지식 그래프 통합** | 연구 결과 저장, 이전 연구 참조, 누적 학습 |
| 15 | **협업 멀티에이전트** | 전문 분야별 에이전트, 에이전트 간 토론/합의 |

---

## 🌐 외부 데모 URL

> ⚠️ **현재 상태**: Studio 외부 접속 준비 중

### 현재 가능한 접속 방법

**로컬 환경 (권장)**:
```bash
cd langgraph_server
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
langgraph dev
```
→ 브라우저에서 자동으로 Studio 열림

**API 문서 (외부 공유 가능)**:
```bash
langgraph dev --tunnel
```
→ 터널 URL의 `/docs` 페이지로 API 직접 테스트 가능

### 예정 사항

| 항목 | 상태 | 설명 |
|------|------|------|
| 로컬 Studio | ✅ 완료 | `langgraph dev`로 로컬 접속 |
| API /docs 공유 | ✅ 완료 | 터널 URL `/docs`로 외부 테스트 |
| Studio 외부 접속 | 🔄 조사 중 | LangGraph CORS 이슈 해결 필요 |
| 클라우드 배포 | 📋 예정 | LangGraph Cloud 또는 Render 배포 |

> 💡 Studio 외부 접속 문제는 LangGraph CLI의 CORS 설정 관련 이슈로, 추후 업데이트 예정입니다.
