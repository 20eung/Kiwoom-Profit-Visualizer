"""
키움 API 데이터 수집 → 구글 시트 저장 통합 스크립트

윈도우/Mac/Linux 환경에서 실행 가능 (64비트 Python)
"""

import sys
from kiwoom_collector import KiwoomRestCollector
from google_sheet_manager import GoogleSheetManager
from config import GOOGLE_SHEET_NAME, WORKSHEET_NAME
from config import KIWOOM_APP_KEY, KIWOOM_APP_SECRET, KIWOOM_ACCOUNT
import argparse


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description='키움 REST API 데이터 수집 및 구글 시트 저장')
    parser.add_argument('--test', action='store_true', help='테스트 모드 (샘플 데이터 사용)')
    parser.add_argument('--credentials', type=str, default='credentials.json', 
                        help='구글 서비스 계정 JSON 파일 경로')
    parser.add_argument('--app-key', type=str, default=KIWOOM_APP_KEY, help='키움 App Key')
    parser.add_argument('--app-secret', type=str, default=KIWOOM_APP_SECRET, help='키움 App Secret')
    parser.add_argument('--account', type=str, default=KIWOOM_ACCOUNT, help='계좌번호')
    parser.add_argument('--start-date', type=str, default=None, help='조회 시작일 (YYYYMMDD)')
    parser.add_argument('--end-date', type=str, default=None, help='조회 종료일 (YYYYMMDD)')
    args = parser.parse_args()
    
    print("=" * 60)
    print("키움 REST API → 구글 시트 데이터 파이프라인")
    print("=" * 60)
    
    # 1단계: 키움 REST API 데이터 수집
    print("\n[1단계] 키움 REST API 데이터 수집")
    print("-" * 60)
    
    collector = KiwoomRestCollector(args.app_key, args.app_secret, args.account)
    
    if args.test:
        print("🧪 테스트 모드: 샘플 데이터 사용")
        df = collector.get_sample_data()
    else:
        if not args.app_key or not args.app_secret:
            print("❌ App Key와 App Secret이 필요합니다.")
            print("💡 config.py에 설정하거나 --app-key, --app-secret 옵션을 사용하세요.")
            return
        
        print("🔐 키움 REST API 인증 중...")
        if not collector.authenticate():
            print("❌ 인증 실패. 프로그램을 종료합니다.")
            return
        
        df = collector.get_realized_profit(
            start_date=args.start_date,
            end_date=args.end_date
        )
    
    if df is None or df.empty:
        print("❌ 데이터를 가져올 수 없습니다.")
        return
    
    print(f"✅ {len(df)}건의 데이터 수집 완료")
    
    # 2단계: 구글 시트에 저장
    print("\n[2단계] 구글 시트에 저장")
    print("-" * 60)
    
    try:
        # 구글 시트 매니저 초기화
        manager = GoogleSheetManager(credentials_file=args.credentials)
        
        # 시트 열기
        if not manager.open_sheet(GOOGLE_SHEET_NAME, WORKSHEET_NAME):
            print("❌ 구글 시트를 열 수 없습니다.")
            return
        
        # 데이터 Upsert
        if manager.upsert_data(df, key_column='날짜'):
            print("✅ 구글 시트 저장 완료")
            print(f"\n📊 시트 URL: https://docs.google.com/spreadsheets/d/{manager.sheet.id}")
        else:
            print("❌ 구글 시트 저장 실패")
            
    except FileNotFoundError:
        print(f"❌ 인증 파일을 찾을 수 없습니다: {args.credentials}")
        print("💡 구글 클라우드 콘솔에서 서비스 계정 JSON 키를 다운로드하세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    
    print("\n" + "=" * 60)
    print("작업 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
