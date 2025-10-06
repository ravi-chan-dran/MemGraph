"""MCP (Model Context Protocol) server for the memory system."""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
import uvicorn

from app.memory.service import memory_service
from app.core.config import settings
from app.core.bedrock import bedrock_client
from app.stores import graph_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MemoryWriteRequest(BaseModel):
    guid: str
    text: str
    channel: str
    ts: str
    thread_id: Optional[str] = None


class MemorySearchRequest(BaseModel):
    guid: str
    query: str
    k: int = 8
    since_days: int = 30
    include_graph: bool = True


class MemoryForgetRequest(BaseModel):
    guid: str
    keys: Optional[List[str]] = None
    entities: Optional[List[str]] = None
    predicates: Optional[List[str]] = None
    hard_delete: bool = False


class MemorySummarizeRequest(BaseModel):
    guid: str
    since_days: int = 7


class MemoryExplainRequest(BaseModel):
    guid: str
    topic: str
    k: int = 3


def verify_token(authorization: str = Header(None)):
    """Verify MCP token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    if token != settings.mcp_token:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return token


# FastAPI app
app = FastAPI(title="Memory MCP Server", version="1.0.0")


@app.post("/memory/write")
async def memory_write(request: MemoryWriteRequest, token: str = Depends(verify_token)):
    """Write memory data."""
    try:
        result = memory_service.write_memory(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/search")
async def memory_search(request: MemorySearchRequest, token: str = Depends(verify_token)):
    """Search memory with ranking and context building."""
    try:
        result = memory_service.search_memory(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/forget")
async def memory_forget(request: MemoryForgetRequest, token: str = Depends(verify_token)):
    """Forget specific memory items."""
    try:
        result = memory_service.forget_memory(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/summarize")
async def memory_summarize(request: MemorySummarizeRequest, token: str = Depends(verify_token)):
    """Summarize recent memory."""
    try:
        result = memory_service.summarize_memory(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/explain")
async def memory_explain(request: MemoryExplainRequest, token: str = Depends(verify_token)):
    """Explain shortest path and generate brief explanation."""
    try:
        # Get shortest paths
        paths = graph_store.find_paths(request.guid, request.topic, request.k)
        
        # Generate explanation using Claude
        if paths:
            path_info = {
                "topic": request.topic,
                "paths": paths,
                "shortest_length": min(path["length"] for path in paths) if paths else 0
            }
            
            system_prompt = """
            Provide a brief explanation of the relationship between the user and topic.
            Include the shortest path length and key connections.
            Be concise and informative.
            """
            
            user_prompt = f"Path information: {json.dumps(path_info, indent=2)}"
            explanation = bedrock_client.claude_complete(system_prompt, user_prompt)
        else:
            explanation = f"No direct path found between user {request.guid} and topic '{request.topic}'"
        
        return {
            "success": True,
            "paths": paths,
            "explanation": explanation
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "OK", "message": "MCP server is running"}


@app.get("/tools")
async def list_tools(token: str = Depends(verify_token)):
    """List available tools."""
    return {
        "tools": [
            {
                "name": "memory.write",
                "description": "Write memory data to all stores",
                "parameters": ["guid", "text", "channel", "ts", "thread_id?"]
            },
            {
                "name": "memory.search",
                "description": "Search memory with ranking and context building",
                "parameters": ["guid", "query", "k?", "since_days?", "include_graph?"]
            },
            {
                "name": "memory.forget",
                "description": "Forget specific memory items",
                "parameters": ["guid", "keys?", "entities?", "predicates?", "hard_delete?"]
            },
            {
                "name": "memory.summarize",
                "description": "Summarize recent memory",
                "parameters": ["guid", "since_days?"]
            },
            {
                "name": "memory.explain",
                "description": "Explain shortest path and generate brief explanation",
                "parameters": ["guid", "topic", "k?"]
            }
        ]
    }


if __name__ == "__main__":
    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=settings.mcp_port,
        reload=True
    )