
"""
LangGraph 03: Persistence (Memory)
===================================
이 예제는 LangGraph의 영속성(Persistence) 기능을 보여줍니다.

핵심 개념:
1. Checkpointer (체크포인터): 그래프의 각 단계마다 상태(State)를 저장하는 메커니즘
   - MemorySaver: 인메모리 저장 (테스트용, 재시작 시 사라짐)
   - SqliteSaver, PostgresSaver: DB 저장 (실제 운영용)
   
2. Thread ID (스레드 ID): 대화 세션을 구분하는 식별자
   - config={"configurable": {"thread_id": "..."}} 형태로 전달
   - 같은 thread_id를 사용하면 이전 대화 맥락이 유지됨

실행 흐름:
[Turn 1] User: "Hi, I'm Bob" --> [Graph 실행] --> [Checkpoint 저장]
    (시간 경과...)
[Turn 2] User: "What is my name?" --> [Checkpoint 로드] --> [Graph 실행: "Your name is Bob"]
"""

import os
import dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver
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
# 1. 상태(State) 정의
# =============================================================================
class State(TypedDict):
    """
    Persistence 예제에서는 이 상태가 Checkpointer에 저장됩니다.
    """
    messages: Annotated[list, add_messages]


# =============================================================================
# 2. 노드(Node) 정의
# =============================================================================
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


# =============================================================================
# 3. 그래프(Graph) 구축 (with Checkpointer)
# =============================================================================
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# !!! 중요: Persistence 설정 !!!
# MemorySaver는 메모리에 상태를 저장합니다. 프로그램이 종료되면 데이터는 날아갑니다.
# 실제 프로덕션에서는 SqliteSaver나 PostgresSaver를 사용하여 DB에 저장해야 합니다.
checkpointer = MemorySaver()

# compile 시 checkpointer를 전달하여 영속성 활성화
graph = graph_builder.compile(checkpointer=checkpointer)


# =============================================================================
# 4. 실행(Execution)
# =============================================================================
def main():
    print("Initializing Persistence Agent...\n")
    
    # 시각화
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        with open("persistence_graph.png", "wb") as f:
            f.write(png_bytes)
        print("Graph saved to 'persistence_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    # Thread ID 설정: 이 ID가 "세션"을 정의합니다.
    # 같은 thread_id를 사용하면 대화 맥락(State)이 이어집니다.
    config = {"configurable": {"thread_id": "thread-1"}}

    # -------------------------------------------------------------------------
    # Turn 1: 첫 인사
    # -------------------------------------------------------------------------
    input_1 = "Hi, I'm Bob."
    print(f"\n--- User (Turn 1): {input_1} ---")
    
    # 첫 실행: thread-1에 대한 기록이 없으므로 빈 상태에서 시작
    for event in graph.stream(
        {"messages": [HumanMessage(content=input_1)]},
        config=config, 
        stream_mode="values"
    ):
        last_msg = event["messages"][-1]
        print(f"[{last_msg.type}]: {last_msg.content}")

    print("\n... Simulating user returning later (사용자가 나중에 다시 옴) ...\n")
    
    # -------------------------------------------------------------------------
    # Turn 2: 기억 테스트
    # -------------------------------------------------------------------------
    # 사용자의 이전 발언("I'm Bob")을 기억하는지 확인
    input_2 = "What is my name?"
    print(f"--- User (Turn 2): {input_2} ---")
    
    # 중요: 이전 conversation history를 직접 넘겨주지 않습니다!
    # LangGraph가 'thread-1' ID를 보고 checkpointer에서 자동으로 상태를 로드합니다.
    for event in graph.stream(
        {"messages": [HumanMessage(content=input_2)]},
        config=config, # 동일한 thread_id 사용
        stream_mode="values"
    ):
        last_msg = event["messages"][-1]
        print(f"[{last_msg.type}]: {last_msg.content}")

    # -------------------------------------------------------------------------
    # 상태 확인 (Snapshot)
    # -------------------------------------------------------------------------
    print("\n--- Checkpoint State Snapshot ---")
    # 현재 시점의 thread-1 상태 조회
    snapshot = graph.get_state(config)
    print(f"Snapshot Created At: {snapshot.created_at}") # 마지막 저장 시간
    print(f"Snapshot Values (Messages Count): {len(snapshot.values['messages'])}")
    # 메시지 개수는 (User1, AI1, User2, AI2) = 4개가 되어야 함

if __name__ == "__main__":
    main()
