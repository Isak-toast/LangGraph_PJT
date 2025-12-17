"""
LangGraph Multi-Agent: Supervisor Pattern
==========================================
이 예제는 Supervisor(감독자)가 여러 에이전트를 관리하는 패턴을 보여줍니다.
여러 전문 에이전트(Researcher, Chart Generator 등)가 있고, Supervisor가 
다음 작업을 누구에게 맡길지 결정합니다.

핵심 개념:
1. Supervisor: 상태를 보고 다음에 실행할 에이전트를 결정하는 LLM 노드
   - Structured Output 등을 사용하여 명확한 라우팅 결정을 내립니다.

2. Workers: 실제 작업을 수행하는 에이전트 노드들
   - 각자 맡은 일을 하고 결과를 Supervisor에게 보고(반환)합니다.

구조:
          [Supervisor]
         /      |     \
   [Research] [Chart]  [Coder] ...
         \      |     /
          ------|-----
             (Loop)
"""

import dotenv
from langchain_core.messages import HumanMessage
from src.graph import create_graph # 그래프 정의는 src/graph.py에 분리되어 있음
from pathlib import Path
import os

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


def main():
    print("Initializing Multi-Agent Supervisor System...")
    
    # 그래프 생성 (src/graph.py의 로직 사용)
    graph = create_graph()
    
    # 시각화
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        with open("graph_diagram.png", "wb") as f:
            f.write(png_bytes)
        print("Graph visualization saved to 'graph_diagram.png'")
    except Exception as e:
        print(f"Skipping visualization (optional dependency missing?): {e}")

    print("\n--- Standard Query ---")
    user_input = "Research the GDP of South Korea over the last 5 years and plot a line chart."
    print(f"User: {user_input}\n")

    initial_state = {"messages": [HumanMessage(content=user_input)]}

    # 실행 스트리밍
    for step in graph.stream(initial_state):
        if "__end__" not in step:
            # 각 노드 실행 결과 출력
            for key, value in step.items():
                print(f"--- Node: {key} ---")
                
                # 메시지가 있으면 내용 출력
                if "messages" in value:
                    print(value["messages"][-1].content)
                
                # Supervisor가 다음 단계를 결정했을 경우
                elif "next" in value:
                    print(f"👨‍✈️ Supervisor 결정: {value['next']}로 이동")
                
                print("---------------------")

if __name__ == "__main__":
    main()
