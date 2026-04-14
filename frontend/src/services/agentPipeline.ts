/**
 * Agent Pipeline API Service
 * Handles communication with the agentic backend
 */

const API_BASE_URL = 'http://localhost:8000';

export interface IntentRequest {
  user_query: string;
  enable_llm?: boolean;
}

export interface IntentResponse {
  task: string;
  entities: string[];
  attributes: string[];
  filters: {
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

/**
 * Extract intent from user query via Intent Agent
 */
export const extractIntent = async (query: string): Promise<IntentResponse> => {
  const response = await fetch(\\/api/intent/extract\, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_query: query,
      enable_llm: true,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to extract intent');
  }

  return response.json();
};

/**
 * Execute full agent pipeline
 * This would call the /api/agent/execute endpoint
 */
export const executeAgentPipeline = async (query: string) => {
  const response = await fetch(\\/api/agent/execute\, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    throw new Error('Failed to execute agent pipeline');
  }

  return response.json();
};

/**
 * Stream reasoning logs via Server-Sent Events
 */
export const streamReasoningLogs = (onMessage: (data: any) => void, onError: (error: Error) => void) => {
  try {
    const eventSource = new EventSource(\\/api/agent/reasoning-stream\);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error('Failed to parse event data:', e);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      onError(new Error('Connection lost'));
    };

    return () => eventSource.close();
  } catch (error) {
    onError(error as Error);
    return () => {};
  }
};
