"""
tools.py - 에이전트 도구 정의
==============================

이 파일은 에이전트들이 사용할 수 있는 도구(Tools)를 정의합니다.
도구는 에이전트가 외부 세계와 상호작용하는 방법입니다.

현재 도구:
- Tavily Search: 웹 검색 API (검색 결과 요약)
- Read URL: 특정 URL의 전체 내용을 읽어오기

도구란?
- LLM이 직접 할 수 없는 작업을 수행하는 함수
- 예: 웹 검색, 데이터베이스 조회, API 호출, 계산 등
"""

import os
import httpx
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool


# ================================================================
# Tavily Search Tool (웹 검색 도구)
# ================================================================
# 
# Tavily는 AI 에이전트를 위해 최적화된 검색 API입니다.
# 검색 결과의 요약과 URL을 반환합니다.
#
# 사용 방법:
#   result = tavily_tool.invoke("검색할 쿼리")
#
# 반환 형식:
#   [{"content": "검색 결과 요약...", "url": "https://..."}, ...]

tavily_tool = TavilySearchResults(
    max_results=5  # 더 많은 검색 결과로 증가
)


# ================================================================
# URL Reader Tool (웹 페이지 내용 읽기)
# ================================================================
# 
# 특정 URL의 실제 내용을 읽어와서 텍스트로 반환합니다.
# Tavily가 요약만 제공하는 것과 달리, 전체 페이지 내용을 가져옵니다.
#
# 사용 방법:
#   result = read_url_tool.invoke("https://arxiv.org/abs/...")
#
# 반환 형식:
#   "웹 페이지의 텍스트 내용 (최대 8000자)"

@tool
def read_url_tool(url: str) -> str:
    """
    Read the full content of a web page URL.
    Use this tool to get detailed information from a specific URL found during search.
    
    Args:
        url: The URL to read (e.g., "https://arxiv.org/abs/2412.03801")
    
    Returns:
        The text content of the web page (max 8000 characters)
    
    Example:
        read_url_tool("https://arxiv.org/html/2412.03801v1")
    """
    try:
        # HTTP 요청으로 페이지 내용 가져오기
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"
        }
        
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
        
        content = response.text
        
        # HTML 태그 간단히 제거 (BeautifulSoup 없이)
        import re
        # script, style 태그 제거
        content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
        content = re.sub(r'<style[^>]*>.*?</style>', '', content, flags=re.DOTALL | re.IGNORECASE)
        # HTML 태그 제거
        content = re.sub(r'<[^>]+>', ' ', content)
        # 연속된 공백 정리
        content = re.sub(r'\s+', ' ', content).strip()
        
        # 토큰 제한을 위해 8000자로 자르기
        if len(content) > 8000:
            content = content[:8000] + "... [truncated]"
        
        print(f"📖 Read URL: {url[:50]}... ({len(content)} chars)")
        return content
        
    except httpx.TimeoutException:
        return f"Error: Timeout while reading URL: {url}"
    except httpx.HTTPStatusError as e:
        return f"Error: HTTP {e.response.status_code} for URL: {url}"
    except Exception as e:
        return f"Error reading URL {url}: {str(e)}"


# ================================================================
# 사용 가능한 도구 목록
# ================================================================
# 
# Researcher는 이 두 도구를 모두 사용할 수 있습니다:
# 1. tavily_tool: 먼저 웹 검색으로 관련 URL 찾기
# 2. read_url_tool: 찾은 URL의 상세 내용 읽기

tools = [tavily_tool, read_url_tool]
