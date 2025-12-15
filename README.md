# LangGraph 튜토리얼 및 예제

이 저장소는 다양한 LangGraph 예제와 튜토리얼을 포함하고 있습니다. 각 하위 폴더를 참고하세요.

## 📚 학습 시작하기

> **처음이신가요?** [LEARNING_GUIDE.md](./LEARNING_GUIDE.md)에서 추천 학습 순서를 확인하세요!

## LangGraph란?

**LangGraph**는 LangChain 팀에서 개발한 라이브러리로, **상태 기반의 순환 그래프 구조**를 통해 복잡한 AI 에이전트 시스템을 구축할 수 있게 해줍니다.

### 핵심 개념

| 개념 | 설명 |
|------|------|
| **StateGraph** | 상태를 정의하고 노드 간에 전달하는 그래프 |
| **Node** | 특정 작업을 수행하는 함수 |
| **Edge** | 노드 간의 연결 (조건부 분기 가능) |
| **Checkpointer** | 상태 저장/복원 메커니즘 |

---

## 프로젝트 목록

각 폴더의 README.md에서 **상세 코드 분석**과 **실행 예시**를 확인할 수 있습니다.

### 🎯 기초 (Foundation)

| 폴더 | 설명 | 핵심 개념 |
|------|------|----------|
| [`01_quickstart_calculator`](./01_quickstart_calculator) | LangGraph Quickstart | StateGraph, ToolNode, Conditional Edge |
| [`single_agent_basic`](./single_agent_basic) | ReAct 에이전트 | create_react_agent, 도구 호출 |
| [`02_streaming_patterns`](./02_streaming_patterns) | 스트리밍 패턴 | values vs updates 모드 |

### 💾 상태 관리 (State Management)

| 폴더 | 설명 | 핵심 개념 |
|------|------|----------|
| [`03_persistence`](./03_persistence) | 영속성/메모리 | Checkpointer, thread_id |
| [`04_human_in_the_loop`](./04_human_in_the_loop) | 사람 승인 패턴 | interrupt_before, 실행 재개 |

### 🚀 고급 패턴 (Advanced Patterns)

| 폴더 | 설명 | 핵심 개념 |
|------|------|----------|
| [`05_hierarchical_subgraphs`](./05_hierarchical_subgraphs) | 서브그래프 | 그래프 합성, 상태 매핑 |
| [`reflection`](./reflection) | 자기 검토 패턴 | Generate-Reflect 루프 |
| [`plan_and_execute`](./plan_and_execute) | 계획-실행 | Planner, Executor, Replanner |
| [`06_agentic_rag`](./06_agentic_rag) | Agentic RAG | 문서 평가, 조건부 생성 |

### 🤖 멀티 에이전트 (Multi-Agent)

| 폴더 | 설명 | 핵심 개념 |
|------|------|----------|
| [`multi_agent_supervisor`](./multi_agent_supervisor) | 슈퍼바이저 패턴 | 중앙 관제, 작업자 라우팅 |
| [`multi_agent_network`](./multi_agent_network) | 네트워크 패턴 | Handoff, 탈중앙화 협업 |
| [`lats`](./lats) | 트리 탐색 | Best-of-N, 후보 평가 |

### 🔬 심화 프로젝트 (Capstone)

| 폴더 | 설명 |
|------|------|
| [`open_deep_research`](./open_deep_research) | 심층 리서치 에이전트 (프로덕션 수준) |

---

## ⚙️ 환경 설정

### 필수 API 키

```bash
# .env 파일 생성
GOOGLE_API_KEY=your_google_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### 공통 의존성

```bash
pip install langgraph langchain-google-genai langchain-community python-dotenv tavily-python
```

---

## 📖 추천 학습 순서

```
01_quickstart_calculator → single_agent_basic → 02_streaming_patterns
                                    ↓
03_persistence → 04_human_in_the_loop → 05_hierarchical_subgraphs
                                    ↓
reflection → plan_and_execute → 06_agentic_rag
                                    ↓
multi_agent_supervisor → multi_agent_network → lats
                                    ↓
                           open_deep_research
```

자세한 학습 가이드는 [LEARNING_GUIDE.md](./LEARNING_GUIDE.md)를 참고하세요.

---

*Happy Learning! 🚀*
