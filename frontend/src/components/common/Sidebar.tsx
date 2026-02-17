import { NavLink } from 'react-router-dom';
import {
  RectangleStackIcon,
  DocumentMagnifyingGlassIcon,
  ChatBubbleLeftRightIcon,
  CpuChipIcon,
  ServerStackIcon,
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Catalog', href: '/catalog', icon: RectangleStackIcon },
  { name: 'Reasoning Logs', href: '/reasoning-logs', icon: DocumentMagnifyingGlassIcon },
  { name: 'Execution Panel', href: '/execution', icon: ChatBubbleLeftRightIcon },
  { name: 'IBM Agent', href: '/ibm-agent', icon: CpuChipIcon },
  { name: 'Unisys Agent', href: '/unisys-agent', icon: ServerStackIcon },
];

export default function Sidebar() {
  return (
    <div className="fixed left-0 top-0 h-screen w-64 bg-terminal-panel border-r border-terminal-border flex flex-col">
      {/* Logo/Brand */}
      <div className="p-6 border-b border-terminal-border">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-gradient-to-br from-terminal-accent to-terminal-blue rounded-lg flex items-center justify-center glow-border">
            <span className="text-terminal-bg font-bold text-xl font-mono">M</span>
          </div>
          <div>
            <h1 className="text-lg font-bold text-terminal-accent font-display">
              MAINFRAME
            </h1>
            <p className="text-xs text-gray-400 font-mono">Command Platform</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 group ${
                isActive
                  ? 'bg-terminal-accent/10 border border-terminal-accent text-terminal-accent'
                  : 'hover:bg-terminal-border/50 text-gray-400 hover:text-terminal-accent border border-transparent'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <item.icon
                  className={`w-5 h-5 ${
                    isActive ? 'text-terminal-accent' : 'text-gray-400 group-hover:text-terminal-accent'
                  }`}
                />
                <span className="font-medium font-display">{item.name}</span>
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-terminal-border">
        <div className="text-xs text-gray-500 font-mono space-y-1">
          <div className="flex justify-between">
            <span>Version:</span>
            <span className="text-terminal-accent">3.2.1</span>
          </div>
          <div className="flex justify-between">
            <span>Status:</span>
            <span className="text-terminal-accent status-online">● ONLINE</span>
          </div>
        </div>
      </div>
    </div>
  );
}
