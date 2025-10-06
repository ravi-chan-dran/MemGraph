"""ChromaDB vector store for semantic search and retrieval."""

import chromadb
from chromadb.config import Settings as ChromaSettings
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timedelta

from ..core.config import settings
from ..core.bedrock import bedrock_client


class ChromaVectorStore:
    """ChromaDB-based vector store for semantic search."""
    
    def __init__(self, persist_directory: Optional[str] = None):
        """Initialize the ChromaDB store."""
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = "episodes_mem"
        self.collection = self._get_or_create_collection()
    
    def _get_or_create_collection(self):
        """Get or create the episodes_mem collection."""
        try:
            return self.client.get_collection(name=self.collection_name)
        except ValueError:
            return self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Episode memories for semantic search"}
            )
    
    def upsert_episode(self, guid: str, text: str, metadata: Dict, embedding: List[float]) -> bool:
        """Upsert an episode with guid, text, metadata, and embedding."""
        try:
            episode_id = f"{guid}_{uuid.uuid4().hex[:8]}"
            
            # Prepare metadata with guid and timestamp
            episode_metadata = {
                "guid": guid,
                "timestamp": datetime.now().isoformat(),
                **metadata
            }
            
            self.collection.upsert(
                ids=[episode_id],
                documents=[text],
                metadatas=[episode_metadata],
                embeddings=[embedding]
            )
            return True
        except Exception as e:
            print(f"Error upserting episode for {guid}: {e}")
            return False
    
    def query_similar(self, guid: str, query: str, k: int = 8, since_days: Optional[int] = 30) -> List[Dict[str, Any]]:
        """Query similar episodes for a guid using titan_embed for query."""
        try:
            # Generate embedding for query using Titan
            query_embeddings = bedrock_client.titan_embed([query])
            if not query_embeddings:
                return []
            
            query_embedding = query_embeddings[0]
            
            # Build where clause for filtering
            where_clause = {"guid": guid}
            if since_days:
                since_date = datetime.now() - timedelta(days=since_days)
                where_clause["timestamp"] = {"$gte": since_date.isoformat()}
            
            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_clause
            )
            
            # Format results
            episodes = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    episodes.append({
                        "id": results["ids"][0][i],
                        "text": doc,
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results["distances"] else 0.0,
                        "similarity": 1 - (results["distances"][0][i] if results["distances"] else 0.0)
                    })
            
            return episodes
        except Exception as e:
            print(f"Error querying similar episodes for {guid}: {e}")
            return []
    
    def add_documents(self, documents: List[str], metadatas: Optional[List[Dict]] = None, ids: Optional[List[str]] = None) -> List[str]:
        """Add documents to the vector store (legacy method)."""
        if not ids:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        if not metadatas:
            metadatas = [{} for _ in documents]
        
        try:
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return ids
        except Exception as e:
            print(f"Error adding documents: {e}")
            return []
    
    def add_embeddings(self, embeddings: List[List[float]], documents: List[str], metadatas: Optional[List[Dict]] = None, ids: Optional[List[str]] = None) -> List[str]:
        """Add pre-computed embeddings to the vector store (legacy method)."""
        if not ids:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        if not metadatas:
            metadatas = [{} for _ in documents]
        
        try:
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            return ids
        except Exception as e:
            print(f"Error adding embeddings: {e}")
            return []
    
    def search(self, query: str, n_results: int = 5, where: Optional[Dict] = None) -> Dict[str, Any]:
        """Search for similar documents (legacy method)."""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            return {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "ids": results["ids"][0] if results["ids"] else []
            }
        except Exception as e:
            print(f"Error searching: {e}")
            return {"documents": [], "metadatas": [], "distances": [], "ids": []}
    
    def search_by_embedding(self, query_embedding: List[float], n_results: int = 5, where: Optional[Dict] = None) -> Dict[str, Any]:
        """Search using pre-computed query embedding (legacy method)."""
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where
            )
            
            return {
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
                "ids": results["ids"][0] if results["ids"] else []
            }
        except Exception as e:
            print(f"Error searching by embedding: {e}")
            return {"documents": [], "metadatas": [], "distances": [], "ids": []}
    
    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        """Retrieve documents by their IDs (legacy method)."""
        try:
            results = self.collection.get(ids=ids)
            return {
                "documents": results["documents"],
                "metadatas": results["metadatas"],
                "ids": results["ids"]
            }
        except Exception as e:
            print(f"Error getting by IDs: {e}")
            return {"documents": [], "metadatas": [], "ids": []}
    
    def delete_by_ids(self, ids: List[str]) -> bool:
        """Delete documents by their IDs (legacy method)."""
        try:
            self.collection.delete(ids=ids)
            return True
        except Exception as e:
            print(f"Error deleting by IDs: {e}")
            return False
    
    def update_metadata(self, ids: List[str], metadatas: List[Dict]) -> bool:
        """Update metadata for existing documents (legacy method)."""
        try:
            self.collection.update(
                ids=ids,
                metadatas=metadatas
            )
            return True
        except Exception as e:
            print(f"Error updating metadata: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the collection."""
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            print(f"Error getting collection info: {e}")
            return {"name": self.collection_name, "count": 0, "persist_directory": self.persist_directory}


# Global ChromaDB store instance
vector_store = ChromaVectorStore()
