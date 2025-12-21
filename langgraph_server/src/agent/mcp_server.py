#!/usr/bin/env python
"""
mcp_server.py - Deep Research용 커스텀 MCP 서버
================================================

Phase 11: 추가 연구 도구를 제공하는 MCP 서버

제공 도구:
1. 텍스트 분석:
   - summarize_text: 긴 텍스트를 요약
   - extract_key_points: 텍스트에서 핵심 포인트 추출
   - count_words: 단어/문자 수 통계

2. 파일 시스템 접근:
   - read_file: 파일 내용 읽기
   - list_files: 디렉토리 파일 목록
   - save_research: 연구 결과 저장

3. 추가 검색:
   - search_wikipedia: 위키피디아 검색
"""

import os
from mcp.server.fastmcp import FastMCP

# MCP 서버 생성
mcp = FastMCP("deep-research-tools")

# ================================================================
# 1. 텍스트 분석 도구
# ================================================================

@mcp.tool()
def summarize_text(text: str, max_length: int = 200) -> str:
    """
    긴 텍스트를 간결하게 요약합니다.
    
    Args:
        text: 요약할 텍스트
        max_length: 최대 요약 길이 (기본값: 200자)
    
    Returns:
        요약된 텍스트
    """
    if len(text) <= max_length:
        return text
    
    # 간단한 요약: 첫 부분 + 마지막 부분
    half = max_length // 2
    return f"{text[:half]}... {text[-half:]}"


@mcp.tool()
def extract_key_points(text: str, num_points: int = 5) -> str:
    """
    텍스트에서 핵심 포인트를 추출합니다.
    
    Args:
        text: 분석할 텍스트
        num_points: 추출할 포인트 수 (기본값: 5)
    
    Returns:
        핵심 포인트 목록
    """
    # 문장 분리
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    
    # 상위 N개 문장 선택 (길이 기준)
    sorted_sentences = sorted(sentences, key=len, reverse=True)
    top_sentences = sorted_sentences[:num_points]
    
    result = "Key Points:\n"
    for i, sentence in enumerate(top_sentences, 1):
        result += f"  {i}. {sentence[:100]}...\n"
    
    return result


@mcp.tool()
def count_words(text: str) -> str:
    """
    텍스트의 단어 수를 세서 통계를 반환합니다.
    
    Args:
        text: 분석할 텍스트
    
    Returns:
        단어 수 및 문자 수 통계
    """
    words = text.split()
    chars = len(text)
    sentences = text.count('.') + text.count('!') + text.count('?')
    
    return f"Stats: {len(words)} words, {chars} chars, ~{sentences} sentences"


# ================================================================
# 2. 파일 시스템 접근 도구
# ================================================================

# 허용된 디렉토리 (보안을 위해 제한)
ALLOWED_DIRS = [
    os.path.expanduser("~/LangGraph_PJT"),
    "/tmp/deep_research"
]


@mcp.tool()
def read_file(file_path: str, max_chars: int = 5000) -> str:
    """
    파일의 내용을 읽어옵니다.
    
    Args:
        file_path: 읽을 파일 경로
        max_chars: 최대 읽을 문자 수 (기본값: 5000)
    
    Returns:
        파일 내용 또는 에러 메시지
    """
    try:
        # 보안: 허용된 디렉토리만 접근
        abs_path = os.path.abspath(os.path.expanduser(file_path))
        allowed = any(abs_path.startswith(d) for d in ALLOWED_DIRS)
        
        if not allowed:
            return f"Error: Access denied. Allowed directories: {ALLOWED_DIRS}"
        
        if not os.path.exists(abs_path):
            return f"Error: File not found: {file_path}"
        
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read(max_chars)
            
        if len(content) >= max_chars:
            content += f"\n... (truncated at {max_chars} chars)"
            
        return content
        
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def list_files(directory: str, extension: str = "") -> str:
    """
    디렉토리의 파일 목록을 반환합니다.
    
    Args:
        directory: 탐색할 디렉토리 경로
        extension: 필터링할 확장자 (예: ".md", ".py")
    
    Returns:
        파일 목록
    """
    try:
        abs_path = os.path.abspath(os.path.expanduser(directory))
        allowed = any(abs_path.startswith(d) for d in ALLOWED_DIRS)
        
        if not allowed:
            return f"Error: Access denied. Allowed directories: {ALLOWED_DIRS}"
        
        if not os.path.isdir(abs_path):
            return f"Error: Not a directory: {directory}"
        
        files = []
        for f in os.listdir(abs_path):
            if extension and not f.endswith(extension):
                continue
            full_path = os.path.join(abs_path, f)
            file_type = "DIR" if os.path.isdir(full_path) else "FILE"
            files.append(f"[{file_type}] {f}")
        
        return f"Files in {directory}:\n" + "\n".join(files[:50])
        
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@mcp.tool()
def save_research(filename: str, content: str) -> str:
    """
    연구 결과를 파일로 저장합니다.
    
    Args:
        filename: 저장할 파일 이름 (확장자 포함)
        content: 저장할 내용
    
    Returns:
        저장 결과 메시지
    """
    try:
        # 저장 디렉토리 생성
        save_dir = "/tmp/deep_research"
        os.makedirs(save_dir, exist_ok=True)
        
        # 파일 경로 (보안: 지정된 디렉토리에만 저장)
        safe_filename = os.path.basename(filename)  # 경로 주입 방지
        file_path = os.path.join(save_dir, safe_filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"✅ Saved to: {file_path} ({len(content)} chars)"
        
    except Exception as e:
        return f"Error saving file: {str(e)}"


# ================================================================
# 3. 추가 검색 도구
# ================================================================

@mcp.tool()
def search_wikipedia(query: str, sentences: int = 3) -> str:
    """
    위키피디아에서 정보를 검색합니다.
    
    Args:
        query: 검색할 키워드
        sentences: 반환할 문장 수 (기본값: 3)
    
    Returns:
        위키피디아 검색 결과 요약
    """
    try:
        import urllib.request
        import urllib.parse
        import json
        
        # Wikipedia API 호출
        encoded_query = urllib.parse.quote(query)
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_query}"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'DeepResearch/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        title = data.get('title', 'Unknown')
        extract = data.get('extract', 'No content found.')
        
        # 문장 수 제한
        sentences_list = extract.split('. ')[:sentences]
        limited_extract = '. '.join(sentences_list)
        if not limited_extract.endswith('.'):
            limited_extract += '.'
        
        return f"📚 Wikipedia: {title}\n\n{limited_extract}"
        
    except Exception as e:
        return f"Wikipedia search failed: {str(e)}"


if __name__ == "__main__":
    print("🚀 Starting Deep Research MCP Server...")
    print("📦 Available tools: summarize_text, extract_key_points, count_words")
    print("📁 File tools: read_file, list_files, save_research")
    print("🔍 Search tools: search_wikipedia")
    mcp.run(transport="stdio")
