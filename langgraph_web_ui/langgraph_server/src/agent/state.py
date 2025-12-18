"""
state.py - 에이전트 상태 정의
=================================

이 파일은 LangGraph에서 모든 노드가 공유하는 상태(State)를 정의합니다.
상태는 그래프 실행 중 노드 간에 전달되는 데이터 구조입니다.

핵심 개념:
- TypedDict: Python의 타입 힌팅을 위한 딕셔너리 타입
- Annotated: 타입에 추가 메타데이터를 붙이는 문법
- add_messages: LangGraph의 메시지 축적 리듀서 (새 메시지를 기존에 추가)
"""

from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    에이전트 간 공유 상태 (State)
    
    그래프의 모든 노드는 이 상태를 읽고 수정할 수 있습니다.
    각 노드는 상태의 일부를 업데이트하여 반환합니다.
    
    Attributes:
        messages: 대화 히스토리. add_messages 리듀서 덕분에 새 메시지가
                  기존 메시지 리스트에 자동으로 추가됩니다.
                  (예: [기존메시지1, 기존메시지2] + [새메시지] = [모든메시지])
        
        next: 다음에 실행할 노드의 이름. Supervisor가 이 값을 설정하여
              라우팅을 제어합니다.
              가능한 값: "Researcher", "Writer", "FINISH"
    
    예시:
        {
            "messages": [HumanMessage("AI 트렌드 알려줘"), AIMessage("검색 결과...")],
            "next": "FINISH"
        }
    """
    
    # 메시지 히스토리 - add_messages 리듀서로 자동 축적
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # 다음 노드 이름 - Supervisor가 결정
    next: str
