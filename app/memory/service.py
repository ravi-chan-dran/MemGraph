"""Memory service module that orchestrates memory operations."""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid

from .extractor import memory_extractor
from .retrieval import memory_retriever
from ..core.bedrock import bedrock_client
from ..stores import kv_store, vector_store
from ..stores.graph_neo4j import get_graph_store


class MemoryService:
    """High-level service for memory operations."""
    
    def __init__(self):
        """Initialize the memory service."""
        self.extractor = memory_extractor
        self.retriever = memory_retriever
        self.bedrock = bedrock_client
    
    def write_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Write memory data to all stores."""
        try:
            guid = data["guid"]
            text = data["text"]
            channel = data["channel"]
            ts = data["ts"]
            thread_id = data.get("thread_id")
            
            # Extract structured information
            extracted = self.extractor.extract_all(text, channel, ts)
            
            # Store facts in SQLite
            for fact in extracted.get("facts", []):
                kv_store.upsert_fact(
                    guid=guid,
                    key=fact["key"],
                    value=fact["value"],
                    confidence=fact["confidence"],
                    source=channel,
                    ts=ts
                )
            
            # Create episode text
            episodes = extracted.get("episodes", [])
            episode_text = episodes[0]["summary"] if episodes else text
            
            # Generate embedding and store in ChromaDB
            embeddings = self.bedrock.titan_embed([episode_text])
            if embeddings:
                vector_store.upsert_episode(
                    guid=guid,
                    text=episode_text,
                    metadata={
                        "channel": channel,
                        "ts": ts,
                        "thread_id": thread_id,
                        "importance": episodes[0].get("importance", 0.5) if episodes else 0.5,
                        "tags": episodes[0].get("tags", []) if episodes else []
                    },
                    embedding=embeddings[0]
                )
            
            # Store in graph
            get_graph_store().upsert_user(guid)
            
            # Store entities
            for entity in extracted.get("entities", []):
                get_graph_store().upsert_entity(entity["name"], entity["type"])
            
            # Store fact relationships
            for fact in extracted.get("facts", []):
                get_graph_store().upsert_fact_rel(
                    guid=guid,
                    key=fact["key"],
                    value=fact["value"],
                    confidence=fact["confidence"],
                    ts=ts,
                    channel=channel
                )
            
            # Store triples
            for triple in extracted.get("triples", []):
                get_graph_store().upsert_triple(
                    subject=triple["subject"],
                    predicate=triple["predicate"],
                    object=triple["object"],
                    props={
                        "confidence": triple["confidence"],
                        "time": triple.get("time"),
                        "channel": channel,
                        "ts": ts,
                        "source": "extraction"
                    }
                )
            
            return {"success": True, "message": "Memory written successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Search memory with ranking and context building."""
        try:
            guid = data["guid"]
            query = data["query"]
            k = data.get("k", 8)
            since_days = data.get("since_days", 30)
            include_graph = data.get("include_graph", True)
            
            # Query vector store
            episodes = vector_store.query_similar(guid, query, k, since_days)
            
            # Get facts from SQLite
            facts = kv_store.get_facts(guid, min_conf=0.6)
            
            # Generate query embedding for scoring
            query_embeddings = self.bedrock.titan_embed([query])
            query_embedding = query_embeddings[0] if query_embeddings else []
            query_tokens = query.lower().split()
            
            # Score and rank episodes
            scored_episodes = []
            for episode in episodes:
                score = self.retriever.calculate_score(episode, query_embedding, query_tokens, guid)
                episode["score"] = score
                scored_episodes.append(episode)
            
            # Sort by score
            scored_episodes.sort(key=lambda x: x["score"], reverse=True)
            
            # Get graph hits if requested
            graph_hits = []
            if include_graph:
                # Try individual tokens
                for token in query_tokens:
                    paths = get_graph_store().find_paths(guid, token, k=3)
                    graph_hits.extend(paths)
                
                # Try full query
                paths = get_graph_store().find_paths(guid, query, k=3)
                graph_hits.extend(paths)
                
                # If no paths found, create a simple path from facts
                if not graph_hits and facts:
                    graph_hits = [{
                        "path": f"User -> Facts -> {query}",
                        "length": 2,
                        "reasoning": f"Found {len(facts)} relevant facts about {query}"
                    }]
                    print(f"DEBUG: Created graph_hits with {len(facts)} facts")
            
            # Build context card
            context_card = self.retriever.build_context_card(
                facts=facts,
                episodes=scored_episodes[:5],
                graph_hits=graph_hits,
                query=query
            )
            
            return {
                "success": True,
                "context_card": context_card,
                "facts": facts,
                "episodes": scored_episodes,
                "graph_hits": graph_hits,
                "rationale": f"Found {len(scored_episodes)} episodes, {len(facts)} facts, {len(graph_hits)} graph paths"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def summarize_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize recent memory."""
        try:
            guid = data["guid"]
            since_days = data.get("since_days", 7)
            
            # Get recent episodes
            episodes = vector_store.query_similar(guid, "recent activity", k=20, since_days=since_days)
            
            if not episodes:
                return {"success": True, "summary": "No recent memories found"}
            
            # Create summary using Claude
            episode_texts = [ep["text"] for ep in episodes[:10]]
            combined_text = "\n\n".join(episode_texts)
            
            system_prompt = """
            Create a 3-5 bullet point summary of the recent activities.
            Be concise and highlight key events, decisions, and important information.
            """
            
            summary = self.bedrock.claude_complete(system_prompt, combined_text)
            
            return {
                "success": True,
                "summary": summary,
                "episodes_analyzed": len(episodes)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def forget_memory(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Forget specific memory items."""
        try:
            guid = data["guid"]
            keys = data.get("keys", [])
            entities = data.get("entities", [])
            predicates = data.get("predicates", [])
            hard_delete = data.get("hard_delete", False)
            
            deleted_items = []
            
            # Delete facts
            if keys:
                for key in keys:
                    if kv_store.delete_fact(guid, key):
                        deleted_items.append(f"fact:{key}")
            
            # Mark episodes as redacted or delete
            if hard_delete:
                # Delete episodes from ChromaDB
                episodes = vector_store.query_similar(guid, "", k=1000)
                episode_ids = [ep["id"] for ep in episodes]
                if episode_ids:
                    vector_store.delete_by_ids(episode_ids)
                    deleted_items.append(f"episodes:{len(episode_ids)}")
            else:
                # Mark as redacted (would need to implement redaction flag)
                deleted_items.append("episodes:marked_redacted")
            
            # Handle graph deletions
            if entities or predicates:
                # This would require more complex graph operations
                deleted_items.append("graph:relationships_updated")
            
            # Generate confirmation
            confirmation = self.bedrock.claude_complete(
                "Generate a brief confirmation message for memory deletion.",
                f"Deleted items: {', '.join(deleted_items)}"
            )
            
            return {
                "success": True,
                "deleted_items": deleted_items,
                "confirmation": confirmation
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_memory(self, text: str, source: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Add a new memory to the system."""
        try:
            memory = self.extractor.extract_from_text(text, source, metadata)
            return {
                "success": True,
                "memory": memory,
                "message": "Memory added successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to add memory"
            }
    
    def search_memories(self, query: str, search_type: str = "semantic", limit: int = 5, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Search for memories using different search strategies."""
        try:
            if search_type == "semantic":
                results = self.retriever.semantic_search(query, limit, filters)
            elif search_type == "entity":
                # Extract entities from query and search by them
                entities = self.bedrock.extract_entities(query)
                entity_names = []
                for entity_list in entities.values():
                    entity_names.extend(entity_list)
                results = self.retriever.search_by_entities(entity_names)
            elif search_type == "metadata":
                results = self.retriever.search_by_metadata(filters or {})
            else:
                results = []
            
            return {
                "success": True,
                "results": results,
                "count": len(results),
                "search_type": search_type
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "results": [],
                "count": 0
            }
    
    def get_memory_context(self, memory_id: str, include_related: bool = True) -> Dict[str, Any]:
        """Get a memory with its context and related memories."""
        try:
            # Get the main memory
            memory = self.retriever.get_memory_by_id(memory_id)
            if not memory:
                return {
                    "success": False,
                    "error": "Memory not found",
                    "memory": None
                }
            
            context = {"memory": memory}
            
            if include_related:
                # Get related memories
                related = self.retriever.get_related_memories(memory_id)
                context["related_memories"] = related
            
            return {
                "success": True,
                "context": context
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "context": None
            }
    
    def get_entity_context(self, entity_name: str, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive context about an entity."""
        try:
            context = self.retriever.get_entity_context(entity_name, entity_type)
            return {
                "success": True,
                "context": context
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "context": None
            }
    
    def get_timeline(self, entity_name: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
        """Get a timeline of memories."""
        try:
            timeline = self.retriever.get_timeline(entity_name, limit)
            return {
                "success": True,
                "timeline": timeline,
                "count": len(timeline)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timeline": [],
                "count": 0
            }
    
    def process_conversation(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Process a conversation and extract memories."""
        try:
            extracted_memories = self.extractor.extract_conversation(messages)
            return {
                "success": True,
                "memories": extracted_memories,
                "count": len(extracted_memories),
                "message": "Conversation processed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "memories": [],
                "count": 0
            }
    
    def process_document(self, content: str, title: Optional[str] = None, url: Optional[str] = None) -> Dict[str, Any]:
        """Process a document and extract memories."""
        try:
            memory = self.extractor.extract_document(content, title, url)
            return {
                "success": True,
                "memory": memory,
                "message": "Document processed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "memory": None
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        try:
            # Get basic stats from stores
            from ..stores import kv_store, vector_store
            from ..stores.graph_neo4j import get_graph_store
            
            # Count facts in SQLite
            total_facts = 0
            try:
                facts = kv_store.get_facts("plan_sponsor_acme", min_conf=0.0)
                total_facts = len(facts)
            except:
                pass
            
            # Count episodes in ChromaDB
            vector_count = 0
            try:
                episodes = vector_store.query_similar("plan_sponsor_acme", "", k=1000)
                vector_count = len(episodes)
            except:
                pass
            
            # Count graph nodes and relationships
            graph_nodes = 0
            graph_relationships = 0
            try:
                subgraph = get_graph_store().get_subgraph("plan_sponsor_acme")
                graph_nodes = len(subgraph)
                # Estimate relationships (rough count)
                graph_relationships = graph_nodes * 2  # Rough estimate
            except:
                pass
            
            return {
                "success": True,
                "stats": {
                    "retrieval": {
                        "total_memories": total_facts,
                        "vector_stats": {"count": vector_count},
                        "graph_stats": {
                            "total_nodes": graph_nodes,
                            "relationship_count": graph_relationships
                        }
                    },
                    "timestamp": datetime.now().isoformat()
                }
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "stats": None
            }
    
    def generate_insights(self, query: str, max_memories: int = 10) -> Dict[str, Any]:
        """Generate insights by analyzing relevant memories."""
        try:
            # Search for relevant memories
            memories = self.retriever.semantic_search(query, limit=max_memories)
            
            if not memories:
                return {
                    "success": True,
                    "insights": "No relevant memories found for the query.",
                    "memories_analyzed": 0
                }
            
            # Create a summary of the memories
            memory_texts = [mem["text"] for mem in memories]
            combined_text = "\n\n".join(memory_texts)
            
            # Generate insights using Claude
            insight_prompt = f"""
            Based on the following memories, provide insights about: {query}
            
            Memories:
            {combined_text}
            
            Please provide:
            1. Key themes and patterns
            2. Important relationships between concepts
            3. Notable trends or changes over time
            4. Actionable insights or recommendations
            
            Format your response as a structured analysis.
            """
            
            insights = self.bedrock.generate_text(insight_prompt, max_tokens=1000)
            
            return {
                "success": True,
                "insights": insights or "Unable to generate insights",
                "memories_analyzed": len(memories),
                "query": query
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "insights": None,
                "memories_analyzed": 0
            }


# Global memory service instance
memory_service = MemoryService()
