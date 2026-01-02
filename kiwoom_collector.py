"""
키움증권 REST API를 이용한 실현손익 데이터 수집 모듈

64비트 Python 환경에서 사용 가능합니다.
필수 패키지: requests, pandas
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import json
try:
    from config import KIWOOM_REST_API_BASE_URL
except ImportError:
    # config.py가 없는 경우(배포 환경 등) 기본값 사용
    KIWOOM_REST_API_BASE_URL = "https://api.kiwoom.com"


class KiwoomRestCollector:
    """키움 REST API 데이터 수집 클래스"""
    
    def __init__(self, app_key, app_secret, account_number=None):
        """
        초기화
        
        Args:
            app_key: 키움 REST API App Key
            app_secret: 키움 REST API App Secret
            account_number: 계좌번호 (선택)
        """
        self.base_url = KIWOOM_REST_API_BASE_URL
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_number = account_number
        self.access_token = None
        self.token_expires_at = None
        
    def authenticate(self):
        """
        OAuth 인증 및 액세스 토큰 발급 (au10001)
        
        Returns:
            bool: 인증 성공 여부
        """
        try:
            print("🔐 키움 REST API 인증 중...")
            
            url = f"{self.base_url}/oauth2/token"
            
            headers = {
                "Content-Type": "application/json;charset=UTF-8"
            }
            
            body = {
                "grant_type": "client_credentials",
                "appkey": self.app_key,
                "secretkey": self.app_secret
            }
            
            response = requests.post(url, json=body, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # 응답 확인
                if data.get("return_code") != 0:
                    print(f"❌ 인증 실패: {data.get('return_msg')}")
                    return False
                
                self.access_token = data.get("token")  # 키움은 'token' 필드 사용
                
                # 만료일시 파싱 (YYYYMMDDHHmmss)
                expires_dt = data.get("expires_dt")
                if expires_dt:
                    self.token_expires_at = datetime.strptime(expires_dt, "%Y%m%d%H%M%S")
                else:
                    self.token_expires_at = datetime.now() + timedelta(hours=24)
                
                print("✅ 인증 성공")
                print(f"📅 토큰 만료 시간: {self.token_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
                return True
            else:
                print(f"❌ 인증 실패: {response.status_code}")
                print(f"응답: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 인증 오류: {e}")
            return False
    
    def _check_token_validity(self):
        """토큰 유효성 확인 및 갱신"""
        if not self.access_token or not self.token_expires_at:
            return self.authenticate()
        
        # 만료 5분 전에 갱신
        if datetime.now() >= self.token_expires_at - timedelta(minutes=5):
            print("🔄 토큰 갱신 중...")
            return self.authenticate()
        
        return True
    
    def get_realized_profit(self, start_date=None, end_date=None, stock_code=""):
        """
        일자별종목별실현손익요청_기간 (ka10073)
        
        Args:
            start_date: 조회 시작일 (YYYYMMDD), None이면 오늘
            end_date: 조회 종료일 (YYYYMMDD), None이면 오늘
            stock_code: 종목코드 (선택, 빈 문자열이면 전체)
            
        Returns:
            DataFrame: 실현손익 데이터
        """
        if not self._check_token_validity():
            print("❌ 토큰 인증 실패")
            return None
        
        # 날짜 설정
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        if not start_date:
            start_date = end_date
        
        try:
            print(f"📥 실현손익 조회 중... ({start_date} ~ {end_date})")
            
            url = f"{self.base_url}/api/dostk/acnt"
            
            headers = {
                "Content-Type": "application/json;charset=UTF-8",
                "api-id": "ka10073",  # TR 코드
                "authorization": f"Bearer {self.access_token}"
            }
            
            body = {
                "stk_cd": stock_code,  # 종목코드 (빈 문자열이면 전체)
                "strt_dt": start_date,  # 시작일자 (YYYYMMDD)
                "end_dt": end_date  # 종료일자 (YYYYMMDD)
            }
            
            # 연속조회 처리
            all_data = []
            cont_yn = ""
            next_key = ""
            
            while True:
                # 연속조회 헤더 추가
                if cont_yn == "Y":
                    headers["cont-yn"] = cont_yn
                    headers["next-key"] = next_key
                
                response = requests.post(url, json=body, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 응답 데이터 확인
                    if "dt_stk_rlzt_pl" in data:
                        records = data["dt_stk_rlzt_pl"]
                        if records:
                            all_data.extend(records)
                        
                        # 연속조회 여부 확인
                        cont_yn = response.headers.get("cont-yn", "")
                        next_key = response.headers.get("next-key", "")
                        
                        if cont_yn != "Y":
                            break
                    else:
                        print(f"⚠️ 예상치 못한 응답 형식: {data}")
                        break
                else:
                    print(f"❌ API 요청 실패: {response.status_code}")
                    print(f"응답: {response.text}")
                    return None
            
            if not all_data:
                print("⚠️ 조회된 데이터가 없습니다.")
                return pd.DataFrame()
            
            # DataFrame 변환
            df = pd.DataFrame(all_data)
            df = self._clean_dataframe(df)
            
            print(f"✅ {len(df)}건의 데이터 조회 완료")
            return df
                
        except Exception as e:
            print(f"❌ 데이터 조회 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _clean_dataframe(self, df):
        """데이터프레임 정리 및 컬럼명 표준화"""
        # 키움 REST API 응답 컬럼명 매핑
        column_mapping = {
            'dt': '날짜',
            'stk_nm': '종목명',
            'stk_cd': '종목코드',
            'cntr_pric': '체결가',
            'cntr_qty': '체결량',
            'tdy_sel_pl': '실현손익',
            'pl_rt': '수익률',
        }
        
        # 존재하는 컬럼만 선택
        available_columns = [col for col in column_mapping.keys() if col in df.columns]
        
        if not available_columns:
            print("⚠️ 예상된 컬럼을 찾을 수 없습니다. 원본 데이터를 반환합니다.")
            print(f"실제 컬럼: {df.columns.tolist()}")
            return df
        
        df = df[available_columns].copy()
        df.rename(columns=column_mapping, inplace=True)
        
        # 데이터 타입 변환
        if '날짜' in df.columns:
            df['날짜'] = pd.to_datetime(df['날짜'], format='%Y%m%d', errors='coerce')
        
        if '체결가' in df.columns:
            df['체결가'] = pd.to_numeric(df['체결가'], errors='coerce')
        
        if '체결량' in df.columns:
            df['체결량'] = pd.to_numeric(df['체결량'], errors='coerce')
        
        if '실현손익' in df.columns:
            df['실현손익'] = pd.to_numeric(df['실현손익'], errors='coerce')
        
        if '수익률' in df.columns:
            # +61.28 형식에서 숫자만 추출
            df['수익률'] = df['수익률'].astype(str).str.replace('+', '').str.replace('%', '')
            df['수익률'] = pd.to_numeric(df['수익률'], errors='coerce')
        
        # 종목코드에서 'A' 제거 (A005930 -> 005930)
        if '종목코드' in df.columns:
            df['종목코드'] = df['종목코드'].astype(str).str.replace('A', '', regex=False)
        
        return df
    
    def get_sample_data(self):
        """테스트용 샘플 데이터 생성"""
        print("📝 샘플 데이터 생성 중...")
        
        sample_data = {
            '날짜': pd.date_range(start='2024-01-01', periods=10, freq='D'),
            '종목명': ['삼성전자', 'SK하이닉스', 'NAVER', '카카오', 'LG에너지솔루션'] * 2,
            '종목코드': ['005930', '000660', '035420', '035720', '373220'] * 2,
            '체결가': [70000, 120000, 180000, 50000, 450000] * 2,
            '체결량': [10, 5, 3, 8, 2] * 2,
            '실현손익': [50000, -20000, 30000, 15000, -10000] * 2,
            '수익률': [7.14, -1.64, 2.00, 4.29, -0.22] * 2,
        }
        
        df = pd.DataFrame(sample_data)
        print(f"✅ {len(df)}건의 샘플 데이터 생성 완료")
        return df


def main():
    """메인 실행 함수"""
    import sys
    import argparse
    try:
        from config import KIWOOM_APP_KEY, KIWOOM_APP_SECRET, KIWOOM_ACCOUNT
    except ImportError:
        # 배포 환경에서는 streamlit secrets에서 로드 시도
        try:
            import streamlit as st
            kiwoom_secrets = st.secrets.get("kiwoom", {})
            KIWOOM_APP_KEY = kiwoom_secrets.get("app_key", "")
            KIWOOM_APP_SECRET = kiwoom_secrets.get("app_secret", "")
            KIWOOM_ACCOUNT = kiwoom_secrets.get("account", "")
        except:
            KIWOOM_APP_KEY = ""
            KIWOOM_APP_SECRET = ""
            KIWOOM_ACCOUNT = ""
    
    print("=" * 50)
    print("키움증권 REST API 실현손익 데이터 수집기")
    print("=" * 50)
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--test', action='store_true', help='테스트 모드 (샘플 데이터)')
    parser.add_argument('--app-key', type=str, default=KIWOOM_APP_KEY, help='App Key')
    parser.add_argument('--app-secret', type=str, default=KIWOOM_APP_SECRET, help='App Secret')
    parser.add_argument('--account', type=str, default=KIWOOM_ACCOUNT, help='계좌번호')
    parser.add_argument('--start-date', type=str, default=None, help='시작일자 (YYYYMMDD)')
    parser.add_argument('--end-date', type=str, default=None, help='종료일자 (YYYYMMDD)')
    args = parser.parse_args()
    
    if args.test:
        print("\n🧪 테스트 모드: 샘플 데이터 사용")
        collector = KiwoomRestCollector("", "")
        df = collector.get_sample_data()
    else:
        if not args.app_key or not args.app_secret:
            print("❌ App Key와 App Secret이 필요합니다.")
            print("💡 config.py에 설정하거나 --app-key, --app-secret 옵션을 사용하세요.")
            return
        
        print("\n🔐 키움 REST API 인증 중...")
        collector = KiwoomRestCollector(args.app_key, args.app_secret, args.account)
        
        if not collector.authenticate():
            print("❌ 인증 실패. 프로그램을 종료합니다.")
            return
        
        # 실현손익 조회
        df = collector.get_realized_profit(
            start_date=args.start_date,
            end_date=args.end_date
        )
    
    if df is not None and not df.empty:
        print("\n📊 조회 결과:")
        print(df.head())
        print(f"\n총 {len(df)}건")
        
        # CSV로 저장
        output_file = "kiwoom_data.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 데이터 저장 완료: {output_file}")
        
        return df
    else:
        print("\n❌ 데이터를 가져올 수 없습니다.")
        return None


if __name__ == "__main__":
    main()
