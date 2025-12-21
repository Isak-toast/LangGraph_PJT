
"""
LangGraph: Plan-and-Execute (계획 및 실행)
===========================================
이 예제는 복잡한 작업을 처리하기 위해 "계획(Plan)"과 "실행(Execute)" 단계를 분리하는 패턴입니다.
ReAct 에이전트와 달리, 먼저 전체 계획을 세우고 하나씩 실행하며, 필요 시 재계획(Replan)을 수행합니다.

핵심 흐름:
[Planner] -> [Executor] -> [Replanner] --(미완료)--> [Executor]
                             |
                           (완료)
                             ↓
                           [END]

구성 요소:
1. Planner: 사용자 입력을 분석하여 단계별 계획(steps)을 생성합니다.
2. Executor: 계획의 첫 번째 단계를 실행합니다. (이 예제에선 실행 시뮬레이션)
3. Replanner: 실행 결과를 보고, 남은 계획을 수정하거나 종료를 결정합니다.
"""

import os
import dotenv
from typing import Annotated, List, TypedDict
import operator
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
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
# 1. 데이터 모델 (Data Models)
# =============================================================================
class Plan(BaseModel):
    """실행할 계획"""
    steps: List[str] = Field(description="실행할 단계들의 목록 (순서대로)")

class Response(BaseModel):
    """최종 답변"""
    response: str
    
class PlanExecuteState(TypedDict):
    """그래프 상태"""
    input: str
    plan: List[str] # 남은 단계들
    past_steps: Annotated[List[tuple], operator.add] # (실행한 단계, 결과)의 리스트
    response: str # 최종 결과


# =============================================================================
# 2. 노드 (Nodes)
# =============================================================================
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

def planner(state: PlanExecuteState):
    """
    [Planner] 초기 계획을 생성합니다.
    """
    print("--- [Planner] 초기 계획 수립 중 ---")
    planner_llm = llm.with_structured_output(Plan)
    plan = planner_llm.invoke(f"For the given objective, come up with a simple step by step plan. \nObjective: {state['input']}")
    return {"plan": plan.steps}

def executor(state: PlanExecuteState):
    """
    [Executor] 계획의 첫 번째 단계를 실행합니다.
    """
    plan = state["plan"]
    step_to_execute = plan[0] # 첫 번째 단계
    print(f"--- [Executor] 단계 실행: {step_to_execute} ---")
    
    # 실제 환경에서는 여기서 도구(Tool)를 호출합니다.
    # 여기서는 LLM에게 실행 결과를 시뮬레이션하도록 요청합니다.
    task_llm = llm
    result = task_llm.invoke(f"Execute this task: {step_to_execute}. Provide a concise result.")
    
    return {
        "past_steps": [(step_to_execute, result.content)], # 실행 기록 추가
        "plan": plan[1:] # 실행한 단계 제거
    }

def replanner(state: PlanExecuteState):
    """
    [Replanner] 재계획 또는 종료를 결정합니다.
    """
    # 남은 단계가 없으면 종료
    if not state["plan"]:
        print("--- [Replanner] 모든 단계 완료! 최종 답변 생성 중 ---")
        final_response = llm.invoke(f"Generate a final response to the original input based on these steps: {state['past_steps']}\nOriginal Input: {state['input']}")
        return {"response": final_response.content}
    
    # 남은 단계가 있으면 계속 진행 (여기서 계획을 수정하는 로직을 추가할 수도 있음)
    print(f"--- [Replanner] {len(state['plan'])}개 단계 남음... 계속 진행 ---")
    return {} # 상태 업데이트는 conditional edge에서 루프 제어용

def should_end(state: PlanExecuteState):
    """
    종료 조건: response가 생성되었으면 종료, 아니면 계속 실행
    """
    if state.get("response"):
        return END
    return "executor"


# =============================================================================
# 3. 그래프 (Graph)
# =============================================================================
workflow = StateGraph(PlanExecuteState)

workflow.add_node("planner", planner)
workflow.add_node("executor", executor)
workflow.add_node("replanner", replanner)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "replanner")
workflow.add_conditional_edges("replanner", should_end, ["executor", END])

app = workflow.compile()


# =============================================================================
# 4. 실행 (Execution)
# =============================================================================
def main():
    print("Initializing Plan-and-Execute Agent...")
    try:
        with open("plan_execute_graph.png", "wb") as f:
            f.write(app.get_graph().draw_mermaid_png())
        print("Graph saved to 'plan_execute_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")
        
    user_input = "Write a haiku about Python and then explain it."
    print(f"\n--- User Request: {user_input} ---")
    
    config = {"recursion_limit": 50}
    inputs = {"input": user_input}
    
    # 실행
    for event in app.stream(inputs, config=config):
        for k, v in event.items():
            # replanner가 최종 응답을 냈을 때만 출력
            if v and k == "replanner" and "response" in v:
                print(f"\n[Final Response]:\n{v['response']}")

if __name__ == "__main__":
    main()
