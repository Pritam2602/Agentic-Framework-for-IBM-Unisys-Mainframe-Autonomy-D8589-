import { Card, CardContent } from "@/components/ui/card";
import { 
  Terminal, 
  Shield, 
  Zap, 
  AlertTriangle,
  Database,
  Monitor,
  Server,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ElementType;
  colorClass: string;
  trend?: "up" | "down" | "neutral";
}

function StatCard({ label, value, icon: Icon, colorClass }: StatCardProps) {
  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-center gap-4">
          <div className={cn("p-3 rounded-lg", colorClass)}>
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <p className="text-2xl font-bold tracking-tight">{value}</p>
            <p className="text-sm text-muted-foreground">{label}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface CatalogStatsProps {
  stats: {
    total: number;
    db2: number;
    cics: number;
    ims: number;
    readOps: number;
    executeOps: number;
    highCost: number;
  };
}

export function CatalogStats({ stats }: CatalogStatsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
      <StatCard
        label="Total Commands"
        value={stats.total}
        icon={Terminal}
        colorClass="bg-primary/10 text-primary"
      />
      <StatCard
        label="DB2"
        value={stats.db2}
        icon={Database}
        colorClass="bg-platform-db2/10 text-platform-db2"
      />
      <StatCard
        label="CICS"
        value={stats.cics}
        icon={Monitor}
        colorClass="bg-platform-cics/10 text-platform-cics"
      />
      <StatCard
        label="IMS"
        value={stats.ims}
        icon={Server}
        colorClass="bg-platform-ims/10 text-platform-ims"
      />
      <StatCard
        label="READ Ops"
        value={stats.readOps}
        icon={Shield}
        colorClass="bg-status-safe-bg text-status-safe-foreground"
      />
      <StatCard
        label="EXECUTE Ops"
        value={stats.executeOps}
        icon={Zap}
        colorClass="bg-status-caution-bg text-status-caution-foreground"
      />
      <StatCard
        label="High Cost"
        value={stats.highCost}
        icon={AlertTriangle}
        colorClass="bg-destructive/10 text-destructive"
      />
    </div>
  );
}
