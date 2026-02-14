// Core domain types for the Mainframe Command Platform

export type CommandType = 'batch' | 'workflow' | 'metadata' | 'query' | 'system';
export type CommandFamily = 'JOB' | 'WORKFLOW' | 'DATASET' | 'SYSTEM';
export type OutputType = 'JSON' | 'TEXT' | 'FILE' | 'STREAM';
export type Scope = 'user' | 'system' | 'enterprise';
export type AccessLevel = 'read-only' | 'admin' | 'restricted';
export type MainframeType = 'JCL' | 'COBOL' | 'PROC' | 'DATASET' | 'WORKFLOW';

export interface Command {
  id: string;
  name: string;
  type: CommandType;
  family: CommandFamily;
  preconditions: string[];
  outputType: OutputType;
  outputFile?: string;
  description: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Job {
  id: string;
  name: string;
  scope: Scope;
  mainframe: string;
  type: MainframeType;
  accessLevel: AccessLevel;
  status: 'active' | 'inactive' | 'pending';
  lastRun?: Date;
  downloadUrl?: string;
}

export interface Workflow extends Job {
  steps: number;
  dependencies: string[];
}

export interface Dataset {
  id: string;
  name: string;
  scope: Scope;
  mainframe: string;
  type: MainframeType;
  accessLevel: AccessLevel;
  size: string;
  records: number;
  downloadUrl?: string;
}

export interface CatalogStats {
  totalCommands: number;
  totalJobs: number;
  totalWorkflows: number;
  totalDatasets: number;
  lastUpdated: Date;
}

export type ReasoningLevel = 'thought' | 'action' | 'observation' | 'decision';

export interface ReasoningLog {
  id: string;
  timestamp: Date;
  level: ReasoningLevel;
  message: string;
  metadata?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
  canonicalOutput?: CanonicalOutput;
}

export interface CanonicalOutput {
  type: 'json' | 'table' | 'file' | 'text';
  data: any;
  fileReference?: string;
}

export interface AgentStatus {
  id: string;
  name: string;
  status: 'online' | 'idle' | 'busy' | 'offline';
  capabilities: string[];
  uptime: number;
  tasksCompleted: number;
  lastActivity: Date;
}

export interface AgentExecution {
  id: string;
  taskId: string;
  command: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime: Date;
  endTime?: Date;
  result?: any;
}

export interface AgentConfig {
  environment: string;
  version: string;
  maxConcurrentTasks: number;
  timeout: number;
  retryPolicy: {
    maxRetries: number;
    backoffMs: number;
  };
}
