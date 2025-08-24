'use client';

import React, { useEffect, useRef, useState } from 'react';
import { GraphData, GraphNode, GraphEdge } from '@/types';
import { getNodeColor, getNodeSize, getNodeShape, formatNodeLabel, truncateText } from '@/utils/graphUtils';

interface FlowVisualizationProps {
  data: GraphData;
  title: string;
  onNodeClick?: (node: GraphNode) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
  selectedNode?: string | null;
}

const FlowVisualization: React.FC<FlowVisualizationProps> = ({
  data,
  title,
  onNodeClick,
  onEdgeClick,
  selectedNode
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [hoveredEdge, setHoveredEdge] = useState<string | null>(null);
  const [showFullLabels, setShowFullLabels] = useState(false);

  // Calculate positions for nodes (simple force-directed layout)
  const calculatePositions = () => {
    const width = 1000;
    const height = 600;
    const centerX = width / 2;
    const centerY = height / 2;

    // Find start and end nodes
    const startNodes = data.nodes.filter(n => n.type === 'start');
    const endNodes = data.nodes.filter(n => n.type === 'end');
    const otherNodes = data.nodes.filter(n => n.type !== 'start' && n.type !== 'end');

    const positions: { [key: string]: { x: number; y: number } } = {};

    // Position start nodes at the top
    startNodes.forEach((node, index) => {
      positions[node.id] = {
        x: centerX + (index - (startNodes.length - 1) / 2) * 200,
        y: 100
      };
    });

    // Position end nodes at the bottom
    endNodes.forEach((node, index) => {
      positions[node.id] = {
        x: centerX + (index - (endNodes.length - 1) / 2) * 200,
        y: height - 100
      };
    });

    // Position other nodes in layers
    const layers = Math.ceil(otherNodes.length / 3);
    const layerHeight = (height - 240) / Math.max(layers, 1);

    otherNodes.forEach((node, index) => {
      const layer = Math.floor(index / 3);
      const posInLayer = index % 3;
      const layerWidth = Math.min(3, otherNodes.length - layer * 3);
      
      positions[node.id] = {
        x: centerX + (posInLayer - (layerWidth - 1) / 2) * 250,
        y: 180 + layer * layerHeight
      };
    });

    return positions;
  };

  const positions = calculatePositions();

  const getConnectedNodes = (nodeId: string): string[] => {
    const connected: string[] = [];
    data.edges.forEach(edge => {
      if (edge.source === nodeId) connected.push(edge.target);
      if (edge.target === nodeId) connected.push(edge.source);
    });
    return connected;
  };

  const isNodeHighlighted = (nodeId: string): boolean => {
    if (!selectedNode) return false;
    if (nodeId === selectedNode) return true;
    return getConnectedNodes(selectedNode).includes(nodeId);
  };

  const getEdgePath = (edge: GraphEdge): string => {
    const sourcePos = positions[edge.source];
    const targetPos = positions[edge.target];
    
    if (!sourcePos || !targetPos) return '';

    // Create curved path for better visibility
    const midX = (sourcePos.x + targetPos.x) / 2;
    const midY = (sourcePos.y + targetPos.y) / 2;
    const offsetX = (targetPos.y - sourcePos.y) * 0.2;
    const offsetY = (sourcePos.x - targetPos.x) * 0.2;

    return `M ${sourcePos.x} ${sourcePos.y} Q ${midX + offsetX} ${midY + offsetY} ${targetPos.x} ${targetPos.y}`;
  };

  const getArrowPosition = (edge: GraphEdge) => {
    const sourcePos = positions[edge.source];
    const targetPos = positions[edge.target];
    
    if (!sourcePos || !targetPos) return { x: 0, y: 0, angle: 0 };

    const dx = targetPos.x - sourcePos.x;
    const dy = targetPos.y - sourcePos.y;
    const angle = Math.atan2(dy, dx) * 180 / Math.PI;
    
    // Position arrow closer to target node
    const distance = Math.sqrt(dx * dx + dy * dy);
    const ratio = Math.max(0.7, (distance - 30) / distance);
    
    return {
      x: sourcePos.x + dx * ratio,
      y: sourcePos.y + dy * ratio,
      angle
    };
  };

  return (
    <div className="w-full h-full flex flex-col bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold text-gray-800">{title}</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setShowFullLabels(!showFullLabels)}
              className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 rounded transition-colors"
            >
              {showFullLabels ? 'Short Labels' : 'Full Labels'}
            </button>
          </div>
        </div>
      </div>

      {/* Graph Container */}
      <div className="flex-1 relative overflow-hidden">
        <svg
          ref={svgRef}
          className="w-full h-full"
          viewBox="0 0 1000 600"
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Definitions for arrows and gradients */}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3.5, 0 7"
                fill="#666"
                stroke="#666"
                strokeWidth="1"
              />
            </marker>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feMorphology operator="dilate" radius="2"/>
              <feColorMatrix values="0 0 0 0 0.3 0 0 0 0 0.6 0 0 0 0 1 0 0 0 1 0"/>
              <feGaussianBlur stdDeviation="3"/>
              <feComposite in="SourceGraphic"/>
            </filter>
          </defs>

          {/* Edges */}
          {data.edges.map((edge) => {
            const isHighlighted = selectedNode && 
              (edge.source === selectedNode || edge.target === selectedNode);
            const isHovered = hoveredEdge === edge.id;
            
            return (
              <g key={edge.id}>
                {/* Edge path */}
                <path
                  d={getEdgePath(edge)}
                  fill="none"
                  stroke={isHighlighted ? "#3B82F6" : isHovered ? "#059669" : "#6B7280"}
                  strokeWidth={isHighlighted ? 3 : isHovered ? 2.5 : 2}
                  markerEnd="url(#arrowhead)"
                  className="cursor-pointer transition-all duration-200"
                  filter={isHighlighted ? "url(#glow)" : "none"}
                  onMouseEnter={() => setHoveredEdge(edge.id)}
                  onMouseLeave={() => setHoveredEdge(null)}
                  onClick={() => onEdgeClick?.(edge)}
                />

                {/* Edge label */}
                {edge.label && (
                  <text
                    x={positions[edge.source] && positions[edge.target] ? 
                      (positions[edge.source].x + positions[edge.target].x) / 2 : 0}
                    y={positions[edge.source] && positions[edge.target] ? 
                      (positions[edge.source].y + positions[edge.target].y) / 2 - 10 : 0}
                    textAnchor="middle"
                    className={`text-xs fill-gray-600 font-medium pointer-events-none
                      ${isHighlighted ? 'fill-blue-600' : ''}
                      ${isHovered ? 'fill-green-600' : ''}`}
                    style={{ fontSize: '11px' }}
                  >
                    {showFullLabels ? edge.label : truncateText(edge.label, 20)}
                  </text>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {data.nodes.map((node) => {
            const pos = positions[node.id];
            if (!pos) return null;

            const isHighlighted = isNodeHighlighted(node.id);
            const isSelected = selectedNode === node.id;
            const isHovered = hoveredNode === node.id;
            const size = getNodeSize(node.type);
            const color = getNodeColor(node.type);

            return (
              <g key={node.id}>
                {/* Node glow effect for selected/highlighted nodes */}
                {(isSelected || isHighlighted) && (
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={size + 8}
                    fill={isSelected ? "#3B82F6" : "#10B981"}
                    opacity="0.3"
                    className="animate-pulse"
                  />
                )}

                {/* Main node */}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={size}
                  fill={color}
                  stroke={isSelected ? "#1E40AF" : isHighlighted ? "#059669" : "#374151"}
                  strokeWidth={isSelected ? 4 : isHighlighted ? 3 : 2}
                  className="cursor-pointer transition-all duration-200 hover:stroke-blue-500"
                  onMouseEnter={() => setHoveredNode(node.id)}
                  onMouseLeave={() => setHoveredNode(null)}
                  onClick={() => onNodeClick?.(node)}
                  style={{ 
                    filter: isHovered ? 'brightness(1.1)' : 'none',
                    transform: isHovered ? 'scale(1.05)' : 'scale(1)',
                    transformOrigin: `${pos.x}px ${pos.y}px`
                  }}
                />

                {/* Node label */}
                <text
                  x={pos.x}
                  y={pos.y}
                  textAnchor="middle"
                  dominantBaseline="central"
                  className="pointer-events-none font-semibold text-gray-800"
                  style={{ fontSize: '10px' }}
                >
                  {formatNodeLabel(
                    showFullLabels ? node.label : truncateText(node.label, 15), 
                    node.type
                  )}
                </text>

                {/* Node type indicator */}
                <circle
                  cx={pos.x + size - 10}
                  cy={pos.y - size + 10}
                  r="6"
                  fill="white"
                  stroke={color}
                  strokeWidth="2"
                  className="pointer-events-none"
                />
                <text
                  x={pos.x + size - 10}
                  y={pos.y - size + 10}
                  textAnchor="middle"
                  dominantBaseline="central"
                  className="pointer-events-none font-bold text-gray-700"
                  style={{ fontSize: '8px' }}
                >
                  {node.type.charAt(0).toUpperCase()}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Tooltip for hovered elements */}
        {(hoveredNode || hoveredEdge) && (
          <div className="absolute bottom-4 left-4 bg-gray-900 text-white p-3 rounded-lg shadow-lg max-w-xs">
            {hoveredNode && (
              <div>
                <div className="font-semibold">
                  {data.nodes.find(n => n.id === hoveredNode)?.label}
                </div>
                <div className="text-sm text-gray-300 mt-1">
                  {data.nodes.find(n => n.id === hoveredNode)?.description}
                </div>
                <div className="text-xs text-blue-300 mt-1">
                  Type: {data.nodes.find(n => n.id === hoveredNode)?.type}
                </div>
              </div>
            )}
            {hoveredEdge && (
              <div>
                <div className="font-semibold">
                  {data.edges.find(e => e.id === hoveredEdge)?.label}
                </div>
                {data.edges.find(e => e.id === hoveredEdge)?.description && (
                  <div className="text-sm text-gray-300 mt-1">
                    {data.edges.find(e => e.id === hoveredEdge)?.description}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex flex-wrap gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#00FF00' }}></div>
            <span className="font-medium text-gray-700">START</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#FF0000' }}></div>
            <span className="font-medium text-gray-700">END</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#FFD700' }}></div>
            <span className="font-medium text-gray-700">Decision</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#87CEEB' }}></div>
            <span className="font-medium text-gray-700">Process</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#DDA0DD' }}></div>
            <span className="font-medium text-gray-700">Validation</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#FFA07A' }}></div>
            <span className="font-medium text-gray-700">Trigger</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#E6E6FA' }}></div>
            <span className="font-medium text-gray-700">Background</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FlowVisualization;