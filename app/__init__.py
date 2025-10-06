"""Main app module for the Bedrock-powered Graph + Memory POC."""

from .core import settings, bedrock_client
from .stores import kv_store, vector_store, get_graph_store
from .memory import memory_extractor, memory_retriever, memory_service
from .api import app

# Lazy initialization for graph store
def graph_store():
    return get_graph_store()

__all__ = [
    "settings",
    "bedrock_client", 
    "kv_store",
    "vector_store", 
    "graph_store",
    "memory_extractor",
    "memory_retriever",
    "memory_service",
    "app"
]
