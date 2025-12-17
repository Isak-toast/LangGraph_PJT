import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env from project root BEFORE imports
env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(env_path)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.graph import graph
from langchain_core.messages import HumanMessage


def test_graph_execution():
    print("Running Graph Test...")
    inputs = {"messages": [HumanMessage(content="Research about LangGraph and write a short summary.")]}
    
    # We use invoke to run full execution
    result = graph.invoke(inputs)
    
    messages = result["messages"]
    print(f"Total messages: {len(messages)}")
    
    # Check if we have Researcher and Writer outputs
    has_researcher = any(m.name == "Researcher" for m in messages if hasattr(m, 'name'))
    has_writer = any(m.name == "Writer" for m in messages if hasattr(m, 'name'))
    
    if has_researcher and has_writer:
        print("✅ Graph executed successfully with both agents.")
    else:
        print("❌ Graph failed to trigger both agents.")
        print(messages)

if __name__ == "__main__":
    test_graph_execution()
