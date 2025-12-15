
import os
import dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.tools import tool

# Load env vars
dotenv.load_dotenv()

# --- Tools ---
@tool
def sensitive_action(data: str) -> str:
    """A tool that requires approval."""
    return f"ACTION EXECUTED: Processed '{data}'"

tools = [sensitive_action]
tools_by_name = {t.name: t for t in tools}

# --- State ---
class State(TypedDict):
    messages: Annotated[list, add_messages]

# --- Nodes ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

def tool_node(state: State):
    outputs = []
    last_message = state["messages"][-1]
    
    for tool_call in last_message.tool_calls:
        tool_result = tools_by_name[tool_call["name"]].invoke(tool_call)
        outputs.append(
            ToolMessage(
                content=str(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"],
            )
        )
            
    return {"messages": outputs}

def should_continue(state: State):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return END

# --- Graph ---
graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", should_continue, ["tools", END])
graph_builder.add_edge("tools", "chatbot")

# !!! HUMAN-IN-THE-LOOP !!!
# We want to interrupt BEFORE the 'tools' node executes
checkpointer = MemorySaver()
graph = graph_builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["tools"] 
)

# --- Execution ---
def main():
    print("Initializing Human-in-the-loop Agent...")
    try:
        with open("human_loop_graph.png", "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        print("Graph saved to 'human_loop_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")
    config = {"configurable": {"thread_id": "thread-2"}}

    # 1. User request
    user_input = "Please execute the sensitive action with data 'Secret123'."
    print(f"\n--- [Step 1] User Request: {user_input} ---")
    
    # We run the graph until it hits the interruption point
    for event in graph.stream(
        {"messages": [HumanMessage(content=user_input)]},
        config=config, 
        stream_mode="values"
    ):
        last_msg = event["messages"][-1]
        print(f"[{last_msg.type}] {last_msg.content}")
        
    # Check status
    snapshot = graph.get_state(config)
    print(f"\n--- [Step 2] Graph Status: {snapshot.next} ---")
    if "tools" in snapshot.next:
        print(">> Graph paused before 'tools'. Waiting for approval...")
    
    # 2. Approve and Continue
    approval = input("\nDo you approve this action? (y/n): ")
    if approval.lower() == "y":
        print(">> Action Approved. Resuming graph...")
        # Passing None as input (or minimal update) resumes execution
        for event in graph.stream(None, config=config, stream_mode="values"):
            last_msg = event["messages"][-1]
            print(f"[{last_msg.type}] {last_msg.content}")
    else:
        print(">> Action Denied.")

if __name__ == "__main__":
    main()
