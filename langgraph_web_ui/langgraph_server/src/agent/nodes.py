"""
nodes.py - 노드 구현
======================

이 파일은 그래프의 각 노드(Node)를 구현합니다.
노드는 그래프에서 실행되는 함수 단위입니다.

노드 구조:
┌─────────────┐
│  Supervisor │ ← 라우터 역할 (어디로 보낼지 결정)
└─────────────┘
      │
      ├──────────────┬───────────────┐
      ▼              ▼               │
┌──────────┐   ┌──────────┐          │
│Researcher│   │  Writer  │ ─────────┘
└──────────┘   └──────────┘
    │              │
 웹 검색        글 작성
"""

from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from src.agent.state import AgentState
from src.agent.tools import tavily_tool


# ================================================================
# LLM 초기화 (모든 노드가 공유)
# ================================================================
# 
# Gemini 2.0 Flash 모델 사용
# temperature=0: 일관된 응답을 위해 랜덤성 제거

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0  # 결정론적 응답 (매번 같은 입력에 같은 출력)
)


# ================================================================
# Worker 에이전트 목록
# ================================================================
# 
# Supervisor가 라우팅할 수 있는 대상들
# FINISH는 종료를 의미 (END 노드로 이동)

members = ["Researcher", "Writer"]  # 워커 노드 이름들
options = ["FINISH"] + members       # Supervisor의 선택지: FINISH, Researcher, Writer


# ================================================================
# Researcher 에이전트 (ReAct 패턴)
# ================================================================
# 
# ReAct = Reasoning + Acting
# LLM이 "생각 → 행동 → 관찰" 사이클을 반복하며 도구를 사용
#
# 예시 실행 흐름:
#   1. 생각: "AI 트렌드를 검색해야겠다"
#   2. 행동: tavily_tool.invoke("2024 AI trends")
#   3. 관찰: 검색 결과 확인
#   4. 생각: "충분한 정보를 얻었다"
#   5. 최종 응답 생성

# Researcher 시스템 프롬프트 - 반드시 검색하도록 강제!
RESEARCHER_PROMPT = """You are a professional researcher agent.

YOUR TASK:
1. ALWAYS use the tavily_search tool to find information
2. NEVER ask for clarification - just search for what the user asked
3. Search in English for better results, then respond in Korean
4. Provide comprehensive, factual information from search results

IMPORTANT: You MUST use the search tool. Do NOT respond without searching first.
절대로 검색 없이 응답하지 마세요. 반드시 tavily_search 도구를 사용하세요.
"""

# ReAct 에이전트 생성 (도구만 주입, 프롬프트는 노드에서 추가)
research_agent = create_react_agent(
    llm, 
    tools=[tavily_tool]  # Researcher는 Tavily 검색 도구 사용 가능
)


def research_node(state: AgentState) -> dict:
    """
    Researcher 노드 - 웹에서 정보를 검색하고 수집
    
    이 노드는 사용자의 질문에 답하기 위해 필요한 정보를
    Tavily 검색 API를 통해 웹에서 수집합니다.
    
    Args:
        state: 현재 그래프 상태 (messages 포함)
    
    Returns:
        상태 업데이트 딕셔너리 {"messages": [...]}
        → 검색 결과가 담긴 AIMessage가 messages에 추가됨
    """
    from langchain_core.messages import SystemMessage
    
    # 시스템 메시지를 맨 앞에 추가하여 검색 강제
    messages_with_prompt = [
        SystemMessage(content=RESEARCHER_PROMPT)
    ] + list(state["messages"])
    
    # 수정된 상태로 에이전트 실행
    modified_state = {"messages": messages_with_prompt}
    result = research_agent.invoke(modified_state)
    
    # 마지막 메시지 추출 (에이전트의 최종 응답)
    last_msg = result["messages"][-1]
    
    # 상태 업데이트: Researcher가 응답했음을 표시
    return {
        "messages": [AIMessage(
            content=last_msg.content,
            name="Researcher"  # 누가 응답했는지 표시 (추적용)
        )]
    }


# ================================================================
# Writer 노드 (단순 LLM 호출)
# ================================================================

def writer_node(state: AgentState) -> dict:
    """
    Writer 노드 - 수집된 정보를 기반으로 글 작성
    
    이 노드는 도구 없이 순수하게 LLM의 글쓰기 능력만 사용합니다.
    주로 요약, 보고서 작성, 정리 등의 작업을 수행합니다.
    
    Args:
        state: 현재 그래프 상태 (messages 포함)
    
    Returns:
        상태 업데이트 딕셔너리 {"messages": [...]}
        → 작성된 글이 담긴 AIMessage가 messages에 추가됨
    """
    # 대화 히스토리를 기반으로 LLM이 응답 생성
    response = llm.invoke(state["messages"])
    
    return {
        "messages": [AIMessage(
            content=response.content,
            name="Writer"  # 누가 응답했는지 표시
        )]
    }


# ================================================================
# Supervisor 노드 (라우터/오케스트레이터)
# ================================================================

def supervisor_node(state: AgentState) -> dict:
    """
    Supervisor 노드 - 다음에 실행할 노드를 결정하는 라우터
    
    Supervisor는 대화 상황을 분석하고 어떤 Worker를 호출할지,
    아니면 작업을 종료할지를 결정합니다.
    
    결정 로직:
        1. 정보 검색이 필요하면 → "Researcher"
        2. 글 작성이 필요하면 → "Writer"
        3. 작업 완료 또는 Worker가 이미 응답했으면 → "FINISH"
    
    Args:
        state: 현재 그래프 상태
    
    Returns:
        {"next": "Researcher" | "Writer" | "FINISH"}
    
    무한 루프 방지:
        Worker가 이미 응답한 경우 강제로 FINISH로 라우팅하여
        재귀 제한(recursion limit) 에러를 방지합니다.
    """
    messages = state["messages"]
    
    # ========================================
    # 무한 루프 방지 체크 (개선됨)
    # ========================================
    # "마지막 Human 메시지 이후에" Worker가 응답했는지 확인
    # 전체 히스토리가 아닌 현재 턴만 체크해야 함!
    
    worker_responded_this_turn = False
    last_human_idx = -1
    
    # 마지막 Human 메시지 위치 찾기
    for i, msg in enumerate(messages):
        if hasattr(msg, 'type') and msg.type == 'human':
            last_human_idx = i
        elif isinstance(msg, HumanMessage):
            last_human_idx = i
    
    # 마지막 Human 메시지 이후의 Worker 응답 확인
    if last_human_idx >= 0:
        for msg in messages[last_human_idx + 1:]:
            if hasattr(msg, 'name') and msg.name in members:
                worker_responded_this_turn = True
                break
    
    # ========================================
    # Supervisor 프롬프트 (LLM 지시)
    # ========================================
    # LLM에게 명확한 규칙을 제시하여 올바른 결정을 유도
    
    supervisor_prompt = f"""You are a supervisor managing workers: {members}.

RULES (규칙):
1. If the user asks a QUESTION that needs research -> route to "Researcher"
   (사용자가 검색이 필요한 질문을 하면 Researcher로)
2. If you need content written/summarized -> route to "Writer"
   (글 작성이나 요약이 필요하면 Writer로)
3. If a worker has ALREADY responded with useful information -> route to "FINISH"
   (Worker가 이미 응답했으면 FINISH로)
4. If the conversation is complete or no action needed -> route to "FINISH"
   (대화가 완료되었거나 할 일이 없으면 FINISH로)
5. NEVER route to the same worker twice in a row
   (같은 Worker를 연속으로 두 번 호출하지 마세요)

Worker already responded this turn: {worker_responded_this_turn}
(현재 턴에서 Worker가 이미 응답했나요: {worker_responded_this_turn})

Respond with ONLY the next action: {options}"""

    # ========================================
    # 구조화된 출력 (Structured Output)
    # ========================================
    # LLM이 반드시 정해진 형식으로 응답하도록 강제
    # 자유 텍스트가 아닌 {"next": "..."} 형태로만 응답
    
    structured_llm = llm.with_structured_output({
        "type": "object", 
        "properties": {
            "next": {
                "type": "string", 
                "enum": options  # FINISH, Researcher, Writer 중 하나만 가능
            }
        }, 
        "required": ["next"]
    })
    
    # 최근 5개 메시지만 사용 (토큰 절약)
    prompt = f"{supervisor_prompt}\n\nConversation:\n{messages[-5:]}"
    
    try:
        response = structured_llm.invoke(prompt)
        next_agent = response.get("next")
    except Exception as e:
        # 에러 발생 시 안전하게 종료
        print(f"Supervisor error: {e}")
        next_agent = "FINISH"
    
    # ========================================
    # 안전 장치: 강제 FINISH
    # ========================================
    # Worker가 이미 응답했는데 또 Worker를 호출하려 하면 강제 종료
    
    if worker_responded_this_turn and next_agent in members:
        print("⚠️ Forcing FINISH: worker already responded this turn")
        next_agent = "FINISH"
    
    # 유효하지 않은 응답 처리
    if not next_agent or next_agent not in options:
        next_agent = "FINISH"
        
    return {"next": next_agent}
