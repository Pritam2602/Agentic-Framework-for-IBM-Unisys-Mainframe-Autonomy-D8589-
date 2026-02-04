import { useState, useMemo } from "react";
import { CatalogStats } from "@/components/CatalogStats";
import { CatalogFiltersBar } from "@/components/CatalogFiltersBar";
import { CatalogTable } from "@/components/CatalogTable";
import { CatalogDetailDrawer } from "@/components/CatalogDetailDrawer";
import { fetchCatalog } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

import { CatalogEntry, CatalogFilters } from "@/types/catalog";
import { CatalogLegend } from "@/components/CatalogLegend";

const Index = () => {
  const [selectedEntry, setSelectedEntry] = useState<CatalogEntry | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [filters, setFilters] = useState<CatalogFilters>({
    search: "",
    commandFamily: "ALL",
    subsystem: "ALL",
    operation: "ALL",
    executionCost: "ALL",
  });

  // Fetch catalog data from API
  const { data: catalogData = [], isLoading, error } = useQuery({
    queryKey: ['catalog', filters.commandFamily], // Optimization: we could filter on backend, but for now we fetch all or filter client side. 
    // Actually, the backend supports filtering by family. But the UI supports multiple filters. 
    // To keep it simple and consistent with previous behavior, let's fetch all and filter client side, 
    // OR we could pass parameters. The current backend only supports 'family' filter.
    // Let's fetch all for now to support all client-side filters efficiently without spamming API.
    queryFn: () => fetchCatalog(),
  });

  // Filter the catalog entries
  const filteredEntries = useMemo(() => {
    return catalogData.filter((entry) => {
      if (
        filters.search &&
        !entry.zowe_command.toLowerCase().includes(filters.search.toLowerCase()) &&
        !entry.ibm_artifact.toLowerCase().includes(filters.search.toLowerCase())
      ) {
        return false;
      }
      if (filters.commandFamily !== "ALL" && entry.command_family !== filters.commandFamily) {
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
  }, [catalogData, filters]);

  // Calculate stats
  const stats = useMemo(() => ({
    total: catalogData.length,
    db2: catalogData.filter((e) => e.command_family === "DB2").length,
    cics: catalogData.filter((e) => e.command_family === "CICS").length,
    ims: catalogData.filter((e) => e.command_family === "IMS").length,
    readOps: catalogData.filter((e) => e.operation === "READ").length,
    executeOps: catalogData.filter((e) => e.operation === "EXECUTE").length,
    highCost: catalogData.filter((e) => e.execution_cost === "HIGH").length,
  }), [catalogData]);

  const handleSelectEntry = (entry: CatalogEntry) => {
    setSelectedEntry(entry);
    setDrawerOpen(true);
  };

  if (isLoading) {
    return (
      <div className="container py-8 flex items-center justify-center h-[50vh]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container py-8 text-center text-red-500">
        Error loading catalog: {(error as Error).message}
        <br />
        Make sure the backend is running on http://localhost:5000
      </div>
    );
  }

  return (
    <div className="container py-8 space-y-6">
      {/* Page Title */}
      <div>
        <h2 className="text-2xl font-bold tracking-tight">Catalog Overview</h2>
        <p className="text-muted-foreground">
          Browse and explore all Zowe CLI capabilities across IBM mainframe subsystems
        </p>
      </div>

      {/* Stats Overview */}
      <section>
        <CatalogStats stats={stats} />
      </section>

      {/* Filters */}
      <section>
        <CatalogFiltersBar
          filters={filters}
          onFiltersChange={setFilters}
          resultCount={filteredEntries.length}
          totalCount={catalogData.length}
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

export default Index;
