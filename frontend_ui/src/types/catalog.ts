export type Category = "metadata" | "data" | "workflow" | "transaction";

export type CommandFamily = "DB2" | "CICS" | "IMS" | "FILES" | "PLATFORM" | "OBSERVABILITY";

export type Subsystem = "DB2" | "CICS" | "IMS" | "z/OSMF";

export type Operation = "READ" | "EXECUTE";

export type AccessPattern = "CLI" | "REST" | "JOB_OUTPUT";

export type ResponseFormat = "JSON" | "TEXT";

export type ExecutionCost = "LOW" | "MEDIUM" | "HIGH";

export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW";

export type AgentType = 
  | "DiscoveryAgent" 
  | "InfraAgent" 
  | "ControlAgent" 
  | "MonitorAgent" 
  | "ComplianceAgent";

export interface CatalogEntry {
  id: string;
  zowe_command: string;
  category: Category;
  command_family: CommandFamily;
  subsystem: Subsystem;
  ibm_artifact: string;
  operation: Operation;
  access_pattern: AccessPattern;
  response_format: ResponseFormat;
  intended_agent: AgentType;
  constraints: string;
  execution_cost: ExecutionCost;
  confidence_level: ConfidenceLevel;
}

export interface CatalogFilters {
  search: string;
  commandFamily: CommandFamily | "ALL";
  subsystem: Subsystem | "ALL";
  operation: Operation | "ALL";
}
