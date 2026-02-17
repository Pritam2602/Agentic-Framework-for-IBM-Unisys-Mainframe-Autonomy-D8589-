import { useEffect, useState } from 'react';
import { Layout, StatCard, LoadingSpinner, Table } from '../components/common';
import { 
  getIBMAgentStatus, 
  getIBMAgentExecutions, 
  getIBMAgentConfig 
} from '../services/api';
import { AgentStatus, AgentExecution, AgentConfig } from '../types';
import { Column } from '../components/common/Table';
import {
  CpuChipIcon,
  ClockIcon,
  CheckCircleIcon,
  ServerStackIcon,
} from '@heroicons/react/24/outline';

export default function IBMAgentPage() {
  const [status, setStatus] = useState<AgentStatus | null>(null);
  const [executions, setExecutions] = useState<AgentExecution[]>([]);
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [statusData, executionsData, configData] = await Promise.all([
          getIBMAgentStatus(),
          getIBMAgentExecutions(),
          getIBMAgentConfig(),
        ]);
        setStatus(statusData);
        setExecutions(executionsData);
        setConfig(configData);
      } catch (error) {
        console.error('Failed to load IBM agent data:', error);
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
        <span className="font-mono text-terminal-accent text-sm">{value}</span>
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

  if (loading) {
    return (
      <Layout title="IBM Agent" subtitle="z/OS Agent Dashboard">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" message="Loading agent data..." />
        </div>
      </Layout>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'online': return 'accent';
      case 'busy': return 'amber';
      case 'idle': return 'blue';
      default: return 'red';
    }
  };

  return (
    <Layout title="IBM Agent" subtitle="z/OS Agent Dashboard">
      {/* Agent Status Overview */}
      <div className="mb-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <StatCard
            title="Agent Status"
            value={status?.status.toUpperCase() || 'UNKNOWN'}
            icon={<CpuChipIcon className={`w-6 h-6 text-terminal-${getStatusColor(status?.status || 'offline')}`} />}
            accentColor={getStatusColor(status?.status || 'offline') as any}
          />
          <StatCard
            title="Uptime"
            value={`${Math.floor((status?.uptime || 0) / 86400000)}d`}
            icon={<ClockIcon className="w-6 h-6 text-terminal-blue" />}
            accentColor="blue"
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
            icon={<ServerStackIcon className="w-6 h-6 text-terminal-purple" />}
            accentColor="purple"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Capabilities */}
        <div className="terminal-panel p-6">
          <h3 className="text-lg font-bold text-terminal-accent mb-4 font-display">
            Capabilities
          </h3>
          <div className="space-y-3">
            {status?.capabilities.map((capability, idx) => (
              <div
                key={idx}
                className="flex items-center space-x-3 p-3 bg-terminal-bg rounded hover:bg-terminal-border/30 transition-colors"
              >
                <div className="w-2 h-2 bg-terminal-accent rounded-full"></div>
                <span className="text-gray-300 font-mono text-sm">{capability}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Configuration */}
        <div className="terminal-panel p-6">
          <h3 className="text-lg font-bold text-terminal-accent mb-4 font-display">
            Configuration
          </h3>
          <div className="space-y-3 font-mono text-sm">
            <div className="flex justify-between p-3 bg-terminal-bg rounded">
              <span className="text-gray-400">Version:</span>
              <span className="text-terminal-accent">{config?.version}</span>
            </div>
            <div className="flex justify-between p-3 bg-terminal-bg rounded">
              <span className="text-gray-400">Max Concurrent Tasks:</span>
              <span className="text-terminal-blue">{config?.maxConcurrentTasks}</span>
            </div>
            <div className="flex justify-between p-3 bg-terminal-bg rounded">
              <span className="text-gray-400">Timeout:</span>
              <span className="text-terminal-amber">{config?.timeout}ms</span>
            </div>
            <div className="flex justify-between p-3 bg-terminal-bg rounded">
              <span className="text-gray-400">Max Retries:</span>
              <span className="text-terminal-purple">{config?.retryPolicy.maxRetries}</span>
            </div>
            <div className="flex justify-between p-3 bg-terminal-bg rounded">
              <span className="text-gray-400">Backoff:</span>
              <span className="text-gray-300">{config?.retryPolicy.backoffMs}ms</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Executions */}
      <div>
        <h3 className="text-lg font-bold text-terminal-accent mb-4 font-display">
          Recent Executions
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
