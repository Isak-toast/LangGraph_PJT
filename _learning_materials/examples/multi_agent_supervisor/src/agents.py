from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_experimental.tools import PythonREPLTool
from langgraph.prebuilt import create_react_agent

def create_agent(llm, tools, system_prompt: str):
    """Create a LangGraph React agent."""
    # create_react_agent returns a CompiledGraph
    agent = create_react_agent(llm, tools, prompt=system_prompt)
    return agent

def get_llm():
    """Return the configured LLM."""
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

def build_agents():
    """Build and return the researcher and chart_generator agents."""
    llm = get_llm()

    # 1. Researcher Agent
    tavily_tool = TavilySearchResults(max_results=5)
    researcher_agent = create_agent(
        llm,
        [tavily_tool],
        "You are a web researcher. You search for accurate data. "
        "SEARCH for the requested information immediately using the tools. "
        "Do not ask for permission. Do not say what you cannot do, just do what you can."
    )

    # 2. Chart Generator Agent (using Python REPL)
    repl_tool = PythonREPLTool()
    
    chart_agent = create_agent(
        llm,
        [repl_tool],
        "You are a data visualizer. You can execute python code to generate charts. "
        "You MUST use the 'Python_REPL' tool to execute any code. "
        "Do not write python code in markdown blocks; you must call the tool. "
        "If you generate a plot, save it as 'chart.png' in the current directory. "
        "Always confirm when the file is saved."
    )

    return researcher_agent, chart_agent, llm

