#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from services.stock_screener import StockScreener

async def test_googl():
    screener = StockScreener()
    print("Testing Alphabet/Google (GOOGL)...")
    
    # ROE 히스토리 테스트
    print("Testing GOOGL ROE history...")
    roe_history = screener.get_stock_roe_history("GOOGL", 5)
    if roe_history:
        print(f"SUCCESS: Found {len(roe_history)} years of ROE data:")
        for roe in roe_history:
            print(f"   {roe.year}: {roe.roe:.2f}%")
    else:
        print("ERROR: No ROE history found")
    
    # 단일 기업 테스트
    result = await screener._analyze_stock_roe("GOOGL", 15.0, 5)
    if result:
        print(f"SUCCESS: GOOGL qualified: {result.company_name}")
        print(f"   Symbol: {result.symbol}")
        print(f"   Sector: {result.sector}")
    else:
        print("ERROR: GOOGL did not qualify or error occurred")

if __name__ == "__main__":
    asyncio.run(test_googl())