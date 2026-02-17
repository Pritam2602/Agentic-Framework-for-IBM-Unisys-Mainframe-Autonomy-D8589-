import { BellIcon, UserCircleIcon } from '@heroicons/react/24/outline';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  const currentTime = new Date().toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit',
    hour12: false 
  });

  return (
    <header className="h-16 bg-terminal-panel border-b border-terminal-border flex items-center justify-between px-6">
      <div>
        <h1 className="text-xl font-bold text-terminal-accent font-display">
          {title}
        </h1>
        {subtitle && (
          <p className="text-sm text-gray-400 font-mono">{subtitle}</p>
        )}
      </div>

      <div className="flex items-center space-x-6">
        {/* System Time */}
        <div className="text-sm font-mono">
          <span className="text-gray-500">SYS TIME:</span>
          <span className="ml-2 text-terminal-accent">{currentTime}</span>
        </div>

        {/* Notifications */}
        <button className="relative p-2 hover:bg-terminal-border rounded-lg transition-colors">
          <BellIcon className="w-5 h-5 text-gray-400 hover:text-terminal-accent transition-colors" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-terminal-red rounded-full"></span>
        </button>

        {/* User Menu */}
        <button className="flex items-center space-x-2 px-3 py-2 hover:bg-terminal-border rounded-lg transition-colors">
          <UserCircleIcon className="w-6 h-6 text-gray-400" />
          <span className="text-sm font-medium text-gray-300">Admin</span>
        </button>
      </div>
    </header>
  );
}
