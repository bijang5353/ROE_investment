class ROEAnalyzer {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.currentChart = null;
        this.analysisData = [];
        this.autoAnalysisTimer = null;
        this.hasPerformedInitialAnalysis = false;
        this.initializeEventListeners();
    }

    initializeEventListeners() {
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.performAnalysis();
        });
        
        // 슬라이더 값 실시간 업데이트 및 자동 분석
        document.getElementById('minRoe').addEventListener('input', (e) => {
            document.getElementById('roeValue').textContent = e.target.value;
            this.scheduleAutoAnalysis();
        });
        
        document.getElementById('years').addEventListener('input', (e) => {
            document.getElementById('yearsValue').textContent = e.target.value;
            this.scheduleAutoAnalysis();
        });
        
        document.getElementById('limit').addEventListener('change', () => {
            this.scheduleAutoAnalysis();
        });
    }

    scheduleAutoAnalysis() {
        // 이미 분석이 한 번 실행된 경우에만 자동 분석 실행
        if (!this.hasPerformedInitialAnalysis) {
            return;
        }
        
        // 기존 타이머가 있으면 클리어
        if (this.autoAnalysisTimer) {
            clearTimeout(this.autoAnalysisTimer);
        }
        
        // 0.8초 후에 분석 실행 (슬라이더 조작이 끝나면 실행)
        this.autoAnalysisTimer = setTimeout(() => {
            this.performAnalysis(true);
        }, 800);
    }

    async performAnalysis(isAutoAnalysis = false) {
        const minRoe = parseFloat(document.getElementById('minRoe').value);
        const years = parseInt(document.getElementById('years').value);
        const limit = parseInt(document.getElementById('limit').value);

        if (minRoe < 5 || years < 5 || limit < 5) {
            this.showError('올바른 분석 조건을 입력해주세요.');
            return;
        }

        // 첫 번째 분석 완료 표시
        this.hasPerformedInitialAnalysis = true;

        // 자동 분석의 경우 로딩 표시를 간소화
        if (!isAutoAnalysis) {
            this.showLoading(true);
            this.hideResults();
        } else {
            // 자동 분석시에는 결과 테이블만 업데이트
            const resultCount = document.getElementById('resultCount');
            resultCount.textContent = '분석 중...';
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    min_roe: minRoe,
                    years: years,
                    limit: limit
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.analysisData = result.data;
                this.displayResults(result.data);
                if (!isAutoAnalysis) {
                    this.showSuccess(`${result.data.length}개 기업 분석이 완료되었습니다.`);
                }
            } else {
                if (!isAutoAnalysis) {
                    this.showError(result.message || '분석 중 오류가 발생했습니다.');
                }
            }

        } catch (error) {
            console.error('Analysis error:', error);
            if (!isAutoAnalysis) {
                this.showError('서버 연결에 실패했습니다. 서버가 실행 중인지 확인해주세요.');
            }
        } finally {
            if (!isAutoAnalysis) {
                this.showLoading(false);
            }
        }
    }

    displayResults(data) {
        const tbody = document.getElementById('resultsTableBody');
        const resultCount = document.getElementById('resultCount');
        
        tbody.innerHTML = '';
        resultCount.textContent = `${data.length}개 기업`;

        // 투자 점수로 정렬
        data.sort((a, b) => b.investment_score.total_score - a.investment_score.total_score);

        data.forEach((item, index) => {
            const row = this.createTableRow(item, index + 1);
            tbody.appendChild(row);
        });

        document.getElementById('resultsSection').style.display = 'block';
    }

    createTableRow(item, rank) {
        const tr = document.createElement('tr');
        
        const gradeClass = this.getGradeClass(item.investment_score.grade);
        const correlationClass = this.getCorrelationClass(item.correlation_analysis.correlation_coefficient);
        
        tr.innerHTML = `
            <td>${rank}</td>
            <td>
                <strong>${item.stock_info.company_name}</strong><br>
                <small class="text-muted">${item.stock_info.symbol}</small>
            </td>
            <td>${item.stock_info.sector || '-'}</td>
            <td>${item.ten_year_roe_avg.toFixed(2)}%</td>
            <td>${item.ten_year_return.toFixed(2)}%</td>
            <td class="${correlationClass}">${item.correlation_analysis.correlation_coefficient.toFixed(3)}</td>
            <td>
                <span class="badge ${gradeClass}">
                    ${item.investment_score.total_score.toFixed(0)}점
                </span>
            </td>
            <td>
                <span class="badge ${gradeClass}">${item.investment_score.grade}</span>
            </td>
            <td>
                <button class="btn btn-chart btn-sm" onclick="analyzer.showChart('${item.stock_info.symbol}')">
                    차트 보기
                </button>
            </td>
        `;

        return tr;
    }

    getGradeClass(grade) {
        const gradeMap = {
            'A+': 'grade-A-plus',
            'A': 'grade-A',
            'B+': 'grade-B-plus',
            'B': 'grade-B',
            'C+': 'grade-C-plus',
            'C': 'grade-C',
            'D': 'grade-D'
        };
        return gradeMap[grade] || 'bg-secondary';
    }

    getCorrelationClass(correlation) {
        if (correlation > 0.3) return 'correlation-positive';
        if (correlation < -0.3) return 'correlation-negative';
        return 'correlation-neutral';
    }

    showChart(symbol) {
        const stockData = this.analysisData.find(item => item.stock_info.symbol === symbol);
        if (!stockData) return;

        this.createDualChart(stockData);
        this.showStockDetails(stockData);
        
        document.getElementById('chartSection').style.display = 'block';
        document.getElementById('detailsSection').style.display = 'block';
        
        // 차트로 스크롤
        document.getElementById('chartSection').scrollIntoView({ behavior: 'smooth' });
    }

    createDualChart(stockData) {
        const ctx = document.getElementById('dualChart').getContext('2d');
        
        if (this.currentChart) {
            this.currentChart.destroy();
        }

        const chartData = stockData.chart_data;
        
        document.getElementById('chartTitle').textContent = 
            `${stockData.stock_info.company_name} (${stockData.stock_info.symbol}) - ROE vs 주가수익률`;

        this.currentChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: 'ROE (%)',
                    data: chartData.roe_data,
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    yAxisID: 'y',
                    tension: 0.4,
                    borderWidth: 3,
                    pointRadius: 6,
                    pointHoverRadius: 8,
                    investmentValues: chartData.investment_value  // 투자가치 데이터 추가
                }, {
                    label: '누적 주가수익률 (%)',
                    data: chartData.return_data,
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    yAxisID: 'y1',
                    tension: 0.4,
                    borderWidth: 3,
                    pointRadius: 6,
                    pointHoverRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: '연도',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'ROE (%)',
                            color: '#28a745',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            color: '#28a745'
                        },
                        grid: {
                            color: 'rgba(40, 167, 69, 0.2)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: '누적 주가수익률 (%)',
                            color: '#007bff',
                            font: {
                                size: 14,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            color: '#007bff'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    },
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'ROE와 주가수익률의 상관관계',
                        font: {
                            size: 16,
                            weight: 'bold'
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            afterBody: function(tooltipItems) {
                                const index = tooltipItems[0].dataIndex;
                                const investmentValue = chartData.investment_value[index];
                                return [``, `💰 1억 투자시: ${investmentValue.toFixed(1)}억원`];
                            }
                        }
                    },
                    legend: {
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            padding: 20,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#fff',
                        borderWidth: 1,
                        cornerRadius: 6,
                        displayColors: true
                    }
                }
            },
            plugins: [{
                afterDraw: function(chart) {
                    const ctx = chart.ctx;
                    const meta = chart.getDatasetMeta(1); // 누적 주가수익률 데이터셋
                    
                    ctx.save();
                    ctx.font = 'bold 15px Arial';
                    ctx.fillStyle = '#dc3545';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'bottom';
                    
                    meta.data.forEach((point, index) => {
                        const investmentValue = chartData.investment_value[index];
                        if (investmentValue) {
                            const label = investmentValue.toFixed(1) + '억';
                            // 점 위에 라벨 표시 (조금 위쪽에)
                            ctx.fillText(label, point.x, point.y - 8);
                        }
                    });
                    
                    ctx.restore();
                }
            }]
        });
    }

    showStockDetails(stockData) {
        const detailsContent = document.getElementById('detailsContent');
        const correlation = stockData.correlation_analysis;
        const score = stockData.investment_score;
        
        const significanceText = {
            'highly_significant': '매우 유의함 (p < 0.01)',
            'significant': '유의함 (p < 0.05)',
            'moderately_significant': '보통 유의함 (p < 0.1)',
            'not_significant': '유의하지 않음 (p ≥ 0.1)',
            'insufficient_data': '데이터 부족',
            'error': '계산 오류'
        };

        detailsContent.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <h6>기업 정보</h6>
                    <ul class="list-unstyled">
                        <li><strong>회사명:</strong> ${stockData.stock_info.company_name}</li>
                        <li><strong>심볼:</strong> ${stockData.stock_info.symbol}</li>
                        <li><strong>섹터:</strong> ${stockData.stock_info.sector || '-'}</li>
                        <li><strong>시가총액:</strong> ${stockData.stock_info.market_cap ? 
                            (stockData.stock_info.market_cap / 1000000000).toFixed(1) + 'B USD' : '-'}</li>
                    </ul>
                    
                    <h6>수익성 지표</h6>
                    <ul class="list-unstyled">
                        <li><strong>10년 평균 ROE:</strong> ${stockData.ten_year_roe_avg.toFixed(2)}%</li>
                        <li><strong>10년 총수익률:</strong> ${stockData.ten_year_return.toFixed(2)}%</li>
                        <li><strong>연평균 수익률:</strong> ${(stockData.ten_year_return / 10).toFixed(2)}%</li>
                    </ul>
                </div>
                
                <div class="col-md-6">
                    <h6>상관관계 분석</h6>
                    <ul class="list-unstyled">
                        <li><strong>상관계수:</strong> ${correlation.correlation_coefficient.toFixed(4)}</li>
                        <li><strong>P-값:</strong> ${correlation.p_value.toFixed(4)}</li>
                        <li><strong>유의성:</strong> ${significanceText[correlation.significance]}</li>
                    </ul>
                    
                    <h6>투자 점수 상세</h6>
                    <div class="score-breakdown">
                        <div class="score-item">
                            <span>ROE 일관성</span>
                            <span>${score.roe_consistency_score}/25</span>
                        </div>
                        <div class="score-item">
                            <span>ROE 성장성</span>
                            <span>${score.roe_growth_score}/25</span>
                        </div>
                        <div class="score-item">
                            <span>주가 수익률</span>
                            <span>${score.price_return_score}/25</span>
                        </div>
                        <div class="score-item">
                            <span>상관관계</span>
                            <span>${score.correlation_score}/25</span>
                        </div>
                        <div class="score-item">
                            <span>총점</span>
                            <span>${score.total_score}/100 (${score.grade})</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    showLoading(show) {
        const loadingSection = document.getElementById('loadingSection');
        loadingSection.style.display = show ? 'block' : 'none';
    }

    hideResults() {
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('chartSection').style.display = 'none';
        document.getElementById('detailsSection').style.display = 'none';
        this.clearMessages();
    }

    showError(message) {
        this.clearMessages();
        const alertDiv = document.createElement('div');
        alertDiv.className = 'error-message';
        alertDiv.textContent = message;
        
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }

    showSuccess(message) {
        this.clearMessages();
        const alertDiv = document.createElement('div');
        alertDiv.className = 'success-message';
        alertDiv.textContent = message;
        
        const container = document.querySelector('.container-fluid');
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 3000);
    }

    clearMessages() {
        const messages = document.querySelectorAll('.error-message, .success-message');
        messages.forEach(msg => {
            if (msg.parentNode) {
                msg.parentNode.removeChild(msg);
            }
        });
    }
}

// 전역 인스턴스 생성
const analyzer = new ROEAnalyzer();