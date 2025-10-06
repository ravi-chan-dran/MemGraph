# MemoryGraph - Bedrock-powered Graph + Memory POC

A comprehensive A/B testing system for graph-based memory management powered by AWS Bedrock, featuring semantic search, entity extraction, knowledge graph construction, and intelligent memory retrieval with context injection.

## 🏗️ Architecture

This system combines multiple storage and processing layers:

- **AWS Bedrock**: Claude for text generation and entity extraction, Titan for embeddings
- **Neo4j**: Graph database for relationship modeling and entity connections
- **ChromaDB**: Vector database for semantic search and similarity matching
- **SQLite**: Key-value store for memory persistence and metadata
- **FastAPI**: REST API for system integration
- **Streamlit**: Web UI for interactive exploration

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (required for latest dependencies)
- **Docker** (for Neo4j database)
- **AWS credentials** with Bedrock access
- **Git**

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd mind-map
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   make install
   # or
   pip install -e .
   ```

4. **Configure environment**:
   ```bash
   cp env.sample .env
   # Edit .env with your AWS credentials and configuration
   ```

5. **Start Neo4j** (using Docker):
   ```bash
   make setup-neo4j
   ```

6. **Verify setup**:
   ```bash
   # Test Neo4j connection
   curl -u neo4j:test123456 http://localhost:7474
   
   # Test API health
   make run-api &
   curl http://localhost:8000/health
   ```

7. **Run the complete demo**:
   ```bash
   make demo-on
   ```

### Manual Setup

If you prefer manual setup:

1. **Start Neo4j**:
   ```bash
   docker run -d --name neo4j-memory \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/test123456 \
     neo4j:latest
   ```

2. **Start all services** (in separate terminals):
   ```bash
   # Terminal 1: API Server
   make run-api
   
   # Terminal 2: MCP Server  
   make run-mcp
   
   # Terminal 3: A/B Relay
   make run-relay
   
   # Terminal 4: Seed demo data
   make seed
   
   # Terminal 5: Streamlit UI
   make run-ui
   ```

3. **Access the services**:
   - **API**: http://localhost:8000/docs
   - **A/B Relay**: http://localhost:8001
   - **MCP Server**: http://localhost:8002
   - **Streamlit UI**: http://localhost:8501
   - **Neo4j Browser**: http://localhost:7474

## 📁 Project Structure

```
mind-map/
├── app/                    # Main application code
│   ├── core/              # Core configuration and Bedrock integration
│   │   ├── config.py      # Settings and environment management
│   │   └── bedrock.py     # AWS Bedrock client (Claude + Titan)
│   ├── stores/            # Storage layer implementations
│   │   ├── kv_sqlite.py   # SQLite key-value store
│   │   ├── vector_chroma.py # ChromaDB vector store
│   │   └── graph_neo4j.py # Neo4j graph database
│   ├── memory/            # Memory processing pipeline
│   │   ├── extractor.py   # Entity and fact extraction
│   │   ├── retrieval.py   # Memory search and scoring
│   │   └── service.py     # High-level memory operations
│   └── api/               # FastAPI routes and endpoints
│       └── routes.py      # REST API implementation
├── orchestrator/          # CLI orchestrator for testing
│   └── mock_cli.py       # Command-line interface
├── ui/                    # Streamlit web interface
│   └── streamlit_app.py  # A/B testing demo UI
├── scripts/               # Utility scripts and demo data
│   ├── seed_demo.py      # Demo data seeding
│   └── demo_run.md       # A/B test scenarios
├── docs/                  # Documentation
│   └── quickstart.md     # Detailed setup guide
├── ab_relay.py           # A/B testing relay service
├── mcp_server.py         # MCP (Model Context Protocol) server
├── pyproject.toml        # Project configuration and dependencies
├── Makefile              # Build and run commands
├── env.sample            # Environment configuration template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

## 🔧 Configuration

The system uses environment variables for configuration. Copy `env.sample` to `.env` and adjust:

```bash
# AWS Bedrock
AWS_REGION=us-east-1
BEDROCK_CLAUDE_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_TITAN_EMB_MODEL_ID=amazon.titan-embed-text-v1

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=test123456

# Database
DB_URL=sqlite:///./memory.db

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## 🎯 Features

### 🧠 Memory Management
- **Intelligent Extraction**: Extract structured facts, entities, and relationships using Claude
- **Semantic Search**: Find relevant memories using Titan embeddings and vector similarity
- **Entity Recognition**: Identify people, organizations, locations, concepts, and events
- **Graph Construction**: Build knowledge graphs with relationship modeling
- **Context Injection**: Automatically inject relevant context into AI conversations

### 💾 Storage Systems
- **SQLite**: Persistent key-value storage for facts and metadata
- **ChromaDB**: Vector embeddings for semantic search and similarity matching
- **Neo4j**: Graph database for relationship modeling and path finding

### 🖥️ User Interfaces
- **REST API**: Full programmatic access to all memory operations
- **Streamlit UI**: Interactive A/B testing interface with real-time visualization
- **MCP Server**: Model Context Protocol integration for AI tools
- **A/B Relay**: Intelligent routing between memory-enabled and memory-disabled responses

### 🧪 A/B Testing Framework
- **Memory Toggle**: Compare responses with and without memory context
- **Context Cards**: Generate concise 120-word context summaries
- **Graph Visualization**: Interactive network graphs showing relationships
- **Performance Metrics**: Track response times, accuracy, and context quality

### 🔧 Advanced Features
- **Retry/Backoff**: Robust AWS Bedrock API integration with exponential backoff
- **Chunking**: Handle large inputs with intelligent text chunking
- **Confidence Filtering**: Filter low-confidence extractions automatically
- **Lazy Loading**: Optimized initialization to prevent connection issues

## 📚 API Reference

### Core Memory Endpoints

- `GET /health` - Health check with Bedrock connectivity test
- `POST /memory/write` - Write memory data to all stores
- `POST /memory/search` - Search memories with context generation
- `POST /memory/summarize` - Generate memory summaries
- `POST /memory/forget` - Delete specific memories

### Graph Endpoints

- `GET /graph/subgraph` - Get user's subgraph
- `GET /graph/paths` - Find paths between user and topic

### A/B Testing Endpoints

- `POST /chat` - A/B testing chat endpoint (memory ON/OFF)
- `POST /toggle` - Toggle memory system on/off
- `GET /health` - Relay health check

### MCP Server Endpoints

- `POST /memory/write` - MCP memory write tool
- `POST /memory/search` - MCP memory search tool
- `POST /memory/forget` - MCP memory forget tool
- `POST /memory/summarize` - MCP memory summarize tool
- `POST /memory/explain` - MCP memory explain tool

### Example Usage

```python
import requests

# Write a memory
response = requests.post("http://localhost:8000/memory/write", json={
    "guid": "user123",
    "text": "I'm working on a new AI project using AWS Bedrock",
    "channel": "conversation",
    "ts": "2024-01-01T12:00:00Z"
})

# Search memories
response = requests.post("http://localhost:8000/memory/search", json={
    "guid": "user123",
    "query": "AI project",
    "k": 5,
    "since_days": 30,
    "include_graph": True
})

# A/B test chat
response = requests.post("http://localhost:8001/chat", json={
    "model": "claude",
    "messages": [{"role": "user", "content": "What do you know about my AI project?"}],
    "guid": "user123",
    "memory_on": True
})
```

## 🧪 A/B Testing Demo

The system includes a comprehensive A/B testing framework to demonstrate the value of memory integration:

### Demo Scenarios

1. **Match Formula Query**: "What is the match formula?" (finds safe harbor info)
2. **Payroll Processing**: "When is payroll processed?" (finds bi-weekly info)  
3. **Auto-enrollment**: "What is the auto-enrollment rate?" (finds 6% info)
4. **Communications**: "When are employee communications?" (finds July/December info)
5. **Forget & Re-ask**: Forget match formula, then re-ask to see difference

### Running the Demo

```bash
# Start all services
make demo-on

# Or manually:
make run-api    # Terminal 1
make run-mcp    # Terminal 2  
make run-relay  # Terminal 3
make seed       # Terminal 4
make run-ui     # Terminal 5
```

### Expected Results

- **Memory ON**: Contextual responses with facts, episodes, graph paths
- **Memory OFF**: Generic responses without specific context
- **Evidence Panel**: Shows context cards and graph visualizations
- **Performance**: Response time, accuracy, and context quality metrics

### Testing Commands

```bash
# Run unit tests
make test

# Run with coverage
make test-coverage

# Health check all services
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## 🛠️ Development

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Type checking
make type-check
```

### Adding New Features

1. **Memory Types**: Extend `MemoryExtractor` for new content types
2. **Search Strategies**: Add new search methods to `MemoryRetriever`
3. **API Endpoints**: Add new routes to `routes.py`
4. **UI Components**: Extend the Streamlit interface
5. **A/B Tests**: Add new test scenarios to `scripts/demo_run.md`

### Architecture Notes

- **Lazy Loading**: Graph store uses lazy initialization to prevent connection issues
- **Retry Logic**: All Bedrock API calls include exponential backoff
- **Chunking**: Large texts are automatically chunked for embedding models
- **Confidence Filtering**: Low-confidence extractions are automatically filtered

## 🐳 Docker Support

The system uses Docker for Neo4j database:

```bash
# Start Neo4j
make setup-neo4j

# Stop Neo4j
make stop-neo4j

# Check Neo4j status
docker ps | grep neo4j
```

## 📊 Monitoring

### Health Checks

```bash
# API Server
curl http://localhost:8000/health

# A/B Relay
curl http://localhost:8001/health

# MCP Server
curl http://localhost:8002/health

# Neo4j
curl -u neo4j:test123456 http://localhost:7474
```

### System Statistics

```bash
# View API stats
curl http://localhost:8000/stats

# Check Neo4j browser
open http://localhost:7474
```

### Logs

```bash
# Neo4j logs
docker logs neo4j-memory

# API logs (when running)
tail -f logs/api.log
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- AWS Bedrock for AI model access
- Neo4j for graph database capabilities
- ChromaDB for vector storage
- FastAPI for the web framework
- Streamlit for the UI framework

## 📞 Support

For questions or issues:

1. Check the [quickstart guide](docs/quickstart.md)
2. Review the [demo run scenarios](scripts/demo_run.md)
3. Check the API documentation at `http://localhost:8000/docs`
4. Open an issue on GitHub

## 🔮 Roadmap

- [ ] Multi-modal memory support (images, audio)
- [ ] Real-time memory updates via WebSockets
- [ ] Advanced graph algorithms (PageRank, community detection)
- [ ] Memory versioning and history tracking
- [ ] Integration with more AI models (GPT-4, Gemini)
- [ ] Distributed deployment support
- [ ] Memory sharing between users
- [ ] Advanced A/B testing metrics and analytics

## 🎉 Success!

If you've successfully set up MemoryGraph, you should now have:

✅ **Working Neo4j database** with proper authentication  
✅ **Functional API server** with Bedrock integration  
✅ **A/B testing relay** for memory comparison  
✅ **MCP server** for AI tool integration  
✅ **Streamlit UI** for interactive demos  
✅ **Demo data** seeded for testing  

**Next Steps:**
1. Open http://localhost:8501 for the Streamlit UI
2. Try the A/B test scenarios in the demo
3. Explore the API documentation at http://localhost:8000/docs
4. Check the Neo4j browser at http://localhost:7474
