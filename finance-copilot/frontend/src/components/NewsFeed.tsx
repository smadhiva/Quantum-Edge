import { useState, useEffect } from 'react';
import { ExternalLink, RefreshCw } from 'lucide-react';

interface NewsItem {
  title: string;
  source: string;
  url: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  published_at: string;
}

export default function NewsFeed() {
  const [news, setNews] = useState<NewsItem[]>([
    {
      title: "Tech stocks rally as Fed signals potential rate cuts",
      source: "Reuters",
      url: "#",
      sentiment: "positive",
      published_at: "2 hours ago"
    },
    {
      title: "Market volatility expected ahead of earnings season",
      source: "Bloomberg",
      url: "#",
      sentiment: "neutral",
      published_at: "3 hours ago"
    },
    {
      title: "Treasury yields drop to monthly lows",
      source: "CNBC",
      url: "#",
      sentiment: "positive",
      published_at: "4 hours ago"
    },
    {
      title: "Oil prices surge amid supply concerns",
      source: "MarketWatch",
      url: "#",
      sentiment: "negative",
      published_at: "5 hours ago"
    },
  ]);
  const [loading, setLoading] = useState(false);

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'bg-green-100 text-green-800';
      case 'negative': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const refreshNews = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 1000);
  };

  return (
    <div className="card h-full">
      <div className="card-header">
        <h2 className="card-title">Market News</h2>
        <button 
          onClick={refreshNews}
          className={`p-2 hover:bg-gray-100 rounded-lg ${loading ? 'animate-spin' : ''}`}
        >
          <RefreshCw className="w-4 h-4 text-gray-500" />
        </button>
      </div>
      
      <div className="space-y-4">
        {news.map((item, index) => (
          <a 
            key={index}
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-800 line-clamp-2 group-hover:text-primary-600 transition-colors">
                  {item.title}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <span className="text-xs text-gray-500">{item.source}</span>
                  <span className="text-xs text-gray-400">•</span>
                  <span className="text-xs text-gray-500">{item.published_at}</span>
                </div>
              </div>
              <div className="flex flex-col items-end gap-2">
                <span className={`badge ${getSentimentColor(item.sentiment)}`}>
                  {item.sentiment}
                </span>
                <ExternalLink className="w-4 h-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </div>
          </a>
        ))}
      </div>
      
      <div className="mt-4 pt-4 border-t">
        <a 
          href="/news" 
          className="text-sm text-primary-600 hover:text-primary-700 font-medium"
        >
          View all news →
        </a>
      </div>
    </div>
  );
}
