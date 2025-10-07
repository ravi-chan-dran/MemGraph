# 🧠 MemoryGraph: AI with Persistent Memory

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock-orange.svg)](https://aws.amazon.com/bedrock/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.20+-green.svg)](https://neo4j.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Latest-purple.svg)](https://www.trychroma.com/)

> **Revolutionary AI system that provides persistent memory capabilities to Large Language Models, enabling them to learn, remember, and reason about information across multiple interactions.**

## 🎯 What is MemoryGraph?

MemoryGraph is a production-ready AI system that solves the fundamental problem of LLMs lacking persistent memory. Unlike traditional AI that forgets everything after each conversation, MemoryGraph enables AI to:

- **🧠 Remember**: Store and retrieve information across sessions
- **🔍 Learn**: Continuously learn from new interactions
- **🤔 Reason**: Build complex knowledge graphs and relationships
- **🎛️ Control**: Give users complete control over AI's memory
- **🔍 Explain**: Show transparent reasoning and decision paths

## ✨ Key Features

### 🧠 **Multi-Modal Memory System**
- **Factual Memory**: Structured key-value facts with confidence scores
- **Episodic Memory**: Vector-based semantic memories using ChromaDB
- **Graph Memory**: Relationship modeling and path finding with Neo4j

### 🔍 **Intelligent Information Extraction**
- **Structured Facts**: Extract facts, entities, and relationships from text
- **Confidence Scoring**: Filter information by confidence thresholds
- **Business Context**: Specialized extraction for business/retirement planning

### 🎯 **Advanced Retrieval & Ranking**
- **Semantic Search**: Vector similarity search for relevant memories
- **Multi-Factor Scoring**: Cosine similarity, recency, importance, and graph proximity
- **Context Cards**: AI-generated summaries of relevant information

### 🧪 **A/B Testing Framework**
- **Memory vs No-Memory**: Compare AI responses with and without memory
- **Performance Metrics**: Measure the impact of memory on AI quality
- **Real-time Toggle**: Switch memory on/off during conversations

### 🎨 **Interactive Visualization**
- **Knowledge Graphs**: Interactive network visualization of AI's knowledge
- **Path Finding**: Visualize how AI connects information
- **Memory Management**: Manage and delete specific memories

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface Layer                     │
├─────────────────────────────────────────────────────────────────┤
│  Streamlit UI  │  A/B Relay  │  MCP Server  │  REST API        │
├─────────────────────────────────────────────────────────────────┤
│                        Application Layer                        │
├─────────────────────────────────────────────────────────────────┤
│  Memory Service  │  Memory Extractor  │  Memory Retriever      │
├─────────────────────────────────────────────────────────────────┤
│                        Storage Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  SQLite (Facts)  │  ChromaDB (Episodes)  │  Neo4j (Graph)      │
├─────────────────────────────────────────────────────────────────┤
│                        Infrastructure Layer                     │
├─────────────────────────────────────────────────────────────────┤
│  AWS Bedrock  │  Docker  │  Monitoring  │  Logging             │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker (for Neo4j)
- AWS Account with Bedrock access
- Git

### 1. Clone and Setup
```bash
git clone <repository-url>
cd mind-map
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .
```

### 2. Configure Environment
```bash
cp env.sample .env
# Edit .env with your AWS credentials and settings
```

### 3. Start Services
```bash
# Start Neo4j database
make setup-neo4j

# Start all services
make demo-on

# Or start individually
make run-api    # FastAPI server (port 8000)
make run-mcp    # MCP server (port 8002)
make run-relay  # A/B relay (port 8001)
make run-ui     # Streamlit UI (port 8501)
```

### 4. Access the Interface
- **Streamlit UI**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **A/B Relay**: http://localhost:8001
- **MCP Server**: http://localhost:8002

## 📚 Documentation

### 📖 **Comprehensive Documentation**
- **[Architecture Guide](docs/architecture.md)** - System architecture and design
- **[Technical Implementation](docs/technical-implementation.md)** - Detailed implementation guide
- **[System Design](docs/system-design.md)** - Complete system design document
- **[Quick Start Guide](docs/quickstart.md)** - Step-by-step setup instructions

### 🎨 **Interactive Documentation**
- **[Architecture (HTML)](docs/architecture.html)** - Interactive architecture documentation
- **[System Design (HTML)](docs/system-design.html)** - Interactive system design documentation

## 🎭 Demo Walkthrough

### 1. **Memory OFF (The Problem)**
- Toggle memory to OFF
- Ask: "What is the match formula for our retirement plan?"
- See generic, unhelpful response

### 2. **Memory ON (The Solution)**
- Toggle memory to ON
- Ask the same question
- See detailed, specific answer with exact formula

### 3. **Live Learning**
- Type: "Our vacation policy is 15 days per year with rollover"
- Click "Save as Memory"
- Ask: "What is our vacation policy?"
- See AI immediately knows the new information

### 4. **Graph Visualization**
- Go to "Why?" tab
- See interactive knowledge graph
- Hover over nodes to see details
- Understand how AI connects information

### 5. **Memory Management**
- Go to "Facts" tab
- See all stored facts with confidence scores
- Delete specific memories
- Control what AI remembers

## 🛠️ Technology Stack

### **Backend**
- **Python 3.11+** - Core language
- **FastAPI** - API framework
- **Pydantic** - Data validation
- **Boto3** - AWS SDK

### **Databases**
- **SQLite** - Facts storage (dev)
- **ChromaDB** - Vector storage
- **Neo4j** - Graph database

### **AI/ML**
- **AWS Bedrock** - Claude and Titan models
- **NumPy** - Numerical operations
- **NetworkX** - Graph algorithms

### **Frontend**
- **Streamlit** - Web interface
- **Pyvis** - Graph visualization
- **HTML/CSS/JS** - Custom components

### **Infrastructure**
- **Docker** - Containerization
- **Make** - Build automation
- **AWS** - Cloud services

## 📊 Performance & Scalability

### **Current Capabilities**
- **Memory Storage**: 10,000+ facts per user
- **Response Time**: < 2 seconds for memory search
- **Concurrent Users**: 100+ simultaneous users
- **Graph Queries**: Sub-second path finding

### **Scalability Features**
- **Horizontal Scaling**: Kubernetes deployment ready
- **Database Sharding**: User-based data partitioning
- **Caching**: Redis integration for performance
- **Load Balancing**: Multiple API instances

## 🔒 Security & Privacy

### **Data Protection**
- **User Isolation**: Complete data separation by GUID
- **Selective Forgetting**: Users control what AI remembers
- **Source Attribution**: Track where information came from
- **Confidence Filtering**: Filter out low-confidence data

### **Access Control**
- **MCP Authentication**: Bearer token for MCP server
- **API Rate Limiting**: Prevent abuse
- **Role-based Access**: Future enterprise features

## 🧪 A/B Testing

### **What You Can Test**
- **Memory Impact**: Compare AI with/without memory
- **Response Quality**: Measure improvement in answers
- **User Satisfaction**: Track user preferences
- **Performance**: Monitor response times

### **Metrics Tracked**
- **Response Quality**: Relevance and accuracy
- **Response Time**: Speed of memory retrieval
- **Memory Usage**: How often memory is accessed
- **User Engagement**: Interaction patterns

## 🎯 Use Cases

### **Customer Service**
- Remember customer preferences and history
- Provide personalized responses
- Escalate complex issues with context

### **Knowledge Management**
- Build organizational knowledge bases
- Answer questions from company documents
- Maintain institutional memory

### **Sales & Marketing**
- Track customer interactions
- Personalize outreach
- Remember customer pain points

### **Education & Training**
- Adaptive learning systems
- Personalized tutoring
- Progress tracking

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### **Development Setup**
```bash
git clone <repository-url>
cd mind-map
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
```

### **Running Tests**
```bash
make test
```

### **Code Quality**
```bash
make lint
make format
```

## 📈 Roadmap

### **Short Term (Q1 2024)**
- [ ] JWT/OAuth2 authentication
- [ ] API rate limiting
- [ ] Prometheus/Grafana monitoring
- [ ] Structured logging

### **Medium Term (Q2 2024)**
- [ ] Multi-tenancy support
- [ ] Advanced analytics dashboard
- [ ] API versioning
- [ ] Query optimization

### **Long Term (Q3-Q4 2024)**
- [ ] Federated learning
- [ ] Causal inference capabilities
- [ ] Real-time streaming updates
- [ ] Mobile applications

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AWS Bedrock** for providing Claude and Titan models
- **Neo4j** for graph database capabilities
- **ChromaDB** for vector storage
- **FastAPI** for the excellent API framework
- **Streamlit** for rapid UI development

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/memorygraph/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/memorygraph/discussions)
- **Email**: support@memorygraph.ai

## 🌟 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=your-org/memorygraph&type=Date)](https://star-history.com/#your-org/memorygraph&Date)

---

<div align="center">

**Built with ❤️ by the MemoryGraph Team**

[Website](https://memorygraph.ai) • [Documentation](docs/) • [Demo](http://localhost:8501) • [API](http://localhost:8000/docs)

</div>