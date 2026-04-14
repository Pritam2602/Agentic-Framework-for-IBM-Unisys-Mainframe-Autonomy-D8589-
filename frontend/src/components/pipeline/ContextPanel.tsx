import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

export interface Context {
  ibm?: {
    programs?: string[];
    datasets?: string[];
    jobs?: string[];
  };
  unisys?: {
    apis?: string[];
    endpoints?: string[];
    services?: string[];
  };
}

interface Props {
  context: Context | null;
  loading?: boolean;
}

export const ContextPanel: React.FC<Props> = ({ context, loading }) => {
  if (!context && !loading) return null;

  return (
    <Card className='w-full bg-slate-900 border-slate-700'>
      <CardHeader>
        <CardTitle className='text-purple-400'>Context Resolution</CardTitle>
        <p className='text-xs text-slate-400 mt-1'>Where is the data located?</p>
      </CardHeader>
      <CardContent className='space-y-4'>
        {loading ? (
          <div className='text-slate-400'>Resolving context...</div>
        ) : context ? (
          <>
            {context.ibm && (
              <div className='border-l-4 border-red-500 pl-4 py-2'>
                <div className='flex items-center gap-2 mb-2'>
                  <Badge className='bg-red-900 text-red-300'>IBM z/OS</Badge>
                </div>
                
                {context.ibm.programs && context.ibm.programs.length > 0 && (
                  <div>
                    <label className='text-xs font-semibold text-slate-400'>Programs:</label>
                    <div className='space-y-1'>
                      {context.ibm.programs.map(p => (
                        <code key={p} className='block text-xs text-cyan-300 bg-slate-800 p-1 rounded'>{p}</code>
                      ))}
                    </div>
                  </div>
                )}

                {context.ibm.datasets && context.ibm.datasets.length > 0 && (
                  <div className='mt-2'>
                    <label className='text-xs font-semibold text-slate-400'>Datasets:</label>
                    <div className='space-y-1'>
                      {context.ibm.datasets.map(d => (
                        <code key={d} className='block text-xs text-cyan-300 bg-slate-800 p-1 rounded'>{d}</code>
                      ))}
                    </div>
                  </div>
                )}

                {context.ibm.jobs && context.ibm.jobs.length > 0 && (
                  <div className='mt-2'>
                    <label className='text-xs font-semibold text-slate-400'>Jobs:</label>
                    <div className='space-y-1'>
                      {context.ibm.jobs.map(j => (
                        <code key={j} className='block text-xs text-cyan-300 bg-slate-800 p-1 rounded'>{j}</code>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {context.unisys && (
              <div className='border-l-4 border-blue-500 pl-4 py-2'>
                <div className='flex items-center gap-2 mb-2'>
                  <Badge className='bg-blue-900 text-blue-300'>Unisys ePortal</Badge>
                </div>
                
                {context.unisys.apis && context.unisys.apis.length > 0 && (
                  <div>
                    <label className='text-xs font-semibold text-slate-400'>APIs:</label>
                    <div className='space-y-1'>
                      {context.unisys.apis.map(a => (
                        <code key={a} className='block text-xs text-green-300 bg-slate-800 p-1 rounded'>{a}</code>
                      ))}
                    </div>
                  </div>
                )}

                {context.unisys.endpoints && context.unisys.endpoints.length > 0 && (
                  <div className='mt-2'>
                    <label className='text-xs font-semibold text-slate-400'>Endpoints:</label>
                    <div className='space-y-1'>
                      {context.unisys.endpoints.map(e => (
                        <code key={e} className='block text-xs text-green-300 bg-slate-800 p-1 rounded'>{e}</code>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className='bg-slate-800 p-2 rounded'>
              <pre className='text-xs text-cyan-300 font-mono overflow-x-auto'>
                {JSON.stringify(context, null, 2)}
              </pre>
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
};
