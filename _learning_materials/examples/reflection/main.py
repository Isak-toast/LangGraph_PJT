
"""
LangGraph: Reflection (성찰)
==============================
이 예제는 Reflection 에이전트 패턴을 보여줍니다.
에이전트가 결과를 생성하고, 그 결과를 스스로(혹은 별도의 노드가) 비평(Critique)한 뒤,
비평을 바탕으로 결과를 개선하는 과정을 반복합니다.

구조 (Loop):
[Generate] -> [Reflect/Critique] -> [should_continue?] --(Yes)--> [Generate] (개선)
                                            |
                                          (No)
                                            ↓
                                          [END]
"""

import os
import dotenv
from typing import Annotated, List, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
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
# 1. 설정 및 상태
# =============================================================================
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)


# =============================================================================
# 2. 노드 (Nodes)
# =============================================================================

def generation_node(state: State):
    """
    [생성] 사용자 요청 또는 비평을 반영하여 텍스트를 생성/수정합니다.
    """
    print("---[Generate] 텍스트 생성 중---")
    # messages 리스트에 이전 대화(비평 포함)가 쌓이므로, LLM은 문맥을 알 수 있습니다.
    return {"messages": [llm.invoke(state["messages"])]}

def reflection_node(state: State):
    """
    [성찰] 이전 생성물을 비평(Critique)합니다.
    """
    print("---[Reflect] 비평(Critique) 생성 중---")
    last_msg = state["messages"][-1]
    
    # LLM에게 비평가(Critic) 페르소나 부여
    reflection_prompt = f"You are a strict critic. Critique the following text for style and accuracy. Provide constructive feedback to improve it.\n\nText:\n{last_msg.content}"
    
    critique = llm.invoke(reflection_prompt)
    
    # 비평 내용을 HumanMessage로 변환하여 Generator가 유저 피드백처럼 느끼게 함 (또는 System prompt 활용 가능)
    # 여기서는 간단히 [Critique] 접두어를 붙여 전달
    return {"messages": [HumanMessage(content=f"[Critique]: {critique.content}")]}

def should_continue(state: State):
    """
    루프를 계속할지 결정합니다. (여기서는 횟수 제한 사용)
    """
    # 메시지 개수로 반복 횟수 제어 (예: 6개 초과 시 종료)
    # (Initial User Msg + Gen + Ref + Gen + Ref + Gen + Ref ...)
    if len(state["messages"]) > 6: 
        print("---반복 횟수 초과, 종료---")
        return END
    return "reflect"


# =============================================================================
# 3. 그래프 (Graph)
# =============================================================================
graph_builder = StateGraph(State)

graph_builder.add_node("generate", generation_node)
graph_builder.add_node("reflect", reflection_node)

graph_builder.add_edge(START, "generate")
# Generate 후에는 루프 조건을 확인 (계속 비평할지, 끝낼지)
graph_builder.add_conditional_edges("generate", should_continue, ["reflect", END])
# Reflect 후에는 다시 Generate로 돌아가서 개선
graph_builder.add_edge("reflect", "generate")

graph = graph_builder.compile()


# =============================================================================
# 4. 실행 (Execution)
# =============================================================================
def main():
    print("Initializing Reflection Agent...")
    try:
        with open("reflection_graph.png", "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        print("Graph saved to 'reflection_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")
        
    initial_input = "Write a very short poem about coding bugs."
    print(f"--- User Input: {initial_input} ---")
    
    inputs = {"messages": [HumanMessage(content=initial_input)]}
    
    # stream_mode="values"로 각 단계의 메시지 변화를 관찰
    for event in graph.stream(inputs, stream_mode="values"):
        last_msg = event["messages"][-1]
        print(f"\n[{last_msg.type.upper()}]:\n{last_msg.content}")

if __name__ == "__main__":
    main()
