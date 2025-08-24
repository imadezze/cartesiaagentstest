'use client';

import React, { useEffect, useRef, useState } from 'react';
import { GraphData, GraphNode, GraphEdge } from '@/types';
import { getNodeColor, getNodeSize, getNodeShape, formatNodeLabel, truncateText, formatNodeLabelForDisplay } from '@/utils/graphUtils';

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
  const [showEdgeLabels, setShowEdgeLabels] = useState(true);
  const [canvasSize, setCanvasSize] = useState<'small' | 'medium' | 'large' | 'auto'>('auto');

  // Canvas size presets
  const getCanvasDimensions = () => {
    const nodeCount = data.nodes.length;
    const edgeCount = data.edges.length;
    
    switch (canvasSize) {
      case 'small':
        return { baseWidth: 600, baseHeight: 400 };
      case 'medium':
        return { baseWidth: 900, baseHeight: 600 };
      case 'large':
        return { baseWidth: 1200, baseHeight: 800 };
      case 'auto':
      default:
        // Dynamic sizing based on content - calculate width based on actual layers
        // First do a quick topological analysis to estimate layers
        const inDegreeTemp: { [key: string]: number } = {};
        const adjacencyListTemp: { [key: string]: string[] } = {};
        
        data.nodes.forEach(node => {
          inDegreeTemp[node.id] = 0;
          adjacencyListTemp[node.id] = [];
        });
        
        data.edges.forEach(edge => {
          adjacencyListTemp[edge.source].push(edge.target);
          inDegreeTemp[edge.target]++;
        });
        
        // Quick layer estimation
        const startNodes = data.nodes.filter(n => n.type === 'start' || inDegreeTemp[n.id] === 0);
        let estimatedLayers = Math.max(1, Math.ceil(nodeCount / 3)); // Simple estimation
        
        const minWidth = 800; // Increased minimum width
        const layerWidth = 220; // Increased base width per layer
        const baseWidth = Math.max(minWidth, estimatedLayers * layerWidth + 400); // More padding
        
        // Calculate height based on maximum nodes that might stack vertically
        const maxNodesInLayer = Math.min(Math.ceil(nodeCount / Math.max(estimatedLayers, 1)), 6);
        const minHeight = 400;
        const baseHeight = Math.max(minHeight, maxNodesInLayer * 120 + 200);
        return { baseWidth, baseHeight };
    }
  };

  // Adaptive layout algorithm that analyzes graph complexity
  const calculatePositions = () => {
    const nodeCount = data.nodes.length;
    const edgeCount = data.edges.length;
    
    const { baseWidth, baseHeight } = getCanvasDimensions();
    const width = baseWidth;
    const height = baseHeight;
    const centerY = height / 2;
    const margin = 60;
    const positions: { [key: string]: { x: number; y: number } } = {};

    // Graph complexity already analyzed above for dimension calculation
    const avgEdgesPerNode = nodeCount > 0 ? edgeCount / nodeCount : 0;
    const edgeDensity = nodeCount > 1 ? (2 * edgeCount) / (nodeCount * (nodeCount - 1)) : 0;
    
    // Build dependency graph
    const inDegree: { [key: string]: number } = {};
    const adjacencyList: { [key: string]: string[] } = {};
    
    data.nodes.forEach(node => {
      inDegree[node.id] = 0;
      adjacencyList[node.id] = [];
    });
    
    data.edges.forEach(edge => {
      adjacencyList[edge.source].push(edge.target);
      inDegree[edge.target]++;
    });

    // Topological sort to create layers
    const startNodes = data.nodes.filter(n => n.type === 'start');
    const layers: string[][] = [];
    const queue = [...startNodes.map(n => n.id)];
    const visited = new Set<string>();
    const currentInDegree = { ...inDegree };

    while (queue.length > 0) {
      const currentLayer: string[] = [];
      const nextQueue: string[] = [];

      for (const nodeId of queue) {
        if (visited.has(nodeId)) continue;
        currentLayer.push(nodeId);
        visited.add(nodeId);

        adjacencyList[nodeId].forEach(childId => {
          currentInDegree[childId]--;
          if (currentInDegree[childId] === 0 && !visited.has(childId) && !nextQueue.includes(childId)) {
            nextQueue.push(childId);
          }
        });
      }

      if (currentLayer.length > 0) {
        layers.push(currentLayer);
      }

      queue.length = 0;
      queue.push(...nextQueue);
    }

    // Add remaining unvisited nodes
    const unvisited = data.nodes.filter(n => !visited.has(n.id));
    if (unvisited.length > 0) {
      layers.push(unvisited.map(n => n.id));
    }

    // Adaptive spacing calculation based on graph complexity - horizontal layout
    const availableWidth = width - 2 * margin;
    const availableHeight = height - 2 * margin;
    
    // Calculate optimal layout parameters based on canvas size
    const maxLayerSize = Math.max(...layers.map(layer => layer.length));
    const layerCount = layers.length;
    
    // Adaptive max nodes per column based on canvas size and graph complexity
    let maxNodesPerCol: number;
    
    // Calculate how many nodes can fit vertically based on available height
    const nodeSize = 40; // Approximate node diameter
    const minVerticalSpacing = 20;
    const maxVerticalNodes = Math.floor(availableHeight / (nodeSize + minVerticalSpacing));
    
    // Adjust node density based on canvas size - for vertical stacking in horizontal layout
    const sizeMultiplier = canvasSize === 'small' ? 0.8 : canvasSize === 'large' ? 1.2 : 1.0;
    
    if (canvasSize === 'small') {
      maxNodesPerCol = Math.min(maxVerticalNodes, Math.max(2, Math.ceil(3 * sizeMultiplier)));
    } else if (canvasSize === 'large') {
      maxNodesPerCol = Math.min(maxVerticalNodes, Math.max(3, Math.ceil(5 * sizeMultiplier)));
    } else {
      maxNodesPerCol = Math.min(maxVerticalNodes, Math.max(2, Math.ceil(4 * sizeMultiplier)));
    }
    
    // Calculate optimal spacing based on available space, node count, and canvas size
    const estimatedTotalCols = layers.reduce((total, layer) => 
      total + Math.ceil(layer.length / maxNodesPerCol), 0);
    
    // Adjust spacing based on canvas size - horizontal layout
    const minLayerWidth = canvasSize === 'small' ? 120 : 150; // Width between layers (columns)
    const maxLayerWidth = canvasSize === 'small' ? 200 : canvasSize === 'large' ? 250 : 220;
    const minNodeSpacing = canvasSize === 'small' ? 80 : 100; // Vertical spacing between nodes
    const maxNodeSpacing = canvasSize === 'small' ? 150 : canvasSize === 'large' ? 200 : 180;
    
    const optimalLayerWidth = Math.max(minLayerWidth, 
      Math.min(maxLayerWidth, availableWidth / Math.max(layers.length, 1)));
    
    const optimalNodeSpacing = Math.max(minNodeSpacing, 
      Math.min(maxNodeSpacing, availableHeight / Math.max(maxNodesPerCol, 2)));
    
    // Position nodes with adaptive spacing - horizontal layout
    let currentX = margin;
    
    layers.forEach((layer, layerIndex) => {
      if (layer.length === 0) return;
      
      const colsNeeded = Math.ceil(layer.length / maxNodesPerCol);
      
      // Sort nodes within layer to minimize crossings
      if (layerIndex > 0) {
        layer.sort((a, b) => {
          const getAvgPredecessorY = (nodeId: string) => {
            const predecessors = data.edges
              .filter(edge => edge.target === nodeId)
              .map(edge => positions[edge.source])
              .filter(Boolean);
            
            if (predecessors.length === 0) return centerY;
            return predecessors.reduce((sum, pos) => sum + pos.y, 0) / predecessors.length;
          };
          
          return getAvgPredecessorY(a) - getAvgPredecessorY(b);
        });
      }
      
      // Position nodes in adaptive columns
      for (let col = 0; col < colsNeeded; col++) {
        const startIdx = col * maxNodesPerCol;
        const endIdx = Math.min(startIdx + maxNodesPerCol, layer.length);
        const colNodes = layer.slice(startIdx, endIdx);
        
        const colSpacingMultiplier = colsNeeded > 1 ? 0.8 : 1.0;
        const x = currentX + (col * optimalLayerWidth * colSpacingMultiplier);
        
        if (colNodes.length === 1) {
          // For single node, use better vertical distribution
          const layerVerticalPosition = layerIndex === 0 ? centerY : // First layer at center
            layerIndex < layers.length / 2 ? centerY - (layers.length * 30) + (layerIndex * 60) : // Upper half
            centerY + ((layerIndex - layers.length / 2) * 60); // Lower half
          positions[colNodes[0]] = { x, y: layerVerticalPosition };
        } else {
          // Adaptive vertical spacing based on column size - use more vertical space
          const actualNodeSpacing = Math.max(optimalNodeSpacing * 0.8, 
            Math.min(optimalNodeSpacing * 1.5, availableHeight / Math.max(colNodes.length + 1, 3)));
          const totalHeight = (colNodes.length - 1) * actualNodeSpacing;
          
          // Spread nodes across more vertical space instead of centering tightly
          const verticalRange = availableHeight * 0.7; // Use 70% of available height
          const effectiveSpacing = Math.min(actualNodeSpacing, verticalRange / Math.max(colNodes.length - 1, 1));
          const startY = margin + (availableHeight - (colNodes.length - 1) * effectiveSpacing) / 2;
          
          colNodes.forEach((nodeId, idx) => {
            positions[nodeId] = {
              x,
              y: startY + idx * effectiveSpacing
            };
          });
        }
      }
      
      // Adaptive layer spacing - distribute evenly across available width
      if (layerIndex === layers.length - 1) {
        // Last layer - no additional spacing needed
      } else {
        // Calculate remaining width and distribute evenly among remaining layers
        const remainingLayers = layers.length - layerIndex - 1;
        // Reserve space for right margin by reducing available width
        const reservedRightMargin = 80; // Extra space for rightmost nodes
        const usableWidth = availableWidth - reservedRightMargin;
        const remainingWidth = usableWidth - (currentX - margin);
        const optimalSpacing = remainingLayers > 0 ? Math.max(minLayerWidth, remainingWidth / remainingLayers) : optimalLayerWidth;
        const actualSpacing = Math.max(minLayerWidth, Math.min(optimalSpacing, maxLayerWidth * 1.2));
        currentX += actualSpacing;
      }
    });

    return { positions, width, height };
  };

  const { positions, width, height } = calculatePositions();

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

  const getEdgePath = (edge: GraphEdge, edgeIndex?: number): string => {
    const sourcePos = positions[edge.source];
    const targetPos = positions[edge.target];
    
    if (!sourcePos || !targetPos) return '';

    // Get node sizes to calculate edge endpoints at circle boundaries
    const sourceNode = data.nodes.find(n => n.id === edge.source);
    const targetNode = data.nodes.find(n => n.id === edge.target);
    
    if (!sourceNode || !targetNode) return '';
    
    const sourceBaseSize = getNodeSize(sourceNode.type);
    const targetBaseSize = getNodeSize(targetNode.type);
    const sizeMultiplier = canvasSize === 'small' ? 0.8 : canvasSize === 'large' ? 1.2 : 1.0;
    const sourceRadius = Math.round(sourceBaseSize * sizeMultiplier);
    const targetRadius = Math.round(targetBaseSize * sizeMultiplier);

    // Check if there are multiple edges between the same nodes
    const parallelEdges = data.edges.filter(e => 
      (e.source === edge.source && e.target === edge.target) ||
      (e.source === edge.target && e.target === edge.source)
    );
    
    let offsetX = 0;
    let offsetY = 0;
    
    // If there are multiple edges, offset them to make them visible
    if (parallelEdges.length > 1 && edgeIndex !== undefined) {
      const currentIndex = parallelEdges.findIndex(e => e.id === edge.id);
      const offsetAmount = 15;
      const offsetDirection = currentIndex - (parallelEdges.length - 1) / 2;
      
      // Calculate perpendicular offset
      const dx = targetPos.x - sourcePos.x;
      const dy = targetPos.y - sourcePos.y;
      const length = Math.sqrt(dx * dx + dy * dy);
      
      if (length > 0) {
        // Perpendicular vector
        const perpX = -dy / length;
        const perpY = dx / length;
        
        offsetX = perpX * offsetAmount * offsetDirection;
        offsetY = perpY * offsetAmount * offsetDirection;
      }
    }

    // Calculate direction vector
    const dx = targetPos.x - sourcePos.x;
    const dy = targetPos.y - sourcePos.y;
    const distance = Math.sqrt(dx * dx + dy * dy);
    
    if (distance === 0) return '';
    
    // Normalize direction vector
    const dirX = dx / distance;
    const dirY = dy / distance;
    
    // Calculate start and end points at circle boundaries
    const startX = sourcePos.x + dirX * sourceRadius + offsetX;
    const startY = sourcePos.y + dirY * sourceRadius + offsetY;
    const endX = targetPos.x - dirX * targetRadius + offsetX;
    const endY = targetPos.y - dirY * targetRadius + offsetY;
    
    const newDx = endX - startX;
    const newDy = endY - startY;
    
    // Use smart curve calculation to avoid overlaps
    const newDistance = Math.sqrt(newDx * newDx + newDy * newDy);
    
    if (newDistance < 50) {
      // Very close nodes - straight line
      return `M ${startX} ${startY} L ${endX} ${endY}`;
    }
    
    // Calculate curve control points to create clean arcs
    const midX = (startX + endX) / 2;
    const midY = (startY + endY) / 2;
    
    // Adaptive curvature based on distance and direction
    let curvature = Math.min(newDistance * 0.3, 80);
    
    // If edge crosses many other edges, increase curvature to go around
    if (Math.abs(newDy) > Math.abs(newDx)) {
      // Vertical-ish edge - curve horizontally
      curvature *= 0.7;
      const controlX = midX + (startX < endX ? curvature : -curvature);
      const controlY = midY;
      return `M ${startX} ${startY} Q ${controlX} ${controlY} ${endX} ${endY}`;
    } else {
      // Horizontal-ish edge - curve vertically
      const controlX = midX;
      const controlY = midY + (startY < endY ? -curvature * 0.8 : curvature * 0.8);
      return `M ${startX} ${startY} Q ${controlX} ${controlY} ${endX} ${endY}`;
    }
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
          <div className="flex gap-3">
            <button
              onClick={() => setShowFullLabels(!showFullLabels)}
              className="px-4 py-2 text-sm font-medium bg-white border-2 border-blue-300 text-blue-700 hover:bg-blue-50 hover:border-blue-400 rounded-lg shadow-sm transition-colors"
            >
              {showFullLabels ? 'Short Labels' : 'Full Labels'}
            </button>
            <button
              onClick={() => setShowEdgeLabels(!showEdgeLabels)}
              className="px-4 py-2 text-sm font-medium bg-white border-2 border-green-300 text-green-700 hover:bg-green-50 hover:border-green-400 rounded-lg shadow-sm transition-colors"
            >
              {showEdgeLabels ? 'Hide Edge Text' : 'Show Edge Text'}
            </button>
            <select
              value={canvasSize}
              onChange={(e) => setCanvasSize(e.target.value as 'small' | 'medium' | 'large' | 'auto')}
              className="px-4 py-2 text-sm font-medium bg-white border-2 border-purple-300 text-purple-700 hover:bg-purple-50 hover:border-purple-400 rounded-lg shadow-sm transition-colors"
            >
              <option value="auto">Auto Size</option>
              <option value="small">Small (600x400)</option>
              <option value="medium">Medium (900x600)</option>
              <option value="large">Large (1200x800)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Graph Container */}
      <div className="flex-1 relative overflow-hidden">
        <svg
          ref={svgRef}
          className="w-full h-full"
          viewBox={`0 0 ${width} ${height}`}
          preserveAspectRatio="xMidYMid meet"
        >
          {/* Definitions for arrows and gradients */}
          <defs>
            <marker
              id="arrowhead"
              markerWidth="8"
              markerHeight="6"
              refX="7"
              refY="3"
              orient="auto"
            >
              <polygon
                points="0 0, 8 3, 0 6"
                fill="#4B5563"
                stroke="#374151"
                strokeWidth="0.5"
              />
            </marker>
            <marker
              id="arrowhead-highlighted"
              markerWidth="9"
              markerHeight="6"
              refX="8"
              refY="3"
              orient="auto"
            >
              <polygon
                points="0 0, 9 3, 0 6"
                fill="#2563eb"
                stroke="#1d4ed8"
                strokeWidth="0.5"
              />
            </marker>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feMorphology operator="dilate" radius="2"/>
              <feColorMatrix values="0 0 0 0 0.3 0 0 0 0 0.6 0 0 0 0 1 0 0 0 1 0"/>
              <feGaussianBlur stdDeviation="3"/>
              <feComposite in="SourceGraphic"/>
            </filter>
          </defs>

          {/* Background layer for edges */}
          <g className="edges-background">
            {data.edges.map((edge, edgeIndex) => {
              const isHighlighted = selectedNode && 
                (edge.source === selectedNode || edge.target === selectedNode);
              
              if (!isHighlighted) return null;
              
              return (
                <path
                  key={`bg-${edge.id}`}
                  d={getEdgePath(edge, edgeIndex)}
                  fill="none"
                  stroke="#93C5FD"
                  strokeWidth="6"
                  strokeOpacity="0.3"
                  className="pointer-events-none"
                />
              );
            })}
          </g>

          {/* Edges */}
          {data.edges.map((edge, edgeIndex) => {
            const isHighlighted = selectedNode && 
              (edge.source === selectedNode || edge.target === selectedNode);
            const isHovered = hoveredEdge === edge.id;
            
            return (
              <g key={edge.id}>
                {/* Edge path */}
                <path
                  d={getEdgePath(edge, edgeIndex)}
                  fill="none"
                  stroke={isHighlighted ? "#3B82F6" : isHovered ? "#059669" : "#4B5563"}
                  strokeWidth={isHighlighted ? 4 : isHovered ? 3 : 2.5}
                  markerEnd={isHighlighted ? "url(#arrowhead-highlighted)" : "url(#arrowhead)"}
                  className="cursor-pointer transition-all duration-200"
                  filter={isHighlighted ? "url(#glow)" : "none"}
                  strokeOpacity={selectedNode ? (isHighlighted ? 1 : 0.3) : 0.8}
                  onMouseEnter={() => setHoveredEdge(edge.id)}
                  onMouseLeave={() => setHoveredEdge(null)}
                  onClick={() => onEdgeClick?.(edge)}
                />

                {/* Edge label - show based on toggle, enhance when highlighted */}
                {edge.label && showEdgeLabels && (
                  <g>
                    {(() => {
                      const sourcePos = positions[edge.source];
                      const targetPos = positions[edge.target];
                      if (!sourcePos || !targetPos) return null;
                      
                      // Position label closer to source node to reduce clutter
                      const ratio = 0.25; // 25% from source to target
                      const labelX = sourcePos.x + (targetPos.x - sourcePos.x) * ratio;
                      const labelY = sourcePos.y + (targetPos.y - sourcePos.y) * ratio;
                      
                      const labelText = showFullLabels ? edge.label : truncateText(edge.label, 8);
                      const labelWidth = Math.max(40, labelText.length * 6);
                      
                      return (
                        <g>
                          <rect
                            x={labelX - labelWidth/2}
                            y={labelY - 8}
                            width={labelWidth}
                            height="16"
                            fill="rgba(255, 255, 255, 0.95)"
                            stroke={isHighlighted ? "rgba(29, 78, 216, 0.8)" : "rgba(5, 150, 105, 0.6)"}
                            strokeWidth="1"
                            rx="8"
                            className="pointer-events-none"
                          />
                          <text
                            x={labelX}
                            y={labelY}
                            textAnchor="middle"
                            dominantBaseline="central"
                            className="pointer-events-none font-semibold"
                            style={{ 
                              fontSize: canvasSize === 'small' ? '7px' : canvasSize === 'large' ? '11px' : '9px',
                              fill: isHighlighted ? '#1d4ed8' : '#059669',
                              textShadow: '0 1px 2px rgba(255,255,255,0.9)'
                            }}
                          >
                            {labelText}
                          </text>
                        </g>
                      );
                    })()} 
                  </g>
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
            const baseSize = getNodeSize(node.type);
            const sizeMultiplier = canvasSize === 'small' ? 0.8 : canvasSize === 'large' ? 1.2 : 1.0;
            const size = Math.round(baseSize * sizeMultiplier);
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
                  style={{ fontSize: canvasSize === 'small' ? '8px' : canvasSize === 'large' ? '12px' : '10px' }}
                >
                  {showFullLabels ? 
                    formatNodeLabel(node.label, node.type) : 
                    formatNodeLabel(formatNodeLabelForDisplay(node.label, node.type), node.type)
                  }
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
                  style={{ fontSize: canvasSize === 'small' ? '6px' : canvasSize === 'large' ? '10px' : '8px' }}
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