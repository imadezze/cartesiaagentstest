// Type definitions for state machine configuration
export interface StateNode {
  id: string;
  name: string;
  type: 'start' | 'end' | 'decision' | 'process' | 'validation' | 'normal' | 'background' | 'trigger';
  description: string;
}

export interface Transition {
  from: string;
  to: string;
  trigger?: string;
  action?: string;
  condition?: string;
}

export interface Flow {
  name: string;
  description: string;
  states: StateNode[];
  transitions: Transition[];
}

export interface SystemComponent {
  id: string;
  name: string;
  type: string;
  description: string;
}

export interface SystemConnection {
  from: string;
  to: string;
  label: string;
  description?: string;
}

export interface SystemArchitecture {
  name: string;
  description: string;
  components: SystemComponent[];
  connections: SystemConnection[];
}

export interface Metadata {
  title: string;
  version: string;
  created: string;
  description: string;
}

export interface ColorScheme {
  start: string;
  end: string;
  decision: string;
  process: string;
  validation: string;
  normal: string;
  background: string;
  trigger: string;
}

export interface StateMachineConfig {
  metadata: Metadata;
  conversation_flow: Flow;
  leads_extraction: Flow;
  research_node: Flow;
  call_validation: Flow;
  system_architecture: SystemArchitecture;
  color_scheme: ColorScheme;
}

// Graph visualization types
export interface GraphNode {
  id: string;
  label: string;
  type: string;
  description: string;
  position?: { x: number; y: number };
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  label: string;
  description?: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}