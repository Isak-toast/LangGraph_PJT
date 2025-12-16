#!/bin/bash
# =============================================================================
# LangGraph Examples - Environment Activation Script
# =============================================================================
# 이 스크립트는 venv 활성화 시 자동으로 실행됩니다.
# 사용법: source scripts/activate_env.sh (또는 venv/bin/activate에서 자동 호출)
# =============================================================================

# 프로젝트 루트 디렉토리 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# PYTHONPATH 설정 (프로젝트 루트 추가)
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

# .env 파일 로드
if [ -f "${PROJECT_ROOT}/.env" ]; then
    echo "📦 Loading environment variables from .env..."
    set -a
    source "${PROJECT_ROOT}/.env"
    set +a
else
    if [ -f "${PROJECT_ROOT}/.env.example" ]; then
        echo "⚠️  .env 파일이 없습니다. .env.example을 참고하여 생성하세요:"
        echo "   cp ${PROJECT_ROOT}/.env.example ${PROJECT_ROOT}/.env"
    fi
fi

# 유용한 alias 정의
alias run01="python ${PROJECT_ROOT}/01_quickstart_calculator/main.py"
alias run02="python ${PROJECT_ROOT}/02_streaming_patterns/main.py"
alias run03="python ${PROJECT_ROOT}/03_persistence/main.py"
alias run04="python ${PROJECT_ROOT}/04_human_in_the_loop/main.py"
alias run05="python ${PROJECT_ROOT}/05_hierarchical_subgraphs/main.py"
alias run06="python ${PROJECT_ROOT}/06_agentic_rag/main.py"
alias run-single="python ${PROJECT_ROOT}/single_agent_basic/main.py"
alias run-supervisor="python ${PROJECT_ROOT}/multi_agent_supervisor/main.py"
alias run-network="python ${PROJECT_ROOT}/multi_agent_network/main.py"
alias run-lats="python ${PROJECT_ROOT}/lats/main.py"
alias run-reflection="python ${PROJECT_ROOT}/reflection/main.py"
alias run-plan="python ${PROJECT_ROOT}/plan_and_execute/main.py"

# 환경 정보 출력
echo "✅ LangGraph Examples 환경이 활성화되었습니다!"
echo "   PROJECT_ROOT: ${PROJECT_ROOT}"
echo ""
echo "📚 사용 가능한 명령어:"
echo "   run01 ~ run06    : 기본 예제 실행 (01~06)"
echo "   run-single       : Single Agent 예제"
echo "   run-supervisor   : Multi-Agent Supervisor 예제"
echo "   run-network      : Multi-Agent Network 예제"
echo "   run-lats         : LATS (Tree Search) 예제"
echo "   run-reflection   : Reflection 예제"
echo "   run-plan         : Plan-and-Execute 예제"
