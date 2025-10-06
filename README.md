# Bedrock-powered Graph + Memory POC

A proof-of-concept system for graph-based memory management powered by AWS Bedrock, featuring semantic search, entity extraction, and knowledge graph construction.

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

- Python 3.8+
- AWS credentials with Bedrock access
- Neo4j database (local or Docker)
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd mind-map
   ```

2. **Install dependencies**:
   ```bash
   make install
   # or
   pip install -e .
   ```

3. **Configure environment**:
   ```bash
   cp env.sample .env
   # Edit .env with your actual configuration values
   ```

4. **Start Neo4j** (using Docker):
   ```bash
   make setup-neo4j
   ```

5. **Run the demo**:
   ```bash
   make demo-on
   ```

### Manual Setup

If you prefer manual setup:

1. **Start Neo4j**:
   ```bash
   docker run -d --name neo4j-memory \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/password \
     neo4j:latest
   ```

2. **Start the API server**:
   ```bash
   make run-api
   ```

3. **Seed demo data**:
   ```bash
   make seed
   ```

4. **Start the UI**:
   ```bash
   make run-ui
   ```

## 📁 Project Structure

```
mind-map/
├── app/                    # Main application code
│   ├── core/              # Core configuration and Bedrock integration
│   ├── stores/            # Storage layer (SQLite, ChromaDB, Neo4j)
│   ├── memory/            # Memory processing (extractor, retrieval, service)
│   └── api/               # FastAPI routes and endpoints
├── orchestrator/          # CLI orchestrator for testing
├── ui/                    # Streamlit web interface
├── scripts/               # Utility scripts and demo data
├── ab_relay.py           # A/B testing relay
├── mcp_server.py         # MCP (Model Context Protocol) server
├── pyproject.toml        # Project configuration and dependencies
├── Makefile              # Build and run commands
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
NEO4J_PASSWORD=password

# Database
DB_URL=sqlite:///./memory.db

# API
API_HOST=0.0.0.0
API_PORT=8000
```

## 🎯 Features

### Memory Management
- **Text Processing**: Extract entities and relationships from text
- **Semantic Search**: Find relevant memories using vector similarity
- **Entity Extraction**: Identify people, organizations, locations, concepts, and events
- **Graph Construction**: Build knowledge graphs from extracted entities

### Storage Systems
- **SQLite**: Persistent key-value storage for memory data
- **ChromaDB**: Vector embeddings for semantic search
- **Neo4j**: Graph database for relationship modeling

### User Interfaces
- **REST API**: Full programmatic access to all features
- **Web UI**: Interactive Streamlit interface for exploration
- **CLI**: Command-line tool for testing and automation

### Advanced Features
- **A/B Testing**: Compare different search strategies
- **MCP Integration**: Model Context Protocol server for AI tool integration
- **Insights Generation**: AI-powered analysis of stored memories

## 📚 API Reference

### Core Endpoints

- `GET /health` - Health check
- `POST /memories` - Add a new memory
- `POST /search` - Search memories
- `GET /memories/{id}` - Get specific memory
- `GET /entities/{name}` - Get entity context
- `GET /timeline` - Get memory timeline
- `POST /insights` - Generate insights

### Example Usage

```python
import requests

# Add a memory
response = requests.post("http://localhost:8000/memories", json={
    "text": "I'm working on a new AI project using AWS Bedrock",
    "source": "conversation",
    "metadata": {"priority": "high", "tags": ["ai", "aws", "project"]}
})

# Search memories
response = requests.post("http://localhost:8000/search", json={
    "query": "AI project",
    "search_type": "semantic",
    "limit": 5
})
```

## 🧪 Testing

Run the test suite:

```bash
make test
```

Run with coverage:

```bash
make test-coverage
```

## 🛠️ Development

### Code Quality

Format code:
```bash
make format
```

Run linting:
```bash
make lint
```

### Adding New Features

1. **Memory Types**: Extend `MemoryExtractor` for new content types
2. **Search Strategies**: Add new search methods to `MemoryRetriever`
3. **API Endpoints**: Add new routes to `routes.py`
4. **UI Components**: Extend the Streamlit interface

## 🐳 Docker Support

Build and run with Docker:

```bash
make docker-build
make docker-run
```

## 📊 Monitoring

Check system health:

```bash
make health-check
```

View system statistics:

```bash
curl http://localhost:8000/stats
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

1. Check the [demo run guide](scripts/demo_run.md)
2. Review the API documentation at `http://localhost:8000/docs`
3. Open an issue on GitHub

## 🔮 Roadmap

- [ ] Multi-modal memory support (images, audio)
- [ ] Real-time memory updates
- [ ] Advanced graph algorithms
- [ ] Memory versioning and history
- [ ] Integration with more AI models
- [ ] Distributed deployment support
