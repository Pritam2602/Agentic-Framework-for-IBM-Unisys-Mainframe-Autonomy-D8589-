import { FormEvent, useEffect, useState } from "react";
import {
  ArrowPathIcon,
  BoltIcon,
  CircleStackIcon,
  CommandLineIcon,
  CpuChipIcon,
  ExclamationTriangleIcon,
  MagnifyingGlassCircleIcon,
  ServerStackIcon,
} from "@heroicons/react/24/outline";
import Layout from "../components/common/Layout";
import { runPipeline, fetchPipelineHealth, fetchContextHealth, fetchCommandsCatalog } from "@/services/api";
import { PipelineVisualization, IntentPanel, ContextPanel, PlannerPanel, ReasoningPanel } from "@/components/pipeline";
import { useAppStore, appStore, type ControlCenterPanel } from "@/store/useAppStore";
import { cn } from "@/lib/utils";

const panelNav: Array<{
  id: ControlCenterPanel;
  label: string;
  icon: typeof BoltIcon;
  description: string;
}> = [
  { id: "execution", label: "Execution", icon: BoltIcon, description: "Run the pipeline and review the workflow summary." },
  { id: "intent", label: "Intent", icon: CommandLineIcon, description: "See what the system understood from the request." },
  { id: "context", label: "Context", icon: CircleStackIcon, description: "Inspect where data exists across systems." },
  { id: "reasoning", label: "Reasoning", icon: MagnifyingGlassCircleIcon, description: "Review AI decision logic and warnings." },
  { id: "planner", label: "Planner", icon: CpuChipIcon, description: "Preview the downstream execution handoff." },
  { id: "normalization", label: "Normalization", icon: CircleStackIcon, description: "Review canonical records produced after execution." },
  { id: "federation", label: "Federation", icon: MagnifyingGlassCircleIcon, description: "Inspect federated view recommendations and output." },
  { id: "zoweCatalog", label: "Zowe Catalog", icon: ServerStackIcon, description: "Browse the command catalog loaded from the backend database." },
];

const systemPillClass = (online: boolean) =>
  online
    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
    : "border-amber-500/30 bg-amber-500/10 text-amber-200";

const validationTone = (status: "pass" | "warn" | "fail") =>
  status === "pass"
    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
    : status === "warn"
      ? "border-amber-500/30 bg-amber-500/10 text-amber-200"
      : "border-red-500/30 bg-red-500/10 text-red-200";

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

const smallStatClass = "rounded-2xl border border-slate-800 bg-slate-900/70 p-4";

const MiniStat = ({ label, value, tone = "slate" }: { label: string; value: unknown; tone?: "slate" | "emerald" | "cyan" | "violet" | "amber" }) => {
  const toneClass =
    tone === "emerald"
      ? "text-emerald-200"
      : tone === "cyan"
        ? "text-cyan-200"
        : tone === "violet"
          ? "text-violet-200"
          : tone === "amber"
            ? "text-amber-200"
            : "text-slate-100";

  return (
    <div className={smallStatClass}>
      <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{label}</p>
      <p className={`mt-2 text-lg font-semibold ${toneClass}`}>{valueText(value)}</p>
    </div>
  );
};

const KeyValueTable = ({ rows }: { rows: Array<[string, unknown]> }) => (
  <div className="overflow-hidden rounded-2xl border border-slate-800">
    <table className="w-full text-left text-sm">
      <tbody>
        {rows.map(([label, value]) => (
          <tr key={label} className="border-b border-slate-800 last:border-b-0">
            <th className="w-1/2 bg-slate-900/70 px-4 py-3 font-medium text-slate-400">{label}</th>
            <td className="px-4 py-3 font-mono text-slate-100">{valueText(value)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </div>
);

const ObjectAmountTable = ({ title, values }: { title: string; values?: Record<string, unknown> }) => {
  const entries = Object.entries(values ?? {});
  if (!entries.length) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
      <h3 className="text-sm font-semibold text-slate-100">{title}</h3>
      <div className="mt-3 overflow-hidden rounded-xl border border-slate-800">
        <table className="w-full text-left text-sm">
          <tbody>
            {entries.map(([key, value]) => (
              <tr key={key} className="border-b border-slate-800 last:border-b-0">
                <td className="px-4 py-2 text-slate-300">{key}</td>
                <td className="px-4 py-2 text-right font-mono text-cyan-200">{valueText(value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const DiscoveryTable = ({
  items,
}: {
  items: Array<{
    entity?: string;
    status?: string;
    discovery_type?: string;
    confidence?: number;
    source?: string;
    relationship?: string;
    reason?: string;
  }>;
}) => {
  if (!items.length) {
    return null;
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-900/80 text-xs uppercase tracking-[0.16em] text-slate-500">
          <tr>
            <th className="px-4 py-3">Entity</th>
            <th className="px-4 py-3">Type</th>
            <th className="px-4 py-3">Confidence</th>
            <th className="px-4 py-3">Source</th>
            <th className="px-4 py-3">Relationship</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={`${item.entity}-${item.discovery_type}`} className="border-t border-slate-800 align-top">
              <td className="px-4 py-3 font-semibold text-slate-100">{valueText(item.entity)}</td>
              <td className="px-4 py-3">
                <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${pillTone(item.discovery_type)}`}>
                  {valueText(item.discovery_type)}
                </span>
              </td>
              <td className="px-4 py-3 font-mono text-cyan-200">
                {typeof item.confidence === "number" ? `${Math.round(item.confidence * 100)}%` : "N/A"}
              </td>
              <td className="px-4 py-3 text-slate-300">{valueText(item.source)}</td>
              <td className="px-4 py-3 text-slate-300">
                <p>{valueText(item.relationship)}</p>
                {item.reason ? <p className="mt-1 text-xs leading-5 text-slate-500">{item.reason}</p> : null}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const SuggestedExplorations = ({
  items,
}: {
  items: Array<{
    id?: string;
    title?: string;
    prompt?: string;
    reason?: string;
    relationship?: string;
    confidence?: number;
  }>;
}) => {
  if (!items.length) {
    return null;
  }

  const handleSuggestion = (prompt?: string) => {
    if (!prompt) {
      return;
    }
    const store = appStore.getState();
    store.setQuery(prompt);
    store.setActivePanel("execution");
  };

  return (
    <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/5 p-4">
      <div className="mb-4">
        <h3 className="text-sm font-semibold text-cyan-100">Suggested Next Actions</h3>
        <p className="mt-1 text-xs leading-5 text-slate-400">
          AI-guided follow-up prompts based on the current entities, schema relationships, and federation context.
        </p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        {items.map((item) => (
          <button
            key={item.id ?? item.title}
            type="button"
            onClick={() => handleSuggestion(item.prompt)}
            className="rounded-2xl border border-slate-800 bg-slate-950/80 p-4 text-left transition hover:border-cyan-500/40 hover:bg-cyan-500/10"
          >
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm font-semibold text-slate-100">{valueText(item.title)}</p>
              <span className="shrink-0 font-mono text-xs text-cyan-200">
                {typeof item.confidence === "number" ? `${Math.round(item.confidence * 100)}%` : ""}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5 text-slate-400">{valueText(item.reason)}</p>
            {item.relationship ? (
              <p className="mt-3 font-mono text-[11px] text-slate-500">{item.relationship}</p>
            ) : null}
          </button>
        ))}
      </div>
    </div>
  );
};

type ZoweCatalogCommand = {
  id: string;
  zowe_command?: string;
  category?: string;
  command_family?: string;
  subsystem?: string;
  ibm_artifact?: string;
  operation?: string;
  access_pattern?: string | null;
  response_format?: string | null;
  intended_agent?: string | null;
  constraints?: string | null;
  execution_cost?: string;
  confidence_level?: number | string | null;
};

const pillTone = (value?: string | null) => {
  const normalized = String(value ?? "").toLowerCase();
  if (normalized === "exact_match") {
    return "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";
  }
  if (normalized === "related_capability") {
    return "border-cyan-500/30 bg-cyan-500/10 text-cyan-200";
  }
  if (normalized === "inferred") {
    return "border-amber-500/30 bg-amber-500/10 text-amber-200";
  }
  if (normalized === "weak_signal") {
    return "border-red-500/30 bg-red-500/10 text-red-200";
  }
  if (["read", "low", "high"].includes(normalized)) {
    return normalized === "high"
      ? "border-red-500/30 bg-red-500/10 text-red-200"
      : normalized === "low"
        ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200"
        : "border-cyan-500/30 bg-cyan-500/10 text-cyan-200";
  }
  if (["execute", "medium"].includes(normalized)) {
    return "border-amber-500/30 bg-amber-500/10 text-amber-200";
  }
  return "border-slate-700 bg-slate-800/70 text-slate-300";
};

const ZoweCatalogPanel = () => {
  const [commands, setCommands] = useState<ZoweCatalogCommand[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    let cancelled = false;
    const loadCommands = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchCommandsCatalog();
        if (!cancelled) {
          setCommands(data as unknown as ZoweCatalogCommand[]);
        }
      } catch (catalogError) {
        if (!cancelled) {
          setError(catalogError instanceof Error ? catalogError.message : "Failed to load command catalog");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadCommands();
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = commands.filter((command) => {
    const text = [
      command.id,
      command.zowe_command,
      command.command_family,
      command.subsystem,
      command.ibm_artifact,
      command.operation,
      command.constraints,
    ].join(" ").toLowerCase();
    return text.includes(search.toLowerCase());
  });

  const families = new Set(commands.map((command) => command.command_family).filter(Boolean)).size;
  const lowRisk = commands.filter((command) => command.execution_cost === "LOW").length;
  const readOps = commands.filter((command) => command.operation === "READ").length;

  return (
    <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h2 className="text-base font-semibold text-cyan-300">Zowe Command Catalog</h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-400">
            Command metadata is loaded from the backend catalog database through <span className="font-mono text-slate-200">/api/catalog/commands</span>.
          </p>
        </div>
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search commands"
          className="h-11 w-full rounded-2xl border border-slate-800 bg-slate-900/70 px-4 text-sm text-slate-100 outline-none transition focus:border-cyan-500/40 focus:ring-2 focus:ring-cyan-500/20 lg:w-72"
        />
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-4">
        <MiniStat label="Commands" value={commands.length} tone="cyan" />
        <MiniStat label="Families" value={families} tone="violet" />
        <MiniStat label="Read Ops" value={readOps} tone="emerald" />
        <MiniStat label="Low Cost" value={lowRisk} tone="amber" />
      </div>

      {loading ? (
        <div className="mt-5 rounded-2xl border border-slate-800 bg-slate-900/70 p-6 text-sm text-slate-300">
          Loading command catalog...
        </div>
      ) : error ? (
        <div className="mt-5 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100">
          {error}
        </div>
      ) : (
        <div className="mt-5 overflow-hidden rounded-2xl border border-slate-800">
          <div className="max-h-[620px] overflow-auto">
            <table className="w-full min-w-[980px] text-left text-sm">
              <thead className="sticky top-0 bg-slate-900 text-xs uppercase tracking-[0.16em] text-slate-500">
                <tr>
                  <th className="px-4 py-3">Command</th>
                  <th className="px-4 py-3">Family</th>
                  <th className="px-4 py-3">Subsystem</th>
                  <th className="px-4 py-3">Operation</th>
                  <th className="px-4 py-3">Artifact</th>
                  <th className="px-4 py-3">Cost</th>
                  <th className="px-4 py-3">Confidence</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((command) => (
                  <tr key={command.id} className="border-t border-slate-800 bg-slate-950/60 align-top">
                    <td className="max-w-[360px] px-4 py-4">
                      <p className="font-mono text-sm leading-6 text-cyan-100">{command.zowe_command}</p>
                      {command.constraints ? (
                        <p className="mt-2 text-xs leading-5 text-slate-500">{command.constraints}</p>
                      ) : null}
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${pillTone(command.command_family)}`}>
                        {valueText(command.command_family)}
                      </span>
                    </td>
                    <td className="px-4 py-4 font-mono text-slate-300">{valueText(command.subsystem)}</td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${pillTone(command.operation)}`}>
                        {valueText(command.operation)}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-slate-300">{valueText(command.ibm_artifact)}</td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${pillTone(command.execution_cost)}`}>
                        {valueText(command.execution_cost)}
                      </span>
                    </td>
                    <td className="px-4 py-4 font-mono text-slate-100">
                      {typeof command.confidence_level === "number"
                        ? `${Math.round(command.confidence_level * 100)}%`
                        : valueText(command.confidence_level)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!filtered.length ? (
            <div className="border-t border-slate-800 bg-slate-950 p-6 text-sm text-slate-400">
              No catalog commands match the current search.
            </div>
          ) : null}
        </div>
      )}
    </section>
  );
};

const renderPanel = (panel: ControlCenterPanel) => {
  const store = appStore.getState();

  if (panel === "intent") {
    return <IntentPanel intent={store.intent} loading={store.loading && !store.intent} />;
  }

  if (panel === "context") {
    return <ContextPanel context={store.context} loading={store.loading && !!store.intent && !store.context} />;
  }

  if (panel === "reasoning") {
    return <ReasoningPanel reasoning={store.reasoning} warnings={store.warnings} />;
  }

  if (panel === "planner") {
    return <PlannerPanel intent={store.intent} context={store.context} planner={store.planner} nextStage={store.nextStage} />;
  }

  if (panel === "zoweCatalog") {
    return <ZoweCatalogPanel />;
  }

  if (panel === "normalization") {
    const normalization = store.normalization as {
      summary?: {
        total_records?: number;
        ibm_records?: number;
        unisys_records?: number;
        canonical_entities?: string[];
        warnings?: string[];
      };
      records?: Array<{
        source_system?: string;
        entity?: string;
        customer_id?: string;
        amount?: number;
        date?: string;
        merchant?: string | null;
        category?: string | null;
        enrichment?: Record<string, unknown>;
      }>;
    } | null;
    const total = normalization?.summary?.total_records;
    return (
      <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
        <h2 className="text-base font-semibold text-emerald-300">Normalization</h2>
        <p className="mt-3 text-sm text-slate-400">
          {normalization
            ? `${total ?? 0} canonical record(s) were produced for federation.`
            : "Run the pipeline to see normalized execution outputs."}
        </p>
        {normalization && (
          <div className="mt-5 space-y-5">
            <div className="grid gap-4 md:grid-cols-3">
              <MiniStat label="Total Records" value={normalization.summary?.total_records} tone="emerald" />
              <MiniStat label="IBM Records" value={normalization.summary?.ibm_records} tone="cyan" />
              <MiniStat label="Unisys Records" value={normalization.summary?.unisys_records} tone="violet" />
            </div>

            <KeyValueTable
              rows={[
                ["Canonical entities", normalization.summary?.canonical_entities?.join(", ")],
                ["Warnings", normalization.summary?.warnings?.join("; ") || "None"],
              ]}
            />

            {normalization.records?.length ? (
              <div className="overflow-hidden rounded-2xl border border-slate-800">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-900/80 text-xs uppercase tracking-[0.16em] text-slate-500">
                    <tr>
                      <th className="px-4 py-3">Source</th>
                      <th className="px-4 py-3">Entity</th>
                      <th className="px-4 py-3">Customer</th>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3">Amount</th>
                      <th className="px-4 py-3">Context</th>
                    </tr>
                  </thead>
                  <tbody>
                    {normalization.records.map((record, index) => (
                      <tr key={`${record.source_system}-${record.entity}-${index}`} className="border-t border-slate-800">
                        <td className="px-4 py-3 text-slate-100">{valueText(record.source_system).toUpperCase()}</td>
                        <td className="px-4 py-3 text-slate-300">{valueText(record.entity)}</td>
                        <td className="px-4 py-3 font-mono text-slate-300">{valueText(record.customer_id)}</td>
                        <td className="px-4 py-3 font-mono text-slate-300">{valueText(record.date)}</td>
                        <td className="px-4 py-3 font-mono text-cyan-200">{valueText(record.amount)}</td>
                        <td className="px-4 py-3 text-slate-300">
                          {record.entity === "inventory"
                            ? [
                                record.enrichment?.sku,
                                record.enrichment?.availabilityStatus,
                                record.enrichment?.stockQuantity !== undefined
                                  ? `stock ${record.enrichment?.stockQuantity}`
                                  : null,
                              ].filter(Boolean).join(" / ")
                            : record.merchant || record.category
                              ? [record.merchant, record.category].filter(Boolean).join(" / ")
                              : "financial record"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : null}
          </div>
        )}
      </section>
    );
  }

  if (panel === "federation") {
    const federation = store.federation as {
      top_view?: { name?: string; view_id?: string };
      federated_result?: {
        federation?: Record<string, unknown>;
        behavioral_enrichment?: {
          merchant_observed_amounts?: Record<string, unknown>;
          category_observed_amounts?: Record<string, unknown>;
          loyalty?: { total_loyalty_points?: number };
          cart_status_breakdown?: Record<string, unknown>;
          browsing?: { total_browsing_minutes?: number };
        };
        reconciliation?: Record<string, unknown>;
      };
      governance?: Record<string, unknown>;
      capability_discovery?: {
        related_capabilities?: Array<{
          entity?: string;
          status?: string;
          discovery_type?: string;
          confidence?: number;
          source?: string;
          relationship?: string;
          reason?: string;
        }>;
        discovery_notes?: string[];
      };
      suggested_explorations?: Array<{
        id?: string;
        title?: string;
        prompt?: string;
        reason?: string;
        relationship?: string;
        confidence?: number;
      }>;
      overall_confidence?: number;
      reasoning?: string;
    } | null;
    const topView = federation?.top_view;
    const result = federation?.federated_result;
    const fedMetrics = result?.federation;
    const enrichment = result?.behavioral_enrichment;
    const reconciliation = result?.reconciliation ?? federation?.governance?.amount_reconciliation as Record<string, unknown> | undefined;
    const discoveryItems = federation?.capability_discovery?.related_capabilities ?? [];
    return (
      <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
        <h2 className="text-base font-semibold text-violet-300">Federation Intelligence</h2>
        <p className="mt-3 text-sm text-slate-400">
          {federation
            ? `Top view: ${topView?.name ?? topView?.view_id ?? "N/A"}`
            : "Run the pipeline to see federated view recommendations."}
        </p>
        {federation && (
          <div className="mt-5 space-y-5">
            <div className="grid gap-4 md:grid-cols-4">
              <MiniStat label="Total Spend" value={fedMetrics?.total_spend} tone="emerald" />
              <MiniStat label="IBM Txns" value={fedMetrics?.ibm_transaction_count} tone="cyan" />
              <MiniStat label="Unisys Events" value={fedMetrics?.unisys_enrichment_count} tone="violet" />
              <MiniStat label="Confidence" value={`${Math.round((federation.overall_confidence ?? 0) * 100)}%`} tone="amber" />
            </div>

            <KeyValueTable
              rows={[
                ["Top view", topView?.name ?? topView?.view_id],
                ["View ID", topView?.view_id],
                ["IBM authoritative total", reconciliation?.ibm_authoritative_total],
                ["Unisys observed total", reconciliation?.unisys_observed_total],
                ["Variance", reconciliation?.variance],
                ["Reconciliation", reconciliation?.status],
                ["Double-counting protected", federation.governance?.double_counting_protected],
                ["LLM refinement", federation.governance?.llm_refinement],
              ]}
            />

            <SuggestedExplorations items={federation.suggested_explorations ?? []} />

            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <div className="mb-3">
                <h3 className="text-sm font-semibold text-slate-100">Supporting Discovery Metadata</h3>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  Grounding signals behind the suggested next actions. These are not automatically added to the current answer.
                </p>
              </div>
              <DiscoveryTable items={discoveryItems} />
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <ObjectAmountTable title="Merchant Observed Amounts" values={enrichment?.merchant_observed_amounts} />
              <ObjectAmountTable title="Category Observed Amounts" values={enrichment?.category_observed_amounts} />
              <ObjectAmountTable title="Cart Status Breakdown" values={enrichment?.cart_status_breakdown} />
              <KeyValueTable
                rows={[
                  ["Total loyalty points", enrichment?.loyalty?.total_loyalty_points],
                  ["Total browsing minutes", enrichment?.browsing?.total_browsing_minutes],
                ]}
              />
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Reasoning</p>
              <p className="mt-2 text-sm leading-7 text-slate-300">{federation.reasoning}</p>
            </div>
          </div>
        )}
      </section>
    );
  }

  return null;
};

export default function ExecutionPage() {
  const query = useAppStore((state) => state.query);
  const activePanel = useAppStore((state) => state.activePanel);
  const pipelineStage = useAppStore((state) => state.pipelineStage);
  const summary = useAppStore((state) => state.summary);
  const nextStage = useAppStore((state) => state.nextStage);
  const intent = useAppStore((state) => state.intent);
  const context = useAppStore((state) => state.context);
  const execution = useAppStore((state) => state.execution);
  const normalization = useAppStore((state) => state.normalization);
  const federation = useAppStore((state) => state.federation);
  const reasoning = useAppStore((state) => state.reasoning);
  const warnings = useAppStore((state) => state.warnings);
  const validation = useAppStore((state) => state.validation);
  const loading = useAppStore((state) => state.loading);
  const error = useAppStore((state) => state.error);
  const health = useAppStore((state) => state.health);
  const resultReady = useAppStore((state) => state.resultReady);
  const setQuery = useAppStore((state) => state.setQuery);
  const setActivePanel = useAppStore((state) => state.setActivePanel);
  const setLoading = useAppStore((state) => state.setLoading);
  const setError = useAppStore((state) => state.setError);
  const setHealth = useAppStore((state) => state.setHealth);
  const resetRunState = useAppStore((state) => state.resetRunState);
  const applyPipelineResponse = useAppStore((state) => state.applyPipelineResponse);

  useEffect(() => {
    let cancelled = false;

    const loadHealth = async () => {
      try {
        const [pipelineHealth, contextHealth] = await Promise.all([
          fetchPipelineHealth(),
          fetchContextHealth(),
        ]);

        if (cancelled) {
          return;
        }

        setHealth({
          pipelineOnline: pipelineHealth.status === "healthy",
          contextOnline: contextHealth.status === "healthy",
          eportalAvailable: Boolean(contextHealth.unisys?.eportal_available),
        });
      } catch {
        if (!cancelled) {
          setHealth({
            pipelineOnline: false,
            contextOnline: false,
            eportalAvailable: false,
          });
        }
      }
    };

    loadHealth();
    return () => {
      cancelled = true;
    };
  }, [setHealth]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim() || loading) {
      return;
    }

    resetRunState();
    setLoading(true);
    setError(null);

    try {
      const response = await runPipeline(query);
      applyPipelineResponse(response);
    } catch (submissionError) {
      setLoading(false);
      setError(submissionError instanceof Error ? submissionError.message : "Failed to run pipeline");
    }
  };

  return (
    <Layout
      title="AI Data Federation Control Center"
      subtitle="Transparent orchestration across intent, context, planning, and validation"
    >
      <div className="space-y-6">
        <section className="overflow-hidden rounded-3xl border border-slate-800 bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.12),_transparent_34%),linear-gradient(135deg,_rgba(15,23,42,0.98),_rgba(2,6,23,0.96))]">
          <div className="p-7 xl:p-8">
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(420px,0.65fr)] xl:items-start">
              <div className="space-y-4">
                <p className="text-xs uppercase tracking-[0.32em] text-slate-500">System Awareness</p>
                <h2 className="max-w-3xl text-3xl font-semibold leading-tight text-slate-50 xl:text-[2.55rem]">
                  AI orchestration dashboard for enterprise federation
                </h2>
                <p className="max-w-3xl text-base leading-8 text-slate-400">
                  Inspect what the system understood, where it found the data, why it made each decision, and what stage is ready next.
                </p>
                <div className="flex flex-wrap gap-3">
                  <span className="rounded-full border border-cyan-500/20 bg-cyan-500/8 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-100/90">
                    Explainability First
                  </span>
                  <span className="rounded-full border border-violet-500/20 bg-violet-500/8 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-violet-100/90">
                    Federation Aware
                  </span>
                  <span className="rounded-full border border-emerald-500/20 bg-emerald-500/8 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-100/90">
                    Validation Layer
                  </span>
                </div>
              </div>

              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Workflow</p>
                  <p className="mt-3 font-mono text-lg text-slate-100">
                    {resultReady ? `wf-${Date.now().toString().slice(-6)}` : "pending"}
                  </p>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Pipeline</p>
                  <span className={`mt-3 inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${systemPillClass(health.pipelineOnline)}`}>
                    {health.pipelineOnline ? "ONLINE" : "OFFLINE"}
                  </span>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Context Service</p>
                  <span className={`mt-3 inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${systemPillClass(health.contextOnline)}`}>
                    {health.contextOnline ? "READY" : "DOWN"}
                  </span>
                </div>
                <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                  <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Unisys ePortal</p>
                  <span className={`mt-3 inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${systemPillClass(health.eportalAvailable)}`}>
                    {health.eportalAvailable ? "CONNECTED" : "FALLBACK"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
          <div className="space-y-6">
            <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
              <div className="pb-4">
                <h2 className="text-base font-semibold text-slate-100">Panels</h2>
              </div>
              <div className="space-y-2">
                {panelNav.map((panel) => (
                  <button
                    key={panel.id}
                    onClick={() => setActivePanel(panel.id)}
                    className={cn(
                      "w-full rounded-2xl border px-4 py-4 text-left transition-all",
                      activePanel === panel.id
                        ? "border-cyan-500/40 bg-cyan-500/10 shadow-[0_0_22px_rgba(34,211,238,0.12)]"
                        : "border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900"
                    )}
                  >
                    <div className="flex items-start gap-3">
                      <panel.icon className="mt-0.5 h-5 w-5 text-cyan-300" />
                      <div>
                        <p className="text-sm font-semibold text-slate-100">{panel.label}</p>
                        <p className="mt-1 text-sm leading-6 text-slate-400">{panel.description}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </section>

            <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
              <div className="pb-4">
                <h2 className="text-base font-semibold text-slate-100">Trust Snapshot</h2>
              </div>
              <div className="space-y-4">
                {validation ? (
                  <>
                    <div className="grid grid-cols-3 gap-3">
                      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                        <p className="text-2xl font-semibold text-emerald-200">{validation.summary.pass}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">Pass</p>
                      </div>
                      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                        <p className="text-2xl font-semibold text-amber-200">{validation.summary.warn}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">Warn</p>
                      </div>
                      <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                        <p className="text-2xl font-semibold text-red-200">{validation.summary.fail}</p>
                        <p className="mt-1 text-xs uppercase tracking-[0.18em] text-slate-500">Fail</p>
                      </div>
                    </div>

                    {(["p0", "p1", "p2"] as const).map((tier) => (
                      <div key={tier} className="rounded-2xl border border-slate-800 bg-slate-900/70 p-5">
                        <div className="flex items-start justify-between gap-4">
                          <div>
                            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{validation[tier].title}</p>
                            <p className="mt-2 text-sm font-semibold text-slate-100">
                              {validation[tier].description}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-semibold text-slate-100">
                              {Math.round(validation[tier].score * 100)}%
                            </p>
                            <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">score</p>
                          </div>
                        </div>

                        <div className="mt-4 space-y-4">
                          {validation[tier].items.map((item) => (
                            <div key={item.label} className="flex items-start justify-between gap-3">
                              <div>
                                <p className="text-sm font-medium text-slate-100">{item.label}</p>
                                <p className="text-xs leading-5 text-slate-400">{item.detail}</p>
                              </div>
                              <span
                                className={cn(
                                  "inline-flex rounded-full border px-3 py-1 text-xs font-semibold",
                                  validationTone(item.status)
                                )}
                              >
                                {item.status.toUpperCase()}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </>
                ) : (
                  <p className="text-sm text-slate-400">Validation metrics will populate after a pipeline run.</p>
                )}
              </div>
            </section>
          </div>

          <div className="space-y-6">
            <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
              <div className="pb-4">
                <h2 className="text-base font-semibold text-slate-100">Execution Panel</h2>
              </div>
              <div className="space-y-4">
                <form onSubmit={handleSubmit} className="space-y-4">
                  <textarea
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="Show me shopping data for customer 101 on 2026-03-10"
                    className="min-h-[132px] w-full rounded-3xl border border-slate-800 bg-slate-900/70 px-5 py-4 text-sm text-slate-100 outline-none transition focus:border-cyan-500/40 focus:ring-2 focus:ring-cyan-500/20"
                  />
                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      type="submit"
                      disabled={!query.trim() || loading}
                      className="inline-flex items-center gap-2 rounded-full border border-cyan-500/40 bg-cyan-500/15 px-6 py-3.5 text-sm font-semibold text-cyan-100 shadow-[0_0_18px_rgba(34,211,238,0.12)] transition hover:bg-cyan-500/25 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      {loading ? <ArrowPathIcon className="h-4 w-4 animate-spin" /> : <BoltIcon className="h-4 w-4" />}
                      Run Pipeline
                    </button>
                    {resultReady && (
                      <button
                        type="button"
                        onClick={() => setActivePanel("context")}
                        className="inline-flex items-center gap-2 rounded-full border border-violet-500/20 bg-transparent px-5 py-3 text-sm font-semibold text-violet-100 transition hover:bg-violet-500/12"
                      >
                        View Resolved Context
                      </button>
                    )}
                  </div>
                </form>

                {error && (
                  <div className="rounded-2xl border border-red-500/20 bg-red-500/10 p-4">
                    <div className="flex items-start gap-3">
                      <ExclamationTriangleIcon className="mt-0.5 h-5 w-5 text-red-300" />
                      <p className="text-sm leading-6 text-red-100">{error}</p>
                    </div>
                  </div>
                )}

                <div className="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(320px,0.85fr)]">
                  <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">System Response Summary</p>
                    {summary ? (
                      <div className="mt-4 space-y-4">
                        <div className="rounded-2xl border border-slate-800 bg-slate-950/60 p-4">
                          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Mission Digest</p>
                          <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-200">{summary}</p>
                        </div>
                        {reasoning?.semanticGaps.length ? (
                          <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4">
                            <p className="text-xs uppercase tracking-[0.18em] text-amber-200/80">Interpretation Gap</p>
                            <p className="mt-3 text-sm leading-6 text-slate-200">
                              {reasoning.semanticGaps[0]}
                            </p>
                          </div>
                        ) : null}
                      </div>
                    ) : (
                      <p className="mt-3 whitespace-pre-line text-sm leading-7 text-slate-200">
                        Submit a natural-language request to see the pipeline transform it into structured intent and resolved context.
                      </p>
                    )}
                  </div>

                  <div className="rounded-3xl border border-slate-800 bg-slate-900/70 p-6">
                    <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Live Snapshot</p>
                    <div className="mt-4 space-y-4 text-sm">
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Intent</span>
                        <span className="text-slate-100">{intent ? `${Math.round(intent.confidence_score * 100)}%` : "pending"}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Context</span>
                        <span className="text-slate-100">
                          {context ? `${Math.round(context.resolution_confidence * 100)}%` : "pending"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Reasoning Notes</span>
                        <span className="text-slate-100">{reasoning?.decisions.length ?? 0}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Execution</span>
                        <span className="text-slate-100">{(execution as { status?: string } | null)?.status ?? "pending"}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Normalized Records</span>
                        <span className="text-slate-100">
                          {(normalization as { summary?: { total_records?: number } } | null)?.summary?.total_records ?? "pending"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Federated View</span>
                        <span className="text-slate-100">
                          {(federation as { top_view?: { view_id?: string } } | null)?.top_view?.view_id ?? "pending"}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Warnings</span>
                        <span className="text-slate-100">{warnings.length}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-slate-400">Next Stage</span>
                        <span className="font-mono text-xs text-cyan-200">{nextStage ?? "n/a"}</span>
                      </div>
                      <div className="border-t border-slate-800 pt-4">
                        <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Current Objective</p>
                        <p className="mt-2 text-sm leading-6 text-slate-200">
                          {reasoning?.objective ?? "No pipeline objective yet."}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            <PipelineVisualization pipelineStage={pipelineStage} loading={loading} nextStage={nextStage} />

            {activePanel !== "execution" ? (
              renderPanel(activePanel)
            ) : (
              <section className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6">
                <div className="pb-4">
                  <h2 className="text-base font-semibold text-slate-100">Execution Overview</h2>
                </div>
                <div className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Question Asked</p>
                      <p className="mt-2 text-sm leading-6 text-slate-200">{query || "No query entered yet."}</p>
                    </div>
                    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-slate-500">What the system understood</p>
                      <p className="mt-2 text-sm leading-6 text-slate-200">
                        {intent
                          ? `${intent.task} on ${intent.entities.join(", ")} across ${intent.systems.join(", ")}.`
                          : "Intent extraction has not run yet."}
                      </p>
                    </div>
                    <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
                      <p className="text-xs uppercase tracking-[0.18em] text-slate-500">How to proceed</p>
                      <p className="mt-2 text-sm leading-6 text-slate-200">
                        {resultReady
                          ? "Use the Intent, Context, and Reasoning panels to inspect the pipeline before planner execution."
                          : "Run the pipeline, then inspect each panel to understand the system decision path."}
                      </p>
                    </div>
                  </div>
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
