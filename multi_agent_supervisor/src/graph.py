import operator
from typing import Annotated, Sequence, TypedDict, Union, List

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, START, END

from src.agents import build_agents, get_llm

# The State of the graph
class AgentState(TypedDict):
    # The annotation tells Graph how to update the state (additively)
    messages: Annotated[Sequence[BaseMessage], operator.add]
    # Who is next
    next: str

def create_graph():
    researcher_agent, chart_agent, llm = build_agents()

    # --- 1. Define Supervisor ---
    members = ["Researcher", "ChartGenerator"]
    system_prompt = (
        "You are a supervisor tasked with managing a conversation between the"
        " following workers:  {members}. Given the following user request,"
        " respond with the worker to act next. Each worker will perform a"
        " task and respond with their results and status. When finished,"
        " respond with FINISH."
    )
    
    options = ["FINISH"] + members
    
    # We use function calling to enforce structured output for routing
    function_def = {
        "name": "route",
        "description": "Select the next role.",
        "parameters": {
            "title": "routeSchema",
            "type": "object",
            "properties": {
                "next": {
                    "title": "Next Role",
                    "type": "string",
                    "enum": options,
                }
            },
            "required": ["next"],
        },
    }

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            (
                "system",
                "Given the conversation above, who should act next?"
                " Or should we FINISH? Select one of: {options}",
            ),
        ]
    ).partial(options=str(options), members=", ".join(members))

    def parse_route(message):
        if message.tool_calls:
            return message.tool_calls[0]["args"]
        return {"next": "FINISH"}

    supervisor_chain = (
        prompt
        | llm.bind_tools(tools=[function_def], tool_choice="route")
        | parse_route
    )

    # --- 2. Define Nodes ---
    
    # Helper to convert agent output to a format suitable for the graph
    def agent_node(agent, name):
        def _node(state):
            result = agent.invoke(state)
            # result is {'messages': [...]}
            # We extract the last message which contains the answer
            print(f"DEBUG: {name} messages: {result['messages']}")
            last_message = result["messages"][-1]
            return {"messages": [AIMessage(content=last_message.content, name=name)]}
        return _node

    researcher_node = agent_node(researcher_agent, "Researcher")
    chart_node = agent_node(chart_agent, "ChartGenerator")

    # Supervisor node
    def supervisor_node(state):
        result = supervisor_chain.invoke(state)
        return result

    # --- 3. Build Graph ---
    workflow = StateGraph(AgentState)
    
    workflow.add_node("Supervisor", supervisor_node)
    workflow.add_node("Researcher", researcher_node)
    workflow.add_node("ChartGenerator", chart_node)

    workflow.add_edge("Researcher", "Supervisor")
    workflow.add_edge("ChartGenerator", "Supervisor")

    # Edges from Supervisor
    conditional_map = {k: k for k in members}
    conditional_map["FINISH"] = END
    
    workflow.add_conditional_edges("Supervisor", lambda x: x["next"], conditional_map)
    
    workflow.add_edge(START, "Supervisor")

    return workflow.compile()
