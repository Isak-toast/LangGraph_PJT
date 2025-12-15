
import os
import dotenv
from typing import Annotated, List, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# Load env vars
dotenv.load_dotenv()

class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

def generation_node(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

def reflection_node(state: State):
    # Reflection: Check the last message and provide critique
    last_msg = state["messages"][-1]
    
    # We ask the LLM to act as a critic
    reflection_prompt = f"You are a strict critic. Critique the following text for style and accuracy. Provide constructive feedback to improve it.\n\nText:\n{last_msg.content}"
    
    critique = llm.invoke(reflection_prompt)
    
    # We return the critique as a message, but we might want to flag it as such.
    # For this simple loop, we just append it.
    # Ideally, we format it so the next generation step knows it's feedback.
    return {"messages": [HumanMessage(content=f"[Critique]: {critique.content}")]}

def should_continue(state: State):
    # Simple loop limit based on message count
    if len(state["messages"]) > 6: # 3 iterations (Gen + Crit) * 3
        return END
    return "reflect"

graph_builder = StateGraph(State)

graph_builder.add_node("generate", generation_node)
graph_builder.add_node("reflect", reflection_node)

graph_builder.add_edge(START, "generate")
graph_builder.add_conditional_edges("generate", should_continue, ["reflect", END])
graph_builder.add_edge("reflect", "generate")

graph = graph_builder.compile()

def main():
    print("Initializing Reflection Agent...")
    try:
        with open("reflection_graph.png", "wb") as f:
            f.write(graph.get_graph().draw_mermaid_png())
        print("Graph saved to 'reflection_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")
    initial_input = "Write a very short poem about coding bugs."
    print(f"--- User Input: {initial_input} ---")
    
    inputs = {"messages": [HumanMessage(content=initial_input)]}
    
    for event in graph.stream(inputs, stream_mode="values"):
        last_msg = event["messages"][-1]
        print(f"\n[{last_msg.type.upper()}]:\n{last_msg.content}")

if __name__ == "__main__":
    main()
