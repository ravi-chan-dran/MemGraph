# MemoryGraph: AI with Persistent Memory - Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Data Flow](#data-flow)
4. [Storage Architecture](#storage-architecture)
5. [Memory Types](#memory-types)
6. [Graph Database Design](#graph-database-design)
7. [API Design](#api-design)
8. [Security & Privacy](#security--privacy)
9. [Performance Considerations](#performance-considerations)
10. [Deployment Architecture](#deployment-architecture)

## System Overview

MemoryGraph is a production-ready AI system that provides persistent memory capabilities to Large Language Models (LLMs). The system enables AI to learn, remember, and reason about information across multiple interactions, creating a more human-like AI experience.

### Core Principles
- **Persistent Memory**: AI retains information across sessions
- **Multi-Modal Storage**: Facts, episodes, and graph relationships
- **Transparent Reasoning**: AI shows how it reaches conclusions
- **Selective Forgetting**: Users control what AI remembers
- **Real-Time Learning**: AI learns from new interactions immediately

## Architecture Components

### 1. Core Services

#### Bedrock Integration (`app/core/`)
- **`config.py`**: Environment configuration and settings management
- **`bedrock.py`**: AWS Bedrock client with retry/backoff and chunking

#### Memory System (`app/memory/`)
- **`extractor.py`**: Information extraction from text using Claude
- **`retrieval.py`**: Memory scoring and ranking algorithms
- **`service.py`**: Orchestrates memory operations

#### Storage Layer (`app/stores/`)
- **`kv_sqlite.py`**: Key-value storage for facts
- **`vector_chroma.py`**: Vector storage for episodic memories
- **`graph_neo4j.py`**: Graph database for relationships

#### API Layer (`app/api/`)
- **`routes.py`**: FastAPI endpoints for memory operations

### 2. External Services

#### A/B Testing Relay (`ab_relay.py`)
- Compares AI responses with and without memory
- Injects context cards into AI prompts
- Measures performance differences

#### MCP Server (`mcp_server.py`)
- Model Context Protocol implementation
- Exposes memory tools to external systems
- Bearer token authentication

#### Streamlit UI (`ui/streamlit_app_improved.py`)
- Interactive web interface
- Real-time memory visualization
- Graph network visualization

## Data Flow

### 1. Memory Writing Flow
```
User Input → Memory Extractor → Multi-Store Write
    ↓              ↓                    ↓
Text/Channel → Facts/Episodes → SQLite/Chroma/Neo4j
    ↓              ↓                    ↓
Timestamp → Entities/Triples → Graph Relationships
```

### 2. Memory Retrieval Flow
```
Query → Vector Search → Fact Lookup → Graph Query
  ↓         ↓              ↓            ↓
Embedding → Episodes → Facts → Relationships
  ↓         ↓              ↓            ↓
Scoring → Ranking → Context Card → AI Response
```

### 3. A/B Testing Flow
```
User Query → Memory Search → Context Injection → Model Response
    ↓              ↓              ↓                ↓
Memory ON → Facts/Episodes → System Prompt → Enhanced Answer
Memory OFF → No Context → Direct Query → Generic Answer
```

## Storage Architecture

### 1. SQLite (Facts Storage)
```sql
CREATE TABLE facts (
    guid TEXT,
    key TEXT,
    value TEXT,
    confidence REAL,
    source TEXT,
    ts TEXT,
    PRIMARY KEY(guid, key)
);
```

**Purpose**: Store structured facts with confidence scores
**Characteristics**: ACID compliance, fast lookups, embedded database

### 2. ChromaDB (Episodic Memory)
```python
Collection: "episodes_mem"
Metadata: {
    "guid": str,
    "timestamp": str,
    "channel": str,
    "importance": float,
    "tags": list
}
```

**Purpose**: Store and retrieve episodic memories using vector similarity
**Characteristics**: Persistent storage, semantic search, metadata filtering

### 3. Neo4j (Graph Database)
```cypher
(:User {guid: "plan_sponsor_acme"})
(:Fact {key: "match_formula", value: "100% of first 3%", confidence: 1.0})
(:Entity {name: "retirement_plan", type: "Policy"})
(:User)-[:HAS_FACT]->(:Fact)
(:Entity)-[:RELATED_TO]->(:Fact)
```

**Purpose**: Store relationships between entities and facts
**Characteristics**: Graph queries, relationship traversal, constraint enforcement

## Memory Types

### 1. Factual Memory (SQLite)
- **Structure**: Key-value pairs with confidence scores
- **Extraction**: Claude extracts structured facts from text
- **Retrieval**: Direct lookup by GUID and key
- **Example**: `{"key": "match_formula", "value": "100% of first 3%", "confidence": 1.0}`

### 2. Episodic Memory (ChromaDB)
- **Structure**: Text summaries with embeddings
- **Extraction**: Claude creates episode summaries
- **Retrieval**: Vector similarity search
- **Example**: `"Employee education sessions on contribution limits and vesting schedules"`

### 3. Graph Memory (Neo4j)
- **Structure**: Nodes and relationships
- **Extraction**: Claude extracts entities and triples
- **Retrieval**: Graph traversal and path finding
- **Example**: `User -> HAS_FACT -> match_formula -> RELATED_TO -> retirement_policy`

## Graph Database Design

### Node Types
1. **User**: `{guid: str, created_at: timestamp}`
2. **Fact**: `{key: str, value: str, confidence: float, source: str, ts: timestamp}`
3. **Entity**: `{name: str, type: str, aliases: list}`
4. **Episode**: `{summary: str, importance: float, tags: list}`

### Relationship Types
1. **HAS_FACT**: User → Fact
2. **HAS_EPISODE**: User → Episode
3. **RELATED_TO**: Entity → Entity
4. **MENTIONS**: Episode → Entity
5. **HAS_FORMULA**: Entity → Fact
6. **SCHEDULED_FOR**: Event → Date

### Constraints
```cypher
CREATE CONSTRAINT user_guid_unique FOR (u:User) REQUIRE u.guid IS UNIQUE;
CREATE CONSTRAINT entity_key_unique FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE;
CREATE CONSTRAINT fact_key_unique FOR (f:Fact) REQUIRE (f.key, f.guid) IS UNIQUE;
```

## API Design

### Memory Operations
- `POST /memory/write`: Store new memories
- `POST /memory/search`: Search memories with ranking
- `POST /memory/summarize`: Generate memory summaries
- `POST /memory/forget`: Delete specific memories

### Graph Operations
- `GET /graph/subgraph`: Get user's knowledge graph
- `GET /graph/paths`: Find paths between entities
- `GET /graph/entities`: List all entities

### A/B Testing
- `POST /chat`: Compare memory vs no-memory responses
- `POST /toggle`: Enable/disable memory context
- `GET /health`: Service health check

## Security & Privacy

### Authentication
- **MCP Server**: Bearer token authentication
- **API Endpoints**: No authentication (demo purposes)
- **Production**: JWT tokens or OAuth2

### Data Privacy
- **Selective Forgetting**: Users can delete specific memories
- **Data Isolation**: Each user has separate GUID
- **Confidence Filtering**: Low-confidence data is filtered out
- **Source Tracking**: All data includes source attribution

### Data Retention
- **Facts**: Persistent until explicitly deleted
- **Episodes**: Can be marked as redacted
- **Graph**: Relationships can be soft-deleted

## Performance Considerations

### Caching Strategy
- **Bedrock Responses**: Cached for repeated queries
- **Embeddings**: Cached to avoid recomputation
- **Graph Queries**: Results cached for common patterns

### Optimization Techniques
- **Chunking**: Large texts split for embedding models
- **Retry Logic**: Exponential backoff for API calls
- **Lazy Loading**: Graph store initialized on demand
- **Batch Operations**: Multiple facts written in batches

### Scalability
- **Horizontal Scaling**: Stateless API services
- **Database Sharding**: By user GUID
- **CDN**: Static assets and UI components
- **Load Balancing**: Multiple API instances

## Deployment Architecture

### Development Environment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   FastAPI API   │    │   A/B Relay     │
│   Port: 8501    │    │   Port: 8000    │    │   Port: 8001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SQLite DB     │    │   ChromaDB      │    │   Neo4j         │
│   memory.db     │    │   chroma_db/    │    │   Port: 7474    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Production Environment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   API Gateway   │    │   CDN           │
│   (nginx)       │    │   (Kong/AWS)    │    │   (CloudFront)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Services  │    │   MCP Server    │    │   A/B Relay     │
│   (ECS/K8s)     │    │   (Lambda)      │    │   (ECS/K8s)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RDS PostgreSQL│    │   OpenSearch    │    │   Neptune       │
│   (Facts)       │    │   (Vectors)     │    │   (Graph)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Technology Stack

### Backend
- **Python 3.11+**: Core language
- **FastAPI**: API framework
- **Pydantic**: Data validation
- **SQLAlchemy**: ORM (future)
- **Boto3**: AWS SDK

### Databases
- **SQLite**: Facts storage (dev)
- **PostgreSQL**: Facts storage (prod)
- **ChromaDB**: Vector storage
- **Neo4j**: Graph database

### AI/ML
- **AWS Bedrock**: Claude and Titan models
- **NumPy**: Numerical operations
- **NetworkX**: Graph algorithms
- **Pyvis**: Graph visualization

### Frontend
- **Streamlit**: Web interface
- **HTML/CSS/JS**: Custom components
- **Pyvis**: Interactive graphs

### Infrastructure
- **Docker**: Containerization
- **Make**: Build automation
- **Git**: Version control
- **AWS**: Cloud services

## Future Enhancements

### Short Term
- **Authentication**: JWT/OAuth2 integration
- **Rate Limiting**: API throttling
- **Monitoring**: Prometheus/Grafana
- **Logging**: Structured logging

### Medium Term
- **Multi-tenancy**: Organization-level isolation
- **Advanced Analytics**: Memory usage patterns
- **API Versioning**: Backward compatibility
- **Performance Optimization**: Query optimization

### Long Term
- **Federated Learning**: Cross-organization learning
- **Advanced Reasoning**: Causal inference
- **Real-time Streaming**: Live memory updates
- **Mobile Apps**: Native mobile interfaces

## Conclusion

MemoryGraph represents a significant advancement in AI capabilities, providing persistent memory that enables more human-like interactions. The architecture is designed for scalability, maintainability, and extensibility, with clear separation of concerns and robust error handling.

The system demonstrates how AI can be enhanced with memory capabilities while maintaining transparency, control, and performance. This foundation enables a wide range of applications in customer service, knowledge management, and intelligent automation.
