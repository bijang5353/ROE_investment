from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class StockInfo(BaseModel):
    symbol: str
    company_name: str
    sector: Optional[str] = None
    market_cap: Optional[float] = None

class ROEData(BaseModel):
    year: int
    roe: float
    revenue: Optional[float] = None
    net_income: Optional[float] = None

class StockPrice(BaseModel):
    date: datetime
    close_price: float
    adjusted_close: float

class CorrelationAnalysis(BaseModel):
    correlation_coefficient: float
    p_value: float
    significance: str

class InvestmentScore(BaseModel):
    total_score: float
    roe_consistency_score: float
    roe_growth_score: float
    price_return_score: float
    correlation_score: float
    grade: str

class StockAnalysisResult(BaseModel):
    stock_info: StockInfo
    roe_history: List[ROEData]
    price_history: List[StockPrice]
    ten_year_return: float
    five_year_roe_avg: float
    correlation_analysis: CorrelationAnalysis
    investment_score: InvestmentScore
    chart_data: Dict

class AnalysisRequest(BaseModel):
    min_roe: float = Field(default=15.0, description="최소 ROE 기준 (%)")
    years: int = Field(default=5, description="ROE 지속 년수")
    limit: int = Field(default=20, description="분석할 기업 수")

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    data: List[StockAnalysisResult]