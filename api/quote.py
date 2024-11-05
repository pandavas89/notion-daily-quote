import sys
import os

# 부모 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 부모 디렉토리에 있는 daily_quote.py 임포트
from daily_quote import main

main()
