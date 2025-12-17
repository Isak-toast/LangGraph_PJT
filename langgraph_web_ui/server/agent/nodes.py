import functools
import operator
from typing import Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from .state import AgentState
from .tools import tools, tavily_tool

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

# 1. Create Agents
# Researcher Agent (uses Tavily)
research_agent = create_react_agent(llm, tools=[tavily_tool])

def research_node(state: AgentState):
    """
    Executes the researcher agent.
    """
    # The agent returns a dictionary with 'messages'
    result = research_agent.invoke(state)
    # We return update to state
    # Ensure the last message is tagged with the agent name for clarity if needed
    last_msg = result["messages"][-1]
    return {
        "messages": [AIMessage(content=last_msg.content, name="Researcher")]
    }

# Writer Agent (No tools, just writing)
def writer_node(state: AgentState):
    """
    Executes the writer agent.
    """
    # Simple direct generation for writer
    prompt = f"Based on the conversation above, write a concise summary or report request. \nConversation: {state['messages']}"
    response = llm.invoke(state["messages"]) # Just pass messages context
    return {
        "messages": [AIMessage(content=response.content, name="Writer")]
    }

# 2. Supervisor Node
members = ["Researcher", "Writer"]
options = ["FINISH"] + members

system_prompt = (
    "You are a supervisor tasked with managing a conversation between the"
    " following workers: {members}. Given the following user request,"
    " respond with the worker to act next. Each worker will perform a"
    " task and respond with their results. When finished, respond with FINISH."
)

class Router(dict):
    """Structured output for routing"""
    # Pydantic-like structure defined via dict for Gemini simple usage or structure output wrapper
    # Here we use LLM function calling or structured output if available
    pass

def supervisor_node(state: AgentState):
    """
    Decides which agent to call next.
    """
    messages = state["messages"]
    
    # We ask the LLM to pick the next step
    supervisor_chain = (
        llm.bind(functions=[
            {
                "name": "route",
                "description": "Select the next role.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "next": {
                            "type": "string",
                            "enum": options,
                        }
                    },
                    "required": ["next"],
                },
            }
        ], function_call={"name": "route"}) 
    )
    # Or simpler: structured output
    # Since gemini-2.0 supports structured output well:
    structured_llm = llm.with_structured_output({"type": "object", "properties": {"next": {"type": "string", "enum": options}}, "required": ["next"]})
    
    # Construct prompt
    prompt = f"{system_prompt.format(members=members)}\n\nConversation history:\n{messages}"
    
    response = structured_llm.invoke(prompt)
    next_agent = response.get("next")
    
    if not next_agent or next_agent not in options:
        next_agent = "FINISH"
        
    return {"next": next_agent}
