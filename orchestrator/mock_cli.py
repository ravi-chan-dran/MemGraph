"""Mock CLI orchestrator for testing the memory system."""

import typer
import requests
import json
from typing import List, Optional
from datetime import datetime

app = typer.Typer()

# API base URL
API_BASE = "http://localhost:8000"


def make_request(method: str, endpoint: str, data: Optional[dict] = None) -> dict:
    """Make a request to the API."""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=data)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


@app.command()
def health():
    """Check API health."""
    result = make_request("GET", "/health")
    typer.echo(json.dumps(result, indent=2))


@app.command()
def add_memory(
    text: str = typer.Argument(..., help="Memory text to add"),
    source: Optional[str] = typer.Option(None, help="Source of the memory"),
    metadata: Optional[str] = typer.Option(None, help="Metadata as JSON string")
):
    """Add a new memory."""
    data = {"text": text}
    if source:
        data["source"] = source
    if metadata:
        try:
            data["metadata"] = json.loads(metadata)
        except json.JSONDecodeError:
            typer.echo("Error: Invalid JSON in metadata")
            raise typer.Exit(1)
    
    result = make_request("POST", "/memories", data)
    typer.echo(json.dumps(result, indent=2))


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    search_type: str = typer.Option("semantic", help="Search type: semantic, entity, metadata"),
    limit: int = typer.Option(5, help="Maximum number of results")
):
    """Search memories."""
    data = {
        "query": query,
        "search_type": search_type,
        "limit": limit
    }
    
    result = make_request("POST", "/search", data)
    typer.echo(json.dumps(result, indent=2))


@app.command()
def get_memory(memory_id: str = typer.Argument(..., help="Memory ID")):
    """Get a specific memory by ID."""
    result = make_request("GET", f"/memories/{memory_id}")
    typer.echo(json.dumps(result, indent=2))


@app.command()
def get_entity(
    entity_name: str = typer.Argument(..., help="Entity name"),
    entity_type: Optional[str] = typer.Option(None, help="Entity type filter")
):
    """Get entity context."""
    params = {"entity_name": entity_name}
    if entity_type:
        params["entity_type"] = entity_type
    
    result = make_request("GET", f"/entities/{entity_name}", params)
    typer.echo(json.dumps(result, indent=2))


@app.command()
def timeline(
    entity_name: Optional[str] = typer.Option(None, help="Filter by entity name"),
    limit: int = typer.Option(20, help="Maximum number of memories")
):
    """Get memory timeline."""
    params = {"limit": limit}
    if entity_name:
        params["entity_name"] = entity_name
    
    result = make_request("GET", "/timeline", params)
    typer.echo(json.dumps(result, indent=2))


@app.command()
def insights(
    query: str = typer.Argument(..., help="Query for insights"),
    max_memories: int = typer.Option(10, help="Maximum memories to analyze")
):
    """Generate insights from memories."""
    data = {
        "query": query,
        "max_memories": max_memories
    }
    
    result = make_request("POST", "/insights", data)
    typer.echo(json.dumps(result, indent=2))


@app.command()
def stats():
    """Get system statistics."""
    result = make_request("GET", "/stats")
    typer.echo(json.dumps(result, indent=2))


@app.command()
def demo_conversation():
    """Run a demo conversation."""
    typer.echo("Running demo conversation...")
    
    # Sample conversation
    conversation = [
        {"speaker": "Alice", "content": "I'm working on a new AI project using AWS Bedrock."},
        {"speaker": "Bob", "content": "That sounds interesting! What kind of AI models are you using?"},
        {"speaker": "Alice", "content": "I'm using Claude for text generation and Titan for embeddings."},
        {"speaker": "Bob", "content": "Are you planning to use any graph databases for the knowledge representation?"},
        {"speaker": "Alice", "content": "Yes, I'm thinking of using Neo4j for the graph storage and ChromaDB for vector search."},
        {"speaker": "Bob", "content": "That's a great combination! Neo4j is excellent for relationship modeling."}
    ]
    
    # Process conversation
    data = {"messages": conversation}
    result = make_request("POST", "/memories/conversation", data)
    
    typer.echo("Conversation processed:")
    typer.echo(json.dumps(result, indent=2))
    
    # Search for AI-related memories
    typer.echo("\nSearching for AI-related memories:")
    search_result = make_request("POST", "/search", {"query": "AI project", "limit": 5})
    typer.echo(json.dumps(search_result, indent=2))


@app.command()
def demo_document():
    """Run a demo document processing."""
    typer.echo("Processing demo document...")
    
    document_content = """
    AWS Bedrock is a fully managed service that makes foundation models (FMs) from leading AI companies 
    available through a single API. It provides access to models from Amazon, Anthropic, AI21 Labs, 
    Cohere, Meta, and Stability AI.
    
    Key features include:
    - Access to high-performing FMs from leading AI companies
    - Serverless experience for inference
    - Fine-tuning capabilities
    - RAG (Retrieval Augmented Generation) support
    - Built-in security and privacy controls
    
    Use cases include text generation, summarization, question answering, and content creation.
    """
    
    data = {
        "content": document_content,
        "title": "AWS Bedrock Overview",
        "url": "https://aws.amazon.com/bedrock/"
    }
    
    result = make_request("POST", "/memories/document", data)
    typer.echo("Document processed:")
    typer.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    app()
