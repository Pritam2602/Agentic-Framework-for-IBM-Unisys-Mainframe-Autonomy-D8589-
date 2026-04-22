import type { ContextData } from "@/store/useAppStore";

interface Props {
  context: ContextData | null;
  loading?: boolean;
}

const confidenceText = (value: number) => `${Math.round(value * 100)}%`;
const isIbmResolved = (context: ContextData | null) =>
  Boolean(context?.ibm?.program || context?.ibm?.dataset || context?.ibm?.jcl_job);
const isUnisysResolved = (context: ContextData | null) =>
  Boolean(context?.unisys?.api || context?.unisys?.tool_name);

export const ContextPanel = ({ context, loading = false }: Props) => {
  if (!context && !loading) {
    return null;
  }

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
      <div className="pb-4">
        <h2 className="text-base font-semibold text-sky-300">Context Resolution</h2>
      </div>
      <div className="space-y-6">
        {loading ? (
          <p className="text-sm text-slate-400">Resolving system metadata and data locations...</p>
        ) : context ? (
          <>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Systems Checked</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {context.systems_checked.map((system) => (
                    <span key={system} className="rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-xs font-semibold text-sky-200">
                      {system.toUpperCase()}
                    </span>
                  ))}
                </div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Entities Resolved</p>
                <div className="mt-2 space-y-1">
                  {context.entities_resolved.length > 0 ? (
                    context.entities_resolved.map((entity) => (
                      <p key={entity} className="font-mono text-sm text-slate-100">
                        {entity}
                      </p>
                    ))
                  ) : (
                    <p className="text-sm text-slate-400">No entity fully resolved yet.</p>
                  )}
                </div>
              </div>
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Resolution Confidence</p>
                <p className="mt-2 text-lg font-semibold text-emerald-300">
                  {confidenceText(context.resolution_confidence)}
                </p>
              </div>
            </div>

            <div className="grid gap-4 xl:grid-cols-2">
              <div className="rounded-3xl border border-red-500/20 bg-red-500/5 p-5">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-red-200">IBM</h3>
                  <span className="rounded-full border border-red-400/30 px-3 py-1 text-xs font-semibold text-red-200">
                    {isIbmResolved(context) ? "Resolved" : context.ibm ? "Partial" : "Skipped"}
                  </span>
                </div>

                {context.ibm ? (
                  <div className="mt-4 space-y-3 text-sm">
                    <div>
                      <p className="text-slate-500">Program</p>
                      <p className="font-mono text-slate-100">{context.ibm.program ?? "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Dataset</p>
                      <p className="font-mono text-slate-100">{context.ibm.dataset ?? "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">JCL Job</p>
                      <p className="font-mono text-slate-100">{context.ibm.jcl_job ?? "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Related Datasets</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {context.ibm.all_datasets.length > 0 ? (
                          context.ibm.all_datasets.map((dataset) => (
                            <span key={dataset} className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs font-semibold text-slate-200">
                              {dataset}
                            </span>
                          ))
                        ) : (
                          <span className="text-slate-400">No datasets returned.</span>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="mt-4 text-sm text-slate-400">
                    IBM metadata was not required for this request.
                  </p>
                )}
              </div>

              <div className="rounded-3xl border border-cyan-500/20 bg-cyan-500/5 p-5">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-cyan-200">Unisys</h3>
                  <span className="rounded-full border border-cyan-400/30 px-3 py-1 text-xs font-semibold text-cyan-200">
                    {isUnisysResolved(context) ? "Resolved" : context.unisys ? "Partial" : "Skipped"}
                  </span>
                </div>

                {context.unisys ? (
                  <div className="mt-4 space-y-3 text-sm">
                    <div>
                      <p className="text-slate-500">API Endpoint</p>
                      <p className="font-mono text-slate-100">{context.unisys.api ?? "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">MCP Tool</p>
                      <p className="font-mono text-slate-100">{context.unisys.tool_name ?? "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Schema Endpoint</p>
                      <p className="font-mono text-slate-100">{context.unisys.schema_endpoint ?? "N/A"}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Available Fields</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {context.unisys.fields.map((field) => (
                          <span key={field} className="rounded-full border border-slate-700 bg-slate-900 px-3 py-1 text-xs font-semibold text-slate-200">
                            {field}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="text-slate-500">Supported Params</p>
                      <div className="mt-2 space-y-2">
                        {context.unisys.params.map((param) => (
                          <div
                            key={param.name}
                            className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/60 px-3 py-2"
                          >
                            <span className="font-mono text-slate-100">{param.name}</span>
                            <span className="text-slate-400">{param.required ? "required" : "optional"}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="mt-4 text-sm text-slate-400">
                    Unisys metadata was not required for this request.
                  </p>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Raw Context JSON</p>
              <pre className="mt-3 overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950/70 p-4 text-xs leading-6 text-slate-200">
                {JSON.stringify(context, null, 2)}
              </pre>
            </div>
          </>
        ) : null}
      </div>
    </section>
  );
};
