#!/usr/bin/env python3
"""
Enhanced State Machine Diagram Generator for Cartesia Sales Agent (2025)

This script reads from state_machine_config.json and generates professional 
visual state machine diagrams using NetworkX and Graphviz.

Features:
- Reads configuration from JSON file
- Generates high-quality PNG diagrams
- Professional styling and color schemes
- Multiple layout options
- Error handling and validation

Requirements:
    pip install networkx matplotlib graphviz pydot
    
    System Graphviz installation:
    macOS: brew install graphviz
    Ubuntu: sudo apt-get install graphviz
    Windows: Download from https://graphviz.org/download/

Usage:
    python generate_diagrams_from_json.py [--config state_machine_config.json]
"""

import json
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
import sys
import argparse
from typing import Dict, List, Tuple, Optional
import pydot
from networkx.drawing.nx_pydot import graphviz_layout

class StateMachineDiagramGenerator:
    """Professional state machine diagram generator."""
    
    def __init__(self, config_path: str = "state_machine_config.json"):
        """Initialize with configuration file."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.output_dir = Path("state_diagrams")
        self.output_dir.mkdir(exist_ok=True)
        
    def _load_config(self) -> Dict:
        """Load and validate configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            print(f"✅ Loaded configuration from {self.config_path}")
            return config
        except FileNotFoundError:
            print(f"❌ Configuration file not found: {self.config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in configuration file: {e}")
            sys.exit(1)
    
    def _get_node_color(self, node_type: str) -> str:
        """Get color for node based on type."""
        color_scheme = self.config.get("color_scheme", {})
        return color_scheme.get(node_type, "#F0F8FF")  # Default to alice blue
    
    def _create_graph_from_config(self, section_key: str) -> nx.DiGraph:
        """Create NetworkX graph from configuration section."""
        section = self.config.get(section_key, {})
        G = nx.DiGraph()
        
        # Add nodes
        states = section.get("states", [])
        for state in states:
            G.add_node(
                state["id"],
                label=state["name"],
                node_type=state.get("type", "normal"),
                description=state.get("description", "")
            )
        
        # Add edges
        transitions = section.get("transitions", [])
        for transition in transitions:
            label = transition.get("trigger", transition.get("action", ""))
            G.add_edge(
                transition["from"],
                transition["to"],
                label=label,
                condition=transition.get("condition", "")
            )
        
        return G
    
    def _create_system_architecture_graph(self) -> nx.DiGraph:
        """Create system architecture overview graph."""
        arch_config = self.config.get("system_architecture", {})
        G = nx.DiGraph()
        
        # Add components as nodes
        components = arch_config.get("components", [])
        for comp in components:
            G.add_node(
                comp["id"],
                label=comp["name"],
                node_type=comp.get("type", "normal"),
                description=comp.get("description", "")
            )
        
        # Add connections as edges
        connections = arch_config.get("connections", [])
        for conn in connections:
            G.add_edge(
                conn["from"],
                conn["to"],
                label=conn["label"],
                condition=conn.get("description", "")
            )
        
        return G
    
    def _get_node_colors(self, G: nx.DiGraph) -> List[str]:
        """Get colors for all nodes in graph."""
        colors = []
        for node in G.nodes():
            node_type = G.nodes[node].get("node_type", "normal")
            colors.append(self._get_node_color(node_type))
        return colors
    
    def _draw_state_diagram(self, G: nx.DiGraph, title: str, output_path: str, 
                          figsize: Tuple[int, int] = (16, 12)):
        """Draw and save a professional state machine diagram."""
        plt.figure(figsize=figsize)
        plt.suptitle(title, fontsize=18, fontweight='bold', y=0.95)
        
        # Try different layout algorithms
        layouts = [
            ('dot', 'Hierarchical Layout'),
            ('neato', 'Spring Layout'),
            ('circo', 'Circular Layout'),
            ('fdp', 'Force-Directed Layout')
        ]
        
        pos = None
        layout_used = "spring"
        
        # Try graphviz layouts first
        for prog, name in layouts:
            try:
                pos = graphviz_layout(G, prog=prog)
                layout_used = f"graphviz_{prog}"
                break
            except:
                continue
        
        # Fallback to NetworkX layouts
        if pos is None:
            try:
                pos = nx.spring_layout(G, k=3, iterations=100, seed=42)
                layout_used = "networkx_spring"
            except:
                pos = nx.random_layout(G, seed=42)
                layout_used = "random"
        
        # Get node colors and sizes
        node_colors = self._get_node_colors(G)
        node_sizes = [4000 if G.nodes[node].get("node_type") == "start" else 3000 for node in G.nodes()]
        
        # Draw nodes with enhanced styling
        nx.draw_networkx_nodes(
            G, pos,
            node_color=node_colors,
            node_size=node_sizes,
            alpha=0.9,
            linewidths=2.5,
            edgecolors='black'
        )
        
        # Draw node labels with better formatting
        node_labels = nx.get_node_attributes(G, 'label')
        nx.draw_networkx_labels(
            G, pos, node_labels, 
            font_size=9, 
            font_weight='bold',
            font_color='black'
        )
        
        # Draw edges with improved styling
        nx.draw_networkx_edges(
            G, pos,
            edge_color='#666666',
            arrows=True,
            arrowsize=25,
            arrowstyle='->',
            width=1.5,
            alpha=0.8
        )
        
        # Draw edge labels
        edge_labels = nx.get_edge_attributes(G, 'label')
        if edge_labels:
            nx.draw_networkx_edge_labels(
                G, pos, edge_labels, 
                font_size=8,
                font_color='#333333',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor='none')
            )
        
        # Create comprehensive legend
        legend_elements = [
            mpatches.Patch(color=self._get_node_color('start'), label='Start State'),
            mpatches.Patch(color=self._get_node_color('end'), label='End State'),
            mpatches.Patch(color=self._get_node_color('decision'), label='Decision Point'),
            mpatches.Patch(color=self._get_node_color('process'), label='Process State'),
            mpatches.Patch(color=self._get_node_color('validation'), label='Validation'),
            mpatches.Patch(color=self._get_node_color('background'), label='Background Process'),
            mpatches.Patch(color=self._get_node_color('trigger'), label='Trigger Event'),
            mpatches.Patch(color=self._get_node_color('normal'), label='Normal State')
        ]
        
        plt.legend(
            handles=legend_elements, 
            loc='upper left', 
            bbox_to_anchor=(0, 0.98),
            frameon=True,
            framealpha=0.9,
            fancybox=True,
            shadow=True
        )
        
        # Add metadata
        metadata = self.config.get("metadata", {})
        version = metadata.get("version", "1.0")
        created = metadata.get("created", "2025")
        
        plt.figtext(0.02, 0.02, f'Generated: {created} | Version: {version} | Layout: {layout_used}', 
                   fontsize=8, alpha=0.7)
        
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close()
        print(f"✅ Saved: {output_path}")
    
    def generate_all_diagrams(self):
        """Generate all state machine diagrams from configuration."""
        print("🔄 Generating Cartesia Sales Agent State Machine Diagrams (2025)...")
        
        diagrams = [
            ("conversation_flow", "User Conversation Flow State Machine", "conversation_flow.png"),
            ("leads_extraction", "Leads Extraction Node Processing Flow", "leads_extraction.png"),
            ("research_node", "Research Node Company Intelligence Flow", "research_flow.png"),
            ("call_validation", "Call Validation Safety Check Flow", "validation_flow.png")
        ]
        
        generated_count = 0
        
        # Generate main state machine diagrams
        for section_key, title, filename in diagrams:
            if section_key in self.config:
                G = self._create_graph_from_config(section_key)
                output_path = self.output_dir / filename
                self._draw_state_diagram(G, title, str(output_path))
                generated_count += 1
            else:
                print(f"⚠️  Section '{section_key}' not found in configuration")
        
        # Generate system architecture diagram
        if "system_architecture" in self.config:
            G = self._create_system_architecture_graph()
            output_path = self.output_dir / "system_architecture.png"
            self._draw_state_diagram(
                G, 
                "Cartesia Sales Agent - System Architecture Overview", 
                str(output_path),
                figsize=(14, 10)
            )
            generated_count += 1
        
        # Generate summary report
        self._generate_summary_report(generated_count)
        
        print(f"\n✅ Successfully generated {generated_count} professional diagrams!")
        print(f"📁 Output directory: {self.output_dir.absolute()}")
        
    def _generate_summary_report(self, diagram_count: int):
        """Generate a summary report of the generated diagrams."""
        report_path = self.output_dir / "generation_report.md"
        
        metadata = self.config.get("metadata", {})
        
        with open(report_path, 'w') as f:
            f.write("# State Machine Diagram Generation Report\n\n")
            f.write(f"**Generated:** {metadata.get('created', '2025')}\n")
            f.write(f"**Version:** {metadata.get('version', '1.0')}\n")
            f.write(f"**Total Diagrams:** {diagram_count}\n\n")
            
            f.write("## Generated Diagrams\n\n")
            for file in self.output_dir.glob("*.png"):
                f.write(f"- `{file.name}`: {file.stat().st_size / 1024:.1f} KB\n")
            
            f.write("\n## Configuration Summary\n\n")
            for key, section in self.config.items():
                if key != "metadata" and isinstance(section, dict):
                    states_count = len(section.get("states", []))
                    transitions_count = len(section.get("transitions", []))
                    f.write(f"- **{key}**: {states_count} states, {transitions_count} transitions\n")
        
        print(f"📄 Generated report: {report_path}")

def main():
    """Main function with command line argument parsing."""
    parser = argparse.ArgumentParser(description='Generate State Machine Diagrams for Cartesia Sales Agent')
    parser.add_argument('--config', default='state_machine_config.json',
                       help='Path to configuration JSON file (default: state_machine_config.json)')
    parser.add_argument('--output-dir', default='state_diagrams',
                       help='Output directory for generated diagrams (default: state_diagrams)')
    
    args = parser.parse_args()
    
    try:
        generator = StateMachineDiagramGenerator(args.config)
        generator.output_dir = Path(args.output_dir)
        generator.output_dir.mkdir(exist_ok=True)
        generator.generate_all_diagrams()
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\n📦 Install required packages:")
        print("pip install networkx matplotlib graphviz pydot")
        print("\n🔧 Install system Graphviz:")
        print("macOS: brew install graphviz")
        print("Ubuntu: sudo apt-get install graphviz") 
        print("Windows: Download from https://graphviz.org/download/")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating diagrams: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()