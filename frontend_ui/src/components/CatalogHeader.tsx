import { Cpu, BookOpen } from "lucide-react";

export function CatalogHeader() {
  return (
    <header className="bg-card border-b border-border">
      <div className="container py-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-xl bg-primary text-primary-foreground">
              <Cpu className="h-8 w-8" />
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight">
                Zowe Capability Catalog
              </h1>
              <p className="text-muted-foreground mt-1">
                Agentic Framework for IBM–Unisys Mainframe Autonomy (D8589)
              </p>
            </div>
          </div>
          <div className="hidden md:flex items-center gap-2 text-sm text-muted-foreground">
            <BookOpen className="h-4 w-4" />
            <span>View-Only Mode</span>
          </div>
        </div>
      </div>
    </header>
  );
}
