import { useState, useMemo, useEffect } from "react";
import { CatalogHeader } from "@/components/CatalogHeader";
import { CatalogStats } from "@/components/CatalogStats";
import { CatalogFiltersBar } from "@/components/CatalogFiltersBar";
import { CatalogTable } from "@/components/CatalogTable";
import { CatalogDetailDrawer } from "@/components/CatalogDetailDrawer";
import { CatalogEntry, CatalogFilters } from "@/types/catalog";

const API_URL = "http://127.0.0.1:5000/api/catalog";

const Index = () => {
  const [catalogData, setCatalogData] = useState<CatalogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [selectedEntry, setSelectedEntry] = useState<CatalogEntry | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const [filters, setFilters] = useState<CatalogFilters>({
    search: "",
    commandFamily: "ALL",
    subsystem: "ALL",
    operation: "ALL",
  });

  // 🔹 Fetch catalog from backend
  useEffect(() => {
    fetch(API_URL)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch catalog");
        return res.json();
      })
      .then((data) => {
        setCatalogData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  // 🔹 Apply filters
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

      return true;
    });
  }, [catalogData, filters]);

  // 🔹 Stats derived from backend data
  const stats = useMemo(() => ({
    total: catalogData.length,
    db2: catalogData.filter((e) => e.command_family === "DB2").length,
    cics: catalogData.filter((e) => e.command_family === "CICS").length,
    ims: catalogData.filter((e) => e.command_family === "IMS").length,
    readOps: catalogData.filter((e) => e.operation === "READ").length,
    executeOps: catalogData.filter((e) => e.operation === "EXECUTE").length,
  }), [catalogData]);

  const handleSelectEntry = (entry: CatalogEntry) => {
    setSelectedEntry(entry);
    setDrawerOpen(true);
  };

  if (loading) {
    return <div className="p-6">Loading catalog...</div>;
  }

  if (error) {
    return <div className="p-6 text-red-600">Error: {error}</div>;
  }

  return (
    <div className="min-h-screen bg-background">
      <CatalogHeader />

      <main className="container py-8 space-y-6">
        <section>
          <h2 className="text-lg font-semibold mb-4">Catalog Overview</h2>
          <CatalogStats stats={stats} />
        </section>

        <section>
          <CatalogFiltersBar
            filters={filters}
            onFiltersChange={setFilters}
            resultCount={filteredEntries.length}
            totalCount={catalogData.length}
          />
        </section>

        <section>
          <CatalogTable
            entries={filteredEntries}
            selectedEntry={selectedEntry}
            onSelectEntry={handleSelectEntry}
          />
        </section>

        {/* Legend unchanged */}
      </main>

      <CatalogDetailDrawer
        entry={selectedEntry}
        open={drawerOpen}
        onOpenChange={setDrawerOpen}
      />

      <footer className="border-t border-border bg-card mt-8">
        <div className="container py-6 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
          <p>Agentic Framework for IBM–Unisys Mainframe Autonomy • D8589</p>
          <p>Catalog viewer for governance and explainable automation</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
