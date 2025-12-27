import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { 
  TrendingUp, 
  TrendingDown, 
  Wallet, 
  PieChart, 
  Newspaper, 
  Bot,
  Plus,
  ArrowRight
} from 'lucide-react';
import MarketOverview from '@/components/MarketOverview';
import PortfolioSummary from '@/components/PortfolioSummary';
import NewsFeed from '@/components/NewsFeed';
import ChatWidget from '@/components/ChatWidget';

interface HomeProps {
  isAuthenticated: boolean;
}

export default function Home({ isAuthenticated }: HomeProps) {
  const [marketData, setMarketData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Simulate loading market data
    setTimeout(() => {
      setMarketData({
        indices: [
          { name: 'S&P 500', value: 4783.45, change: 0.82 },
          { name: 'NASDAQ', value: 15055.65, change: 1.15 },
          { name: 'DOW', value: 37545.33, change: 0.45 },
        ]
      });
      setLoading(false);
    }, 1000);
  }, []);

  if (!isAuthenticated) {
    return (
      <>
        <Head>
          <title>Finance Portfolio Copilot - AI Investment Intelligence</title>
        </Head>
        
        <div className="min-h-screen bg-gradient-to-br from-primary-600 to-primary-900">
          {/* Hero Section */}
          <div className="container mx-auto px-4 py-20">
            <div className="text-center text-white">
              <h1 className="text-5xl font-bold mb-6">
                💰 Finance Portfolio Copilot
              </h1>
              <p className="text-xl mb-8 opacity-90">
                Live, Multi-Threaded, Agentic Investment Intelligence
                <br />
                Powered by Pathway + Gemini LLM
              </p>
              
              <div className="flex justify-center gap-4 mb-16">
                <Link href="/login" className="btn btn-primary bg-white text-primary-700 hover:bg-gray-100 px-8 py-3 text-lg">
                  Get Started
                </Link>
                <Link href="/demo" className="btn border-2 border-white text-white hover:bg-white/10 px-8 py-3 text-lg">
                  View Demo
                </Link>
              </div>
              
              {/* Features Grid */}
              <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
                <div className="bg-white/10 backdrop-blur rounded-xl p-6 text-left">
                  <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                    <TrendingUp className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Live Market Data</h3>
                  <p className="opacity-80">
                    Real-time stock prices, news, and market trends streamed directly to your dashboard
                  </p>
                </div>
                
                <div className="bg-white/10 backdrop-blur rounded-xl p-6 text-left">
                  <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                    <Bot className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Multi-Agent Analysis</h3>
                  <p className="opacity-80">
                    10+ specialized AI agents analyze your portfolio from every angle
                  </p>
                </div>
                
                <div className="bg-white/10 backdrop-blur rounded-xl p-6 text-left">
                  <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center mb-4">
                    <PieChart className="w-6 h-6" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">Smart Recommendations</h3>
                  <p className="opacity-80">
                    Get actionable insights based on fundamentals, technicals, and sentiment
                  </p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Tech Stack */}
          <div className="bg-white/5 py-12">
            <div className="container mx-auto px-4">
              <p className="text-center text-white/60 mb-6">Powered by</p>
              <div className="flex justify-center items-center gap-12 text-white/80">
                <span className="text-lg font-semibold">🛤️ Pathway</span>
                <span className="text-lg font-semibold">🤖 Gemini</span>
                <span className="text-lg font-semibold">⚡ FastAPI</span>
                <span className="text-lg font-semibold">⚛️ React</span>
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Head>
        <title>Dashboard - Finance Portfolio Copilot</title>
      </Head>
      
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
            <p className="text-gray-500">Welcome back! Here's your portfolio overview.</p>
          </div>
          <Link href="/portfolio/create" className="btn btn-primary flex items-center gap-2">
            <Plus className="w-5 h-5" />
            New Portfolio
          </Link>
        </div>
        
        {/* Market Overview */}
        <div className="mb-8">
          <MarketOverview />
        </div>
        
        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-8">
          {/* Portfolio Summary - Takes 2 columns */}
          <div className="lg:col-span-2">
            <PortfolioSummary />
          </div>
          
          {/* News Feed - Takes 1 column */}
          <div>
            <NewsFeed />
          </div>
        </div>
        
        {/* Chat Widget */}
        <ChatWidget />
      </div>
    </>
  );
}
