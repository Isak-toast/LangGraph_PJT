
import os
import dotenv
import time
from typing import Annotated
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage

# Load env vars
dotenv.load_dotenv()

# --- Define State ---
class State(TypedDict):
    messages: Annotated[list, add_messages]

# --- Define Nodes ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0, stream=True)

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

def slow_node(state: State):
    """A node that simulated work to demonstrate streaming updates."""
    time.sleep(1)
    return {"messages": [AIMessage(content="[System] Processed data slowly...")]}

# --- Build Graph ---
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("slow_process", slow_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", "slow_process")
graph_builder.add_edge("slow_process", END)

graph = graph_builder.compile()

# --- Execution ---
def main():
    try:
        with open("streaming_graph.png", "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        print("Graph saved to 'streaming_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    user_input = "Tell me a very short story about a robot."
    print(f"--- User Input: {user_input} ---\n")
    
    inputs = {"messages": [HumanMessage(content=user_input)]}

    print("=== Mode 1: Stream Values (Complete State at each step) ===")
    print("Use case: UI rendering of the entire chat history.")
    for event in graph.stream(inputs, stream_mode="values"):
        # Returns the entire state {'messages': [...]}
        last_msg = event["messages"][-1]
        print(f"State Update: Last message from {last_msg.type}: {last_msg.content[:30]}...")

    print("\n=== Mode 2: Stream Updates (Node Outputs) ===")
    print("Use case: Seeing distinct steps/actions as they complete.")
    for event in graph.stream(inputs, stream_mode="updates"):
        # Returns correct node output {'chatbot': {'messages': [...]}}
        for node_name, node_output in event.items():
            print(f"Node '{node_name}' finished. Added {len(node_output['messages'])} message(s).")
            
    print("\n=== Mode 3: Stream Tokens (LLM Tokens) ===")
    print("Use case: Real-time typing effect.")
    
    # Note: To stream LLM tokens, we often use .astream_events or specific callback handlers.
    # LangGraph's .stream() generally steps through nodes. 
    # For token streaming inside a node, the node itself must stream chunks.
    
    print("(Not implemented in this simple block-level example, usually requires astream_events API)")

if __name__ == "__main__":
    main()
