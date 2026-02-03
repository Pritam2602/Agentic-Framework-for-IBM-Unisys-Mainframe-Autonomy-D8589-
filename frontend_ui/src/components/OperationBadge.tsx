import { cn } from "@/lib/utils";
import { Operation } from "@/types/catalog";
import { Shield, Zap } from "lucide-react";

interface OperationBadgeProps {
  operation: Operation;
  className?: string;
}

export function OperationBadge({ operation, className }: OperationBadgeProps) {
  const isRead = operation === "READ";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors",
        isRead
          ? "bg-status-safe-bg text-status-safe-foreground"
          : "bg-status-caution-bg text-status-caution-foreground",
        className
      )}
    >
      {isRead ? (
        <Shield className="h-3 w-3" />
      ) : (
        <Zap className="h-3 w-3" />
      )}
      {operation}
    </span>
  );
}
