"""Streamlit UI for the Bedrock-powered Graph + Memory POC."""

import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import pyvis
import networkx as nx

# Page configuration
st.set_page_config(
    page_title="Bedrock Graph + Memory POC",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API base URLs
API_BASE = "http://localhost:8000"
RELAY_BASE = "http://localhost:8001"
MCP_BASE = "http://localhost:8002"


def make_request(method: str, endpoint: str, data: Dict = None) -> Dict:
    """Make a request to the API."""
    url = f"{API_BASE}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=data)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {"error": str(e)}


def main():
    """Main Streamlit application."""
    st.title("🧠 Bedrock Graph + Memory POC")
    st.markdown("A proof-of-concept system for graph-based memory management powered by AWS Bedrock")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["A/B Demo", "Facts", "Evidence", "Why?", "Dashboard", "Add Memory", "Search Memories", "Entity Explorer", "Timeline", "Insights", "System Stats"]
    )
    
    if page == "A/B Demo":
        show_ab_demo()
    elif page == "Facts":
        show_facts()
    elif page == "Evidence":
        show_evidence()
    elif page == "Why?":
        show_why()
    elif page == "Dashboard":
        show_dashboard()
    elif page == "Add Memory":
        show_add_memory()
    elif page == "Search Memories":
        show_search_memories()
    elif page == "Entity Explorer":
        show_entity_explorer()
    elif page == "Timeline":
        show_timeline()
    elif page == "Insights":
        show_insights()
    elif page == "System Stats":
        show_system_stats()


def show_ab_demo():
    """Show the A/B demo interface."""
    st.header("🧪 A/B Demo")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "memory_on" not in st.session_state:
        st.session_state.memory_on = True
    if "context_card" not in st.session_state:
        st.session_state.context_card = None
    if "graph_paths" not in st.session_state:
        st.session_state.graph_paths = None
    
    # Three columns layout
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.subheader("Facts")
        
        # Channel dropdown
        channel = st.selectbox("Channel", ["mock-email", "mock-chat", "mock-voice"])
        
        # Memory toggle
        memory_toggle = st.toggle("Memory ON/OFF", value=st.session_state.memory_on)
        if memory_toggle != st.session_state.memory_on:
            st.session_state.memory_on = memory_toggle
            # Toggle memory in relay
            try:
                response = requests.post(f"{RELAY_BASE}/toggle", json={"on": memory_toggle})
                if response.status_code == 200:
                    st.success(f"Memory {'enabled' if memory_toggle else 'disabled'}")
            except:
                st.error("Failed to toggle memory")
        
        # Action buttons
        if st.button("Remember"):
            if st.session_state.messages:
                last_message = st.session_state.messages[-1]["content"]
                # Write to memory
                memory_data = {
                    "guid": "plan_sponsor_acme",
                    "text": last_message,
                    "channel": channel,
                    "ts": datetime.now().isoformat()
                }
                try:
                    response = requests.post(f"{API_BASE}/memory/write", json=memory_data)
                    if response.status_code == 200:
                        st.success("Memory saved!")
                    else:
                        st.error("Failed to save memory")
                except:
                    st.error("Failed to connect to memory API")
        
        if st.button("Ask"):
            if st.session_state.messages:
                last_message = st.session_state.messages[-1]["content"]
                # Send to relay
                chat_data = {
                    "model": "claude",
                    "messages": st.session_state.messages,
                    "guid": "plan_sponsor_acme",
                    "memory_on": st.session_state.memory_on
                }
                try:
                    response = requests.post(f"{RELAY_BASE}/chat", json=chat_data)
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": result.get("response", "No response")
                        })
                        st.session_state.context_card = result.get("context_card")
                    else:
                        st.error("Failed to get response")
                except:
                    st.error("Failed to connect to relay")
        
        if st.button("Summarize (7d)"):
            # Get summary
            summary_data = {
                "guid": "plan_sponsor_acme",
                "since_days": 7
            }
            try:
                response = requests.post(f"{API_BASE}/memory/summarize", json=summary_data)
                if response.status_code == 200:
                    result = response.json()
                    st.text_area("Summary", result.get("summary", "No summary available"), height=200)
                else:
                    st.error("Failed to get summary")
            except:
                st.error("Failed to connect to memory API")
    
    with col2:
        st.subheader("Chat")
        
        # Chat input
        user_input = st.text_input("Enter message:", key="chat_input")
        
        if st.button("Send") and user_input:
            st.session_state.messages.append({
                "role": "user",
                "content": user_input
            })
            st.rerun()
        
        # Display messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    
    with col3:
        st.subheader("Evidence")
        
        # Context card
        if st.session_state.context_card:
            st.text_area("Context Card", st.session_state.context_card, height=200)
        else:
            st.info("No context card available")
        
        # Graph paths
        if st.session_state.graph_paths:
            st.json(st.session_state.graph_paths)
        else:
            st.info("No graph paths available")


def show_facts():
    """Show facts table with forget buttons."""
    st.header("📋 Facts")
    
    # Get facts for the demo GUID
    try:
        facts = requests.get(f"{API_BASE}/memory/facts?guid=plan_sponsor_acme").json()
        if facts.get("success"):
            facts_data = facts["facts"]
            
            if facts_data:
                # Create DataFrame
                df = pd.DataFrame(facts_data)
                
                # Add forget buttons
                for idx, row in df.iterrows():
                    col1, col2, col3, col4, col5 = st.columns([2, 3, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**{row['key']}**")
                    with col2:
                        st.write(row['value'])
                    with col3:
                        st.write(f"Conf: {row['confidence']:.2f}")
                    with col4:
                        st.write(row['source'])
                    with col5:
                        if st.button("Forget", key=f"forget_{idx}"):
                            # Call forget API
                            forget_data = {
                                "guid": "plan_sponsor_acme",
                                "keys": [row['key']],
                                "hard_delete": False
                            }
                            try:
                                response = requests.post(f"{API_BASE}/memory/forget", json=forget_data)
                                if response.status_code == 200:
                                    st.success("Fact forgotten!")
                                    st.rerun()
                                else:
                                    st.error("Failed to forget fact")
                            except:
                                st.error("Failed to connect to API")
            else:
                st.info("No facts found")
        else:
            st.error("Failed to load facts")
    except:
        st.error("Failed to connect to API")


def show_evidence():
    """Show evidence panel."""
    st.header("🔍 Evidence")
    
    # This would show the last context card and graph path JSON
    st.info("Evidence panel - shows context card and graph paths from memory operations")


def show_why():
    """Show graph visualization."""
    st.header("🤔 Why?")
    
    # Get graph data
    try:
        # Get subgraph
        subgraph_response = requests.get(f"{API_BASE}/graph/subgraph?guid=plan_sponsor_acme")
        if subgraph_response.status_code == 200:
            subgraph_data = subgraph_response.json()
            st.subheader("Subgraph")
            st.json(subgraph_data)
        
        # Get paths to a specific topic
        topic = st.text_input("Enter topic to find paths to:", value="retirement")
        if st.button("Find Paths") and topic:
            paths_response = requests.get(f"{API_BASE}/graph/paths?guid=plan_sponsor_acme&topic={topic}")
            if paths_response.status_code == 200:
                paths_data = paths_response.json()
                st.subheader(f"Paths to '{topic}'")
                st.json(paths_data)
                
                # Simple network visualization
                if paths_data.get("paths"):
                    G = nx.Graph()
                    
                    for path in paths_data["paths"]:
                        nodes = path.get("nodes", [])
                        for i in range(len(nodes) - 1):
                            G.add_edge(nodes[i].get("name", "unknown"), nodes[i+1].get("name", "unknown"))
                    
                    # Create pyvis network
                    net = pyvis.network.Network(height="400px", width="100%")
                    
                    for node in G.nodes():
                        net.add_node(node, label=node)
                    
                    for edge in G.edges():
                        net.add_edge(edge[0], edge[1])
                    
                    # Generate HTML
                    net_html = net.generate_html()
                    st.components.v1.html(net_html, height=400)
            else:
                st.error("Failed to get paths")
    except Exception as e:
        st.error(f"Failed to load graph data: {e}")


def show_dashboard():
    """Show the main dashboard."""
    st.header("📊 Dashboard")
    
    # Check API health
    health_result = make_request("GET", "/health")
    if "error" in health_result:
        st.error("API is not available. Please start the API server.")
        return
    
    st.success("✅ API is running")
    
    # Get system stats
    stats_result = make_request("GET", "/stats")
    if "error" not in stats_result and stats_result.get("success"):
        stats = stats_result["stats"]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Memories", stats["retrieval"]["total_memories"])
        
        with col2:
            graph_stats = stats["retrieval"]["graph_stats"]
            st.metric("Graph Nodes", graph_stats.get("total_nodes", 0))
        
        with col3:
            st.metric("Graph Relationships", graph_stats.get("relationship_count", 0))
    
    # Recent memories
    st.subheader("Recent Memories")
    timeline_result = make_request("GET", "/timeline", {"limit": 5})
    if "error" not in timeline_result and timeline_result.get("success"):
        memories = timeline_result["timeline"]
        for memory in memories:
            with st.expander(f"Memory: {memory['id'][:8]}..."):
                st.write(f"**Text:** {memory['text']}")
                st.write(f"**Source:** {memory.get('source', 'N/A')}")
                st.write(f"**Created:** {memory.get('created_at', 'N/A')}")
                
                entities = memory.get('entities', {})
                if entities:
                    st.write("**Entities:**")
                    for entity_type, entity_list in entities.items():
                        if entity_list:
                            st.write(f"- {entity_type}: {', '.join(entity_list)}")


def show_add_memory():
    """Show the add memory page."""
    st.header("➕ Add Memory")
    
    with st.form("add_memory_form"):
        text = st.text_area("Memory Text", height=100, placeholder="Enter the memory text here...")
        source = st.text_input("Source (optional)", placeholder="e.g., conversation, document, user input")
        
        # Metadata section
        st.subheader("Metadata (optional)")
        col1, col2 = st.columns(2)
        
        with col1:
            memory_type = st.selectbox("Memory Type", ["conversation", "document", "note", "other"])
            priority = st.selectbox("Priority", ["low", "medium", "high"])
        
        with col2:
            tags = st.text_input("Tags (comma-separated)", placeholder="tag1, tag2, tag3")
            author = st.text_input("Author (optional)")
        
        submitted = st.form_submit_button("Add Memory")
        
        if submitted and text:
            metadata = {
                "type": memory_type,
                "priority": priority,
                "author": author
            }
            
            if tags:
                metadata["tags"] = [tag.strip() for tag in tags.split(",")]
            
            data = {
                "text": text,
                "source": source if source else None,
                "metadata": metadata
            }
            
            result = make_request("POST", "/memories", data)
            
            if "error" not in result and result.get("success"):
                st.success("Memory added successfully!")
                st.json(result["memory"])
            else:
                st.error(f"Error adding memory: {result.get('error', 'Unknown error')}")


def show_search_memories():
    """Show the search memories page."""
    st.header("🔍 Search Memories")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input("Search Query", placeholder="Enter your search query...")
    
    with col2:
        search_type = st.selectbox("Search Type", ["semantic", "entity", "metadata"])
    
    limit = st.slider("Number of Results", 1, 20, 5)
    
    if st.button("Search") and query:
        data = {
            "query": query,
            "search_type": search_type,
            "limit": limit
        }
        
        result = make_request("POST", "/search", data)
        
        if "error" not in result and result.get("success"):
            memories = result["results"]
            st.write(f"Found {len(memories)} memories")
            
            for i, memory in enumerate(memories):
                with st.expander(f"Result {i+1}: {memory['id'][:8]}... (Score: {memory.get('similarity_score', 'N/A')})"):
                    st.write(f"**Text:** {memory['text']}")
                    st.write(f"**Source:** {memory.get('source', 'N/A')}")
                    st.write(f"**Created:** {memory.get('created_at', 'N/A')}")
                    
                    entities = memory.get('entities', {})
                    if entities:
                        st.write("**Entities:**")
                        for entity_type, entity_list in entities.items():
                            if entity_list:
                                st.write(f"- {entity_type}: {', '.join(entity_list)}")
        else:
            st.error(f"Search error: {result.get('error', 'Unknown error')}")


def show_entity_explorer():
    """Show the entity explorer page."""
    st.header("🔍 Entity Explorer")
    
    entity_name = st.text_input("Entity Name", placeholder="Enter entity name to explore...")
    entity_type = st.selectbox("Entity Type (optional)", ["", "PERSON", "ORGANIZATION", "LOCATION", "CONCEPT", "EVENT"])
    
    if st.button("Explore Entity") and entity_name:
        params = {"entity_name": entity_name}
        if entity_type:
            params["entity_type"] = entity_type
        
        result = make_request("GET", f"/entities/{entity_name}", params)
        
        if "error" not in result and result.get("success"):
            context = result["context"]
            entity = context["entity"]
            memories = context["memories"]
            relationships = context["relationships"]
            
            if entity:
                st.subheader(f"Entity: {entity.get('name', 'Unknown')}")
                st.write(f"**Type:** {', '.join(entity.get('labels', []))}")
                st.write(f"**ID:** {entity.get('id', 'N/A')}")
                
                # Entity properties
                entity_props = {k: v for k, v in entity.items() if k not in ['id', 'labels']}
                if entity_props:
                    st.write("**Properties:**")
                    st.json(entity_props)
                
                # Related memories
                if memories:
                    st.subheader(f"Related Memories ({len(memories)})")
                    for memory in memories:
                        with st.expander(f"Memory: {memory['id'][:8]}..."):
                            st.write(f"**Text:** {memory['text']}")
                            st.write(f"**Source:** {memory.get('source', 'N/A')}")
                            st.write(f"**Created:** {memory.get('created_at', 'N/A')}")
                
                # Relationships
                if relationships:
                    st.subheader(f"Relationships ({len(relationships)})")
                    for rel in relationships:
                        st.write(f"- **{rel['relationship']['type']}** → {rel['target']['name']} ({', '.join(rel['target_labels'])})")
            else:
                st.warning("Entity not found")
        else:
            st.error(f"Error exploring entity: {result.get('error', 'Unknown error')}")


def show_timeline():
    """Show the timeline page."""
    st.header("📅 Memory Timeline")
    
    entity_filter = st.text_input("Filter by Entity (optional)", placeholder="Enter entity name to filter...")
    limit = st.slider("Number of Memories", 5, 50, 20)
    
    if st.button("Load Timeline"):
        params = {"limit": limit}
        if entity_filter:
            params["entity_name"] = entity_filter
        
        result = make_request("GET", "/timeline", params)
        
        if "error" not in result and result.get("success"):
            memories = result["timeline"]
            st.write(f"Showing {len(memories)} memories")
            
            for memory in memories:
                with st.expander(f"{memory.get('created_at', 'Unknown date')} - {memory['id'][:8]}..."):
                    st.write(f"**Text:** {memory['text']}")
                    st.write(f"**Source:** {memory.get('source', 'N/A')}")
                    
                    entities = memory.get('entities', {})
                    if entities:
                        st.write("**Entities:**")
                        for entity_type, entity_list in entities.items():
                            if entity_list:
                                st.write(f"- {entity_type}: {', '.join(entity_list)}")
        else:
            st.error(f"Error loading timeline: {result.get('error', 'Unknown error')}")


def show_insights():
    """Show the insights page."""
    st.header("💡 Generate Insights")
    
    query = st.text_area("Insight Query", height=100, placeholder="What insights would you like to generate?")
    max_memories = st.slider("Max Memories to Analyze", 5, 50, 10)
    
    if st.button("Generate Insights") and query:
        data = {
            "query": query,
            "max_memories": max_memories
        }
        
        result = make_request("POST", "/insights", data)
        
        if "error" not in result and result.get("success"):
            st.subheader("Generated Insights")
            st.write(result["insights"])
            st.write(f"*Analyzed {result['memories_analyzed']} memories*")
        else:
            st.error(f"Error generating insights: {result.get('error', 'Unknown error')}")


def show_system_stats():
    """Show the system statistics page."""
    st.header("📊 System Statistics")
    
    result = make_request("GET", "/stats")
    
    if "error" not in result and result.get("success"):
        stats = result["stats"]
        
        # Memory statistics
        st.subheader("Memory Statistics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Memories", stats["retrieval"]["total_memories"])
        
        with col2:
            vector_stats = stats["retrieval"]["vector_stats"]
            st.metric("Vector Store Documents", vector_stats.get("count", 0))
        
        # Graph statistics
        st.subheader("Graph Statistics")
        graph_stats = stats["retrieval"]["graph_stats"]
        
        if graph_stats.get("node_counts"):
            st.write("**Nodes by Type:**")
            node_df = pd.DataFrame(list(graph_stats["node_counts"].items()), columns=["Type", "Count"])
            st.dataframe(node_df, use_container_width=True)
        
        st.metric("Total Relationships", graph_stats.get("relationship_count", 0))
        
        # Raw stats
        st.subheader("Raw Statistics")
        st.json(stats)
    else:
        st.error(f"Error loading stats: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
