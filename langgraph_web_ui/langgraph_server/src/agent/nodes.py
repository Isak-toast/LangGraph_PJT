"""
nodes.py - Deep Research 노드 구현
===================================

5개 노드로 구성된 Deep Research 시스템:
1. Planner: 리서치 계획 수립
2. Searcher: 웹 검색 (Tavily)
3. ContentReader: URL 내용 읽기
4. Analyzer: 정보 분석 + 추가 검색 판단
5. Writer: 최종 응답 작성

그래프 구조:
  Planner → Searcher → ContentReader → Analyzer → Writer
                 ↑                          │
                 └──────────────────────────┘
                      (추가 검색 필요시)
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agent.state import DeepResearchState
from src.agent.tools import tavily_tool, read_url_tool


# ================================================================
# LLM 초기화
# ================================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    temperature=0.3
)


# ================================================================
# 1. Planner 노드 - 리서치 계획 수립
# ================================================================

PLANNER_PROMPT = """You are a RESEARCH PLANNER. Your job is to create a research strategy.

Analyze the user's question and create a research plan with:
1. Multiple search queries (in English for better results)
2. Focus areas to explore
3. Depth level (1=quick, 2=medium, 3=deep)

OUTPUT FORMAT (JSON):
{
    "search_queries": ["query1", "query2", "query3"],
    "focus_areas": ["area1", "area2"],
    "depth_level": 2
}

EXAMPLES:
- "LangGraph Vision AI papers" → queries: ["LangGraph Vision AI paper", "LangGraph computer vision", "LangGraph image processing agent"]
- "AI trends 2024" → queries: ["AI trends 2024", "machine learning trends 2024", "generative AI advances 2024"]

Create 2-4 diverse search queries to get comprehensive results.
"""

def planner_node(state: DeepResearchState) -> dict:
    """리서치 계획을 수립하는 Planner 노드"""
    
    messages = state["messages"]
    user_query = ""
    
    # 마지막 사용자 메시지 찾기
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or (hasattr(msg, 'type') and msg.type == 'human'):
            user_query = msg.content
            break
    
    print(f"📋 Planner: Creating research plan for: {user_query[:50]}...")
    
    # LLM에게 계획 생성 요청
    structured_llm = llm.with_structured_output({
        "type": "object",
        "properties": {
            "search_queries": {"type": "array", "items": {"type": "string"}},
            "focus_areas": {"type": "array", "items": {"type": "string"}},
            "depth_level": {"type": "integer", "minimum": 1, "maximum": 3}
        },
        "required": ["search_queries", "focus_areas", "depth_level"]
    })
    
    try:
        plan = structured_llm.invoke(f"{PLANNER_PROMPT}\n\nUser Question: {user_query}")
        print(f"📋 Planner: Generated {len(plan.get('search_queries', []))} queries")
    except Exception as e:
        print(f"❌ Planner error: {e}")
        plan = {
            "search_queries": [user_query],
            "focus_areas": ["general"],
            "depth_level": 2
        }
    
    return {
        "research_plan": plan,
        "current_query_index": 0,
        "research_iteration": 1,
        "search_results": [],
        "urls_to_read": [],
        "read_contents": [],
        "findings": []
    }


# ================================================================
# 2. Searcher 노드 - 웹 검색
# ================================================================

def searcher_node(state: DeepResearchState) -> dict:
    """Tavily 검색을 수행하는 Searcher 노드"""
    
    plan = state.get("research_plan", {})
    queries = plan.get("search_queries", [])
    current_idx = state.get("current_query_index", 0)
    iteration = state.get("research_iteration", 1)
    
    # 추가 검색 쿼리가 있으면 사용
    next_query = state.get("next_search_query")
    if next_query:
        query = next_query
        print(f"🔍 Searcher [{iteration}]: Follow-up search for: {query}")
    elif current_idx < len(queries):
        query = queries[current_idx]
        print(f"🔍 Searcher [{iteration}]: Searching for: {query}")
    else:
        return {"search_results": [], "urls_to_read": []}
    
    try:
        results = tavily_tool.invoke(query)
        urls = [r.get("url", "") for r in results if r.get("url")]
        
        print(f"🔍 Searcher: Found {len(results)} results, {len(urls)} URLs")
        
        return {
            "search_results": results,
            "urls_to_read": urls[:5],  # 상위 5개 URL
            "current_query_index": current_idx + 1,
            "next_search_query": None  # 사용 후 리셋
        }
    except Exception as e:
        print(f"❌ Searcher error: {e}")
        return {"search_results": [], "urls_to_read": []}


# ================================================================
# 3. ContentReader 노드 - URL 내용 읽기
# ================================================================

def content_reader_node(state: DeepResearchState) -> dict:
    """URL 내용을 읽는 ContentReader 노드"""
    
    urls = state.get("urls_to_read", [])
    existing_contents = state.get("read_contents", [])
    
    if not urls:
        print("📖 ContentReader: No URLs to read")
        return {"read_contents": existing_contents}
    
    print(f"📖 ContentReader: Reading {len(urls)} URLs...")
    
    new_contents = []
    for url in urls[:3]:  # 상위 3개만 읽기 (토큰 절약)
        try:
            content = read_url_tool.invoke(url)
            new_contents.append({
                "url": url,
                "content": content[:4000],  # 각 URL 4000자 제한
                "title": url.split("/")[-1]
            })
            print(f"  ✓ Read: {url[:60]}...")
        except Exception as e:
            print(f"  ✗ Failed: {url[:40]}... ({e})")
    
    # 기존 내용 + 새 내용
    all_contents = existing_contents + new_contents
    
    return {"read_contents": all_contents, "urls_to_read": []}


# ================================================================
# 4. Analyzer 노드 - 정보 분석 + 추가 검색 판단
# ================================================================

ANALYZER_PROMPT = """You are a RESEARCH ANALYZER. Analyze the collected information.

YOUR TASKS:
1. Extract key findings from the search results and read contents
2. Determine if the information is sufficient to answer the user's question
3. If more research is needed, suggest a specific search query

CONSIDER:
- Have we found specific papers/articles about the topic?
- Is the information detailed enough?
- Are there gaps in our knowledge?

OUTPUT FORMAT (JSON):
{
    "findings": ["finding1", "finding2", ...],
    "needs_more_research": true/false,
    "next_search_query": "specific query if more research needed"
}
"""

def analyzer_node(state: DeepResearchState) -> dict:
    """수집된 정보를 분석하는 Analyzer 노드"""
    
    search_results = state.get("search_results", [])
    read_contents = state.get("read_contents", [])
    iteration = state.get("research_iteration", 1)
    existing_findings = state.get("findings", [])
    
    print(f"🔬 Analyzer [{iteration}]: Analyzing {len(search_results)} results, {len(read_contents)} contents")
    
    # 분석할 내용 준비
    content_summary = ""
    for r in search_results[:5]:
        content_summary += f"- {r.get('content', '')[:500]}\n"
    for c in read_contents:
        content_summary += f"- [URL: {c.get('url', '')}] {c.get('content', '')[:800]}\n"
    
    # 사용자 질문 가져오기
    user_query = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break
    
    # LLM 분석
    structured_llm = llm.with_structured_output({
        "type": "object",
        "properties": {
            "findings": {"type": "array", "items": {"type": "string"}},
            "needs_more_research": {"type": "boolean"},
            "next_search_query": {"type": "string"}
        },
        "required": ["findings", "needs_more_research"]
    })
    
    try:
        prompt = f"""{ANALYZER_PROMPT}

User Question: {user_query}
Research Iteration: {iteration}/3

Collected Information:
{content_summary[:6000]}

Existing Findings: {existing_findings}
"""
        analysis = structured_llm.invoke(prompt)
        
        new_findings = existing_findings + analysis.get("findings", [])
        needs_more = analysis.get("needs_more_research", False)
        next_query = analysis.get("next_search_query", "")
        
        # 최대 3회 반복 제한
        if iteration >= 3:
            needs_more = False
            print("🔬 Analyzer: Max iterations reached, proceeding to Writer")
        
        if needs_more:
            print(f"🔬 Analyzer: More research needed - {next_query}")
        else:
            print(f"🔬 Analyzer: Research complete with {len(new_findings)} findings")
        
        return {
            "findings": new_findings,
            "needs_more_research": needs_more,
            "next_search_query": next_query if needs_more else None,
            "research_iteration": iteration + 1 if needs_more else iteration
        }
        
    except Exception as e:
        print(f"❌ Analyzer error: {e}")
        return {
            "findings": existing_findings,
            "needs_more_research": False,
            "next_search_query": None
        }


# ================================================================
# 5. Writer 노드 - 최종 응답 작성
# ================================================================

WRITER_PROMPT = """You are a PROFESSIONAL WRITER. Write the FINAL RESPONSE based on research.

INSTRUCTIONS:
1. Synthesize ALL findings into a comprehensive response
2. Write in Korean (한국어)
3. Use proper markdown formatting
4. Include analysis and insights
5. Reference key sources

STRUCTURE:
## 핵심 요약
(1-2 sentences overview)

## 주요 발견 사항
(Key findings from research)

## 상세 분석
(Detailed analysis with structure)

## 관련 자료 및 출처
(List of relevant sources)

## 결론 및 평가
(Conclusion and your assessment)

IMPORTANT:
- Write clear, professional Korean
- DO NOT just copy findings - synthesize and analyze
- Provide valuable insights
"""

def writer_node(state: DeepResearchState) -> dict:
    """최종 응답을 작성하는 Writer 노드"""
    
    findings = state.get("findings", [])
    read_contents = state.get("read_contents", [])
    search_results = state.get("search_results", [])
    
    print(f"✍️ Writer: Composing response from {len(findings)} findings")
    
    # 사용자 질문 가져오기
    user_query = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break
    
    # 소스 URL 목록
    source_urls = list(set([c.get("url", "") for c in read_contents if c.get("url")]))
    
    # 프롬프트 구성
    content_details = ""
    for c in read_contents[:5]:
        content_details += f"\n### Source: {c.get('url', '')}\n{c.get('content', '')[:1500]}\n"
    
    prompt = f"""{WRITER_PROMPT}

USER QUESTION: {user_query}

RESEARCH FINDINGS:
{chr(10).join(f'- {f}' for f in findings)}

DETAILED CONTENT FROM SOURCES:
{content_details}

SOURCE URLs:
{chr(10).join(f'- {url}' for url in source_urls)}

Now write the final response in Korean:
"""
    
    try:
        response = llm.invoke([SystemMessage(content=prompt)])
        content = response.content
        
        if not content or len(content.strip()) < 50:
            content = f"""## 검색 결과 요약

{chr(10).join(f'- {f}' for f in findings)}

### 출처
{chr(10).join(f'- {url}' for url in source_urls)}
"""
        
        print(f"✍️ Writer: Generated {len(content)} chars")
        
    except Exception as e:
        print(f"❌ Writer error: {e}")
        content = f"응답 생성 중 오류: {e}"
    
    return {
        "messages": [AIMessage(content=content, name="Writer")]
    }


# ================================================================
# 라우팅 함수
# ================================================================

def should_continue_research(state: DeepResearchState) -> str:
    """Analyzer 후 추가 검색 여부 판단"""
    if state.get("needs_more_research", False):
        return "continue"
    return "finish"


def route_after_planner(state: DeepResearchState) -> str:
    """Planner 후 Searcher로 이동"""
    return "Searcher"
