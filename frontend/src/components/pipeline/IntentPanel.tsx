import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';

export interface IntentData {
  task: string;
  entities: string[];
  attributes: string[];
  filters?: {
    time_range?: {
      start: string;
      end: string;
    };
    conditions?: string[];
  };
  systems: string[];
  priority: string;
  confidence_score: number;
}

interface Props {
  intent: IntentData | null;
  loading?: boolean;
}

export const IntentPanel: React.FC<Props> = ({ intent, loading }) => {
  if (!intent && !loading) return null;

  return (
    <Card className='w-full bg-slate-900 border-slate-700'>
      <CardHeader>
        <CardTitle className='text-amber-400'>Intent Extraction</CardTitle>
      </CardHeader>
      <CardContent className='space-y-4'>
        {loading ? (
          <div className='text-slate-400'>Processing intent...</div>
        ) : intent ? (
          <>
            <div className='space-y-2'>
              <label className='text-xs font-semibold text-slate-400'>Task</label>
              <Badge className='bg-amber-900 text-amber-300'>{intent.task}</Badge>
            </div>

            <div className='space-y-2'>
              <label className='text-xs font-semibold text-slate-400'>Entities</label>
              <div className='flex flex-wrap gap-2'>
                {intent.entities.map(e => (
                  <Badge key={e} className='bg-blue-900 text-blue-300'>{e}</Badge>
                ))}
              </div>
            </div>

            <div className='space-y-2'>
              <label className='text-xs font-semibold text-slate-400'>Attributes</label>
              <div className='flex flex-wrap gap-2'>
                {intent.attributes.map(a => (
                  <Badge key={a} className='bg-cyan-900 text-cyan-300'>{a}</Badge>
                ))}
              </div>
            </div>

            <div className='space-y-2'>
              <label className='text-xs font-semibold text-slate-400'>Systems</label>
              <div className='flex flex-wrap gap-2'>
                {intent.systems.map(s => (
                  <Badge key={s} className='bg-green-900 text-green-300'>{s.toUpperCase()}</Badge>
                ))}
              </div>
            </div>

            <div className='grid grid-cols-2 gap-4'>
              <div>
                <label className='text-xs font-semibold text-slate-400'>Priority</label>
                <p className='text-slate-300 font-mono'>{intent.priority}</p>
              </div>
              <div>
                <label className='text-xs font-semibold text-slate-400'>Confidence</label>
                <div className='w-full bg-slate-700 rounded h-2 overflow-hidden'>
                  <div 
                    className='bg-gradient-to-r from-green-500 to-cyan-500 h-full transition-all'
                    style={{ width: \\%\ }}
                  ></div>
                </div>
                <p className='text-xs text-slate-400 mt-1'>{(intent.confidence_score * 100).toFixed(1)}%</p>
              </div>
            </div>

            {intent.filters?.time_range && (
              <div className='space-y-2'>
                <label className='text-xs font-semibold text-slate-400'>Time Range</label>
                <p className='text-slate-300 font-mono text-xs'>{intent.filters.time_range.start} to {intent.filters.time_range.end}</p>
              </div>
            )}

            <div className='bg-slate-800 p-2 rounded'>
              <pre className='text-xs text-cyan-300 font-mono overflow-x-auto'>
                {JSON.stringify(intent, null, 2)}
              </pre>
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
};
