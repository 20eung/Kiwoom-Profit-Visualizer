"""
기간별 데이터 수집 스크립트
2023년 12월부터 2026년 1월까지 월별로 나눠서 조회
"""

import subprocess
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

def get_month_range(year, month):
    """해당 월의 시작일과 종료일 반환"""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1) - timedelta(days=1)
    
    return start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")

def collect_data_by_month(start_year, start_month, end_year, end_month):
    """월별로 데이터 수집"""
    current = datetime(start_year, start_month, 1)
    end = datetime(end_year, end_month, 1)
    
    total_collected = 0
    
    while current <= end:
        year = current.year
        month = current.month
        
        start_dt, end_dt = get_month_range(year, month)
        
        print(f"\n{'='*60}")
        print(f"📅 {year}년 {month}월 데이터 수집 중...")
        print(f"기간: {start_dt} ~ {end_dt}")
        print(f"{'='*60}")
        
        # run_pipeline.py 실행
        cmd = [
            "python", "run_pipeline.py",
            "--credentials", "credentials.json",
            "--start-date", start_dt,
            "--end-date", end_dt
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # 결과 출력
            print(result.stdout)
            
            # 수집 건수 확인
            if "건의 데이터 조회 완료" in result.stdout:
                # 예: "✅ 151건의 데이터 조회 완료"
                for line in result.stdout.split('\n'):
                    if "건의 데이터 조회 완료" in line:
                        count = int(line.split('✅')[1].split('건')[0].strip())
                        total_collected += count
                        print(f"✅ {year}년 {month}월: {count}건 수집")
                        break
            
        except subprocess.TimeoutExpired:
            print(f"⚠️ {year}년 {month}월 조회 시간 초과")
        except Exception as e:
            print(f"❌ {year}년 {month}월 조회 오류: {e}")
        
        # 다음 달로 이동
        current += relativedelta(months=1)
    
    print(f"\n{'='*60}")
    print(f"🎉 전체 수집 완료!")
    print(f"총 수집 건수: {total_collected}건")
    print(f"{'='*60}")

if __name__ == "__main__":
    # 2023년 12월 ~ 2026년 1월
    collect_data_by_month(2023, 12, 2026, 1)
