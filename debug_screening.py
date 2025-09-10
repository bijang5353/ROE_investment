#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from services.stock_screener import StockScreener

async def debug_screening():
    screener = StockScreener()
    print("Debug: Testing full screening process...")
    
    # 처음 5개 종목만 테스트
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    qualified_stocks = []
    for symbol in test_symbols:
        print(f"\n--- Testing {symbol} ---")
        try:
            result = await screener._analyze_stock_roe(symbol, 15.0, 5)
            if result:
                print(f"SUCCESS: {symbol} qualified - {result.company_name}")
                qualified_stocks.append(result)
            else:
                print(f"FAILED: {symbol} did not qualify")
        except Exception as e:
            print(f"ERROR testing {symbol}: {e}")
    
    print(f"\n=== FINAL RESULT ===")
    print(f"Qualified stocks: {len(qualified_stocks)}")
    for stock in qualified_stocks:
        print(f"  - {stock.symbol}: {stock.company_name}")

if __name__ == "__main__":
    asyncio.run(debug_screening())