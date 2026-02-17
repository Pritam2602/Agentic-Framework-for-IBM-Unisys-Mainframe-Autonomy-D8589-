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

// Mock Commands
export const mockCommands: Command[] = [
  {
    id: 'cmd-001',
    name: 'LISTCAT',
    type: 'query',
    family: 'DATASET',
    preconditions: ['RACF_AUTH', 'CATALOG_ACCESS'],
    outputType: 'JSON',
    outputFile: 'listcat_output.json',
    description: 'List catalog entries for datasets',
    createdAt: new Date('2024-01-15'),
    updatedAt: new Date('2024-02-01'),
  },
  {
    id: 'cmd-002',
    name: 'SUBMIT_JOB',
    type: 'batch',
    family: 'JOB',
    preconditions: ['JOB_AUTH', 'SPOOL_ACCESS'],
    outputType: 'STREAM',
    outputFile: 'job_output.log',
    description: 'Submit JCL job to execution queue',
    createdAt: new Date('2024-01-20'),
    updatedAt: new Date('2024-01-28'),
  },
  {
    id: 'cmd-003',
    name: 'WORKFLOW_STATUS',
    type: 'workflow',
    family: 'WORKFLOW',
    preconditions: ['WORKFLOW_READ'],
    outputType: 'JSON',
    outputFile: 'workflow_status.json',
    description: 'Retrieve status of running workflows',
    createdAt: new Date('2024-01-10'),
    updatedAt: new Date('2024-02-05'),
  },
  {
    id: 'cmd-004',
    name: 'SYSINFO',
    type: 'system',
    family: 'SYSTEM',
    preconditions: ['SYSTEM_READ'],
    outputType: 'TEXT',
    description: 'Display system configuration and status',
    createdAt: new Date('2024-01-05'),
    updatedAt: new Date('2024-01-30'),
  },
  {
    id: 'cmd-005',
    name: 'ALLOC_DATASET',
    type: 'metadata',
    family: 'DATASET',
    preconditions: ['DATASET_CREATE', 'STORAGE_QUOTA'],
    outputType: 'JSON',
    outputFile: 'allocation_result.json',
    description: 'Allocate new dataset with specified parameters',
    createdAt: new Date('2024-01-25'),
    updatedAt: new Date('2024-02-03'),
  },
];

// Mock Jobs
export const mockJobs: Job[] = [
  {
    id: 'job-001',
    name: 'PAYROLL_BATCH',
    scope: 'enterprise',
    mainframe: 'ZPROD01',
    type: 'JCL',
    accessLevel: 'restricted',
    status: 'active',
    lastRun: new Date('2024-02-09T03:00:00'),
    downloadUrl: '/downloads/payroll_batch.jcl',
  },
  {
    id: 'job-002',
    name: 'BACKUP_PROC',
    scope: 'system',
    mainframe: 'ZPROD02',
    type: 'PROC',
    accessLevel: 'admin',
    status: 'active',
    lastRun: new Date('2024-02-10T01:00:00'),
    downloadUrl: '/downloads/backup_proc.jcl',
  },
  {
    id: 'job-003',
    name: 'REPORT_GEN',
    scope: 'user',
    mainframe: 'ZDEV01',
    type: 'COBOL',
    accessLevel: 'read-only',
    status: 'active',
    lastRun: new Date('2024-02-09T12:00:00'),
    downloadUrl: '/downloads/report_gen.cob',
  },
];

// Mock Workflows
export const mockWorkflows: Workflow[] = [
  {
    id: 'wf-001',
    name: 'ETL_PIPELINE',
    scope: 'enterprise',
    mainframe: 'ZPROD01',
    type: 'WORKFLOW',
    accessLevel: 'admin',
    status: 'active',
    lastRun: new Date('2024-02-10T00:00:00'),
    steps: 5,
    dependencies: ['DATASET.EXTRACT', 'DATASET.STAGING'],
    downloadUrl: '/downloads/etl_pipeline.xml',
  },
  {
    id: 'wf-002',
    name: 'MONTHLY_CLOSE',
    scope: 'enterprise',
    mainframe: 'ZPROD01',
    type: 'WORKFLOW',
    accessLevel: 'restricted',
    status: 'active',
    lastRun: new Date('2024-02-01T00:00:00'),
    steps: 12,
    dependencies: ['JOB.PAYROLL', 'JOB.RECONCILE'],
    downloadUrl: '/downloads/monthly_close.xml',
  },
];

// Mock Datasets
export const mockDatasets: Dataset[] = [
  {
    id: 'ds-001',
    name: 'PROD.MASTER.DATA',
    scope: 'enterprise',
    mainframe: 'ZPROD01',
    type: 'DATASET',
    accessLevel: 'read-only',
    size: '2.4 GB',
    records: 1500000,
    downloadUrl: '/downloads/master_data.dat',
  },
  {
    id: 'ds-002',
    name: 'USER.TEMP.WORK',
    scope: 'user',
    mainframe: 'ZDEV01',
    type: 'DATASET',
    accessLevel: 'read-only',
    size: '128 MB',
    records: 50000,
    downloadUrl: '/downloads/temp_work.dat',
  },
  {
    id: 'ds-003',
    name: 'SYS.CONFIG.PARMS',
    scope: 'system',
    mainframe: 'ZPROD02',
    type: 'DATASET',
    accessLevel: 'admin',
    size: '4.2 MB',
    records: 1200,
    downloadUrl: '/downloads/config_parms.dat',
  },
];

// Mock Catalog Stats
export const mockCatalogStats: CatalogStats = {
  totalCommands: 247,
  totalJobs: 183,
  totalWorkflows: 42,
  totalDatasets: 1548,
  lastUpdated: new Date('2024-02-10T08:30:00'),
};

// Mock Reasoning Logs
export const mockReasoningLogs: ReasoningLog[] = [
  {
    id: 'log-001',
    timestamp: new Date('2024-02-10T10:15:23'),
    level: 'thought',
    message: 'User requesting dataset allocation. Analyzing prerequisites...',
  },
  {
    id: 'log-002',
    timestamp: new Date('2024-02-10T10:15:24'),
    level: 'action',
    message: 'Checking user permissions for DATASET_CREATE',
  },
  {
    id: 'log-003',
    timestamp: new Date('2024-02-10T10:15:25'),
    level: 'observation',
    message: 'User has required permissions. Storage quota: 80% utilized',
  },
  {
    id: 'log-004',
    timestamp: new Date('2024-02-10T10:15:26'),
    level: 'decision',
    message: 'Proceeding with allocation on ZPROD01. Executing ALLOC_DATASET command',
  },
];

// Mock Chat Messages
export const mockChatMessages: ChatMessage[] = [
  {
    id: 'msg-001',
    role: 'user',
    content: 'Show me all active jobs on ZPROD01',
    timestamp: new Date('2024-02-10T10:00:00'),
  },
  {
    id: 'msg-002',
    role: 'agent',
    content: 'I found 23 active jobs on ZPROD01. Here are the results:',
    timestamp: new Date('2024-02-10T10:00:02'),
    canonicalOutput: {
      type: 'table',
      data: mockJobs.filter(j => j.mainframe === 'ZPROD01'),
    },
  },
];

// Mock IBM Agent Status
export const mockIBMAgentStatus: AgentStatus = {
  id: 'ibm-agent-001',
  name: 'IBM z/OS Agent',
  status: 'online',
  capabilities: [
    'JCL Execution',
    'Dataset Management',
    'RACF Integration',
    'CICS Transaction Processing',
    'DB2 Query Execution',
  ],
  uptime: 864000000, // 10 days in ms
  tasksCompleted: 1547,
  lastActivity: new Date('2024-02-10T10:30:00'),
};

// Mock Unisys Agent Status
export const mockUnisysAgentStatus: AgentStatus = {
  id: 'unisys-agent-001',
  name: 'Unisys MCP Agent',
  status: 'online',
  capabilities: [
    'WFL Execution',
    'File Management',
    'Security Matrix Integration',
    'COMS Processing',
    'DMSII Operations',
  ],
  uptime: 432000000, // 5 days in ms
  tasksCompleted: 892,
  lastActivity: new Date('2024-02-10T10:28:00'),
};

// Mock Agent Executions
export const mockAgentExecutions: AgentExecution[] = [
  {
    id: 'exec-001',
    taskId: 'task-1001',
    command: 'LISTCAT LEVEL(PROD.MASTER)',
    status: 'completed',
    startTime: new Date('2024-02-10T09:45:00'),
    endTime: new Date('2024-02-10T09:45:12'),
    result: { recordsFound: 234 },
  },
  {
    id: 'exec-002',
    taskId: 'task-1002',
    command: 'SUBMIT JOB(PAYROLL)',
    status: 'running',
    startTime: new Date('2024-02-10T10:30:00'),
  },
  {
    id: 'exec-003',
    taskId: 'task-1003',
    command: 'WORKFLOW_STATUS(ETL_PIPELINE)',
    status: 'completed',
    startTime: new Date('2024-02-10T10:15:00'),
    endTime: new Date('2024-02-10T10:15:03'),
    result: { status: 'running', progress: '60%' },
  },
];

// Mock Agent Configs
export const mockIBMAgentConfig: AgentConfig = {
  environment: 'z/OS 2.5',
  version: '3.2.1',
  maxConcurrentTasks: 10,
  timeout: 300000,
  retryPolicy: {
    maxRetries: 3,
    backoffMs: 5000,
  },
};

export const mockUnisysAgentConfig: AgentConfig = {
  environment: 'MCP 18.1',
  version: '2.8.4',
  maxConcurrentTasks: 8,
  timeout: 300000,
  retryPolicy: {
    maxRetries: 3,
    backoffMs: 5000,
  },
};
