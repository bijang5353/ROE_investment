#!/usr/bin/env python3
"""
ROE 기반 장기투자 분석 시스템 실행 스크립트
"""

import uvicorn
import os
import sys
import webbrowser
from pathlib import Path

def main():
    print("="*50)
    print("ROE 기반 장기투자 분석 시스템 시작")
    print("="*50)
    
    # 프로젝트 루트 디렉토리를 Python 경로에 추가
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    print("서버를 시작합니다...")
    print("접속 주소: http://localhost:8000/static/index.html")
    print("서버를 중단하려면 Ctrl+C를 누르세요.")
    print("-"*50)
    
    try:
        # 브라우저에서 자동으로 페이지 열기
        import threading
        import time
        
        def open_browser():
            time.sleep(2)  # 서버가 완전히 시작될 때까지 대기
            webbrowser.open('http://localhost:8000/static/index.html')
        
        # 브라우저 열기를 별도 쓰레드에서 실행
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # FastAPI 서버 시작
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n서버가 중단되었습니다.")
    except Exception as e:
        print(f"서버 실행 중 오류가 발생했습니다: {e}")
        print("requirements.txt의 모든 패키지가 설치되어 있는지 확인해주세요.")
        print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()