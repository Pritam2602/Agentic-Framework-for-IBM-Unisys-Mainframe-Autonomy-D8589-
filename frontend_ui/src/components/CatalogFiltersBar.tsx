import { CatalogFilters, CommandFamily, Subsystem, Operation } from "@/types/catalog";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, Filter } from "lucide-react";

interface CatalogFiltersBarProps {
  filters: CatalogFilters;
  onFiltersChange: (filters: CatalogFilters) => void;
  resultCount: number;
  totalCount: number;
}

const commandFamilies: (CommandFamily | "ALL")[] = ["ALL", "DB2", "CICS", "IMS", "FILES", "PLATFORM", "OBSERVABILITY"];
const subsystems: (Subsystem | "ALL")[] = ["ALL", "DB2", "CICS", "IMS", "z/OSMF"];
const operations: (Operation | "ALL")[] = ["ALL", "READ", "EXECUTE"];

export function CatalogFiltersBar({ 
  filters, 
  onFiltersChange, 
  resultCount, 
  totalCount 
}: CatalogFiltersBarProps) {
  return (
    <div className="enterprise-card p-4">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center flex-1">
          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search Zowe commands..."
              value={filters.search}
              onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
              className="pl-10"
            />
          </div>

          {/* Filters */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground hidden sm:block" />
            
            <Select
              value={filters.commandFamily}
              onValueChange={(value) => 
                onFiltersChange({ ...filters, commandFamily: value as CommandFamily | "ALL" })
              }
            >
              <SelectTrigger className="w-[140px]">
                <SelectValue placeholder="Family" />
              </SelectTrigger>
              <SelectContent>
                {commandFamilies.map((family) => (
                  <SelectItem key={family} value={family}>
                    {family === "ALL" ? "All Families" : family}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={filters.subsystem}
              onValueChange={(value) => 
                onFiltersChange({ ...filters, subsystem: value as Subsystem | "ALL" })
              }
            >
              <SelectTrigger className="w-[130px]">
                <SelectValue placeholder="Subsystem" />
              </SelectTrigger>
              <SelectContent>
                {subsystems.map((subsystem) => (
                  <SelectItem key={subsystem} value={subsystem}>
                    {subsystem === "ALL" ? "All Subsystems" : subsystem}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={filters.operation}
              onValueChange={(value) => 
                onFiltersChange({ ...filters, operation: value as Operation | "ALL" })
              }
            >
              <SelectTrigger className="w-[120px]">
                <SelectValue placeholder="Operation" />
              </SelectTrigger>
              <SelectContent>
                {operations.map((op) => (
                  <SelectItem key={op} value={op}>
                    {op === "ALL" ? "All Ops" : op}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Result count */}
        <div className="text-sm text-muted-foreground">
          Showing <span className="font-semibold text-foreground">{resultCount}</span> of{" "}
          <span className="font-semibold text-foreground">{totalCount}</span> commands
        </div>
      </div>
    </div>
  );
}
