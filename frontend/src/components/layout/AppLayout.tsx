import { Outlet, Link, useLocation } from "react-router-dom";
import { Cpu, BookOpen, Home, Briefcase, Database, GitBranch } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { path: "/", label: "Home", icon: Home },
  { path: "/jobs", label: "Jobs", icon: Briefcase },
  { path: "/datasets", label: "Datasets", icon: Database },
  { path: "/workflows", label: "Workflows", icon: GitBranch },
];

export function AppLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top Header */}
      <header className="bg-card border-b border-border sticky top-0 z-50">
        <div className="container">
          <div className="flex items-center justify-between py-4">
            {/* Logo & Title */}
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-primary text-primary-foreground">
                <Cpu className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-lg font-bold tracking-tight">
                  Zowe Capability Catalog
                </h1>
                <p className="text-xs text-muted-foreground hidden sm:block">
                  D8589 Research Project
                </p>
              </div>
            </div>

            {/* View-Only Badge */}
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-muted text-sm text-muted-foreground">
              <BookOpen className="h-4 w-4" />
              <span>View-Only Mode</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center gap-1 -mb-px">
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors",
                    isActive
                      ? "border-primary text-primary"
                      : "border-transparent text-muted-foreground hover:text-foreground hover:border-border"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Page Content */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-border bg-card mt-auto">
        <div className="container py-6 flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-muted-foreground">
          <p>
            Agentic Framework for IBM–Unisys Mainframe Autonomy • D8589 Research Project
          </p>
          <p>
            Catalog viewer for governance and explainable automation
          </p>
        </div>
      </footer>
    </div>
  );
}
