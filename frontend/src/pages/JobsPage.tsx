import { useEffect, useState } from 'react';
import { Layout, Table, LoadingSpinner } from '../components/common';
import { fetchJobs } from '../services/api';
import { Job } from '../types';
import { Column } from '../components/common/Table';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadJobs = async () => {
      try {
        const data = await fetchJobs();
        setJobs(data);
      } catch (error) {
        console.error('Failed to load jobs:', error);
      } finally {
        setLoading(false);
      }
    };

    loadJobs();
  }, []);

  const handleDownload = (url: string, name: string) => {
    console.log('Downloading:', url);
    alert(`Download initiated for: ${name}`);
  };

  const columns: Column<Job>[] = [
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
        <span className="px-2 py-1 bg-terminal-amber/20 text-terminal-amber rounded text-xs font-mono">
          {value}
        </span>
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
            title="Download job file"
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
      <Layout title="Jobs" subtitle="Catalog / Jobs">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" message="Loading jobs..." />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Jobs" subtitle="Catalog / Jobs">
      <div className="mb-6">
        <p className="text-gray-400">
          View and manage JCL jobs across mainframe instances.
        </p>
      </div>

      <Table
        data={jobs}
        columns={columns}
        searchable
        searchPlaceholder="Search jobs..."
      />
    </Layout>
  );
}
