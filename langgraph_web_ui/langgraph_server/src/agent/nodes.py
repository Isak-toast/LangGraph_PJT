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
from src.agent.tools import tavily_tool, read_url_tool, think_tool


# ================================================================
# LLM 및 설정 초기화 (Phase 6: Multi-LLM)
# ================================================================

from src.agent.config import research_config

# 역할별 LLM 인스턴스 생성
llm = research_config.get_llm("analyzer")  # 기본 LLM (분석용)
planner_llm = research_config.get_llm("planner")
writer_llm = research_config.get_llm("writer")
critic_llm = research_config.get_llm("critic")

# ================================================================
# 로깅 설정
# ================================================================

# 환경변수 또는 전역 설정으로 verbose 모드 제어
import os
VERBOSE_MODE = research_config.verbose_mode


def truncate_text(text: str, max_len: int = 200, force_full: bool = False) -> str:
    """텍스트 자르기 (verbose 모드면 전체 출력)
    
    Args:
        text: 원본 텍스트
        max_len: 최대 길이 (기본 200자)
        force_full: True면 무조건 전체 출력
    
    Returns:
        잘린 텍스트 (필요시에만 ... 추가)
    """
    if force_full or VERBOSE_MODE:
        return text
    
    if len(text) <= max_len:
        return text  # 짧으면 그대로 (... 없이)
    
    return text[:max_len] + "..."


# ================================================================
# 0. Clarify 노드 - 질문 분석 및 명확화 (Phase 3)
# ================================================================

CLARIFY_PROMPT = """You are a QUERY ANALYZER. Assess if the user's question needs clarification.

<Task>
Analyze the user query for:
1. Ambiguous terms or acronyms that might have multiple meanings
2. Missing context (time period, scope, specific technology)
3. Unclear intent (asking for comparison vs explanation vs tutorial)
</Task>

<Decision Criteria>
NEEDS_CLARIFICATION when:
- Contains acronyms without context (e.g., "RAG" could be Retrieval-Augmented Generation or other)
- Timeframe is unclear for trending topics
- Comparing items without specifying criteria
- Very broad topics without focus

CLEAR when:
- Query is specific and well-defined
- Context is sufficient for research
- Intent is obvious

Most queries are CLEAR. Only flag truly ambiguous ones.
</Decision Criteria>

<Output Format>
{
    "needs_clarification": boolean,
    "clarification_question": "question to ask user (if needed)" or null,
    "analysis": "brief analysis of the query",
    "detected_topics": ["topic1", "topic2"]
}
</Output Format>
"""

def clarify_node(state: DeepResearchState) -> dict:
    """질문을 분석하고 명확화 필요 여부를 판단하는 Clarify 노드"""
    
    messages = state.get("messages", [])
    user_query = ""
    for msg in messages:
        if isinstance(msg, HumanMessage) or (hasattr(msg, 'type') and msg.type == 'human'):
            user_query = msg.content
            break
    
    print(f"\n🔎 Clarify: Analyzing query...")
    print(f"   └─ Query: {truncate_text(user_query, 80)}")
    
    try:
        # LLM에게 질문 분석 요청
        structured_llm = llm.with_structured_output({
            "type": "object",
            "properties": {
                "needs_clarification": {"type": "boolean"},
                "clarification_question": {"type": "string"},
                "analysis": {"type": "string"},
                "detected_topics": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["needs_clarification", "analysis", "detected_topics"]
        })
        
        result = structured_llm.invoke([
            SystemMessage(content=CLARIFY_PROMPT),
            HumanMessage(content=f"Analyze this query: {user_query}")
        ])
        
        needs_clarification = result.get("needs_clarification", False)
        clarification_question = result.get("clarification_question")
        analysis = result.get("analysis", "")
        topics = result.get("detected_topics", [])
        
        # 로깅
        status = "🟡 Needs clarification" if needs_clarification else "🟢 Clear"
        print(f"   └─ Status: {status}")
        print(f"   └─ Analysis: {truncate_text(analysis, 150)}")
        print(f"   └─ Topics: {', '.join(topics[:5])}")
        
        if needs_clarification and clarification_question:
            print(f"   └─ Suggested question: {clarification_question}")
        
        return {
            "needs_clarification": needs_clarification,
            "clarification_question": clarification_question if needs_clarification else None,
            "query_analysis": analysis
        }
        
    except Exception as e:
        print(f"❌ Clarify error: {e}")
        # 에러 시 명확화 불필요로 처리
        return {
            "needs_clarification": False,
            "clarification_question": None,
            "query_analysis": f"Analysis failed: {e}"
        }


# ================================================================
# 1. Planner 노드 - 리서치 계획 수립
# ================================================================

PLANNER_PROMPT = """You are a RESEARCH PLANNER. Your job is to create a research strategy.

<Task>
Analyze the user's question and create a comprehensive research plan.
</Task>

<Requirements>
1. Create multiple search queries (in English for better results)
2. Identify focus areas to explore
3. Determine appropriate depth level (1=quick, 2=medium, 3=deep)
</Requirements>

<Output_Format>
{
    "search_queries": ["query1", "query2", "query3"],
    "focus_areas": ["area1", "area2"],
    "depth_level": 2
}

depth_level: 1=quick, 2=medium, 3=deep
</Output_Format>

<Examples>
- "LangGraph Vision AI papers" → queries: ["LangGraph Vision AI paper", "LangGraph computer vision", "LangGraph image processing agent"]
- "AI trends 2024" → queries: ["AI trends 2024", "machine learning trends 2024", "generative AI advances 2024"]
</Examples>

<Guidelines>
- Create 2-4 diverse search queries to get comprehensive results
- Use English for search queries for broader results
- Ensure queries cover different aspects of the topic
</Guidelines>
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
    
    print(f"📋 Planner: Creating research plan for: {user_query[:50]}")
    
    # LLM에게 계획 생성 요청 (Phase 6: planner_llm 사용)
    structured_llm = planner_llm.with_structured_output({
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
        queries = plan.get('search_queries', [])
        print(f"\n📋 Planner: Generated {len(queries)} queries")
        print("   └─ Queries:")
        for i, q in enumerate(queries, 1):
            print(f"      [{i}] {q}")
        if plan.get('focus_areas'):
            print(f"   └─ Focus: {', '.join(plan.get('focus_areas', []))}")
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
        
        print(f"\n🔍 Searcher: Found {len(results)} results")
        print("   └─ URLs found:")
        for i, url in enumerate(urls[:5], 1):
            print(f"      [{i}] {url}")
        print("   └─ Snippets:")
        for r in results[:3]:
            snippet = truncate_text(r.get('content', '').replace('\n', ' '), 200)
            print(f"      • {snippet}")
        
        # think_tool: 검색 후 전략적 분석
        snippets_summary = " | ".join([r.get('content', '')[:100] for r in results[:3]])
        think_result = think_tool.invoke(
            f"Query: {query} | Found {len(results)} results, {len(urls)} URLs. "
            f"Key snippets: {snippets_summary[:300]}. "
            f"Assessment: Is this sufficient or need more specific search?"
        )
        
        return {
            "search_results": results,
            "urls_to_read": urls[:5],
            "current_query_index": current_idx + 1,
            "next_search_query": None
        }
    except Exception as e:
        print(f"❌ Searcher error: {e}")
        return {"search_results": [], "urls_to_read": []}


# ================================================================
# 3. ContentReader 노드 - URL 내용 읽기
# ================================================================

def content_reader_node(state: DeepResearchState) -> dict:
    """본문 내용을 읽는 ContentReader 노드"""
    
    urls = state.get("urls_to_read", [])
    existing_contents = state.get("read_contents", [])
    
    if not urls:
        print("📖 ContentReader: No URLs to read")
        return {"read_contents": existing_contents}
    
    print(f"\n📖 ContentReader: Reading {len(urls[:3])} URLs")
    
    new_contents = []
    for url in urls[:3]:  # 상위 3개만 읽기 (토큰 절약)
        try:
            content = read_url_tool.invoke(url)
            new_contents.append({
                "url": url,
                "content": content[:4000],  # 각 URL 4000자 제한
                "title": url.split("/")[-1]
            })
            preview = truncate_text(content.replace('\n', ' '), 300)
            print(f"   └─ [{truncate_text(url, 60)}]")
            print(f"      Preview: {preview}")
        except Exception as e:
            print(f"   ✗ Failed: {truncate_text(url, 40)} ({e})")
    
    # 기존 내용 + 새 내용
    all_contents = existing_contents + new_contents
    
    return {"read_contents": all_contents, "urls_to_read": []}


# ================================================================
# 4. Analyzer 노드 - 정보 분석 + 추가 검색 판단
# ================================================================

ANALYZER_PROMPT = """You are a RESEARCH ANALYZER. Analyze the collected information.

<Task>
1. Extract key findings from the search results and read contents
2. Determine if the information is sufficient to answer the user's question
3. If more research is needed, suggest a specific search query
</Task>

<Show_Your_Thinking>
BEFORE making a decision, think strategically about:
- What key information did I find?
- What's still missing to fully answer the question?
- Is additional research worth the time cost?
- What specific query would fill the gaps?
</Show_Your_Thinking>

<Decision_Criteria>
STOP researching (needs_more_research=false) when:
- You have 3+ quality sources covering the main points
- You found specific data, examples, or expert opinions
- Additional searches would likely return duplicate information

CONTINUE researching (needs_more_research=true) when:
- Key aspects of the question are unanswered
- You only have 1-2 low-quality sources
- You're missing specific examples or data
</Decision_Criteria>

<Hard_Limits>
- Maximum 3 research iterations (enforced by system)
- Stop if you have enough information for a good answer
- Prefer quality over quantity
</Hard_Limits>

<Output_Format>
{
    "findings": ["finding1", "finding2", ...],
    "needs_more_research": true/false,
    "next_search_query": "specific query if more research needed"
}
</Output_Format>
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
            print("\n🔬 Analyzer: Max iterations reached, proceeding to Writer")
        
        # 상세 로그 출력
        print(f"\n🔬 Analyzer [{iteration}]: Analyzed {len(search_results)} results, {len(read_contents)} contents")
        if analysis.get("findings"):
            print("   └─ New findings:")
            for i, finding in enumerate(analysis.get("findings", [])[:5], 1):
                preview = truncate_text(finding.replace('\n', ' '), 150)
                print(f"      [{i}] {preview}")
        
        if needs_more:
            print(f"   └─ Decision: More research needed")
            print(f"   └─ Next query: {next_query}")
        else:
            print(f"   └─ Decision: Research complete ({len(new_findings)} total findings)")
        
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
# 5. Compress 노드 - 연구 결과 압축 (Phase 1)
# ================================================================

COMPRESS_PROMPT = """You are a RESEARCH COMPRESSOR. Your job is to clean up and compress research findings.

<Task>
Clean up information gathered from research. Remove duplicates, preserve key facts with citations.
All relevant information should be preserved but in a cleaner, more organized format.
</Task>

<Guidelines>
1. Remove duplicate or redundant information
2. Preserve ALL key facts, statistics, and insights
3. Group related findings together
4. Add inline citations [1], [2], etc. for each source
5. Include a Sources section at the end
</Guidelines>

<Output Format>
## Key Findings
- Finding 1 [1]
- Finding 2 [2]
- ...

## Detailed Information
(Organized, deduplicated content with citations)

## Sources
[1] URL or source name
[2] URL or source name
...
</Output Format>

<Citation Rules>
- Assign each unique URL a citation number [1], [2], [3]...
- Use citations inline after each fact
- List all sources at the end with corresponding numbers
- Number sources sequentially without gaps
</Citation Rules>
"""

def compress_node(state: DeepResearchState) -> dict:
    """연구 결과를 압축하고 정리하는 Compress 노드"""
    
    findings = state.get("findings", [])
    read_contents = state.get("read_contents", [])
    search_results = state.get("search_results", [])
    
    print(f"\n📦 Compress: Compressing {len(findings)} findings, {len(read_contents)} contents")
    
    # 소스 URL 수집
    source_urls = list(set([c.get("url", "") for c in read_contents if c.get("url")]))
    
    # 압축할 내용 준비
    content_to_compress = ""
    
    # Findings
    content_to_compress += "=== FINDINGS ===\n"
    for i, finding in enumerate(findings, 1):
        content_to_compress += f"[{i}] {finding}\n"
    
    # Read contents (일부)
    content_to_compress += "\n=== SOURCE CONTENTS ===\n"
    for c in read_contents[:5]:
        url = c.get("url", "Unknown")
        text = c.get("content", "")[:800]
        content_to_compress += f"\n[Source: {url}]\n{text}\n"
    
    # 소스 URL 목록
    content_to_compress += "\n=== SOURCE URLS ===\n"
    for i, url in enumerate(source_urls, 1):
        content_to_compress += f"[{i}] {url}\n"
    
    try:
        prompt = f"""{COMPRESS_PROMPT}

Here is the raw research data to compress:

{content_to_compress[:8000]}

Now compress and organize this information with proper citations:
"""
        response = llm.invoke([HumanMessage(content=prompt)])
        compressed = response.content
        
        # 상세 로그 출력
        print(f"   └─ Compressed to {len(compressed)} chars (from ~{len(content_to_compress)} raw chars)")
        print(f"   └─ Sources cited: {len(source_urls)}")
        preview = truncate_text(compressed, 400).replace('\n', '\n      ')
        print(f"   └─ Preview:\n      {preview}")
        
        return {"compressed_notes": compressed}
        
    except Exception as e:
        print(f"❌ Compress error: {e}")
        # 에러 시 원본 findings 반환
        fallback = "\n".join(f"- {f}" for f in findings)
        return {"compressed_notes": fallback}


# ================================================================
# 6. Writer 노드 - 최종 응답 작성
# ================================================================

WRITER_PROMPT = """You are a PROFESSIONAL WRITER. Write the FINAL RESPONSE based on research.

<Task>
Synthesize ALL research findings into a comprehensive, well-structured response.
</Task>

<Requirements>
1. Write in Korean (한국어)
2. Use proper markdown formatting
3. Include analysis and insights, not just copied findings
4. Reference key sources with inline citations
</Requirements>

<Output_Structure>
## 핵심 요약
(1-2 sentences overview of the main findings)

## 주요 발견 사항
(Key bullet points from research with citations [1], [2]...)

## 상세 분석
(Detailed analysis organized by topic or theme)

## 관련 자료 및 출처
(List of sources with URLs and references)

## 결론 및 평가
(Your synthesis, assessment, and recommendations)
</Output_Structure>

<Quality_Guidelines>
- Write clear, professional Korean
- DO NOT just copy findings - synthesize and analyze
- Provide valuable insights and actionable conclusions
- Ensure logical flow between sections
- Use proper citation format [1], [2]...
</Quality_Guidelines>
"""

def writer_node(state: DeepResearchState) -> dict:
    """최종 응답을 작성하는 Writer 노드"""
    
    findings = state.get("findings", [])
    read_contents = state.get("read_contents", [])
    search_results = state.get("search_results", [])
    compressed_notes = state.get("compressed_notes", "")  # Phase 1: 압축된 노트 사용
    
    print(f"\n✍️ Writer: Composing response from {len(findings)} findings")
    
    # 사용자 질문 가져오기
    user_query = ""
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage) or (hasattr(msg, 'type') and msg.type == 'human'):
            user_query = getattr(msg, 'content', str(msg))
            break
    
    # 소스 URL 목록
    source_urls = list(set([c.get("url", "") for c in read_contents if c.get("url")]))
    
    # Phase 1: compressed_notes가 있으면 사용, 없으면 기존 방식
    if compressed_notes:
        print(f"   └─ Using compressed notes ({len(compressed_notes)} chars)")
        research_content = compressed_notes
    else:
        # fallback: 원본 findings 사용
        research_content = "\n".join(f"- {f}" for f in findings) if findings else "No findings available"
        for c in read_contents[:3]:
            research_content += f"\n\n[Source: {c.get('url', '')}]\n{c.get('content', '')[:500]}"
    
    # URLs 문자열
    urls_str = "\n".join(f"- {url}" for url in source_urls) if source_urls else "- No source URLs"
    
    full_prompt = f"""{WRITER_PROMPT}

USER QUESTION: {user_query}

RESEARCH CONTENT (already organized with citations):
{research_content}

SOURCE URLs:
{urls_str}

Now write the final comprehensive response in Korean (한국어로 작성하세요).
IMPORTANT: Preserve and include the citations [1], [2], etc. from the research content.
"""
    
    try:
        # HumanMessage로 호출해야 Gemini가 제대로 응답함 (Phase 6: writer_llm 사용)
        response = writer_llm.invoke([HumanMessage(content=full_prompt)])
        content = response.content
        
        if not content or len(content.strip()) < 50:
            # fallback 응답 생성
            content = f"""## 검색 결과 요약

{findings_str}

### 출처
{urls_str}
"""
        
        # 상세 로그 출력
        print(f"\n✍️ Writer: Generated response ({len(content)} chars)")
        print("   └─ Sources used:")
        for i, url in enumerate(source_urls[:3], 1):
            print(f"      [{i}] {truncate_text(url, 60)}")
        print(f"   └─ Response preview:")
        preview = truncate_text(content, 500).replace('\n', '\n      ')
        print(f"      {preview}")
        
    except Exception as e:
        print(f"❌ Writer error: {e}")
        # 에러 시에도 의미 있는 내용 반환
        content = f"""## 검색 결과 요약

{findings_str}

### 참고 자료
{urls_str}

> 상세 응답 생성 중 오류가 발생했습니다. 위 정보를 참고해 주세요.
"""
    
    return {
        "messages": [AIMessage(content=content, name="Writer")]
    }


# ================================================================
# 7. Critique 노드 - CARC 다차원 품질 평가 (Phase 5 확장)
# ================================================================

CRITIQUE_PROMPT = """You are a RESPONSE QUALITY EVALUATOR using the CARC Framework.

<Task>
Evaluate the research response quality using 4 dimensions, each scored 1-5.
</Task>

<CARC_Framework>
1. **Completeness** (1-5): Did the response answer ALL parts of the question?
   - 5: Fully complete, addresses every aspect
   - 3: Partially complete, some aspects missing
   - 1: Incomplete, major parts unanswered

2. **Accuracy** (1-5): Are the cited facts and sources correct?
   - 5: All citations accurate and verifiable
   - 3: Some inaccuracies or questionable sources
   - 1: Major factual errors or fabricated citations

3. **Relevance** (1-5): Is the response directly relevant to the question?
   - 5: Highly relevant, stays on topic throughout
   - 3: Somewhat relevant, includes tangential info
   - 1: Off-topic or irrelevant content

4. **Clarity** (1-5): Is the response well-structured and easy to understand?
   - 5: Excellent structure, clear language
   - 3: Decent structure, some unclear parts
   - 1: Disorganized, hard to follow
</CARC_Framework>

<Output_Format>
{
    "completeness": 4,
    "accuracy": 5,
    "relevance": 4,
    "clarity": 5,
    "total": 18,
    "feedback": "Brief overall assessment",
    "improvement_suggestions": ["suggestion1", "suggestion2"]
}
</Output_Format>

<Decision>
- Total >= 16: Excellent quality ✅
- Total 12-15: Good quality, minor improvements possible
- Total < 12: Needs significant improvement ⚠️
</Decision>
"""

def critique_node(state: DeepResearchState) -> dict:
    """CARC 프레임워크로 응답 품질을 다차원 평가하는 Critique 노드"""
    
    # 마지막 Writer 응답 찾기
    messages = state.get("messages", [])
    writer_response = ""
    for msg in reversed(messages):
        if hasattr(msg, 'name') and msg.name == "Writer":
            writer_response = msg.content
            break
    
    if not writer_response:
        print("🔍 Critique: No Writer response found, skipping...")
        return {
            "quality_completeness": None,
            "quality_accuracy": None,
            "quality_relevance": None,
            "quality_clarity": None,
            "quality_total": None,
            "critique_feedback": None,
            "needs_improvement": False
        }
    
    # 원본 질문 찾기
    user_query = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            user_query = msg.content
            break
    
    print(f"\n🔍 Critique: CARC Quality Evaluation...")
    
    try:
        # 평가 요청
        evaluation_request = f"""
Original Question: {user_query}

Response to Evaluate:
{writer_response[:3000]}...

Please evaluate this response using the CARC Framework.
"""
        
        # JSON 출력을 위한 구조화된 응답 요청
        from pydantic import BaseModel
        from typing import List
        
        class CARCResult(BaseModel):
            completeness: int
            accuracy: int
            relevance: int
            clarity: int
            total: int
            feedback: str
            improvement_suggestions: List[str]
        
        # Phase 6: critic_llm 사용
        structured_critic = critic_llm.with_structured_output(CARCResult)
        
        result = structured_critic.invoke([
            SystemMessage(content=CRITIQUE_PROMPT),
            HumanMessage(content=evaluation_request)
        ])
        
        # 결과 계산 및 로깅
        c, a, r, cl = result.completeness, result.accuracy, result.relevance, result.clarity
        total = c + a + r + cl
        
        # 품질 등급 결정
        if total >= 16:
            grade = "✅ Excellent"
        elif total >= 12:
            grade = "👍 Good"
        else:
            grade = "⚠️ Needs work"
        
        needs_improvement = total < 14
        
        print(f"   └─ CARC Scores: C={c} A={a} R={r} C={cl}")
        print(f"   └─ Total: {total}/20 {grade}")
        print(f"   └─ Feedback: {truncate_text(result.feedback, 150)}")
        
        return {
            "quality_completeness": c,
            "quality_accuracy": a,
            "quality_relevance": r,
            "quality_clarity": cl,
            "quality_total": total,
            "critique_feedback": result.feedback,
            "needs_improvement": needs_improvement
        }
        
    except Exception as e:
        print(f"❌ Critique error: {e}")
        return {
            "quality_completeness": None,
            "quality_accuracy": None,
            "quality_relevance": None,
            "quality_clarity": None,
            "quality_total": None,
            "critique_feedback": str(e),
            "needs_improvement": False
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
