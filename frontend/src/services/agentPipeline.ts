/**
 * Legacy pipeline service wrapper.
 * Prefer using services/api.ts for the control-center route.
 */

import type { PipelineResponse } from "@/store/useAppStore";

const API_BASE_URL = "http://localhost:8000";

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
    conditions?: Array<{ field: string; value: string | number | boolean | null }>;
  };
  systems: string[];
  metric?: string | null;
  aggregation?: string | null;
  output_mode: string;
  requires_federation: boolean;
  priority: string;
  confidence_score: number;
}

export const extractIntent = async (query: string): Promise<IntentResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/intent/extract`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_query: query,
      enable_llm: true,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || "Failed to extract intent");
  }

  return response.json();
};

export const executeAgentPipeline = async (query: string): Promise<PipelineResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/pipeline/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_query: query, enable_llm: true }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || "Failed to execute agent pipeline");
  }

  return response.json();
};

export const streamReasoningLogs = (
  onMessage: (data: unknown) => void,
  onError: (error: Error) => void
) => {
  try {
    const eventSource = new EventSource(`${API_BASE_URL}/api/agent/reasoning-stream`);

    eventSource.onmessage = (event) => {
      try {
        onMessage(JSON.parse(event.data));
      } catch (parseError) {
        onError(parseError instanceof Error ? parseError : new Error("Failed to parse event data"));
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      onError(new Error("Connection lost"));
    };

    return () => eventSource.close();
  } catch (error) {
    onError(error instanceof Error ? error : new Error("Failed to stream reasoning logs"));
    return () => {};
  }
};
