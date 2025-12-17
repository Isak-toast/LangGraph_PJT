from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import research_node, writer_node, supervisor_node, members

# Create the graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("Supervisor", supervisor_node)
workflow.add_node("Researcher", research_node)
workflow.add_node("Writer", writer_node)

# Add edges
# Start -> Supervisor
workflow.add_edge(START, "Supervisor")

# Supervisor -> [Researcher, Writer, END] (Conditional)
for member in members:
    # After a worker finishes, go back to supervisor
    workflow.add_edge(member, "Supervisor")

# Conditional Edge definition
def route_supervisor(state: AgentState):
    next_node = state["next"]
    if next_node == "FINISH":
        return "FINISH"
    return next_node

workflow.add_conditional_edges(
    "Supervisor",
    route_supervisor,
    # Map 'next' string to Node Name (exact match)
    {
        "Researcher": "Researcher",
        "Writer": "Writer",
        "FINISH": END 
    }
)

# Compile
graph = workflow.compile()
