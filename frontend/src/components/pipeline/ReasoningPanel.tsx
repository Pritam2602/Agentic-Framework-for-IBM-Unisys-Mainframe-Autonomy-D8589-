import { ExclamationTriangleIcon, LightBulbIcon } from "@heroicons/react/24/outline";
import type { ReasoningData } from "@/store/useAppStore";

interface Props {
  reasoning: ReasoningData | null;
  warnings: string[];
}

export const ReasoningPanel = ({ reasoning, warnings }: Props) => {
  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
      <div className="pb-4">
        <h2 className="text-base font-semibold text-violet-300">Reasoning</h2>
      </div>
      <div className="space-y-8">
        <section className="grid gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(260px,0.65fr)]">
          <div className="rounded-2xl border border-violet-500/15 bg-violet-500/5 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-violet-200/70">
              Objective
            </p>
            <p className="mt-3 text-lg leading-8 text-slate-100">
              {reasoning?.objective ?? "Run the pipeline to see the interpreted objective."}
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              Reasoning Summary
            </p>
            <div className="mt-4 grid grid-cols-3 gap-3">
              <div>
                <p className="text-2xl font-semibold text-slate-100">{reasoning?.decisions.length ?? 0}</p>
                <p className="mt-1 text-xs text-slate-500">decisions</p>
              </div>
              <div>
                <p className="text-2xl font-semibold text-amber-200">{warnings.length}</p>
                <p className="mt-1 text-xs text-slate-500">warnings</p>
              </div>
              <div>
                <p className="text-2xl font-semibold text-rose-200">{reasoning?.semanticGaps.length ?? 0}</p>
                <p className="mt-1 text-xs text-slate-500">gaps</p>
              </div>
            </div>
          </div>
        </section>

        <section className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            <LightBulbIcon className="h-4 w-4 text-violet-300" />
            Decision Logic
          </div>

          {reasoning && reasoning.decisions.length > 0 ? (
            <div className="space-y-3">
              {reasoning.decisions.map((entry, index) => (
                <div key={`${entry}-${index}`} className="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-4">
                  <p className="text-sm leading-6 text-slate-200">{entry}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <p className="text-sm text-slate-400">
                No separate reasoning summary was returned for this run. When the LLM provides a narrative explanation, it will appear here.
              </p>
            </div>
          )}
        </section>

        <section className="grid gap-6 xl:grid-cols-2">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
              <ExclamationTriangleIcon className="h-4 w-4 text-cyan-300" />
              Skipped Systems
            </div>

            {reasoning && reasoning.skippedSystems.length > 0 ? (
              <div className="space-y-3">
                {reasoning.skippedSystems.map((entry, index) => (
                  <div key={`${entry}-${index}`} className="rounded-2xl border border-cyan-500/20 bg-cyan-500/5 p-4">
                    <p className="text-sm leading-6 text-slate-200">{entry}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-sm text-slate-400">No systems were explicitly skipped in this run.</p>
              </div>
            )}
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
              <ExclamationTriangleIcon className="h-4 w-4 text-rose-300" />
              Semantic Gaps
            </div>

            {reasoning && reasoning.semanticGaps.length > 0 ? (
              <div className="space-y-3">
                {reasoning.semanticGaps.map((entry, index) => (
                  <div key={`${entry}-${index}`} className="rounded-2xl border border-rose-500/20 bg-rose-500/5 p-4">
                    <p className="text-sm leading-6 text-slate-200">{entry}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4">
                <p className="text-sm text-emerald-200">No obvious semantic gaps were detected for this run.</p>
              </div>
            )}
          </div>
        </section>

        <section className="space-y-3">
          <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">
            <ExclamationTriangleIcon className="h-4 w-4 text-amber-300" />
            Operational Warnings
          </div>

          {warnings.length > 0 ? (
            <div className="space-y-3">
              {warnings.map((entry, index) => (
                <div key={`${entry}-${index}`} className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4">
                  <p className="text-sm leading-6 text-slate-200">{entry}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4">
              <p className="text-sm text-emerald-200">No runtime warnings were returned for this request.</p>
            </div>
          )}
        </section>
      </div>
    </section>
  );
};
