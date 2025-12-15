import dotenv
from langchain_core.messages import HumanMessage
from src.graph import create_graph

# Load env vars
dotenv.load_dotenv()

def main():
    print("Initializing Multi-Agent Supervisor System...")
    graph = create_graph()
    
    # Generate visualization
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        with open("graph_diagram.png", "wb") as f:
            f.write(png_bytes)
        print("Graph visualization saved to 'graph_diagram.png'")
    except Exception as e:
        print(f"Skipping visualization (optional dependency missing?): {e}")

    print("\n--- Standard Query ---")
    user_input = "Research the GDP of South Korea over the last 5 years and plot a line chart."
    print(f"User: {user_input}\n")

    initial_state = {"messages": [HumanMessage(content=user_input)]}

    # Stream the execution
    for step in graph.stream(initial_state):
        if "__end__" not in step:
            for key, value in step.items():
                print(f"--- Node: {key} ---")
                if "messages" in value:
                    print(value["messages"][-1].content)
                elif "next" in value:
                    print(f"Supervisor decided next: {value['next']}")
                print("---------------------")

if __name__ == "__main__":
    main()
