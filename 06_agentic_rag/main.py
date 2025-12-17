
"""
LangGraph 06: Agentic RAG (Adaptive RAG)
=========================================
이 예제는 Agentic RAG(검색 증강 생성) 패턴을 보여줍니다.
단순히 검색하고 답하는 것이 아니라, 검색된 문서가 유용한지 '평가(Grade)'하고
필요하면 다시 검색하거나, 답변 생성을 진행하는 능동적인 흐름을 가집니다.

핵심 개념:
1. Retrieval (검색): Tavily Search를 통해 관련 문서 수집
2. Grading (평가): LLM(Structured Output)을 사용해 문서의 관련성 점수(Yes/No) 판단
3. Conditional Logic (조건부 로직): 
   - 관련 문서가 있으면 -> 답변 생성(Generate)
   - 없으면 -> (이 예제에선) 종료하거나 재검색 로직 추가 가능

실행 흐름:
[Retrieve] --> [Grade Documents] --(Relevant?)--> [Generate] --> [END]
                                        |
                                   (No Docs)
                                        ↓
                               [Generate (Unknown)]
"""

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
from pathlib import Path

# 환경 변수 로드
script_dir = Path(__file__).parent
project_root = script_dir.parent
env_file = project_root / ".env"
if not env_file.exists():
    env_file = script_dir / ".env"
dotenv.load_dotenv(env_file)

# LangSmith 추적 설정
if os.getenv("LANGCHAIN_TRACING_V2") == "true":
    print("📊 LangSmith 추적이 활성화되었습니다.")
    print(f"   프로젝트: {os.getenv('LANGCHAIN_PROJECT', 'default')}")


# =============================================================================
# 1. 설정 (Config)
# =============================================================================
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
search_tool = TavilySearchResults(k=3)


# =============================================================================
# 2. 컴포넌트(Components) 정의: Grader & Generator
# =============================================================================

# --- 2.1 문서 평가기 (Grader) ---
class GradeDocuments(BaseModel):
    """문서의 관련성을 'yes' 또는 'no'로 평가하는 바이너리 스코어 모델"""
    binary_score: str = Field(description="Documents are relevant to the question, 'yes' or 'no'")

# Structured Output을 사용하여 LLM이 항상 JSON 형태(GradeDocuments)로 응답하게 강제함
structured_llm_grader = llm.with_structured_output(GradeDocuments)

def grade_documents(state):
    """
    검색된 문서들이 질문과 관련이 있는지 평가하여 필터링합니다.
    """
    print("---[Grade] 문서 관련성 평가 중---")
    question = state["question"]
    documents = state["documents"]
    
    # 예제 단순화를 위해 첫 번째 문서만 평가합니다 (실제로는 모든 문서를 평가해야 함)
    score = structured_llm_grader.invoke(f"User question: {question}\n\nRetrieved document: {documents[0]['content']}")
    grade = score.binary_score
    
    if grade == "yes":
        print("   >>> 결정: 문서가 관련 있음 (Relevant)")
        return {"documents": documents}
    else:
        print("   >>> 결정: 문서가 관련 없음 (Not Relevant)")
        # 관련 없는 문서는 필터링 (빈 리스트 반환)
        return {"documents": []} 


# --- 2.2 답변 생성기 (Generator) ---
def generate(state):
    """
    검색된 문서를 바탕으로 답변을 생성합니다.
    """
    print("---[Generate] 답변 생성 중---")
    question = state["question"]
    documents = state["documents"]
    
    # 관련 문서가 하나도 없으면 모른다고 답함
    if not documents:
        return {"generation": "죄송합니다. 관련 정보를 찾을 수 없어 답변드릴 수 없습니다."}

    # 문서 내용 연결 (Context)
    context = "\n\n".join([doc['content'] for doc in documents])
    
    # RAG 프롬프트
    prompt = f"""You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    
    Question: {question} 
    
    Context: {context} 
    
    Answer:"""
    
    generation = llm.invoke(prompt)
    return {"generation": generation.content}


# --- 2.3 검색기 (Retriever) ---
def retrieve(state):
    """
    질문에 대한 관련 정보를 검색합니다.
    """
    print("---[Retrieve] 정보 검색 중---")
    question = state["question"]
    docs = search_tool.invoke(question)
    # Tavily는 [{'content': '...', 'url': '...'}, ...] 형태의 리스트 반환
    return {"documents": docs}


# =============================================================================
# 3. 상태(State) 정의
# =============================================================================
class GraphState(TypedDict):
    """
    그래프 상태: 질문, 생성된 답변, 검색된 문서들을 저장
    """
    question: str
    generation: str
    documents: List[dict]


# =============================================================================
# 4. 그래프(Graph) 구축
# =============================================================================
workflow = StateGraph(GraphState)

# 노드 추가
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate", generate)

# 엣지 연결
workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade_documents")

# 조건부 엣지 함수
def decide_to_generate(state):
    """
    문서 평가 결과에 따라 다음 단계를 결정합니다.
    - 문서가 있으면(Relevant) -> generate
    - 문서가 없으면(Not Relevant) -> generate (여기선 바로 종료하거나 모른다고 하기 위해)
    (Advanced RAG에서는 여기서 'transform_query'로 가서 재검색을 시도합니다.)
    """
    if not state["documents"]:
        return "generate" # 문서가 없어도 generate로 가서 "모른다"고 답변
    return "generate"

workflow.add_conditional_edges(
    "grade_documents",
    decide_to_generate,
    {
        "generate": "generate",
    }
)
workflow.add_edge("generate", END)

# 컴파일
app = workflow.compile()


# =============================================================================
# 5. 실행(Execution)
# =============================================================================
def main():
    print("Initializing Agentic RAG...\n")
    
    # 시각화
    try:
        with open("agentic_rag_graph.png", "wb") as f:
            f.write(app.get_graph().draw_mermaid_png())
        print("Graph saved to 'agentic_rag_graph.png'")
    except Exception as e:
        print(f"Skipping visualization: {e}")

    inputs = {"question": "What are the key features of LangGraph?"}
    print(f"\n--- User Question: {inputs['question']} ---")
    
    for output in app.stream(inputs):
        for key, value in output.items():
            # 노드 실행 완료 메시지
            pass # 출력은 각 노드 함수 내부의 print문에 맡김

    print("\n--- Final Result ---")
    # stream()의 마지막 출력값이 최종 상태라고 보장할 수 없으므로,
    # 여기서는 간단히 마지막으로 잡힌 value를 사용 (실제로는 run loop 구조에 따라 다름)
    if 'generation' in value:
         print(f"🤖 Answer: {value['generation']}")

if __name__ == "__main__":
    main()
