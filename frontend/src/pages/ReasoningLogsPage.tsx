import { useEffect, useState, useRef } from 'react';
import { Layout } from '../components/common';
import { subscribeToAgentReasoningStream } from '../services/api';
import { ReasoningLog } from '../types';
import { PlayIcon, PauseIcon, TrashIcon } from '@heroicons/react/24/outline';

export default function ReasoningLogsPage() {
  const [logs, setLogs] = useState<ReasoningLog[]>([]);
  const [isPaused, setIsPaused] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isPaused) {
      const unsubscribe = subscribeToAgentReasoningStream(
        (log) => {
          setLogs((prev) => [...prev, log]);
        },
        (error) => {
          console.error('Stream error:', error);
        }
      );

      return () => unsubscribe();
    }
  }, [isPaused]);

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      setAutoScroll(isAtBottom);
    }
  };

  const clearLogs = () => {
    setLogs([]);
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'thought':
        return 'text-terminal-accent';
      case 'action':
        return 'text-terminal-blue';
      case 'observation':
        return 'text-terminal-amber';
      case 'decision':
        return 'text-terminal-purple';
      default:
        return 'text-gray-400';
    }
  };

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'thought':
        return '💭';
      case 'action':
        return '⚡';
      case 'observation':
        return '👁️';
      case 'decision':
        return '✓';
      default:
        return '•';
    }
  };

  return (
    <Layout title="Reasoning Agent Logs" subtitle="Live agent reasoning stream">
      {/* Controls */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg border transition-all ${
              isPaused
                ? 'border-terminal-accent text-terminal-accent hover:bg-terminal-accent hover:text-terminal-bg'
                : 'border-terminal-amber text-terminal-amber hover:bg-terminal-amber hover:text-terminal-bg'
            }`}
          >
            {isPaused ? (
              <>
                <PlayIcon className="w-5 h-5" />
                <span className="font-mono">Resume</span>
              </>
            ) : (
              <>
                <PauseIcon className="w-5 h-5" />
                <span className="font-mono">Pause</span>
              </>
            )}
          </button>

          <button
            onClick={clearLogs}
            className="flex items-center space-x-2 px-4 py-2 border border-terminal-red text-terminal-red rounded-lg hover:bg-terminal-red hover:text-terminal-bg transition-all"
          >
            <TrashIcon className="w-5 h-5" />
            <span className="font-mono">Clear</span>
          </button>
        </div>

        <div className="flex items-center space-x-4 text-sm font-mono">
          <div className="flex items-center space-x-2">
            <span className="text-gray-500">Total Logs:</span>
            <span className="text-terminal-accent font-semibold">{logs.length}</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-gray-500">Auto-scroll:</span>
            <span className={autoScroll ? 'text-terminal-accent' : 'text-gray-500'}>
              {autoScroll ? 'ON' : 'OFF'}
            </span>
          </div>
        </div>
      </div>

      {/* Log Terminal */}
      <div className="terminal-panel p-6">
        <div className="flex items-center justify-between mb-4 pb-4 border-b border-terminal-border">
          <div className="flex items-center space-x-3">
            <div className="flex space-x-2">
              <div className="w-3 h-3 rounded-full bg-terminal-red"></div>
              <div className="w-3 h-3 rounded-full bg-terminal-amber"></div>
              <div className="w-3 h-3 rounded-full bg-terminal-accent"></div>
            </div>
            <span className="text-sm font-mono text-gray-400">
              agent_reasoning_stream.log
            </span>
          </div>
          {!isPaused && (
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-terminal-accent rounded-full animate-pulse"></div>
              <span className="text-xs text-terminal-accent font-mono">STREAMING</span>
            </div>
          )}
        </div>

        <div
          ref={containerRef}
          onScroll={handleScroll}
          className="h-[600px] overflow-y-auto bg-terminal-bg p-4 rounded font-mono text-sm scrollbar-thin"
        >
          {logs.length === 0 ? (
            <div className="text-center text-gray-500 py-20">
              Waiting for reasoning logs...
            </div>
          ) : (
            logs.map((log) => (
              <div
                key={log.id}
                className="mb-3 flex items-start space-x-3 fade-in hover:bg-terminal-border/30 p-2 rounded transition-colors"
              >
                <span className="text-gray-500 text-xs mt-1">
                  {new Date(log.timestamp).toLocaleTimeString('en-US', {
                    hour12: false,
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </span>
                <span className="text-lg">{getLevelIcon(log.level)}</span>
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className={`uppercase text-xs font-bold ${getLevelColor(log.level)}`}>
                      [{log.level}]
                    </span>
                  </div>
                  <p className="text-gray-300 leading-relaxed">{log.message}</p>
                </div>
              </div>
            ))
          )}
          <div ref={logsEndRef} />
        </div>

        {/* Legend */}
        <div className="mt-4 pt-4 border-t border-terminal-border flex flex-wrap gap-4 text-xs font-mono">
          <div className="flex items-center space-x-2">
            <span>💭</span>
            <span className="text-terminal-accent">THOUGHT</span>
          </div>
          <div className="flex items-center space-x-2">
            <span>⚡</span>
            <span className="text-terminal-blue">ACTION</span>
          </div>
          <div className="flex items-center space-x-2">
            <span>👁️</span>
            <span className="text-terminal-amber">OBSERVATION</span>
          </div>
          <div className="flex items-center space-x-2">
            <span>✓</span>
            <span className="text-terminal-purple">DECISION</span>
          </div>
        </div>
      </div>
    </Layout>
  );
}
