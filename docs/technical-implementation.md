# MemoryGraph: Technical Implementation Guide

## Table of Contents
1. [Core Implementation Details](#core-implementation-details)
2. [Memory Extraction Pipeline](#memory-extraction-pipeline)
3. [Storage Layer Implementation](#storage-layer-implementation)
4. [Graph Database Operations](#graph-database-operations)
5. [Retrieval and Scoring](#retrieval-and-scoring)
6. [API Implementation](#api-implementation)
7. [A/B Testing Framework](#ab-testing-framework)
8. [UI Implementation](#ui-implementation)
9. [Performance Optimizations](#performance-optimizations)
10. [Error Handling](#error-handling)

## Core Implementation Details

### Configuration Management (`app/core/config.py`)

The configuration system uses Pydantic Settings for environment variable management with type validation and defaults:

```python
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # AWS Bedrock Configuration
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    bedrock_claude_model_id: str = Field(default="anthropic.claude-3-sonnet-20240229-v1:0", env="BEDROCK_CLAUDE_MODEL_ID")
    bedrock_titan_emb_model_id: str = Field(default="amazon.titan-embed-text-v1", env="BEDROCK_TITAN_EMB_MODEL_ID")
    
    # Database Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="test123456", env="NEO4J_PASSWORD")
    db_url: str = Field(default="sqlite:///./memory.db", env="DB_URL")
    
    # ChromaDB Configuration
    chroma_persist_directory: str = Field(default="./chroma_db", env="CHROMA_PERSIST_DIRECTORY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
```

### Bedrock Client Implementation (`app/core/bedrock.py`)

The Bedrock client implements retry logic with exponential backoff and chunking for large inputs:

```python
import boto3
import time
import random
from typing import List

class BedrockClient:
    def __init__(self, settings: Settings):
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=settings.aws_region
        )
        self.claude_model_id = settings.bedrock_claude_model_id
        self.titan_model_id = settings.bedrock_titan_emb_model_id
        self.max_retries = 3
        self.base_delay = 1.0
        self.max_delay = 60.0

    def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                
                delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                time.sleep(delay)

    def claude_complete(self, system_prompt: str, user_prompt: str, temperature: float = 0) -> str:
        """Complete text using Claude model."""
        def _call_claude():
            response = self.bedrock_runtime.invoke_model(
                modelId=self.claude_model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4000,
                    "temperature": temperature,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}]
                })
            )
            return json.loads(response['body'].read())['content'][0]['text']
        
        return self._retry_with_backoff(_call_claude)

    def titan_embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Titan model with chunking."""
        all_embeddings = []
        chunk_size = 32  # Titan's limit
        
        for i in range(0, len(texts), chunk_size):
            chunk = texts[i:i + chunk_size]
            
            def _call_titan():
                response = self.bedrock_runtime.invoke_model(
                    modelId=self.titan_model_id,
                    body=json.dumps({"inputText": chunk})
                )
                return json.loads(response['body'].read())['embeddings']
            
            embeddings = self._retry_with_backoff(_call_titan)
            all_embeddings.extend(embeddings)
        
        return all_embeddings
```

## Memory Extraction Pipeline

### Information Extractor (`app/memory/extractor.py`)

The extractor uses Claude to extract structured information from text with confidence filtering:

```python
class MemoryExtractor:
    def __init__(self, bedrock_client: BedrockClient):
        self.bedrock = bedrock_client
        self.confidence_threshold = 0.6

    def extract_structured(self, text: str, channel: str, ts: str) -> Dict[str, Any]:
        """Extract structured facts and episodes from text."""
        system_prompt = """
        Extract structured information from the text and return ONLY valid JSON with:
        - facts: array of {key, value, confidence, reason}
        - episodes: array of {summary, importance, tags}
        
        Only include items with confidence >= 0.6.
        Be precise and factual.
        Return ONLY the JSON object, no other text.
        """
        
        user_prompt = f"Text: {text}\nChannel: {channel}\nTimestamp: {ts}"
        response = self.bedrock.claude_complete(system_prompt, user_prompt)
        
        try:
            result = json.loads(response)
            # Filter by confidence threshold
            if "facts" in result:
                result["facts"] = [f for f in result["facts"] 
                                 if f.get("confidence", 0) >= self.confidence_threshold]
            if "episodes" in result:
                result["episodes"] = [e for e in result["episodes"] 
                                    if e.get("importance", 0) >= self.confidence_threshold]
            return result
        except json.JSONDecodeError:
            return {"facts": [], "episodes": []}

    def extract_triples(self, text: str, channel: str, ts: str) -> Dict[str, Any]:
        """Extract entities and triples from text."""
        system_prompt = """
        Extract entities and relationships from the text and return JSON with:
        - entities: array of {name, type, aliases?} where type is one of: Person, Place, DateRange, Preference, Task, Product, Org, Event, Policy, Process, Formula, Rate, Date, Plan
        - triples: array of {subject, predicate, object, confidence, time?} where predicate is one of: PREFERS, PLANS, OCCURS_ON, HAS_SIZE, HAS_ROLE, MENTIONS, RELATED_TO, HAS_FORMULA, HAS_RATE, SCHEDULED_FOR, APPLIES_TO
        
        Only include items with confidence >= 0.6.
        Be precise about entity types and predicates.
        For business/retirement plan content, create entities for key concepts like "match formula", "contribution rate", "payroll processing", etc.
        """
        
        user_prompt = f"Text: {text}\nChannel: {channel}\nTimestamp: {ts}"
        response = self.bedrock.claude_complete(system_prompt, user_prompt)
        
        try:
            result = json.loads(response)
            # Filter by confidence threshold and validate types
            if "entities" in result:
                valid_types = {"Person", "Place", "DateRange", "Preference", "Task", "Product", "Org", "Event", "Policy", "Process", "Formula", "Rate", "Date", "Plan"}
                result["entities"] = [e for e in result["entities"] 
                                    if e.get("type") in valid_types and e.get("confidence", 0) >= self.confidence_threshold]
            if "triples" in result:
                valid_predicates = {"PREFERS", "PLANS", "OCCURS_ON", "HAS_SIZE", "HAS_ROLE", "MENTIONS", "RELATED_TO", "HAS_FORMULA", "HAS_RATE", "SCHEDULED_FOR", "APPLIES_TO"}
                result["triples"] = [t for t in result["triples"] 
                                   if t.get("predicate") in valid_predicates and t.get("confidence", 0) >= self.confidence_threshold]
            return result
        except json.JSONDecodeError:
            return {"entities": [], "triples": []}
```

## Storage Layer Implementation

### SQLite Facts Store (`app/stores/kv_sqlite.py`)

```python
import sqlite3
from typing import List, Dict, Any, Optional

class SQLiteKVStore:
    def __init__(self, db_path: str = "memory.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Initialize the facts table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS facts (
                    guid TEXT,
                    key TEXT,
                    value TEXT,
                    confidence REAL,
                    source TEXT,
                    ts TEXT,
                    PRIMARY KEY(guid, key)
                )
            """)
            conn.commit()

    def upsert_fact(self, guid: str, key: str, value: str, confidence: float, source: str, ts: str) -> bool:
        """Upsert a fact into the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO facts (guid, key, value, confidence, source, ts)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (guid, key, value, confidence, source, ts))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error upserting fact: {e}")
            return False

    def get_facts(self, guid: str, min_conf: float = 0.6) -> List[Dict[str, Any]]:
        """Get facts for a user with minimum confidence."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT key, value, confidence, source, ts
                    FROM facts
                    WHERE guid = ? AND confidence >= ?
                    ORDER BY confidence DESC, ts DESC
                """, (guid, min_conf))
                
                return [
                    {
                        "key": row[0],
                        "value": row[1],
                        "confidence": row[2],
                        "source": row[3],
                        "ts": row[4]
                    }
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            print(f"Error getting facts: {e}")
            return []

    def delete_fact(self, guid: str, key: str) -> bool:
        """Delete a specific fact."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM facts WHERE guid = ? AND key = ?", (guid, key))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error deleting fact: {e}")
            return False
```

### ChromaDB Vector Store (`app/stores/vector_chroma.py`)

```python
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

class ChromaVectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """Get or create the episodes_mem collection."""
        try:
            return self.client.get_collection("episodes_mem")
        except Exception:
            return self.client.create_collection(
                name="episodes_mem",
                metadata={"description": "Episodic memories with embeddings"}
            )

    def upsert_episode(self, guid: str, text: str, metadata: Dict, embedding: List[float]) -> bool:
        """Upsert an episode with guid, text, metadata, and embedding."""
        try:
            episode_id = f"{guid}_{uuid.uuid4().hex[:8]}"
            
            # Prepare metadata with guid and timestamp, converting lists to strings
            episode_metadata = {
                "guid": guid,
                "timestamp": datetime.now().isoformat()
            }
            
            # Add metadata, converting lists to strings for ChromaDB compatibility
            for key, value in metadata.items():
                if isinstance(value, list):
                    episode_metadata[key] = ",".join(str(item) for item in value)
                else:
                    episode_metadata[key] = value
            
            self.collection.upsert(
                ids=[episode_id],
                documents=[text],
                metadatas=[episode_metadata],
                embeddings=[embedding]
            )
            return True
        except Exception as e:
            print(f"Error upserting episode for {guid}: {e}")
            return False

    def query_similar(self, guid: str, query: str, k: int = 8, since_days: Optional[int] = 30) -> List[Dict[str, Any]]:
        """Query similar episodes using vector similarity."""
        try:
            # Get query embedding (this would typically use the embedding model)
            # For now, we'll use a placeholder
            query_embedding = [0.0] * 1536  # Titan embedding dimension
            
            # Build where clause for filtering
            where_clause = {"guid": guid}
            if since_days:
                from datetime import datetime, timedelta
                cutoff_date = (datetime.now() - timedelta(days=since_days)).isoformat()
                where_clause["timestamp"] = {"$gte": cutoff_date}
            
            # Query the collection - use simple where clause for ChromaDB compatibility
            try:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k,
                    where=where_clause
                )
            except Exception as e:
                # Fallback to simple guid filter if complex where clause fails
                print(f"ChromaDB query error, using fallback: {e}")
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=k,
                    where={"guid": guid}
                )
            
            # Format results
            episodes = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    episodes.append({
                        "text": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        "distance": results['distances'][0][i] if results['distances'] and results['distances'][0] else 0.0
                    })
            
            return episodes
        except Exception as e:
            print(f"Error querying similar episodes: {e}")
            return []
```

## Graph Database Operations

### Neo4j Graph Store (`app/stores/graph_neo4j.py`)

```python
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import json

class Neo4jGraphStore:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.init_constraints()

    def init_constraints(self):
        """Initialize unique constraints."""
        with self.driver.session() as session:
            # Create unique constraints
            session.run("CREATE CONSTRAINT user_guid_unique FOR (u:User) REQUIRE u.guid IS UNIQUE")
            session.run("CREATE CONSTRAINT entity_key_unique FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE")
            session.run("CREATE CONSTRAINT fact_key_unique FOR (f:Fact) REQUIRE (f.key, f.guid) IS UNIQUE")

    def upsert_user(self, guid: str) -> bool:
        """Upsert a user node."""
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (u:User {guid: $guid})
                    SET u.created_at = datetime()
                """, guid=guid)
            return True
        except Exception as e:
            print(f"Error upserting user {guid}: {e}")
            return False

    def upsert_entity(self, name: str, entity_type: str, aliases: List[str] = None) -> bool:
        """Upsert an entity node."""
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (e:Entity {name: $name, type: $type})
                    SET e.aliases = $aliases,
                        e.updated_at = datetime()
                """, name=name, type=entity_type, aliases=aliases or [])
            return True
        except Exception as e:
            print(f"Error upserting entity {name}: {e}")
            return False

    def upsert_fact_rel(self, guid: str, key: str, value: str, confidence: float, ts: str, channel: str) -> bool:
        """Upsert a fact node and relationship to user."""
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (u:User {guid: $guid})
                    MERGE (f:Fact {key: $key, guid: $guid})
                    SET f.value = $value,
                        f.confidence = $confidence,
                        f.source = $channel,
                        f.ts = $ts,
                        f.updated_at = datetime()
                    MERGE (u)-[:HAS_FACT]->(f)
                """, guid=guid, key=key, value=value, confidence=confidence, ts=ts, channel=channel)
            return True
        except Exception as e:
            print(f"Error upserting fact relationship: {e}")
            return False

    def upsert_triple(self, subject: str, predicate: str, obj: str, props: Dict = None) -> bool:
        """Upsert a triple relationship."""
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (s:Entity {name: $subject})
                    MERGE (o:Entity {name: $object})
                    MERGE (s)-[r:RELATION {predicate: $predicate}]->(o)
                    SET r.properties = $props,
                        r.updated_at = datetime()
                """, subject=subject, predicate=predicate, object=obj, props=props or {})
            return True
        except Exception as e:
            print(f"Error upserting triple: {e}")
            return False

    def shortest_path_len(self, guid: str, topic: str) -> int:
        """Find shortest path length from user to topic."""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:User {guid: $guid})
                    MATCH (t:Entity {name: $topic})
                    MATCH path = shortestPath((u)-[*]-(t))
                    RETURN length(path) as path_length
                """, guid=guid, topic=topic)
                
                record = result.single()
                return record['path_length'] if record else 99
        except Exception as e:
            print(f"Error finding shortest path: {e}")
            return 99

    def get_subgraph(self, guid: str, since_days: int = 30) -> List[Dict[str, Any]]:
        """Get user's subgraph."""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:User {guid: $guid})-[:HAS_FACT]->(f:Fact)
                    WHERE f.ts >= datetime() - duration({days: $since_days})
                    RETURN f.key as key, f.value as value, f.confidence as confidence, 
                           f.source as channel, f.ts as ts
                    ORDER BY f.confidence DESC, f.ts DESC
                """, guid=guid, since_days=since_days)
                
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error getting subgraph: {e}")
            return []

    def find_paths(self, guid: str, topic: str, k: int = 3) -> List[Dict[str, Any]]:
        """Find paths from user to topic."""
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (u:User {guid: $guid})
                    MATCH (t:Entity {name: $topic})
                    MATCH path = (u)-[*1..3]-(t)
                    RETURN path, length(path) as path_length
                    ORDER BY path_length
                    LIMIT $k
                """, guid=guid, topic=topic, k=k)
                
                paths = []
                for record in result:
                    path = record['path']
                    path_length = record['path_length']
                    path_str = " -> ".join([node.get('name', node.get('key', 'Unknown')) for node in path])
                    paths.append({
                        "path": path_str,
                        "length": path_length,
                        "reasoning": f"Found path of length {path_length} from user to {topic}"
                    })
                
                return paths
        except Exception as e:
            print(f"Error finding paths: {e}")
            return []
```

## Retrieval and Scoring

### Memory Retriever (`app/memory/retrieval.py`)

```python
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta

class MemoryRetriever:
    def __init__(self, bedrock_client):
        self.bedrock = bedrock_client

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        except:
            return 0.0

    def recency_score(self, timestamp: str, decay_days: float = 7.0) -> float:
        """Calculate recency score with exponential decay."""
        try:
            ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            days_ago = (datetime.now() - ts).total_seconds() / (24 * 3600)
            return np.exp(-days_ago / decay_days)
        except:
            return 0.5

    def importance_score(self, metadata: Dict) -> float:
        """Calculate importance score from metadata."""
        return metadata.get('importance', 0.5)

    def graph_proximity_score(self, path_length: int) -> float:
        """Calculate graph proximity score."""
        if path_length == 0:
            return 1.0
        elif path_length >= 99:
            return 0.0
        else:
            return 1.0 / (1.0 + path_length)

    def calculate_score(self, similarity: float, recency: float, importance: float, graph_prox: float) -> float:
        """Calculate final weighted score."""
        return 0.55 * similarity + 0.2 * recency + 0.15 * importance + 0.1 * graph_prox

    def build_context_card(self, facts: List[Dict], episodes: List[Dict], graph_hits: List[Dict], query: str) -> str:
        """Build context card using Claude."""
        context_parts = []
        
        if facts:
            context_parts.append("FACTS:")
            for fact in facts[:5]:  # Top 5 facts
                context_parts.append(f"- {fact['key']}: {fact['value']} (confidence: {fact['confidence']:.2f})")
        
        if episodes:
            context_parts.append("\nEPISODES:")
            for episode in episodes[:3]:  # Top 3 episodes
                context_parts.append(f"- {episode['text'][:100]}...")
        
        if graph_hits:
            context_parts.append("\nGRAPH PATHS:")
            for hit in graph_hits[:2]:  # Top 2 paths
                context_parts.append(f"- {hit['path']} (length: {hit['length']})")
        
        context_text = "\n".join(context_parts)
        
        system_prompt = """
        Create a concise 120-word context card that summarizes the relevant information for the user's query.
        Include key facts, important episodes, and reasoning paths.
        Be specific and actionable.
        """
        
        user_prompt = f"Query: {query}\n\nContext:\n{context_text}"
        
        try:
            return self.bedrock.claude_complete(system_prompt, user_prompt)
        except:
            return f"Context: {context_text[:200]}..."
```

## API Implementation

### FastAPI Routes (`app/api/routes.py`)

```python
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time

app = FastAPI(title="MemoryGraph API", version="1.0.0")

# Pydantic models
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

class MemorySummarizeRequest(BaseModel):
    guid: str
    since_days: int = 7

class MemoryForgetRequest(BaseModel):
    guid: str
    keys: Optional[List[str]] = None
    entities: Optional[List[str]] = None
    predicates: Optional[List[str]] = None
    hard_delete: bool = False

@app.get("/health")
async def health_check():
    """Health check with Bedrock self-test."""
    try:
        from ..core.bedrock import bedrock_client
        from ..core.config import settings
        
        # Test Titan embedding
        test_embedding = bedrock_client.titan_embed(["hello"])
        vector_length = len(test_embedding[0]) if test_embedding else 0
        
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "bedrock_test": {
                "titan_embedding_length": vector_length,
                "status": "success" if vector_length > 0 else "failed"
            },
            "services": {
                "api": "running",
                "bedrock": "connected" if vector_length > 0 else "disconnected"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.post("/memory/write")
async def write_memory(request: MemoryWriteRequest):
    """Write new memory."""
    try:
        from ..memory.service import memory_service
        
        result = memory_service.write_memory({
            "guid": request.guid,
            "text": request.text,
            "channel": request.channel,
            "ts": request.ts,
            "thread_id": request.thread_id
        })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/search")
async def search_memory(request: MemorySearchRequest):
    """Search memories."""
    try:
        from ..memory.service import memory_service
        
        result = memory_service.search_memory({
            "guid": request.guid,
            "query": request.query,
            "k": request.k,
            "since_days": request.since_days,
            "include_graph": request.include_graph
        })
        
        return result
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
async def get_subgraph(guid: str = Query(..., description="User GUID")):
    """Get user's knowledge graph."""
    try:
        from ..stores.graph_neo4j import get_graph_store
        nodes = get_graph_store().get_subgraph(guid)
        return {
            "success": True,
            "nodes": nodes,
            "count": len(nodes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/paths")
async def get_graph_paths(guid: str = Query(..., description="User GUID"), 
                         topic: str = Query(..., description="Topic to find paths to")):
    """Find paths from user to topic."""
    try:
        from ..stores.graph_neo4j import get_graph_store
        paths = get_graph_store().find_paths(guid, topic)
        return {
            "success": True,
            "paths": paths,
            "count": len(paths)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## A/B Testing Framework

### A/B Relay (`ab_relay.py`)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import requests
import time
import json

app = FastAPI(title="A/B Testing Relay")

class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    guid: str
    memory_on: bool

class ToggleRequest(BaseModel):
    on: bool

class ABRelay:
    def __init__(self):
        self.memory_enabled = True
        self.api_base = "http://localhost:8000"
        self.mcp_base = "http://localhost:8002"

    async def chat_with_memory(self, request: ChatRequest) -> Dict[str, Any]:
        """Handle chat with memory enabled."""
        start_time = time.time()
        tools_invoked = []
        context_card = ""
        graph_hits = []
        
        try:
            # Get last user message
            user_message = None
            for msg in reversed(request.messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            if not user_message:
                raise ValueError("No user message found")
            
            # Search memory
            memory_response = requests.post(f"{self.api_base}/memory/search", json={
                "guid": request.guid,
                "query": user_message,
                "k": 8,
                "since_days": 30,
                "include_graph": True
            })
            
            if memory_response.status_code == 200:
                memory_data = memory_response.json()
                context_card = memory_data.get("context_card", "")
                graph_hits = memory_data.get("graph_hits", [])
                tools_invoked.append("memory.search")
            
            # Prepare messages with context
            messages = request.messages.copy()
            if context_card:
                messages.insert(0, {
                    "role": "system",
                    "content": f"CONTEXT CARD:\n{context_card}"
                })
            
            # Call Claude via Bedrock
            from app.core.bedrock import bedrock_client
            
            system_prompt = "You are a helpful AI assistant with access to the user's memory and context."
            user_prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
            
            response = bedrock_client.claude_complete(system_prompt, user_prompt)
            tools_invoked.append("bedrock.claude")
            
            duration = time.time() - start_time
            
            return {
                "response": response,
                "memory_used": True,
                "tools_invoked": tools_invoked,
                "duration": duration,
                "context_card": context_card,
                "graph_hits": graph_hits
            }
            
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "memory_used": False,
                "tools_invoked": tools_invoked,
                "duration": time.time() - start_time,
                "context_card": "",
                "graph_hits": []
            }

    async def chat_without_memory(self, request: ChatRequest) -> Dict[str, Any]:
        """Handle chat without memory."""
        start_time = time.time()
        
        try:
            from app.core.bedrock import bedrock_client
            
            system_prompt = "You are a helpful AI assistant."
            user_prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in request.messages])
            
            response = bedrock_client.claude_complete(system_prompt, user_prompt)
            
            duration = time.time() - start_time
            
            return {
                "response": response,
                "memory_used": False,
                "tools_invoked": ["bedrock.claude"],
                "duration": duration,
                "context_card": "",
                "graph_hits": []
            }
            
        except Exception as e:
            return {
                "response": f"Error: {str(e)}",
                "memory_used": False,
                "tools_invoked": [],
                "duration": time.time() - start_time,
                "context_card": "",
                "graph_hits": []
            }

relay = ABRelay()

@app.post("/chat")
async def chat(request: ChatRequest):
    """Handle chat requests with A/B testing."""
    if request.memory_on and relay.memory_enabled:
        return await relay.chat_with_memory(request)
    else:
        return await relay.chat_without_memory(request)

@app.post("/toggle")
async def toggle_memory(request: ToggleRequest):
    """Toggle memory context on/off."""
    relay.memory_enabled = request.on
    return {
        "success": True,
        "memory_enabled": relay.memory_enabled,
        "message": f"Memory context {'enabled' if request.on else 'disabled'}"
    }

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "memory_enabled": relay.memory_enabled,
        "timestamp": time.time()
    }
```

## Performance Optimizations

### 1. Caching Strategy
- **Bedrock Responses**: Cache repeated queries
- **Embeddings**: Cache computed embeddings
- **Graph Queries**: Cache common path queries

### 2. Batch Operations
- **Fact Upserts**: Batch multiple facts
- **Entity Creation**: Batch entity operations
- **Embedding Generation**: Process multiple texts together

### 3. Lazy Loading
- **Graph Store**: Initialize only when needed
- **Database Connections**: Connect on demand
- **Model Loading**: Load models when required

### 4. Error Handling
- **Retry Logic**: Exponential backoff for API calls
- **Graceful Degradation**: Fallback to simpler operations
- **Circuit Breakers**: Prevent cascade failures

## Error Handling

### 1. Database Errors
```python
try:
    # Database operation
    result = database_operation()
except DatabaseError as e:
    logger.error(f"Database error: {e}")
    return {"success": False, "error": "Database operation failed"}
```

### 2. API Errors
```python
try:
    # API call
    response = api_call()
except APIError as e:
    logger.error(f"API error: {e}")
    return {"success": False, "error": "API call failed"}
```

### 3. Validation Errors
```python
try:
    # Validation
    validated_data = validate_input(data)
except ValidationError as e:
    logger.error(f"Validation error: {e}")
    return {"success": False, "error": "Invalid input data"}
```

This technical implementation guide provides detailed insights into how each component of the MemoryGraph system works, including code examples, error handling strategies, and performance optimizations. The system is designed to be modular, scalable, and maintainable while providing robust AI memory capabilities.
