# LangGraph Agent Server

LangGraph CLI를 사용한 에이전트 서버입니다.

## 시작하기

### 1. 의존성 설치
```bash
pip install -U "langgraph-cli[inmem]"
pip install -e .
```

### 2. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일에서 API 키 입력
```

### 3. 서버 실행
```bash
langgraph dev
```

LangGraph Studio가 자동으로 열립니다!

## 프로젝트 구조
```
langgraph_server/
├── langgraph.json      # LangGraph CLI 설정
├── pyproject.toml      # Python 프로젝트 설정
├── .env.example        # 환경 변수 예시
└── src/
    └── agent/
        ├── __init__.py
        ├── graph.py    # 에이전트 그래프 정의
        ├── state.py    # 상태 정의
        ├── nodes.py    # 노드 구현
        └── tools.py    # 도구 정의
```
