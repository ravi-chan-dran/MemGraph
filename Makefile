# Makefile for Bedrock Graph + Memory POC

.PHONY: help install dev-install run-api run-ui run-relay run-mcp seed demo-on demo-off test clean lint format

# Default target
help:
	@echo "Available targets:"
	@echo "  install      - Install production dependencies"
	@echo "  dev-install  - Install development dependencies"
	@echo "  run-api      - Start the FastAPI server"
	@echo "  run-ui       - Start the Streamlit UI"
	@echo "  run-relay    - Start the A/B testing relay"
	@echo "  run-mcp      - Start the MCP server"
	@echo "  seed         - Seed demo data"
	@echo "  demo-on      - Start all services for demo"
	@echo "  demo-off     - Stop all demo services"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting"
	@echo "  format       - Format code"
	@echo "  clean        - Clean up generated files"

# Installation targets
install:
	pip install -e .

dev-install:
	pip install -e ".[dev,test,docs]"

# Service targets
run-api:
	@echo "Starting FastAPI server..."
	uvicorn app.api.routes:app --host 0.0.0.0 --port 8000 --reload

run-ui:
	@echo "Starting Streamlit UI..."
	streamlit run ui/streamlit_app_improved.py --server.port 8501 --server.address 0.0.0.0

run-relay:
	@echo "Starting A/B testing relay..."
	python ab_relay.py

run-mcp:
	@echo "Starting MCP server..."
	python mcp_server.py

run-cli:
	@echo "Starting CLI orchestrator..."
	python orchestrator/mock_cli.py

# Data management
seed:
	@echo "Seeding demo data..."
	@source .venv/bin/activate && python scripts/seed_demo.py

seed-once:
	@echo "Seeding demo data (first time only)..."
	@source .venv/bin/activate && python scripts/seed_demo.py
	@echo "✅ Demo data seeded! Now run 'make demo-on' to start services."

# Demo orchestration
demo-on:
	@echo "Starting demo environment with improved startup script..."
	@source .venv/bin/activate && python scripts/start_demo.py

demo-on-simple:
	@echo "Starting demo environment (simple mode)..."
	@echo "1. Starting API server in background..."
	@$(MAKE) run-api &
	@sleep 10
	@echo "2. Starting MCP server in background..."
	@$(MAKE) run-mcp &
	@sleep 5
	@echo "3. Starting A/B relay in background..."
	@$(MAKE) run-relay &
	@sleep 5
	@echo "4. Seeding demo data..."
	@$(MAKE) seed
	@echo "5. Starting UI..."
	@echo "Demo is ready! Access the UI at http://localhost:8501"
	@echo "API docs available at http://localhost:8000/docs"
	@echo "A/B Relay available at http://localhost:8001"
	@echo "MCP Server available at http://localhost:8002"
	@$(MAKE) run-ui

demo-off:
	@echo "Stopping demo services..."
	@pkill -f "uvicorn app.api.routes:app" || true
	@pkill -f "python mcp_server.py" || true
	@pkill -f "python ab_relay.py" || true
	@pkill -f "streamlit run ui/streamlit_app.py" || true
	@echo "All demo services stopped."

# Development targets
test:
	@echo "Running tests..."
	pytest

test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=app --cov-report=html --cov-report=term

lint:
	@echo "Running linting..."
	flake8 app orchestrator ui scripts
	mypy app orchestrator ui scripts

format:
	@echo "Formatting code..."
	black app orchestrator ui scripts
	isort app orchestrator ui scripts

# Cleanup
clean:
	@echo "Cleaning up..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf chroma_db/
	rm -f memory.db
	rm -f *.log
	@echo "Cleanup complete"

# Docker targets (optional)
docker-build:
	@echo "Building Docker image..."
	docker build -t bedrock-memory-poc .

docker-run:
	@echo "Running Docker container..."
	docker run -p 8000:8000 -p 8501:8501 --env-file .env bedrock-memory-poc

# Database setup
setup-neo4j:
	@echo "Setting up Neo4j with Docker..."
	docker run -d \
		--name neo4j-memory \
		-p 7474:7474 \
		-p 7687:7687 \
		-e NEO4J_AUTH=neo4j/test123456 \
		-e NEO4J_PLUGINS='["apoc"]' \
		neo4j:latest
	@echo "Neo4j is starting up. Access at http://localhost:7474"
	@echo "Username: neo4j, Password: test123456"

stop-neo4j:
	@echo "Stopping Neo4j container..."
	docker stop neo4j-memory || true
	docker rm neo4j-memory || true

# Health checks
health-check:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health || echo "API not responding"
	@curl -s http://localhost:8501 || echo "UI not responding"

# Development workflow
dev-setup: dev-install setup-neo4j
	@echo "Development environment setup complete!"
	@echo "Next steps:"
	@echo "1. Copy env.sample to .env and configure your settings"
	@echo "2. Run 'make demo-on' to start the demo"

# Quick start
quick-start: install
	@echo "Quick start - setting up minimal environment..."
	@cp env.sample .env
	@echo "Environment file created. Please edit .env with your settings."
	@echo "Then run: make demo-on"
