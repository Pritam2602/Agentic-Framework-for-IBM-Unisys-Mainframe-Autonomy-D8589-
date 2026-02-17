import { useEffect, useState } from 'react';
import { Layout, Table, LoadingSpinner } from '../components/common';
import { fetchDatasets } from '../services/api';
import { Dataset } from '../types';
import { Column } from '../components/common/Table';
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline';

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDatasets = async () => {
      try {
        const data = await fetchDatasets();
        setDatasets(data);
      } catch (error) {
        console.error('Failed to load datasets:', error);
      } finally {
        setLoading(false);
      }
    };

    loadDatasets();
  }, []);

  const handleDownload = (url: string, name: string) => {
    console.log('Downloading:', url);
    alert(`Download initiated for: ${name}`);
  };

  const columns: Column<Dataset>[] = [
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
      key: 'size',
      label: 'Size',
      render: (value) => (
        <span className="text-terminal-amber font-mono font-semibold">{value}</span>
      ),
    },
    {
      key: 'records',
      label: 'Records',
      render: (value) => (
        <span className="text-gray-300 font-mono">{value.toLocaleString()}</span>
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
      key: 'downloadUrl',
      label: 'Download',
      render: (value, item) => {
        if (!value) return <span className="text-gray-500">—</span>;
        
        return (
          <button
            onClick={() => handleDownload(value, item.name)}
            className="p-2 hover:bg-terminal-accent/10 rounded transition-colors flex items-center space-x-2"
            title="Download dataset"
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
      <Layout title="Datasets" subtitle="Catalog / Datasets">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" message="Loading datasets..." />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Datasets" subtitle="Catalog / Datasets">
      <div className="mb-6">
        <p className="text-gray-400">
          Access and manage mainframe datasets across all instances.
        </p>
      </div>

      <Table
        data={datasets}
        columns={columns}
        searchable
        searchPlaceholder="Search datasets..."
      />
    </Layout>
  );
}
