
import os
import dotenv
from typing import Annotated, List, Literal, TypedDict, Union
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_community.tools.tavily_search import TavilySearchResults

# Load env vars
dotenv.load_dotenv()

# --- Configs ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# --- Tools ---

# 1. Handoff Tools
# These tools are special: they don't do 'work', they just signal a state change in the graph.
# In a robust implementation, these would return a structured object that the router interprets.

def transfer_to_writer():
    """Transfer control to the Writer agent."""
    return "Transferred to Writer"

def transfer_to_researcher():
    """Transfer control to the Researcher agent."""
    return "Transferred to Researcher"

# Agent Definitions

# We will use prebuilt agents but we need to give them the handoff tools.

# Researcher
search_tool = TavilySearchResults(k=2)

def researcher_node(state):
    # This is a custom node wrapper around the agent to handle the handoff logic if we werent using prebuilt.
    # But to show "Network", let's define the graph explicitly with nodes that call LLMs + Tools.
    pass

# Let's use a simpler approach: 
# Each node is an agent. The agent has tools. 
# One tool is "call_other_agent".

# Define the tools available to each agent
researcher_tools = [search_tool, transfer_to_writer]
writer_tools = [transfer_to_researcher] 

# Bind tools to LLM
researcher_model = llm.bind_tools(researcher_tools)
writer_model = llm.bind_tools(writer_tools)

# Instructions
detailed_researcher_prompt = """You are a Researcher. 
1. Search for information requested by the user. 
2. If you have found enough info, transfer to the Writer to draft the response.
3. If you need the Writer to explain something or format it, transfer to them."""

detailed_writer_prompt = """You are a Writer. 
1. Write a high-quality response based on the research provided.
2. If you need more information, transfer back to the Researcher.
3. If you are done, just output the final answer."""

# State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    # We track the 'active' sender to know who sent the last message, though strictly not needed if disjoint
    sender: str 

# Nodes
def get_last_message(state: AgentState) -> BaseMessage:
    return state["messages"][-1]

def researcher(state: AgentState):
    print("---Researcher---")
    res = researcher_model.invoke([SystemMessage(content=detailed_researcher_prompt)] + state["messages"])
    return {"messages": [res], "sender": "researcher"}

def writer(state: AgentState):
    print("---Writer---")
    res = writer_model.invoke([SystemMessage(content=detailed_writer_prompt)] + state["messages"])
    return {"messages": [res], "sender": "writer"}

# Tool Node (Shared)
# We need a tool node that can handle the actual search tool.
# The handoff tools don't really need to "run" if we catch them in conditional edges, 
# but for simplicity let's rely on the tool calls appearing in the message.

from langgraph.prebuilt import ToolNode
tool_node = ToolNode([search_tool])

# Logic for routing
def router(state: AgentState) -> Literal["call_tool", "enter_writer", "enter_researcher", "__end__"]:
    # This is the conditional edge function
    messages = state["messages"]
    last_message = messages[-1]
    
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        # Check what tool is called
        tool_name = last_message.tool_calls[0]["name"]
        
        if tool_name == "transfer_to_writer":
            return "enter_writer"
        elif tool_name == "transfer_to_researcher":
            return "enter_researcher"
        else:
            return "call_tool" # It's a real tool like search
            
    return "__end__" # No tool calls = final answer

# Graph
workflow = StateGraph(AgentState)

workflow.add_node("researcher", researcher)
workflow.add_node("writer", writer)
workflow.add_node("tools", tool_node)

# Start with researcher
workflow.add_edge(START, "researcher")

# Researcher outputs
workflow.add_conditional_edges(
    "researcher",
    router,
    {
        "enter_writer": "writer",
        "enter_researcher": "researcher", # Should not happen typically but for completeness
        "call_tool": "tools",
        "__end__": END
    }
)

# Writer outputs
workflow.add_conditional_edges(
    "writer",
    router,
    {
        "enter_writer": "writer",
        "enter_researcher": "researcher",
        "call_tool": "tools", # Writer has no real tools, but if transfer is a tool call it's handled above
        "__end__": END
    }
)

# Tool outputs -> return to sender?
# This is tricky in a mesh. We need to know who called the tool.
# For simplicity in this demo, Researcher is the main tool user.
workflow.add_edge("tools", "researcher")

app = workflow.compile()

def main():
    print("Initializing Multi-Agent Network (Mesh)...")
    try:
        with open("network_graph.png", "wb") as f:
            f.write(app.get_graph().draw_mermaid_png())
        print("Graph saved to 'network_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    events = app.stream(
        {"messages": [HumanMessage(content="Find a short summary of the philosophy of Stoicism and write a haiku about it.")]},
        {"recursion_limit": 20}
    )
    
    for event in events:
        for k, v in event.items():
            if "messages" in v:
                last_msg = v["messages"][-1]
                # print(f"[{k}]: {last_msg.content} (Tool Calls: {len(last_msg.tool_calls) if hasattr(last_msg, 'tool_calls') else 0})")

    print("\n--- Final Message ---")
    # Due to the loops, just verifying functionality via logs mostly.
    
if __name__ == "__main__":
    main()
