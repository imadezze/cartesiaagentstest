'use client';

import React from 'react';
import { StateMachineConfig } from '@/types';

interface FlowSelectorProps {
  config: StateMachineConfig;
  currentFlow: string;
  onFlowChange: (flowKey: string) => void;
}

const FlowSelector: React.FC<FlowSelectorProps> = ({ config, currentFlow, onFlowChange }) => {
  const flows = [
    {
      key: 'conversation_flow',
      name: 'Conversation Flow',
      description: 'Main user conversation states and transitions',
      icon: '💬',
      color: 'blue'
    },
    {
      key: 'leads_extraction',
      name: 'Leads Extraction',
      description: 'Background processing for extracting user information',
      icon: '📊',
      color: 'green'
    },
    {
      key: 'research_node',
      name: 'Research Node',
      description: 'Company research and intelligence gathering',
      icon: '🔍',
      color: 'purple'
    },
    {
      key: 'call_validation',
      name: 'Call Validation',
      description: 'End-call condition validation and safety checks',
      icon: '✅',
      color: 'orange'
    },
    {
      key: 'system_architecture',
      name: 'System Architecture',
      description: 'High-level system component interactions',
      icon: '🏗️',
      color: 'gray'
    }
  ];

  const getColorClasses = (color: string, isActive: boolean) => {
    const colorMap = {
      blue: isActive 
        ? 'bg-blue-500 text-white border-blue-600' 
        : 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100',
      green: isActive 
        ? 'bg-green-500 text-white border-green-600' 
        : 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100',
      purple: isActive 
        ? 'bg-purple-500 text-white border-purple-600' 
        : 'bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100',
      orange: isActive 
        ? 'bg-orange-500 text-white border-orange-600' 
        : 'bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100',
      gray: isActive 
        ? 'bg-gray-500 text-white border-gray-600' 
        : 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'
    };
    return colorMap[color as keyof typeof colorMap] || colorMap.gray;
  };

  const getFlowStats = (flowKey: string) => {
    if (flowKey === 'system_architecture') {
      const arch = config[flowKey as keyof StateMachineConfig] as any;
      return {
        nodes: arch?.components?.length || 0,
        edges: arch?.connections?.length || 0
      };
    } else {
      const flow = config[flowKey as keyof StateMachineConfig] as any;
      return {
        nodes: flow?.states?.length || 0,
        edges: flow?.transitions?.length || 0
      };
    }
  };

  return (
    <div className="w-full bg-white border-b border-gray-200">
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-800">
            Cartesia Sales Agent - Flow Visualizer
          </h1>
          <div className="text-sm text-gray-500">
            v{config.metadata.version} • {config.metadata.created}
          </div>
        </div>
        
        <p className="text-gray-600 mb-6">{config.metadata.description}</p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {flows.map((flow) => {
            const isActive = currentFlow === flow.key;
            const stats = getFlowStats(flow.key);
            const colorClasses = getColorClasses(flow.color, isActive);

            return (
              <button
                key={flow.key}
                onClick={() => onFlowChange(flow.key)}
                className={`p-4 border-2 rounded-lg transition-all duration-200 text-left ${colorClasses}
                  transform hover:scale-105 hover:shadow-lg`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{flow.icon}</span>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-sm mb-1 truncate">
                      {flow.name}
                    </h3>
                    <p className={`text-xs mb-3 line-clamp-2 ${
                      isActive ? 'text-white/90' : 'text-gray-500'
                    }`}>
                      {flow.description}
                    </p>
                    <div className="flex justify-between items-center text-xs">
                      <div className={`flex gap-4 ${
                        isActive ? 'text-white/80' : 'text-gray-400'
                      }`}>
                        <span>{stats.nodes} nodes</span>
                        <span>{stats.edges} edges</span>
                      </div>
                      {isActive && (
                        <div className="flex items-center gap-1">
                          <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                          <span className="text-white/90">Active</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default FlowSelector;