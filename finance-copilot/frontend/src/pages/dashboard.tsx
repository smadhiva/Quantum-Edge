import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { Plus, TrendingUp, TrendingDown, Search } from 'lucide-react';
import { portfolioAPI } from '@/services/api';
import PortfolioSummary from '@/components/PortfolioSummary';
import MarketOverview from '@/components/MarketOverview';
import NewsFeed from '@/components/NewsFeed';
import ChatWidget from '@/components/ChatWidget';

interface DashboardStats {
  total_value: number;
  total_gain_loss: number;
  total_gain_loss_percent: number;
  day_change: number;
  day_change_percent: number;
  portfolios_count: number;
}

export default function Dashboard() {
  const [portfolios, setPortfolios] = useState<any[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      const data = await portfolioAPI.getAll();
      setPortfolios(data);
      
      // Calculate aggregate stats
      const totalValue = data.reduce((sum: number, p: any) => sum + (p.total_value || 0), 0);
      const totalGainLoss = data.reduce((sum: number, p: any) => sum + (p.total_gain_loss || 0), 0);
      const dayChange = data.reduce((sum: number, p: any) => sum + (p.day_change || 0), 0);
      
      setStats({
        total_value: totalValue,
        total_gain_loss: totalGainLoss,
        total_gain_loss_percent: totalValue > 0 ? (totalGainLoss / totalValue) * 100 : 0,
        day_change: dayChange,
        day_change_percent: totalValue > 0 ? (dayChange / totalValue) * 100 : 0,
        portfolios_count: data.length,
      });
    } catch (error) {
      console.error('Error loading dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredPortfolios = portfolios.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-500 border-t-transparent"></div>
      </div>
    );
  }

  const isPositive = (stats?.total_gain_loss || 0) >= 0;
  const isDayPositive = (stats?.day_change || 0) >= 0;

  return (
    <>
      <Head>
        <title>Dashboard | Finance Copilot</title>
      </Head>
      
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
          <p className="text-gray-500">Overview of your investment portfolios</p>
        </div>
        
        <Link href="/portfolio/create" className="btn btn-primary">
          <Plus className="w-4 h-4 mr-2" />
          New Portfolio
        </Link>
      </div>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="card bg-gradient-to-br from-primary-600 to-primary-700 text-white">
          <p className="text-sm opacity-80">Total Portfolio Value</p>
          <p className="text-3xl font-bold mt-1">
            ${(stats?.total_value || 0).toLocaleString()}
          </p>
          <p className="text-sm opacity-80 mt-2">
            {stats?.portfolios_count || 0} portfolios
          </p>
        </div>
        
        <div className="card">
          <p className="text-sm text-gray-500">Total Gain/Loss</p>
          <p className={`text-2xl font-bold mt-1 ${isPositive ? 'text-positive' : 'text-negative'}`}>
            {isPositive ? '+' : ''}${(stats?.total_gain_loss || 0).toLocaleString()}
          </p>
          <p className={`text-sm ${isPositive ? 'text-positive' : 'text-negative'}`}>
            {isPositive ? '+' : ''}{(stats?.total_gain_loss_percent || 0).toFixed(2)}%
          </p>
        </div>
        
        <div className="card">
          <p className="text-sm text-gray-500">Today's Change</p>
          <div className="flex items-center gap-2 mt-1">
            {isDayPositive ? (
              <TrendingUp className="w-6 h-6 text-positive" />
            ) : (
              <TrendingDown className="w-6 h-6 text-negative" />
            )}
            <p className={`text-2xl font-bold ${isDayPositive ? 'text-positive' : 'text-negative'}`}>
              {isDayPositive ? '+' : ''}{(stats?.day_change_percent || 0).toFixed(2)}%
            </p>
          </div>
        </div>
        
        <div className="card">
          <p className="text-sm text-gray-500">Portfolios</p>
          <p className="text-2xl font-bold mt-1 text-gray-800">
            {stats?.portfolios_count || 0}
          </p>
          <p className="text-sm text-gray-500">active portfolios</p>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Portfolios */}
        <div className="lg:col-span-2 space-y-6">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search portfolios..."
              className="input pl-10"
            />
          </div>
          
          {/* Portfolios List */}
          {filteredPortfolios.length > 0 ? (
            <PortfolioSummary portfolios={filteredPortfolios} />
          ) : portfolios.length === 0 ? (
            <div className="card text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Plus className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">No portfolios yet</h3>
              <p className="text-gray-500 mb-4">Create your first portfolio to get started</p>
              <Link href="/portfolio/create" className="btn btn-primary">
                Create Portfolio
              </Link>
            </div>
          ) : (
            <div className="card text-center py-8">
              <p className="text-gray-500">No portfolios match your search</p>
            </div>
          )}
          
          {/* Market Overview */}
          <MarketOverview />
        </div>
        
        {/* Right Column - News */}
        <div className="space-y-6">
          <NewsFeed />
        </div>
      </div>
      
      {/* Chat Widget */}
      <ChatWidget />
    </>
  );
}
