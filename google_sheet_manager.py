"""
구글 시트 데이터 관리 모듈

gspread를 이용한 구글 시트 읽기/쓰기 및 Upsert 기능 제공
"""

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import streamlit as st
import json


class GoogleSheetManager:
    """구글 시트 관리 클래스"""
    
    def __init__(self, credentials_dict=None, credentials_file=None):
        """
        초기화
        
        Args:
            credentials_dict: 서비스 계정 인증 정보 딕셔너리 (Streamlit Secrets용)
            credentials_file: 서비스 계정 JSON 파일 경로 (로컬 테스트용)
        """
        self.gc = None
        self.sheet = None
        self.worksheet = None
        
        # 인증
        if credentials_dict:
            self._authenticate_from_dict(credentials_dict)
        elif credentials_file:
            self._authenticate_from_file(credentials_file)
        else:
            raise ValueError("credentials_dict 또는 credentials_file 중 하나는 필수입니다.")
    
    def _authenticate_from_dict(self, credentials_dict):
        """딕셔너리로부터 인증 (Streamlit Cloud용)"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_info(
                credentials_dict,
                scopes=scopes
            )
            
            self.gc = gspread.authorize(credentials)
            print("✅ 구글 시트 인증 성공 (딕셔너리)")
            
        except Exception as e:
            print(f"❌ 인증 실패: {e}")
            raise
    
    def _authenticate_from_file(self, credentials_file):
        """파일로부터 인증 (로컬 테스트용)"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            credentials = Credentials.from_service_account_file(
                credentials_file,
                scopes=scopes
            )
            
            self.gc = gspread.authorize(credentials)
            print("✅ 구글 시트 인증 성공 (파일)")
            
        except Exception as e:
            print(f"❌ 인증 실패: {e}")
            raise
    
    def open_sheet(self, sheet_name, worksheet_name="실현손익"):
        """
        구글 시트 열기
        
        Args:
            sheet_name: 구글 시트 이름
            worksheet_name: 워크시트 이름
        """
        try:
            self.sheet = self.gc.open(sheet_name)
            
            # 워크시트가 없으면 생성
            try:
                self.worksheet = self.sheet.worksheet(worksheet_name)
                print(f"✅ 워크시트 '{worksheet_name}' 열기 성공")
            except gspread.WorksheetNotFound:
                self.worksheet = self.sheet.add_worksheet(
                    title=worksheet_name,
                    rows=1000,
                    cols=20
                )
                print(f"✅ 워크시트 '{worksheet_name}' 생성 완료")
            
            return True
            
        except Exception as e:
            print(f"❌ 시트 열기 실패: {e}")
            return False
    
    def read_data(self):
        """
        구글 시트에서 데이터 읽기
        
        Returns:
            DataFrame: 읽어온 데이터
        """
        if not self.worksheet:
            print("❌ 워크시트가 열려있지 않습니다.")
            return None
        
        try:
            # 모든 데이터 가져오기
            data = self.worksheet.get_all_records()
            
            if not data:
                print("⚠️ 시트에 데이터가 없습니다.")
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            
            # 날짜 컬럼 변환
            if '날짜' in df.columns:
                df['날짜'] = pd.to_datetime(df['날짜'], errors='coerce')
            
            print(f"✅ {len(df)}건의 데이터 읽기 완료")
            return df
            
        except Exception as e:
            print(f"❌ 데이터 읽기 실패: {e}")
            return None
    
    def write_data(self, df, mode='replace'):
        """
        구글 시트에 데이터 쓰기
        
        Args:
            df: 저장할 DataFrame
            mode: 'replace' (전체 교체) 또는 'append' (추가)
        """
        if not self.worksheet:
            print("❌ 워크시트가 열려있지 않습니다.")
            return False
        
        try:
            # 날짜 형식 변환
            df_copy = df.copy()
            if '날짜' in df_copy.columns:
                df_copy['날짜'] = df_copy['날짜'].dt.strftime('%Y-%m-%d')
            
            if mode == 'replace':
                # 기존 데이터 삭제 후 새로 쓰기
                self.worksheet.clear()
                self.worksheet.update(
                    [df_copy.columns.values.tolist()] + df_copy.values.tolist()
                )
                print(f"✅ {len(df)}건의 데이터 저장 완료 (전체 교체)")
                
            elif mode == 'append':
                # 기존 데이터에 추가
                self.worksheet.append_rows(df_copy.values.tolist())
                print(f"✅ {len(df)}건의 데이터 추가 완료")
            
            return True
            
        except Exception as e:
            print(f"❌ 데이터 쓰기 실패: {e}")
            return False
    
    def upsert_data(self, new_df, key_column='날짜'):
        """
        날짜 기준으로 데이터 Upsert (업데이트 또는 삽입)
        
        Args:
            new_df: 새로운 데이터 DataFrame
            key_column: 중복 확인 기준 컬럼
        """
        if not self.worksheet:
            print("❌ 워크시트가 열려있지 않습니다.")
            return False
        
        try:
            # 기존 데이터 읽기
            existing_df = self.read_data()
            
            if existing_df is None or existing_df.empty:
                # 기존 데이터가 없으면 그냥 쓰기
                return self.write_data(new_df, mode='replace')
            
            # 날짜 형식 통일
            if key_column in existing_df.columns:
                existing_df[key_column] = pd.to_datetime(existing_df[key_column])
            if key_column in new_df.columns:
                new_df[key_column] = pd.to_datetime(new_df[key_column])
            
            # 기존 데이터에서 중복 제거 후 새 데이터와 병합
            existing_df = existing_df[~existing_df[key_column].isin(new_df[key_column])]
            merged_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # 날짜 기준 정렬
            merged_df = merged_df.sort_values(by=key_column, ascending=False)
            
            # 전체 교체
            result = self.write_data(merged_df, mode='replace')
            
            if result:
                print(f"✅ Upsert 완료: 기존 {len(existing_df)}건 + 신규 {len(new_df)}건 = 총 {len(merged_df)}건")
            
            return result
            
        except Exception as e:
            print(f"❌ Upsert 실패: {e}")
            return False


def main():
    """메인 실행 함수 (테스트용)"""
    import sys
    
    print("=" * 50)
    print("구글 시트 연동 테스트")
    print("=" * 50)
    
    # 테스트 모드 확인
    test_mode = "--test" in sys.argv
    
    if test_mode:
        print("\n🧪 테스트 모드")
        print("⚠️ 실제 구글 시트 연동을 위해서는 서비스 계정 JSON 파일이 필요합니다.")
        print("📝 credentials.json 파일을 프로젝트 루트에 배치하세요.")
        
        # 샘플 데이터 생성
        sample_data = {
            '날짜': pd.date_range(start='2024-01-01', periods=5, freq='D'),
            '종목명': ['삼성전자', 'SK하이닉스', 'NAVER', '카카오', 'LG에너지솔루션'],
            '실현손익': [50000, -20000, 30000, 15000, -10000],
        }
        df = pd.DataFrame(sample_data)
        
        print("\n📊 테스트 데이터:")
        print(df)
        
        # 실제 연동 테스트는 credentials.json이 있을 때만
        try:
            manager = GoogleSheetManager(credentials_file="credentials.json")
            manager.open_sheet("키움_실현손익_데이터", "실현손익")
            manager.upsert_data(df)
        except FileNotFoundError:
            print("\n⚠️ credentials.json 파일이 없어 실제 연동은 건너뜁니다.")
        except Exception as e:
            print(f"\n⚠️ 연동 테스트 중 오류: {e}")
    else:
        print("\n사용법: python google_sheet_manager.py --test")


if __name__ == "__main__":
    main()
