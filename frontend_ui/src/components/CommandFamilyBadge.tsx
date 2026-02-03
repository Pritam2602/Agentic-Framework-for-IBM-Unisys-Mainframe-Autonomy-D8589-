import { cn } from "@/lib/utils";
import { CommandFamily } from "@/types/catalog";
import {
  Database,
  Monitor,
  Server,
  FolderOpen,
  Cpu,
  Activity,
  HelpCircle
} from "lucide-react";

interface CommandFamilyBadgeProps {
  family?: CommandFamily | string;
  className?: string;
}

const familyConfig: Record<string, { icon: React.ElementType; colorClass: string }> = {
  DB2: { icon: Database, colorClass: "bg-platform-db2/10 text-platform-db2 border-platform-db2/20" },
  CICS: { icon: Monitor, colorClass: "bg-platform-cics/10 text-platform-cics border-platform-cics/20" },
  IMS: { icon: Server, colorClass: "bg-platform-ims/10 text-platform-ims border-platform-ims/20" },
  FILES: { icon: FolderOpen, colorClass: "bg-platform-files/10 text-platform-files border-platform-files/20" },
  PLATFORM: { icon: Cpu, colorClass: "bg-platform-platform/10 text-platform-platform border-platform-platform/20" },
  OBSERVABILITY: { icon: Activity, colorClass: "bg-platform-observability/10 text-platform-observability border-platform-observability/20" },
};

export function CommandFamilyBadge({ family, className }: CommandFamilyBadgeProps) {
  const config = family ? familyConfig[family] : null;
  const Icon = config?.icon ?? HelpCircle;
  const colorClass =
    config?.colorClass ?? "bg-muted text-muted-foreground border-muted";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium border",
        colorClass,
        className
      )}
    >
      <Icon className="h-3 w-3" />
      {family ?? "UNKNOWN"}
    </span>
  );
}
