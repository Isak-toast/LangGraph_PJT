
"""
LangGraph: LATS (Language Agent Tree Search)
=============================================
이 예제는 LATS(Language Agent Tree Search)의 핵심 아이디어를 보여주기 위한
간소화된 데모입니다. (실제 트리를 탐색하는 복잡한 로직 대신, 'Best-of-N' 방식에 가깝습니다)

핵심 개념:
1. Expansion (확장): 하나의 상태에서 여러 가지 해결책(후보)을 생성합니다.
   - LLM Temperature를 높여서 다양한 시도를 유도합니다.

2. Scoring (평가): 생성된 후보들의 점수를 매깁니다.
   - LLM이 자신의 생성물을 스스로 평가(Self-Correction/Reflection)하게 섭니다.

3. Selection (선택): 가장 점수가 높은 후보를 선택하여 다음 단계로 나아갑니다.

구조 (Best-of-N Pipeline):
[Expand] --(N개 후보)--> [Score] --(점수)--> [Select] --> [END]
"""

import os
import dotenv
from typing import Annotated, List, Dict, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
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
# 1. 설정 및 상태 (Config & State)
# =============================================================================
# LATS는 확장을 위해 다양성이 필요하므로 Temperature를 높게 설정합니다.
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=1.0)

class LatsState(BaseModel):
    """LATS 그래프 상태"""
    # 해결해야 할 문제
    input: str
    # 현재까지 찾은 최고의 해결책
    final_answer: str = None
    # 현재 단계(깊이)에서 생성된 후보들
    candidates: List[str] = []
    # 후보들에 대한 점수
    scores: List[float] = []
    # 탐색 깊이 (이 예제에선 크게 활용 안됨)
    height: int = 0


# =============================================================================
# 2. 노드 (Nodes)
# =============================================================================

def expand_node(state: LatsState):
    """
    [확장] N개의 후보 해결책을 생성합니다.
    (실제 LATS는 '다음 단계'를 생성하지만, 여기서는 '전체 해결책'을 N번 시도합니다)
    """
    print(f"---[Expand] 후보 생성 중 (Height: {state.height})---")
    
    n = 3 # 생성할 후보 개수
    candidates = []
    for i in range(n):
        res = llm.invoke(f"Solve this problem: {state.input}. Provide a short candidate solution attempt. Current attempt number {i+1}")
        candidates.append(res.content)
    
    return {"candidates": candidates}

def score_node(state: LatsState):
    """
    [평가] 생성된 후보들에 점수(0.0 ~ 1.0)를 매깁니다.
    """
    print("---[Score] 후보 평가 중---")
    candidates = state.candidates
    scores = []
    
    # LLM에게 채점을 요청
    for cand in candidates:
        prompt = f"""Rate the correctness of the following solution to the problem: '{state.input}'.
        Solution: {cand}
        Provide ONLY a float number between 0.0 and 1.0."""
        res = llm.invoke(prompt)
        try:
            score = float(res.content.strip())
        except:
            score = 0.5 # 파싱 실패 시 기본값
        scores.append(score)
        print(f"   > Score: {score}")
        
    return {"scores": scores}

def select_node(state: LatsState):
    """
    [선택] 가장 높은 점수를 받은 후보를 선택합니다.
    """
    print("---[Select] 최고 후보 선택 중---")
    
    # 최고점 찾기
    best_idx = state.scores.index(max(state.scores))
    best_score = state.scores[best_idx]
    best_candidate = state.candidates[best_idx]
    
    print(f"   >>> Best Score: {best_score}")
    
    # (선택적 로직) 점수가 일정 수준 이상이어야 채택하거나, 아니면 재시도하는 로직을 추가할 수 있음
    # 여기서는 무조건 베스트를 선택하고 종료
    return {"final_answer": best_candidate}


# =============================================================================
# 3. 그래프 (Graph)
# =============================================================================
workflow = StateGraph(LatsState)

workflow.add_node("expand", expand_node)
workflow.add_node("score", score_node)
workflow.add_node("select", select_node)

workflow.add_edge(START, "expand")
workflow.add_edge("expand", "score")
workflow.add_edge("score", "select")
workflow.add_edge("select", END) 

app = workflow.compile()


# =============================================================================
# 4. 실행 (Execution)
# =============================================================================
def main():
    print("Initializing LATS (Best-of-N Demo)...")
    try:
        with open("lats_graph.png", "wb") as f:
            f.write(app.get_graph().draw_mermaid_png())
        print("Graph saved to 'lats_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    # 검증이 필요한 수학 문제
    problem = "What is 24 * 56 + 18?"
    inputs = {"input": problem}
    print(f"\n--- User Problem: {problem} ---\n")
    
    result = app.invoke(inputs)
    
    print("\n--- Final Best Solution ---")
    print(result["final_answer"])

if __name__ == "__main__":
    main()
