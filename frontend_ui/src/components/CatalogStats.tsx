import { Database, Monitor, Server, Activity, Shield, Terminal } from "lucide-react";

interface StatCardProps {
  label: string;
  value: number;
  icon: React.ElementType;
  color: string;
}

function StatCard({ label, value, icon: Icon, color }: StatCardProps) {
  return (
    <div className="enterprise-card p-4 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-sm text-muted-foreground">{label}</p>
      </div>
    </div>
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
  };
}

export function CatalogStats({ stats }: CatalogStatsProps) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
      <StatCard
        label="Total Commands"
        value={stats.total}
        icon={Terminal}
        color="bg-primary/10 text-primary"
      />
      <StatCard
        label="DB2 Commands"
        value={stats.db2}
        icon={Database}
        color="bg-platform-db2/10 text-platform-db2"
      />
      <StatCard
        label="CICS Commands"
        value={stats.cics}
        icon={Monitor}
        color="bg-platform-cics/10 text-platform-cics"
      />
      <StatCard
        label="IMS Commands"
        value={stats.ims}
        icon={Server}
        color="bg-platform-ims/10 text-platform-ims"
      />
      <StatCard
        label="Read Operations"
        value={stats.readOps}
        icon={Shield}
        color="bg-status-safe-bg text-status-safe-foreground"
      />
      <StatCard
        label="Execute Operations"
        value={stats.executeOps}
        icon={Activity}
        color="bg-status-caution-bg text-status-caution-foreground"
      />
    </div>
  );
}
