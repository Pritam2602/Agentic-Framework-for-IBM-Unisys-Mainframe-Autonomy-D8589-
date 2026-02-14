import { useState, useRef, useEffect } from 'react';
import { Layout, LoadingSpinner } from '../components/common';
import { sendUserQuery } from '../services/api';
import { ChatMessage } from '../types';
import { 
  PaperAirplaneIcon, 
  MicrophoneIcon,
  CodeBracketIcon 
} from '@heroicons/react/24/outline';

export default function ExecutionPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputText,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const agentResponse = await sendUserQuery(inputText);
      setMessages((prev) => [...prev, agentResponse]);
    } catch (error) {
      console.error('Failed to send message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const renderCanonicalOutput = (output: ChatMessage['canonicalOutput']) => {
    if (!output) return null;

    switch (output.type) {
      case 'json':
        return (
          <div className="mt-4 terminal-panel p-4">
            <div className="flex items-center space-x-2 mb-3">
              <CodeBracketIcon className="w-5 h-5 text-terminal-accent" />
              <span className="text-sm font-mono text-terminal-accent">Canonical Output (JSON)</span>
            </div>
            <pre className="bg-terminal-bg p-4 rounded font-mono text-xs text-terminal-accent overflow-x-auto">
              {JSON.stringify(output.data, null, 2)}
            </pre>
          </div>
        );
      
      case 'table':
        return (
          <div className="mt-4 terminal-panel p-4">
            <div className="flex items-center space-x-2 mb-3">
              <CodeBracketIcon className="w-5 h-5 text-terminal-blue" />
              <span className="text-sm font-mono text-terminal-blue">Canonical Output (Table)</span>
            </div>
            <div className="overflow-x-auto">
              <table className="terminal-table">
                <thead>
                  <tr>
                    {Object.keys(output.data[0] || {}).map((key) => (
                      <th key={key}>{key}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {output.data.map((row: any, idx: number) => (
                    <tr key={idx}>
                      {Object.values(row).map((value: any, i) => (
                        <td key={i}>{String(value)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );

      case 'file':
        return (
          <div className="mt-4 terminal-panel p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CodeBracketIcon className="w-5 h-5 text-terminal-amber" />
                <span className="text-sm font-mono text-terminal-amber">File Reference</span>
              </div>
              <a
                href={output.fileReference}
                download
                className="px-3 py-1 border border-terminal-accent text-terminal-accent rounded text-xs font-mono hover:bg-terminal-accent hover:text-terminal-bg transition-all"
              >
                Download
              </a>
            </div>
            <p className="mt-2 text-sm font-mono text-gray-400">{output.fileReference}</p>
          </div>
        );

      default:
        return (
          <div className="mt-4 terminal-panel p-4">
            <pre className="font-mono text-sm text-gray-300">{String(output.data)}</pre>
          </div>
        );
    }
  };

  return (
    <Layout title="Execution Panel" subtitle="Interactive agent command interface">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-12rem)]">
        {/* Chat History */}
        <div className="lg:col-span-2 terminal-panel flex flex-col">
          <div className="p-4 border-b border-terminal-border">
            <h3 className="text-lg font-bold text-terminal-accent font-display">
              Conversation
            </h3>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {messages.length === 0 ? (
              <div className="text-center text-gray-500 py-20 font-mono">
                <p className="text-lg mb-2">Ready to assist</p>
                <p className="text-sm">Type a command or query to get started</p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`fade-in ${
                    message.role === 'user' ? 'flex justify-end' : 'flex justify-start'
                  }`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-4 ${
                      message.role === 'user'
                        ? 'bg-terminal-accent/10 border border-terminal-accent'
                        : 'bg-terminal-panel border border-terminal-border'
                    }`}
                  >
                    <div className="flex items-center space-x-2 mb-2">
                      <span
                        className={`text-xs font-mono uppercase ${
                          message.role === 'user' ? 'text-terminal-accent' : 'text-terminal-blue'
                        }`}
                      >
                        {message.role}
                      </span>
                      <span className="text-xs text-gray-500 font-mono">
                        {new Date(message.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-gray-200 leading-relaxed">{message.content}</p>
                    
                    {message.canonicalOutput && renderCanonicalOutput(message.canonicalOutput)}
                  </div>
                </div>
              ))
            )}

            {isLoading && (
              <div className="flex justify-start fade-in">
                <div className="bg-terminal-panel border border-terminal-border rounded-lg p-4">
                  <LoadingSpinner size="sm" message="Agent is processing..." />
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 border-t border-terminal-border">
            <div className="flex space-x-3">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Enter your command or query..."
                  className="input-terminal resize-none h-20"
                  disabled={isLoading}
                />
              </div>
              <div className="flex flex-col space-y-2">
                <button
                  onClick={handleSendMessage}
                  disabled={!inputText.trim() || isLoading}
                  className="btn-primary flex items-center justify-center h-full px-6 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <PaperAirplaneIcon className="w-5 h-5" />
                </button>
                <button
                  className="btn-secondary flex items-center justify-center px-6 py-3"
                  title="Voice input (coming soon)"
                  disabled
                >
                  <MicrophoneIcon className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Canonical Output Panel */}
        <div className="terminal-panel flex flex-col">
          <div className="p-4 border-b border-terminal-border">
            <h3 className="text-lg font-bold text-terminal-accent font-display">
              Latest Output
            </h3>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            {messages.length === 0 || !messages[messages.length - 1]?.canonicalOutput ? (
              <div className="text-center text-gray-500 py-20 font-mono text-sm">
                No output yet
              </div>
            ) : (
              <div>
                {renderCanonicalOutput(messages[messages.length - 1].canonicalOutput)}
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
