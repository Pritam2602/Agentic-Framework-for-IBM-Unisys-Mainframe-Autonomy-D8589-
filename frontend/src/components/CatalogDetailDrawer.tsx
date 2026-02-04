import { CatalogEntry } from "@/types/catalog";
import { OperationBadge } from "./OperationBadge";
import { CommandFamilyBadge } from "./CommandFamilyBadge";
import { ExecutionCostIndicator } from "./ExecutionCostIndicator";
import { AgentBadge } from "./AgentBadge";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import {
  Terminal,
  Box,
  Shield,
  Gauge,
  AlertTriangle,
  FileJson,
  Network,
  CheckCircle2
} from "lucide-react";

import { useQuery } from "@tanstack/react-query";
import { fetchCapability } from "@/lib/api";
import { ListChecks } from "lucide-react";

interface CatalogDetailDrawerProps {
  entry: CatalogEntry | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function DetailSection({
  icon: Icon,
  title,
  children
}: {
  icon: React.ElementType;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <Icon className="h-4 w-4" />
        {title}
      </div>
      <div className="pl-6">{children}</div>
    </div>
  );
}

export function CatalogDetailDrawer({ entry, open, onOpenChange }: CatalogDetailDrawerProps) {
  // Fetch detailed info (preconditions) when drawer is open and entry is selected
  const { data: detailData, isLoading: isLoadingDetail } = useQuery({
    queryKey: ['capability', entry?.zowe_command],
    queryFn: () => fetchCapability(entry!.zowe_command),
    enabled: !!entry && open,
  });

  if (!entry) return null;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[500px] sm:max-w-[500px] overflow-y-auto">
        <SheetHeader className="space-y-4">
          <div className="flex items-center gap-3">
            <CommandFamilyBadge family={entry.command_family} />
            <OperationBadge operation={entry.operation} />
          </div>
          <SheetTitle className="text-xl font-semibold">{entry.ibm_artifact}</SheetTitle>
        </SheetHeader>

        <div className="mt-6 space-y-6 animate-fade-in">
          {/* Preconditions (Loaded from API) */}
          {isLoadingDetail ? (
            <div className="flex items-center gap-2 text-sm text-muted-foreground pl-6">
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-primary"></div>
              Loading details...
            </div>
          ) : detailData?.preconditions && detailData.preconditions.length > 0 ? (
            <>
              <DetailSection icon={ListChecks} title="Preconditions">
                <ul className="list-disc list-inside space-y-1 text-sm">
                  {detailData.preconditions.map((pre, idx) => (
                    <li key={idx}>{pre}</li>
                  ))}
                </ul>
              </DetailSection>
              <Separator />
            </>
          ) : null}

          {/* Command */}
          <DetailSection icon={Terminal} title="Zowe Command">
            <div className="bg-secondary p-3 rounded-lg font-mono text-sm break-all">
              {entry.zowe_command}
            </div>
          </DetailSection>

          <Separator />

          {/* Classification */}
          <DetailSection icon={Box} title="Classification">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Category</p>
                <Badge variant="outline" className="capitalize">{entry.category}</Badge>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Subsystem</p>
                <Badge variant="outline">{entry.subsystem}</Badge>
              </div>
            </div>
          </DetailSection>

          <Separator />

          {/* Access & Response */}
          <DetailSection icon={Network} title="Access Pattern">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Access Method</p>
                <Badge variant="secondary">{entry.access_pattern}</Badge>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Response Format</p>
                <div className="flex items-center gap-1.5">
                  <FileJson className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-sm">{entry.response_format}</span>
                </div>
              </div>
            </div>
          </DetailSection>

          <Separator />

          {/* Agent Assignment */}
          <DetailSection icon={Shield} title="Agent Assignment">
            <div className="flex items-center gap-3">
              <AgentBadge agent={entry.intended_agent} />
              <span className="text-sm text-muted-foreground">
                designated handler
              </span>
            </div>
          </DetailSection>

          <Separator />

          {/* Execution Cost */}
          <DetailSection icon={Gauge} title="Execution Cost">
            <ExecutionCostIndicator cost={entry.execution_cost} />
          </DetailSection>

          <Separator />

          {/* Confidence Level */}
          <DetailSection icon={CheckCircle2} title="Mapping Confidence">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${entry.confidence_level === "HIGH" ? "bg-cost-low" :
                  entry.confidence_level === "MEDIUM" ? "bg-cost-medium" : "bg-cost-high"
                }`} />
              <span className="text-sm font-medium">{entry.confidence_level}</span>
              <span className="text-sm text-muted-foreground">confidence</span>
            </div>
          </DetailSection>

          <Separator />

          {/* Constraints / Governance */}
          <DetailSection icon={AlertTriangle} title="Constraints & Governance">
            <div className="bg-status-caution-bg border border-status-caution/20 p-4 rounded-lg">
              <p className="text-sm text-status-caution-foreground leading-relaxed">
                {entry.constraints}
              </p>
            </div>
          </DetailSection>
        </div>
      </SheetContent>
    </Sheet>
  );
}
