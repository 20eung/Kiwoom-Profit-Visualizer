"""
키움 API 데이터 수집 → 구글 시트 저장 통합 스크립트

윈도우/Mac/Linux 환경에서 실행 가능 (64비트 Python)
"""

import sys
import requests # 텔레그램 전송용
from kiwoom_collector import KiwoomRestCollector
from google_sheet_manager import GoogleSheetManager
try:
    from config import GOOGLE_SHEET_NAME, WORKSHEET_NAME
    from config import KIWOOM_APP_KEY, KIWOOM_APP_SECRET, KIWOOM_ACCOUNT
    from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
except ImportError:
    # config.py가 없는 경우 기본값 및 Streamlit Secrets 활용
    GOOGLE_SHEET_NAME = "키움_실현손익_데이터"
    WORKSHEET_NAME = "실현손익"
    KIWOOM_APP_KEY = ""
    KIWOOM_APP_SECRET = ""
    KIWOOM_ACCOUNT = ""
    TELEGRAM_BOT_TOKEN = ""
    TELEGRAM_CHAT_ID = ""
    
    try:
        import streamlit as st
        if "kiwoom" in st.secrets:
            KIWOOM_APP_KEY = st.secrets["kiwoom"].get("app_key", "")
            KIWOOM_APP_SECRET = st.secrets["kiwoom"].get("app_secret", "")
            KIWOOM_ACCOUNT = st.secrets["kiwoom"].get("account", "")
        GOOGLE_SHEET_NAME = st.secrets.get("sheet_name", GOOGLE_SHEET_NAME)
        WORKSHEET_NAME = st.secrets.get("worksheet_name", WORKSHEET_NAME)
        # 텔레그램 시크릿 (선택)
        if "telegram" in st.secrets:
            TELEGRAM_BOT_TOKEN = st.secrets["telegram"].get("bot_token", "")
            TELEGRAM_CHAT_ID = st.secrets["telegram"].get("chat_id", "")
    except:
        pass
import argparse


def send_telegram_alert(message):
    """텔레그램 메시지 전송"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        response = requests.post(url, data=data, timeout=5)
        if response.status_code != 200:
            print(f"⚠️ 텔레그램 전송 실패: {response.text}")
    except Exception as e:
        print(f"⚠️ 텔레그램 전송 오류: {e}")


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
    
    try:
        # 1단계: 키움 REST API 데이터 수집
        print("\n[1단계] 키움 REST API 데이터 수집")
        print("-" * 60)
        
        collector = KiwoomRestCollector(args.app_key, args.app_secret, args.account)
        
        if args.test:
            print("🧪 테스트 모드: 샘플 데이터 사용")
            df = collector.get_sample_data()
        else:
            if not args.app_key or not args.app_secret:
                error_msg = "❌ App Key와 App Secret이 필요합니다."
                print(error_msg)
                send_telegram_alert(error_msg)
                return
            
            print("🔐 키움 REST API 인증 중...")
            if not collector.authenticate():
                error_msg = "❌ 인증 실패. 프로그램을 종료합니다."
                print(error_msg)
                send_telegram_alert(error_msg)
                return
            
            # 날짜 범위 설정
            from datetime import datetime, timedelta
            import pandas as pd
            import time

            end_date_str = args.end_date if args.end_date else datetime.now().strftime("%Y%m%d")
            start_date_str = args.start_date if args.start_date else end_date_str
            
            # 반복 수집
            print(f"📥 데이터 수집 기간: {start_date_str} ~ {end_date_str}")
            
            start_dt = datetime.strptime(start_date_str, "%Y%m%d")
            end_dt = datetime.strptime(end_date_str, "%Y%m%d")
            
            all_dfs = []
            current_dt = start_dt
            
            while current_dt <= end_dt:
                base_date = current_dt.strftime("%Y%m%d")
                
                # 주말/휴일 체크 로직은 없지만, API가 빈 데이터를 반환하므로 그대로 진행
                # 너무 빠른 요청 방지를 위해 약간의 딜레이
                if len(all_dfs) > 0:
                    time.sleep(0.5) 
                    
                df_daily = collector.get_realized_profit(base_date=base_date)
                
                if df_daily is not None and not df_daily.empty:
                    all_dfs.append(df_daily)
                
                current_dt += timedelta(days=1)
                
            if not all_dfs:
                 msg = "ℹ️ 수집된 데이터가 없습니다. (휴일이거나 거래 없음)"
                 print(msg)
                 # 데이터 없음도 알림을 받을지 여부는 선택적이나, 일단 전송
                 # send_telegram_alert(msg) 
                 return
                 
            # 전체 데이터 병합
            df = pd.concat(all_dfs, ignore_index=True)
             
        
        if df is None or df.empty:
            print("❌ 데이터를 가져올 수 없습니다.")
            return
        
        # 총 수익금 계산
        total_profit = 0
        if '실현손익' in df.columns:
             total_profit = df['실현손익'].sum()

        print(f"✅ 총 {len(df)}건의 데이터 수집 완료 (기간 합계)")
        
        # CSV 파일로 저장 (백업용)
        csv_filename = "collected_data.csv"
        try:
            df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
            print(f"💾 로컬 파일 저장 완료: {csv_filename}")
        except Exception as e:
            print(f"⚠️ 로컬 파일 저장 실패: {e}")
        
        # 2단계: 구글 시트에 저장
        print("\n[2단계] 구글 시트에 저장")
        print("-" * 60)
        
        # 구글 시트 매니저 초기화
        manager = GoogleSheetManager(credentials_file=args.credentials)
        
        # 시트 열기
        if not manager.open_sheet(GOOGLE_SHEET_NAME, WORKSHEET_NAME):
            error_msg = "❌ 구글 시트를 열 수 없습니다."
            print(error_msg)
            send_telegram_alert(error_msg)
            return
        
        # 데이터 Upsert
        if manager.upsert_data(df, key_column='날짜'):
            print("✅ 구글 시트 저장 완료")
            print(f"\n📊 시트 URL: https://docs.google.com/spreadsheets/d/{manager.sheet.id}")
            
            # 성공 알림 전송
            success_msg = (
                f"✅ [키움 실현손익 수집 완료]\n"
                f"- 날짜: {start_date_str} ~ {end_date_str}\n"
                f"- 건수: {len(df)}건\n"
                f"- 손익합계: {total_profit:,.0f}원"
            )
            send_telegram_alert(success_msg)
            
        else:
            error_msg = "❌ 구글 시트 저장 실패"
            print(error_msg)
            send_telegram_alert(error_msg)
                
    except FileNotFoundError:
        error_msg = f"❌ 인증 파일을 찾을 수 없습니다: {args.credentials}"
        print(error_msg)
        print("💡 구글 클라우드 콘솔에서 서비스 계정 JSON 키를 다운로드하세요.")
        send_telegram_alert(error_msg)
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_msg = f"❌ 파이프라인 오류 발생: {str(e)}"
        print(error_msg)
        send_telegram_alert(error_msg)
    
    print("\n" + "=" * 60)
    print("작업 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
