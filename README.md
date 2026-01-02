# 키움증권 실현손익 시각화 프로젝트

키움증권 REST API를 통해 실현손익 데이터를 수집하고, 구글 시트에 저장한 후, Streamlit Cloud로 시각화하는 전체 파이프라인입니다.

## 📋 프로젝트 구조

```
Kiwoom-Profit-Visualizer/
├── kiwoom_collector.py        # 키움 REST API 데이터 수집 모듈
├── google_sheet_manager.py    # 구글 시트 연동 모듈
├── streamlit_app.py            # Streamlit 대시보드
├── run_pipeline.py             # 통합 실행 스크립트
├── config.py                   # 설정 파일
├── requirements.txt            # Python 패키지 목록
├── requirements_windows.txt    # 윈도우용 패키지 목록
├── .gitignore                  # Git 제외 파일
└── README.md                   # 프로젝트 문서
```

## 🎯 주요 기능

- ✅ **키움 REST API** 연동을 통한 실현손익 데이터 수집 (64비트 Python 사용 가능)
- ✅ **원클릭 동기화**: 대시보드 내 **Sync** 버튼으로 간편하게 최신 데이터 업데이트
- ✅ **구글 시트**를 데이터베이스로 활용 (날짜 기준 Upsert)
- ✅ **프리미엄 UI V2.0**: 글래스모피즘(Glassmorphism) 기반의 현대적이고 세련된 디자인
- ✅ **3단계 드릴다운**: 연도별 → 월별 → 일별로 이어지는 정밀한 데이터 분석
- ✅ **동적 차트 시스템**: 드릴다운 단계와 실시간 연동되는 고해상도 시각화
- ✅ **모바일 최적화**: Streamlit Cloud를 통한 언제 어디서나 접근 가능한 대시보드
- ✅ **OS 무관**: Windows/Mac/Linux 모두 지원

## 🚀 시작하기

### 1단계: 환경 준비

#### Python 환경 설정 (64비트 Python 사용 가능)

```bash
# Python 3.8 이상 권장
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

#### 키움 REST API 설정

1. **키움증권 OpenAPI 사이트** 접속: https://openapi.kiwoom.com/
2. **회원가입** 및 **로그인**
3. **App Key 발급**:
   - 마이페이지 > API 관리 > 앱 등록
   - App Key와 App Secret 발급받기
4. **config.py** 파일에 설정:
   ```python
   KIWOOM_APP_KEY = "발급받은_APP_KEY"
   KIWOOM_APP_SECRET = "발급받은_APP_SECRET"
   KIWOOM_ACCOUNT = "계좌번호"  # 예: 1234567890
   ```

#### 구글 클라우드 설정

1. **구글 클라우드 콘솔** 접속: https://console.cloud.google.com/
2. **새 프로젝트** 생성
3. **API 활성화**:
   - Google Sheets API
   - Google Drive API
4. **서비스 계정** 생성:
   - IAM 및 관리자 > 서비스 계정
   - 서비스 계정 만들기
   - JSON 키 다운로드 → `credentials.json`으로 저장
5. **구글 시트** 생성:
   - 새 스프레드시트 생성: "키움_실현손익_데이터"
   - 서비스 계정 이메일에 **편집자** 권한 부여

### 2단계: 데이터 수집 및 동기화

본 프로젝트는 대시보드 내에서 직접 데이터를 수집하고 동기화하는 기능을 제공합니다.

1. **로컬 실행**: `python streamlit_app.py` 명령으로 대시보드를 실행합니다.
2. **동기화**: 사이드바의 **🚀 Sync Kiwoom API** 버튼을 클릭하여 최신 실현손익을 수집하고 구글 시트에 업데이트합니다.

> **참고**: 커맨드라인 환경에서 직접 실행하려면 `python run_pipeline.py`를 사용할 수 있습니다.

### 3단계: Streamlit 대시보드 배포

#### GitHub 저장소 생성

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/Kiwoom-Profit-Visualizer.git
git push -u origin main
```

#### Streamlit Cloud 배포

1. **Streamlit Cloud** 접속: https://streamlit.io/cloud
2. **Sign in with GitHub** 클릭
3. **New app** 클릭
4. **Main file path**: `streamlit_app.py`
5. **Secrets** 설정:

```toml
# Streamlit Cloud > Settings > Secrets에 추가

sheet_name = "키움_실현손익_데이터"
worksheet_name = "실현손익"

[gcp_service_account]
type = "service_account"
project_id = "YOUR_PROJECT_ID"
private_key_id = "YOUR_PRIVATE_KEY_ID"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_PRIVATE_KEY\n-----END PRIVATE KEY-----\n"
client_email = "YOUR_SERVICE_ACCOUNT_EMAIL"
client_id = "YOUR_CLIENT_ID"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "YOUR_CERT_URL"
```

6. **Deploy** 클릭

## 📱 사용 방법

### 실시간 데이터 업데이트 (Sync)

대시보드 사이드바의 **Settings** 메뉴에서 두 가지 업데이트 방식을 제공합니다:

1. **🔄 Refresh Dashboard**: 구글 시트에 이미 저장된 데이터를 화면에 다시 불러옵니다.
2. **🚀 Sync Kiwoom API**: 키움증권 서버에서 최근 15일간의 새로운 거래 내역을 수집하여 구글 시트에 저장하고 화면을 갱신합니다.

### 모바일/PC에서 대시보드 접속

Streamlit Cloud 배포 후 제공되는 URL로 접속:
```
https://YOUR_APP_NAME.streamlit.app
```

## 🔧 설정 파일

### config.py

```python
# 구글 시트 설정
GOOGLE_SHEET_NAME = "키움_실현손익_데이터"
WORKSHEET_NAME = "실현손익"

# 키움 REST API 설정
KIWOOM_APP_KEY = "발급받은_APP_KEY"
KIWOOM_APP_SECRET = "발급받은_APP_SECRET"
KIWOOM_ACCOUNT = "계좌번호"
```

## ⚠️ 주의사항

> **64비트 Python 사용 가능**
> 
> 키움 REST API는 32/64비트 제약이 없습니다. 일반적인 64비트 Python 환경에서 사용 가능합니다.

> **API 호출 제한**
> 
> 키움 API는 초당 조회 횟수 제한이 있습니다. 과도한 요청 시 계정이 일시적으로 차단될 수 있습니다.

> **인증 정보 보안**
> 
> `credentials.json` 및 `config.py`의 App Key/Secret은 절대 GitHub에 커밋하지 마세요. `.gitignore`에 포함되어 있는지 확인하세요.

## 🐛 문제 해결

### 키움 REST API 인증 실패

- App Key와 App Secret 확인
- 키움 OpenAPI 사이트에서 API 상태 확인
- `config.py`에 올바르게 설정되었는지 확인

### 구글 시트 권한 오류

- 서비스 계정 이메일에 편집 권한 부여 확인
- `credentials.json` 파일 경로 확인
- API 활성화 상태 확인

### Streamlit 배포 오류

- `requirements.txt` 패키지 버전 확인
- Secrets 설정 확인 (JSON 형식 주의)
- 로그 확인 후 오류 메시지 분석

## 📊 대시보드 기능

- **프리미엄 대시보드**: 글래스모피즘 디자인 및 현대적인 색상 시스템 적용
- **3단계 드릴다운**: 연도 → 월 → 일 단위의 계층적 데이터 탐색
- **동적 실현손익 차트**: 드릴다운 수준에 맞춰 자동 업데이트되는 막대 그래프
- **종목별 분석**: 상위 수익 종목 분석 (Top 10 고정 및 최적화된 레이아웃)
- **상세 거래 내역**: 기간별/종목별 필터링 및 숫자 데이터 우정렬 최적화
- **반응형 내비게이션**: 사이드바를 통한 앵커 기반의 매끄러운 섹션 이동

## 🆚 REST API vs OpenAPI+ 비교

| 항목 | OpenAPI+ (ActiveX) | REST API |
|------|-------------------|----------|
| **Python 버전** | 32비트 필수 | 64비트 가능 ✅ |
| **OS** | 윈도우 전용 | OS 무관 ✅ |
| **설치** | ActiveX 설치 필요 | 불필요 ✅ |
| **라이브러리** | PyQt5, pykiwoom | requests만 있으면 됨 ✅ |

## 📝 라이선스

MIT License

## 🤝 기여

이슈 및 풀 리퀘스트를 환영합니다!

## 📧 문의

프로젝트 관련 문의사항은 GitHub Issues를 이용해주세요.
