#!/bin/bash

# ============================================
# LangGraph Server - Setup & Run Script
# ============================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  LangGraph Server Setup${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check Python version
PYTHON_CMD=""
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    echo -e "${RED}Error: Python 3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Using Python: $($PYTHON_CMD --version)${NC}"

# Create virtual environment if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}▶ Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}▶ Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo -e "${YELLOW}▶ Upgrading pip...${NC}"
pip install --upgrade pip -q

# Install LangGraph CLI
echo -e "${YELLOW}▶ Installing LangGraph CLI...${NC}"
pip install -U "langgraph-cli[inmem]" -q

# Install project dependencies
echo -e "${YELLOW}▶ Installing project dependencies...${NC}"
pip install -e . -q

# Check for .env file
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    if [ -f "$SCRIPT_DIR/.env.example" ]; then
        echo -e "${YELLOW}▶ Creating .env from .env.example...${NC}"
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        echo -e "${RED}⚠ Please edit .env and add your API keys!${NC}"
    else
        echo -e "${RED}⚠ No .env file found${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

echo ""
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Setup Complete!${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "To activate the virtual environment:"
echo -e "  ${YELLOW}source .venv/bin/activate${NC}"
echo ""
echo -e "To start the server:"
echo -e "  ${YELLOW}langgraph dev${NC}"
echo ""

# Parse arguments
if [[ "$1" == "--run" || "$1" == "-r" ]]; then
    echo -e "${YELLOW}▶ Starting LangGraph Server...${NC}"
    langgraph dev
fi
