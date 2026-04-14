import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { ChevronDown, ChevronRight, CheckCircle2, Circle, Clock } from 'lucide-react';

export interface PipelineStage {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  data?: any;
  error?: string;
  duration?: number;
}

export interface PipelineState {
  userQuery: string;
  stages: {
    intent: PipelineStage;
    context: PipelineStage;
    planner: PipelineStage;
    execution: PipelineStage;
  };
}

interface Props {
  pipeline: PipelineState;
}

export const PipelineVisualization: React.FC<Props> = ({ pipeline }) => {
  const [expandedStage, setExpandedStage] = useState<string>('intent');

  const getStatusIcon = (status: PipelineStage['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className='w-5 h-5 text-green-500' />;
      case 'processing':
        return <Clock className='w-5 h-5 text-blue-500 animate-spin' />;
      case 'error':
        return <Circle className='w-5 h-5 text-red-500' />;
      default:
        return <Circle className='w-5 h-5 text-gray-500' />;
    }
  };

  const getStatusColor = (status: PipelineStage['status']) => {
    switch (status) {
      case 'completed':
        return 'border-green-500 bg-green-50';
      case 'processing':
        return 'border-blue-500 bg-blue-50';
      case 'error':
        return 'border-red-500 bg-red-50';
      default:
        return 'border-gray-300 bg-gray-50';
    }
  };

  const stages = [
    { key: 'intent', label: 'Intent Agent', data: pipeline.stages.intent },
    { key: 'context', label: 'Context Resolution', data: pipeline.stages.context },
    { key: 'planner', label: 'Planner', data: pipeline.stages.planner },
    { key: 'execution', label: 'Execution', data: pipeline.stages.execution },
  ];

  return (
    <Card className='w-full bg-slate-900 border-slate-700'>
      <CardHeader>
        <CardTitle className='text-cyan-400'>Agent Pipeline</CardTitle>
        <p className='text-xs text-slate-400 mt-1'>Query: {pipeline.userQuery}</p>
      </CardHeader>
      <CardContent className='space-y-3'>
        <div className='space-y-2'>
          {stages.map((stage, idx) => (
            <div key={stage.key}>
              <button
                onClick={() => setExpandedStage(expandedStage === stage.key ? '' : stage.key)}
                className={w-full p-3 rounded border-l-4 transition-all }
              >
                <div className='flex items-center justify-between'>
                  <div className='flex items-center gap-3'>
                    {getStatusIcon(stage.data.status)}
                    <span className='font-mono text-sm font-semibold'>{stage.label}</span>
                    {stage.data.duration && (
                      <span className='text-xs text-slate-500 ml-2'>{stage.data.duration}ms</span>
                    )}
                  </div>
                  {expandedStage === stage.key ? <ChevronDown className='w-4 h-4' /> : <ChevronRight className='w-4 h-4' />}
                </div>
              </button>

              {expandedStage === stage.key && stage.data.data && (
                <div className='bg-slate-800 p-3 rounded mt-1 border border-slate-700'>
                  <pre className='text-xs text-cyan-300 overflow-x-auto font-mono'>
                    {JSON.stringify(stage.data.data, null, 2)}
                  </pre>
                </div>
              )}

              {stage.data.error && (
                <div className='bg-red-900 bg-opacity-30 p-2 rounded mt-1 border border-red-700'>
                  <p className='text-xs text-red-300 font-mono'>{stage.data.error}</p>
                </div>
              )}

              {idx < stages.length - 1 && (
                <div className='flex justify-center py-1'>
                  <div className='w-0.5 h-4 bg-slate-600'></div>
                </div>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};
