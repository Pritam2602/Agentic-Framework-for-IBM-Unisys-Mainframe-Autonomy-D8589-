import { ReactNode } from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon?: ReactNode;
  subtitle?: string;
  accentColor?: 'accent' | 'amber' | 'blue' | 'purple' | 'red';
}

export default function StatCard({ 
  title, 
  value, 
  icon, 
  subtitle,
  accentColor = 'accent' 
}: StatCardProps) {
  const colorClasses = {
    accent: 'text-terminal-accent border-terminal-accent',
    amber: 'text-terminal-amber border-terminal-amber',
    blue: 'text-terminal-blue border-terminal-blue',
    purple: 'text-terminal-purple border-terminal-purple',
    red: 'text-terminal-red border-terminal-red',
  };

  return (
    <div className="stat-card">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <p className="text-sm text-gray-400 font-medium uppercase tracking-wider mb-2">
            {title}
          </p>
          <p className={`text-3xl font-bold font-display ${colorClasses[accentColor]}`}>
            {value}
          </p>
        </div>
        {icon && (
          <div className={`p-3 rounded-lg border ${colorClasses[accentColor]} bg-opacity-10`}>
            {icon}
          </div>
        )}
      </div>

      {subtitle && (
        <div className="text-sm text-gray-500 font-mono">
          {subtitle}
        </div>
      )}
    </div>
  );
}
