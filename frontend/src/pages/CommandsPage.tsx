import { useEffect, useState } from 'react';
import { Layout, Table, LoadingSpinner, Modal } from '../components/common';
import { fetchCommandsCatalog } from '../services/api';
import { Command } from '../types';
import { Column } from '../components/common/Table';

export default function CommandsPage() {
  const [commands, setCommands] = useState<Command[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOutput, setSelectedOutput] = useState<{ name: string; content: string } | null>(null);

  useEffect(() => {
    const loadCommands = async () => {
      try {
        const data = await fetchCommandsCatalog();
        setCommands(data);
      } catch (error) {
        console.error('Failed to load commands:', error);
      } finally {
        setLoading(false);
      }
    };

    loadCommands();
  }, []);



  const columns: Column<Command>[] = [
    {
      key: 'zowe_command' as any,
      label: 'Zowe Command',
      render: (value) => (
        <span className="font-mono text-terminal-accent font-semibold text-xs">{value}</span>
      ),
    },
    {
      key: 'command_family' as any,
      label: 'Family',
      render: (value) => (
        <span className={`px-2 py-1 rounded text-xs font-mono uppercase ${value === 'DB2' ? 'bg-blue-500/20 text-blue-400' :
          value === 'CICS' ? 'bg-purple-500/20 text-purple-400' :
            value === 'IMS' ? 'bg-amber-500/20 text-amber-400' :
              value === 'JES' ? 'bg-green-500/20 text-green-400' :
                value === 'TSO' ? 'bg-cyan-500/20 text-cyan-400' :
                  value === 'USS' ? 'bg-orange-500/20 text-orange-400' :
                    'bg-gray-500/20 text-gray-400'
          }`}>
          {value}
        </span>
      ),
    },
    {
      key: 'subsystem' as any,
      label: 'Subsystem',
      render: (value) => (
        <span className="text-gray-300 text-xs font-mono">{value}</span>
      ),
    },
    {
      key: 'operation' as any,
      label: 'Operation',
      render: (value) => (
        <span className={`px-2 py-1 rounded text-xs font-mono ${value === 'READ' ? 'bg-terminal-accent/20 text-terminal-accent' :
          value === 'EXECUTE' ? 'bg-terminal-amber/20 text-terminal-amber' :
            value === 'WRITE' ? 'bg-red-500/20 text-red-400' :
              'bg-gray-500/20 text-gray-400'
          }`}>
          {value}
        </span>
      ),
    },
    {
      key: 'ibm_artifact' as any,
      label: 'IBM Artifact',
      render: (value) => (
        <span className="text-gray-400 text-sm">{value}</span>
      ),
    },
    {
      key: 'execution_cost' as any,
      label: 'Cost',
      render: (value) => (
        <span className={`px-2 py-1 rounded text-xs font-mono ${value === 'HIGH' ? 'bg-red-500/20 text-red-400' :
          value === 'MEDIUM' ? 'bg-amber-500/20 text-amber-400' :
            'bg-green-500/20 text-green-400'
          }`}>
          {value}
        </span>
      ),
    },
    {
      key: 'confidence_level' as any,
      label: 'Confidence',
      render: (value) => (
        <span className="text-gray-300 text-xs font-mono">
          {typeof value === 'number' ? `${(value * 100).toFixed(0)}%` : value}
        </span>
      ),
    },
  ];

  if (loading) {
    return (
      <Layout title="Commands" subtitle="Catalog / Commands">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" message="Loading commands..." />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Commands" subtitle="Catalog / Commands">
      <div className="mb-6">
        <p className="text-gray-400">
          Browse and execute mainframe commands. Click on output files to view or download.
        </p>
      </div>

      <Table
        data={commands}
        columns={columns}
        searchable
        searchPlaceholder="Search commands..."
      />

      {/* Output Viewer Modal */}
      <Modal
        isOpen={selectedOutput !== null}
        onClose={() => setSelectedOutput(null)}
        title={selectedOutput?.name || 'Output'}
        size="lg"
      >
        <pre className="bg-terminal-bg p-4 rounded font-mono text-sm text-terminal-accent overflow-x-auto">
          {selectedOutput?.content}
        </pre>
      </Modal>
    </Layout>
  );
}
