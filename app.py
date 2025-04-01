from flask import Flask, jsonify
from flask_cors import CORS
from flask_caching import Cache
import yfinance as yf
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

# Configure cache
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # Cache for 5 minutes
cache = Cache(app)

# ✅ List of 100 Stocks (Indian + US)
STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "KOTAKBANK.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "ITC.NS",
    "ASIANPAINT.NS", "SUNPHARMA.NS", "HCLTECH.NS", "WIPRO.NS", "MARUTI.NS",
    "ULTRACEMCO.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "BHARTIARTL.NS",
    "SBIN.NS", "GRASIM.NS", "TITAN.NS", "HINDALCO.NS", "JSWSTEEL.NS",
    "COALINDIA.NS", "BPCL.NS", "INDUSINDBK.NS", "ADANIENT.NS", "ADANIPORTS.NS",
    "DRREDDY.NS", "CIPLA.NS", "APOLLOHOSP.NS", "BRITANNIA.NS", "TATAMOTORS.NS",
    "M&M.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "SHREECEM.NS",
    "DIVISLAB.NS", "UPL.NS", "TECHM.NS", "ZOMATO.NS", "DLF.NS",
    "GAIL.NS", "PNB.NS", "BANKBARODA.NS", "BHEL.NS", "IRCTC.NS",
    # US Stocks
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NFLX", "NVDA", "BABA", "PYPL",
    "V", "JNJ", "PG", "HD", "DIS", "MA", "XOM", "PFE", "KO", "PEP",
    "MRNA", "AMD", "INTC", "WMT", "CRM", "ADBE", "NKE", "COST", "ORCL", "BA",
    "IBM", "GE", "F", "T", "GM", "CAT", "LMT", "MMM", "CVX", "CSCO"
]

# ✅ Function to fetch real-time stock data with caching
@cache.cached(timeout=300, key_prefix='stock_data')
def fetch_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        current_price = info.get('currentPrice', 0) or 0
        book_value = info.get('bookValue', 0) or 0
        roe = info.get('returnOnEquity', 0) or 0
        roce = info.get('returnOnAssets', 0) or 0  # Using ROA as ROCE proxy
        pe_ratio = info.get('trailingPE', 0) or 0
        debt_equity = info.get('debtToEquity', 0) or 0
        country = "India" if ".NS" in symbol else "USA"
        
        # ✅ Recommended buy price logic
        recommended_buy_price = current_price * 0.9  # 10% below current price
        
        data = {
            "symbol": symbol,
            "country": country,
            "current_price": current_price,
            "recommended_buy_price": recommended_buy_price,
            "roe": roe,
            "roce": roce,
            "pe_ratio": pe_ratio,
            "debt_equity": debt_equity,
            "book_value": book_value
        }
        return data
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# ✅ Function to rank stocks based on various criteria
def rank_stocks():
    stock_data = [fetch_stock_data(symbol) for symbol in STOCKS]
    stock_data = [data for data in stock_data if data]
    df = pd.DataFrame(stock_data)

    if df.empty:
        return [{"error": "No valid stock data fetched"}]

    # ✅ Scoring Algorithm
    df['raw_score'] = (
        (df['roe'] * 0.3) +           # ROE weight: 30%
        (df['roce'] * 0.25) -         # ROCE weight: 25%
        (df['pe_ratio'] * -0.2) -     # P/E: lower is better (negative weight)
        (df['debt_equity'] * 0.15) +  # Debt/Equity weight: 15%
        (df['book_value'] * 0.1)      # Book Value weight: 10%
    )

    # ✅ Normalize scores to range [1, 10]
    min_score = df['raw_score'].min()
    max_score = df['raw_score'].max()
    df['score'] = 1 + ((df['raw_score'] - min_score) / (max_score - min_score)) * 9

    # ✅ Sort by score (higher = better)
    df = df.sort_values('score', ascending=False)

    # ✅ Convert to list of dicts
    ranked_stocks = df.to_dict(orient='records')
    return ranked_stocks

# ✅ API endpoint to get ranked stocks
@app.route('/stocks', methods=['GET'])
def get_stocks():
    ranked_stocks = rank_stocks()
    return jsonify(ranked_stocks)

# ✅ Port Binding for Render Deployment
if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 5000))  # Use Render's port
    app.run(host='0.0.0.0', port=PORT, debug=True)
