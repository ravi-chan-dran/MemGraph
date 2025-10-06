"""Improved Streamlit UI for the Bedrock-powered Graph + Memory POC."""

import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any
import pyvis
import networkx as nx

# Page configuration
st.set_page_config(
    page_title="MemoryGraph - AI with Memory",
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


def show_ab_demo():
    """Show the improved A/B demo interface."""
    st.title("🧪 A/B Testing Demo")
    st.markdown("**Compare AI responses with and without memory context**")
    
    # Initialize session state
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "memory_on" not in st.session_state:
        st.session_state.memory_on = True
    if "context_card" not in st.session_state:
        st.session_state.context_card = None
    if "graph_paths" not in st.session_state:
        st.session_state.graph_paths = None
    
    # Control panel at the top
    st.subheader("🎛️ Control Panel")
    
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        # Memory toggle with clear visual indicator
        memory_toggle = st.toggle(
            "🧠 Memory Context", 
            value=st.session_state.memory_on,
            help="Toggle memory context for AI responses. ON = AI has access to stored memories, OFF = AI responds without context"
        )
        if memory_toggle != st.session_state.memory_on:
            st.session_state.memory_on = memory_toggle
            try:
                response = requests.post(f"{RELAY_BASE}/toggle", json={"on": memory_toggle})
                if response.status_code == 200:
                    st.success(f"Memory context {'enabled' if memory_toggle else 'disabled'}")
            except:
                st.error("Failed to toggle memory")
    
    with col2:
        # Channel selection
        channel = st.selectbox(
            "📡 Source Channel", 
            ["mock-email", "mock-chat", "mock-voice"],
            help="Channel for new memories"
        )
    
    with col3:
        if st.button("💾 Save as Memory", help="Save the last message as a memory"):
            if st.session_state.messages:
                last_message = st.session_state.messages[-1]["content"]
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
            else:
                st.warning("No messages to remember")
    
    with col4:
        if st.button("📊 Get Summary", help="Get a summary of recent memories"):
            summary_data = {
                "guid": "plan_sponsor_acme",
                "since_days": 7
            }
            try:
                response = requests.post(f"{API_BASE}/memory/summarize", json=summary_data)
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.summary = result.get("summary", "No summary available")
                else:
                    st.error("Failed to get summary")
            except:
                st.error("Failed to connect to memory API")
    
    # Show summary if available
    if hasattr(st.session_state, 'summary') and st.session_state.summary:
        with st.expander("📋 Memory Summary", expanded=False):
            st.write(st.session_state.summary)
    
    st.divider()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat Interface")
        
        # Example questions
        st.markdown("**💡 Try these example questions:**")
        example_cols = st.columns(4)
        examples = [
            "What is the match formula?",
            "When is payroll processed?", 
            "What is the auto-enrollment rate?",
            "When are employee communications?"
        ]
        
        for i, example in enumerate(examples):
            with example_cols[i]:
                if st.button(f"💬 {example}", key=f"example_{i}"):
                    st.session_state.messages.append({
                        "role": "user",
                        "content": example
                    })
                    st.rerun()
        
        st.markdown("---")
        
        # Chat input
        user_input = st.text_input(
            "Ask a question about the retirement plan:", 
            placeholder="Type your question here...",
            key="chat_input"
        )
        
        col_send, col_ask = st.columns([1, 1])
        with col_send:
            if st.button("📤 Send Message", type="secondary"):
                if user_input:
                    st.session_state.messages.append({
                        "role": "user",
                        "content": user_input
                    })
                    st.rerun()
                else:
                    st.warning("Please enter a message")
        
        with col_ask:
            if st.button("🤖 Ask AI with Memory", type="primary"):
                if st.session_state.messages:
                    chat_data = {
                        "model": "claude",
                        "messages": st.session_state.messages,
                        "guid": "plan_sponsor_acme",
                        "memory_on": st.session_state.memory_on
                    }
                    try:
                        with st.spinner("Getting AI response..."):
                            response = requests.post(f"{RELAY_BASE}/chat", json=chat_data)
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": result.get("response", "No response")
                            })
                            st.session_state.context_card = result.get("context_card")
                            st.session_state.graph_paths = result.get("graph_hits", [])
                            st.rerun()
                        else:
                            st.error("Failed to get response")
                    except Exception as e:
                        st.error(f"Failed to connect to relay: {e}")
                else:
                    st.warning("No messages to ask about")
        
        # Display chat messages
        if st.session_state.messages:
            st.markdown("**💭 Conversation History**")
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"])
        else:
            st.info("👆 Click an example question above or type your own question to get started!")
    
    with col2:
        st.subheader("🔍 Evidence Panel")
        
        # Memory status indicator
        if st.session_state.memory_on:
            st.success("🧠 **Memory Context: ON**")
            st.caption("AI has access to stored memories")
        else:
            st.warning("🧠 **Memory Context: OFF**")
            st.caption("AI responds without memory context")
        
        # Context card
        if st.session_state.context_card:
            st.markdown("**📄 Context Card**")
            st.caption("Information used by AI to answer your question")
            st.text_area("", st.session_state.context_card, height=150, key="context_display")
        else:
            st.info("No context card available yet")
            st.caption("Context will appear after asking questions with memory ON")
        
        # Graph paths
        if st.session_state.graph_paths:
            st.markdown("**🕸️ Graph Paths**")
            st.caption("How AI connected different pieces of information")
            st.json(st.session_state.graph_paths)
        else:
            st.info("No graph paths available yet")
            st.caption("Graph paths will appear after asking questions")
        
        # Quick stats
        try:
            facts_response = requests.get(f"{API_BASE}/memory/facts?guid=plan_sponsor_acme")
            if facts_response.status_code == 200:
                facts_data = facts_response.json()
                st.metric("📊 Stored Facts", facts_data.get("count", 0))
        except:
            pass


def show_facts():
    """Show stored facts in a clear table."""
    st.header("📊 Stored Facts")
    st.markdown("All facts stored in the memory system")
    
    try:
        response = requests.get(f"{API_BASE}/memory/facts?guid=plan_sponsor_acme")
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("facts"):
                facts_df = pd.DataFrame(data["facts"])
                st.dataframe(facts_df, use_container_width=True)
                st.success(f"Found {len(facts_df)} facts")
            else:
                st.info("No facts found")
        else:
            st.error("Failed to load facts")
    except Exception as e:
        st.error(f"Error loading facts: {e}")


def show_why():
    """Show graph visualization and reasoning."""
    st.header("🤔 Why? - Graph Visualization")
    st.markdown("**Interactive graph showing how AI connects information**")
    
    # Get graph data
    try:
        response = requests.get(f"{API_BASE}/graph/subgraph?guid=plan_sponsor_acme")
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("nodes"):
                nodes = data["nodes"]
                st.success(f"Found {len(nodes)} nodes in the knowledge graph")
                
                # Create NetworkX graph
                G = nx.Graph()
                
                # Add nodes
                for node in nodes:
                    node_id = f"{node['key']}: {node['value']}"
                    G.add_node(node_id, 
                              label=node['key'],
                              value=node['value'],
                              confidence=node['confidence'],
                              source=node['channel'],
                              timestamp=node['ts'])
                
                # Add edges (simplified - connect all nodes to user)
                user_node = "User: plan_sponsor_acme"
                G.add_node(user_node, label="User", value="plan_sponsor_acme")
                
                for node in nodes:
                    node_id = f"{node['key']}: {node['value']}"
                    G.add_edge(user_node, node_id)
                
                # Create Pyvis network
                net = pyvis.network.Network(height="600px", width="100%", bgcolor="#222222", font_color="white")
                
                # Add nodes to Pyvis
                for node in G.nodes():
                    node_data = G.nodes[node]
                    if node == user_node:
                        net.add_node(node, 
                                   label=node_data['label'],
                                   color="#ff6b6b",
                                   size=30,
                                   title=f"User: {node_data['value']}")
                    else:
                        confidence = node_data.get('confidence', 0.5)
                        color_intensity = int(255 * confidence)
                        net.add_node(node,
                                   label=node_data['label'],
                                   color=f"rgb({color_intensity}, {255-color_intensity//2}, 100)",
                                   size=20,
                                   title=f"Key: {node_data['label']}\nValue: {node_data['value']}\nConfidence: {confidence:.2f}\nSource: {node_data.get('source', 'unknown')}\nTime: {node_data.get('timestamp', 'unknown')}")
                
                # Add edges
                for edge in G.edges():
                    net.add_edge(edge[0], edge[1], color="#888888")
                
                # Configure physics
                net.set_options("""
                {
                  "physics": {
                    "enabled": true,
                    "stabilization": {"iterations": 100},
                    "barnesHut": {
                      "gravitationalConstant": -2000,
                      "centralGravity": 0.1,
                      "springLength": 100,
                      "springConstant": 0.05
                    }
                  }
                }
                """)
                
                # Generate HTML
                net_html = net.generate_html()
                
                # Display the graph
                components.html(net_html, height=600)
                
                # Show graph statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Nodes", len(nodes) + 1)
                with col2:
                    st.metric("Total Edges", len(nodes))
                with col3:
                    st.metric("Graph Density", f"{nx.density(G):.3f}")
                
                # Show node details
                with st.expander("📋 Node Details", expanded=False):
                    for node in nodes:
                        st.write(f"**{node['key']}**: {node['value']}")
                        st.write(f"  - Confidence: {node['confidence']}")
                        st.write(f"  - Source: {node['channel']}")
                        st.write(f"  - Time: {node['ts']}")
                        st.write("---")
                
            else:
                st.warning("No graph data available. Try asking some questions first!")
        else:
            st.error("Failed to load graph data")
    except Exception as e:
        st.error(f"Error loading graph: {e}")


def main():
    """Main Streamlit application."""
    st.title("🧠 MemoryGraph")
    st.markdown("**AI with Persistent Memory - A/B Testing Demo**")
    
    # Sidebar navigation
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["A/B Demo", "Facts", "Evidence", "Why?", "Dashboard", "Add Memory", "Search Memories", "System Stats"]
    )
    
    if page == "A/B Demo":
        show_ab_demo()
    elif page == "Facts":
        show_facts()
    elif page == "Evidence":
        st.header("🔍 Evidence")
        st.info("Evidence will appear in the A/B Demo page after asking questions")
    elif page == "Why?":
        show_why()
    elif page == "Dashboard":
        st.header("📊 Dashboard")
        st.info("System overview and statistics")
    elif page == "Add Memory":
        st.header("➕ Add Memory")
        st.info("Add new memories to the system")
    elif page == "Search Memories":
        st.header("🔍 Search Memories")
        st.info("Search through stored memories")
    elif page == "System Stats":
        st.header("📈 System Stats")
        st.info("System performance and statistics")


if __name__ == "__main__":
    main()
