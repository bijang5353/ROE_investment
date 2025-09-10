import yfinance as yf
import pandas as pd
import asyncio
from typing import List, Optional
from models.stock_models import StockInfo, ROEData
import time

try:
    from alpha_vantage.fundamentaldata import FundamentalData
    ALPHA_VANTAGE_AVAILABLE = True
except ImportError:
    ALPHA_VANTAGE_AVAILABLE = False

class StockScreener:
    def __init__(self):
        # S&P 500 주요 기업들 - 실제 환경에서는 더 많은 기업 리스트 사용
        self.sp500_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JNJ', 'JPM', 'V',
            'UNH', 'PG', 'HD', 'MA', 'BAC', 'XOM', 'ABBV', 'PFE', 'ASML', 'KO',
            'AVGO', 'PEP', 'TMO', 'COST', 'MRK', 'WMT', 'ABT', 'NFLX', 'CRM', 'ACN',
            'LLY', 'NKE', 'ORCL', 'DHR', 'TXN', 'NEE', 'VZ', 'RTX', 'CMCSA', 'INTC',
            'AMD', 'HON', 'T', 'QCOM', 'LOW', 'IBM', 'UPS', 'INTU', 'AMGN', 'CAT'
        ]
        self.alpha_vantage_key = "LPDBEJCLJ60EUYU0"
        if ALPHA_VANTAGE_AVAILABLE:
            self.fundamental_data = FundamentalData(key=self.alpha_vantage_key, output_format='pandas')
    
    async def screen_high_roe_stocks(self, min_roe: float = 15.0, years: int = 5, limit: int = 20) -> List[StockInfo]:
        """ROE 기준 완화된 스크리닝: 최근 5년 평균 또는 10년 중 7년 이상"""
        
        qualified_stocks = []
        print(f"\n=== ROE 스크리닝 시작 (기준: {min_roe}%, 기간: {years}년) ===")
        
        # S&P 500 기업들 중에서 스크리닝 
        for symbol in self.sp500_symbols[:30]:  # 처음 30개 기업만 테스트
            try:
                print(f"\n--- {symbol} 분석 중 ---")
                roe_history = self.get_stock_roe_history(symbol, 10)
                
                if not roe_history:
                    print(f"{symbol}: ROE 데이터 없음")
                    continue
                
                # ROE 히스토리 출력 (디버깅용)
                print(f"{symbol} ROE 히스토리:")
                for roe_data in roe_history:
                    print(f"  {roe_data.year}: {roe_data.roe:.1f}%")
                
                # 1. 최근 5년 평균 ROE 기준
                recent_years = [r for r in roe_history if r.year >= 2019]
                if len(recent_years) >= 3:  # 최근 3년 이상 데이터
                    avg_roe = sum(r.roe for r in recent_years) / len(recent_years)
                    print(f"{symbol}: 최근 {len(recent_years)}년 평균 ROE = {avg_roe:.1f}%")
                    
                    if avg_roe >= min_roe:
                        print(f"[PASS] {symbol}: 최근 평균 ROE 기준 통과")
                        qualified_stocks.append(await self._get_stock_info(symbol))
                        continue
                
                # 2. 10년 중 7년 이상 ROE 15% 달성 기준 
                good_years = [r for r in roe_history if r.roe >= min_roe]
                print(f"{symbol}: {len(good_years)}/{len(roe_history)}년 ROE {min_roe}% 이상 달성")
                
                if len(good_years) >= min(7, len(roe_history) * 0.7):
                    print(f"[PASS] {symbol}: 다년도 ROE 기준 통과")
                    qualified_stocks.append(await self._get_stock_info(symbol))
                    continue
                
                # 3. 데이터 부족시 ROE 12% 기준으로 완화
                if len(roe_history) < 5 and min_roe > 12:
                    avg_roe = sum(r.roe for r in roe_history) / len(roe_history)
                    if avg_roe >= 12:
                        print(f"[PASS] {symbol}: 완화된 ROE 기준(12%) 통과")
                        qualified_stocks.append(await self._get_stock_info(symbol))
                        continue
                
                print(f"[FAIL] {symbol}: 모든 ROE 기준 미달")
                
                if len(qualified_stocks) >= limit:
                    break
                    
            except Exception as e:
                print(f"[ERROR] {symbol}: 분석 중 오류 - {e}")
                continue
        
        print(f"\n=== 스크리닝 완료: {len(qualified_stocks)}개 기업 선정 ===")
        return qualified_stocks[:limit]

    async def _get_stock_info(self, symbol: str) -> StockInfo:
        """주식 기본 정보 가져오기"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return StockInfo(
                symbol=symbol,
                company_name=info.get('longName', symbol),
                sector=info.get('sector', ''),
                market_cap=float(info.get('marketCap', 0)) if info.get('marketCap') else None
            )
        except:
            return StockInfo(symbol=symbol, company_name=symbol, sector="", market_cap=None)
    
    async def _analyze_stock_roe(self, symbol: str, min_roe: float, years: int) -> Optional[StockInfo]:
        """개별 주식의 ROE 분석"""
        try:
            ticker = yf.Ticker(symbol)
            
            # 기업 정보 가져오기
            info = ticker.info
            company_name = info.get('longName', symbol)
            sector = info.get('sector', '')
            market_cap = info.get('marketCap', 0)
            
            # 재무제표 데이터 가져오기 (yfinance 사용)
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            
            if financials.empty or balance_sheet.empty:
                return None
            
            # ROE 계산 (Net Income / Shareholders' Equity)
            roe_data = []
            current_year = pd.Timestamp.now().year
            
            for i in range(years + 2):  # 추가 년수를 더 확인해서 데이터 수집률 높임
                year = current_year - i - 1
                try:
                    # 해당 연도의 데이터 찾기
                    year_cols = [col for col in financials.columns if col.year == year]
                    if not year_cols:
                        continue
                        
                    year_col = year_cols[0]
                    
                    # Net Income
                    net_income = financials.loc['Net Income', year_col] if 'Net Income' in financials.index else None
                    if net_income is None:
                        net_income = financials.loc['Total Revenue', year_col] * 0.1  # 임시 추정치
                    
                    # Shareholders' Equity
                    equity_rows = ['Stockholders Equity', 'Total Stockholder Equity', 'Shareholders Equity']
                    shareholders_equity = None
                    
                    for equity_row in equity_rows:
                        if equity_row in balance_sheet.index:
                            equity_cols = [col for col in balance_sheet.columns if col.year == year]
                            if equity_cols:
                                shareholders_equity = balance_sheet.loc[equity_row, equity_cols[0]]
                                break
                    
                    if shareholders_equity is None or shareholders_equity == 0:
                        continue
                    
                    # ROE 계산
                    roe = (net_income / shareholders_equity) * 100
                    
                    if roe >= min_roe:
                        roe_data.append(ROEData(
                            year=year,
                            roe=roe,
                            net_income=float(net_income) if net_income else None
                        ))
                    else:
                        # ROE가 기준에 미달하면 실격
                        return None
                        
                except Exception as e:
                    print(f"Error calculating ROE for {symbol} year {year}: {e}")
                    continue
            
            # 지정된 년수만큼 ROE 기준을 충족했는지 확인 (최소 3년 이상이면 허용)
            min_years = max(3, years - 2)  # 5년 요구시 3년 이상이면 허용
            if len(roe_data) >= min_years:
                return StockInfo(
                    symbol=symbol,
                    company_name=company_name,
                    sector=sector,
                    market_cap=float(market_cap) if market_cap else None
                )
            
            return None
            
        except Exception as e:
            print(f"Error in _analyze_stock_roe for {symbol}: {e}")
            return None
    
    def get_stock_roe_history(self, symbol: str, years: int = 10) -> List[ROEData]:
        """특정 주식의 ROE 히스토리 가져오기"""
        # 먼저 Alpha Vantage API 시도
        if ALPHA_VANTAGE_AVAILABLE and hasattr(self, 'fundamental_data'):
            alpha_data = self._get_roe_from_alpha_vantage(symbol, years)
            if alpha_data and len(alpha_data) >= 3:  # 최소 3년 이상 데이터가 있으면 사용
                return alpha_data
        
        # Alpha Vantage 실패시 yfinance 사용
        try:
            ticker = yf.Ticker(symbol)
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            
            roe_history = []
            current_year = pd.Timestamp.now().year
            
            for i in range(years + 2):  # 추가 년수를 더 확인해서 데이터 수집률 높임
                year = current_year - i - 1
                try:
                    year_cols = [col for col in financials.columns if col.year == year]
                    if not year_cols:
                        continue
                        
                    year_col = year_cols[0]
                    
                    # Net Income
                    net_income = financials.loc['Net Income', year_col] if 'Net Income' in financials.index else None
                    if net_income is None:
                        continue
                    
                    # Shareholders' Equity
                    equity_rows = ['Stockholders Equity', 'Total Stockholder Equity', 'Shareholders Equity']
                    shareholders_equity = None
                    
                    for equity_row in equity_rows:
                        if equity_row in balance_sheet.index:
                            equity_cols = [col for col in balance_sheet.columns if col.year == year]
                            if equity_cols:
                                shareholders_equity = balance_sheet.loc[equity_row, equity_cols[0]]
                                break
                    
                    if shareholders_equity is None or shareholders_equity == 0:
                        continue
                    
                    roe = (net_income / shareholders_equity) * 100
                    
                    roe_history.append(ROEData(
                        year=year,
                        roe=roe,
                        net_income=float(net_income)
                    ))
                    
                except Exception as e:
                    continue
            
            return sorted(roe_history, key=lambda x: x.year)
            
        except Exception as e:
            print(f"Error getting ROE history for {symbol}: {e}")
            return []
    
    def _get_roe_from_alpha_vantage(self, symbol: str, years: int = 10) -> List[ROEData]:
        """Alpha Vantage API를 사용하여 ROE 데이터 가져오기"""
        if not ALPHA_VANTAGE_AVAILABLE or not hasattr(self, 'fundamental_data'):
            return []
        
        try:
            # Alpha Vantage에서 재무제표 데이터 가져오기
            income_statement, _ = self.fundamental_data.get_income_statement_annual(symbol)
            balance_sheet, _ = self.fundamental_data.get_balance_sheet_annual(symbol)
            
            if income_statement is None or balance_sheet is None:
                return []
            
            roe_history = []
            
            for year_str in income_statement.columns[:years]:  # 최근 년도부터
                try:
                    year = pd.to_datetime(year_str).year
                    
                    # Net Income 가져오기
                    net_income = income_statement.loc['netIncome', year_str]
                    if pd.isna(net_income) or net_income == 0:
                        continue
                    
                    # Shareholders' Equity 가져오기  
                    shareholders_equity = balance_sheet.loc['totalShareholderEquity', year_str]
                    if pd.isna(shareholders_equity) or shareholders_equity == 0:
                        continue
                    
                    # ROE 계산
                    roe = (float(net_income) / float(shareholders_equity)) * 100
                    
                    roe_history.append(ROEData(
                        year=year,
                        roe=roe,
                        net_income=float(net_income)
                    ))
                    
                except Exception as e:
                    continue
            
            return sorted(roe_history, key=lambda x: x.year)
            
        except Exception as e:
            print(f"Error getting Alpha Vantage data for {symbol}: {e}")
            return []