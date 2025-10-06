"""Memory extraction module for processing and extracting information from text."""

from typing import Dict, List, Any, Optional, Tuple
import uuid
import json
from datetime import datetime

from ..core.bedrock import bedrock_client
from ..core.config import settings


class MemoryExtractor:
    """Extracts and processes information from text into structured memory."""
    
    def __init__(self):
        """Initialize the memory extractor."""
        self.bedrock = bedrock_client
        self.confidence_threshold = settings.default_confidence_threshold
    
    def extract_structured(self, text: str, channel: str, ts: str) -> Dict[str, Any]:
        """Extract structured facts and episodes from text."""
        system_prompt = """
        Extract structured information from the text and return JSON with:
        - facts: array of {key, value, confidence, reason}
        - episodes: array of {summary, importance, tags}
        
        Only include items with confidence >= 0.6.
        Be precise and factual.
        """
        
        user_prompt = f"Text: {text}\nChannel: {channel}\nTimestamp: {ts}"
        
        response = self.bedrock.claude_complete(system_prompt, user_prompt)
        
        try:
            result = json.loads(response)
            # Filter by confidence threshold
            if "facts" in result:
                result["facts"] = [f for f in result["facts"] if f.get("confidence", 0) >= self.confidence_threshold]
            if "episodes" in result:
                result["episodes"] = [e for e in result["episodes"] if e.get("importance", 0) >= self.confidence_threshold]
            return result
        except json.JSONDecodeError:
            return {"facts": [], "episodes": []}
    
    def extract_triples(self, text: str, channel: str, ts: str) -> Dict[str, Any]:
        """Extract entities and triples from text."""
        system_prompt = """
        Extract entities and relationships from the text and return JSON with:
        - entities: array of {name, type, aliases?} where type is one of: Person, Place, DateRange, Preference, Task, Product, Org, Event
        - triples: array of {subject, predicate, object, confidence, time?} where predicate is one of: PREFERS, PLANS, OCCURS_ON, HAS_SIZE, HAS_ROLE, MENTIONS, RELATED_TO
        
        Only include items with confidence >= 0.6.
        Be precise about entity types and predicates.
        """
        
        user_prompt = f"Text: {text}\nChannel: {channel}\nTimestamp: {ts}"
        
        response = self.bedrock.claude_complete(system_prompt, user_prompt)
        
        try:
            result = json.loads(response)
            # Filter by confidence threshold and validate types
            if "entities" in result:
                valid_types = {"Person", "Place", "DateRange", "Preference", "Task", "Product", "Org", "Event"}
                result["entities"] = [e for e in result["entities"] 
                                    if e.get("type") in valid_types and e.get("confidence", 0) >= self.confidence_threshold]
            if "triples" in result:
                valid_predicates = {"PREFERS", "PLANS", "OCCURS_ON", "HAS_SIZE", "HAS_ROLE", "MENTIONS", "RELATED_TO"}
                result["triples"] = [t for t in result["triples"] 
                                   if t.get("predicate") in valid_predicates and t.get("confidence", 0) >= self.confidence_threshold]
            return result
        except json.JSONDecodeError:
            return {"entities": [], "triples": []}
    
    def extract_all(self, text: str, channel: str, ts: str) -> Dict[str, Any]:
        """Extract both structured facts and triples, merging outputs."""
        structured = self.extract_structured(text, channel, ts)
        triples = self.extract_triples(text, channel, ts)
        
        return {
            "facts": structured.get("facts", []),
            "episodes": structured.get("episodes", []),
            "entities": triples.get("entities", []),
            "triples": triples.get("triples", [])
        }
    
    def extract_from_text(self, text: str, source: Optional[str] = None, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Extract structured information from text (legacy method)."""
        # Generate embeddings
        embeddings = self.bedrock.titan_embed([text])
        if not embeddings:
            return {"error": "Failed to generate embeddings"}
        
        # Extract entities
        entities = self.bedrock.extract_entities(text)
        
        # Create memory entry
        memory_id = str(uuid.uuid4())
        memory_entry = {
            "id": memory_id,
            "text": text,
            "source": source,
            "metadata": metadata or {},
            "entities": entities,
            "created_at": datetime.now().isoformat(),
            "embedding": embeddings[0]
        }
        
        return memory_entry
    
    def _store_memory(self, memory_entry: Dict[str, Any]) -> bool:
        """Store memory entry in key-value and vector stores."""
        try:
            # Store in SQLite
            kv_store.put(f"memory:{memory_entry['id']}", memory_entry)
            
            # Store in ChromaDB
            vector_store.add_embeddings(
                embeddings=[memory_entry["embedding"]],
                documents=[memory_entry["text"]],
                metadatas=[{
                    "id": memory_entry["id"],
                    "source": memory_entry.get("source", ""),
                    "created_at": memory_entry["created_at"],
                    **memory_entry.get("metadata", {})
                }],
                ids=[memory_entry["id"]]
            )
            
            return True
        except Exception as e:
            print(f"Error storing memory: {e}")
            return False
    
    def _create_entity_nodes(self, entities: Dict[str, List[str]], memory_id: str) -> None:
        """Create entity nodes in the graph."""
        for entity_type, entity_list in entities.items():
            for entity_name in entity_list:
                if entity_name.strip():  # Skip empty entities
                    entity_id = f"{entity_type.lower()}:{entity_name.lower().replace(' ', '_')}"
                    
                    # Create entity node
                    graph_store.create_entity(
                        entity_id=entity_id,
                        entity_type=entity_type,
                        properties={
                            "name": entity_name,
                            "type": entity_type,
                            "first_seen": datetime.now().isoformat(),
                            "memory_refs": [memory_id]
                        }
                    )
    
    def _create_relationships(self, entities: Dict[str, List[str]], memory_id: str) -> None:
        """Create relationships between entities."""
        all_entities = []
        for entity_type, entity_list in entities.items():
            for entity_name in entity_list:
                if entity_name.strip():
                    entity_id = f"{entity_type.lower()}:{entity_name.lower().replace(' ', '_')}"
                    all_entities.append((entity_id, entity_type))
        
        # Create co-occurrence relationships
        for i, (source_id, source_type) in enumerate(all_entities):
            for target_id, target_type in all_entities[i+1:]:
                # Create bidirectional relationship
                graph_store.create_relationship(
                    source_id=source_id,
                    target_id=target_id,
                    relationship_type="CO_OCCURS_WITH",
                    properties={
                        "memory_id": memory_id,
                        "strength": 1.0,
                        "created_at": datetime.now().isoformat()
                    }
                )
    
    def extract_conversation(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Extract memory from a conversation."""
        extracted_memories = []
        
        for message in messages:
            text = message.get("content", "")
            speaker = message.get("speaker", "unknown")
            
            if text.strip():
                memory = self.extract_from_text(
                    text=text,
                    source=f"conversation:{speaker}",
                    metadata={
                        "message_type": "conversation",
                        "speaker": speaker,
                        "timestamp": message.get("timestamp", datetime.now().isoformat())
                    }
                )
                extracted_memories.append(memory)
        
        return extracted_memories
    
    def extract_document(self, content: str, title: Optional[str] = None, url: Optional[str] = None) -> Dict[str, Any]:
        """Extract memory from a document."""
        metadata = {}
        if title:
            metadata["title"] = title
        if url:
            metadata["url"] = url
        metadata["document_type"] = "document"
        
        return self.extract_from_text(
            text=content,
            source=url or title or "document",
            metadata=metadata
        )
    
    def update_entity_relationships(self, entity_id: str, new_relationships: List[Tuple[str, str, Dict]]) -> bool:
        """Update relationships for an existing entity."""
        try:
            for target_id, relationship_type, properties in new_relationships:
                graph_store.create_relationship(
                    source_id=entity_id,
                    target_id=target_id,
                    relationship_type=relationship_type,
                    properties=properties
                )
            return True
        except Exception as e:
            print(f"Error updating entity relationships: {e}")
            return False
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """Get statistics about extracted memories."""
        try:
            # Get memory count from SQLite
            memory_keys = kv_store.list_keys("memory:")
            memory_count = len(memory_keys)
            
            # Get graph stats
            graph_stats = graph_store.get_graph_stats()
            
            # Get vector store stats
            vector_stats = vector_store.get_collection_info()
            
            return {
                "total_memories": memory_count,
                "graph_stats": graph_stats,
                "vector_stats": vector_stats
            }
        except Exception as e:
            print(f"Error getting extraction stats: {e}")
            return {"total_memories": 0, "graph_stats": {}, "vector_stats": {}}


# Global memory extractor instance
memory_extractor = MemoryExtractor()
