import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

export interface ExecutionStep {
  step: number;
  system: 'ibm' | 'unisys';
  action: string;
  command?: string;
  api?: string;
  parameters?: Record<string, any>;
  description?: string;
}

export interface PlanData {
  totalSteps: number;
  steps: ExecutionStep[];
  estimatedDuration?: number;
}

interface Props {
  plan: PlanData | null;
  loading?: boolean;
}

export const PlannerPanel: React.FC<Props> = ({ plan, loading }) => {
  if (!plan && !loading) return null;

  const getSystemColor = (system: string) => {
    return system === 'ibm' ? 'bg-red-900 text-red-300' : 'bg-blue-900 text-blue-300';
  };

  return (
    <Card className='w-full bg-slate-900 border-slate-700'>
      <CardHeader>
        <CardTitle className='text-orange-400'>Execution Plan</CardTitle>
        <p className='text-xs text-slate-400 mt-1'>How will the task be executed?</p>
      </CardHeader>
      <CardContent className='space-y-4'>
        {loading ? (
          <div className='text-slate-400'>Planning execution...</div>
        ) : plan ? (
          <>
            <div className='flex items-center justify-between p-2 bg-slate-800 rounded'>
              <span className='text-xs font-semibold text-slate-400'>Total Steps</span>
              <span className='text-lg font-mono text-orange-400'>{plan.totalSteps}</span>
            </div>

            {plan.estimatedDuration && (
              <div className='flex items-center justify-between p-2 bg-slate-800 rounded'>
                <span className='text-xs font-semibold text-slate-400'>Est. Duration</span>
                <span className='text-sm font-mono text-slate-300'>{plan.estimatedDuration}ms</span>
              </div>
            )}

            <div className='space-y-3'>
              {plan.steps.map((step, idx) => (
                <div key={idx} className='border-l-4 border-orange-500 pl-4 py-2'>
                  <div className='flex items-center gap-2 mb-2'>
                    <span className='inline-flex items-center justify-center w-6 h-6 rounded-full bg-orange-900 text-orange-300 font-semibold text-xs'>
                      {step.step}
                    </span>
                    <Badge className={getSystemColor(step.system)}>
                      {step.system.toUpperCase()}
                    </Badge>
                  </div>
                  
                  <p className='text-slate-300 font-semibold text-sm mb-1'>{step.action}</p>
                  
                  {step.description && (
                    <p className='text-xs text-slate-400 mb-2'>{step.description}</p>
                  )}

                  {step.command && (
                    <div className='bg-slate-800 p-2 rounded mb-2'>
                      <code className='text-xs text-cyan-300 font-mono'>{step.command}</code>
                    </div>
                  )}

                  {step.api && (
                    <div className='bg-slate-800 p-2 rounded mb-2'>
                      <code className='text-xs text-green-300 font-mono'>{step.api}</code>
                    </div>
                  )}

                  {step.parameters && Object.keys(step.parameters).length > 0 && (
                    <div className='bg-slate-800 p-2 rounded'>
                      <pre className='text-xs text-slate-300 font-mono overflow-x-auto'>
                        {JSON.stringify(step.parameters, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className='bg-slate-800 p-2 rounded'>
              <pre className='text-xs text-cyan-300 font-mono overflow-x-auto'>
                {JSON.stringify(plan, null, 2)}
              </pre>
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
};
