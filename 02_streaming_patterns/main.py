
"""
LangGraph 02: Streaming Patterns
=================================
이 예제는 LangGraph의 스트리밍 기능을 보여줍니다.

핵심 개념:
1. Stream Mode "values": 각 단계마다 전체 상태(State)를 반환
   - 용도: 채팅 히스토리 전체를 다시 렌더링해야 하는 UI
   
2. Stream Mode "updates": 각 노드가 실행된 후 변경된 상태만 반환
   - 용도: 진행 상황을 단계별로 보여주거나, 특정 노드의 완료를 감지할 때

3. Stream Mode "debug": (이 코드엔 없지만) 각 단계의 상세 디버그 정보 반환

실행 흐름:
[START] --> [chatbot] --> [slow_node] --> [END]
             (LLM)       (Simulated)
"""

import os
import dotenv
import time
from typing import Annotated
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from pathlib import Path

# 환경 변수 로드
# .env 파일을 스크립트 위치 기준 또는 프로젝트 루트에서 찾음
script_dir = Path(__file__).parent
project_root = script_dir.parent
env_file = project_root / ".env"
if not env_file.exists():
    env_file = script_dir / ".env"
dotenv.load_dotenv(env_file)

# LangSmith 추적 설정 (선택사항)
if os.getenv("LANGCHAIN_TRACING_V2") == "true":
    print("📊 LangSmith 추적이 활성화되었습니다.")
    print(f"   프로젝트: {os.getenv('LANGCHAIN_PROJECT', 'default')}")


# =============================================================================
# 1. 상태(State) 정의
# =============================================================================
class State(TypedDict):
    """
    그래프 상태 정의
    - messages: 대화 내역 (add_messages 리듀서 사용으로 자동 누적)
    """
    messages: Annotated[list, add_messages]


# =============================================================================
# 2. 노드(Node) 정의
# =============================================================================
# stream=True 옵션은 LLM 수준의 토큰 스트리밍을 위한 것이며,
# LangGraph의 stream()과는 별개입니다.
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, stream=True)

def chatbot(state: State):
    """
    사용자 메시지를 받아 LLM 응답을 생성하는 노드
    """
    print(f"   [chatbot 노드 실행 중] 입력 메시지 수: {len(state['messages'])}")
    return {"messages": [llm.invoke(state["messages"])]}

def slow_node(state: State):
    """
    처리가 오래 걸리는 작업을 시뮬레이션하는 노드
    - 스트리밍 중에 사용자에게 대기 시간을 체감하게 함
    """
    print("   [slow_node 실행 중] 데이터 처리 시뮬레이션 (1초 대기)...")
    time.sleep(1)
    return {"messages": [AIMessage(content="[System] 데이터 처리가 완료되었습니다.")]}


# =============================================================================
# 3. 그래프(Graph) 구축
# =============================================================================
graph_builder = StateGraph(State)

# 노드 등록
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("slow_process", slow_node)

# 엣지 연결 (순차 실행)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", "slow_process")
graph_builder.add_edge("slow_process", END)

# 컴파일
graph = graph_builder.compile()


# =============================================================================
# 4. 실행(Execution)
# =============================================================================
def main():
    # 그래프 시각화
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        with open("streaming_graph.png", "wb") as f:
            f.write(png_bytes)
        print("Graph saved to 'streaming_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    user_input = "Tell me a very short story about a robot."
    print(f"\n--- User Input: {user_input} ---\n")
    
    inputs = {"messages": [HumanMessage(content=user_input)]}

    # -------------------------------------------------------------------------
    # 모드 1: Stream Values (값 스트리밍)
    # -------------------------------------------------------------------------
    print("=== Mode 1: Stream Values (각 단계의 전체 상태 반환) ===")
    print("용도: 현재까지의 전체 대화 내역을 화면에 갱신할 때 유용\n")
    
    for event in graph.stream(inputs, stream_mode="values"):
        # event는 전체 State 딕셔너리입니다. {'messages': [msg1, msg2, ...]}
        last_msg = event["messages"][-1]
        print(f"👉 State Update: 마지막 메시지 ({last_msg.type}): {last_msg.content[:30]}...")

    print("\n" + "="*50 + "\n")

    # -------------------------------------------------------------------------
    # 모드 2: Stream Updates (업데이트 스트리밍)
    # -------------------------------------------------------------------------
    print("=== Mode 2: Stream Updates (각 노드의 출력만 반환) ===")
    print("용도: 어떤 노드가 방금 실행을 마쳤는지, 무엇을 변경했는지 확인할 때 유용\n")
    
    # 입력을 다시 초기화 (이전 실행 영향 없애기 위해)
    # 실제로는 Persistence를 쓰면 이어지지만, 여기서는 in-memory라 별도 실행으로 취급
    
    for event in graph.stream(inputs, stream_mode="updates"):
        # event는 방금 실행된 노드의 출력 딕셔너리입니다.
        # 예: {'chatbot': {'messages': [AIMessage(...)]}}
        for node_name, node_output in event.items():
            print(f"✅ Node '{node_name}' 완료.")
            new_msgs = node_output.get('messages', [])
            if new_msgs:
                print(f"   -> 생성된 메시지: {new_msgs[0].content[:40]}...")
            
    print("\n" + "="*50 + "\n")

    # -------------------------------------------------------------------------
    # 모드 3: Stream Tokens (LLM 토큰 스트리밍)
    # -------------------------------------------------------------------------
    print("=== Mode 3: Stream Tokens (LLM 토큰 단위) ===")
    print("용도: 타자기 효과처럼 글자가 하나씩 나오는 UX 구현\n")
    print("(이 예제에서는 노드 레벨 스트리밍만 다루므로 생략합니다.)")
    print("(토큰 스트리밍을 위해서는 astream_events API를 주로 사용합니다.)")

if __name__ == "__main__":
    main()
