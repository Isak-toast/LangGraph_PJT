import os
import dotenv
from typing import Annotated
from typing_extensions import TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage, HumanMessage
from langchain_core.tools import tool

# Load env vars
dotenv.load_dotenv()

# --- 1. Define Tools ---
@tool
def add(a: int, b: int) -> int:
    """Adds a and b."""
    return a + b

@tool
def multiply(a: int, b: int) -> int:
    """Multiplies a and b."""
    return a * b

@tool
def divide(a: int, b: int) -> float:
    """Divides a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return a / b

tools = [add, multiply, divide]
tools_by_name = {t.name: t for t in tools}

# --- 2. Define State ---
class State(TypedDict):
    # 'add_messages' handles appending messages to the list
    messages: Annotated[list, add_messages]

# --- 3. Define Nodes ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

def tool_node(state: State):
    outputs = []
    # inspect the last message (AIMessage) for tool calls
    last_message = state["messages"][-1]
    
    for tool_call in last_message.tool_calls:
        try:
            tool_result = tools_by_name[tool_call["name"]].invoke(tool_call)
            outputs.append(
                ToolMessage(
                    content=str(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        except Exception as e:
            outputs.append(
                ToolMessage(
                    content=f"Error: {e}",
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
            
    return {"messages": outputs}

# --- 4. Define Routing ---
def should_continue(state: State):
    last_message = state["messages"][-1]
    # If there are tool calls, go to 'tools', otherwise END
    if last_message.tool_calls:
        return "tools"
    return END

# --- 5. Build Graph ---
graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", should_continue, ["tools", END])
graph_builder.add_edge("tools", "chatbot") # Loop back to chatbot after tools

graph = graph_builder.compile()

# --- 6. Execution ---
def main():
    print("Initializing Calculator Agent...")
    
    # Visualization
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        with open("calculator_graph.png", "wb") as f:
            f.write(png_bytes)
        print("Graph saved to 'calculator_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    user_input = "Calculate (50 * 25) + 100"
    print(f"\n--- User Query: {user_input} ---")
    
    events = graph.stream(
        {"messages": [HumanMessage(content=user_input)]},
        stream_mode="values"
    )
    
    for event in events:
        last_msg = event["messages"][-1]
        print(f"[{last_msg.type}]: {last_msg.content}")

if __name__ == "__main__":
    main()
