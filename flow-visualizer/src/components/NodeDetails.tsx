'use client';

import React from 'react';
import { GraphNode, GraphEdge } from '@/types';
import { getNodeColor } from '@/utils/graphUtils';

interface NodeDetailsProps {
  node: GraphNode | null;
  connectedEdges: GraphEdge[];
  onClose: () => void;
  onNavigateToNode?: (nodeId: string) => void;
}

const NodeDetails: React.FC<NodeDetailsProps> = ({ 
  node, 
  connectedEdges, 
  onClose, 
  onNavigateToNode 
}) => {
  if (!node) return null;

  const incomingEdges = connectedEdges.filter(edge => edge.target === node.id);
  const outgoingEdges = connectedEdges.filter(edge => edge.source === node.id);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'start': return '🟢';
      case 'end': return '🔴';
      case 'decision': return '🔶';
      case 'process': return '⚙️';
      case 'validation': return '✅';
      case 'trigger': return '⚡';
      case 'background': return '🔄';
      default: return '💬';
    }
  };

  const formatNodeType = (type: string) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        {/* Header */}
        <div 
          className="p-6 rounded-t-lg text-white"
          style={{ backgroundColor: getNodeColor(node.type) }}
        >
          <div className="flex justify-between items-start">
            <div className="flex items-center gap-3">
              <span className="text-2xl">{getTypeIcon(node.type)}</span>
              <div>
                <h2 className="text-xl font-bold">{node.label}</h2>
                <p className="text-sm opacity-90">{formatNodeType(node.type)} Node</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-white hover:text-gray-200 transition-colors"
              aria-label="Close"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Description */}
          <div>
            <h3 className="text-lg font-semibold mb-2 text-gray-800">Description</h3>
            <p className="text-gray-600 leading-relaxed">{node.description || 'No description available.'}</p>
          </div>

          {/* Node Properties */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-800 mb-2">Node ID</h4>
              <code className="text-sm text-blue-600 bg-blue-50 px-2 py-1 rounded">
                {node.id}
              </code>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-semibold text-gray-800 mb-2">Type</h4>
              <span className="inline-flex items-center gap-1 text-sm font-medium text-gray-700">
                {getTypeIcon(node.type)} {formatNodeType(node.type)}
              </span>
            </div>
          </div>

          {/* Incoming Connections */}
          {incomingEdges.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3 text-gray-800 flex items-center gap-2">
                <span>⬅️</span> Incoming Connections ({incomingEdges.length})
              </h3>
              <div className="space-y-2">
                {incomingEdges.map((edge, index) => (
                  <div key={index} className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="font-medium text-green-800">
                          From: <span className="font-mono text-sm">{edge.source}</span>
                        </div>
                        <div className="text-sm text-green-700 mt-1">
                          <strong>Trigger:</strong> {edge.label}
                        </div>
                        {edge.description && (
                          <div className="text-sm text-green-600 mt-1">
                            <strong>Condition:</strong> {edge.description}
                          </div>
                        )}
                      </div>
                      {onNavigateToNode && (
                        <button
                          onClick={() => onNavigateToNode(edge.source)}
                          className="ml-2 text-green-600 hover:text-green-800 transition-colors"
                          title="Navigate to source node"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Outgoing Connections */}
          {outgoingEdges.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold mb-3 text-gray-800 flex items-center gap-2">
                <span>➡️</span> Outgoing Connections ({outgoingEdges.length})
              </h3>
              <div className="space-y-2">
                {outgoingEdges.map((edge, index) => (
                  <div key={index} className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="font-medium text-blue-800">
                          To: <span className="font-mono text-sm">{edge.target}</span>
                        </div>
                        <div className="text-sm text-blue-700 mt-1">
                          <strong>Trigger:</strong> {edge.label}
                        </div>
                        {edge.description && (
                          <div className="text-sm text-blue-600 mt-1">
                            <strong>Condition:</strong> {edge.description}
                          </div>
                        )}
                      </div>
                      {onNavigateToNode && (
                        <button
                          onClick={() => onNavigateToNode(edge.target)}
                          className="ml-2 text-blue-600 hover:text-blue-800 transition-colors"
                          title="Navigate to target node"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* No connections message */}
          {incomingEdges.length === 0 && outgoingEdges.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <svg className="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p>This node has no connections.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 rounded-b-lg border-t">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NodeDetails;