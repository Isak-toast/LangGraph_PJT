#!/bin/bash

# ============================================
# Agentic Insight Dashboard - Test Runner
# ============================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Paths
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIENT_DIR="$PROJECT_ROOT/client"
SERVER_DIR="$PROJECT_ROOT/server"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Agentic Insight Dashboard - Test Suite${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Parse arguments
RUN_UNIT=false
RUN_E2E=false
RUN_BACKEND=false
RUN_ALL=false
UPDATE_SNAPSHOTS=false

if [ $# -eq 0 ]; then
    RUN_ALL=true
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit|-u)
            RUN_UNIT=true
            shift
            ;;
        --e2e|-e)
            RUN_E2E=true
            shift
            ;;
        --backend|-b)
            RUN_BACKEND=true
            shift
            ;;
        --all|-a)
            RUN_ALL=true
            shift
            ;;
        --update-snapshots|-s)
            UPDATE_SNAPSHOTS=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -u, --unit              Run frontend unit tests (Vitest)"
            echo "  -e, --e2e               Run E2E tests (Playwright)"
            echo "  -b, --backend           Run backend tests (pytest)"
            echo "  -a, --all               Run all tests (default)"
            echo "  -s, --update-snapshots  Update Playwright visual snapshots"
            echo "  -h, --help              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                      # Run all tests"
            echo "  $0 --unit               # Run only unit tests"
            echo "  $0 --e2e --update-snapshots  # Update E2E snapshots"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

if $RUN_ALL; then
    RUN_UNIT=true
    RUN_E2E=true
    RUN_BACKEND=true
fi

# Track results
UNIT_RESULT=0
E2E_RESULT=0
BACKEND_RESULT=0

# ============================================
# 1. Frontend Unit Tests (Vitest)
# ============================================
if $RUN_UNIT; then
    echo -e "${YELLOW}▶ Running Frontend Unit Tests (Vitest)...${NC}"
    cd "$CLIENT_DIR"
    
    if npx vitest run; then
        echo -e "${GREEN}✓ Unit tests passed!${NC}"
    else
        echo -e "${RED}✗ Unit tests failed!${NC}"
        UNIT_RESULT=1
    fi
    echo ""
fi

# ============================================
# 2. E2E Tests (Playwright)
# ============================================
if $RUN_E2E; then
    echo -e "${YELLOW}▶ Running E2E Tests (Playwright)...${NC}"
    cd "$CLIENT_DIR"
    
    # Check if dev server is running
    if ! curl -s http://localhost:5173 > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Dev server not running. Starting...${NC}"
        npm run dev &
        DEV_PID=$!
        sleep 5
    fi
    
    PLAYWRIGHT_CMD="npx playwright test --reporter=list"
    if $UPDATE_SNAPSHOTS; then
        PLAYWRIGHT_CMD="$PLAYWRIGHT_CMD --update-snapshots"
    fi
    
    if $PLAYWRIGHT_CMD; then
        echo -e "${GREEN}✓ E2E tests passed!${NC}"
    else
        echo -e "${RED}✗ E2E tests failed!${NC}"
        E2E_RESULT=1
    fi
    
    # Kill dev server if we started it
    if [ ! -z "$DEV_PID" ]; then
        kill $DEV_PID 2>/dev/null || true
    fi
    echo ""
fi

# ============================================
# 3. Backend Tests (pytest)
# ============================================
if $RUN_BACKEND; then
    echo -e "${YELLOW}▶ Running Backend Tests (pytest)...${NC}"
    cd "$SERVER_DIR"
    
    if [ -f "requirements.txt" ]; then
        # Activate venv if exists
        if [ -d "venv" ]; then
            source venv/bin/activate
        fi
        
        if python -m pytest tests/ -v; then
            echo -e "${GREEN}✓ Backend tests passed!${NC}"
        else
            echo -e "${RED}✗ Backend tests failed!${NC}"
            BACKEND_RESULT=1
        fi
    else
        echo -e "${YELLOW}⚠ No backend requirements.txt found, skipping...${NC}"
    fi
    echo ""
fi

# ============================================
# Summary
# ============================================
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}============================================${NC}"

TOTAL_FAILED=0

if $RUN_UNIT; then
    if [ $UNIT_RESULT -eq 0 ]; then
        echo -e "  Unit Tests:    ${GREEN}✓ PASSED${NC}"
    else
        echo -e "  Unit Tests:    ${RED}✗ FAILED${NC}"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
fi

if $RUN_E2E; then
    if [ $E2E_RESULT -eq 0 ]; then
        echo -e "  E2E Tests:     ${GREEN}✓ PASSED${NC}"
    else
        echo -e "  E2E Tests:     ${RED}✗ FAILED${NC}"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
fi

if $RUN_BACKEND; then
    if [ $BACKEND_RESULT -eq 0 ]; then
        echo -e "  Backend Tests: ${GREEN}✓ PASSED${NC}"
    else
        echo -e "  Backend Tests: ${RED}✗ FAILED${NC}"
        TOTAL_FAILED=$((TOTAL_FAILED + 1))
    fi
fi

echo ""

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! 🎉${NC}"
    exit 0
else
    echo -e "${RED}$TOTAL_FAILED test suite(s) failed.${NC}"
    exit 1
fi
