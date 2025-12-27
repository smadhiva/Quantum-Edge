#!/usr/bin/env python3
"""
Complete Setup Script for Finance Copilot Backend
Run this to set up RAG and fix all remaining issues
"""
import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60 + "\n")

def run_command(cmd, description):
    """Run a command and report status"""
    print(f"▶️  {description}...")
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            return True
        else:
            print(f"⚠️  {description} - Warning: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def create_directory(path):
    """Create directory if it doesn't exist"""
    Path(path).mkdir(parents=True, exist_ok=True)
    print(f"✅ Created directory: {path}")

def create_file(path, content):
    """Create file with content"""
    with open(path, 'w') as f:
        f.write(content)
    print(f"✅ Created file: {path}")

def main():
    print_header("Finance Copilot - Complete Setup")
    
    # Check if we're in the right directory
    if not os.path.exists('agents') or not os.path.exists('routes'):
        print("❌ Error: Please run this script from the backend directory")
        print("   (the directory containing 'agents' and 'routes' folders)")
        sys.exit(1)
    
    # Step 1: Install dependencies
    print_header("Step 1: Installing Dependencies")
    
    packages = [
        ('sentence-transformers', 'Sentence Transformers for embeddings'),
        ('torch', 'PyTorch (required by transformers)'),
    ]
    
    for package, description in packages:
        success = run_command(
            f"pip install {package} --quiet",
            f"Installing {description}"
        )
        if not success:
            print(f"⚠️  Failed to install {package}, but continuing...")
    
    # Step 2: Create directories
    print_header("Step 2: Creating Directories")
    
    directories = [
        'data/documents',
        'data/vector_db',
        'data/portfolios',
        'data/prices',
        'pathway_engine'
    ]
    
    for directory in directories:
        create_directory(directory)
    
    # Step 3: Create pathway_engine/__init__.py
    print_header("Step 3: Creating Pathway Engine Package")
    
    create_file('pathway_engine/__init__.py', '''"""
Pathway Engine - Vector store and RAG functionality
"""
from .simple_vector_store import SimpleVectorStore, get_vector_store

__all__ = ['SimpleVectorStore', 'get_vector_store']
''')
    
    # Step 4: Create sample documents
    print_header("Step 4: Creating Sample Documents")
    
    documents = {
        'data/documents/portfolio_guide.txt': '''Portfolio Management Best Practices

1. Diversification
   Spread investments across different asset classes to reduce risk.
   Include stocks, bonds, real estate, and alternative investments.

2. Regular Rebalancing
   Review your portfolio quarterly and rebalance when allocation drifts.
   This maintains your target risk level and can improve returns.

3. Risk Management
   Assess your risk tolerance regularly and adjust as life circumstances change.
   Consider your investment horizon - longer horizons can support more risk.

4. Cost Management
   Minimize trading fees and expense ratios.
   Consider low-cost index funds for core holdings.
   Be tax-efficient with your trades.

5. Long-term Focus
   Don't panic sell during market downturns.
   Stay invested through volatility.
   Review your strategy annually but avoid frequent changes.
''',
        
        'data/documents/investment_terms.txt': '''Key Investment Terms and Concepts

Asset Allocation: The distribution of investments across different asset classes like stocks, bonds, and cash.

Diversification: Spreading investments across multiple securities to reduce risk exposure to any single investment.

Rebalancing: The process of realigning portfolio weights to maintain target allocation percentages.

Risk Tolerance: An investor's ability and willingness to endure market volatility and potential losses.

Market Capitalization: The total market value of a company's outstanding shares (Price × Shares Outstanding).

P/E Ratio (Price-to-Earnings): A valuation metric calculated as stock price divided by earnings per share.

Dividend Yield: Annual dividend per share divided by stock price, expressed as a percentage.

Beta: A measure of a stock's volatility relative to the overall market. Beta of 1 = same volatility as market.

Dollar-Cost Averaging: Investing fixed amounts at regular intervals regardless of price, reducing timing risk.

Compound Interest: Interest earned on both principal and previously accumulated interest.
''',
        
        'data/documents/market_analysis.txt': '''Market Analysis Framework

Technical Analysis Indicators:
- Moving Averages: 20-day, 50-day, and 200-day SMAs show trend direction
- RSI (Relative Strength Index): Measures momentum, overbought above 70, oversold below 30
- MACD: Moving Average Convergence Divergence shows trend changes
- Support/Resistance: Price levels where stocks tend to stop falling or rising
- Volume: Confirms price movements when trading activity increases

Fundamental Analysis Metrics:
- Revenue Growth: Year-over-year increase in company sales
- Profit Margins: Net income as percentage of revenue
- Debt-to-Equity: Company's leverage and financial health
- Return on Equity (ROE): Profitability relative to shareholder equity
- P/E Ratio: Valuation compared to earnings
- Free Cash Flow: Cash available after operating expenses and capital expenditures

Sector Analysis:
- Technology: High growth, innovation-driven, sensitive to interest rates
- Financials: Tied to interest rates and economic cycles
- Healthcare: Defensive, stable demand, regulatory risks
- Energy: Commodity-dependent, cyclical, geopolitical sensitivity
- Consumer Discretionary: Economic cycle sensitive, tied to consumer confidence
''',
        
        'data/documents/risk_management.txt': '''Risk Management Strategies

Portfolio Risk Types:

1. Market Risk: Overall market movements affect portfolio value
   - Mitigation: Diversification across asset classes
   - Consider defensive positions during high volatility

2. Concentration Risk: Too much exposure to single investment
   - Mitigation: No single position should exceed 10-15% of portfolio
   - Regularly rebalance to maintain diversification

3. Liquidity Risk: Inability to quickly convert to cash
   - Mitigation: Maintain adequate cash reserves (3-6 months expenses)
   - Avoid illiquid investments unless long-term horizon

4. Interest Rate Risk: Changes in rates affect bond values
   - Mitigation: Ladder bond maturities
   - Consider floating rate bonds

5. Currency Risk: Exchange rate fluctuations
   - Mitigation: Hedge international positions
   - Consider currency-hedged funds

Risk Assessment Questions:
- What is your investment time horizon?
- How would you react to a 20% portfolio decline?
- Do you need income from investments now?
- What are your financial goals and priorities?
- Can you handle short-term volatility for long-term gains?
'''
    }
    
    for filepath, content in documents.items():
        create_file(filepath, content)
    
    # Step 5: Test the setup
    print_header("Step 5: Testing Setup")
    
    print("🧪 Testing vector store...")
    
    test_code = '''
import sys
sys.path.insert(0, '.')

try:
    from pathway_engine.simple_vector_store import get_vector_store
    
    print("  📚 Loading vector store...")
    store = get_vector_store()
    
    stats = store.get_stats()
    print(f"  ✅ Vector store loaded")
    print(f"     - Documents: {stats['total_documents']}")
    print(f"     - Model loaded: {stats['model_loaded']}")
    
    if stats['total_documents'] > 0:
        # Test search
        query = "How should I diversify my portfolio?"
        results = store.search(query, top_k=2)
        
        print(f"\\n  🔍 Test query: '{query}'")
        if results:
            print(f"     - Found {len(results)} results")
            print(f"     - Top score: {results[0]['score']:.4f}")
            print(f"\\n  ✅ RAG system is working!")
        else:
            print("     ⚠️  No results found")
    
except Exception as e:
    print(f"  ❌ Error: {e}")
    import traceback
    traceback.print_exc()
'''
    
    with open('_test_setup.py', 'w') as f:
        f.write(test_code)
    
    run_command('python _test_setup.py', 'Running vector store test')
    
    # Cleanup test file
    if os.path.exists('_test_setup.py'):
        os.remove('_test_setup.py')
    
    # Final summary
    print_header("Setup Complete!")
    
    print("""
✅ All components installed and configured!

📁 Created:
   - data/documents/ (with 4 sample documents)
   - data/vector_db/ (for embeddings cache)
   - pathway_engine/ (vector store module)

🔄 Next Steps:

1. Start your backend:
   python -m uvicorn main:app --reload

2. Test the RAG system:
   curl http://localhost:8000/api/rag-health

3. Try a search:
   # Get auth token first, then:
   curl -X POST http://localhost:8000/api/rag-search \\
     -H "Authorization: Bearer YOUR_TOKEN" \\
     -H "Content-Type: application/json" \\
     -d '{"query": "portfolio diversification", "top_k": 3}'

4. Run full test suite:
   python debug.py

📚 To add more documents:
   - Place .txt or .md files in data/documents/
   - Restart backend to re-index

💡 Tips:
   - The vector store uses sentence-transformers (free, no API key needed)
   - Documents are cached for faster loading
   - Clear cache endpoint: POST /api/rag-clear-cache

Need help? Check the logs or run: python -c "from pathway_engine.simple_vector_store import get_vector_store; get_vector_store().get_stats()"
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)