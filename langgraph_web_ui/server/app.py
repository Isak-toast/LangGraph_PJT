from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import uvicorn
import os
import json
import asyncio
from dotenv import load_dotenv
from typing import AsyncGenerator
from langchain_core.messages import HumanMessage
from pathlib import Path

# Load env variables (Current dir or Project Root)
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
env_path = current_dir / ".env"
if not env_path.exists():
    env_path = project_root / ".env"

load_dotenv(env_path)

# Import our graph
from agent.graph import graph

app = FastAPI(title="Agentic Insight Dashboard API")

# Configure CORS
origins = [
    "http://localhost:5173", # Vue Dev Server
    "http://localhost:5174", # Alternate
    "http://127.0.0.1:5173",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Agentic Insight Dashboard API is running"}

async def event_generator(user_input: str, thread_id: str) -> AsyncGenerator[str, None]:
    """
    Generator that creates SSE events from the LangGraph execution.
    """
    config = {"configurable": {"thread_id": thread_id}}
    
    # Send User Message
    inputs = {"messages": [HumanMessage(content=user_input)]}
    
    # Stream events
    # We use 'values' or 'updates' or 'events'. 
    # 'astream_events' gives fine-grained data (tokens, tool calls).
    # For this dashboard, specific custom events for Node changes are good.
    # Let's use 'astream_events' filtering for 'on_chain_start', 'on_chat_model_stream', etc.
    
    try:
        async for event in graph.astream_events(inputs, config=config, version="v2"):
            event_type = event["event"]
            data = "{}"
            
            # Filter and format events
            if event_type == "on_chat_model_stream":
                # Stream Tokens
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    payload = {"type": "token", "content": chunk.content}
                    yield f"data: {json.dumps(payload)}\n\n"
                    
            elif event_type == "on_chain_start":
                # Node Entry (Supervisor, Researcher, etc)
                name = event["name"]
                if name in ["Supervisor", "Researcher", "Writer"]:
                    payload = {"type": "node_start", "node": name}
                    yield f"data: {json.dumps(payload)}\n\n"
                    
            elif event_type == "on_chain_end":
                # Node Exit
                name = event["name"]
                if name in ["Supervisor", "Researcher", "Writer"]:
                    payload = {"type": "node_end", "node": name}
                    yield f"data: {json.dumps(payload)}\n\n"
            
            # Keep-alive or other events could be added
            
        yield "data: {\"type\": \"end\"}\n\n"
        
    except Exception as e:
        print(f"Error: {e}")
        yield f"data: {{\"type\": \"error\", \"content\": \"{str(e)}\"}}\n\n"

from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_thread"

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    return StreamingResponse(
        event_generator(request.message, request.thread_id),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
