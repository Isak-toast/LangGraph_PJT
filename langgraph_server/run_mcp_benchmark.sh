#!/bin/bash
# ================================================================
# Phase 11 MCP Benchmark Comparison Script
# ================================================================
# 
# MCP_ENABLED=false vs MCP_ENABLED=true 벤치마크 비교
#

set -e
cd "$(dirname "$0")"

# 환경 로드
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_DIR=benchmark_logs

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Phase 11: MCP Benchmark Comparison                           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# ================================================================
# Test 1: MCP Disabled (기본)
# ================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔴 Test 1: MCP DISABLED (baseline)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
export MCP_ENABLED=false
python run_benchmark.py --phase "Phase 11 MCP OFF" --verbose 2>&1 | tee ${LOG_DIR}/phase_11_mcp_off_${TIMESTAMP}.log

echo ""
echo ""

# ================================================================
# Test 2: MCP Enabled
# ================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🟢 Test 2: MCP ENABLED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
export MCP_ENABLED=true
python run_benchmark.py --phase "Phase 11 MCP ON" --verbose 2>&1 | tee ${LOG_DIR}/phase_11_mcp_on_${TIMESTAMP}.log

echo ""
echo ""

# ================================================================
# Summary
# ================================================================
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  Benchmark Complete                                           ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "Log files saved to:"
echo "  - ${LOG_DIR}/phase_11_mcp_off_${TIMESTAMP}.log"
echo "  - ${LOG_DIR}/phase_11_mcp_on_${TIMESTAMP}.log"
echo ""
echo "Compare results with:"
echo "  grep 'Summary' ${LOG_DIR}/phase_11_mcp_*_${TIMESTAMP}.log"
echo ""
