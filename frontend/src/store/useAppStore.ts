import { useSyncExternalStore } from "react";

export type ControlCenterPanel =
  | "execution"
  | "intent"
  | "context"
  | "reasoning"
  | "planner"
  | "normalization"
  | "federation";

export interface IntentCondition {
  field: string;
  value: string | number | boolean | null;
}

export interface IntentData {
  task: string;
  entities: string[];
  attributes: string[];
  filters: {
    time_range?: {
      start: string;
      end: string;
    } | null;
    conditions: IntentCondition[];
  };
  systems: string[];
  metric?: string | null;
  aggregation?: string | null;
  output_mode: string;
  requires_federation: boolean;
  priority: string;
  confidence_score: number;
}

export interface IBMContextData {
  program?: string | null;
  program_name?: string | null;
  dataset?: string | null;
  all_datasets: string[];
  jcl_job?: string | null;
  jcl_steps: Array<Record<string, unknown>>;
  variables: Array<Record<string, unknown>>;
  io_operations: Record<string, string[]>;
}

export interface UnisysParam {
  name: string;
  type: string;
  required: boolean;
}

export interface UnisysContextData {
  api?: string | null;
  fields: string[];
  tool_name?: string | null;
  params: UnisysParam[];
  schema_endpoint?: string | null;
  entity?: string | null;
}

export interface ContextData {
  ibm?: IBMContextData | null;
  unisys?: UnisysContextData | null;
  entity_mapping: Record<string, string>;
  entities_resolved: string[];
  systems_checked: string[];
  resolution_confidence: number;
  is_federation: boolean;
  reasoning_summary?: string | null;
  warnings: string[];
}

export interface PipelineResponse {
  intent: IntentData;
  context: ContextData;
  planner_json?: Record<string, unknown> | null;
  execution?: Record<string, unknown> | null;
  normalization?: Record<string, unknown> | null;
  federation_intelligence?: Record<string, unknown> | null;
  pipeline_stage: string;
  next_stage: string;
  summary: string;
}

export interface ValidationItem {
  label: string;
  status: "pass" | "warn" | "fail";
  detail: string;
}

export interface ValidationGroup {
  title: string;
  description: string;
  score: number;
  items: ValidationItem[];
}

export interface ValidationData {
  summary: {
    pass: number;
    warn: number;
    fail: number;
  };
  p0: ValidationGroup;
  p1: ValidationGroup;
  p2: ValidationGroup;
}

export interface ReasoningData {
  objective: string;
  decisions: string[];
  skippedSystems: string[];
  semanticGaps: string[];
  operationalWarnings: string[];
}

export interface SystemHealth {
  pipelineOnline: boolean;
  contextOnline: boolean;
  eportalAvailable: boolean;
}

export interface AppState {
  query: string;
  activePanel: ControlCenterPanel;
  pipelineStage: string;
  summary: string | null;
  nextStage: string | null;
  intent: IntentData | null;
  context: ContextData | null;
  planner: Record<string, unknown> | null;
  execution: Record<string, unknown> | null;
  normalization: Record<string, unknown> | null;
  federation: Record<string, unknown> | null;
  reasoning: ReasoningData | null;
  warnings: string[];
  validation: ValidationData | null;
  trace: Record<string, unknown> | null;
  loading: boolean;
  error: string | null;
  health: SystemHealth;
  resultReady: boolean;
  setQuery: (query: string) => void;
  setActivePanel: (panel: ControlCenterPanel) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setHealth: (health: Partial<SystemHealth>) => void;
  resetRunState: () => void;
  applyPipelineResponse: (response: PipelineResponse) => void;
}

const isOperationalWarning = (message: string) => {
  const normalized = message.toLowerCase();
  return [
    "fallback",
    "failed",
    "error",
    "unreachable",
    "quota",
    "retry",
    "timeout",
    "unavailable",
  ].some((token) => normalized.includes(token));
};

const extractObjective = (query: string, intent: IntentData) => {
  const trimmedQuery = query.trim();
  if (trimmedQuery) {
    return trimmedQuery;
  }
  return `${intent.task} ${intent.entities.join(", ")}`;
};

const detectSemanticGaps = (query: string, response: PipelineResponse) => {
  const normalizedQuery = query.toLowerCase();
  const gaps: string[] = [];

  const asksForAggregate =
    /\b(total|sum|average|avg|count|maximum|max|minimum|min)\b/.test(normalizedQuery);

  if (asksForAggregate && response.intent.task === "fetch") {
    gaps.push(
      "The query asks for an aggregate result, but the current intent model only captured a fetch request."
    );
  }

  if (
    asksForAggregate &&
    !response.summary.toLowerCase().includes("total") &&
    response.context.unisys?.api
  ) {
    gaps.push(
      "The pipeline resolved a source system, but it did not yet model the aggregation step needed to compute the final total spend."
    );
  }

  return gaps;
};

const deriveReasoning = (query: string, response: PipelineResponse): ReasoningData => {
  const nonOperationalMessages = response.context.warnings.filter(
    (entry) => !isOperationalWarning(entry)
  );
  const operationalWarnings = response.context.warnings.filter(isOperationalWarning);

  const decisions = [
    `Intent mapped the request to ${response.intent.task} on ${response.intent.entities.join(", ")}.`,
    `Systems selected: ${response.intent.systems.join(", ")}.`,
    ...(response.context.reasoning_summary ? [response.context.reasoning_summary] : []),
    ...(response.execution ? ["Execution Agent ran the planner handoff and returned step results."] : []),
    ...(response.normalization ? ["Normalization Agent mapped execution outputs into common canonical records."] : []),
    ...(response.federation_intelligence ? ["Federation Intelligence consumed normalized records to recommend a federated view."] : []),
    ...nonOperationalMessages,
  ];

  const skippedSystems: string[] = [];
  if (!response.intent.systems.includes("ibm")) {
    skippedSystems.push("IBM was skipped because the intent model assigned shopping to the Unisys domain.");
  }
  if (!response.intent.systems.includes("unisys")) {
    skippedSystems.push("Unisys was skipped because the request did not resolve to a Unisys-owned entity.");
  }

  return {
    objective: extractObjective(query, response.intent),
    decisions,
    skippedSystems,
    semanticGaps: detectSemanticGaps(query, response),
    operationalWarnings,
  };
};

const deriveValidation = (response: PipelineResponse): ValidationData => {
  const intentConfidence = response.intent?.confidence_score ?? 0;
  const contextConfidence = response.context?.resolution_confidence ?? 0;
  const warnings = response.context?.warnings ?? [];
  const operationalWarnings = warnings.filter(isOperationalWarning);

  const p0: ValidationGroup = {
    title: "P0",
    description: "Critical trust and governance checks",
    score: response.context.entities_resolved.length > 0 ? 0.94 : 0.7,
    items: [
      {
        label: "Access control",
        status: "pass",
        detail: "No access-control violations surfaced by the pipeline response.",
      },
      {
        label: "Policy compliance",
        status: operationalWarnings.length > 0 ? "warn" : "pass",
        detail: operationalWarnings.length > 0
          ? "Review runtime warnings before execution planning."
          : "No policy-related warnings were returned.",
      },
      {
        label: "Data integrity",
        status: response.context.entities_resolved.length > 0 ? "pass" : "warn",
        detail:
          response.context.entities_resolved.length > 0
            ? "At least one target system was resolved for the request."
            : "No system was resolved yet.",
      },
    ],
  };

  const p1: ValidationGroup = {
    title: "P1",
    description: "Pipeline and dependency health",
    score: response.context.systems_checked.length > 0 ? 0.9 : 0.68,
    items: [
      {
        label: "Pipeline health",
        status: "pass",
        detail: `Pipeline stopped at ${response.pipeline_stage}.`,
      },
      {
        label: "Dependency health",
        status: response.context.systems_checked.length > 0 ? "pass" : "warn",
        detail: `${response.context.systems_checked.length} downstream system(s) checked.`,
      },
      {
        label: "Planner readiness",
        status: response.planner_json ? "pass" : "warn",
        detail: `Next orchestration handoff: ${response.next_stage}.`,
      },
    ],
  };

  const p2: ValidationGroup = {
    title: "P2",
    description: "AI quality and model confidence",
    score: (intentConfidence + contextConfidence) / 2,
    items: [
      {
        label: "Intent confidence",
        status: intentConfidence >= 0.8 ? "pass" : "warn",
        detail: `${Math.round(intentConfidence * 100)}% confidence in intent extraction.`,
      },
      {
        label: "Context confidence",
        status: contextConfidence >= 0.8 ? "pass" : "warn",
        detail: `${Math.round(contextConfidence * 100)}% confidence in context resolution.`,
      },
      {
        label: "Hallucination risk",
        status: operationalWarnings.length > 0 ? "warn" : "pass",
        detail: operationalWarnings.length > 0
          ? "Fallback or infrastructure warnings increase review need."
          : "No immediate reasoning anomalies surfaced.",
      },
    ],
  };

  const allItems = [...p0.items, ...p1.items, ...p2.items];

  return {
    summary: {
      pass: allItems.filter((item) => item.status === "pass").length,
      warn: allItems.filter((item) => item.status === "warn").length,
      fail: allItems.filter((item) => item.status === "fail").length,
    },
    p0,
    p1,
    p2,
  };
};

const initialState = (): Omit<
  AppState,
  "setQuery" | "setActivePanel" | "setLoading" | "setError" | "setHealth" | "resetRunState" | "applyPipelineResponse"
> => ({
  query: "",
  activePanel: "execution",
  pipelineStage: "idle",
  summary: null,
  nextStage: null,
  intent: null,
  context: null,
  planner: null,
  execution: null,
  normalization: null,
  federation: null,
  reasoning: null,
  warnings: [],
  validation: null,
  trace: null,
  loading: false,
  error: null,
  health: {
    pipelineOnline: false,
    contextOnline: false,
    eportalAvailable: false,
  },
  resultReady: false,
});

let state: AppState;
const listeners = new Set<() => void>();

const emitChange = () => {
  listeners.forEach((listener) => listener());
};

const updateState = (updater: Partial<AppState> | ((current: AppState) => Partial<AppState>)) => {
  const next = typeof updater === "function" ? updater(state) : updater;
  state = { ...state, ...next };
  emitChange();
};

state = {
  ...initialState(),
  setQuery: (query) => updateState({ query }),
  setActivePanel: (panel) => updateState({ activePanel: panel }),
  setLoading: (loading) => updateState({ loading }),
  setError: (error) => updateState({ error }),
  setHealth: (health) =>
    updateState((current) => ({ health: { ...current.health, ...health } })),
  resetRunState: () =>
    updateState((current) => ({
      ...initialState(),
      health: current.health,
      query: current.query,
      activePanel: "execution",
    })),
  applyPipelineResponse: (response) => {
    const reasoning = deriveReasoning(state.query, response);
    const warnings = reasoning.operationalWarnings;

    updateState({
      intent: response.intent,
      context: response.context,
      planner: response.planner_json ?? null,
      execution: response.execution ?? null,
      normalization: response.normalization ?? null,
      federation: response.federation_intelligence ?? null,
      reasoning,
      warnings: [
        ...warnings,
        ...((response.normalization as { warnings?: string[] } | null | undefined)?.warnings ?? []),
      ],
      validation: deriveValidation(response),
      trace: {
        pipeline_stage: response.pipeline_stage,
        next_stage: response.next_stage,
        systems_checked: response.context.systems_checked,
        execution_status: (response.execution as { status?: string } | null | undefined)?.status,
        normalized_records: (response.normalization as { summary?: { total_records?: number } } | null | undefined)?.summary?.total_records,
        federation_view: (response.federation_intelligence as { top_view?: { view_id?: string } } | null | undefined)?.top_view?.view_id,
      },
      pipelineStage: response.pipeline_stage,
      summary: response.summary,
      nextStage: response.next_stage,
      loading: false,
      error: null,
      resultReady: true,
    });
  },
};

const subscribe = (listener: () => void) => {
  listeners.add(listener);
  return () => listeners.delete(listener);
};

export const useAppStore = <T,>(selector: (appState: AppState) => T): T =>
  useSyncExternalStore(subscribe, () => selector(state), () => selector(state));

export const appStore = {
  getState: () => state,
};
