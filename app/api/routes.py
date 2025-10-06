"""FastAPI routes for the Bedrock-powered Graph + Memory POC."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import uvicorn

from ..core.config import settings
from ..core.bedrock import bedrock_client
from ..memory.service import memory_service


# Pydantic models for request/response
class WriteMemoryRequest(BaseModel):
    guid: str
    text: str
    channel: str
    ts: str
    thread_id: Optional[str] = None


class SearchMemoryRequest(BaseModel):
    guid: str
    query: str
    k: int = 8
    since_days: int = 30
    include_graph: bool = True


class SummarizeMemoryRequest(BaseModel):
    guid: str
    since_days: int = 7


class ForgetMemoryRequest(BaseModel):
    guid: str
    keys: Optional[List[str]] = None
    entities: Optional[List[str]] = None
    predicates: Optional[List[str]] = None
    hard_delete: bool = False


class MemoryRequest(BaseModel):
    text: str
    source: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationRequest(BaseModel):
    messages: List[Dict[str, str]]


class DocumentRequest(BaseModel):
    content: str
    title: Optional[str] = None
    url: Optional[str] = None


class SearchRequest(BaseModel):
    query: str
    search_type: str = "semantic"
    limit: int = 5
    filters: Optional[Dict[str, Any]] = None


class InsightRequest(BaseModel):
    query: str
    max_memories: int = 10


# Initialize FastAPI app
app = FastAPI(
    title="Bedrock Graph + Memory POC",
    description="A proof-of-concept system for graph-based memory management powered by AWS Bedrock",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint with Bedrock self-test."""
    try:
        # Test Titan embedding
        embeddings = bedrock_client.titan_embed(["hello"])
        vector_length = len(embeddings[0]) if embeddings and embeddings[0] else 0
        
        return {
            "status": "OK", 
            "message": "Service is running",
            "bedrock_test": {
                "titan_embed_vector_length": vector_length,
                "test_passed": vector_length > 0
            }
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": "Service is running but Bedrock test failed",
            "bedrock_test": {
                "error": str(e),
                "test_passed": False
            }
        }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Bedrock Graph + Memory POC API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "add_memory": "/memories",
            "search": "/search",
            "insights": "/insights",
            "stats": "/stats"
        }
    }


@app.post("/memories")
async def add_memory(request: MemoryRequest):
    """Add a new memory to the system."""
    try:
        result = memory_service.add_memory(
            text=request.text,
            source=request.source,
            metadata=request.metadata
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memories/conversation")
async def process_conversation(request: ConversationRequest):
    """Process a conversation and extract memories."""
    try:
        result = memory_service.process_conversation(request.messages)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memories/document")
async def process_document(request: DocumentRequest):
    """Process a document and extract memories."""
    try:
        result = memory_service.process_document(
            content=request.content,
            title=request.title,
            url=request.url
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search")
async def search_memories(request: SearchRequest):
    """Search for memories using different strategies."""
    try:
        result = memory_service.search_memories(
            query=request.query,
            search_type=request.search_type,
            limit=request.limit,
            filters=request.filters
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/search")
async def search_memories_get(
    query: str = Query(..., description="Search query"),
    search_type: str = Query("semantic", description="Search type: semantic, entity, metadata"),
    limit: int = Query(5, description="Maximum number of results")
):
    """Search for memories using GET method."""
    try:
        result = memory_service.search_memories(
            query=query,
            search_type=search_type,
            limit=limit
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memories/{memory_id}")
async def get_memory(memory_id: str):
    """Get a specific memory by ID."""
    try:
        result = memory_service.get_memory_context(memory_id, include_related=True)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/entities/{entity_name}")
async def get_entity_context(
    entity_name: str,
    entity_type: Optional[str] = Query(None, description="Entity type filter")
):
    """Get context about a specific entity."""
    try:
        result = memory_service.get_entity_context(entity_name, entity_type)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/timeline")
async def get_timeline(
    entity_name: Optional[str] = Query(None, description="Filter by entity name"),
    limit: int = Query(20, description="Maximum number of memories")
):
    """Get a timeline of memories."""
    try:
        result = memory_service.get_timeline(entity_name, limit)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/insights")
async def generate_insights(request: InsightRequest):
    """Generate insights from memories."""
    try:
        result = memory_service.generate_insights(
            query=request.query,
            max_memories=request.max_memories
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/write")
async def write_memory(request: WriteMemoryRequest):
    """Write memory data to all stores."""
    try:
        result = memory_service.write_memory(request.dict())
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/search")
async def search_memory(request: SearchMemoryRequest):
    """Search memory with ranking and context building."""
    try:
        result = memory_service.search_memory(request.dict())
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/summarize")
async def summarize_memory(request: SummarizeMemoryRequest):
    """Summarize recent memory."""
    try:
        result = memory_service.summarize_memory(request.dict())
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/memory/forget")
async def forget_memory(request: ForgetMemoryRequest):
    """Forget specific memory items."""
    try:
        result = memory_service.forget_memory(request.dict())
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/facts")
async def get_memory_facts(guid: str = Query(..., description="User GUID")):
    """Get all facts for a user."""
    try:
        from ..stores import kv_store
        facts = kv_store.get_facts(guid, min_conf=0.0)
        return {
            "success": True,
            "facts": facts,
            "count": len(facts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/subgraph")
async def get_subgraph(
    guid: str = Query(..., description="User GUID"),
    since_days: Optional[int] = Query(None, description="Days to look back")
):
    """Get subgraph for a user."""
    try:
        from ..stores.graph_neo4j import get_graph_store
        nodes = get_graph_store().get_subgraph(guid, since_days)
        return {"success": True, "nodes": nodes, "count": len(nodes)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph/paths")
async def get_paths(
    guid: str = Query(..., description="User GUID"),
    topic: str = Query(..., description="Topic to find paths to"),
    k: int = Query(3, description="Number of paths to return")
):
    """Find paths between user and topic."""
    try:
        from ..stores.graph_neo4j import get_graph_store
        paths = get_graph_store().find_paths(guid, topic, k)
        return {"success": True, "paths": paths, "count": len(paths)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_system_stats():
    """Get system statistics."""
    try:
        result = memory_service.get_system_stats()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(
        "app.api.routes:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
