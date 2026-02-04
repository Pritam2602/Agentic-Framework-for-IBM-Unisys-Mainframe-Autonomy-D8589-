import { useState, useMemo } from "react";
import { CatalogFiltersBar } from "@/components/CatalogFiltersBar";
import { CatalogTable } from "@/components/CatalogTable";
import { CatalogDetailDrawer } from "@/components/CatalogDetailDrawer";
import { sampleCatalogData } from "@/data/sampleCatalog";
import { CatalogEntry, CatalogFilters } from "@/types/catalog";
import { CatalogLegend } from "@/components/CatalogLegend";
import { Card, CardContent } from "@/components/ui/card";
import { Database, Shield, Zap, AlertTriangle } from "lucide-react";

const Datasets = () => {
  const [selectedEntry, setSelectedEntry] = useState<CatalogEntry | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [filters, setFilters] = useState<CatalogFilters>({
    search: "",
    commandFamily: "FILES",
    subsystem: "ALL",
    operation: "ALL",
    executionCost: "ALL",
  });

  // Get only FILES family entries
  const filesEntries = useMemo(() => {
    return sampleCatalogData.filter((entry) => entry.command_family === "FILES");
  }, []);

  // Filter the catalog entries
  const filteredEntries = useMemo(() => {
    return filesEntries.filter((entry) => {
      if (
        filters.search &&
        !entry.zowe_command.toLowerCase().includes(filters.search.toLowerCase()) &&
        !entry.ibm_artifact.toLowerCase().includes(filters.search.toLowerCase())
      ) {
        return false;
      }
      if (filters.subsystem !== "ALL" && entry.subsystem !== filters.subsystem) {
        return false;
      }
      if (filters.operation !== "ALL" && entry.operation !== filters.operation) {
        return false;
      }
      if (filters.executionCost !== "ALL" && entry.execution_cost !== filters.executionCost) {
        return false;
      }
      return true;
    });
  }, [filters, filesEntries]);

  // Calculate stats for datasets
  const stats = useMemo(() => ({
    total: filesEntries.length,
    readOps: filesEntries.filter((e) => e.operation === "READ").length,
    executeOps: filesEntries.filter((e) => e.operation === "EXECUTE").length,
    highCost: filesEntries.filter((e) => e.execution_cost === "HIGH").length,
  }), [filesEntries]);

  const handleSelectEntry = (entry: CatalogEntry) => {
    setSelectedEntry(entry);
    setDrawerOpen(true);
  };

  return (
    <div className="container py-8 space-y-6">
      {/* Page Title */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Dataset Commands</h2>
        <p className="text-muted-foreground">
          Manage MVS datasets, PDS members, and file operations
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-platform-files/10 text-platform-files">
              <Database className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.total}</p>
              <p className="text-sm text-muted-foreground">Total Commands</p>
            </div>
          </CardContent>
        </Card>
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-status-safe-bg text-status-safe-foreground">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.readOps}</p>
              <p className="text-sm text-muted-foreground">READ Ops</p>
            </div>
          </CardContent>
        </Card>
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-status-caution-bg text-status-caution-foreground">
              <Zap className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.executeOps}</p>
              <p className="text-sm text-muted-foreground">EXECUTE Ops</p>
            </div>
          </CardContent>
        </Card>
        <Card className="hover:shadow-md transition-shadow">
          <CardContent className="p-4 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-destructive/10 text-destructive">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <p className="text-2xl font-bold">{stats.highCost}</p>
              <p className="text-sm text-muted-foreground">High Cost</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <section>
        <CatalogFiltersBar
          filters={filters}
          onFiltersChange={setFilters}
          resultCount={filteredEntries.length}
          totalCount={filesEntries.length}
          hideCommandFamilyFilter
        />
      </section>

      {/* Catalog Table */}
      <section>
        <CatalogTable
          entries={filteredEntries}
          selectedEntry={selectedEntry}
          onSelectEntry={handleSelectEntry}
        />
      </section>

      {/* Legend */}
      <CatalogLegend />

      {/* Detail Drawer */}
      <CatalogDetailDrawer
        entry={selectedEntry}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
      />
    </div>
  );
};

export default Datasets;
