import { cn } from "@/lib/utils";
import { AgentType } from "@/types/catalog";
import { Search, Wrench, Settings, Eye, FileCheck, HelpCircle } from "lucide-react";

interface AgentBadgeProps {
  agent?: AgentType | string;
  className?: string;
}

const agentConfig: Record<string, { icon: React.ElementType; label: string }> = {
  DiscoveryAgent: { icon: Search, label: "Discovery" },
  InfraAgent: { icon: Wrench, label: "Infrastructure" },
  ControlAgent: { icon: Settings, label: "Control" },
  MonitorAgent: { icon: Eye, label: "Monitor" },
  ComplianceAgent: { icon: FileCheck, label: "Compliance" },
};

export function AgentBadge({ agent, className }: AgentBadgeProps) {
  const config = agent ? agentConfig[agent] : null;
  const Icon = config?.icon ?? HelpCircle;
  const label = config?.label ?? agent ?? "Unknown Agent";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium bg-secondary text-secondary-foreground",
        className
      )}
    >
      <Icon className="h-3 w-3" />
      {label}
    </span>
  );
}
