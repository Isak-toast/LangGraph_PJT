
import os
import dotenv
from typing import Annotated, List, TypedDict, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults
from pydantic import BaseModel, Field

# Load env vars
dotenv.load_dotenv()

# --- Configs ---
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
search_tool = TavilySearchResults(k=3)

# --- Components ---

# 1. Grader
class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")

structured_llm_grader = llm.with_structured_output(GradeDocuments)

system_prompt_grader = """You are a grader assessing relevance of a retrieved document to a user question. \n 
If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n
Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""

def grade_documents(state):
    """
    Determines whether the retrieved documents are relevant to the question.
    """
    print("---CHECK RELEVANCE---")
    question = state["question"]
    documents = state["documents"]
    
    # Simple grader: just grade the first doc for this tutorial demo to keep it fast
    # In reality, you'd grade all of them.
    score = structured_llm_grader.invoke(f"User question: {question}\n\nRetrieved document: {documents[0]['content']}")
    grade = score.binary_score
    
    if grade == "yes":
        print("---DECISION: DOCUMENT RELEVANT---")
        return {"documents": documents}
    else:
        print("---DECISION: DOCUMENT NOT RELEVANT---")
        # In a full recurring loop we might rewrite query here, 
        # but for this simple DAG we will just proceed with empty docs or flag it.
        # Let's filter out irrelevant docs.
        return {"documents": []} # Filtered out

# 2. Generator
def generate(state):
    """
    Generates answer using the retrieved documents.
    """
    print("---GENERATE---")
    question = state["question"]
    documents = state["documents"]
    
    if not documents:
        return {"generation": "I could not find relevant information to answer your question."}

    # Context concatenation
    context = "\n\n".join([doc['content'] for doc in documents])
    
    prompt = f"""You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    
    Question: {question} 
    
    Context: {context} 
    
    Answer:"""
    
    generation = llm.invoke(prompt)
    return {"generation": generation.content}

# 3. Retrieval
def retrieve(state):
    """
    Retrieve documents
    """
    print("---RETRIEVE---")
    question = state["question"]
    docs = search_tool.invoke(question)
    # Tavily returns list of dicts with 'content' key
    return {"documents": docs}

# --- State ---
class GraphState(TypedDict):
    question: str
    generation: str
    documents: List[dict]

# --- Graph ---
workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)

workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade_documents")

def decide_to_generate(state):
    """
    Determines whether to generate an answer, or re-generate a question.
    """
    if not state["documents"]:
        # If no documents determined relevant (filtered out), we ends
        # In advanced RAG we would rewrite query here.
        return "generate" # We go to generate to say "I don't know"
    return "generate"

workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "generate": "generate",
    }
)
workflow.add_edge("generate", END)

app = workflow.compile()

def main():
    print("Initializing Agentic RAG...")
    try:
        with open("agentic_rag_graph.png", "wb") as f:
            f.write(app.get_graph().draw_mermaid_png())
        print("Graph saved to 'agentic_rag_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    inputs = {"question": "What are the key features of LangGraph?"}
    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"Finished node: {key}")

    print("\n--- Final Result ---")
    # State is not directly returned by stream iterator values in this specific structure easily without accumulating,
    # but let's just use the last known yielding. 
    # Actually 'value' in the loop is the state update.
    if 'generation' in value:
         print(value['generation'])

if __name__ == "__main__":
    main()
