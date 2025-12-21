from typing import TypedDict, Annotated, List, Union
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
import operator

class AgentState(TypedDict):
    """
    The state of the agent graph.
    Track messages and the next agent to route to.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    next: str
