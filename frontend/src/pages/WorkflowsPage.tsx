import { useEffect, useState } from 'react';
import { Layout, Table, LoadingSpinner } from '../components/common';
import { fetchWorkflows } from '../services/api';
import { Workflow } from '../types';
import { Column } from '../components/common/Table';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';

export default function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadWorkflows = async () => {
      try {
        const data = await fetchWorkflows();
        setWorkflows(data);
      } catch (error) {
        console.error('Failed to load workflows:', error);
      } finally {
        setLoading(false);
      }
    };

    loadWorkflows();
  }, []);

  const handleDownload = (url: string, name: string) => {
    console.log('Downloading:', url);
    alert(`Download initiated for: ${name}`);
  };

  const columns: Column<Workflow>[] = [
    {
      key: 'name',
      label: 'Name',
      render: (value) => (
        <span className="font-mono text-terminal-accent font-semibold">{value}</span>
      ),
    },
    {
      key: 'scope',
      label: 'Scope',
      render: (value) => (
        <span className={`px-2 py-1 rounded text-xs font-mono uppercase ${
          value === 'enterprise' ? 'bg-terminal-purple/20 text-terminal-purple' :
          value === 'system' ? 'bg-terminal-blue/20 text-terminal-blue' :
          'bg-terminal-accent/20 text-terminal-accent'
        }`}>
          {value}
        </span>
      ),
    },
    {
      key: 'mainframe',
      label: 'Mainframe',
      render: (value) => (
        <span className="font-mono text-terminal-blue">{value}</span>
      ),
    },
    {
      key: 'type',
      label: 'Type',
      render: (value) => (
        <span className="px-2 py-1 bg-terminal-purple/20 text-terminal-purple rounded text-xs font-mono">
          {value}
        </span>
      ),
    },
    {
      key: 'steps',
      label: 'Steps',
      render: (value) => (
        <span className="text-terminal-amber font-mono font-semibold">{value}</span>
      ),
    },
    {
      key: 'dependencies',
      label: 'Dependencies',
      render: (value: string[]) => (
        <span className="text-gray-300 text-xs font-mono">{value.join(', ')}</span>
      ),
    },
    {
      key: 'accessLevel',
      label: 'Access Level',
      render: (value) => (
        <span className={`px-2 py-1 rounded text-xs font-mono ${
          value === 'restricted' ? 'bg-terminal-red/20 text-terminal-red' :
          value === 'admin' ? 'bg-terminal-amber/20 text-terminal-amber' :
          'bg-terminal-accent/20 text-terminal-accent'
        }`}>
          {value}
        </span>
      ),
    },
    {
      key: 'status',
      label: 'Status',
      render: (value) => (
        <span className={`px-2 py-1 rounded text-xs font-mono uppercase ${
          value === 'active' ? 'bg-terminal-accent/20 text-terminal-accent' :
          value === 'inactive' ? 'bg-gray-500/20 text-gray-400' :
          'bg-terminal-amber/20 text-terminal-amber'
        }`}>
          {value}
        </span>
      ),
    },
    {
      key: 'lastRun',
      label: 'Last Run',
      render: (value: Date | undefined) => (
        <span className="text-gray-300 text-xs font-mono">
          {value ? new Date(value).toLocaleString() : '—'}
        </span>
      ),
    },
    {
      key: 'downloadUrl',
      label: 'Download',
      render: (value, item) => {
        if (!value) return <span className="text-gray-500">—</span>;
        
        return (
          <button
            onClick={() => handleDownload(value, item.name)}
            className="p-2 hover:bg-terminal-accent/10 rounded transition-colors flex items-center space-x-2"
            title="Download workflow"
          >
            <ArrowDownTrayIcon className="w-4 h-4 text-terminal-accent" />
            <span className="text-xs text-terminal-accent font-mono">Download</span>
          </button>
        );
      },
      sortable: false,
    },
  ];

  if (loading) {
    return (
      <Layout title="Workflows" subtitle="Catalog / Workflows">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" message="Loading workflows..." />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Workflows" subtitle="Catalog / Workflows">
      <div className="mb-6">
        <p className="text-gray-400">
          Orchestrate and manage multi-step mainframe workflows.
        </p>
      </div>

      <Table
        data={workflows}
        columns={columns}
        searchable
        searchPlaceholder="Search workflows..."
      />
    </Layout>
  );
}
