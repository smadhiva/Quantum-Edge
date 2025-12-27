import { useState, useEffect } from 'react';
import Link from 'next/link';
import { TrendingUp, TrendingDown, Plus, ArrowRight } from 'lucide-react';
import { api } from '@/services/api';

interface Portfolio {
  id: string;
  name: string;
  total_value: number;
  daily_change: number;
  daily_change_percent: number;
  holdings_count: number;
}

export default function PortfolioSummary() {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPortfolios();
  }, []);

  const loadPortfolios = async () => {
    try {
      const data = await api.listPortfolios();
      setPortfolios(data);
    } catch (error) {
      // Use demo data if API fails
      setPortfolios([
        { 
          id: 'demo-1', 
          name: 'Tech Growth', 
          total_value: 125000, 
          daily_change: 1250, 
          daily_change_percent: 1.01,
          holdings_count: 8
        },
        { 
          id: 'demo-2', 
          name: 'Dividend Income', 
          total_value: 75000, 
          daily_change: -375, 
          daily_change_percent: -0.5,
          holdings_count: 12
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="card">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-4">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const totalValue = portfolios.reduce((sum, p) => sum + p.total_value, 0);
  const totalChange = portfolios.reduce((sum, p) => sum + p.daily_change, 0);
  const totalChangePercent = totalValue > 0 ? (totalChange / totalValue) * 100 : 0;

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Your Portfolios</h2>
        <Link href="/portfolio/create" className="btn btn-primary btn-sm flex items-center gap-1">
          <Plus className="w-4 h-4" />
          New
        </Link>
      </div>

      {/* Total Summary */}
      <div className="p-4 bg-gradient-to-r from-primary-600 to-primary-700 rounded-lg text-white mb-6">
        <p className="text-sm opacity-80 mb-1">Total Portfolio Value</p>
        <p className="text-3xl font-bold">${totalValue.toLocaleString()}</p>
        <div className={`flex items-center gap-1 mt-2 ${totalChange >= 0 ? 'text-green-300' : 'text-red-300'}`}>
          {totalChange >= 0 ? (
            <TrendingUp className="w-4 h-4" />
          ) : (
            <TrendingDown className="w-4 h-4" />
          )}
          <span className="text-sm font-medium">
            {totalChange >= 0 ? '+' : ''}${totalChange.toLocaleString()} ({totalChangePercent.toFixed(2)}%) today
          </span>
        </div>
      </div>

      {/* Portfolio List */}
      <div className="space-y-3">
        {portfolios.map((portfolio) => {
          const isPositive = portfolio.daily_change >= 0;
          return (
            <Link 
              key={portfolio.id} 
              href={`/portfolio/${portfolio.id}`}
              className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
            >
              <div>
                <p className="font-semibold text-gray-800">{portfolio.name}</p>
                <p className="text-sm text-gray-500">{portfolio.holdings_count} holdings</p>
              </div>
              <div className="text-right">
                <p className="font-semibold text-gray-800">${portfolio.total_value.toLocaleString()}</p>
                <p className={`text-sm ${isPositive ? 'text-positive' : 'text-negative'}`}>
                  {isPositive ? '+' : ''}{portfolio.daily_change_percent.toFixed(2)}%
                </p>
              </div>
              <ArrowRight className="w-5 h-5 text-gray-400 group-hover:text-primary-600 transition-colors" />
            </Link>
          );
        })}

        {portfolios.length === 0 && (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">No portfolios yet</p>
            <Link href="/portfolio/create" className="btn btn-primary">
              Create Your First Portfolio
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
