import { BellIcon, UserCircleIcon } from "@heroicons/react/24/outline";

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  const currentTime = new Date().toLocaleString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    month: "short",
    day: "2-digit",
  });

  return (
    <header className="sticky top-0 z-20 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur">
      <div className="flex flex-col gap-4 px-4 py-5 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <div>
          <p className="text-xs uppercase tracking-[0.32em] text-slate-500">AI Data Federation Control Center</p>
          <h1 className="mt-2 text-2xl font-semibold text-slate-50">{title}</h1>
          {subtitle ? <p className="mt-1 text-sm text-slate-400">{subtitle}</p> : null}
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div className="rounded-full border border-slate-800 bg-slate-900/70 px-4 py-2 text-slate-300">
            {currentTime}
          </div>
          <button className="rounded-full border border-slate-800 bg-slate-900/70 p-2 text-slate-400 transition hover:text-cyan-300">
            <BellIcon className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2 rounded-full border border-slate-800 bg-slate-900/70 px-3 py-2">
            <UserCircleIcon className="h-6 w-6 text-slate-400" />
            <span className="text-slate-300">Operator</span>
          </div>
        </div>
      </div>
    </header>
  );
}
