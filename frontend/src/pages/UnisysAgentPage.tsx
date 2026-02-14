import { useEffect, useState } from 'react';
import { Layout, StatCard, LoadingSpinner, Table } from '../components/common';
import { 
  getUnisysAgentStatus, 
  getUnisysAgentExecutions, 
  getUnisysAgentConfig 
} from '../services/api';
import { AgentStatus, AgentExecution, AgentConfig } from '../types';
import { Column } from '../components/common/Table';
import {
  ServerStackIcon,
  ClockIcon,
  CheckCircleIcon,
  CpuChipIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

export default function UnisysAgentPage() {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [executions, setExecutions] = useState<AgentExecution[]>([]);
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [statusData, executionsData, configData] = await Promise.all([
          getUnisysAgentStatus(),
          getUnisysAgentExecutions(),
          getUnisysAgentConfig(),
        ]);
        setStatus(statusData);
        setExecutions(executionsData);
        setConfig(configData);
      } catch (error) {
        console.error('Failed to load Unisys agent data:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const executionColumns: Column<AgentExecution>[] = [
    {
      key: 'taskId',
      label: 'Task ID',
      render: (value) => (
        <span className="font-mono text-terminal-blue text-sm">{value}</span>
      ),
    },
    {
      key: 'command',
      label: 'Command',
      render: (value) => (
        <span className="font-mono text-gray-300 text-sm">{value}</span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (value) => (
        <span className={`px-2 py-1 rounded text-xs font-mono uppercase ${
          value === 'completed' ? 'bg-terminal-accent/20 text-terminal-accent' :
          value === 'running' ? 'bg-terminal-blue/20 text-terminal-blue' :
          value === 'failed' ? 'bg-terminal-red/20 text-terminal-red' :
          'bg-terminal-amber/20 text-terminal-amber'
        }`}>
          {value}
        </span>
      ),
    },
    {
      key: 'startTime',
      label: 'Start Time',
      render: (value: Date) => (
        <span className="text-gray-300 text-xs font-mono">
          {new Date(value).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'endTime',
      label: 'End Time',
      render: (value: Date | undefined) => (
        <span className="text-gray-300 text-xs font-mono">
          {value ? new Date(value).toLocaleString() : '—'}
        </span>
      ),
    },
  ];

  // Mock command compatibility matrix
  const compatibilityMatrix = [
    { command: 'WFL Execution', supported: true, version: '2.8+' },
    { command: 'File Management', supported: true, version: '2.0+' },
    { command: 'Security Matrix', supported: true, version: '2.5+' },
    { command: 'COMS Processing', supported: true, version: '2.3+' },
    { command: 'DMSII Operations', supported: true, version: '2.7+' },
    { command: 'Batch Processing', supported: true, version: '2.4+' },
  ];

  if (loading) {
    return (
      <Layout title="Unisys Agent" subtitle="MCP Agent Dashboard">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" message="Loading agent data..." />
        </div>
      </Layout>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'blue';
      case 'busy': return 'amber';
      case 'idle': return 'accent';
      default: return 'red';
    }
  };

  return (
    <Layout title="Unisys Agent" subtitle="MCP Agent Dashboard">
      {/* Agent Status Overview */}
      <div className="mb-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <StatCard
            title="Agent Status"
            value={status?.status.toUpperCase() || 'UNKNOWN'}
            icon={<ServerStackIcon className={`w-6 h-6 text-terminal-${getStatusColor(status?.status || 'offline')}`} />}
            accentColor={getStatusColor(status?.status || 'offline') as any}
          />
          <StatCard
            title="Uptime"
            value={`${Math.floor((status?.uptime || 0) / 86400000)}d`}
            icon={<ClockIcon className="w-6 h-6 text-terminal-purple" />}
            accentColor="purple"
          />
          <StatCard
            title="Tasks Completed"
            value={status?.tasksCompleted || 0}
            icon={<CheckCircleIcon className="w-6 h-6 text-terminal-accent" />}
            accentColor="accent"
          />
          <StatCard
            title="Environment"
            value={config?.environment || 'N/A'}
            icon={<CpuChipIcon className="w-6 h-6 text-terminal-amber" />}
            accentColor="amber"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Capabilities */}
        <div className="terminal-panel p-6">
          <h3 className="text-lg font-bold text-terminal-blue mb-4 font-display">
            Capabilities
          </h3>
          <div className="space-y-3">
            {status?.capabilities.map((capability, idx) => (
              <div
                key={idx}
                className="flex items-center space-x-3 p-3 bg-terminal-bg rounded hover:bg-terminal-border/30 transition-colors"
              >
                <div className="w-2 h-2 bg-terminal-blue rounded-full"></div>
                <span className="text-gray-300 font-mono text-sm">{capability}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Configuration */}
        <div className="terminal-panel p-6">
          <h3 className="text-lg font-bold text-terminal-blue mb-4 font-display">
            Environment Metadata
          </h3>
          <div className="space-y-3 font-mono text-sm">
            <div className="flex justify-between p-3 bg-terminal-bg rounded">
              <span className="text-gray-400">Environment:</span>
              <span className="text-terminal-blue">{config?.environment}</span>
            </div>
            <div className="flex justify-between p-3 bg-terminal-bg rounded">
              <span className="text-gray-400">Agent Version:</span>
              <span className="text-terminal-accent">{config?.version}</span>
            </div>
            <div className="flex justify-between p-3 bg-terminal-bg rounded">
              <span className="text-gray-400">Max Concurrent Tasks:</span>
              <span className="text-terminal-amber">{config?.maxConcurrentTasks}</span>
            </div>
            <div className="flex justify-between p-3 bg-terminal-bg rounded">
              <span className="text-gray-400">Task Timeout:</span>
              <span className="text-terminal-purple">{config?.timeout}ms</span>
            </div>
            <div className="flex justify-between p-3 bg-terminal-bg rounded">
              <span className="text-gray-400">Last Activity:</span>
              <span className="text-gray-300">
                {status?.lastActivity ? new Date(status.lastActivity).toLocaleString() : '—'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Command Compatibility Matrix */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-4">
          <ChartBarIcon className="w-6 h-6 text-terminal-blue" />
          <h3 className="text-lg font-bold text-terminal-blue font-display">
            Command Compatibility Matrix
          </h3>
        </div>
        <div className="terminal-panel p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {compatibilityMatrix.map((item, idx) => (
              <div
                key={idx}
                className="p-4 bg-terminal-bg rounded border border-terminal-border hover:border-terminal-blue transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-mono text-gray-300">{item.command}</span>
                  <span className={`w-3 h-3 rounded-full ${
                    item.supported ? 'bg-terminal-accent' : 'bg-terminal-red'
                  }`}></span>
                </div>
                <div className="text-xs font-mono text-gray-500">
                  Since: {item.version}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Execution History Timeline */}
      <div>
        <h3 className="text-lg font-bold text-terminal-blue mb-4 font-display">
          Execution History
        </h3>
        <Table
          data={executions}
          columns={executionColumns}
          searchable
          searchPlaceholder="Search executions..."
        />
      </div>
    </Layout>
  );
}
