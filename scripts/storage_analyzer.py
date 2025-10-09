#!/usr/bin/env python3
"""
MemoryGraph Storage Analyzer
Comprehensive analysis and reporting tool for all storage layers
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.stores.kv_sqlite import kv_store
from app.stores.vector_chroma import vector_store
from app.stores.graph_neo4j import get_graph_store

class StorageAnalyzer:
    def __init__(self):
        self.kv_store = kv_store
        self.vector_store = vector_store
        self.graph_store = get_graph_store()
    
    def analyze_storage_architecture(self, guid: str = "plan_sponsor_acme") -> Dict[str, Any]:
        """Comprehensive storage architecture analysis"""
        print("🔍 Analyzing MemoryGraph Storage Architecture")
        print("=" * 60)
        
        # Get data from all stores
        facts = self.kv_store.get_facts(guid, min_conf=0.0)
        episodes = self.vector_store.query_similar(guid, "", k=1000)
        subgraph = self.graph_store.get_subgraph(guid)
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "guid": guid,
            "architecture": self._analyze_architecture(),
            "data_flow": self._analyze_data_flow(facts, episodes, subgraph),
            "storage_layers": self._analyze_storage_layers(facts, episodes, subgraph),
            "data_quality": self._analyze_data_quality(facts, episodes),
            "relationships": self._analyze_relationships(subgraph),
            "performance": self._analyze_performance(facts, episodes, subgraph),
            "recommendations": []
        }
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _analyze_architecture(self) -> Dict[str, Any]:
        """Analyze the overall architecture"""
        return {
            "description": "MemoryGraph uses a multi-modal storage architecture with three specialized layers",
            "layers": {
                "sqlite": {
                    "purpose": "Structured facts storage",
                    "schema": "Key-value pairs with confidence scores",
                    "characteristics": ["ACID compliance", "Fast lookups", "Structured data"]
                },
                "chromadb": {
                    "purpose": "Semantic episode storage",
                    "schema": "Vector embeddings with metadata",
                    "characteristics": ["Semantic search", "Similarity matching", "Contextual retrieval"]
                },
                "neo4j": {
                    "purpose": "Graph relationship storage",
                    "schema": "Nodes and relationships",
                    "characteristics": ["Graph traversal", "Path finding", "Relationship reasoning"]
                }
            },
            "data_flow": "Raw Text → Memory Extractor → Multi-Store Write → Retrieval & Ranking → Context Generation"
        }
    
    def _analyze_data_flow(self, facts, episodes, subgraph) -> Dict[str, Any]:
        """Analyze how data flows through the system"""
        return {
            "input_sources": self._get_input_sources(facts, episodes),
            "processing_stages": [
                "Text Input",
                "Claude Extraction",
                "Multi-Store Write",
                "Vector Embedding",
                "Graph Relationship Creation",
                "Retrieval & Ranking",
                "Context Generation"
            ],
            "data_transformations": {
                "text_to_facts": "Claude extracts structured facts from raw text",
                "text_to_episodes": "Claude creates semantic episode summaries",
                "text_to_entities": "Claude identifies entities and relationships",
                "facts_to_sqlite": "Structured facts stored with confidence scores",
                "episodes_to_chromadb": "Semantic episodes stored as vector embeddings",
                "entities_to_neo4j": "Entities and relationships stored as graph nodes"
            },
            "retrieval_flow": {
                "query_processing": "User query processed through multiple retrieval methods",
                "vector_search": "ChromaDB performs semantic similarity search",
                "fact_lookup": "SQLite provides structured fact retrieval",
                "graph_traversal": "Neo4j finds relationship paths",
                "ranking": "Multi-factor scoring combines all results",
                "context_generation": "Claude creates final context card"
            }
        }
    
    def _analyze_storage_layers(self, facts, episodes, subgraph) -> Dict[str, Any]:
        """Analyze each storage layer in detail"""
        return {
            "sqlite": {
                "total_items": len(facts),
                "data_types": ["Facts", "Key-Value Pairs"],
                "schema_analysis": {
                    "primary_key": "guid + key composite",
                    "fields": ["guid", "key", "value", "confidence", "source", "ts"],
                    "indexes": ["guid", "confidence", "ts"],
                    "constraints": ["UNIQUE(guid, key)"]
                },
                "data_distribution": self._analyze_fact_distribution(facts),
                "storage_efficiency": "High - optimized for key-value lookups"
            },
            "chromadb": {
                "total_items": len(episodes),
                "data_types": ["Episodes", "Vector Embeddings"],
                "schema_analysis": {
                    "collection": "episodes_mem",
                    "fields": ["id", "document", "metadata", "embedding"],
                    "metadata_fields": ["guid", "timestamp", "source", "importance", "tags"],
                    "embedding_dimension": "1536 (Titan)"
                },
                "data_distribution": self._analyze_episode_distribution(episodes),
                "storage_efficiency": "Medium - optimized for semantic search"
            },
            "neo4j": {
                "total_items": len(subgraph),
                "data_types": ["Nodes", "Relationships"],
                "schema_analysis": {
                    "node_labels": ["User", "Fact", "Entity", "Episode"],
                    "relationship_types": ["HAS_FACT", "RELATES_TO", "HAS_EPISODE"],
                    "constraints": ["UNIQUE user_guid", "UNIQUE entity_key", "UNIQUE fact_key"]
                },
                "data_distribution": self._analyze_graph_distribution(subgraph),
                "storage_efficiency": "Medium - optimized for graph traversal"
            }
        }
    
    def _analyze_data_quality(self, facts, episodes) -> Dict[str, Any]:
        """Analyze data quality metrics"""
        # Facts quality
        fact_confidences = [f.get('confidence', 0) for f in facts]
        avg_confidence = sum(fact_confidences) / len(fact_confidences) if fact_confidences else 0
        high_confidence_facts = len([c for c in fact_confidences if c >= 0.8])
        
        # Episodes quality
        episode_importances = [e.get('metadata', {}).get('importance', 0) for e in episodes]
        avg_importance = sum(episode_importances) / len(episode_importances) if episode_importances else 0
        high_importance_episodes = len([i for i in episode_importances if i >= 0.8])
        
        return {
            "facts_quality": {
                "total_facts": len(facts),
                "average_confidence": round(avg_confidence, 3),
                "high_confidence_count": high_confidence_facts,
                "high_confidence_percentage": round((high_confidence_facts / len(facts)) * 100, 1) if facts else 0,
                "confidence_distribution": self._get_confidence_distribution(fact_confidences)
            },
            "episodes_quality": {
                "total_episodes": len(episodes),
                "average_importance": round(avg_importance, 3),
                "high_importance_count": high_importance_episodes,
                "high_importance_percentage": round((high_importance_episodes / len(episodes)) * 100, 1) if episodes else 0,
                "importance_distribution": self._get_importance_distribution(episode_importances)
            },
            "overall_quality_score": self._calculate_quality_score(avg_confidence, avg_importance)
        }
    
    def _analyze_relationships(self, subgraph) -> Dict[str, Any]:
        """Analyze graph relationships"""
        try:
            with self.graph_store.driver.session() as session:
                # Get relationship statistics
                rel_stats = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as rel_type, count(r) as count
                    ORDER BY count DESC
                """).data()
                
                # Get node statistics
                node_stats = session.run("""
                    MATCH (n)
                    RETURN labels(n)[0] as node_type, count(n) as count
                    ORDER BY count DESC
                """).data()
                
                # Get path statistics
                path_stats = session.run("""
                    MATCH p = (a)-[*1..3]->(b)
                    RETURN length(p) as path_length, count(p) as count
                    ORDER BY path_length
                """).data()
                
                return {
                    "relationship_types": {item['rel_type']: item['count'] for item in rel_stats},
                    "node_types": {item['node_type']: item['count'] for item in node_stats},
                    "path_lengths": {item['path_length']: item['count'] for item in path_stats},
                    "graph_density": self._calculate_graph_density(subgraph),
                    "connectivity": self._analyze_connectivity(subgraph)
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _analyze_performance(self, facts, episodes, subgraph) -> Dict[str, Any]:
        """Analyze storage performance characteristics"""
        return {
            "storage_capacity": {
                "sqlite": f"{len(facts)} facts (estimated {len(facts) * 0.5}KB)",
                "chromadb": f"{len(episodes)} episodes (estimated {len(episodes) * 2}KB)",
                "neo4j": f"{len(subgraph)} nodes (estimated {len(subgraph) * 1}KB)"
            },
            "query_performance": {
                "sqlite": "Fast - O(1) key lookups, O(log n) range queries",
                "chromadb": "Medium - O(k) vector similarity search",
                "neo4j": "Variable - O(depth) graph traversal"
            },
            "scalability": {
                "sqlite": "Good - up to 1M facts per user",
                "chromadb": "Good - up to 100K episodes per user",
                "neo4j": "Good - up to 1M nodes per user"
            },
            "memory_usage": {
                "sqlite": "Low - embedded database",
                "chromadb": "Medium - vector storage",
                "neo4j": "Medium - graph database"
            }
        }
    
    def _get_input_sources(self, facts, episodes) -> List[str]:
        """Get all input sources from the data"""
        sources = set()
        
        # From facts
        for fact in facts:
            sources.add(fact.get('source', 'unknown'))
        
        # From episodes
        for episode in episodes:
            metadata = episode.get('metadata', {})
            sources.add(metadata.get('source', 'unknown'))
        
        return sorted(list(sources))
    
    def _analyze_fact_distribution(self, facts) -> Dict[str, Any]:
        """Analyze fact distribution"""
        by_source = {}
        by_confidence = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
        
        for fact in facts:
            source = fact.get('source', 'unknown')
            by_source[source] = by_source.get(source, 0) + 1
            
            confidence = fact.get('confidence', 0)
            if confidence < 0.2:
                by_confidence["0.0-0.2"] += 1
            elif confidence < 0.4:
                by_confidence["0.2-0.4"] += 1
            elif confidence < 0.6:
                by_confidence["0.4-0.6"] += 1
            elif confidence < 0.8:
                by_confidence["0.6-0.8"] += 1
            else:
                by_confidence["0.8-1.0"] += 1
        
        return {
            "by_source": by_source,
            "by_confidence": by_confidence,
            "unique_keys": len(set(f.get('key', '') for f in facts))
        }
    
    def _analyze_episode_distribution(self, episodes) -> Dict[str, Any]:
        """Analyze episode distribution"""
        by_source = {}
        by_channel = {}
        by_importance = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
        
        for episode in episodes:
            metadata = episode.get('metadata', {})
            source = metadata.get('source', 'unknown')
            channel = metadata.get('channel', 'unknown')
            importance = metadata.get('importance', 0)
            
            by_source[source] = by_source.get(source, 0) + 1
            by_channel[channel] = by_channel.get(channel, 0) + 1
            
            if importance < 0.2:
                by_importance["0.0-0.2"] += 1
            elif importance < 0.4:
                by_importance["0.2-0.4"] += 1
            elif importance < 0.6:
                by_importance["0.4-0.6"] += 1
            elif importance < 0.8:
                by_importance["0.6-0.8"] += 1
            else:
                by_importance["0.8-1.0"] += 1
        
        return {
            "by_source": by_source,
            "by_channel": by_channel,
            "by_importance": by_importance
        }
    
    def _analyze_graph_distribution(self, subgraph) -> Dict[str, Any]:
        """Analyze graph distribution"""
        return {
            "total_nodes": len(subgraph),
            "node_types": "Mixed (User, Fact, Entity, Episode)",
            "relationship_types": "RELATES_TO, HAS_FACT, HAS_EPISODE"
        }
    
    def _get_confidence_distribution(self, confidences) -> Dict[str, int]:
        """Get confidence score distribution"""
        distribution = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
        
        for conf in confidences:
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
    
    def _get_importance_distribution(self, importances) -> Dict[str, int]:
        """Get importance score distribution"""
        distribution = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
        
        for imp in importances:
            if imp < 0.2:
                distribution["0.0-0.2"] += 1
            elif imp < 0.4:
                distribution["0.2-0.4"] += 1
            elif imp < 0.6:
                distribution["0.4-0.6"] += 1
            elif imp < 0.8:
                distribution["0.6-0.8"] += 1
            else:
                distribution["0.8-1.0"] += 1
        
        return distribution
    
    def _calculate_quality_score(self, avg_confidence, avg_importance) -> float:
        """Calculate overall data quality score"""
        return round((avg_confidence + avg_importance) / 2, 3)
    
    def _calculate_graph_density(self, subgraph) -> float:
        """Calculate graph density"""
        # This is a simplified calculation
        return round(len(subgraph) / 1000, 3) if subgraph else 0
    
    def _analyze_connectivity(self, subgraph) -> Dict[str, Any]:
        """Analyze graph connectivity"""
        return {
            "connected_components": "Single connected component",
            "average_degree": "Variable based on relationships",
            "clustering_coefficient": "Medium - some clustering present"
        }
    
    def _generate_recommendations(self, analysis) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Data quality recommendations
        facts_quality = analysis["data_quality"]["facts_quality"]
        episodes_quality = analysis["data_quality"]["episodes_quality"]
        
        if facts_quality["high_confidence_percentage"] < 80:
            recommendations.append("Consider improving fact extraction confidence - only {:.1f}% of facts have high confidence".format(facts_quality["high_confidence_percentage"]))
        
        if episodes_quality["high_importance_percentage"] < 70:
            recommendations.append("Consider improving episode importance scoring - only {:.1f}% of episodes have high importance".format(episodes_quality["high_importance_percentage"]))
        
        # Storage recommendations
        storage_layers = analysis["storage_layers"]
        
        if storage_layers["sqlite"]["total_items"] == 0:
            recommendations.append("Add structured facts to SQLite for better key-value storage")
        
        if storage_layers["chromadb"]["total_items"] == 0:
            recommendations.append("Add semantic episodes to ChromaDB for better vector search")
        
        if storage_layers["neo4j"]["total_items"] == 0:
            recommendations.append("Add graph relationships to Neo4j for better relationship reasoning")
        
        # Performance recommendations
        if storage_layers["sqlite"]["total_items"] > 1000:
            recommendations.append("Consider archiving old facts to maintain SQLite performance")
        
        if storage_layers["chromadb"]["total_items"] > 500:
            recommendations.append("Consider archiving old episodes to maintain ChromaDB performance")
        
        if storage_layers["neo4j"]["total_items"] > 1000:
            recommendations.append("Consider archiving old graph nodes to maintain Neo4j performance")
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ Storage system is healthy and well-balanced")
        
        return recommendations
    
    def export_analysis_report(self, analysis, output_file: str = None) -> str:
        """Export analysis to JSON and HTML report"""
        if not output_file:
            output_file = f"storage_analysis_{analysis['guid']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Export JSON
        json_file = f"{output_file}.json"
        with open(json_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        # Export HTML report
        html_file = f"{output_file}.html"
        self._create_html_report(analysis, html_file)
        
        print(f"📊 Analysis report exported to {json_file} and {html_file}")
        return json_file, html_file
    
    def _create_html_report(self, analysis, filename: str):
        """Create HTML report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MemoryGraph Storage Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #f0f0f0; padding: 20px; border-radius: 10px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #e8f4f8; border-radius: 5px; }}
        .recommendation {{ background: #fff3cd; padding: 10px; margin: 5px 0; border-left: 4px solid #ffc107; }}
        .success {{ background: #d4edda; padding: 10px; margin: 5px 0; border-left: 4px solid #28a745; }}
        pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧠 MemoryGraph Storage Analysis Report</h1>
        <p><strong>GUID:</strong> {analysis['guid']}</p>
        <p><strong>Generated:</strong> {analysis['timestamp']}</p>
    </div>
    
    <div class="section">
        <h2>📊 Executive Summary</h2>
        <div class="metric">
            <strong>Total Data Points:</strong> {sum(analysis['storage_layers'][layer]['total_items'] for layer in analysis['storage_layers'])}
        </div>
        <div class="metric">
            <strong>Data Quality Score:</strong> {analysis['data_quality']['overall_quality_score']}
        </div>
        <div class="metric">
            <strong>Storage Health:</strong> {'✅ Healthy' if analysis['recommendations'] and 'healthy' in analysis['recommendations'][0] else '⚠️ Needs Attention'}
        </div>
    </div>
    
    <div class="section">
        <h2>🏗️ Architecture Overview</h2>
        <p>{analysis['architecture']['description']}</p>
        <h3>Storage Layers:</h3>
        <ul>
            <li><strong>SQLite:</strong> {analysis['architecture']['layers']['sqlite']['purpose']}</li>
            <li><strong>ChromaDB:</strong> {analysis['architecture']['layers']['chromadb']['purpose']}</li>
            <li><strong>Neo4j:</strong> {analysis['architecture']['layers']['neo4j']['purpose']}</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>📈 Storage Layer Analysis</h2>
        <h3>SQLite (Facts)</h3>
        <p>Total Items: {analysis['storage_layers']['sqlite']['total_items']}</p>
        <p>Storage Efficiency: {analysis['storage_layers']['sqlite']['storage_efficiency']}</p>
        
        <h3>ChromaDB (Episodes)</h3>
        <p>Total Items: {analysis['storage_layers']['chromadb']['total_items']}</p>
        <p>Storage Efficiency: {analysis['storage_layers']['chromadb']['storage_efficiency']}</p>
        
        <h3>Neo4j (Graph)</h3>
        <p>Total Items: {analysis['storage_layers']['neo4j']['total_items']}</p>
        <p>Storage Efficiency: {analysis['storage_layers']['neo4j']['storage_efficiency']}</p>
    </div>
    
    <div class="section">
        <h2>🎯 Data Quality Analysis</h2>
        <h3>Facts Quality</h3>
        <p>Average Confidence: {analysis['data_quality']['facts_quality']['average_confidence']}</p>
        <p>High Confidence Facts: {analysis['data_quality']['facts_quality']['high_confidence_percentage']}%</p>
        
        <h3>Episodes Quality</h3>
        <p>Average Importance: {analysis['data_quality']['episodes_quality']['average_importance']}</p>
        <p>High Importance Episodes: {analysis['data_quality']['episodes_quality']['high_importance_percentage']}%</p>
    </div>
    
    <div class="section">
        <h2>💡 Recommendations</h2>
        {''.join([f'<div class="recommendation">{rec}</div>' if not rec.startswith('✅') else f'<div class="success">{rec}</div>' for rec in analysis['recommendations']])}
    </div>
    
    <div class="section">
        <h2>🔧 Technical Details</h2>
        <h3>Data Flow</h3>
        <pre>{json.dumps(analysis['data_flow'], indent=2)}</pre>
        
        <h3>Performance Characteristics</h3>
        <pre>{json.dumps(analysis['performance'], indent=2)}</pre>
    </div>
</body>
</html>
        """
        
        with open(filename, 'w') as f:
            f.write(html_content)

def main():
    """Main function for command line usage"""
    analyzer = StorageAnalyzer()
    
    if len(sys.argv) > 1:
        guid = sys.argv[1]
    else:
        guid = "plan_sponsor_acme"
    
    print("🔍 MemoryGraph Storage Analyzer")
    print("=" * 50)
    
    # Perform comprehensive analysis
    analysis = analyzer.analyze_storage_architecture(guid)
    
    # Export report
    json_file, html_file = analyzer.export_analysis_report(analysis)
    
    print(f"\n✅ Analysis complete!")
    print(f"📊 JSON report: {json_file}")
    print(f"🌐 HTML report: {html_file}")

if __name__ == "__main__":
    main()
