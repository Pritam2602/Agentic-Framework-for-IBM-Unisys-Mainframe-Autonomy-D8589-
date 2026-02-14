import { useEffect, useState } from 'react';
import { Layout, Table, LoadingSpinner, Modal } from '../components/common';
import { fetchCommandsCatalog } from '../services/api';
import { Command } from '../types';
import { Column } from '../components/common/Table';
import { ArrowDownTrayIcon, EyeIcon } from '@heroicons/react/24/outline';

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

  const handleViewOutput = (fileName: string) => {
    // Mock output content
    const mockContent = {
      'listcat_output.json': JSON.stringify({
        datasets: ['PROD.MASTER.DATA', 'USER.TEMP.WORK'],
        totalRecords: 1550000,
        catalogDate: '2024-02-10',
      }, null, 2),
      'job_output.log': `JOB SUBMITTED SUCCESSFULLY
JOB ID: JOB12345
STATUS: RUNNING
START TIME: 10:30:00
ESTIMATED COMPLETION: 10:45:00`,
      'workflow_status.json': JSON.stringify({
        workflowId: 'ETL_PIPELINE',
        status: 'running',
        currentStep: 3,
        totalSteps: 5,
        progress: '60%',
      }, null, 2),
      'allocation_result.json': JSON.stringify({
        datasetName: 'USER.NEW.DATASET',
        allocated: true,
        size: '100MB',
        recordFormat: 'FB',
      }, null, 2),
    };

    setSelectedOutput({
      name: fileName,
      content: mockContent[fileName as keyof typeof mockContent] || 'Content not available',
    });
  };

  const handleDownloadOutput = (fileName: string) => {
    // Mock download functionality
    console.log('Downloading:', fileName);
    alert(`Download initiated for: ${fileName}`);
  };

  const columns: Column<Command>[] = [
    {
      key: 'name',
      label: 'Command Name',
      render: (value) => (
        <span className="font-mono text-terminal-accent font-semibold">{value}</span>
      ),
    },
    {
      key: 'type',
      label: 'Type',
      render: (value) => (
        <span className="px-2 py-1 bg-terminal-blue/20 text-terminal-blue rounded text-xs font-mono uppercase">
          {value}
        </span>
      ),
    },
    {
      key: 'family',
      label: 'Family',
      render: (value) => (
        <span className="px-2 py-1 bg-terminal-purple/20 text-terminal-purple rounded text-xs font-mono">
          {value}
        </span>
      ),
    },
    {
      key: 'preconditions',
      label: 'Preconditions',
      render: (value: string[]) => (
        <span className="text-gray-300 text-xs font-mono">{value.join(', ')}</span>
      ),
    },
    {
      key: 'outputType',
      label: 'Output Type',
      render: (value) => (
        <span className={`px-2 py-1 rounded text-xs font-mono ${
          value === 'JSON' ? 'bg-terminal-accent/20 text-terminal-accent' :
          value === 'TEXT' ? 'bg-terminal-amber/20 text-terminal-amber' :
          value === 'FILE' ? 'bg-terminal-blue/20 text-terminal-blue' :
          'bg-terminal-purple/20 text-terminal-purple'
        }`}>
          {value}
        </span>
      ),
    },
    {
      key: 'outputFile',
      label: 'Output File',
      render: (value, item) => {
        if (!value) return <span className="text-gray-500">—</span>;
        
        const isViewable = item.outputType === 'JSON' || item.outputType === 'TEXT';
        
        return (
          <div className="flex items-center space-x-2">
            <span className="text-gray-300 text-xs font-mono">{value}</span>
            {isViewable ? (
              <button
                onClick={() => handleViewOutput(value)}
                className="p-1 hover:bg-terminal-accent/10 rounded transition-colors"
                title="View output"
              >
                <EyeIcon className="w-4 h-4 text-terminal-accent" />
              </button>
            ) : (
              <button
                onClick={() => handleDownloadOutput(value)}
                className="p-1 hover:bg-terminal-blue/10 rounded transition-colors"
                title="Download output"
              >
                <ArrowDownTrayIcon className="w-4 h-4 text-terminal-blue" />
              </button>
            )}
          </div>
        );
      },
    },
    {
      key: 'description',
      label: 'Description',
      render: (value) => (
        <span className="text-gray-400 text-sm">{value}</span>
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
