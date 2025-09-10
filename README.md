# ROE 기반 장기투자 분석 시스템

신나구로의 투자철학을 기반으로 한 ROE와 복리수익률의 상관관계를 검증하는 장기투자 종목 선별 시스템입니다.

## 주요 기능

1. **자동 스크리닝**: 미국 주식 중 ROE 15% 이상을 5년간 지속한 기업 20개를 자동으로 선별
2. **듀얼 차트 시각화**: 선별된 기업들의 10년간 ROE 데이터와 주가 수익률을 듀얼 Y축 차트로 비교
3. **상관관계 분석**: 각 기업별로 ROE와 주가 수익률의 피어슨 상관계수 계산 및 유의성 검증
4. **투자 점수 제공**: ROE 일관성, 성장성, 주가 수익률, 상관관계를 종합한 100점 만점 투자 점수

## 기술 스택

- **Backend**: Python FastAPI
- **Frontend**: HTML/CSS/JavaScript with Chart.js
- **데이터**: yfinance, Alpha Vantage API
- **차트**: Chart.js (듀얼 Y축)

## 설치 및 실행

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 서버 실행
```bash
python backend/main.py
```

또는

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 웹 애플리케이션 접속
브라우저에서 `http://localhost:8000/static/index.html` 접속

## 사용법

1. **분석 설정**:
   - 최소 ROE: 기준 ROE 설정 (기본값: 15%)
   - 지속 년수: ROE 지속 기간 설정 (기본값: 5년)
   - 분석 기업 수: 선별할 기업 수 설정 (기본값: 20개)

2. **분석 실행**: "장기투자 적합 기업 찾기" 버튼 클릭

3. **결과 확인**:
   - 투자 점수 순으로 정렬된 기업 목록 확인
   - 각 기업의 차트 보기 버튼 클릭으로 ROE vs 주가수익률 비교 차트 확인
   - 상세 분석 정보에서 상관관계 및 투자 점수 세부 내용 확인

## 투자 점수 구성

- **ROE 일관성 (25점)**: ROE의 변동계수 기반 일관성 평가
- **ROE 성장성 (25점)**: 초기 3년 대비 최근 3년 ROE 성장률 평가
- **주가 수익률 (25점)**: 10년간 연평균 주가 수익률 평가
- **상관관계 (25점)**: ROE와 주가 수익률간 상관계수 및 유의성 평가

## 등급 체계

- A+ (85점 이상): 최우수 투자 대상
- A (75-84점): 우수 투자 대상
- B+ (65-74점): 양호 투자 대상
- B (55-64점): 보통 투자 대상
- C+ (45-54점): 주의 필요
- C (35-44점): 투자 재검토 필요
- D (35점 미만): 투자 부적합

## 주의사항

1. 본 시스템은 투자 참고용으로만 사용하시기 바랍니다.
2. 실제 투자 결정은 충분한 검토와 전문가 상담을 거쳐 진행하시기 바랍니다.
3. Alpha Vantage API 키가 필요한 경우 `services/stock_screener.py`에서 설정하세요.
4. 데이터 수집에는 시간이 소요될 수 있으니 양해 바랍니다.

## 프로젝트 구조

```
Stock-long-term-investment/
├── backend/
│   └── main.py              # FastAPI 메인 서버
├── models/
│   └── stock_models.py      # 데이터 모델 정의
├── services/
│   ├── stock_screener.py    # 주식 스크리닝 서비스
│   └── investment_analyzer.py # 투자 분석 서비스
├── frontend/
│   ├── index.html          # 메인 웹 페이지
│   ├── styles.css          # 스타일시트
│   └── script.js           # JavaScript 로직
└── requirements.txt        # Python 의존성
```

## 개발자 정보

ROE 기반 장기투자 분석 시스템 v1.0.0
신나구로의 투자철학 기반 구현