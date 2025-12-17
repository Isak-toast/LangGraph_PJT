"""
LangGraph Basic: Single Agent (ReAct)
======================================
이 예제는 LangGraph에서 가장 기본적인 단일 에이전트(Single Agent)를 만드는 방법을 보여줍니다.
`create_react_agent`라는 미리 만들어진(prebuilt) 함수를 사용하면, 복잡한 그래프 정의 없이도
ReAct(Reasoning + Acting) 에이전트를 쉽게 생성할 수 있습니다.

핵심 개념:
1. create_react_agent: 
   - LLM과 Tool을 입력받아 자동으로 [LLM] <-> [Tool] 순환 그래프를 생성합니다.
   - 내부적으로 MessageState를 사용하며, Tool Calling을 처리하는 노드가 포함되어 있습니다.

2. ReAct 패턴:
   - 질문 -> 생각(LLM) -> 도구 선택 -> 도구 실행 -> 결과 관찰 -> 최종 답변
"""

import os
import dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
from pathlib import Path

# 환경 변수 로드
script_dir = Path(__file__).parent
project_root = script_dir.parent
env_file = project_root / ".env"
if not env_file.exists():
    env_file = script_dir / ".env"
dotenv.load_dotenv(env_file)

# LangSmith 추적 설정
if os.getenv("LANGCHAIN_TRACING_V2") == "true":
    print("📊 LangSmith 추적이 활성화되었습니다.")
    print(f"   프로젝트: {os.getenv('LANGCHAIN_PROJECT', 'default')}")


# =============================================================================
# 실행 (Execution)
# =============================================================================
def main():
    print("Initializing Single Agent (ReAct) System...")
    
    # 1. LLM 설정
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    
    # 2. 도구(Tools) 설정
    # Tavily Search: 웹 검색 도구 (최대 3개 결과)
    tavily_tool = TavilySearchResults(max_results=3)
    tools = [tavily_tool]

    # 3. 에이전트 생성 (LangGraph Prebuilt)
    # create_react_agent는 내부적으로 다음 구조의 그래프를 만듭니다:
    # [START] -> [model] --(tool_calls)--> [tools]
    #               ^________(result)________|
    agent = create_react_agent(
        llm, 
        tools, 
        state_modifier="You are a helpful AI assistant. Use tools to find up-to-date information."
        # state_modifier는 시스템 프롬프트 역할을 합니다.
    )

    # 4. 시각화 (Optional)
    try:
        png_bytes = agent.get_graph().draw_mermaid_png()
        with open("agent_graph.png", "wb") as f:
            f.write(png_bytes)
        print("Graph visualization saved to 'agent_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    # 5. 실행
    user_input = "Who won the World Series in 2024? If not played yet, who won in 2023?"
    print(f"\n--- User Query ---\n{user_input}\n")
    
    messages = [HumanMessage(content=user_input)]
    
    print("--- Streaming Execution ---")
    
    # stream_mode="values": 각 단계의 전체 메시지 리스트를 반환
    for step in agent.stream({"messages": messages}, stream_mode="values"):
        # 현재 상태의 메시지 목록
        current_messages = step["messages"]
        last_message = current_messages[-1]
        
        # 메시지 타입과 내용 출력
        msg_type = last_message.type
        content = last_message.content
        
        print(f"\n[{msg_type.upper()}]: {content}")
        
        # 도구 호출 정보가 있다면 출력
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            for tc in last_message.tool_calls:
                 print(f"  └─ 🔧 Tool Call: {tc['name']}({tc['args']})")

if __name__ == "__main__":
    main()
