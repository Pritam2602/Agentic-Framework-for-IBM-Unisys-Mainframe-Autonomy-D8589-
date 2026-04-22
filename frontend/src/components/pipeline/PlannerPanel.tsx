import type { ContextData, IntentData } from "@/store/useAppStore";

export interface ExecutionStep {
  step: number;
  label: string;
  detail: string;
  system?: "ibm" | "unisys" | "federation";
}

export interface PlanData {
  totalSteps: number;
  steps: ExecutionStep[];
}

interface Props {
  intent: IntentData | null;
  context: ContextData | null;
  nextStage: string | null;
}

const buildPlanPreview = (intent: IntentData | null, context: ContextData | null): PlanData | null => {
  if (!intent || !context) {
    return null;
  }

  const steps: ExecutionStep[] = [];

  if (context.unisys?.api) {
    steps.push({
      step: steps.length + 1,
      label: "Call Unisys API",
      detail: `Query ${context.unisys.api} with extracted filters for ${intent.entities.join(", ")}.`,
      system: "unisys",
    });
  }

  if (context.ibm?.program || context.ibm?.dataset) {
    steps.push({
      step: steps.length + 1,
      label: "Plan IBM access",
      detail: `Use the Zowe command catalog to plan access for ${context.ibm.dataset ?? context.ibm.program ?? "mainframe assets"}.`,
      system: "ibm",
    });
  }

  steps.push({
    step: steps.length + 1,
    label: "Assemble business response",
    detail: "Normalize system outputs into a planner-ready federation payload.",
    system: "federation",
  });

  return {
    totalSteps: steps.length,
    steps,
  };
};

const badgeClass = (system?: ExecutionStep["system"]) => {
  if (system === "ibm") {
    return "border-red-500/30 bg-red-500/10 text-red-200";
  }
  if (system === "unisys") {
    return "border-cyan-500/30 bg-cyan-500/10 text-cyan-200";
  }
  return "border-violet-500/30 bg-violet-500/10 text-violet-200";
};

export const PlannerPanel = ({ intent, context, nextStage }: Props) => {
  const plan = buildPlanPreview(intent, context);

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
      <div className="pb-4">
        <h2 className="text-base font-semibold text-orange-300">Planner Preview</h2>
      </div>
      <div className="space-y-5">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Next Stage</p>
          <p className="mt-2 text-lg font-semibold text-slate-100">{nextStage ?? "Planner not assigned"}</p>
          <p className="mt-2 text-sm text-slate-400">
            The backend has not produced a full planner artifact yet, so this panel shows the execution design that would be passed downstream.
          </p>
        </div>

        {plan ? (
          <div className="space-y-3">
            {plan.steps.map((step) => (
              <div key={step.step} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-slate-100">
                      Step {step.step}: {step.label}
                    </p>
                    <p className="mt-1 text-sm text-slate-400">{step.detail}</p>
                  </div>
                  <span className={`rounded-full border px-3 py-1 text-xs font-semibold ${badgeClass(step.system)}`}>
                    {(step.system ?? "federation").toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-sm text-slate-400">Run the pipeline to generate a planner handoff preview.</p>
        )}
      </div>
    </section>
  );
};
