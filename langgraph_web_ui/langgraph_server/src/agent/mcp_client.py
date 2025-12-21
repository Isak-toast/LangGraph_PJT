"""
mcp_client.py - MCP (Model Context Protocol) 통합
==================================================

Phase 11: 외부 도구 확장을 위한 MCP 클라이언트 설정

이 모듈은 LangChain MCP Adapters를 사용하여 외부 MCP 서버와 연결하고,
도구를 Deep Research 에이전트에 통합합니다.
"""

import os
import asyncio
from typing import Optional, List
from langchain_core.tools import BaseTool

# MCP 도구 사용 여부 (환경변수로 제어)
MCP_ENABLED = os.environ.get("MCP_ENABLED", "false").lower() == "true"


async def get_mcp_tools() -> List[BaseTool]:
    """
    MCP 서버에서 도구를 로드합니다.
    
    환경변수 MCP_ENABLED=true 일 때만 MCP 도구를 로드합니다.
    MCP 서버가 없거나 연결 실패 시 빈 리스트를 반환합니다.
    
    Returns:
        MCP 도구 리스트
    """
    if not MCP_ENABLED:
        return []
    
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        
        # MCP 서버 설정
        # 커스텀 Python MCP 서버: 텍스트 분석 도구
        import sys
        mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")
        
        mcp_server_config = {
            # Deep Research 텍스트 분석 도구 (Python MCP Server)
            "research_tools": {
                "command": sys.executable,
                "args": [mcp_server_path],
                "transport": "stdio",
            },
            
            # 예시: Brave Search (BRAVE_API_KEY 필요)
            # "brave_search": {
            #     "command": "npx",
            #     "args": ["-y", "@anthropics/mcp-server-brave-search"],
            #     "transport": "stdio",
            #     "env": {"BRAVE_API_KEY": os.environ.get("BRAVE_API_KEY", "")}
            # },
            
            # 예시: 파일 시스템 접근
            # "filesystem": {
            #     "command": "npx",
            #     "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
            #     "transport": "stdio",
            # },
        }
        
        if not mcp_server_config:
            print("📦 MCP: No MCP servers configured")
            return []
        
        client = MultiServerMCPClient(mcp_server_config)
        tools = await client.get_tools()
        
        print(f"📦 MCP: Loaded {len(tools)} tools from MCP servers")
        for tool in tools:
            print(f"   └─ {tool.name}: {tool.description[:50]}...")
        
        return tools
        
    except ImportError as e:
        print(f"📦 MCP: langchain-mcp-adapters not installed: {e}")
        return []
    except Exception as e:
        print(f"📦 MCP: Failed to load tools: {e}")
        return []


def get_mcp_tools_sync() -> List[BaseTool]:
    """
    MCP 도구를 동기적으로 가져옵니다.
    
    이미 실행 중인 이벤트 루프가 있으면 새 루프를 생성하지 않습니다.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop is None:
        # 이벤트 루프가 없으면 새로 생성
        return asyncio.run(get_mcp_tools())
    else:
        # 이미 실행 중인 루프가 있으면 nest_asyncio 사용 또는 빈 리스트 반환
        try:
            import nest_asyncio
            nest_asyncio.apply()
            return asyncio.run(get_mcp_tools())
        except ImportError:
            print("📦 MCP: nest_asyncio not installed, skipping MCP tools in async context")
            return []


# ================================================================
# MCP 상태 확인
# ================================================================

def print_mcp_status():
    """MCP 통합 상태를 출력합니다."""
    print(f"\n📦 MCP Integration Status:")
    print(f"   └─ Enabled: {MCP_ENABLED}")
    if MCP_ENABLED:
        print(f"   └─ Note: MCP tools will be loaded at runtime")
    else:
        print(f"   └─ Enable: export MCP_ENABLED=true")
