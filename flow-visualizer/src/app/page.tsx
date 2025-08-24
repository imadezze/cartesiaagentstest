'use client';

import React, { useState, useEffect } from 'react';
import FlowVisualization from '@/components/FlowVisualization';
import FlowSelector from '@/components/FlowSelector';
import NodeDetails from '@/components/NodeDetails';
import { StateMachineConfig, GraphData, GraphNode, GraphEdge, Flow } from '@/types';
import { flowToGraphData, systemArchitectureToGraphData } from '@/utils/graphUtils';

export default function Home() {
  const [config, setConfig] = useState<StateMachineConfig | null>(null);
  const [currentFlow, setCurrentFlow] = useState<string>('conversation_flow');
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load configuration from JSON file
  useEffect(() => {
    const loadConfig = async () => {
      try {
        setLoading(true);
        const response = await fetch('/state_machine_config.json');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: StateMachineConfig = await response.json();
        setConfig(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load configuration');
        console.error('Error loading config:', err);
      } finally {
        setLoading(false);
      }
    };

    loadConfig();
  }, []);

  // Update graph data when flow changes
  useEffect(() => {
    if (!config) return;

    try {
      let newGraphData: GraphData;

      if (currentFlow === 'system_architecture') {
        newGraphData = systemArchitectureToGraphData(config.system_architecture);
      } else {
        const flow = config[currentFlow as keyof StateMachineConfig] as Flow;
        if (!flow || !flow.states) {
          throw new Error(`Invalid flow: ${currentFlow}`);
        }
        newGraphData = flowToGraphData(flow);
      }

      setGraphData(newGraphData);
      setSelectedNode(null);
      setSelectedNodeId(null);
    } catch (err) {
      setError(`Error loading flow data: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  }, [config, currentFlow]);

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node);
    setSelectedNodeId(node.id);
  };

  const handleEdgeClick = (edge: GraphEdge) => {
    // Could implement edge details modal here
    console.log('Edge clicked:', edge);
  };

  const handleCloseNodeDetails = () => {
    setSelectedNode(null);
    setSelectedNodeId(null);
  };

  const handleNavigateToNode = (nodeId: string) => {
    const node = graphData.nodes.find(n => n.id === nodeId);
    if (node) {
      setSelectedNode(node);
      setSelectedNodeId(nodeId);
    }
  };

  const getConnectedEdges = (nodeId: string): GraphEdge[] => {
    return graphData.edges.filter(
      edge => edge.source === nodeId || edge.target === nodeId
    );
  };

  const getFlowTitle = () => {
    if (!config) return 'Loading...';
    
    const flowTitles: { [key: string]: string } = {
      conversation_flow: config.conversation_flow.name,
      leads_extraction: config.leads_extraction.name,
      research_node: config.research_node.name,
      call_validation: config.call_validation.name,
      system_architecture: config.system_architecture.name
    };

    return flowTitles[currentFlow] || currentFlow;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-700">Loading State Machine Configuration...</h2>
          <p className="text-gray-500 mt-2">Please wait while we load the flow data.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center bg-white p-8 rounded-lg shadow-lg max-w-md">
          <div className="text-red-500 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.996-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">Error Loading Configuration</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  if (!config) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Header */}
      <FlowSelector 
        config={config}
        currentFlow={currentFlow}
        onFlowChange={setCurrentFlow}
      />

      {/* Main Content */}
      <div className="flex-1 p-6">
        <div className="bg-white rounded-lg shadow-lg h-full">
          {graphData.nodes.length > 0 ? (
            <FlowVisualization
              data={graphData}
              title={getFlowTitle()}
              onNodeClick={handleNodeClick}
              onEdgeClick={handleEdgeClick}
              selectedNode={selectedNodeId}
            />
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center text-gray-500">
                <svg className="w-16 h-16 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="text-lg font-medium mb-2">No Flow Data Available</h3>
                <p>The selected flow does not contain any nodes or edges.</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Node Details Modal */}
      {selectedNode && (
        <NodeDetails
          node={selectedNode}
          connectedEdges={getConnectedEdges(selectedNode.id)}
          onClose={handleCloseNodeDetails}
          onNavigateToNode={handleNavigateToNode}
        />
      )}

      {/* Quick Stats Footer */}
      <div className="bg-white border-t border-gray-200 px-6 py-3">
        <div className="flex justify-between items-center text-sm text-gray-600">
          <div className="flex gap-6">
            <span>{graphData.nodes.length} nodes</span>
            <span>{graphData.edges.length} edges</span>
            {selectedNodeId && (
              <span className="text-blue-600 font-medium">
                Selected: {graphData.nodes.find(n => n.id === selectedNodeId)?.label}
              </span>
            )}
          </div>
          <div className="flex items-center gap-4">
            <span>Click nodes to inspect • Hover for details</span>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span>Interactive</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
