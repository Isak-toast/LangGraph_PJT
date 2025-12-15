
import os
import dotenv
from typing import Annotated, List, TypedDict
import operator
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

# Load env vars
dotenv.load_dotenv()

# --- Data Models ---
class Plan(BaseModel):
    """Plan to follow."""
    steps: List[str] = Field(description="different steps to follow, should be in sorted order")

class Response(BaseModel):
    """Response to user."""
    response: str
    
class PlanExecuteState(TypedDict):
    input: str
    plan: List[str]
    past_steps: Annotated[List[tuple], operator.add]
    response: str

# --- LLM ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# --- Nodes ---

def planner(state: PlanExecuteState):
    """Generates the initial plan."""
    print("--- [Planner] Generating Plan ---")
    planner_llm = llm.with_structured_output(Plan)
    plan = planner_llm.invoke(f"For the given objective, come up with a simple step by step plan. \nObjective: {state['input']}")
    return {"plan": plan.steps}

def executor(state: PlanExecuteState):
    """Executes the first step of the plan."""
    plan = state["plan"]
    step_to_execute = plan[0]
    print(f"--- [Executor] Executing Step: {step_to_execute} ---")
    
    # Simulate execution (in reality, this would call tools)
    # We just ask the LLM to 'perform' the step by simulating knowledge
    task_llm = llm
    result = task_llm.invoke(f"Execute this task: {step_to_execute}. Provide a concise result.")
    
    return {
        "past_steps": [(step_to_execute, result.content)],
        "plan": plan[1:] # Remove executed step
    }

def replanner(state: PlanExecuteState):
    """Decides whether to continue or finish."""
    # If no steps left, we are done
    if not state["plan"]:
        # Generate final response
        print("--- [Replanner] Finished! Generating final response ---")
        final_response = llm.invoke(f"Generate a final response to the original input based on these steps: {state['past_steps']}\nOriginal Input: {state['input']}")
        return {"response": final_response.content}
    
    # Otherwise, loop back to executor
    # (Real implementation might update the plan here based on new info)
    print(f"--- [Replanner] {len(state['plan'])} steps remaining... ---")
    return {} # State update handled by edges mostly

def should_end(state: PlanExecuteState):
    if state.get("response"):
        return END
    return "executor"

# --- Graph ---
workflow = StateGraph(PlanExecuteState)

workflow.add_node("planner", planner)
workflow.add_node("executor", executor)
workflow.add_node("replanner", replanner)

workflow.add_edge(START, "planner")
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "replanner")
workflow.add_conditional_edges("replanner", should_end, ["executor", END])

app = workflow.compile()

# --- Execution ---
def main():
    print("Initializing Plan-and-Execute Agent...")
    try:
        with open("plan_execute_graph.png", "wb") as f:
            f.write(app.get_graph().draw_mermaid_png())
        print("Graph saved to 'plan_execute_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")
    user_input = "Write a haiku about Python and then explain it."
    
    config = {"recursion_limit": 50}
    inputs = {"input": user_input}
    
    for event in app.stream(inputs, config=config):
        for k, v in event.items():
            if v and k == "replanner" and "response" in v:
                print(f"\n[Final Response]:\n{v['response']}")

if __name__ == "__main__":
    main()
