import os
import dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# Load env vars from root or current dir
dotenv.load_dotenv()

def main():
    print("Initializing Single Agent (ReAct) System...")
    
    # 1. Setup LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    
    # 2. Setup Tools
    # Note: explicit max_results helps keep context size manageable
    tavily_tool = TavilySearchResults(max_results=3)
    tools = [tavily_tool]

    # 3. Create Agent (LangGraph Prebuilt)
    # create_react_agent creates a graph with a message state and tool calling node
    agent = create_react_agent(llm, tools, prompt="You are a helpful AI assistant. Use tools to find up-to-date information.")

    # 4. Generate Visualization (Optional)
    try:
        png_bytes = agent.get_graph().draw_mermaid_png()
        with open("agent_graph.png", "wb") as f:
            f.write(png_bytes)
        print("Graph visualization saved to 'agent_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    # 5. Run
    user_input = "Who won the World Series in 2024? If not played yet, who won in 2023?"
    print(f"\n--- User Query ---\n{user_input}\n")
    
    messages = [HumanMessage(content=user_input)]
    
    print("--- Streaming Execution ---")
    for step in agent.stream({"messages": messages}, stream_mode="values"):
        # The stream returns the current state (list of messages)
        current_messages = step["messages"]
        last_message = current_messages[-1]
        
        # Determine strict type for cleaner printing
        msg_type = last_message.type
        content = last_message.content
        
        print(f"\n[{msg_type.upper()}]: {content}")

if __name__ == "__main__":
    main()
