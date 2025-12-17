from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool

# Initialize Tavily Search Tool
# Ensure TAVILY_API_KEY is set in environment
tavily_tool = TavilySearchResults(max_results=3)

@tool
def read_chart_data():
    """Reads dummy chart data for visualization."""
    return {"data": [10, 20, 30, 40, 50], "labels": ["A", "B", "C", "D", "E"]}

tools = [tavily_tool]
