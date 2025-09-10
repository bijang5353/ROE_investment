#!/usr/bin/env python3
"""
실제 주가수익률 계산 및 디버깅 스크립트
"""
import yfinance as yf
import pandas as pd
from datetime import datetime

def calculate_real_stock_returns():
    """실제 주가수익률 계산 및 디버깅"""
    
    # 주요 종목들
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'META', 'UNH', 'V', 'JNJ', 'PG', 'KO']
    
    # 정확한 기간 설정
    start_date = '2015-01-01'
    end_date = '2024-12-31'
    
    print("=" * 80)
    print("실제 주가수익률 계산 및 디버깅")
    print("=" * 80)
    print(f"기간: {start_date} ~ {end_date}")
    print(f"계산 공식: ((마지막가격/첫번째가격) - 1) * 100")
    print("-" * 80)
    
    results = {}
    
    for symbol in symbols:
        try:
            print(f"\n--- {symbol} 분석 중 ---")
            
            # yfinance에서 데이터 가져오기
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=start_date, end=end_date)
            
            if data.empty:
                print(f"❌ {symbol}: 데이터 없음")
                continue
            
            # Adjusted Close 사용 (주식분할 조정됨)
            adj_close = data['Close']  # yfinance history()는 자동으로 조정된 가격 제공
            
            # 첫 번째와 마지막 가격
            first_price = adj_close.iloc[0]
            last_price = adj_close.iloc[-1]
            
            # 수익률 계산
            total_return = ((last_price / first_price) - 1) * 100
            
            # 결과 저장
            results[symbol] = {
                'first_price': first_price,
                'last_price': last_price,
                'total_return': total_return,
                'first_date': adj_close.index[0].strftime('%Y-%m-%d'),
                'last_date': adj_close.index[-1].strftime('%Y-%m-%d')
            }
            
            # 디버깅 출력
            print(f"시작일: {results[symbol]['first_date']}")
            print(f"종료일: {results[symbol]['last_date']}")
            print(f"시작가격: ${first_price:.2f}")
            print(f"종료가격: ${last_price:.2f}")
            print(f"총 수익률: {total_return:.1f}%")
            print(f"투자배수: {last_price/first_price:.1f}x")
            
            # 1억원 투자시 결과
            investment_result = 1.0 * (1 + total_return/100)
            print(f"1억 투자시: {investment_result:.1f}억원")
            
        except Exception as e:
            print(f"❌ {symbol}: 오류 발생 - {e}")
            continue
    
    print("\n" + "=" * 80)
    print("요약 결과")
    print("=" * 80)
    
    for symbol, data in results.items():
        print(f"{symbol:5}: {data['total_return']:6.1f}% | "
              f"${data['first_price']:6.2f} → ${data['last_price']:7.2f} | "
              f"{1.0 * (1 + data['total_return']/100):.1f}억원")
    
    return results

if __name__ == "__main__":
    results = calculate_real_stock_returns()