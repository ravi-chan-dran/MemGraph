# A/B Demo Run Guide

This guide walks you through running the A/B testing demo for the Bedrock-powered Graph + Memory POC.

## Prerequisites

1. **Python 3.11+**: Required for the latest features
2. **AWS Credentials**: Configure with Bedrock access
3. **Neo4j**: Install and start Neo4j database
4. **Docker**: For easy Neo4j setup

## Quick Setup

1. **Install dependencies**:
   ```bash
   pip install -e .
   ```

2. **Configure environment**:
   ```bash
   cp env.sample .env
   # Edit .env with your AWS credentials and settings
   ```

3. **Start Neo4j**:
   ```bash
   docker run --name neo4j-memory -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/test123 neo4j:5.20
   ```

4. **Start all services**:
   ```bash
   # Terminal 1: API server
   make run-api
   
   # Terminal 2: MCP server
   make run-mcp
   
   # Terminal 3: A/B relay
   make run-relay
   
   # Terminal 4: Seed data
   make seed
   
   # Terminal 5: Streamlit UI
   make run-ui
   ```

## A/B Test Scenarios

### Test 1: Match Formula Query
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

### Test 2: Payroll Processing
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude",
    "messages": [{"role": "user", "content": "When is payroll processed?"}],
    "guid": "plan_sponsor_acme",
    "memory_on": true
  }'
```

### Test 3: Auto-enrollment
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude",
    "messages": [{"role": "user", "content": "What is the auto-enrollment rate?"}],
    "guid": "plan_sponsor_acme",
    "memory_on": true
  }'
```

### Test 4: Communications Timing
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude",
    "messages": [{"role": "user", "content": "When are employee communications?"}],
    "guid": "plan_sponsor_acme",
    "memory_on": true
  }'
```

### Test 5: Forget and Re-ask
```bash
# Forget match formula
curl -X POST http://localhost:8000/memory/forget \
  -H "Content-Type: application/json" \
  -d '{
    "guid": "plan_sponsor_acme",
    "keys": ["match_formula"],
    "hard_delete": false
  }'

# Re-ask the same question
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude",
    "messages": [{"role": "user", "content": "What is the match formula?"}],
    "guid": "plan_sponsor_acme",
    "memory_on": true
  }'
```

## Web UI A/B Demo

1. **Open Streamlit UI**: http://localhost:8501
2. **Navigate to "A/B Demo"** tab
3. **Three-column layout**:
   - **Left**: Facts panel with channel dropdown and action buttons
   - **Center**: Chat interface for testing
   - **Right**: Evidence panel showing context cards and graph paths

### Demo Workflow

1. **Toggle Memory**: Use the Memory ON/OFF toggle in the left panel
2. **Send Messages**: Type questions in the chat interface
3. **Observe Differences**: Compare responses with memory ON vs OFF
4. **View Evidence**: See context cards and graph paths in the right panel
5. **Manage Facts**: Use the "Facts" tab to view and forget specific facts

## API Endpoints

### Memory API (Port 8000)
- `POST /memory/write` - Write memory data
- `POST /memory/search` - Search with ranking
- `POST /memory/summarize` - Summarize recent memory
- `POST /memory/forget` - Forget specific items
- `GET /graph/subgraph` - Get user subgraph
- `GET /graph/paths` - Find paths to topic

### A/B Relay (Port 8001)
- `POST /chat` - Process chat with optional memory
- `POST /toggle` - Toggle memory on/off
- `GET /health` - Health check
- `GET /stats` - Relay statistics

### MCP Server (Port 8002)
- `POST /memory/write` - Write memory (with auth)
- `POST /memory/search` - Search memory (with auth)
- `POST /memory/forget` - Forget memory (with auth)
- `POST /memory/summarize` - Summarize memory (with auth)
- `POST /memory/explain` - Explain paths (with auth)

## Troubleshooting

### Common Issues

1. **Bedrock IAM**: Ensure your AWS credentials have `bedrock:InvokeModel` permissions
2. **Neo4j Auth**: Default password is `test123` (not `password`)
3. **Chroma Path**: Ensure `./chroma_db` directory is writable
4. **Long Prompts**: Reduce prompt length if hitting token limits

### Debug Steps

1. **Check API Health**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8001/health
   curl http://localhost:8002/health
   ```

2. **Verify Neo4j**:
   ```bash
   # Check if Neo4j is running
   docker ps | grep neo4j
   
   # Test connection
   curl http://localhost:7474
   ```

3. **Check Logs**:
   ```bash
   # API server logs
   tail -f logs/api.log
   
   # Relay logs
   tail -f logs/relay.log
   ```

### Reset Everything

```bash
# Stop all services
make demo-off

# Clear data
rm -rf chroma_db/
rm -f memory.db
docker stop neo4j-memory
docker rm neo4j-memory

# Restart
make demo-on
```

## Expected A/B Results

### With Memory ON
- Responses include relevant context from stored memories
- Context cards show extracted facts and relationships
- Graph paths demonstrate knowledge connections
- More accurate and contextual answers

### With Memory OFF
- Generic responses without specific context
- No context cards or graph information
- Less accurate answers to specific questions
- Demonstrates the value of memory integration

## Performance Metrics

Monitor these metrics during A/B testing:
- **Response Time**: Memory ON vs OFF
- **Accuracy**: Correctness of answers
- **Context Quality**: Relevance of retrieved information
- **User Satisfaction**: Subjective assessment of responses

## Next Steps

1. **Customize Data**: Modify `scripts/seed_demo.py` with your own scenarios
2. **Add Metrics**: Implement detailed performance tracking
3. **Scale Testing**: Run longer A/B tests with more data
4. **Production**: Deploy with proper monitoring and alerting
