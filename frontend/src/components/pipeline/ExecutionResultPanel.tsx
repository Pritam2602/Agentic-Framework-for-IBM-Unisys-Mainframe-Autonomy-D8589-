import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { CheckCircle2, AlertCircle } from 'lucide-react';

export interface ExecutionResult {
  status: 'success' | 'error' | 'pending';
  source: 'ibm' | 'unisys' | 'federated';
  duration: number;
  recordsFound?: number;
  data?: any;
  error?: string;
  timestamp: string;
}

interface Props {
  result: ExecutionResult | null;
  loading?: boolean;
}

export const ExecutionResultPanel: React.FC<Props> = ({ result, loading }) => {
  if (!result && !loading) return null;

  const getStatusIcon = (status: ExecutionResult['status']) => {
    if (status === 'success') {
      return <CheckCircle2 className='w-5 h-5 text-green-500' />;
    }
    return <AlertCircle className='w-5 h-5 text-red-500' />;
  };

  const getStatusColor = (status: ExecutionResult['status']) => {
    switch (status) {
      case 'success':
        return 'bg-green-900 text-green-300';
      case 'error':
        return 'bg-red-900 text-red-300';
      default:
        return 'bg-yellow-900 text-yellow-300';
    }
  };

  const getSourceColor = (source: string) => {
    switch (source) {
      case 'ibm':
        return 'bg-red-900 text-red-300';
      case 'unisys':
        return 'bg-blue-900 text-blue-300';
      default:
        return 'bg-purple-900 text-purple-300';
    }
  };

  return (
    <Card className='w-full bg-slate-900 border-slate-700'>
      <CardHeader>
        <CardTitle className='text-green-400'>Execution Result</CardTitle>
      </CardHeader>
      <CardContent className='space-y-4'>
        {loading ? (
          <div className='text-slate-400'>Executing...</div>
        ) : result ? (
          <>
            <div className='flex items-center justify-between p-3 bg-slate-800 rounded'>
              <div className='flex items-center gap-2'>
                {getStatusIcon(result.status)}
                <span className='font-semibold text-slate-300'>Status</span>
              </div>
              <Badge className={getStatusColor(result.status)}>
                {result.status.toUpperCase()}
              </Badge>
            </div>

            <div className='grid grid-cols-3 gap-3'>
              <div className='bg-slate-800 p-2 rounded'>
                <p className='text-xs text-slate-400 font-semibold'>Source</p>
                <Badge className={getSourceColor(result.source)}>
                  {result.source.toUpperCase()}
                </Badge>
              </div>

              <div className='bg-slate-800 p-2 rounded'>
                <p className='text-xs text-slate-400 font-semibold'>Duration</p>
                <p className='text-sm font-mono text-slate-300'>{result.duration}ms</p>
              </div>

              {result.recordsFound !== undefined && (
                <div className='bg-slate-800 p-2 rounded'>
                  <p className='text-xs text-slate-400 font-semibold'>Records</p>
                  <p className='text-sm font-mono text-slate-300'>{result.recordsFound}</p>
                </div>
              )}
            </div>

            {result.error && (
              <div className='bg-red-900 bg-opacity-30 border border-red-700 rounded p-3'>
                <p className='text-xs font-semibold text-red-300 mb-1'>Error</p>
                <p className='text-xs text-red-300 font-mono'>{result.error}</p>
              </div>
            )}

            {result.data && (
              <div className='space-y-2'>
                <p className='text-xs font-semibold text-slate-400'>Data Output</p>
                <div className='bg-slate-800 p-3 rounded max-h-60 overflow-y-auto'>
                  <pre className='text-xs text-cyan-300 font-mono'>
                    {JSON.stringify(result.data, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            <div className='text-xs text-slate-500 text-right'>
              {new Date(result.timestamp).toLocaleTimeString()}
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
};
