import { cn } from "@/lib/utils";
import { ExecutionCost } from "@/types/catalog";

interface ExecutionCostIndicatorProps {
  cost: ExecutionCost;
  showLabel?: boolean;
  className?: string;
}

export function ExecutionCostIndicator({ cost, showLabel = true, className }: ExecutionCostIndicatorProps) {
  const bars = cost === "LOW" ? 1 : cost === "MEDIUM" ? 2 : 3;

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="flex items-end gap-0.5 h-4">
        {[1, 2, 3].map((level) => (
          <div
            key={level}
            className={cn(
              "w-1.5 rounded-sm transition-colors",
              level <= bars
                ? cost === "LOW"
                  ? "bg-cost-low"
                  : cost === "MEDIUM"
                  ? "bg-cost-medium"
                  : "bg-cost-high"
                : "bg-muted",
              level === 1 && "h-1.5",
              level === 2 && "h-2.5",
              level === 3 && "h-4"
            )}
          />
        ))}
      </div>
      {showLabel && (
        <span
          className={cn(
            "text-xs font-medium",
            cost === "LOW" && "text-cost-low",
            cost === "MEDIUM" && "text-cost-medium",
            cost === "HIGH" && "text-cost-high"
          )}
        >
          {cost}
        </span>
      )}
    </div>
  );
}
