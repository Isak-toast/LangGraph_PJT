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
    - Routes to Researcher for information gathering
    - Routes to Writer for content creation
    - Routes to FINISH when the task is complete
    """
    messages = state["messages"]
    
    # Check if we already have a worker response (to avoid infinite loops)
    worker_responded = False
    for msg in reversed(messages):
        if hasattr(msg, 'name') and msg.name in members:
            worker_responded = True
            break
    
    # Improved system prompt with clear termination conditions
    supervisor_prompt = f"""You are a supervisor managing workers: {members}.

RULES:
1. If the user asks a QUESTION that needs research -> route to "Researcher"
2. If you need content to be written/summarized -> route to "Writer"  
3. If a worker has ALREADY responded with useful information -> route to "FINISH"
4. If the conversation is complete or no action needed -> route to "FINISH"
5. NEVER route to the same worker twice in a row without FINISH

Current worker already responded: {worker_responded}

Respond with ONLY the next action: {options}"""

    # Use structured output
    structured_llm = llm.with_structured_output({
        "type": "object", 
        "properties": {"next": {"type": "string", "enum": options}}, 
        "required": ["next"]
    })
    
    # Build prompt with conversation
    prompt = f"{supervisor_prompt}\n\nConversation:\n{messages[-5:]}"  # Only last 5 messages
    
    try:
        response = structured_llm.invoke(prompt)
        next_agent = response.get("next")
    except Exception as e:
        print(f"Supervisor error: {e}")
        next_agent = "FINISH"
    
    # Force FINISH if worker already responded (safety net)
    if worker_responded and next_agent in members:
        print(f"⚠️ Forcing FINISH: worker already responded")
        next_agent = "FINISH"
    
    if not next_agent or next_agent not in options:
        next_agent = "FINISH"
        
    return {"next": next_agent}

