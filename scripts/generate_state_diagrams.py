#!/usr/bin/env python3
"""
State Machine Diagram Generator for Cartesia Sales Agent

This script generates visual state machine diagrams from JSON configuration files
using NetworkX and Graphviz to create professional-looking state diagrams.

Requirements:
    pip install networkx matplotlib graphviz pydot
    
    Also install system Graphviz:
    macOS: brew install graphviz
    Ubuntu: sudo apt-get install graphviz
    Windows: Download from https://graphviz.org/download/

Usage:
    python generate_state_diagrams.py
"""

import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import sys
from typing import Dict, List, Tuple
import pydot
from networkx.drawing.nx_pydot import graphviz_layout

def create_conversation_flow_graph(data: Dict) -> nx.DiGraph:
    """Create the main conversation flow state machine."""
    G = nx.DiGraph()
    
    # Add nodes with attributes
    for state in data["states"]:
        node_type = state.get("type", "normal")
        G.add_node(
            state["id"], 
            label=state["name"],
            node_type=node_type,
            description=state.get("description", "")
        )
    
    # Add edges with labels
    for transition in data["transitions"]:
        G.add_edge(
            transition["from"],
            transition["to"],
            label=transition["trigger"],
            condition=transition.get("condition", "")
        )
    
    return G

def create_background_agent_graph(agent_data: Dict) -> nx.DiGraph:
    """Create background agent processing flow."""
    G = nx.DiGraph()
    
    for state in agent_data["states"]:
        G.add_node(
            state["id"],
            label=state["name"],
            node_type=state.get("type", "process"),
            description=state.get("description", "")
        )
    
    for transition in agent_data["transitions"]:
        G.add_edge(
            transition["from"],
            transition["to"],
            label=transition.get("action", ""),
            condition=transition.get("condition", "")
        )
    
    return G

def get_node_colors(G: nx.DiGraph) -> Dict[str, str]:
    """Assign colors based on node types."""
    color_map = {
        "start": "#00FF00",      # Bright green - very visible START
        "end": "#FF0000",        # Bright red - very visible END
        "decision": "#FFD700",   # Gold
        "process": "#87CEEB",    # Sky blue
        "validation": "#DDA0DD", # Plum
        "normal": "#F0F8FF",     # Alice blue
        "background": "#E6E6FA", # Lavender
        "trigger": "#FFA07A"     # Light salmon
    }
    
    colors = []
    for node in G.nodes():
        node_type = G.nodes[node].get("node_type", "normal")
        colors.append(color_map.get(node_type, color_map["normal"]))
    
    return colors

def draw_state_diagram(G: nx.DiGraph, title: str, output_path: str, figsize=(16, 12)):
    """Draw and save a state machine diagram."""
    plt.figure(figsize=figsize)
    plt.title(title, fontsize=16, fontweight='bold', pad=20)
    
    # Use graphviz layout for better positioning
    try:
        pos = graphviz_layout(G, prog='dot')
    except:
        # Fallback to spring layout if graphviz not available
        pos = nx.spring_layout(G, k=3, iterations=50)
    
    # Get node colors
    node_colors = get_node_colors(G)
    
    # Draw nodes with different sizes for start/end
    node_sizes = []
    edge_colors = []
    for node in G.nodes():
        node_type = G.nodes[node].get("node_type", "normal")
        if node_type in ["start", "end"]:
            node_sizes.append(4000)  # Larger for start/end
            edge_colors.append('black' if node_type == "start" else 'darkred')
        else:
            node_sizes.append(3000)
            edge_colors.append('black')
    
    nx.draw_networkx_nodes(
        G, pos,
        node_color=node_colors,
        node_size=node_sizes,
        alpha=0.9,
        linewidths=3,
        edgecolors=edge_colors
    )
    
    # Draw node labels
    node_labels = nx.get_node_attributes(G, 'label')
    nx.draw_networkx_labels(G, pos, node_labels, font_size=10, font_weight='bold')
    
    # Draw edges
    nx.draw_networkx_edges(
        G, pos,
        edge_color='gray',
        arrows=True,
        arrowsize=20,
        arrowstyle='->'
    )
    
    # Draw edge labels
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels, font_size=8)
    
    # Create legend with clear START/END indicators
    legend_elements = [
        mpatches.Patch(color='#00FF00', label='🟢 START - Flow Entry Point'),
        mpatches.Patch(color='#FF0000', label='🔴 END - Flow Exit Point'),
        mpatches.Patch(color='#FFD700', label='Decision Point'),
        mpatches.Patch(color='#87CEEB', label='Process State'),
        mpatches.Patch(color='#DDA0DD', label='Validation'),
        mpatches.Patch(color='#F0F8FF', label='Normal State')
    ]
    
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
    plt.axis('off')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Saved diagram: {output_path}")

def create_system_architecture_diagram(data: Dict, output_path: str):
    """Create system architecture overview diagram."""
    G = nx.DiGraph()
    
    # Add components
    components = [
        ("User", "start", "User Input"),
        ("ChatNode", "process", "Main Conversation Handler"),
        ("LeadsNode", "background", "Background Leads Analysis"),
        ("ResearchNode", "background", "Company Research"),
        ("ValidationNode", "validation", "Call Validation"),
        ("Response", "end", "Agent Response")
    ]
    
    for comp_id, comp_type, description in components:
        G.add_node(comp_id, label=comp_id, node_type=comp_type, description=description)
    
    # Add connections
    connections = [
        ("User", "ChatNode", "UserTranscription"),
        ("User", "LeadsNode", "UserStopped"),
        ("LeadsNode", "ChatNode", "LeadsAnalysis"),
        ("LeadsNode", "ResearchNode", "LeadsAnalysis"),
        ("ResearchNode", "ChatNode", "ResearchAnalysis"),
        ("ChatNode", "ValidationNode", "end_call attempt"),
        ("ValidationNode", "Response", "Validation result"),
        ("ChatNode", "Response", "Normal response")
    ]
    
    for from_node, to_node, label in connections:
        G.add_edge(from_node, to_node, label=label)
    
    draw_state_diagram(G, "Cartesia Sales Agent - System Architecture", output_path, figsize=(14, 10))

def generate_all_diagrams():
    """Generate all state machine diagrams."""
    print("🔄 Generating Cartesia Sales Agent State Machine Diagrams...")
    
    # Create output directory
    output_dir = Path("state_diagrams")
    output_dir.mkdir(exist_ok=True)
    
    # Define conversation flow states
    conversation_data = {
        "states": [
            {"id": "start", "name": "🟢 START\nInitial", "type": "start", "description": "Conversation begins"},
            {"id": "greeting", "name": "Greeting\nReceived", "type": "normal", "description": "User provides name/greeting"},
            {"id": "discovery", "name": "Discovery\nActive", "type": "normal", "description": "Agent discovers user needs"},
            {"id": "pain_point", "name": "Pain Point\nReceived", "type": "process", "description": "User shares problems"},
            {"id": "company", "name": "Company\nMentioned", "type": "trigger", "description": "User provides company info"},
            {"id": "research", "name": "Research\nTriggered", "type": "background", "description": "Background research starts"},
            {"id": "value_prop", "name": "Value Prop\nPresentation", "type": "process", "description": "Present tailored solution"},
            {"id": "questions", "name": "Question\nAsked", "type": "decision", "description": "User asks questions"},
            {"id": "contact", "name": "Contact\nCollection", "type": "process", "description": "Collect remaining info"},
            {"id": "validation", "name": "Info\nValidation", "type": "validation", "description": "Check completeness"},
            {"id": "end", "name": "🔴 END\nCall End", "type": "end", "description": "Conversation ends"}
        ],
        "transitions": [
            {"from": "start", "to": "greeting", "trigger": "User greeting"},
            {"from": "start", "to": "pain_point", "trigger": "Direct problem"},
            {"from": "start", "to": "questions", "trigger": "User question"},
            {"from": "greeting", "to": "discovery", "trigger": "Agent asks help"},
            {"from": "discovery", "to": "pain_point", "trigger": "Pain points shared"},
            {"from": "discovery", "to": "company", "trigger": "Company mentioned"},
            {"from": "pain_point", "to": "company", "trigger": "Company provided"},
            {"from": "company", "to": "research", "trigger": "Background research"},
            {"from": "company", "to": "discovery", "trigger": "Continue discovery"},
            {"from": "research", "to": "value_prop", "trigger": "Research complete"},
            {"from": "value_prop", "to": "questions", "trigger": "User questions"},
            {"from": "value_prop", "to": "contact", "trigger": "User satisfied"},
            {"from": "questions", "to": "discovery", "trigger": "Continue conversation"},
            {"from": "questions", "to": "contact", "trigger": "Move to collection"},
            {"from": "contact", "to": "validation", "trigger": "Check info"},
            {"from": "validation", "to": "end", "trigger": "Complete info"},
            {"from": "validation", "to": "discovery", "trigger": "Missing info"},
            {"from": "questions", "to": "end", "trigger": "User satisfied"},
            {"from": "value_prop", "to": "end", "trigger": "User wants to end"}
        ]
    }
    
    # Define leads extraction flow
    leads_data = {
        "states": [
            {"id": "listening", "name": "🟢 START\nListening", "type": "start"},
            {"id": "user_stopped", "name": "User Stopped", "type": "trigger"},
            {"id": "analyzing", "name": "Analyzing\nConversation", "type": "process"},
            {"id": "extracting", "name": "Extracting\nLeads", "type": "process"},
            {"id": "validating", "name": "Validating\nJSON", "type": "validation"},
            {"id": "complete", "name": "Leads\nComplete", "type": "process"},
            {"id": "error", "name": "🔴 END\nLeads Error", "type": "end"},
            {"id": "broadcast", "name": "🔴 END\nBroadcast Leads", "type": "end"}
        ],
        "transitions": [
            {"from": "listening", "to": "user_stopped", "action": "UserStoppedSpeaking"},
            {"from": "user_stopped", "to": "analyzing", "action": "Extract history"},
            {"from": "analyzing", "to": "extracting", "action": "Process with Gemini"},
            {"from": "extracting", "to": "validating", "action": "Parse response"},
            {"from": "validating", "to": "complete", "action": "Valid JSON"},
            {"from": "validating", "to": "error", "action": "Invalid JSON"},
            {"from": "complete", "to": "broadcast", "action": "Emit LeadsAnalysis"},
            {"from": "broadcast", "to": "listening", "action": "Ready for next"},
            {"from": "error", "to": "listening", "action": "Log and continue"}
        ]
    }
    
    # Define research flow
    research_data = {
        "states": [
            {"id": "waiting", "name": "🟢 START\nWaiting", "type": "start"},
            {"id": "leads_received", "name": "Leads\nReceived", "type": "trigger"},
            {"id": "checking_company", "name": "Checking\nCompany", "type": "decision"},
            {"id": "skip_research", "name": "🔴 END\nSkip Research", "type": "end"},
            {"id": "checking_cache", "name": "Checking\nCache", "type": "decision"},
            {"id": "start_research", "name": "Start\nResearch", "type": "process"},
            {"id": "google_search", "name": "Google\nSearch", "type": "process"},
            {"id": "processing", "name": "Processing\nResults", "type": "process"},
            {"id": "extracting", "name": "Extracting\nInsights", "type": "process"},
            {"id": "research_complete", "name": "Research\nComplete", "type": "process"},
            {"id": "broadcast", "name": "🔴 END\nBroadcast Research", "type": "end"}
        ],
        "transitions": [
            {"from": "waiting", "to": "leads_received", "action": "LeadsAnalysis event"},
            {"from": "leads_received", "to": "checking_company", "action": "Extract company"},
            {"from": "checking_company", "to": "skip_research", "action": "No company name"},
            {"from": "checking_company", "to": "checking_cache", "action": "Company exists"},
            {"from": "checking_cache", "to": "skip_research", "action": "Already researched"},
            {"from": "checking_cache", "to": "start_research", "action": "New company"},
            {"from": "start_research", "to": "google_search", "action": "Gemini Live API"},
            {"from": "google_search", "to": "processing", "action": "Multiple queries"},
            {"from": "processing", "to": "extracting", "action": "Parse results"},
            {"from": "extracting", "to": "research_complete", "action": "Structure data"},
            {"from": "research_complete", "to": "broadcast", "action": "Emit ResearchAnalysis"},
            {"from": "broadcast", "to": "waiting", "action": "Ready for next"},
            {"from": "skip_research", "to": "waiting", "action": "Continue waiting"}
        ]
    }
    
    # Define validation flow
    validation_data = {
        "states": [
            {"id": "monitoring", "name": "🟢 START\nMonitoring", "type": "start"},
            {"id": "end_call_requested", "name": "End Call\nRequested", "type": "trigger"},
            {"id": "extracting_leads", "name": "Extracting\nLeads", "type": "process"},
            {"id": "validating_contact", "name": "Validating\nContact", "type": "validation"},
            {"id": "checking_intent", "name": "Checking\nUser Intent", "type": "validation"},
            {"id": "call_approved", "name": "🔴 END\nCall Approved", "type": "end"},
            {"id": "call_blocked", "name": "🔴 END\nCall Blocked", "type": "end"},
            {"id": "generating_message", "name": "Generating\nMessage", "type": "process"}
        ],
        "transitions": [
            {"from": "monitoring", "to": "end_call_requested", "action": "end_call attempt"},
            {"from": "end_call_requested", "to": "extracting_leads", "action": "Get LeadsAnalysis"},
            {"from": "extracting_leads", "to": "validating_contact", "action": "Check fields"},
            {"from": "validating_contact", "to": "checking_intent", "action": "Validate info"},
            {"from": "checking_intent", "to": "call_approved", "action": "All conditions met"},
            {"from": "checking_intent", "to": "call_blocked", "action": "Missing requirements"},
            {"from": "call_approved", "to": "monitoring", "action": "Allow EndCall"},
            {"from": "call_blocked", "to": "generating_message", "action": "Create validation response"},
            {"from": "generating_message", "to": "monitoring", "action": "Send message"}
        ]
    }
    
    # Generate all diagrams
    diagrams = [
        (conversation_data, "User Conversation Flow", "conversation_flow.png"),
        (leads_data, "Leads Extraction Node", "leads_extraction.png"),
        (research_data, "Research Node Flow", "research_flow.png"),
        (validation_data, "Call Validation Flow", "validation_flow.png")
    ]
    
    for data, title, filename in diagrams:
        if "conversation" in filename.lower():
            G = create_conversation_flow_graph(data)
        else:
            G = create_background_agent_graph(data)
        
        output_path = output_dir / filename
        draw_state_diagram(G, f"Cartesia Sales Agent - {title}", str(output_path))
    
    # Generate system architecture diagram
    create_system_architecture_diagram({}, str(output_dir / "system_architecture.png"))
    
    print(f"\n✅ All diagrams generated successfully!")
    print(f"📁 Output directory: {output_dir.absolute()}")
    print(f"📊 Generated {len(diagrams) + 1} diagrams:")
    for _, title, filename in diagrams:
        print(f"   - {filename}: {title}")
    print(f"   - system_architecture.png: System Architecture")

if __name__ == "__main__":
    try:
        generate_all_diagrams()
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\n📦 Please install required packages:")
        print("pip install networkx matplotlib graphviz pydot")
        print("\n🔧 Also install system Graphviz:")
        print("macOS: brew install graphviz")
        print("Ubuntu: sudo apt-get install graphviz")
        print("Windows: Download from https://graphviz.org/download/")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating diagrams: {e}")
        sys.exit(1)