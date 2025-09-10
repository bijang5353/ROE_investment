import yfinance as yf
import pandas as pd
import numpy as np
from scipy import stats
from typing import Optional, List
from datetime import datetime, timedelta
from models.stock_models import (
    StockInfo, StockAnalysisResult, ROEData, StockPrice,
    CorrelationAnalysis, InvestmentScore
)
from services.stock_screener import StockScreener

class InvestmentAnalyzer:
    def __init__(self):
        self.screener = StockScreener()
    
    async def analyze_stock(self, stock_info: StockInfo) -> Optional[StockAnalysisResult]:
        """개별 주식에 대한 종합 분석"""
        try:
            # 10년간 ROE 데이터 수집
            roe_history = self.screener.get_stock_roe_history(stock_info.symbol, 10)
            if len(roe_history) < 5:
                return None
            
            # 10년간 주가 데이터 수집
            price_history = self._get_price_history(stock_info.symbol, 10)
            if not price_history:
                return None
            
            # 10년 수익률 계산
            ten_year_return = self._calculate_total_return(price_history)
            
            # 5년 평균 ROE 계산
            recent_roe = [r for r in roe_history if r.year >= (datetime.now().year - 5)]
            five_year_roe_avg = np.mean([r.roe for r in recent_roe]) if recent_roe else 0
            
            # ROE와 주가 수익률 상관관계 분석
            correlation_analysis = self._analyze_correlation(roe_history, price_history)
            
            # 투자 점수 계산
            investment_score = self._calculate_investment_score(
                roe_history, price_history, ten_year_return, correlation_analysis
            )
            
            # 차트 데이터 준비
            chart_data = self._prepare_chart_data(roe_history, price_history)
            
            return StockAnalysisResult(
                stock_info=stock_info,
                roe_history=roe_history,
                price_history=price_history,
                ten_year_return=ten_year_return,
                five_year_roe_avg=five_year_roe_avg,
                correlation_analysis=correlation_analysis,
                investment_score=investment_score,
                chart_data=chart_data
            )
            
        except Exception as e:
            print(f"Error analyzing {stock_info.symbol}: {e}")
            return None
    
    def _get_price_history(self, symbol: str, years: int = 10) -> List[StockPrice]:
        """주가 히스토리 가져오기"""
        try:
            ticker = yf.Ticker(symbol)
            
            # period만 사용 (start, end와 함께 사용 불가)
            period_map = {1: "1y", 2: "2y", 3: "3y", 5: "5y", 10: "10y", 15: "15y", 20: "20y"}
            period = period_map.get(years, "10y")
            
            hist = ticker.history(period=period)
            
            price_history = []
            for date, row in hist.iterrows():
                price_history.append(StockPrice(
                    date=date.to_pydatetime(),
                    close_price=float(row['Close']),
                    adjusted_close=float(row['Close'])
                ))
            
            return sorted(price_history, key=lambda x: x.date)
            
        except Exception as e:
            print(f"Error getting price history for {symbol}: {e}")
            return []
    
    def _calculate_total_return(self, price_history: List[StockPrice]) -> float:
        """총 수익률 계산 (복리)"""
        if len(price_history) < 2:
            return 0.0
        
        start_price = price_history[0].adjusted_close
        end_price = price_history[-1].adjusted_close
        
        if start_price <= 0:
            return 0.0
        
        years = (price_history[-1].date - price_history[0].date).days / 365.25
        if years <= 0:
            return 0.0
        
        # 연평균 복리 수익률 계산
        annual_return = ((end_price / start_price) ** (1 / years)) - 1
        return annual_return * 100
    
    def _analyze_correlation(self, roe_history: List[ROEData], 
                           price_history: List[StockPrice]) -> CorrelationAnalysis:
        """ROE와 주가 수익률 상관관계 분석"""
        try:
            # 연도별로 데이터 매칭
            roe_by_year = {r.year: r.roe for r in roe_history}
            
            # 연도별 주가 수익률 계산
            annual_returns = {}
            price_by_year = {}
            
            for price in price_history:
                year = price.date.year
                if year not in price_by_year:
                    price_by_year[year] = price.adjusted_close
                else:
                    # 해당 연도의 마지막 가격으로 업데이트
                    if price.date.month == 12:
                        price_by_year[year] = price.adjusted_close
            
            # 연간 수익률 계산
            years = sorted(price_by_year.keys())
            for i in range(1, len(years)):
                prev_year = years[i-1]
                curr_year = years[i]
                if prev_year in price_by_year and curr_year in price_by_year:
                    prev_price = price_by_year[prev_year]
                    curr_price = price_by_year[curr_year]
                    if prev_price > 0:
                        annual_return = ((curr_price / prev_price) - 1) * 100
                        annual_returns[curr_year] = annual_return
            
            # 공통 연도 데이터 추출
            common_years = set(roe_by_year.keys()) & set(annual_returns.keys())
            if len(common_years) < 3:
                return CorrelationAnalysis(
                    correlation_coefficient=0.0,
                    p_value=1.0,
                    significance="insufficient_data"
                )
            
            roe_values = [roe_by_year[year] for year in sorted(common_years)]
            return_values = [annual_returns[year] for year in sorted(common_years)]
            
            # 피어슨 상관계수 계산
            correlation, p_value = stats.pearsonr(roe_values, return_values)
            
            # NaN 값 처리
            if pd.isna(correlation):
                correlation = 0.0
            if pd.isna(p_value):
                p_value = 1.0
            
            # 유의성 판단
            if p_value < 0.01:
                significance = "highly_significant"
            elif p_value < 0.05:
                significance = "significant"
            elif p_value < 0.1:
                significance = "moderately_significant"
            else:
                significance = "not_significant"
            
            return CorrelationAnalysis(
                correlation_coefficient=float(correlation),
                p_value=float(p_value),
                significance=significance
            )
            
        except Exception as e:
            print(f"Error calculating correlation: {e}")
            return CorrelationAnalysis(
                correlation_coefficient=0.0,
                p_value=1.0,
                significance="error"
            )
    
    def _calculate_investment_score(self, roe_history: List[ROEData], 
                                  price_history: List[StockPrice],
                                  ten_year_return: float,
                                  correlation: CorrelationAnalysis) -> InvestmentScore:
        """투자 점수 계산"""
        try:
            # 1. ROE 일관성 점수 (0-25점)
            roe_values = [r.roe for r in roe_history]
            roe_std = np.std(roe_values)
            roe_mean = np.mean(roe_values)
            
            # NaN 값 처리
            if pd.isna(roe_std):
                roe_std = 0.0
            if pd.isna(roe_mean) or roe_mean == 0:
                roe_mean = 1.0
            
            # 변동계수 기반 일관성 점수
            cv = roe_std / roe_mean if roe_mean > 0 else float('inf')
            if cv < 0.2:
                roe_consistency_score = 25
            elif cv < 0.4:
                roe_consistency_score = 20
            elif cv < 0.6:
                roe_consistency_score = 15
            elif cv < 0.8:
                roe_consistency_score = 10
            else:
                roe_consistency_score = 5
            
            # 2. ROE 성장 점수 (0-25점)
            if len(roe_values) >= 5:
                recent_roe = np.mean(roe_values[-3:])  # 최근 3년 평균
                early_roe = np.mean(roe_values[:3])    # 초기 3년 평균
                
                if early_roe > 0:
                    roe_growth_rate = ((recent_roe / early_roe) - 1) * 100
                    if roe_growth_rate > 20:
                        roe_growth_score = 25
                    elif roe_growth_rate > 10:
                        roe_growth_score = 20
                    elif roe_growth_rate > 0:
                        roe_growth_score = 15
                    elif roe_growth_rate > -10:
                        roe_growth_score = 10
                    else:
                        roe_growth_score = 5
                else:
                    roe_growth_score = 10
            else:
                roe_growth_score = 10
            
            # 3. 주가 수익률 점수 (0-25점)
            if ten_year_return > 15:
                price_return_score = 25
            elif ten_year_return > 12:
                price_return_score = 20
            elif ten_year_return > 9:
                price_return_score = 15
            elif ten_year_return > 6:
                price_return_score = 10
            elif ten_year_return > 0:
                price_return_score = 5
            else:
                price_return_score = 0
            
            # 4. 상관관계 점수 (0-25점)
            corr_coef = correlation.correlation_coefficient
            if correlation.significance in ["highly_significant", "significant"]:
                if corr_coef > 0.7:
                    correlation_score = 25
                elif corr_coef > 0.5:
                    correlation_score = 20
                elif corr_coef > 0.3:
                    correlation_score = 15
                elif corr_coef > 0.1:
                    correlation_score = 10
                else:
                    correlation_score = 5
            else:
                correlation_score = 5
            
            # 총점 계산
            total_score = (roe_consistency_score + roe_growth_score + 
                          price_return_score + correlation_score)
            
            # 등급 판정
            if total_score >= 85:
                grade = "A+"
            elif total_score >= 75:
                grade = "A"
            elif total_score >= 65:
                grade = "B+"
            elif total_score >= 55:
                grade = "B"
            elif total_score >= 45:
                grade = "C+"
            elif total_score >= 35:
                grade = "C"
            else:
                grade = "D"
            
            return InvestmentScore(
                total_score=total_score,
                roe_consistency_score=roe_consistency_score,
                roe_growth_score=roe_growth_score,
                price_return_score=price_return_score,
                correlation_score=correlation_score,
                grade=grade
            )
            
        except Exception as e:
            print(f"Error calculating investment score: {e}")
            return InvestmentScore(
                total_score=0,
                roe_consistency_score=0,
                roe_growth_score=0,
                price_return_score=0,
                correlation_score=0,
                grade="F"
            )
    
    def _prepare_chart_data(self, roe_history: List[ROEData], 
                           price_history: List[StockPrice]) -> dict:
        """차트 데이터 준비"""
        try:
            # 연도별 데이터 정렬
            roe_data = {}
            for roe in roe_history:
                roe_data[roe.year] = roe.roe
            
            # 연도별 누적 수익률 계산
            price_returns = {}
            if price_history:
                # 전체 기간에서 가장 이른 날짜의 주가를 기준으로 사용
                sorted_prices = sorted(price_history, key=lambda x: x.date)
                base_price = sorted_prices[0].adjusted_close
                print(f"DEBUG: Base price (earliest): ${base_price:.2f} on {sorted_prices[0].date}")
                
                # 연도별로 가장 늦은 날짜의 가격 사용
                yearly_latest_prices = {}
                for price in price_history:
                    year = price.date.year
                    if year not in yearly_latest_prices or price.date > yearly_latest_prices[year]['date']:
                        yearly_latest_prices[year] = {'price': price.adjusted_close, 'date': price.date}
                
                # 각 연도별로 누적 수익률 계산
                for year, data in yearly_latest_prices.items():
                    if base_price > 0:
                        cumulative_return = ((data['price'] / base_price) - 1) * 100
                        price_returns[year] = cumulative_return
                        print(f"DEBUG: {year}: ${data['price']:.2f} -> {cumulative_return:.2f}% (date: {data['date']})")
            
            # 공통 연도 추출
            common_years = sorted(set(roe_data.keys()) & set(price_returns.keys()))
            
            chart_data = {
                "labels": common_years,
                "roe_data": [roe_data.get(year, 0) for year in common_years],
                "return_data": [price_returns.get(year, 0) for year in common_years]
            }
            
            return chart_data
            
        except Exception as e:
            print(f"Error preparing chart data: {e}")
            return {
                "labels": [],
                "roe_data": [],
                "return_data": []
            }