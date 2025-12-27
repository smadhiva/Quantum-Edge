import Link from 'next/link';
import { TrendingUp, TrendingDown, MoreVertical, Eye } from 'lucide-react';

interface Holding {
  symbol: string;
  name: string;
  asset_type: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  current_value: number;
  gain_loss: number;
  gain_loss_percent: number;
  weight: number;
}

interface StockCardProps {
  holding: Holding;
  portfolioId: string;
}

export default function StockCard({ holding, portfolioId }: StockCardProps) {
  const isPositive = holding.gain_loss >= 0;

  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group">
      <div className="flex items-center gap-4">
        {/* Stock Icon */}
        <div className="w-12 h-12 bg-white rounded-lg shadow-sm flex items-center justify-center font-bold text-primary-600">
          {holding.symbol.slice(0, 2)}
        </div>
        
        {/* Stock Info */}
        <div>
          <div className="flex items-center gap-2">
            <p className="font-semibold text-gray-800">{holding.symbol}</p>
            <span className="badge badge-info">{holding.asset_type}</span>
          </div>
          <p className="text-sm text-gray-500">{holding.name}</p>
          <p className="text-xs text-gray-400">
            {holding.quantity} shares @ ${holding.average_cost.toFixed(2)}
          </p>
        </div>
      </div>
      
      {/* Price & Change */}
      <div className="text-right">
        <p className="text-lg font-semibold text-gray-800">
          ${holding.current_value.toLocaleString()}
        </p>
        <p className="text-sm text-gray-500">
          ${holding.current_price.toFixed(2)} / share
        </p>
        <div className={`flex items-center justify-end gap-1 ${isPositive ? 'text-positive' : 'text-negative'}`}>
          {isPositive ? (
            <TrendingUp className="w-4 h-4" />
          ) : (
            <TrendingDown className="w-4 h-4" />
          )}
          <span className="text-sm font-medium">
            {isPositive ? '+' : ''}${holding.gain_loss.toFixed(2)} ({isPositive ? '+' : ''}{holding.gain_loss_percent.toFixed(2)}%)
          </span>
        </div>
      </div>
      
      {/* Actions */}
      <div className="flex items-center gap-2 ml-4">
        <Link 
          href={`/stock/${holding.symbol}`}
          className="p-2 hover:bg-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Eye className="w-4 h-4 text-gray-500" />
        </Link>
        <button className="p-2 hover:bg-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity">
          <MoreVertical className="w-4 h-4 text-gray-500" />
        </button>
      </div>
      
      {/* Weight Bar */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 rounded-b-lg overflow-hidden">
        <div 
          className="h-full bg-primary-500"
          style={{ width: `${holding.weight}%` }}
        ></div>
      </div>
    </div>
  );
}
