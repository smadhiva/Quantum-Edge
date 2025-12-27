import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, RefreshCw } from 'lucide-react';

interface IndexData {
  name: string;
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
}

export default function MarketOverview() {
  const [indices, setIndices] = useState<IndexData[]>([
    { name: 'S&P 500', symbol: 'SPY', price: 478.45, change: 3.92, changePercent: 0.82 },
    { name: 'NASDAQ 100', symbol: 'QQQ', price: 412.65, change: 4.72, changePercent: 1.15 },
    { name: 'Dow Jones', symbol: 'DIA', price: 375.33, change: 1.69, changePercent: 0.45 },
    { name: 'Russell 2000', symbol: 'IWM', price: 198.45, change: -1.23, changePercent: -0.62 },
  ]);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const refreshData = () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIndices(indices.map(idx => ({
        ...idx,
        price: idx.price + (Math.random() - 0.5) * 2,
        change: (Math.random() - 0.5) * 5,
        changePercent: (Math.random() - 0.5) * 2
      })));
      setLastUpdate(new Date());
      setLoading(false);
    }, 500);
  };

  // Auto-refresh every 60 seconds
  useEffect(() => {
    const interval = setInterval(refreshData, 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <h2 className="card-title">Market Overview</h2>
          <p className="text-sm text-gray-500">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </div>
        <button 
          onClick={refreshData} 
          className={`p-2 hover:bg-gray-100 rounded-lg ${loading ? 'animate-spin' : ''}`}
          disabled={loading}
        >
          <RefreshCw className="w-5 h-5 text-gray-500" />
        </button>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {indices.map((index) => {
          const isPositive = index.changePercent >= 0;
          return (
            <div 
              key={index.symbol} 
              className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <p className="text-sm text-gray-500 mb-1">{index.name}</p>
              <p className="text-xl font-bold text-gray-800">
                ${index.price.toFixed(2)}
              </p>
              <div className={`flex items-center gap-1 mt-1 ${isPositive ? 'text-positive' : 'text-negative'}`}>
                {isPositive ? (
                  <TrendingUp className="w-4 h-4" />
                ) : (
                  <TrendingDown className="w-4 h-4" />
                )}
                <span className="text-sm font-medium">
                  {isPositive ? '+' : ''}{index.changePercent.toFixed(2)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
