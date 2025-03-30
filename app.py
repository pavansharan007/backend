from flask import Flask, jsonify
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import os

app = Flask(__name__)
CORS(app)
# ✅ 50 Indian and 50 US Stocks → 100 total
STOCKS = {
    "INDIA": [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
        "KOTAKBANK.NS", "HINDUNILVR.NS", "LT.NS", "BAJFINANCE.NS", "ITC.NS",
        "ASIANPAINT.NS", "SUNPHARMA.NS", "HCLTECH.NS", "WIPRO.NS", "MARUTI.NS",
        "ULTRACEMCO.NS", "ONGC.NS", "NTPC.NS", "POWERGRID.NS", "BHARTIARTL.NS",
        "SBIN.NS", "GRASIM.NS", "TITAN.NS", "HINDALCO.NS", "JSWSTEEL.NS",
        "COALINDIA.NS", "BPCL.NS", "INDUSINDBK.NS", "ADANIENT.NS", "ADANIPORTS.NS",
        "DRREDDY.NS", "CIPLA.NS", "APOLLOHOSP.NS", "BRITANNIA.NS", "TATAMOTORS.NS",
        "M&M.NS", "EICHERMOT.NS", "HEROMOTOCO.NS", "BAJAJ-AUTO.NS", "SHREECEM.NS",
        "DIVISLAB.NS", "UPL.NS", "TECHM.NS", "ZOMATO.NS", "DLF.NS",
        "GAIL.NS", "PNB.NS", "BANKBARODA.NS", "BHEL.NS", "IRCTC.NS"
    ],
    "US": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
        "META", "NVDA", "NFLX", "BRK-B", "JPM",
        "V", "MA", "PYPL", "DIS", "ADBE",
        "INTC", "CSCO", "PEP", "KO", "XOM",
        "WMT", "PFE", "NKE", "MCD", "IBM",
        "CRM", "ABNB", "SQ", "TWTR", "UBER",
        "LYFT", "ORCL", "AMD", "BA", "GE",
        "F", "GM", "LMT", "BABA", "JD",
        "SHOP", "SNAP", "ZM", "DOCU", "ROKU",
        "SPOT", "PLTR", "HOOD", "BYND", "PTON"
    ]
}

# ✅ Fetch stock data with price, score & country
def fetch_stock_data(symbol, country):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        current_price = info.get("currentPrice", 0) or 0
        pe_ratio = info.get('trailingPE', 0) or 0
        book_value = info.get('bookValue', 0) or 0
        debt_equity = info.get('debtToEquity', 0) or 0
        roe = info.get('returnOnEquity', 0) or 0
        roce = info.get('returnOnAssets', 0) or 0

        # ✅ Calculate recommended buy price
        recommended_buy_price = round(book_value * (1 + (pe_ratio / 10)), 2) if book_value > 0 and pe_ratio > 0 else 0

        # ✅ Calculate score with normalized range 1-10
        score = (
            (roe * 0.3) +           # ROE: 30%
            (roce * 0.25) -         # ROCE: 25%
            (pe_ratio * -0.2) -     # P/E: negative weight (lower is better)
            (debt_equity * 0.15) +  # Debt/Equity: 15%
            (book_value * 0.1)      # Book Value: 10%
        )

        # Normalize score between 1 and 10
        score_normalized = max(1, min(10, round((score + 5) / 10 * 10, 1)))

        return {
            "symbol": symbol,
            "country": "🇮🇳" if country == "INDIA" else "🇺🇸",
            "current_price": current_price,
            "recommended_buy_price": recommended_buy_price,
            "score": score_normalized
        }
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None

# ✅ Rank and normalize the stock data
def rank_stocks():
    stock_data = []

    for country, symbols in STOCKS.items():
        for symbol in symbols:
            data = fetch_stock_data(symbol, country)
            if data:
                stock_data.append(data)

    df = pd.DataFrame(stock_data)

    if df.empty:
        return [{"error": "No valid stock data fetched"}]

    # ✅ Add rank by score
    df['rank'] = df['score'].rank(ascending=False).astype(int)

    # ✅ Sort by rank
    df = df.sort_values('rank')

    return df.to_dict(orient='records')

# ✅ API endpoint
@app.route('/stocks', methods=['GET'])
def get_stocks():
    ranked_stocks = rank_stocks()
    return jsonify(ranked_stocks)

# ✅ Render Deployment Port
if __name__ == '__main__':
    PORT = int(os.environ.get("PORT", 5000))
    print(f"Running on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
