import type { IntentData } from "@/store/useAppStore";

interface Props {
  intent: IntentData | null;
  loading?: boolean;
}

const percent = (value: number) => `${Math.round(value * 100)}%`;

export const IntentPanel = ({ intent, loading = false }: Props) => {
  if (!intent && !loading) {
    return null;
  }

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
      <div className="pb-4">
        <h2 className="text-base font-semibold text-amber-300">Intent Analysis</h2>
      </div>
      <div className="space-y-6">
        {loading ? (
          <p className="text-sm text-slate-400">Extracting task, entities, and filters...</p>
        ) : intent ? (
          <>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Task</p>
                <p className="mt-2 text-lg font-semibold text-slate-100">{intent.task}</p>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Priority</p>
                <p className="mt-2 text-lg font-semibold capitalize text-slate-100">{intent.priority}</p>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Confidence</p>
                <p className="mt-2 text-lg font-semibold text-emerald-300">{percent(intent.confidence_score)}</p>
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Entities</p>
              <div className="flex flex-wrap gap-2">
                {intent.entities.map((entity) => (
                  <span key={entity} className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-200">
                    {entity}
                  </span>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Attributes</p>
              <div className="flex flex-wrap gap-2">
                {intent.attributes.map((attribute) => (
                  <span key={attribute} className="rounded-full border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-200">
                    {attribute}
                  </span>
                ))}
              </div>
            </div>

            <div className="space-y-3">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Systems</p>
              <div className="flex flex-wrap gap-2">
                {intent.systems.map((system) => (
                  <span key={system} className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-200">
                    {system.toUpperCase()}
                  </span>
                ))}
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Time Range</p>
                <p className="mt-2 text-sm text-slate-200">
                  {intent.filters.time_range
                    ? `${intent.filters.time_range.start} to ${intent.filters.time_range.end}`
                    : "No explicit range extracted"}
                </p>
              </div>

              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Filter Conditions</p>
                <div className="mt-2 space-y-2">
                  {intent.filters.conditions.length > 0 ? (
                    intent.filters.conditions.map((condition) => (
                      <div
                        key={`${condition.field}-${String(condition.value)}`}
                        className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2 text-sm"
                      >
                        <span className="text-slate-400">{condition.field}</span>
                        <span className="font-mono text-cyan-200">{String(condition.value)}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-slate-400">No explicit filter conditions extracted.</p>
                  )}
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Raw Intent JSON</p>
              <pre className="mt-3 overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950/70 p-4 text-xs leading-6 text-slate-200">
                {JSON.stringify(intent, null, 2)}
              </pre>
            </div>
          </>
        ) : null}
      </div>
    </section>
  );
};
