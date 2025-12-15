
import os
import dotenv
from typing import Annotated, List, Dict, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field

# Load env vars
dotenv.load_dotenv()

# --- Configs ---
# LATS benefits from higher temperature for diversity in expansion
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=1.0)

# --- State ---
class LatsState(BaseModel):
    # The root problem
    input: str
    # The current best solution found so far
    final_answer: str = None
    # Current candidates at this depth
    candidates: List[str] = []
    # Feedbacks/scores for candidates
    scores: List[float] = []
    # Depth
    height: int = 0

# --- Nodes ---

def expand_node(state: LatsState):
    """Generates N candidate steps/solutions."""
    # Simplified expansion: just generate 3 distinct next steps/solutions
    print(f"---EXPAND (Height: {state.height})---")
    
    # In a real LATS, this would be "next step". Here we simulate "solution attempts".
    n = 3
    candidates = []
    for _ in range(n):
        res = llm.invoke(f"Solve this problem: {state.input}. Provide a short candidate solution attempt. Current attempt number {_}")
        candidates.append(res.content)
    
    return {"candidates": candidates}

def score_node(state: LatsState):
    """Scores the generated candidates."""
    print("---SCORE---")
    candidates = state.candidates
    scores = []
    
    # We ask the LLM to score 0-1
    for cand in candidates:
        prompt = f"""Rate the correctness of the following solution to the problem: '{state.input}'.
        Solution: {cand}
        Provide ONLY a float number between 0.0 and 1.0."""
        res = llm.invoke(prompt)
        try:
            score = float(res.content.strip())
        except:
            score = 0.5
        scores.append(score)
        
    return {"scores": scores}

def select_node(state: LatsState):
    """Selects the best candidate."""
    print("---SELECT---")
    # Identify best score
    best_idx = state.scores.index(max(state.scores))
    best_score = state.scores[best_idx]
    best_candidate = state.candidates[best_idx]
    
    print(f"Best Score: {best_score}")
    
    # If the score is high enough (e.g., > 0.9), we accept it.
    if best_score > 0.9:
        return {"final_answer": best_candidate}
    
    # If not, and depth < limit, we might retry or just keep the best one for now.
    # PROPER LATS would Backtrack here. 
    # For this simplified tutorial, we will loop to Expand again (Monte Calro simulation style) 
    # but maybe modify input to "Refine this solution".
    
    # Let's simple keep the best as final for now if max depth reached.
    return {"final_answer": best_candidate} # Pass through for conditional check

# --- Graph ---
workflow = StateGraph(LatsState)

workflow.add_node("expand", expand_node)
workflow.add_node("score", score_node)
workflow.add_node("select", select_node)

workflow.add_edge(START, "expand")
workflow.add_edge("expand", "score")
workflow.add_edge("score", "select")

def should_terminate(state: LatsState):
    if state.final_answer and max(state.scores) > 0.9:
        return END
    if state.height > 2: # Max depth 3
        return END
    return "expand" # In full LATS, this would be more complex with Tree Node navigation

# For this demo, since we don't update 'input' or 'height' properly to refine, 
# let's just make it a linear Generate N -> Score -> Pick Best pipeline 
# (which is Best-of-N, a component of LATS/ToT).
workflow.add_edge("select", END) 

app = workflow.compile()

def main():
    print("Initializing LATS (Best-of-N via Tree Search components)...")
    try:
        with open("lats_graph.png", "wb") as f:
            f.write(app.get_graph().draw_mermaid_png())
        print("Graph saved to 'lats_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    # A math problem that might benefit from checking
    inputs = {"input": "What is 24 * 56 + 18?"}
    
    result = app.invoke(inputs)
    print("\n--- Final Best Solution ---")
    print(result["final_answer"])

if __name__ == "__main__":
    main()
