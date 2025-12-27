import { useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import { ArrowLeft, Plus, Upload, Check } from 'lucide-react';
import Link from 'next/link';
import { portfolioAPI } from '@/services/api';

interface StockInput {
  symbol: string;
  name: string;
  asset_type: string;
  quantity: string;
  price: string;
}

export default function CreatePortfolio() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Portfolio details
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  
  // Stock inputs
  const [stocks, setStocks] = useState<StockInput[]>([
    { symbol: '', name: '', asset_type: 'stock', quantity: '', price: '' }
  ]);
  
  // CSV import
  const [csvFile, setCsvFile] = useState<File | null>(null);

  const handleAddStock = () => {
    setStocks([...stocks, { symbol: '', name: '', asset_type: 'stock', quantity: '', price: '' }]);
  };

  const handleRemoveStock = (index: number) => {
    if (stocks.length > 1) {
      setStocks(stocks.filter((_, i) => i !== index));
    }
  };

  const handleStockChange = (index: number, field: keyof StockInput, value: string) => {
    const updated = [...stocks];
    updated[index][field] = value;
    setStocks(updated);
  };

  const handleCreatePortfolio = async () => {
    if (!name.trim()) {
      setError('Portfolio name is required');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      // Create portfolio
      const portfolio = await portfolioAPI.create({ name, description });
      
      // Add stocks if any
      const validStocks = stocks.filter(s => s.symbol && s.quantity && s.price);
      for (const stock of validStocks) {
        await portfolioAPI.addTransaction(portfolio.id, {
          symbol: stock.symbol.toUpperCase(),
          name: stock.name || stock.symbol.toUpperCase(),
          asset_type: stock.asset_type,
          transaction_type: 'buy',
          quantity: parseFloat(stock.quantity),
          price: parseFloat(stock.price),
        });
      }
      
      // Import CSV if provided
      if (csvFile) {
        await portfolioAPI.importCsv(portfolio.id, csvFile);
      }
      
      // Redirect to portfolio page
      router.push(`/portfolio/${portfolio.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create portfolio');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Create Portfolio | Finance Copilot</title>
      </Head>
      
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link 
            href="/portfolio"
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-800">Create New Portfolio</h1>
            <p className="text-gray-500">Set up a new investment portfolio</p>
          </div>
        </div>
        
        {/* Progress Steps */}
        <div className="flex items-center gap-4 mb-8">
          {[1, 2, 3].map((s) => (
            <div key={s} className="flex items-center">
              <div 
                className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  step >= s 
                    ? 'bg-primary-600 text-white' 
                    : 'bg-gray-200 text-gray-500'
                }`}
              >
                {step > s ? <Check className="w-5 h-5" /> : s}
              </div>
              {s < 3 && (
                <div className={`w-20 h-1 ml-2 ${step > s ? 'bg-primary-600' : 'bg-gray-200'}`}></div>
              )}
            </div>
          ))}
        </div>
        
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-600 rounded-lg">
            {error}
          </div>
        )}
        
        {/* Step 1: Portfolio Details */}
        {step === 1 && (
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-800 mb-6">Portfolio Details</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Portfolio Name *
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="input"
                  placeholder="e.g., Tech Growth Portfolio"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (Optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="input min-h-[100px]"
                  placeholder="Describe the investment strategy or goals for this portfolio..."
                />
              </div>
            </div>
            
            <div className="mt-8 flex justify-end">
              <button
                onClick={() => setStep(2)}
                disabled={!name.trim()}
                className="btn btn-primary"
              >
                Continue
              </button>
            </div>
          </div>
        )}
        
        {/* Step 2: Add Holdings */}
        {step === 2 && (
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-800 mb-6">Add Holdings</h2>
            
            {/* Manual Input */}
            <div className="space-y-4 mb-6">
              {stocks.map((stock, index) => (
                <div key={index} className="flex gap-3 items-start">
                  <div className="flex-1 grid grid-cols-5 gap-3">
                    <input
                      type="text"
                      value={stock.symbol}
                      onChange={(e) => handleStockChange(index, 'symbol', e.target.value)}
                      className="input"
                      placeholder="Symbol"
                    />
                    <input
                      type="text"
                      value={stock.name}
                      onChange={(e) => handleStockChange(index, 'name', e.target.value)}
                      className="input"
                      placeholder="Name"
                    />
                    <select
                      value={stock.asset_type}
                      onChange={(e) => handleStockChange(index, 'asset_type', e.target.value)}
                      className="input"
                    >
                      <option value="stock">Stock</option>
                      <option value="etf">ETF</option>
                      <option value="mutual_fund">Mutual Fund</option>
                      <option value="crypto">Crypto</option>
                      <option value="bond">Bond</option>
                    </select>
                    <input
                      type="number"
                      value={stock.quantity}
                      onChange={(e) => handleStockChange(index, 'quantity', e.target.value)}
                      className="input"
                      placeholder="Qty"
                    />
                    <input
                      type="number"
                      value={stock.price}
                      onChange={(e) => handleStockChange(index, 'price', e.target.value)}
                      className="input"
                      placeholder="Price"
                    />
                  </div>
                  <button
                    onClick={() => handleRemoveStock(index)}
                    className="p-2 text-gray-400 hover:text-red-500"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
            
            <button
              onClick={handleAddStock}
              className="btn btn-secondary mb-6"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Another Stock
            </button>
            
            {/* CSV Import */}
            <div className="border-t pt-6">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Or Import from CSV</h3>
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                  className="hidden"
                  id="csv-upload"
                />
                <label htmlFor="csv-upload" className="cursor-pointer">
                  <Upload className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                  {csvFile ? (
                    <p className="text-primary-600 font-medium">{csvFile.name}</p>
                  ) : (
                    <p className="text-gray-500">Click to upload CSV file</p>
                  )}
                </label>
              </div>
              <p className="text-xs text-gray-400 mt-2">
                CSV should have columns: symbol, name, asset_type, quantity, price
              </p>
            </div>
            
            <div className="mt-8 flex justify-between">
              <button
                onClick={() => setStep(1)}
                className="btn btn-secondary"
              >
                Back
              </button>
              <button
                onClick={() => setStep(3)}
                className="btn btn-primary"
              >
                Continue
              </button>
            </div>
          </div>
        )}
        
        {/* Step 3: Review & Create */}
        {step === 3 && (
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-800 mb-6">Review & Create</h2>
            
            <div className="space-y-4 mb-8">
              <div className="flex justify-between p-4 bg-gray-50 rounded-lg">
                <span className="text-gray-600">Portfolio Name</span>
                <span className="font-semibold">{name}</span>
              </div>
              
              {description && (
                <div className="flex justify-between p-4 bg-gray-50 rounded-lg">
                  <span className="text-gray-600">Description</span>
                  <span className="font-semibold">{description}</span>
                </div>
              )}
              
              <div className="flex justify-between p-4 bg-gray-50 rounded-lg">
                <span className="text-gray-600">Holdings</span>
                <span className="font-semibold">
                  {stocks.filter(s => s.symbol && s.quantity && s.price).length} stocks
                  {csvFile && ' + CSV import'}
                </span>
              </div>
              
              {stocks.filter(s => s.symbol).length > 0 && (
                <div className="p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Holdings to add:</p>
                  <div className="flex flex-wrap gap-2">
                    {stocks.filter(s => s.symbol).map((stock, i) => (
                      <span key={i} className="badge badge-info">
                        {stock.symbol.toUpperCase()}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="mt-8 flex justify-between">
              <button
                onClick={() => setStep(2)}
                className="btn btn-secondary"
              >
                Back
              </button>
              <button
                onClick={handleCreatePortfolio}
                disabled={loading}
                className="btn btn-primary"
              >
                {loading ? 'Creating...' : 'Create Portfolio'}
              </button>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
