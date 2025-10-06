"""Store modules for the Bedrock-powered Graph + Memory POC."""

from .kv_sqlite import kv_store
from .vector_chroma import vector_store
from .graph_neo4j import get_graph_store

# Lazy initialization for graph store
def get_stores():
    return {
        'kv_store': kv_store,
        'vector_store': vector_store,
        'graph_store': get_graph_store()
    }

__all__ = ["kv_store", "vector_store", "graph_store"]
