import { CheckCircleIcon, ClockIcon, ArrowPathIcon } from "@heroicons/react/24/outline";
import { cn } from "@/lib/utils";

type VisualStatus = "completed" | "active" | "pending";

interface VisualStage {
  id: string;
  label: string;
  status: VisualStatus;
  detail: string;
}

interface Props {
  pipelineStage: string;
  loading: boolean;
  nextStage: string | null;
}

const getStages = (pipelineStage: string, loading: boolean, nextStage: string | null): VisualStage[] => {
  const completed = new Set<string>();
  let active = "execution";

  if (loading) {
    active = "intent";
  } else if (pipelineStage === "context_resolved") {
    completed.add("intent");
    completed.add("context");
    active = "planner";
  } else if (pipelineStage === "planner_ready") {
    completed.add("intent");
    completed.add("context");
    completed.add("planner");
    active = "execution";
  } else if (pipelineStage === "federated") {
    completed.add("intent");
    completed.add("context");
    completed.add("planner");
    completed.add("execution");
    completed.add("federation");
    active = "federation";
  } else if (pipelineStage === "consumer_ready") {
    completed.add("intent");
    completed.add("context");
    completed.add("planner");
    completed.add("execution");
    completed.add("normalization");
    completed.add("federation");
    active = "consumer";
  }

  const base: Array<Omit<VisualStage, "status">> = [
    { id: "intent", label: "Intent", detail: "Understand the business request." },
    { id: "context", label: "Context", detail: "Resolve IBM and Unisys data locations." },
    {
      id: "planner",
      label: "Planner",
      detail: nextStage === "planner_agent" ? "Next stage is queued for planning." : "Execution plan not generated yet.",
    },
    { id: "execution", label: "Execution", detail: "Run APIs or jobs when planner is ready." },
    { id: "normalization", label: "Normalization", detail: "Map outputs into common records." },
    { id: "federation", label: "Federation", detail: "Recommend and assemble federated views." },
  ];

  return base.map((stage) => ({
    ...stage,
    status: completed.has(stage.id) ? "completed" : stage.id === active ? "active" : "pending",
  }));
};

const iconForStatus = (status: VisualStatus) => {
  if (status === "completed") {
    return <CheckCircleIcon className="h-5 w-5 text-emerald-400" />;
  }
  if (status === "active") {
    return <ArrowPathIcon className="h-5 w-5 animate-spin text-cyan-400" />;
  }
  return <ClockIcon className="h-5 w-5 text-slate-500" />;
};

export const PipelineVisualization = ({ pipelineStage, loading, nextStage }: Props) => {
  const stages = getStages(pipelineStage, loading, nextStage);

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
      <div className="pb-4">
        <h2 className="text-base font-semibold text-cyan-300">Pipeline Status</h2>
      </div>
      <div className="space-y-4">
        <div className="grid gap-3 md:grid-cols-6">
          {stages.map((stage, index) => (
            <div key={stage.id} className="flex items-center gap-3 md:block">
              <div
                className={cn(
                  "rounded-2xl border p-4 transition-all",
                  stage.status === "completed" && "border-emerald-500/40 bg-emerald-500/10",
                  stage.status === "active" && "border-cyan-500/50 bg-cyan-500/10 shadow-[0_0_24px_rgba(34,211,238,0.14)]",
                  stage.status === "pending" && "border-slate-800 bg-slate-900/80"
                )}
              >
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-semibold text-slate-100">{stage.label}</span>
                  {iconForStatus(stage.status)}
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-400">{stage.detail}</p>
              </div>
              {index < stages.length - 1 && (
                <div className="hidden h-px flex-1 bg-gradient-to-r from-slate-700 to-slate-900 md:block" />
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export type PipelineStage = VisualStage;
export interface PipelineState {
  pipelineStage: string;
  loading: boolean;
  nextStage: string | null;
}
