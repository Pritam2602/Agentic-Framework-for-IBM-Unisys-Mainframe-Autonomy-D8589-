import { CatalogEntry } from "@/types/catalog";
import { OperationBadge } from "./OperationBadge";
import { CommandFamilyBadge } from "./CommandFamilyBadge";
import { ExecutionCostIndicator } from "./ExecutionCostIndicator";
import { AgentBadge } from "./AgentBadge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

interface CatalogTableProps {
  entries: CatalogEntry[];
  selectedEntry: CatalogEntry | null;
  onSelectEntry: (entry: CatalogEntry) => void;
}

export function CatalogTable({ entries, selectedEntry, onSelectEntry }: CatalogTableProps) {
  return (
    <div className="enterprise-card overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50 hover:bg-muted/50">
            <TableHead className="font-semibold text-foreground w-[350px]">Zowe Command</TableHead>
            <TableHead className="font-semibold text-foreground">Family</TableHead>
            <TableHead className="font-semibold text-foreground">Subsystem</TableHead>
            <TableHead className="font-semibold text-foreground">IBM Artifact</TableHead>
            <TableHead className="font-semibold text-foreground">Operation</TableHead>
            <TableHead className="font-semibold text-foreground">Agent</TableHead>
            <TableHead className="font-semibold text-foreground">Cost</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {entries.length === 0 ? (
            <TableRow>
              <TableCell colSpan={7} className="h-24 text-center text-muted-foreground">
                No catalog entries match your filters.
              </TableCell>
            </TableRow>
          ) : (
            entries.map((entry) => (
              <TableRow
                key={entry.id}
                onClick={() => onSelectEntry(entry)}
                className={cn(
                  "table-row-interactive",
                  selectedEntry?.id === entry.id && "bg-accent"
                )}
              >
                <TableCell className="font-mono text-sm">
                  <div className="max-w-[350px] truncate" title={entry.zowe_command}>
                    {entry.zowe_command}
                  </div>
                </TableCell>
                <TableCell>
                  <CommandFamilyBadge family={entry.command_family} />
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {entry.subsystem}
                </TableCell>
                <TableCell>
                  <span className="text-sm font-medium">{entry.ibm_artifact}</span>
                </TableCell>
                <TableCell>
                  <OperationBadge operation={entry.operation} />
                </TableCell>
                <TableCell>
                  <AgentBadge agent={entry.intended_agent} />
                </TableCell>
                <TableCell>
                  <ExecutionCostIndicator cost={entry.execution_cost} showLabel={false} />
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
