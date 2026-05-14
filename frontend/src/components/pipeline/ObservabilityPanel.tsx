import { useEffect, useState } from "react";

type ObservabilityPanelProps = {
  trace: Record<string, unknown> | null;
  observability: Record<string, unknown> | null;
};

type LlmUsage = {
  id?: number;
  timestamp?: string;
  stage?: string;
  model?: string;
  input_tokens?: number;
  output_tokens?: number;
  total_tokens?: number;
  estimated_cost_usd?: number;
};

const valueText = (value: unknown) => {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }
  if (typeof value === "number") {
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  return String(value);
};

const statusTone = (value: unknown) => {
  const normalized = String(value ?? "").toLowerCase();
  if (["success", "pass", "healthy"].includes(normalized)) {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";
  }
  if (["warn", "warning"].includes(normalized)) {
    return "border-amber-500/30 bg-amber-500/10 text-amber-200";
  }
  if (["failed", "fail", "error"].includes(normalized)) {
    return "border-red-500/30 bg-red-500/10 text-red-200";
  }
  return "border-slate-700 bg-slate-800/70 text-slate-300";
};

export const ObservabilityPanel = ({ trace, observability }: ObservabilityPanelProps) => {
  const [liveEvents, setLiveEvents] = useState<Array<Record<string, unknown>>>([]);
  const [llmUsage, setLlmUsage] = useState<LlmUsage[]>([]);
  const stages = (observability?.stages as Array<Record<string, unknown>> | undefined) ?? [];
  const domain = (observability?.domain_metrics as Record<string, unknown> | undefined) ?? {};
  const records = (domain.records as Record<string, unknown> | undefined) ?? {};
  const stageReasoning = (trace?.stage_reasoning as Record<string, string[]> | undefined) ?? {};
  const errors = (trace?.errors as Array<Record<string, unknown>> | undefined) ?? [];
  const usageByAgent = aggregateLlmUsage(llmUsage);

  useEffect(() => {
    fetch("http://localhost:8000/api/observability/llm-usage?limit=100")
      .then((response) => response.json())
      .then((payload) => {
        const usage = Array.isArray(payload?.usage) ? payload.usage : [];
        setLlmUsage(usage);
      })
      .catch(() => {
        setLlmUsage([]);
      });
  }, [trace?.request_id]);

  useEffect(() => {
    const source = new EventSource("http://localhost:8000/api/observability/stream");
    source.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data) as Record<string, unknown>;
        setLiveEvents((current) => [parsed, ...current].slice(0, 20));
        if (parsed.type === "llm_usage") {
          setLlmUsage((current) => [parsed as LlmUsage, ...current].slice(0, 100));
        }
      } catch {
        // Ignore malformed stream payloads.
      }
    };
    source.onerror = () => {
      source.close();
    };
    return () => source.close();
  }, []);

  if (!trace && !observability) {
    return (
      <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
        <h2 className="text-base font-semibold text-cyan-300">Observability</h2>
        <p className="mt-3 text-sm text-slate-400">
          Run the pipeline to capture request timing, stage reasoning, and domain health checks.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <h2 className="text-base font-semibold text-cyan-300">Observability</h2>
          <p className="mt-3 text-sm text-slate-400">
            Request correlation, pipeline latency, stage timings, and enterprise data-quality signals.
          </p>
        </div>
        <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${statusTone(trace?.pipeline_status ?? observability?.status)}`}>
          {valueText(trace?.pipeline_status ?? observability?.status)}
        </span>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-4">
        <MetricCard label="Request ID" value={trace?.request_id ?? observability?.request_id} />
        <MetricCard label="Total Duration" value={`${valueText(trace?.total_duration_ms ?? observability?.duration_ms)} ms`} />
        <MetricCard label="Join Match" value={formatPercent(domain.join_key_match_rate)} />
        <MetricCard label="Authority Violations" value={domain.amount_authority_violations ?? 0} />
      </div>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <h3 className="text-sm font-semibold text-slate-100">Stage Timings</h3>
          <div className="mt-3 overflow-hidden rounded-xl border border-slate-800">
            <table className="w-full text-left text-sm">
              <tbody>
                {stages.map((stage) => (
                  <tr key={String(stage.stage)} className="border-b border-slate-800 last:border-b-0">
                    <td className="px-4 py-3 text-slate-300">{valueText(stage.stage)}</td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${statusTone(stage.status)}`}>
                        {valueText(stage.status)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-cyan-200">{valueText(stage.duration_ms)} ms</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <h3 className="text-sm font-semibold text-slate-100">Domain Checks</h3>
          <div className="mt-3 space-y-3">
            <CheckRow label="Amount authority" status={domain.amount_authority_status} detail={`${valueText(domain.amount_authority_violations ?? 0)} violation(s)`} />
            <CheckRow label="Join key match" status={domain.join_key_status} detail={formatPercent(domain.join_key_match_rate)} />
            <CheckRow label="LLM fallback" status={domain.llm_fallback ? "warn" : "pass"} detail={domain.llm_fallback ? "Fallback detected" : "No fallback detected"} />
            <CheckRow label="Records" status="pass" detail={`IBM ${valueText(records.ibm)} / Unisys ${valueText(records.unisys)} / Total ${valueText(records.normalized_total)}`} />
          </div>
        </div>
      </div>

      <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">LLM Token Usage By Agent</h3>
            <p className="mt-1 text-xs text-slate-500">
              Persisted from `/api/observability/llm-usage` and updated by live events.
            </p>
          </div>
          <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-200">
            {usageByAgent.length} agents
          </span>
        </div>
        <div className="mt-3 overflow-hidden rounded-xl border border-slate-800">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950/70 text-xs uppercase tracking-[0.14em] text-slate-500">
              <tr>
                <th className="px-4 py-3">Agent</th>
                <th className="px-4 py-3">Model</th>
                <th className="px-4 py-3 text-right">Input</th>
                <th className="px-4 py-3 text-right">Output</th>
                <th className="px-4 py-3 text-right">Total</th>
                <th className="px-4 py-3 text-right">Cost</th>
              </tr>
            </thead>
            <tbody>
              {usageByAgent.length ? (
                usageByAgent.map((usage) => (
                  <tr key={usage.stage} className="border-t border-slate-800">
                    <td className="px-4 py-3 font-mono text-cyan-200">{usage.stage}</td>
                    <td className="px-4 py-3 text-slate-300">{usage.models}</td>
                    <td className="px-4 py-3 text-right font-mono text-slate-100">{usage.input}</td>
                    <td className="px-4 py-3 text-right font-mono text-slate-100">{usage.output}</td>
                    <td className="px-4 py-3 text-right font-mono text-cyan-200">{usage.total}</td>
                    <td className="px-4 py-3 text-right font-mono text-emerald-200">${usage.cost.toFixed(6)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="px-4 py-4 text-sm text-slate-400">
                    No token usage captured yet. Run with LLM enabled and a Gemini API key configured.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
        <h3 className="text-sm font-semibold text-slate-100">Stage Reasoning</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          {Object.entries(stageReasoning).map(([stage, items]) => (
            <div key={stage} className="rounded-xl border border-slate-800 bg-slate-950/70 p-4">
              <p className="font-mono text-xs uppercase tracking-[0.14em] text-slate-500">{stage}</p>
              <ul className="mt-3 space-y-2 text-sm leading-6 text-slate-300">
                {items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      {errors.length ? (
        <div className="mt-5 rounded-2xl border border-red-500/20 bg-red-500/10 p-4">
          <h3 className="text-sm font-semibold text-red-100">Errors</h3>
          <div className="mt-3 space-y-2 text-sm text-red-100/80">
            {errors.map((error, index) => (
              <p key={index}>{valueText(error.stage)}: {valueText(error.message)}</p>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
        <div className="flex items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold text-slate-100">Live Event Stream</h3>
            <p className="mt-1 text-xs text-slate-500">
              Server-sent events from `/api/observability/stream`.
            </p>
          </div>
          <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs font-semibold text-cyan-200">
            {liveEvents.length} events
          </span>
        </div>
        <div className="mt-3 max-h-80 space-y-2 overflow-auto">
          {liveEvents.length ? (
            liveEvents.map((event, index) => (
              <div key={`${event.type}-${event.timestamp}-${index}`} className="rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-mono text-xs uppercase tracking-[0.14em] text-cyan-200">{valueText(event.type)}</span>
                  <span className="font-mono text-xs text-slate-500">{valueText(event.stage)}</span>
                  <span className="font-mono text-xs text-slate-500">{valueText(event.request_id)}</span>
                </div>
                <p className="mt-2 truncate font-mono text-xs text-slate-400">
                  {JSON.stringify(event)}
                </p>
              </div>
            ))
          ) : (
            <p className="rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3 text-sm text-slate-400">
              Waiting for live observability events.
            </p>
          )}
        </div>
      </div>
    </section>
  );
};

const MetricCard = ({ label, value }: { label: string; value: unknown }) => (
  <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{label}</p>
    <p className="mt-2 break-words font-mono text-sm font-semibold text-slate-100">{valueText(value)}</p>
  </div>
);

const CheckRow = ({ label, status, detail }: { label: string; status: unknown; detail: string }) => (
  <div className="flex items-center justify-between gap-4 rounded-xl border border-slate-800 bg-slate-950/70 px-4 py-3">
    <div>
      <p className="text-sm font-medium text-slate-100">{label}</p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </div>
    <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${statusTone(status)}`}>
      {valueText(status)}
    </span>
  </div>
);

const formatPercent = (value: unknown) => {
  if (typeof value === "number") {
    return `${Math.round(value * 100)}%`;
  }
  return "N/A";
};

const aggregateLlmUsage = (usage: LlmUsage[]) => {
  const grouped = new Map<
    string,
    {
      stage: string;
      models: Set<string>;
      input: number;
      output: number;
      total: number;
      cost: number;
    }
  >();

  usage.forEach((item) => {
    const stage = item.stage || "unknown";
    const current = grouped.get(stage) ?? {
      stage,
      models: new Set<string>(),
      input: 0,
      output: 0,
      total: 0,
      cost: 0,
    };
    if (item.model) {
      current.models.add(item.model);
    }
    current.input += Number(item.input_tokens || 0);
    current.output += Number(item.output_tokens || 0);
    current.total += Number(item.total_tokens || 0);
    current.cost += Number(item.estimated_cost_usd || 0);
    grouped.set(stage, current);
  });

  return Array.from(grouped.values())
    .map((item) => ({
      ...item,
      models: Array.from(item.models).join(", ") || "N/A",
    }))
    .sort((left, right) => right.total - left.total);
};
