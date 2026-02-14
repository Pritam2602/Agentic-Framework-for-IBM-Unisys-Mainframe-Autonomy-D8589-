/**
 * API Service Layer
 * Connects to COMMUNICATOR backend at http://localhost:8000
 */

import {
  Command,
  Job,
  Workflow,
  Dataset,
  CatalogStats,
  ReasoningLog,
  ChatMessage,
  AgentStatus,
  AgentExecution,
  AgentConfig,
} from '../types';

const API_BASE_URL = 'http://localhost:8000';

// ============================================================================
// CATALOG SERVICE
// ============================================================================

/**
 * Fetch all commands from catalog
 * Backend: GET /api/catalog/commands
 */
export const fetchCommandsCatalog = async (): Promise<Command[]> => {
  const response = await fetch(`${API_BASE_URL}/api/catalog/commands`);
  if (!response.ok) throw new Error('Failed to fetch commands');
  return await response.json();
};

/**
 * Fetch all jobs
 * Backend: GET /api/catalog/jobs
 */
export const fetchJobs = async (): Promise<Job[]> => {
  const response = await fetch(`${API_BASE_URL}/api/catalog/jobs`);
  if (!response.ok) throw new Error('Failed to fetch jobs');
  return await response.json();
};

/**
 * Fetch all workflows
 * Backend: GET /api/catalog/workflows
 */
export const fetchWorkflows = async (): Promise<Workflow[]> => {
  const response = await fetch(`${API_BASE_URL}/api/catalog/workflows`);
  if (!response.ok) throw new Error('Failed to fetch workflows');
  return await response.json();
};

/**
 * Fetch all datasets
 * Backend: GET /api/catalog/datasets
 */
export const fetchDatasets = async (): Promise<Dataset[]> => {
  const response = await fetch(`${API_BASE_URL}/api/catalog/datasets`);
  if (!response.ok) throw new Error('Failed to fetch datasets');
  return await response.json();
};

/**
 * Fetch catalog statistics
 * Backend: GET /api/catalog/stats
 */
export const fetchCatalogStats = async (): Promise<CatalogStats> => {
  const response = await fetch(`${API_BASE_URL}/api/catalog/stats`);
  if (!response.ok) throw new Error('Failed to fetch catalog stats');
  return await response.json();
};

// ============================================================================
// REASONING AGENT SERVICE
// ============================================================================

/**
 * Subscribe to agent reasoning stream
 * Backend: GET /api/agent/reasoning-stream (Server-Sent Events)
 */
export const subscribeToAgentReasoningStream = (
  onLog: (log: ReasoningLog) => void,
  onError?: (error: Error) => void
): (() => void) => {
  const eventSource = new EventSource(`${API_BASE_URL}/api/agent/reasoning-stream`);
  
  eventSource.onmessage = (event) => {
    try {
      const log = JSON.parse(event.data);
      onLog(log);
    } catch (error) {
      console.error('Failed to parse reasoning log:', error);
    }
  };
  
  eventSource.onerror = (error) => {
    console.error('EventSource error:', error);
    if (onError) onError(new Error('Stream connection error'));
    eventSource.close();
  };
  
  return () => eventSource.close();
};

// ============================================================================
// CHAT / EXECUTION SERVICE
// ============================================================================

/**
 * Send user query to agent
 * Backend: POST /api/agent/execute
 */
export const sendUserQuery = async (text: string): Promise<ChatMessage> => {
  const response = await fetch(`${API_BASE_URL}/api/agent/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: text }),
  });
  
  if (!response.ok) throw new Error('Failed to send query');
  
  const agentResponse = await response.json();
  
  // Convert backend response to ChatMessage format
  const chatMessage: ChatMessage = {
    id: `msg-${Date.now()}`,
    role: 'agent',
    content: agentResponse.natural_response,
    timestamp: new Date(),
    canonicalOutput: agentResponse.canonical_output,
  };
  
  return chatMessage;
};

/**
 * Execute a specific command
 * Backend: POST /api/commands/execute (Not yet implemented)
 */
export const executeCommand = async (commandId: string, params?: Record<string, any>): Promise<any> => {
  // TODO: Implement when backend endpoint is ready
  throw new Error('Not implemented');
};

/**
 * Get canonical output for a command
 * Backend: GET /api/commands/{id}/output (Not yet implemented)
 */
export const getCanonicalOutput = async (commandId: string): Promise<any> => {
  // TODO: Implement when backend endpoint is ready
  throw new Error('Not implemented');
};

// ============================================================================
// IBM AGENT SERVICE
// ============================================================================

/**
 * Get IBM agent status
 * Backend: GET /api/agent/status
 */
export const getIBMAgentStatus = async (): Promise<AgentStatus> => {
  const response = await fetch(`${API_BASE_URL}/api/agent/status`);
  if (!response.ok) throw new Error('Failed to fetch IBM agent status');
  return await response.json();
};

/**
 * Send task to IBM agent
 * Backend: POST /api/agents/ibm/tasks (Not yet implemented)
 */
export const sendTaskToIBMAgent = async (task: string, params?: Record<string, any>): Promise<AgentExecution> => {
  // TODO: Implement when backend endpoint is ready
  throw new Error('Not implemented');
};

/**
 * Get IBM agent executions
 * Backend: GET /api/agent/executions
 */
export const getIBMAgentExecutions = async (): Promise<AgentExecution[]> => {
  const response = await fetch(`${API_BASE_URL}/api/agent/executions`);
  if (!response.ok) throw new Error('Failed to fetch executions');
  return await response.json();
};

/**
 * Get IBM agent configuration
 * Backend: GET /api/agent/config
 */
export const getIBMAgentConfig = async (): Promise<AgentConfig> => {
  const response = await fetch(`${API_BASE_URL}/api/agent/config`);
  if (!response.ok) throw new Error('Failed to fetch config');
  return await response.json();
};

// ============================================================================
// UNISYS AGENT SERVICE
// ============================================================================

/**
 * Get Unisys agent status
 * Backend: Using same agent status endpoint for now
 */
export const getUnisysAgentStatus = async (): Promise<AgentStatus> => {
  // TODO: Create separate endpoint for Unisys agent
  return getIBMAgentStatus();
};

/**
 * Send task to Unisys agent
 * Backend: POST /api/agents/unisys/tasks (Not yet implemented)
 */
export const sendTaskToUnisysAgent = async (task: string, params?: Record<string, any>): Promise<AgentExecution> => {
  // TODO: Implement when backend endpoint is ready
  throw new Error('Not implemented');
};

/**
 * Get Unisys agent executions
 * Backend: Using same executions endpoint for now
 */
export const getUnisysAgentExecutions = async (): Promise<AgentExecution[]> => {
  // TODO: Create separate endpoint for Unisys agent
  return getIBMAgentExecutions();
};

/**
 * Get Unisys agent configuration
 * Backend: Using same config endpoint for now
 */
export const getUnisysAgentConfig = async (): Promise<AgentConfig> => {
  // TODO: Create separate endpoint for Unisys agent
  return getIBMAgentConfig();
};
