import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { 
  ArrowLeft, 
  TrendingUp, 
  TrendingDown, 
  Wallet,
  Download,
  RefreshCw,
  Plus,
  Settings,
  BarChart2
} from 'lucide-react';
import api, { portfolioAPI, analysisAPI } from '@/services/api';
import StockCard from '@/components/StockCard';
import AllocationChart from '@/components/AllocationChart';

export default function PortfolioDetail() {
  const router = useRouter();
  const { id } = router.query;
  
  const [portfolio, setPortfolio] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analysis, setAnalysis] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);

  useEffect(() => {
    if (id) {
      loadPortfolio();
    }
  }, [id]);

  const loadPortfolio = async () => {
    try {
      setLoading(true);
      const data = await portfolioAPI.getById(id as string);
      setPortfolio(data);
    } catch (error) {
      console.error('Error loading portfolio:', error);
    } finally {
      setLoading(false);
    }
  };

  const runAnalysis = async () => {
    try {
      setAnalyzing(true);
      const data = await analysisAPI.analyzeStock('', id as string);
      setAnalysis(data);
    } catch (error) {
      console.error('Error analyzing portfolio:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const exportCSV = async () => {
    try {
      const blob = await portfolioAPI.exportCsv(id as string);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `portfolio_${id}.csv`;
      a.click();
    } catch (error) {
      console.error('Error exporting:', error);
    }
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ width: 48, height: 48, borderRadius: '50%', borderBottom: '4px solid var(--color-violet)', borderLeft: '4px solid transparent', animation: 'spin 1s linear infinite' }} />
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div style={{ maxWidth: 600, margin: '48px auto', padding: 32 }}>
        <div style={{ textAlign: 'center' }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 16, color: 'var(--color-white)' }}>Portfolio Not Found</h1>
          <Link href="/" style={{ background: 'var(--color-violet)', color: 'var(--color-white)', padding: '10px 24px', borderRadius: 8, textDecoration: 'none', fontWeight: 600 }}>Go Back</Link>
        </div>
      </div>
    );
  }

  const isPositive = portfolio.total_gain_loss >= 0;

  return (
    <>
      <Head>
        <title>{portfolio.name} - Finance Portfolio Copilot</title>
      </Head>
      
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: 32 }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 32 }}>
          <Link href="/" style={{ padding: 8, borderRadius: 8, background: 'var(--color-bg-alt)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ArrowLeft style={{ width: 20, height: 20, color: 'var(--color-violet)' }} />
          </Link>
          <div style={{ flex: 1 }}>
            <h1 style={{ fontSize: 28, fontWeight: 700, color: 'var(--color-white)' }}>{portfolio.name}</h1>
            {portfolio.description && (
              <p style={{ color: 'var(--color-text-muted)' }}>{portfolio.description}</p>
            )}
          </div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={loadPortfolio} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <RefreshCw style={{ width: 16, height: 16 }} />
              Refresh
            </button>
            <button onClick={exportCSV} className="btn btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Download style={{ width: 16, height: 16 }} />
              Export
            </button>
            <button onClick={runAnalysis} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 8 }} disabled={analyzing}>
              <BarChart2 style={{ width: 16, height: 16 }} />
              {analyzing ? 'Analyzing...' : 'Analyze'}
            </button>
          </div>
        </div>
        
        {/* Portfolio Summary Cards */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
          {/* Total Value */}
          <div className="card" style={{ borderRadius: 16, background: 'var(--color-bg-alt)', padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: 14, color: 'var(--color-text-muted)' }}>Total Value</p>
                <p style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-white)' }}>${portfolio.total_value.toLocaleString()}</p>
              </div>
              <div style={{ width: 48, height: 48, background: 'var(--color-violet-light)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Wallet style={{ width: 24, height: 24, color: 'var(--color-violet)' }} />
              </div>
            </div>
          </div>
          {/* Total Invested */}
          <div className="card" style={{ borderRadius: 16, background: 'var(--color-bg-alt)', padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: 14, color: 'var(--color-text-muted)' }}>Total Invested</p>
                <p style={{ fontSize: 24, fontWeight: 700, color: 'var(--color-white)' }}>${portfolio.total_invested.toLocaleString()}</p>
              </div>
              <div style={{ width: 48, height: 48, background: 'var(--color-bg)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Plus style={{ width: 24, height: 24, color: 'var(--color-white)' }} />
              </div>
            </div>
          </div>
          {/* Total Gain/Loss */}
          <div className="card" style={{ borderRadius: 16, background: 'var(--color-bg-alt)', padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: 14, color: 'var(--color-text-muted)' }}>Total Gain/Loss</p>
                <p style={{ fontSize: 24, fontWeight: 700, color: isPositive ? 'var(--color-positive)' : 'var(--color-negative)' }}>
                  {isPositive ? '+' : ''}${portfolio.total_gain_loss.toLocaleString()}
                </p>
              </div>
              <div style={{ width: 48, height: 48, background: isPositive ? 'var(--color-positive-bg)' : 'var(--color-negative-bg)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {isPositive ? (
                  <TrendingUp style={{ width: 24, height: 24, color: 'var(--color-positive)' }} />
                ) : (
                  <TrendingDown style={{ width: 24, height: 24, color: 'var(--color-negative)' }} />
                )}
              </div>
            </div>
          </div>
          {/* Return */}
          <div className="card" style={{ borderRadius: 16, background: 'var(--color-bg-alt)', padding: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div>
                <p style={{ fontSize: 14, color: 'var(--color-text-muted)' }}>Return</p>
                <p style={{ fontSize: 24, fontWeight: 700, color: isPositive ? 'var(--color-positive)' : 'var(--color-negative)' }}>
                  {isPositive ? '+' : ''}{portfolio.total_gain_loss_percent.toFixed(2)}%
                </p>
              </div>
              <div style={{ width: 48, height: 48, background: isPositive ? 'var(--color-positive-bg)' : 'var(--color-negative-bg)', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {isPositive ? (
                  <TrendingUp style={{ width: 24, height: 24, color: 'var(--color-positive)' }} />
                ) : (
                  <TrendingDown style={{ width: 24, height: 24, color: 'var(--color-negative)' }} />
                )}
              </div>
            </div>
          </div>
        </div>
        
        {/* Main Content */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 32 }}>
          {/* Holdings List */}
          <div>
            <div className="card" style={{ marginBottom: 24, borderRadius: 16, background: 'var(--color-bg-alt)', padding: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
                <h2 style={{ fontSize: 20, fontWeight: 600, color: 'var(--color-white)' }}>Holdings ({portfolio.holdings.length})</h2>
                <Link href={`/portfolio/${id}/add`} className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 14, padding: '6px 16px' }}>
                  <Plus style={{ width: 16, height: 16 }} />
                  Add
                </Link>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                {portfolio.holdings.map((holding: any, index: number) => (
                  <StockCard key={index} holding={holding} portfolioId={id as string} />
                ))}
                {portfolio.holdings.length === 0 && (
                  <div style={{ textAlign: 'center', padding: '32px 0', color: 'var(--color-text-muted)' }}>
                    <p>No holdings yet. Add your first stock!</p>
                  </div>
                )}
              </div>
            </div>
          </div>
          {/* Allocation Chart & Analysis */}
          <div>
            <div className="card" style={{ marginBottom: 24, borderRadius: 16, background: 'var(--color-bg-alt)', padding: 24 }}>
              <h2 style={{ fontSize: 20, fontWeight: 600, color: 'var(--color-white)', marginBottom: 16 }}>Asset Allocation</h2>
              <AllocationChart data={portfolio.allocation} />
            </div>
            {/* Analysis Results */}
            {analysis && (
              <div className="card" style={{ borderRadius: 16, background: 'var(--color-bg-alt)', padding: 24 }}>
                <h2 style={{ fontSize: 20, fontWeight: 600, color: 'var(--color-white)', marginBottom: 16 }}>AI Analysis</h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  {/* Risk Score */}
                  {analysis.risk_assessment && (
                    <div>
                      <p style={{ fontSize: 14, color: 'var(--color-text-muted)', marginBottom: 4 }}>Risk Score</p>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <div style={{ flex: 1, background: 'var(--color-bg)', borderRadius: 8, height: 8 }}>
                          <div 
                            style={{ background: 'var(--color-violet)', height: 8, borderRadius: 8, width: `${(analysis.risk_assessment.risk_score || 5) * 10}%` }}
                          ></div>
                        </div>
                        <span style={{ fontSize: 14, fontWeight: 500, color: 'var(--color-white)' }}>{analysis.risk_assessment.risk_score}/10</span>
                      </div>
                    </div>
                  )}
                  {/* Recommendations */}
                  {analysis.recommendations && analysis.recommendations.length > 0 && (
                    <div>
                      <p style={{ fontSize: 14, color: 'var(--color-text-muted)', marginBottom: 8 }}>Recommendations</p>
                      <ul style={{ display: 'flex', flexDirection: 'column', gap: 8, margin: 0, padding: 0, listStyle: 'none' }}>
                        {analysis.recommendations.slice(0, 3).map((rec: string, idx: number) => (
                          <li key={idx} style={{ fontSize: 14, color: 'var(--color-white)', display: 'flex', alignItems: 'flex-start', gap: 8 }}>
                            <span style={{ color: 'var(--color-violet)' }}>•</span>
                            {rec}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
