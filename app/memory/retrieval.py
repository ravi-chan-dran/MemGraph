"""Memory retrieval module for searching and retrieving stored memories."""

from typing import Dict, List, Any, Optional, Tuple
import json
import numpy as np
from datetime import datetime, timedelta

from ..core.bedrock import bedrock_client
from ..stores import kv_store, vector_store
from ..stores.graph_neo4j import get_graph_store


class MemoryRetriever:
    """Retrieves and searches through stored memories."""
    
    def __init__(self):
        """Initialize the memory retriever."""
        self.bedrock = bedrock_client
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            a_np = np.array(a)
            b_np = np.array(b)
            return np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np))
        except:
            return 0.0
    
    def recency_score(self, ts: str, days: int = 7) -> float:
        """Calculate recency score using exponential decay."""
        try:
            if not ts:
                return 0.0
            timestamp = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            delta = datetime.now() - timestamp
            return np.exp(-delta.total_seconds() / (days * 24 * 3600))
        except:
            return 0.0
    
    def importance_score(self, metadata: Dict[str, Any]) -> float:
        """Calculate importance score from metadata."""
        importance = metadata.get("importance", 0.5)
        priority = metadata.get("priority", "medium")
        priority_scores = {"high": 1.0, "medium": 0.5, "low": 0.2}
        return importance * priority_scores.get(priority, 0.5)
    
    def graph_proximity_score(self, guid: str, topic: str) -> float:
        """Calculate graph proximity score."""
        try:
            path_len = get_graph_store().shortest_path_len(guid, topic)
            return 1.0 / (1.0 + path_len) if path_len < 99 else 0.0
        except:
            return 0.0
    
    def calculate_score(self, episode: Dict[str, Any], query_embedding: List[float], 
                       query_tokens: List[str], guid: str) -> float:
        """Calculate final score for an episode."""
        # Cosine similarity (0.55 weight)
        episode_embedding = episode.get("embedding", [])
        sim_score = self.cosine_similarity(query_embedding, episode_embedding) if episode_embedding else 0.0
        
        # Recency (0.2 weight)
        recency_score = self.recency_score(episode.get("metadata", {}).get("timestamp", ""))
        
        # Importance (0.15 weight)
        importance_score = self.importance_score(episode.get("metadata", {}))
        
        # Graph proximity (0.1 weight)
        graph_score = 0.0
        for token in query_tokens:
            graph_score = max(graph_score, self.graph_proximity_score(guid, token))
        
        # Final weighted score
        final_score = (0.55 * sim_score + 
                      0.2 * recency_score + 
                      0.15 * importance_score + 
                      0.1 * graph_score)
        
        return final_score
    
    def build_context_card(self, facts: List[Dict], episodes: List[Dict], 
                          graph_hits: List[Dict], query: str) -> str:
        """Build a context card using Claude."""
        system_prompt = """
        Create a concise 120-word context card that synthesizes the provided information.
        Include relevant dates, sources, and key facts.
        Be factual and organized.
        """
        
        context_data = {
            "query": query,
            "facts": facts[:5],  # Limit to top 5 facts
            "episodes": episodes[:3],  # Limit to top 3 episodes
            "graph_hits": graph_hits[:3]  # Limit to top 3 graph hits
        }
        
        user_prompt = f"Context data: {json.dumps(context_data, indent=2)}"
        
        return self.bedrock.claude_complete(system_prompt, user_prompt)
    
    def semantic_search(self, query: str, limit: int = 5, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Perform semantic search across memories."""
        try:
            # Search in vector store
            vector_results = vector_store.search(query, n_results=limit, where=filters)
            
            # Enrich with full memory data from SQLite
            enriched_results = []
            for i, memory_id in enumerate(vector_results["ids"]):
                memory_data = kv_store.get(f"memory:{memory_id}")
                if memory_data:
                    memory_data["similarity_score"] = 1 - vector_results["distances"][i]  # Convert distance to similarity
                    enriched_results.append(memory_data)
            
            return enriched_results
        except Exception as e:
            print(f"Error in semantic search: {e}")
            return []
    
    def search_by_entities(self, entity_names: List[str], entity_types: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search memories by entity names and types."""
        try:
            # Find entity IDs in graph
            entity_ids = []
            for entity_name in entity_names:
                if entity_types:
                    for entity_type in entity_types:
                        entity_id = f"{entity_type.lower()}:{entity_name.lower().replace(' ', '_')}"
                        entity_ids.append(entity_id)
                else:
                    # Search across all entity types
                    for entity_type in ["PERSON", "ORGANIZATION", "LOCATION", "CONCEPT", "EVENT"]:
                        entity_id = f"{entity_type.lower()}:{entity_name.lower().replace(' ', '_')}"
                        entity_ids.append(entity_id)
            
            # Get memories associated with these entities
            memory_ids = set()
            for entity_id in entity_ids:
                entity_data = get_graph_store().get_entity(entity_id)
                if entity_data and "memory_refs" in entity_data:
                    memory_ids.update(entity_data["memory_refs"])
            
            # Retrieve full memory data
            memories = []
            for memory_id in memory_ids:
                memory_data = kv_store.get(f"memory:{memory_id}")
                if memory_data:
                    memories.append(memory_data)
            
            return memories
        except Exception as e:
            print(f"Error searching by entities: {e}")
            return []
    
    def get_related_memories(self, memory_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Get memories related to a specific memory through entity relationships."""
        try:
            # Get the original memory
            original_memory = kv_store.get(f"memory:{memory_id}")
            if not original_memory:
                return []
            
            # Get entities from the memory
            entities = original_memory.get("entities", {})
            all_entity_names = []
            for entity_list in entities.values():
                all_entity_names.extend(entity_list)
            
            # Find related memories through entity co-occurrence
            related_memories = self.search_by_entities(all_entity_names)
            
            # Filter out the original memory and limit results
            related_memories = [m for m in related_memories if m["id"] != memory_id]
            return related_memories[:10]  # Limit to 10 related memories
            
        except Exception as e:
            print(f"Error getting related memories: {e}")
            return []
    
    def get_entity_context(self, entity_name: str, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive context about an entity."""
        try:
            # Find entity ID
            if entity_type:
                entity_id = f"{entity_type.lower()}:{entity_name.lower().replace(' ', '_')}"
            else:
                # Search across all types
                search_results = get_graph_store().search_entities(entity_name, limit=1)
                if not search_results:
                    return {"entity": None, "memories": [], "relationships": []}
                entity_id = search_results[0]["id"]
            
            # Get entity data
            entity_data = get_graph_store().get_entity(entity_id)
            if not entity_data:
                return {"entity": None, "memories": [], "relationships": []}
            
            # Get related memories
            memory_refs = entity_data.get("memory_refs", [])
            memories = []
            for memory_id in memory_refs:
                memory_data = kv_store.get(f"memory:{memory_id}")
                if memory_data:
                    memories.append(memory_data)
            
            # Get relationships
            relationships = get_graph_store().get_entity_relationships(entity_id)
            
            return {
                "entity": entity_data,
                "memories": memories,
                "relationships": relationships
            }
        except Exception as e:
            print(f"Error getting entity context: {e}")
            return {"entity": None, "memories": [], "relationships": []}
    
    def get_timeline(self, entity_name: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get a timeline of memories, optionally filtered by entity."""
        try:
            if entity_name:
                # Get memories for specific entity
                memories = self.search_by_entities([entity_name])
            else:
                # Get all memories
                memory_keys = kv_store.list_keys("memory:")
                memories = []
                for key in memory_keys:
                    memory_data = kv_store.get(key)
                    if memory_data:
                        memories.append(memory_data)
            
            # Sort by creation time
            memories.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            return memories[:limit]
        except Exception as e:
            print(f"Error getting timeline: {e}")
            return []
    
    def search_by_metadata(self, metadata_filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search memories by metadata filters."""
        try:
            # Get all memory keys
            memory_keys = kv_store.list_keys("memory:")
            matching_memories = []
            
            for key in memory_keys:
                memory_data = kv_store.get(key)
                if memory_data:
                    metadata = memory_data.get("metadata", {})
                    
                    # Check if all filters match
                    matches = True
                    for filter_key, filter_value in metadata_filters.items():
                        if filter_key not in metadata or metadata[filter_key] != filter_value:
                            matches = False
                            break
                    
                    if matches:
                        matching_memories.append(memory_data)
            
            return matching_memories
        except Exception as e:
            print(f"Error searching by metadata: {e}")
            return []
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific memory by its ID."""
        try:
            return kv_store.get(f"memory:{memory_id}")
        except Exception as e:
            print(f"Error getting memory by ID: {e}")
            return None
    
    def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get statistics about the retrieval system."""
        try:
            # Get memory count
            memory_keys = kv_store.list_keys("memory:")
            memory_count = len(memory_keys)
            
            # Get graph stats
            graph_stats = get_graph_store().get_graph_stats()
            
            # Get vector store stats
            vector_stats = vector_store.get_collection_info()
            
            return {
                "total_memories": memory_count,
                "graph_stats": graph_stats,
                "vector_stats": vector_stats
            }
        except Exception as e:
            print(f"Error getting retrieval stats: {e}")
            return {"total_memories": 0, "graph_stats": {}, "vector_stats": {}}


# Global memory retriever instance
memory_retriever = MemoryRetriever()
