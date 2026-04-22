import { NavLink } from "react-router-dom";
import {
  CircleStackIcon,
  CommandLineIcon,
  CpuChipIcon,
  DocumentMagnifyingGlassIcon,
  Squares2X2Icon,
  ServerStackIcon,
} from "@heroicons/react/24/outline";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Control Center", href: "/execution", icon: Squares2X2Icon },
  { name: "Intent Console", href: "/execution", icon: CpuChipIcon },
  { name: "Context Console", href: "/execution", icon: ServerStackIcon },
  { name: "Trace View", href: "/execution", icon: DocumentMagnifyingGlassIcon },
  { name: "System Map", href: "/execution", icon: CircleStackIcon },
];

export default function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 border-r border-slate-800/80 bg-slate-950/90 backdrop-blur lg:flex lg:flex-col">
      <div className="border-b border-slate-800 px-6 py-6">
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-blue-500 text-lg font-black text-slate-950">
            AI
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Enterprise UI</p>
            <h2 className="mt-1 text-lg font-semibold text-slate-50">Federation Console</h2>
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-2 px-4 py-6">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                "flex items-start gap-3 rounded-2xl border px-4 py-4 transition-all",
                isActive
                  ? "border-cyan-500/30 bg-cyan-500/10 text-cyan-100"
                  : "border-transparent bg-transparent text-slate-400 hover:border-slate-800 hover:bg-slate-900/70 hover:text-slate-100"
              )
            }
          >
            {({ isActive }) => (
              <>
                <item.icon className={cn("mt-0.5 h-5 w-5", isActive ? "text-cyan-300" : "text-slate-500")} />
                <div>
                  <p className="text-sm font-semibold">{item.name}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-500">
                    {item.name === "Control Center"
                      ? "Run and inspect the AI federation pipeline."
                      : "Phase 1 keeps these views inside the control center route."}
                  </p>
                </div>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-slate-800 px-6 py-5">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/70 p-4">
          <div className="flex items-center gap-2 text-sm text-emerald-300">
            <CommandLineIcon className="h-4 w-4" />
            System online
          </div>
          <p className="mt-2 text-xs leading-5 text-slate-400">
            Intent and context agents are available from the same control surface.
          </p>
        </div>
      </div>
    </aside>
  );
}
