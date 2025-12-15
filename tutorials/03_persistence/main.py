
import os
import dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

# Load env vars
dotenv.load_dotenv()

# --- Define State ---
class State(TypedDict):
    messages: Annotated[list, add_messages]

# --- Define Nodes ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

# --- Build Graph ---
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)

# !!! ADD PERSISTENCE !!!
# SQLite, Postgres, etc. can be used. MemorySaver is in-memory for testing.
checkpointer = MemorySaver()

# Compile with checkpointer
graph = graph_builder.compile(checkpointer=checkpointer)

# --- Execution ---
def main():
    print("Initializing Persistence Agent...\n")
    try:
        with open("persistence_graph.png", "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        print("Graph saved to 'persistence_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    # Thread ID defines the "session"
    config = {"configurable": {"thread_id": "thread-1"}}

    # Turn 1
    input_1 = "Hi, I'm Bob."
    print(f"--- User (Turn 1): {input_1} ---")
    
    for event in graph.stream(
        {"messages": [HumanMessage(content=input_1)]},
        config=config, 
        stream_mode="values"
    ):
        last_msg = event["messages"][-1]
        print(f"[{last_msg.type}]: {last_msg.content}")

    print("\n... Simulating user returning later ...\n")
    
    # Turn 2 (Same Thread ID)
    input_2 = "What is my name?"
    print(f"--- User (Turn 2): {input_2} ---")
    
    # We do NOT pass the previous history manually. 
    # LangGraph fetches it from the checkpointer using 'thread-1'.
    for event in graph.stream(
        {"messages": [HumanMessage(content=input_2)]},
        config=config, 
        stream_mode="values"
    ):
        last_msg = event["messages"][-1]
        # We expect a content roughly like "Your name is Bob."
        print(f"[{last_msg.type}]: {last_msg.content}")

    print("\n--- Checkpoint State Snapshot ---")
    snapshot = graph.get_state(config)
    print(f"Snapshot Created At: {snapshot.created_at}")
    print(f"Snapshot Values (Messages Count): {len(snapshot.values['messages'])}")

if __name__ == "__main__":
    main()
