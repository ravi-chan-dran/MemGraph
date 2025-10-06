"""A/B testing relay for comparing different memory strategies."""

import asyncio
import json
import random
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

from app.memory.service import memory_service
from app.core.config import settings
from app.core.bedrock import bedrock_client


class ChatRequest(BaseModel):
    model: str
    messages: List[Dict[str, str]]
    guid: str
    memory_on: bool = True


class ToggleRequest(BaseModel):
    on: bool


class ABRelay:
    """A/B testing relay for memory system strategies."""
    
    def __init__(self):
        """Initialize the A/B relay."""
        self.strategies = {
            "semantic": {"weight": 0.4, "description": "Semantic search only"},
            "hybrid": {"weight": 0.3, "description": "Semantic + entity search"},
            "graph": {"weight": 0.2, "description": "Graph-based search"},
            "metadata": {"weight": 0.1, "description": "Metadata filtering"}
        }
        self.results = []
        self.memory_enabled = True
    
    def select_strategy(self) -> str:
        """Select a strategy based on weights."""
        rand = random.random()
        cumulative = 0
        
        for strategy, config in self.strategies.items():
            cumulative += config["weight"]
            if rand <= cumulative:
                return strategy
        
        return "semantic"  # fallback
    
    def process_chat(self, request: ChatRequest) -> Dict[str, Any]:
        """Process chat request with optional memory."""
        start_time = time.time()
        tools_invoked = []
        
        try:
            messages = request.messages.copy()
            
            if request.memory_on and self.memory_enabled:
                # Get last user message for memory search
                last_user_message = None
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        last_user_message = msg.get("content", "")
                        break
                
                if last_user_message:
                    # Search memory
                    search_result = memory_service.search_memory({
                        "guid": request.guid,
                        "query": last_user_message,
                        "k": 5,
                        "since_days": 30,
                        "include_graph": True
                    })
                    
                    if search_result.get("success") and search_result.get("context_card"):
                        # Inject context as system message
                        context_message = {
                            "role": "system",
                            "content": f"CONTEXT CARD:\n{search_result['context_card']}"
                        }
                        messages.insert(0, context_message)
                        tools_invoked.append("memory.search")
            
            # Forward to model
            if request.model.startswith("claude"):
                # Use Bedrock Claude
                system_prompt = ""
                user_prompt = ""
                
                for msg in messages:
                    if msg["role"] == "system":
                        system_prompt = msg["content"]
                    elif msg["role"] == "user":
                        user_prompt = msg["content"]
                
                response = bedrock_client.claude_complete(system_prompt, user_prompt)
                tools_invoked.append("bedrock.claude")
            else:
                # For other models, would need to implement API calls
                response = "Model not supported in this implementation"
                tools_invoked.append("unsupported_model")
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Log the interaction
            self.results.append({
                "timestamp": datetime.now().isoformat(),
                "guid": request.guid,
                "memory_on": request.memory_on,
                "model": request.model,
                "tools_invoked": tools_invoked,
                "duration": duration,
                "success": True
            })
            
            return {
                "response": response,
                "memory_used": request.memory_on and self.memory_enabled,
                "tools_invoked": tools_invoked,
                "duration": duration
            }
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            
            self.results.append({
                "timestamp": datetime.now().isoformat(),
                "guid": request.guid,
                "memory_on": request.memory_on,
                "model": request.model,
                "tools_invoked": tools_invoked,
                "duration": duration,
                "success": False,
                "error": str(e)
            })
            
            return {
                "error": str(e),
                "memory_used": False,
                "tools_invoked": tools_invoked,
                "duration": duration
            }
    
    async def process_query(self, query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a query using A/B testing."""
        strategy = self.select_strategy()
        start_time = datetime.now()
        
        try:
            # Execute search based on strategy
            if strategy == "semantic":
                result = memory_service.search_memories(query, search_type="semantic", limit=5)
            elif strategy == "hybrid":
                # Combine semantic and entity search
                semantic_result = memory_service.search_memories(query, search_type="semantic", limit=3)
                entity_result = memory_service.search_memories(query, search_type="entity", limit=2)
                
                # Merge results
                all_results = []
                if semantic_result.get("success"):
                    all_results.extend(semantic_result["results"])
                if entity_result.get("success"):
                    all_results.extend(entity_result["results"])
                
                result = {
                    "success": True,
                    "results": all_results[:5],
                    "count": len(all_results[:5]),
                    "search_type": "hybrid"
                }
            elif strategy == "graph":
                # Use graph-based search (simplified)
                result = memory_service.search_memories(query, search_type="entity", limit=5)
            else:  # metadata
                result = memory_service.search_memories(query, search_type="metadata", limit=5)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Record result
            test_result = {
                "query": query,
                "strategy": strategy,
                "user_id": user_id,
                "success": result.get("success", False),
                "result_count": result.get("count", 0),
                "duration": duration,
                "timestamp": start_time.isoformat()
            }
            
            self.results.append(test_result)
            
            return {
                "strategy": strategy,
                "result": result,
                "test_id": len(self.results) - 1
            }
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            test_result = {
                "query": query,
                "strategy": strategy,
                "user_id": user_id,
                "success": False,
                "error": str(e),
                "duration": duration,
                "timestamp": start_time.isoformat()
            }
            
            self.results.append(test_result)
            
            return {
                "strategy": strategy,
                "error": str(e),
                "test_id": len(self.results) - 1
            }
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """Get statistics for each strategy."""
        if not self.results:
            return {"strategies": {}, "total_tests": 0}
        
        strategy_stats = {}
        total_tests = len(self.results)
        
        for strategy in self.strategies.keys():
            strategy_results = [r for r in self.results if r["strategy"] == strategy]
            
            if strategy_results:
                success_count = sum(1 for r in strategy_results if r["success"])
                avg_duration = sum(r["duration"] for r in strategy_results) / len(strategy_results)
                avg_result_count = sum(r["result_count"] for r in strategy_results) / len(strategy_results)
                
                strategy_stats[strategy] = {
                    "total_tests": len(strategy_results),
                    "success_rate": success_count / len(strategy_results),
                    "avg_duration": avg_duration,
                    "avg_result_count": avg_result_count,
                    "description": self.strategies[strategy]["description"]
                }
            else:
                strategy_stats[strategy] = {
                    "total_tests": 0,
                    "success_rate": 0,
                    "avg_duration": 0,
                    "avg_result_count": 0,
                    "description": self.strategies[strategy]["description"]
                }
        
        return {
            "strategies": strategy_stats,
            "total_tests": total_tests,
            "overall_success_rate": sum(1 for r in self.results if r["success"]) / total_tests
        }
    
    def export_results(self, filename: Optional[str] = None) -> str:
        """Export test results to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ab_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "results": self.results,
                "strategy_stats": self.get_strategy_stats(),
                "export_timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        return filename
    
    def clear_results(self):
        """Clear all test results."""
        self.results = []


# Global A/B relay instance
ab_relay = ABRelay()

# FastAPI app
app = FastAPI(title="A/B Relay", version="1.0.0")


@app.post("/chat")
async def chat(request: ChatRequest):
    """Process chat with optional memory."""
    try:
        result = ab_relay.process_chat(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/toggle")
async def toggle_memory(request: ToggleRequest):
    """Toggle memory on/off."""
    ab_relay.memory_enabled = request.on
    return {
        "memory_enabled": ab_relay.memory_enabled,
        "message": f"Memory {'enabled' if request.on else 'disabled'}"
    }


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "OK",
        "memory_enabled": ab_relay.memory_enabled,
        "total_requests": len(ab_relay.results)
    }


@app.get("/stats")
async def get_stats():
    """Get relay statistics."""
    return ab_relay.get_strategy_stats()


if __name__ == "__main__":
    uvicorn.run(
        "ab_relay:app",
        host="0.0.0.0",
        port=settings.relay_port,
        reload=True
    )
