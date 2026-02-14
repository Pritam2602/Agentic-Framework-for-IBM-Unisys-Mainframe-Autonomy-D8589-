import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Layout, StatCard, LoadingSpinner } from '../components/common';
import { fetchCatalogStats } from '../services/api';
import { CatalogStats } from '../types';
import {
  CommandLineIcon,
  BriefcaseIcon,
  ArrowPathIcon,
  CircleStackIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline';

export default function CatalogPage() {
  const [stats, setStats] = useState<CatalogStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const data = await fetchCatalogStats();
        setStats(data);
      } catch (error) {
        console.error('Failed to load catalog stats:', error);
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, []);

  const catalogSections = [
    {
      name: 'Commands',
      href: '/catalog/commands',
      icon: CommandLineIcon,
      color: 'accent' as const,
      description: 'Browse and execute mainframe commands',
    },
    {
      name: 'Jobs',
      href: '/catalog/jobs',
      icon: BriefcaseIcon,
      color: 'blue' as const,
      description: 'View and manage JCL jobs',
    },
    {
      name: 'Workflows',
      href: '/catalog/workflows',
      icon: ArrowPathIcon,
      color: 'purple' as const,
      description: 'Orchestrate multi-step workflows',
    },
    {
      name: 'Datasets',
      href: '/catalog/datasets',
      icon: CircleStackIcon,
      color: 'amber' as const,
      description: 'Access and manage datasets',
    },
  ];

  if (loading) {
    return (
      <Layout title="Catalog" subtitle="Mainframe resource management">
        <div className="flex items-center justify-center h-64">
          <LoadingSpinner size="lg" message="Loading catalog..." />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Catalog" subtitle="Mainframe resource management">
      {/* Statistical Overview */}
      <div className="mb-8">
        <div className="flex items-center space-x-3 mb-6">
          <ChartBarIcon className="w-6 h-6 text-terminal-accent" />
          <h2 className="text-xl font-bold text-terminal-accent font-display">
            Statistical Overview
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Commands"
            value={stats?.totalCommands || 0}
            icon={<CommandLineIcon className="w-6 h-6 text-terminal-accent" />}
            accentColor="accent"
          />
          <StatCard
            title="Total Jobs"
            value={stats?.totalJobs || 0}
            icon={<BriefcaseIcon className="w-6 h-6 text-terminal-blue" />}
            accentColor="blue"
          />
          <StatCard
            title="Total Workflows"
            value={stats?.totalWorkflows || 0}
            icon={<ArrowPathIcon className="w-6 h-6 text-terminal-purple" />}
            accentColor="purple"
          />
          <StatCard
            title="Total Datasets"
            value={stats?.totalDatasets.toLocaleString() || 0}
            icon={<CircleStackIcon className="w-6 h-6 text-terminal-amber" />}
            accentColor="amber"
          />
        </div>

        {stats?.lastUpdated && (
          <div className="mt-4 text-sm text-gray-500 font-mono">
            Last updated: {new Date(stats.lastUpdated).toLocaleString()}
          </div>
        )}
      </div>

      {/* Navigation Cards */}
      <div>
        <h2 className="text-xl font-bold text-terminal-accent font-display mb-6">
          Browse Catalog
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {catalogSections.map((section) => (
            <Link
              key={section.name}
              to={section.href}
              className="terminal-panel p-6 hover:border-terminal-accent transition-all duration-200 group"
            >
              <div className={`w-12 h-12 rounded-lg border border-terminal-${section.color} flex items-center justify-center mb-4 group-hover:bg-terminal-${section.color} group-hover:bg-opacity-10 transition-all`}>
                <section.icon className={`w-6 h-6 text-terminal-${section.color}`} />
              </div>
              <h3 className="text-lg font-bold text-white mb-2 font-display">
                {section.name}
              </h3>
              <p className="text-sm text-gray-400">
                {section.description}
              </p>
              <div className="mt-4 text-sm text-terminal-accent font-mono group-hover:text-terminal-blue transition-colors">
                View →
              </div>
            </Link>
          ))}
        </div>
      </div>
    </Layout>
  );
}
