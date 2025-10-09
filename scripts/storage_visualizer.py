#!/usr/bin/env python3
"""
MemoryGraph Storage Visualizer
Interactive tool to visualize data flow and storage relationships
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import networkx as nx
from collections import defaultdict

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.stores.kv_sqlite import kv_store
from app.stores.vector_chroma import vector_store
from app.stores.graph_neo4j import get_graph_store

class StorageVisualizer:
    def __init__(self):
        self.kv_store = kv_store
        self.vector_store = vector_store
        self.graph_store = get_graph_store()
    
    def create_data_flow_diagram(self, guid: str = "plan_sponsor_acme"):
        """Create a comprehensive data flow diagram"""
        print("🎨 Creating data flow diagram...")
        
        # Get data from all stores
        facts = self.kv_store.get_facts(guid, min_conf=0.0)
        episodes = self.vector_store.query_similar(guid, "", k=1000)
        subgraph = self.graph_store.get_subgraph(guid)
        
        # Create the diagram
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f'MemoryGraph Storage Analysis for {guid}', fontsize=16, fontweight='bold')
        
        # 1. Data Distribution Pie Chart
        self._create_distribution_pie(ax1, facts, episodes, subgraph)
        
        # 2. Source Analysis Bar Chart
        self._create_source_analysis(ax2, facts, episodes)
        
        # 3. Confidence/Importance Distribution
        self._create_confidence_analysis(ax3, facts, episodes)
        
        # 4. Timeline Analysis
        self._create_timeline_analysis(ax4, facts, episodes)
        
        plt.tight_layout()
        plt.savefig(f'storage_analysis_{guid}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png', 
                   dpi=300, bbox_inches='tight')
        print(f"📊 Data flow diagram saved as storage_analysis_{guid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        
        return fig
    
    def _create_distribution_pie(self, ax, facts, episodes, subgraph):
        """Create data distribution pie chart"""
        labels = ['SQLite Facts', 'ChromaDB Episodes', 'Neo4j Graph Nodes']
        sizes = [len(facts), len(episodes), len(subgraph)]
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax.set_title('Data Distribution Across Storage Layers')
        
        # Add count annotations
        for i, (label, size) in enumerate(zip(labels, sizes)):
            ax.annotate(f'{size} items', xy=(0.5, 0.5), xytext=(0, 0), 
                       ha='center', va='center', fontsize=10, fontweight='bold')
    
    def _create_source_analysis(self, ax, facts, episodes):
        """Create source analysis bar chart"""
        # Analyze facts by source
        fact_sources = defaultdict(int)
        for fact in facts:
            fact_sources[fact.get('source', 'unknown')] += 1
        
        # Analyze episodes by source
        episode_sources = defaultdict(int)
        for episode in episodes:
            metadata = episode.get('metadata', {})
            source = metadata.get('source', 'unknown')
            episode_sources[source] += 1
        
        # Combine and sort
        all_sources = set(fact_sources.keys()) | set(episode_sources.keys())
        sources = sorted(all_sources)
        
        fact_counts = [fact_sources[source] for source in sources]
        episode_counts = [episode_sources[source] for source in sources]
        
        x = range(len(sources))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], fact_counts, width, label='Facts', color='#ff9999')
        ax.bar([i + width/2 for i in x], episode_counts, width, label='Episodes', color='#66b3ff')
        
        ax.set_xlabel('Source')
        ax.set_ylabel('Count')
        ax.set_title('Data by Source')
        ax.set_xticks(x)
        ax.set_xticklabels(sources, rotation=45)
        ax.legend()
    
    def _create_confidence_analysis(self, ax, facts, episodes):
        """Create confidence/importance analysis"""
        # Facts confidence distribution
        fact_confidences = [f.get('confidence', 0) for f in facts]
        
        # Episodes importance distribution
        episode_importances = []
        for episode in episodes:
            metadata = episode.get('metadata', {})
            importance = metadata.get('importance', 0)
            episode_importances.append(importance)
        
        # Create histogram
        ax.hist(fact_confidences, bins=20, alpha=0.7, label='Facts Confidence', color='#ff9999')
        ax.hist(episode_importances, bins=20, alpha=0.7, label='Episodes Importance', color='#66b3ff')
        
        ax.set_xlabel('Score')
        ax.set_ylabel('Frequency')
        ax.set_title('Confidence/Importance Distribution')
        ax.legend()
    
    def _create_timeline_analysis(self, ax, facts, episodes):
        """Create timeline analysis"""
        # Extract timestamps and group by day
        fact_timestamps = []
        for fact in facts:
            ts = fact.get('ts', '')
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    fact_timestamps.append(dt.date())
                except:
                    pass
        
        episode_timestamps = []
        for episode in episodes:
            metadata = episode.get('metadata', {})
            ts = metadata.get('timestamp', '')
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    episode_timestamps.append(dt.date())
                except:
                    pass
        
        # Count by date
        fact_counts = defaultdict(int)
        for date in fact_timestamps:
            fact_counts[date] += 1
        
        episode_counts = defaultdict(int)
        for date in episode_timestamps:
            episode_counts[date] += 1
        
        # Get all dates
        all_dates = sorted(set(fact_counts.keys()) | set(episode_counts.keys()))
        
        if all_dates:
            fact_values = [fact_counts[date] for date in all_dates]
            episode_values = [episode_counts[date] for date in all_dates]
            
            ax.plot(all_dates, fact_values, marker='o', label='Facts', color='#ff9999')
            ax.plot(all_dates, episode_values, marker='s', label='Episodes', color='#66b3ff')
            
            ax.set_xlabel('Date')
            ax.set_ylabel('Count')
            ax.set_title('Data Creation Timeline')
            ax.legend()
            ax.tick_params(axis='x', rotation=45)
        else:
            ax.text(0.5, 0.5, 'No timestamp data available', ha='center', va='center', transform=ax.transAxes)
            ax.set_title('Data Creation Timeline')
    
    def create_knowledge_graph_visualization(self, guid: str = "plan_sponsor_acme"):
        """Create an interactive knowledge graph visualization"""
        print("🕸️ Creating knowledge graph visualization...")
        
        try:
            # Get graph data
            with self.graph_store.driver.session() as session:
                # Get all nodes and relationships
                nodes_result = session.run("""
                    MATCH (n)
                    WHERE n.guid = $guid OR n.name IS NOT NULL
                    RETURN n, labels(n) as node_labels
                """, guid=guid)
                
                relationships_result = session.run("""
                    MATCH (a)-[r]->(b)
                    WHERE a.guid = $guid OR b.guid = $guid OR r.predicate IS NOT NULL
                    RETURN a, r, b
                """, guid=guid)
                
                # Build NetworkX graph
                G = nx.Graph()
                
                # Add nodes
                for record in nodes_result:
                    node = record['n']
                    labels = record['node_labels']
                    
                    node_id = node.get('name', node.get('key', str(node.get('id', 'unknown'))))
                    node_type = labels[0] if labels else 'Unknown'
                    
                    G.add_node(node_id, 
                              node_type=node_type,
                              properties=dict(node),
                              guid=node.get('guid', ''),
                              confidence=node.get('confidence', 0))
                
                # Add edges
                for record in relationships_result:
                    source = record['a']
                    rel = record['r']
                    target = record['b']
                    
                    source_id = source.get('name', source.get('key', str(source.get('id', 'unknown'))))
                    target_id = target.get('name', target.get('key', str(target.get('id', 'unknown'))))
                    rel_type = rel.get('predicate', 'RELATES_TO')
                    
                    G.add_edge(source_id, target_id, 
                              relationship_type=rel_type,
                              properties=dict(rel))
                
                # Create visualization
                plt.figure(figsize=(20, 16))
                
                # Layout
                pos = nx.spring_layout(G, k=3, iterations=50)
                
                # Color nodes by type
                node_colors = []
                node_types = nx.get_node_attributes(G, 'node_type')
                type_colors = {
                    'User': '#ff6b6b',
                    'Fact': '#4ecdc4',
                    'Entity': '#45b7d1',
                    'Episode': '#96ceb4',
                    'Unknown': '#f9ca24'
                }
                
                for node in G.nodes():
                    node_type = node_types.get(node, 'Unknown')
                    node_colors.append(type_colors.get(node_type, '#f9ca24'))
                
                # Draw nodes
                nx.draw_networkx_nodes(G, pos, node_color=node_colors, 
                                     node_size=500, alpha=0.8)
                
                # Draw edges
                nx.draw_networkx_edges(G, pos, alpha=0.5, edge_color='gray')
                
                # Draw labels
                nx.draw_networkx_labels(G, pos, font_size=8, font_weight='bold')
                
                # Add legend
                legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                                            markerfacecolor=color, markersize=10, label=node_type)
                                 for node_type, color in type_colors.items()]
                plt.legend(handles=legend_elements, loc='upper right')
                
                plt.title(f'Knowledge Graph for {guid}', fontsize=16, fontweight='bold')
                plt.axis('off')
                
                # Save
                filename = f'knowledge_graph_{guid}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
                plt.savefig(filename, dpi=300, bbox_inches='tight')
                print(f"🕸️ Knowledge graph saved as {filename}")
                
                return G
                
        except Exception as e:
            print(f"❌ Error creating knowledge graph: {e}")
            return None
    
    def create_storage_health_dashboard(self, guid: str = "plan_sponsor_acme"):
        """Create a comprehensive storage health dashboard"""
        print("📊 Creating storage health dashboard...")
        
        # Get comprehensive data
        facts = self.kv_store.get_facts(guid, min_conf=0.0)
        episodes = self.vector_store.query_similar(guid, "", k=1000)
        subgraph = self.graph_store.get_subgraph(guid)
        
        # Create dashboard
        fig = plt.figure(figsize=(20, 12))
        gs = fig.add_gridspec(3, 4, hspace=0.3, wspace=0.3)
        
        # Title
        fig.suptitle(f'MemoryGraph Storage Health Dashboard - {guid}', fontsize=20, fontweight='bold')
        
        # 1. Storage Overview (top left)
        ax1 = fig.add_subplot(gs[0, :2])
        self._create_storage_overview(ax1, facts, episodes, subgraph)
        
        # 2. Data Quality Metrics (top right)
        ax2 = fig.add_subplot(gs[0, 2:])
        self._create_quality_metrics(ax2, facts, episodes)
        
        # 3. Source Distribution (middle left)
        ax3 = fig.add_subplot(gs[1, :2])
        self._create_source_distribution(ax3, facts, episodes)
        
        # 4. Timeline Analysis (middle right)
        ax4 = fig.add_subplot(gs[1, 2:])
        self._create_timeline_analysis(ax4, facts, episodes)
        
        # 5. Confidence Distribution (bottom left)
        ax5 = fig.add_subplot(gs[2, :2])
        self._create_confidence_distribution(ax5, facts, episodes)
        
        # 6. Recommendations (bottom right)
        ax6 = fig.add_subplot(gs[2, 2:])
        self._create_recommendations(ax6, facts, episodes, subgraph)
        
        # Save dashboard
        filename = f'storage_dashboard_{guid}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Storage dashboard saved as {filename}")
        
        return fig
    
    def _create_storage_overview(self, ax, facts, episodes, subgraph):
        """Create storage overview chart"""
        categories = ['SQLite\n(Facts)', 'ChromaDB\n(Episodes)', 'Neo4j\n(Graph)']
        counts = [len(facts), len(episodes), len(subgraph)]
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1']
        
        bars = ax.bar(categories, counts, color=colors, alpha=0.8)
        ax.set_title('Storage Layer Overview', fontweight='bold')
        ax.set_ylabel('Number of Items')
        
        # Add count labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{count}', ha='center', va='bottom', fontweight='bold')
    
    def _create_quality_metrics(self, ax, facts, episodes):
        """Create data quality metrics"""
        # Calculate metrics
        avg_confidence = sum(f.get('confidence', 0) for f in facts) / len(facts) if facts else 0
        avg_importance = sum(e.get('metadata', {}).get('importance', 0) for e in episodes) / len(episodes) if episodes else 0
        
        metrics = ['Avg Confidence\n(Facts)', 'Avg Importance\n(Episodes)']
        values = [avg_confidence, avg_importance]
        colors = ['#ff6b6b', '#4ecdc4']
        
        bars = ax.bar(metrics, values, color=colors, alpha=0.8)
        ax.set_title('Data Quality Metrics', fontweight='bold')
        ax.set_ylabel('Score (0-1)')
        ax.set_ylim(0, 1)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{value:.3f}', ha='center', va='bottom', fontweight='bold')
    
    def _create_source_distribution(self, ax, facts, episodes):
        """Create source distribution chart"""
        # Count by source
        fact_sources = defaultdict(int)
        for fact in facts:
            fact_sources[fact.get('source', 'unknown')] += 1
        
        episode_sources = defaultdict(int)
        for episode in episodes:
            metadata = episode.get('metadata', {})
            source = metadata.get('source', 'unknown')
            episode_sources[source] += 1
        
        # Combine sources
        all_sources = set(fact_sources.keys()) | set(episode_sources.keys())
        sources = sorted(all_sources)
        
        fact_counts = [fact_sources[s] for s in sources]
        episode_counts = [episode_sources[s] for s in sources]
        
        x = range(len(sources))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], fact_counts, width, label='Facts', color='#ff6b6b', alpha=0.8)
        ax.bar([i + width/2 for i in x], episode_counts, width, label='Episodes', color='#4ecdc4', alpha=0.8)
        
        ax.set_title('Data Distribution by Source', fontweight='bold')
        ax.set_xlabel('Source')
        ax.set_ylabel('Count')
        ax.set_xticks(x)
        ax.set_xticklabels(sources, rotation=45)
        ax.legend()
    
    def _create_confidence_distribution(self, ax, facts, episodes):
        """Create confidence distribution histogram"""
        fact_confidences = [f.get('confidence', 0) for f in facts]
        episode_importances = [e.get('metadata', {}).get('importance', 0) for e in episodes]
        
        ax.hist(fact_confidences, bins=20, alpha=0.7, label='Facts Confidence', color='#ff6b6b')
        ax.hist(episode_importances, bins=20, alpha=0.7, label='Episodes Importance', color='#4ecdc4')
        
        ax.set_title('Confidence/Importance Distribution', fontweight='bold')
        ax.set_xlabel('Score')
        ax.set_ylabel('Frequency')
        ax.legend()
    
    def _create_recommendations(self, ax, facts, episodes, subgraph):
        """Create recommendations panel"""
        ax.axis('off')
        ax.set_title('Recommendations', fontweight='bold')
        
        recommendations = []
        
        if len(facts) == 0:
            recommendations.append("• Add structured facts to SQLite")
        if len(episodes) == 0:
            recommendations.append("• Add semantic episodes to ChromaDB")
        if len(subgraph) == 0:
            recommendations.append("• Add graph relationships to Neo4j")
        
        if len(facts) > 0 and len(episodes) > 0 and len(subgraph) > 0:
            recommendations.append("✅ All storage layers populated")
        
        if len(facts) > 100:
            recommendations.append("• Consider archiving old facts")
        
        if len(episodes) > 100:
            recommendations.append("• Consider archiving old episodes")
        
        # Display recommendations
        y_pos = 0.9
        for rec in recommendations:
            ax.text(0.05, y_pos, rec, transform=ax.transAxes, fontsize=10, 
                   color='green' if rec.startswith('✅') else 'black')
            y_pos -= 0.1

def main():
    """Main function for command line usage"""
    visualizer = StorageVisualizer()
    
    if len(sys.argv) > 1:
        guid = sys.argv[1]
    else:
        guid = "plan_sponsor_acme"
    
    print("🎨 MemoryGraph Storage Visualizer")
    print("=" * 50)
    
    # Create all visualizations
    print(f"Creating visualizations for GUID: {guid}")
    
    # 1. Data flow diagram
    visualizer.create_data_flow_diagram(guid)
    
    # 2. Knowledge graph
    visualizer.create_knowledge_graph_visualization(guid)
    
    # 3. Storage health dashboard
    visualizer.create_storage_health_dashboard(guid)
    
    print("\n✅ All visualizations created successfully!")

if __name__ == "__main__":
    main()
