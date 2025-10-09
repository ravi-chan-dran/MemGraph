#!/usr/bin/env python3
"""
MemoryGraph Storage Inspector
Comprehensive tool to inspect and visualize all storage layers
"""

import sys
import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.stores.kv_sqlite import kv_store
from app.stores.vector_chroma import vector_store
from app.stores.graph_neo4j import get_graph_store

class StorageInspector:
    def __init__(self):
        self.kv_store = kv_store
        self.vector_store = vector_store
        self.graph_store = get_graph_store()
    
    def inspect_all_storage(self, guid: str = "plan_sponsor_acme") -> Dict[str, Any]:
        """Inspect all storage layers for a given GUID"""
        print(f"🔍 Inspecting storage for GUID: {guid}")
        print("=" * 60)
        
        result = {
            "guid": guid,
            "timestamp": datetime.now().isoformat(),
            "sqlite": self.inspect_sqlite(guid),
            "chromadb": self.inspect_chromadb(guid),
            "neo4j": self.inspect_neo4j(guid),
            "summary": {}
        }
        
        # Calculate summary statistics
        result["summary"] = self.calculate_summary(result)
        
        return result
    
    def inspect_sqlite(self, guid: str) -> Dict[str, Any]:
        """Inspect SQLite facts storage"""
        print("\n📊 SQLite (Facts) Storage:")
        print("-" * 30)
        
        try:
            # Get all facts for the GUID
            facts = self.kv_store.get_facts(guid, min_conf=0.0)
            
            # Group by source
            by_source = {}
            for fact in facts:
                source = fact.get('source', 'unknown')
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(fact)
            
            # Calculate statistics
            total_facts = len(facts)
            avg_confidence = sum(f.get('confidence', 0) for f in facts) / total_facts if total_facts > 0 else 0
            
            # Get unique keys
            unique_keys = list(set(f.get('key', '') for f in facts))
            
            result = {
                "total_facts": total_facts,
                "unique_keys": len(unique_keys),
                "average_confidence": round(avg_confidence, 3),
                "by_source": {k: len(v) for k, v in by_source.items()},
                "sample_facts": facts[:5],  # First 5 facts
                "all_keys": unique_keys[:20],  # First 20 keys
                "confidence_distribution": self.get_confidence_distribution(facts)
            }
            
            print(f"  Total Facts: {total_facts}")
            print(f"  Unique Keys: {len(unique_keys)}")
            print(f"  Avg Confidence: {avg_confidence:.3f}")
            print(f"  By Source: {dict(result['by_source'])}")
            print(f"  Sample Facts: {len(result['sample_facts'])}")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {"error": str(e)}
    
    def inspect_chromadb(self, guid: str) -> Dict[str, Any]:
        """Inspect ChromaDB episodes storage"""
        print("\n🔍 ChromaDB (Episodes) Storage:")
        print("-" * 30)
        
        try:
            # Query for episodes (using empty query to get all)
            episodes = self.vector_store.query_similar(guid, "", k=1000)
            
            # Analyze episodes
            total_episodes = len(episodes)
            
            # Extract metadata
            sources = {}
            channels = {}
            importance_scores = []
            
            for episode in episodes:
                metadata = episode.get('metadata', {})
                source = metadata.get('source', 'unknown')
                channel = metadata.get('channel', 'unknown')
                importance = metadata.get('importance', 0)
                
                sources[source] = sources.get(source, 0) + 1
                channels[channel] = channels.get(channel, 0) + 1
                importance_scores.append(importance)
            
            avg_importance = sum(importance_scores) / len(importance_scores) if importance_scores else 0
            
            result = {
                "total_episodes": total_episodes,
                "by_source": sources,
                "by_channel": channels,
                "average_importance": round(avg_importance, 3),
                "sample_episodes": episodes[:3],  # First 3 episodes
                "importance_distribution": self.get_importance_distribution(episodes)
            }
            
            print(f"  Total Episodes: {total_episodes}")
            print(f"  By Source: {sources}")
            print(f"  By Channel: {channels}")
            print(f"  Avg Importance: {avg_importance:.3f}")
            print(f"  Sample Episodes: {len(result['sample_episodes'])}")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {"error": str(e)}
    
    def inspect_neo4j(self, guid: str) -> Dict[str, Any]:
        """Inspect Neo4j graph storage"""
        print("\n🕸️ Neo4j (Graph) Storage:")
        print("-" * 30)
        
        try:
            # Get subgraph for the GUID
            subgraph = self.graph_store.get_subgraph(guid)
            
            # Get all nodes and relationships
            with self.graph_store.driver.session() as session:
                # Count nodes by type
                node_counts = session.run("""
                    MATCH (n)
                    WHERE n.guid = $guid OR n.name IS NOT NULL
                    RETURN labels(n)[0] as node_type, count(n) as count
                    ORDER BY count DESC
                """, guid=guid).data()
                
                # Count relationships
                rel_counts = session.run("""
                    MATCH ()-[r]->()
                    WHERE r.guid = $guid OR r.predicate IS NOT NULL
                    RETURN type(r) as rel_type, count(r) as count
                    ORDER BY count DESC
                """, guid=guid).data()
                
                # Get sample nodes
                sample_nodes = session.run("""
                    MATCH (n)
                    WHERE n.guid = $guid OR n.name IS NOT NULL
                    RETURN n
                    LIMIT 10
                """, guid=guid).data()
            
            result = {
                "total_nodes": len(subgraph),
                "node_types": {item['node_type']: item['count'] for item in node_counts},
                "relationship_types": {item['rel_type']: item['count'] for item in rel_counts},
                "sample_nodes": sample_nodes[:5],
                "subgraph_size": len(subgraph)
            }
            
            print(f"  Total Nodes: {len(subgraph)}")
            print(f"  Node Types: {result['node_types']}")
            print(f"  Relationship Types: {result['relationship_types']}")
            print(f"  Sample Nodes: {len(result['sample_nodes'])}")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {"error": str(e)}
    
    def get_confidence_distribution(self, facts: List[Dict]) -> Dict[str, int]:
        """Get confidence score distribution"""
        distribution = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
        
        for fact in facts:
            conf = fact.get('confidence', 0)
            if conf < 0.2:
                distribution["0.0-0.2"] += 1
            elif conf < 0.4:
                distribution["0.2-0.4"] += 1
            elif conf < 0.6:
                distribution["0.4-0.6"] += 1
            elif conf < 0.8:
                distribution["0.6-0.8"] += 1
            else:
                distribution["0.8-1.0"] += 1
        
        return distribution
    
    def get_importance_distribution(self, episodes: List[Dict]) -> Dict[str, int]:
        """Get importance score distribution"""
        distribution = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
        
        for episode in episodes:
            metadata = episode.get('metadata', {})
            importance = metadata.get('importance', 0)
            if importance < 0.2:
                distribution["0.0-0.2"] += 1
            elif importance < 0.4:
                distribution["0.2-0.4"] += 1
            elif importance < 0.6:
                distribution["0.4-0.6"] += 1
            elif importance < 0.8:
                distribution["0.6-0.8"] += 1
            else:
                distribution["0.8-1.0"] += 1
        
        return distribution
    
    def calculate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics across all storage layers"""
        summary = {
            "total_data_points": 0,
            "storage_health": "unknown",
            "data_distribution": {},
            "recommendations": []
        }
        
        # Count total data points
        sqlite_count = data.get('sqlite', {}).get('total_facts', 0)
        chroma_count = data.get('chromadb', {}).get('total_episodes', 0)
        neo4j_count = data.get('neo4j', {}).get('total_nodes', 0)
        
        summary["total_data_points"] = sqlite_count + chroma_count + neo4j_count
        
        # Data distribution
        summary["data_distribution"] = {
            "facts": sqlite_count,
            "episodes": chroma_count,
            "graph_nodes": neo4j_count
        }
        
        # Health assessment
        if sqlite_count > 0 and chroma_count > 0 and neo4j_count > 0:
            summary["storage_health"] = "healthy"
        elif sqlite_count > 0 or chroma_count > 0 or neo4j_count > 0:
            summary["storage_health"] = "partial"
        else:
            summary["storage_health"] = "empty"
        
        # Recommendations
        if sqlite_count == 0:
            summary["recommendations"].append("No facts stored - consider adding structured data")
        if chroma_count == 0:
            summary["recommendations"].append("No episodes stored - consider adding semantic memories")
        if neo4j_count == 0:
            summary["recommendations"].append("No graph data - consider adding relationships")
        
        return summary
    
    def drill_down_facts(self, guid: str, key_filter: str = None) -> Dict[str, Any]:
        """Drill down into specific facts"""
        print(f"\n🔍 Drilling down into facts for GUID: {guid}")
        if key_filter:
            print(f"Filter: {key_filter}")
        print("-" * 40)
        
        try:
            facts = self.kv_store.get_facts(guid, min_conf=0.0)
            
            if key_filter:
                facts = [f for f in facts if key_filter.lower() in f.get('key', '').lower()]
            
            # Group by key
            by_key = {}
            for fact in facts:
                key = fact.get('key', 'unknown')
                if key not in by_key:
                    by_key[key] = []
                by_key[key].append(fact)
            
            result = {
                "filtered_facts": len(facts),
                "unique_keys": len(by_key),
                "by_key": {k: len(v) for k, v in by_key.items()},
                "detailed_facts": by_key
            }
            
            print(f"  Filtered Facts: {len(facts)}")
            print(f"  Unique Keys: {len(by_key)}")
            
            # Show top keys
            sorted_keys = sorted(by_key.items(), key=lambda x: len(x[1]), reverse=True)
            print(f"  Top Keys: {dict(sorted_keys[:10])}")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {"error": str(e)}
    
    def drill_down_episodes(self, guid: str, source_filter: str = None) -> Dict[str, Any]:
        """Drill down into specific episodes"""
        print(f"\n🔍 Drilling down into episodes for GUID: {guid}")
        if source_filter:
            print(f"Filter: {source_filter}")
        print("-" * 40)
        
        try:
            episodes = self.vector_store.query_similar(guid, "", k=1000)
            
            if source_filter:
                episodes = [e for e in episodes if source_filter.lower() in e.get('metadata', {}).get('source', '').lower()]
            
            # Group by source
            by_source = {}
            for episode in episodes:
                source = episode.get('metadata', {}).get('source', 'unknown')
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(episode)
            
            result = {
                "filtered_episodes": len(episodes),
                "unique_sources": len(by_source),
                "by_source": {k: len(v) for k, v in by_source.items()},
                "detailed_episodes": by_source
            }
            
            print(f"  Filtered Episodes: {len(episodes)}")
            print(f"  Unique Sources: {len(by_source)}")
            
            # Show top sources
            sorted_sources = sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True)
            print(f"  Top Sources: {dict(sorted_sources[:10])}")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {"error": str(e)}
    
    def export_storage_data(self, guid: str, output_file: str = None) -> str:
        """Export all storage data to JSON file"""
        if not output_file:
            output_file = f"storage_export_{guid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = self.inspect_all_storage(guid)
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"\n💾 Storage data exported to: {output_file}")
        return output_file

def main():
    """Main function for command line usage"""
    inspector = StorageInspector()
    
    if len(sys.argv) > 1:
        guid = sys.argv[1]
    else:
        guid = "plan_sponsor_acme"
    
    print("🧠 MemoryGraph Storage Inspector")
    print("=" * 50)
    
    # Full inspection
    data = inspector.inspect_all_storage(guid)
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"  Total Data Points: {data['summary']['total_data_points']}")
    print(f"  Storage Health: {data['summary']['storage_health']}")
    print(f"  Data Distribution: {data['summary']['data_distribution']}")
    
    if data['summary']['recommendations']:
        print(f"  Recommendations:")
        for rec in data['summary']['recommendations']:
            print(f"    - {rec}")
    
    # Export data
    export_file = inspector.export_storage_data(guid)
    
    print(f"\n✅ Inspection complete! Data exported to {export_file}")

if __name__ == "__main__":
    main()
