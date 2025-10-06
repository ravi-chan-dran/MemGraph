"""Neo4j graph store for knowledge graph operations."""

from neo4j import GraphDatabase
from typing import Dict, List, Any, Optional, Tuple
import json
from datetime import datetime, timedelta

from ..core.config import settings


class Neo4jGraphStore:
    """Neo4j-based graph store for knowledge graph operations."""
    
    def __init__(self, uri: Optional[str] = None, user: Optional[str] = None, password: Optional[str] = None):
        """Initialize the Neo4j store."""
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.init_constraints()
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
    
    def init_constraints(self):
        """Initialize database constraints and indexes."""
        with self.driver.session() as session:
            # Create constraints for unique nodes
            session.run("CREATE CONSTRAINT user_guid_unique IF NOT EXISTS FOR (u:User) REQUIRE u.guid IS UNIQUE")
            session.run("CREATE CONSTRAINT entity_key_unique IF NOT EXISTS FOR (e:Entity) REQUIRE (e.name, e.type) IS UNIQUE")
            session.run("CREATE CONSTRAINT fact_key_unique IF NOT EXISTS FOR (f:Fact) REQUIRE (f.key, f.guid) IS UNIQUE")
    
    def upsert_user(self, guid: str) -> bool:
        """Upsert a user node."""
        try:
            with self.driver.session() as session:
                query = """
                MERGE (u:User {guid: $guid})
                SET u.created_at = coalesce(u.created_at, datetime())
                RETURN u
                """
                session.run(query, guid=guid)
                return True
        except Exception as e:
            print(f"Error upserting user {guid}: {e}")
            return False
    
    def upsert_entity(self, name: str, entity_type: str) -> bool:
        """Upsert an entity node."""
        try:
            with self.driver.session() as session:
                query = """
                MERGE (e:Entity {name: $name, type: $type})
                SET e.created_at = coalesce(e.created_at, datetime())
                RETURN e
                """
                session.run(query, name=name, type=entity_type)
                return True
        except Exception as e:
            print(f"Error upserting entity {name}:{entity_type}: {e}")
            return False
    
    def upsert_fact_rel(self, guid: str, key: str, value: str, confidence: float, ts: str, channel: str) -> bool:
        """Upsert a fact relationship."""
        try:
            with self.driver.session() as session:
                # Create fact node
                query = """
                MERGE (f:Fact {key: $key, guid: $guid})
                SET f.value = $value, f.confidence = $confidence, f.ts = $ts, f.channel = $channel
                RETURN f
                """
                session.run(query, key=key, guid=guid, value=value, confidence=confidence, ts=ts, channel=channel)
                
                # Connect to user
                user_query = """
                MATCH (u:User {guid: $guid})
                MATCH (f:Fact {key: $key, guid: $guid})
                MERGE (u)-[:HAS_FACT]->(f)
                """
                session.run(user_query, guid=guid, key=key)
                return True
        except Exception as e:
            print(f"Error upserting fact relation {guid}:{key}: {e}")
            return False
    
    def upsert_triple(self, subject: str, predicate: str, object: str, props: Dict[str, Any]) -> bool:
        """Upsert a triple relationship."""
        try:
            with self.driver.session() as session:
                query = """
                MERGE (s:Entity {name: $subject})
                MERGE (o:Entity {name: $object})
                MERGE (s)-[r:RELATES_TO {predicate: $predicate}]->(o)
                SET r += $props
                RETURN r
                """
                session.run(query, subject=subject, predicate=predicate, object=object, props=props)
                return True
        except Exception as e:
            print(f"Error upserting triple {subject}-{predicate}->{object}: {e}")
            return False
    
    def shortest_path_len(self, guid: str, topic: str) -> int:
        """Get shortest path length between user and topic."""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (u:User {guid: $guid})
                MATCH (t:Entity {name: $topic})
                MATCH path = shortestPath((u)-[*]-(t))
                RETURN length(path) as path_length
                """
                result = session.run(query, guid=guid, topic=topic).single()
                return result["path_length"] if result else 99
        except Exception as e:
            print(f"Error getting shortest path {guid}->{topic}: {e}")
            return 99
    
    def get_subgraph(self, guid: str, since_days: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get subgraph for a user."""
        try:
            with self.driver.session() as session:
                if since_days:
                    since_date = datetime.now() - timedelta(days=since_days)
                    query = """
                    MATCH (u:User {guid: $guid})-[r*1..3]-(n)
                    WHERE r.ts >= $since_date OR r.ts IS NULL
                    RETURN DISTINCT n, labels(n) as node_labels
                    LIMIT 100
                    """
                    result = session.run(query, guid=guid, since_date=since_date.isoformat())
                else:
                    query = """
                    MATCH (u:User {guid: $guid})-[r*1..3]-(n)
                    RETURN DISTINCT n, labels(n) as node_labels
                    LIMIT 100
                    """
                    result = session.run(query, guid=guid)
                
                nodes = []
                for record in result:
                    node_data = dict(record["n"])
                    node_data["labels"] = record["node_labels"]
                    nodes.append(node_data)
                return nodes
        except Exception as e:
            print(f"Error getting subgraph for {guid}: {e}")
            return []
    
    def find_paths(self, guid: str, topic: str, k: int = 3) -> List[Dict[str, Any]]:
        """Find paths between user and topic."""
        try:
            with self.driver.session() as session:
                query = """
                MATCH (u:User {guid: $guid})
                MATCH (t:Entity {name: $topic})
                MATCH path = (u)-[*1..5]-(t)
                RETURN path, length(path) as path_length
                ORDER BY path_length
                LIMIT $k
                """
                result = session.run(query, guid=guid, topic=topic, k=k)
                
                paths = []
                for record in result:
                    path = record["path"]
                    path_data = {
                        "length": record["path_length"],
                        "nodes": [dict(node) for node in path.nodes],
                        "relationships": [dict(rel) for rel in path.relationships]
                    }
                    paths.append(path_data)
                return paths
        except Exception as e:
            print(f"Error finding paths {guid}->{topic}: {e}")
            return []
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the graph."""
        try:
            with self.driver.session() as session:
                # Count nodes by label
                node_counts = {}
                result = session.run("CALL db.labels()")
                for record in result:
                    label = record[0]
                    count_result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                    node_counts[label] = count_result.single()["count"]
                
                # Count relationships
                rel_count_result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
                relationship_count = rel_count_result.single()["count"]
                
                return {
                    "node_counts": node_counts,
                    "relationship_count": relationship_count,
                    "total_nodes": sum(node_counts.values())
                }
        except Exception as e:
            print(f"Error getting graph stats: {e}")
            return {"node_counts": {}, "relationship_count": 0, "total_nodes": 0}
    
    def clear_graph(self) -> bool:
        """Clear all data from the graph."""
        try:
            with self.driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
                return True
        except Exception as e:
            print(f"Error clearing graph: {e}")
            return False


# Global Neo4j store instance (lazy initialization)
graph_store = None

def get_graph_store():
    global graph_store
    if graph_store is None:
        graph_store = Neo4jGraphStore()
    return graph_store
