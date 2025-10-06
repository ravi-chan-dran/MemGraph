# Quick Start Guide

Get up and running with the Bedrock-powered Graph + Memory POC in minutes.

## Prerequisites

- **Python 3.11+** (required for latest features)
- **Docker** (for Neo4j)
- **AWS Account** with Bedrock access
- **Git** (to clone the repository)

## One-Shot Setup

### 1. Install Python 3.11+

**macOS (using Homebrew):**
```bash
brew install python@3.11
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/) or use Chocolatey:
```bash
choco install python311
```

### 2. Clone and Setup

```bash
git clone <repository-url>
cd mind-map

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 3. Configure Environment

```bash
# Copy environment template
cp env.sample .env

# Edit with your settings
nano .env  # or use your preferred editor
```

**Required settings in `.env`:**
```bash
# AWS Configuration
AWS_REGION=us-east-1
BEDROCK_CLAUDE_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
BEDROCK_TITAN_EMB_MODEL_ID=amazon.titan-embed-text-v1

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=test123

# Other settings use defaults
```

### 4. Start Neo4j

```bash
# Start Neo4j with Docker
docker run --name neo4j-memory \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/test123 \
  neo4j:5.20

# Verify it's running
curl http://localhost:7474
```

### 5. Start All Services

**Terminal 1 - API Server:**
```bash
make run-api
# or: uvicorn app.api.routes:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - MCP Server:**
```bash
make run-mcp
# or: python mcp_server.py
```

**Terminal 3 - A/B Relay:**
```bash
make run-relay
# or: python ab_relay.py
```

**Terminal 4 - Seed Demo Data:**
```bash
make seed
# or: python scripts/seed_demo.py
```

**Terminal 5 - Streamlit UI:**
```bash
make run-ui
# or: streamlit run ui/streamlit_app.py
```

### 6. Verify Setup

**Check all services:**
```bash
# API Health
curl http://localhost:8000/health

# Relay Health
curl http://localhost:8001/health

# MCP Health
curl http://localhost:8002/health
```

**Expected response:**
```json
{
  "status": "OK",
  "message": "Service is running",
  "bedrock_test": {
    "titan_embed_vector_length": 1536,
    "test_passed": true
  }
}
```

## Quick Demo

### 1. Open the UI

Navigate to: http://localhost:8501

### 2. Run A/B Tests

**Test 1: Basic Memory Query**
```bash
# With memory ON
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude",
    "messages": [{"role": "user", "content": "What is the match formula?"}],
    "guid": "plan_sponsor_acme",
    "memory_on": true
  }'

# With memory OFF
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude",
    "messages": [{"role": "user", "content": "What is the match formula?"}],
    "guid": "plan_sponsor_acme",
    "memory_on": false
  }'
```

**Test 2: Memory Operations**
```bash
# Write memory
curl -X POST http://localhost:8000/memory/write \
  -H "Content-Type: application/json" \
  -d '{
    "guid": "plan_sponsor_acme",
    "text": "New plan feature: Roth 401k option available starting January 2025",
    "channel": "mock-email",
    "ts": "2024-11-08T10:00:00Z"
  }'

# Search memory
curl -X POST http://localhost:8000/memory/search \
  -H "Content-Type: application/json" \
  -d '{
    "guid": "plan_sponsor_acme",
    "query": "Roth 401k",
    "k": 5
  }'

# Summarize recent memory
curl -X POST http://localhost:8000/memory/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "guid": "plan_sponsor_acme",
    "since_days": 7
  }'
```

### 3. Explore the Graph

```bash
# Get subgraph
curl "http://localhost:8000/graph/subgraph?guid=plan_sponsor_acme"

# Find paths to topic
curl "http://localhost:8000/graph/paths?guid=plan_sponsor_acme&topic=retirement"
```

## Troubleshooting

### Common Issues

**1. AWS Bedrock Access Denied**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Verify Bedrock permissions
aws bedrock list-foundation-models --region us-east-1
```

**2. Neo4j Connection Failed**
```bash
# Check if Neo4j is running
docker ps | grep neo4j

# Check logs
docker logs neo4j-memory

# Restart if needed
docker restart neo4j-memory
```

**3. ChromaDB Path Issues**
```bash
# Create directory
mkdir -p chroma_db

# Check permissions
ls -la chroma_db/
```

**4. Port Conflicts**
```bash
# Check what's using ports
lsof -i :8000
lsof -i :8001
lsof -i :8002
lsof -i :8501

# Kill processes if needed
kill -9 <PID>
```

**5. Python Version Issues**
```bash
# Check Python version
python --version

# Should be 3.11+
# If not, reinstall or use pyenv
```

### Debug Mode

**Enable detailed logging:**
```bash
export LOG_LEVEL=DEBUG
export PYTHONPATH=.

# Run with debug
python -m app.api.routes
```

**Check service logs:**
```bash
# API logs
tail -f logs/api.log

# Relay logs
tail -f logs/relay.log

# MCP logs
tail -f logs/mcp.log
```

### Reset Everything

**Complete reset:**
```bash
# Stop all services
make demo-off

# Remove data
rm -rf chroma_db/
rm -f memory.db
docker stop neo4j-memory
docker rm neo4j-memory

# Restart
make demo-on
```

## Next Steps

1. **Customize Data**: Edit `scripts/seed_demo.py` with your own scenarios
2. **Add Features**: Extend the memory extraction logic
3. **Scale Up**: Deploy to production with proper infrastructure
4. **Monitor**: Add metrics and alerting

## Getting Help

1. **Check Logs**: Look for error messages in service logs
2. **Verify Services**: Ensure all services are running and healthy
3. **Test Components**: Use individual API endpoints to isolate issues
4. **Review Documentation**: Check the full demo guide in `scripts/demo_run.md`

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit UI  │    │   A/B Relay     │    │   MCP Server    │
│   (Port 8501)   │    │   (Port 8001)   │    │   (Port 8002)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Memory API    │
                    │   (Port 8000)   │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SQLite KV     │    │   ChromaDB      │    │   Neo4j Graph   │
│   (Facts)       │    │   (Vectors)     │    │   (Relations)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   AWS Bedrock   │
                    │   (Claude/Titan)│
                    └─────────────────┘
```

## Performance Tips

1. **Use SSD**: Store databases on SSD for better performance
2. **Memory**: Allocate at least 4GB RAM for smooth operation
3. **Network**: Ensure stable internet for AWS Bedrock calls
4. **Monitoring**: Watch memory usage and response times

## Security Notes

1. **AWS Credentials**: Never commit `.env` file to version control
2. **Neo4j**: Change default password in production
3. **MCP Token**: Use strong, unique tokens
4. **Network**: Consider VPN for production deployments
