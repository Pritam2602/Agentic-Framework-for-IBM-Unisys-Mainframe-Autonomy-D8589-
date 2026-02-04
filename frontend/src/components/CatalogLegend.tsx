export function CatalogLegend() {
  return (
    <section className="enterprise-card p-4">
      <h3 className="text-sm font-semibold mb-3">Legend</h3>
      <div className="flex flex-wrap gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-status-safe" />
          <span className="text-muted-foreground">READ — Safe, read-only operation</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-status-caution" />
          <span className="text-muted-foreground">EXECUTE — State-changing operation</span>
        </div>
        <div className="flex items-center gap-4 ml-auto">
          <span className="text-muted-foreground">Execution Cost:</span>
          <div className="flex items-center gap-1">
            <div className="flex items-end gap-0.5 h-3">
              <div className="w-1 h-1 bg-cost-low rounded-sm" />
              <div className="w-1 h-2 bg-muted rounded-sm" />
              <div className="w-1 h-3 bg-muted rounded-sm" />
            </div>
            <span className="text-xs">Low</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="flex items-end gap-0.5 h-3">
              <div className="w-1 h-1 bg-cost-medium rounded-sm" />
              <div className="w-1 h-2 bg-cost-medium rounded-sm" />
              <div className="w-1 h-3 bg-muted rounded-sm" />
            </div>
            <span className="text-xs">Medium</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="flex items-end gap-0.5 h-3">
              <div className="w-1 h-1 bg-cost-high rounded-sm" />
              <div className="w-1 h-2 bg-cost-high rounded-sm" />
              <div className="w-1 h-3 bg-cost-high rounded-sm" />
            </div>
            <span className="text-xs">High</span>
          </div>
        </div>
      </div>
    </section>
  );
}
