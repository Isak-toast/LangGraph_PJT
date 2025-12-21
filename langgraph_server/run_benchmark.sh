#!/bin/bash
# ==============================================
# Deep Research Benchmark 실행 스크립트
# ==============================================
#
# 사용법:
#   ./run_benchmark.sh                     # Phase 0 전체 테스트 (500자 미리보기)
#   ./run_benchmark.sh "Phase 1"           # Phase 1 테스트
#   ./run_benchmark.sh "Phase 0" --verbose # 전체 응답 로그 저장
#   ./run_benchmark.sh "Phase 0" "질문"    # 단일 질문 테스트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# .env 파일 로드
if [ -f ".env" ]; then
    echo -e "${YELLOW}Loading .env file...${NC}"
    export $(grep -v '^#' .env | xargs)
fi

# 기본값
PHASE="${1:-Phase 0}"
VERBOSE=""
QUERY=""

# 인자 파싱
shift 2>/dev/null || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE="--verbose"
            export VERBOSE_LOGGING="true"  # 노드 로깅에서 전체 출력
            shift
            ;;
        *)
            QUERY="$1"
            shift
            ;;
    esac
done

# 로그 디렉토리 설정
LOG_DIR="benchmark_logs"
mkdir -p "$LOG_DIR"

# 타임스탬프
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PHASE_SLUG=$(echo "$PHASE" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')
VERBOSE_TAG=""
if [ -n "$VERBOSE" ]; then
    VERBOSE_TAG="_verbose"
fi
LOG_FILE="$LOG_DIR/${PHASE_SLUG}${VERBOSE_TAG}_${TIMESTAMP}.log"

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════"
echo "║  Deep Research Benchmark"
echo "╠═══════════════════════════════════════════════════════════════"
echo "║  Phase: $PHASE"
echo "║  Verbose: $([ -n "$VERBOSE" ] && echo "ON (full response)" || echo "OFF (500 char preview)")"
echo "║  Log: $LOG_FILE"
echo "║  Time: $(date)"
echo "╚═══════════════════════════════════════════════════════════════"
echo -e "${NC}"

# Python 경로 확인
PYTHON_CMD="python"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
fi

# 벤치마크 실행 및 로그 저장
echo -e "${YELLOW}Starting benchmark...${NC}"
echo ""

if [ -z "$QUERY" ]; then
    # 전체 테스트
    $PYTHON_CMD run_benchmark.py --phase "$PHASE" $VERBOSE 2>&1 | tee "$LOG_FILE"
else
    # 단일 쿼리 테스트
    $PYTHON_CMD run_benchmark.py --phase "$PHASE" --query "$QUERY" $VERBOSE 2>&1 | tee "$LOG_FILE"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Benchmark Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "📁 Log saved: ${BLUE}$LOG_FILE${NC}"
echo -e "📊 Results:   ${BLUE}benchmark_results/${PHASE_SLUG}_*.json${NC}"
echo ""

# 요약 정보 추가
echo "═══════════════════════════════════════════════════════════════" >> "$LOG_FILE"
echo "Benchmark completed at: $(date)" >> "$LOG_FILE"
echo "═══════════════════════════════════════════════════════════════" >> "$LOG_FILE"
