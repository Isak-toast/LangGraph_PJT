
import os
import dotenv
from typing import Annotated, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage

# Load env vars
dotenv.load_dotenv()

# --- Shared Resources ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# ==========================================
# 1. Define Subgraph (The "Research Team")
# ==========================================

class ResearchState(TypedDict):
    # Subgraph has its own isolated state schema if needed
    # (Here we reuse messages for simplicity)
    messages: Annotated[list, add_messages]
    research_summary: str

def basic_search(state: ResearchState):
    # Simulate search
    return {"messages": [AIMessage(content="[SearchBot] Found info about LangGraph.")]}

def summarizer(state: ResearchState):
    # Simulate summarizing
    return {"research_summary": "LangGraph is a library for building stateful, multi-actor applications with LLMs."}

research_builder = StateGraph(ResearchState)
research_builder.add_node("search", basic_search)
research_builder.add_node("summarize", summarizer)

research_builder.add_edge(START, "search")
research_builder.add_edge("search", "summarize")
research_builder.add_edge("summarize", END)

# Compile the subgraph
research_graph = research_builder.compile()


# ==========================================
# 2. Define Parent Graph (The "Company")
# ==========================================

class CorporateState(TypedDict):
    messages: Annotated[list, add_messages]
    final_report: str

def manager(state: CorporateState):
    return {"messages": [AIMessage(content="[Manager] I will assign this to the research team.")]}

# To use a compiled graph as a node, we wrap it in a function or use it directly if state matches.
# Since states differ slightly (ResearchState vs CorporateState), we need a wrapper to map inputs/outputs.
def call_research_team(state: CorporateState):
    # input map
    subgraph_input = {"messages": state["messages"]}
    
    # invoke subgraph
    result = research_graph.invoke(subgraph_input)
    
    # output map
    return {
        "messages": [AIMessage(content=f"[Manager] Team finished. Summary: {result['research_summary']}")],
        "final_report": result['research_summary']
    }

builder = StateGraph(CorporateState)
builder.add_node("manager", manager)
builder.add_node("research_team", call_research_team)

builder.add_edge(START, "manager")
builder.add_edge("manager", "research_team")
builder.add_edge("research_team", END)

graph = builder.compile()

# ==========================================
# 3. Execution
# ==========================================
def main():
    print("Initializing Hierarchical Agent...\n")
    try:
        with open("hierarchical_graph.png", "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        print("Graph saved to 'hierarchical_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")
    
    user_input = "Learn about LangGraph."
    print(f"--- User Request: {user_input} ---")
    
    events = graph.stream(
        {"messages": [HumanMessage(content=user_input)]},
        stream_mode="values"
    )
    
    for event in events:
        if "messages" in event:
            last_msg = event["messages"][-1]
            print(f"[{last_msg.type}]: {last_msg.content}")

if __name__ == "__main__":
    main()
