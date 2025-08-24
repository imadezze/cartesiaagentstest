import { StateMachineConfig, Flow, GraphData, GraphNode, GraphEdge, SystemArchitecture } from '@/types';

export const NODE_COLORS = {
  start: '#00FF00',
  end: '#FF0000', 
  decision: '#FFD700',
  process: '#87CEEB',
  validation: '#DDA0DD',
  normal: '#F0F8FF',
  background: '#E6E6FA',
  trigger: '#FFA07A'
};

export const getNodeColor = (type: string): string => {
  return NODE_COLORS[type as keyof typeof NODE_COLORS] || NODE_COLORS.normal;
};

export const getNodeSize = (type: string): number => {
  if (type === 'start' || type === 'end') return 35;
  if (type === 'decision' || type === 'validation') return 30;
  return 28;
};

export const getNodeShape = (type: string): string => {
  switch (type) {
    case 'start': return 'round-rectangle';
    case 'end': return 'round-rectangle';
    case 'decision': return 'diamond';
    case 'validation': return 'hexagon';
    default: return 'ellipse';
  }
};

export const flowToGraphData = (flow: Flow): GraphData => {
  const nodes: GraphNode[] = flow.states.map(state => ({
    id: state.id,
    label: state.name.replace('\\n', '\n'),
    type: state.type,
    description: state.description
  }));

  const edges: GraphEdge[] = flow.transitions.map((transition, index) => {
    const trigger = transition.trigger || transition.action || '';
    const condition = transition.condition || '';
    const label = condition && condition.length < 50 
      ? `${trigger}\n(${condition})` 
      : trigger;

    return {
      id: `edge-${index}`,
      source: transition.from,
      target: transition.to,
      label: label,
      description: condition
    };
  });

  return { nodes, edges };
};

export const systemArchitectureToGraphData = (architecture: SystemArchitecture): GraphData => {
  const nodes: GraphNode[] = architecture.components.map(component => ({
    id: component.id,
    label: component.name,
    type: component.type,
    description: component.description
  }));

  const edges: GraphEdge[] = architecture.connections.map((connection, index) => ({
    id: `edge-${index}`,
    source: connection.from,
    target: connection.to,
    label: connection.label,
    description: connection.description
  }));

  return { nodes, edges };
};

export const truncateText = (text: string, maxLength: number = 30): string => {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

export const formatNodeLabel = (name: string, type: string): string => {
  let prefix = '';
  if (type === 'start') prefix = '🟢 START\n';
  if (type === 'end') prefix = '🔴 END\n';
  
  return prefix + name;
};

// Layout algorithms for better visualization
export const calculateLayout = (nodes: GraphNode[], edges: GraphEdge[]): GraphNode[] => {
  // Simple hierarchical layout
  const startNodes = nodes.filter(n => n.type === 'start');
  const endNodes = nodes.filter(n => n.type === 'end');
  const otherNodes = nodes.filter(n => n.type !== 'start' && n.type !== 'end');

  const layoutNodes = nodes.map(node => ({ ...node }));
  
  // Position start nodes at top
  startNodes.forEach((node, index) => {
    const layoutNode = layoutNodes.find(n => n.id === node.id);
    if (layoutNode) {
      layoutNode.position = { x: index * 200, y: 50 };
    }
  });

  // Position end nodes at bottom
  endNodes.forEach((node, index) => {
    const layoutNode = layoutNodes.find(n => n.id === node.id);
    if (layoutNode) {
      layoutNode.position = { x: index * 200, y: 400 };
    }
  });

  // Position other nodes in middle
  otherNodes.forEach((node, index) => {
    const layoutNode = layoutNodes.find(n => n.id === node.id);
    if (layoutNode && !layoutNode.position) {
      const row = Math.floor(index / 3);
      const col = index % 3;
      layoutNode.position = { x: col * 200, y: 150 + row * 100 };
    }
  });

  return layoutNodes;
};