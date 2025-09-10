#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from services.stock_screener import StockScreener
from services.investment_analyzer import InvestmentAnalyzer
from models.stock_models import *

async def create_demo_data():
    """확실히 작동하는 데모 데이터 생성"""
    
    # Microsoft 데모 데이터
    msft_info = StockInfo(
        symbol="MSFT",
        company_name="Microsoft Corporation",
        sector="Technology",
        market_cap=3000000000000  # 3조 달러
    )
    
    # Google 데모 데이터  
    googl_info = StockInfo(
        symbol="GOOGL",
        company_name="Alphabet Inc.", 
        sector="Communication Services",
        market_cap=2000000000000  # 2조 달러
    )
    
    # Apple 데모 데이터
    aapl_info = StockInfo(
        symbol="AAPL",
        company_name="Apple Inc.",
        sector="Technology", 
        market_cap=3500000000000  # 3.5조 달러
    )
    
    demo_stocks = [msft_info, googl_info, aapl_info]
    
    # 각 주식에 대한 상세 분석 생성
    analyzer = InvestmentAnalyzer()
    results = []
    
    for stock in demo_stocks:
        try:
            print(f"Analyzing {stock.symbol}...")
            result = await analyzer.analyze_stock(stock)
            if result:
                results.append(result)
                print(f"Success: {stock.symbol} analyzed")
            else:
                print(f"Failed: {stock.symbol} analysis failed")
        except Exception as e:
            print(f"Error analyzing {stock.symbol}: {e}")
    
    print(f"Total results: {len(results)}")
    return results

if __name__ == "__main__":
    asyncio.run(create_demo_data())