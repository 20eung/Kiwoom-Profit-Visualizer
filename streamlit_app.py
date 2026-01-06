"""
키움증권 실현손익 시각화 대시보드

구글 시트에서 데이터를 읽어와 누적 수익 차트와 통계를 표시합니다.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from google_sheet_manager import GoogleSheetManager
from kiwoom_collector import KiwoomRestCollector
from datetime import datetime, timedelta
import time
import requests


# 페이지 설정
st.set_page_config(
    page_title="키움 실현손익 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"  # 기본적으로 사이드바 숨김
)

# 커스텀 CSS 및 디자인 시스템
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');

    :root {
        --primary: #4F46E5;
        --secondary: #6366F1;
        --positive: #10B981;
        --negative: #F43F5E;
        --background: #F8FAFC;
        --card-bg: rgba(255, 255, 255, 0.8);
        --text-main: #1E293B;
        --text-dim: #64748B;
        --glass-border: rgba(255, 255, 255, 0.3);
        --shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }

    /* 전역 폰트: 기본적인 텍스트 요소에만 적용 */
    html, body {
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* 스트림릿 마크다운 텍스트 */
    [data-testid="stMarkdownContainer"] p, 
    [data-testid="stMarkdownContainer"] h1, 
    [data-testid="stMarkdownContainer"] h2, 
    [data-testid="stMarkdownContainer"] h3,
    [data-testid="stMarkdownContainer"] span {
        font-family: 'Outfit', sans-serif !important;
    }

    /* 버튼 및 입력창 */
    .stButton button, .stSelectbox label, .stRadio label, .stNumberInput label {
        font-family: 'Outfit', sans-serif !important;
    }

    /* [CRITICAL] 익스팬더 헤더 아이콘 깨짐 방지: 헤더 내부 폰트 격리 */
    [data-testid="stExpanderSummary"] * {
        font-family: inherit !important;
    }
    [data-testid="stExpanderSummary"] [data-testid="stMarkdownContainer"] p {
        font-family: 'Outfit', sans-serif !important; /* 텍스트만 다시 적용 */
        font-weight: 700 !important;
    }

    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #EFF6FF 100%);
    }

    [data-testid="stAppViewBlockContainer"] {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        max-width: 1200px !important;
    }

    /* 프리미엄 헤더 */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.2rem;
        letter-spacing: -0.04em;
        white-space: nowrap;
    }

    /* 글래스모피즘 카드 스타일 심화 */
    .stExpander {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 24px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06) !important;
        margin-bottom: 2rem !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stExpander:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.8) !important;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04) !important;
        border: 1px solid rgba(79, 70, 229, 0.2) !important;
    }

    /* 테이블 스타일 리뉴얼 */
    .metric-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin: 0.2rem 0 1.5rem 0;
        border-radius: 12px;
        overflow: hidden;
    }
    .metric-table th {
        background-color: rgba(79, 70, 229, 0.05);
        color: var(--text-main);
        font-weight: 600;
        padding: 0.6rem 1rem;
        text-align: center;
        border-bottom: 1px solid rgba(0,0,0,0.05);
        line-height: 1.2;
    }
    .metric-table td {
        padding: 0.5rem 1rem;
        text-align: right;
        border-bottom: 1px solid rgba(0,0,0,0.02);
        color: var(--text-main);
        line-height: 1.2;
    }
    .metric-table tr:hover {
        background-color: rgba(79, 70, 229, 0.02);
    }
    .metric-table td:first-child {
        text-align: center;
        font-weight: 600;
        color: var(--text-dim);
    }

    .total-row {
        background-color: rgba(79, 70, 229, 0.05) !important;
        font-weight: 700 !important;
    }
    .total-row td {
        border-top: 1px solid rgba(79, 70, 229, 0.2) !important;
    }

    .metric-value {
        font-weight: 700;
    }
    .positive {
        color: var(--positive) !important;
    }
    .negative {
        color: var(--negative) !important;
    }

    /* 사이드바 프리미엄 스타일 */
    [data-testid="stSidebar"] {
        background-color: white !important;
        border-right: 1px solid var(--glass-border) !important;
    }
    [data-testid="stSidebar"] section[data-testid="stSidebarNav"] {
        background-color: transparent !important;
    }

    /* 버튼 스타일 */
    .stButton > button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2) !important;
    }

    /* 주요 지표 섹션 내 모든 버튼 (연도/월/뒤로가기) 정밀 조정 */
    [data-testid="stExpander"] [data-testid="column"] .stButton > button {
        font-size: 0.9rem !important; /* 안내 문구와 동일한 크기 */
        height: 1.5em !important; /* 글꼴 크기의 150% */
        min-height: 1.5em !important;
        padding: 0 !important;
        line-height: 1.5 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        border-radius: 6px !important;
    }
    
    /* 버튼 행 사이의 수직 간격 축소 - 충돌 방지 및 최적화 */
    [data-testid="stExpander"] [data-testid="stVerticalBlock"] {
        gap: 0.6rem !important;
    }
    
    /* 뒤로가기 전용 (투명 배경 유지) */
    [data-testid="stExpander"] [data-testid="column"]:last-child .stButton > button:has(span:contains("←")) {
        background: transparent !important;
        color: var(--primary) !important;
        border: 1px solid rgba(79, 70, 229, 0.3) !important;
    }

    /* 사이드바 바로가기 버튼 전용 */
    div[data-testid="stSidebar"] .stButton > button {
        text-align: left !important;
        justify-content: flex-start !important;
        padding: 0.75rem 1rem !important;
        background-color: transparent !important;
        border: 1px solid transparent !important;
    }
    div[data-testid="stSidebar"] .stButton > button:hover {
        background-color: rgba(79, 70, 229, 0.05) !important;
        color: var(--primary) !important;
    }

    /* 정보 박스 스타일 */
    .stAlert {
        border-radius: 12px !important;
        border: none !important;
        background-color: rgba(79, 70, 229, 0.05) !important;
    }

    /* 익스팬더 디자인 고도화 */
    .stExpander {
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        border-radius: 20px !important;
        overflow: hidden !important;
    }
    [data-testid="stExpanderSummary"] {
        padding: 1rem 1.5rem !important;
        transition: background 0.3s ease !important;
    }
    [data-testid="stExpanderSummary"]:hover {
        background-color: rgba(79, 70, 229, 0.03) !important;
    }

    /* 선택된 월 버튼 (주요 지표 내부) */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%) !important;
        color: white !important;
        border: none !important;
    }

    /* 커스텀 스크롤바 */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb {
        background: #c7c7c7;
        border-radius: 10px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--primary);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)  # 5분 캐시
def load_data():
    """구글 시트에서 데이터 로드"""
    try:
        # Streamlit Secrets에서 인증 정보 가져오기
        credentials_dict = dict(st.secrets["gcp_service_account"])
        
        # 구글 시트 매니저 초기화
        manager = GoogleSheetManager(credentials_dict=credentials_dict)
        
        # 시트 열기
        sheet_name = st.secrets.get("sheet_name", "키움_실현손익_데이터")
        worksheet_name = st.secrets.get("worksheet_name", "실현손익")
        
        if manager.open_sheet(sheet_name, worksheet_name):
            df = manager.read_data()
            
            if df is not None and not df.empty:
                # 날짜 컬럼 확인 및 변환
                if '날짜' in df.columns:
                    df['날짜'] = pd.to_datetime(df['날짜'])
                    df = df.sort_values('날짜')
                
                return df
            else:
                return pd.DataFrame()
        else:
            return None
            
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return None


def sync_with_kiwoom():
    """키움 API 최신 데이터를 수집하여 구글 시트와 동기화"""
    try:
        status_placeholder = st.empty()
        with status_placeholder.status("🚀 키움 API 동기화 시작...", expanded=True) as status:
            # 1. 시크릿 설정 확인
            if "kiwoom" not in st.secrets:
                st.error("❌ **키움 API 설정 누락**")
                st.info("""
                **설정 방법:**
                1. `.streamlit/secrets.toml` 파일을 열거나 Streamlit Cloud의 Secrets 설정으로 이동합니다.
                2. 아래 형식을 추가해주세요:
                ```toml
                [kiwoom]
                app_key = "YOUR_APP_KEY"
                app_secret = "YOUR_APP_SECRET"
                account = "YOUR_ACCOUNT_NUMBER"
                ```
                """)
                return False
                
            kiwoom_secrets = st.secrets["kiwoom"]
            app_key = kiwoom_secrets.get("app_key")
            app_secret = kiwoom_secrets.get("app_secret")
            account = kiwoom_secrets.get("account")
            
            # 2. 키움 API 인증
            status.write("🔐 키움 REST API 인증 중...")
            collector = KiwoomRestCollector(app_key, app_secret, account)
            if not collector.authenticate():
                status.update(label="❌ 키움 API 인증 실패", state="error")
                return False
                
            # 3. 데이터 수집 (최근 15일치 수집하여 안전성 확보)
            status.write("📥 최신 실현손익 데이터 수집 중...")
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=15)).strftime("%Y%m%d")
            
            new_df = collector.get_realized_profit(start_date=start_date, end_date=end_date)
            
            if new_df is None or new_df.empty:
                status.update(label="⚠️ 수집된 새로운 데이터가 없습니다.", state="complete")
                time.sleep(2)
                status_placeholder.empty()
                return True

            status.write(f"✅ {len(new_df)}건의 데이터 수집 완료")
            
            # 4. 구글 시트 저장
            status.write("💾 구글 시트에 데이터 업로드 중...")
            credentials_dict = dict(st.secrets["gcp_service_account"])
            sheet_manager = GoogleSheetManager(credentials_dict=credentials_dict)
            
            sheet_name = st.secrets.get("sheet_name", "키움_실현손익_데이터")
            worksheet_name = st.secrets.get("worksheet_name", "실현손익")
            
            if sheet_manager.open_sheet(sheet_name, worksheet_name):
                if sheet_manager.upsert_data(new_df, key_column='날짜'):
                    status.update(label="🎉 동기화 성공! 대시보드를 갱신합니다.", state="complete")
                    st.cache_data.clear()
                    time.sleep(2)
                    status_placeholder.empty()
                    return True
                else:
                    status.update(label="❌ 구글 시트 업로드 실패", state="error")
            else:
                status.update(label="❌ 구글 시트를 열 수 없습니다.", state="error")
                
        return False
        
    except Exception as e:
        st.error(f"동기화 중 오류 발생: {e}")
        return False


def calculate_statistics(df):
    """통계 계산"""
    if df is None or df.empty:
        return None
    
    stats = {
        '총_거래건수': len(df),
        '총_실현손익': df['실현손익'].sum() if '실현손익' in df.columns else 0,
        '평균_수익': df['실현손익'].mean() if '실현손익' in df.columns else 0,
        '최대_수익': df['실현손익'].max() if '실현손익' in df.columns else 0,
        '최대_손실': df['실현손익'].min() if '실현손익' in df.columns else 0,
    }
    
    # 승률 계산
    if '실현손익' in df.columns:
        profitable_trades = len(df[df['실현손익'] > 0])
        stats['승률'] = (profitable_trades / len(df) * 100) if len(df) > 0 else 0
    else:
        stats['승률'] = 0
    
    return stats


def get_date_range(period, df):
    """날짜 범위 계산"""
    if df is None or df.empty or '날짜' not in df.columns:
        return None, None
    
    max_date = df['날짜'].max().date()
    
    if period == "오늘":
        return max_date, max_date
    elif period == "이번주":
        # 이번 주 월요일부터
        start_date = max_date - timedelta(days=max_date.weekday())
        return start_date, max_date
    elif period == "이번달":
        # 이번 달 1일부터
        start_date = max_date.replace(day=1)
        return start_date, max_date
    elif period == "올해":
        # 올해 1월 1일부터
        start_date = max_date.replace(month=1, day=1)
        return start_date, max_date
    elif period == "전체":
        min_date = df['날짜'].min().date()
        return min_date, max_date
    else:  # 사용자화
        return None, None


def plot_performance_chart(df, view_type='연도별', title='실현손익 추이'):
    """연도별/월별/일별 실현손익 막대 차트"""
    if df is None or df.empty or '실현손익' not in df.columns:
        return None
    
    # 뷰 타입에 따른 데이터 집계 (정렬 키 포함)
    plot_df = df.copy()
    if view_type == '연도별':
        plot_df['sort_key'] = plot_df['날짜'].dt.year
        plot_df['group'] = plot_df['sort_key'].astype(str) + "년"
        x_label = '연도'
    elif view_type == '월별':
        plot_df['sort_key'] = plot_df['날짜'].dt.month
        plot_df['group'] = plot_df['sort_key'].astype(str) + "월"
        x_label = '월'
    else:  # 일별
        plot_df['sort_key'] = plot_df['날짜'].dt.day
        plot_df['group'] = plot_df['sort_key'].astype(str) + "일"
        x_label = '일'
        
    # group과 x_label 매핑을 유지하며 sort_key로 정렬
    chart_data = plot_df.groupby(['sort_key', 'group'])['실현손익'].sum().reset_index().sort_values('sort_key')
    chart_data = chart_data[['group', '실현손익']]
    chart_data.columns = [x_label, '실현손익']
    chart_data['실현손익_만원'] = chart_data['실현손익'] / 10000
    
    # Plotly 차트 생성
    fig = go.Figure()
    
    # 세련된 Emerald/Rose 팔레트 적용
    colors = ['#10B981' if x >= 0 else '#F43F5E' for x in chart_data['실현손익_만원']]
    
    fig.add_trace(go.Bar(
        x=chart_data[x_label],
        y=chart_data['실현손익_만원'],
        marker=dict(
            color=colors,
            line=dict(width=0),
            opacity=0.9
        ),
        text=chart_data['실현손익_만원'].apply(lambda x: f'{x:,.0f}'),
        textposition='outside',
        textfont=dict(family="Outfit, sans-serif", size=11, color="#1E293B"),
        hovertemplate='%{x}: <b>%{y:,.1f}만원</b><extra></extra>'
    ))
    
    # 상단 수치가 잘리지 않도록 Y축 범위 여유 있게 자동 설정 (15% 여유)
    y_max = chart_data['실현손익_만원'].max()
    y_min = chart_data['실현손익_만원'].min()
    y_range_pad = (y_max - y_min) * 0.15 if y_max != y_min else 10
    
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(family="Outfit, sans-serif", size=18, color="#1E293B", weight=700),
            x=0,
            y=0.98
        ),
        xaxis=dict(
            title='',
            tickfont=dict(family="Outfit, sans-serif", size=12, color="#64748B"),
            showgrid=False
        ),
        yaxis=dict(
            title=dict(text='실현손익 (만원)', font=dict(family="Outfit, sans-serif", size=12, color="#64748B")),
            tickfont=dict(family="Outfit, sans-serif", size=12, color="#64748B"),
            gridcolor='rgba(0,0,0,0.05)',
            zeroline=True,
            zerolinecolor='rgba(0,0,0,0.1)',
            zerolinewidth=2,
            range=[y_min - (y_range_pad * 0.1), y_max + y_range_pad] # 상단 여유 확보
        ),
        height=280, # 400에서 70% 수준으로 축소
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=60, b=40),
        showlegend=False
    )
    
    return fig


def plot_cumulative_profit(df):
    """누적 수익 차트"""
    if df is None or df.empty or '실현손익' not in df.columns:
        return None
    
    # 누적 수익 계산
    df_sorted = df.sort_values('날짜')
    df_sorted['누적수익'] = df_sorted['실현손익'].cumsum()
    df_sorted['누적수익_만원'] = df_sorted['누적수익'] / 10000  # 만원 단위로 변환
    
    # Plotly 차트 생성
    fig = go.Figure()
    
    # 누적 수익 라인
    fig.add_trace(go.Scatter(
        x=df_sorted['날짜'],
        y=df_sorted['누적수익_만원'],
        mode='lines+markers',
        name='누적 수익',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=6),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.1)',
        hovertemplate='%{y:,.0f}만원<extra></extra>'
    ))
    
    # 0 기준선
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    # 레이아웃 설정
    fig.update_layout(
        title='누적 실현손익 추이',
        xaxis_title='날짜',
        yaxis_title='누적 수익 (만원)',
        hovermode='x unified',
        height=500,
        template='plotly_white'
    )
    
    # y축 포맷 설정
    fig.update_yaxes(tickformat=',')
    
    return fig


def plot_stock_performance(df, top_n=None):
    """종목별 수익 현황"""
    if df is None or df.empty or '종목명' not in df.columns or '실현손익' not in df.columns:
        return None
    
    # 종목별 집계
    stock_summary = df.groupby('종목명')['실현손익'].agg(['sum', 'count']).reset_index()
    stock_summary.columns = ['종목명', '총수익', '거래횟수']
    stock_summary['총수익_만원'] = stock_summary['총수익'] / 10000  # 만원 단위로 변환
    stock_summary = stock_summary.sort_values('총수익_만원', ascending=True)
    
    # Top N 필터링
    if top_n and top_n > 0:
        # 상위 N개만 선택 (수익이 높은 순)
        stock_summary = stock_summary.nlargest(top_n, '총수익_만원')
        stock_summary = stock_summary.sort_values('총수익_만원', ascending=True)
    
    # 막대 차트
    fig = go.Figure()
    
    # 세련된 Emerald/Rose 팔레트 적용
    colors = ['#10B981' if x > 0 else '#F43F5E' for x in stock_summary['총수익_만원']]
    
    fig.add_trace(go.Bar(
        x=stock_summary['총수익_만원'],
        y=stock_summary['종목명'],
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(width=0),
            opacity=0.9
        ),
        text=stock_summary['총수익_만원'].apply(lambda x: f'{x:,.0f}만원'),
        textposition='outside',
        textfont=dict(family="Outfit, sans-serif", size=12, color="#1E293B", weight=600),
        cliponaxis=False,
        hovertemplate='<b>%{y}</b><br>실현손익: %{x:,.0f}만원<extra></extra>'
    ))
    
    chart_height = max(320, len(stock_summary) * 42)  
    
    # 우측 수치가 잘리지 않도록 X축 범위 여유 있게 자동 설정 (15% 여유)
    x_max = stock_summary['총수익_만원'].max()
    x_min = stock_summary['총수익_만원'].min()
    x_range_pad = (x_max - x_min) * 0.15 if x_max != x_min else 10

    fig.update_layout(
        title=dict(
            text=f'종목별 실현손익 {"(Top " + str(top_n) + ")" if top_n else ""}',
            font=dict(family="Outfit, sans-serif", size=20, color="#1E293B", weight=700),
            x=0,
            y=0.98
        ),
        xaxis=dict(
            visible=False,
            showgrid=False,
            zeroline=False,
            range=[x_min - (x_range_pad * 0.1), x_max + x_range_pad] # 우측 여유 확보
        ),
        yaxis=dict(
            tickfont=dict(family="Outfit, sans-serif", size=13, color="#1E293B", weight=500),
            automargin=True
        ),
        height=chart_height,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=80, t=50, b=20),
        bargap=0.2,
        showlegend=False
    )
    
    return fig


def main():
    """메인 앱"""
    
    # 헤더
    # 헤더 섹션
    st.markdown('<div class="main-header">Realized Profit Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: var(--text-dim); margin-top: -0.5rem; margin-bottom: 2.5rem; font-size: 1.1rem;">키움증권 실현손익 프리미엄 대시보드</p>', unsafe_allow_html=True)
    
    # 데이터 로드
    with st.spinner("데이터 로딩 중..."):
        df = load_data()
    
    if df is None:
        st.error("❌ 데이터를 불러올 수 없습니다. Streamlit Secrets 설정을 확인하세요.")
        st.stop()
    
    if df.empty:
        st.warning("⚠️ 아직 데이터가 없습니다. 키움 API에서 데이터를 수집해주세요.")
        st.stop()
    
    # Session state 초기화
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = None
    if 'selected_month' not in st.session_state:
        st.session_state.selected_month = None
    
    # 사이드바 리뉴얼
    with st.sidebar:
        st.markdown('<h2 style="color: var(--primary); font-weight: 700;">Settings</h2>', unsafe_allow_html=True)
        
        # 1. 화면 새로고침 버튼
        if st.button("🔄 Refresh Dashboard", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        st.caption("구글 시트의 최신 데이터를 화면에 즉시 다시 불러옵니다.")
        
        st.markdown('<div style="margin: 0.8rem 0;"></div>', unsafe_allow_html=True)
        
        # 2. 키움 API 동기화 버튼
        sync_btn = st.button("🚀 Sync Kiwoom API", use_container_width=True)
        st.caption("키움증권에서 최근 15일간의 실현손익을 수집하여 시트와 동기화합니다.")
            
        if sync_btn:
            if sync_with_kiwoom():
                st.rerun()
        
        st.markdown('<div style="margin: 1.5rem 0; border-bottom: 1px solid rgba(0,0,0,0.05);"></div>', unsafe_allow_html=True)

        # 3. 임시 IP 확인 (화이트리스트 설정용)
        with st.expander("🌐 Cloud IP 확인", expanded=False):
            try:
                current_ip = requests.get('https://api.ipify.org', timeout=5).text
                st.code(current_ip, language="bash")
                st.caption("위 IP를 키움 API 설정의 '허용 IP'에 등록해 주세요. (주의: 배포 시마다 바뀔 수 있음)")
            except:
                st.error("IP 정보를 가져올 수 없습니다.")
        
        # 프리미엄 네비게이션 메뉴
        st.markdown('<p style="font-weight: 600; color: var(--text-dim); margin-bottom: 0.5rem; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.05em;">Navigation</p>', unsafe_allow_html=True)
        
        st.components.v1.html("""
        <div id="nav-menu">
            <button class="nav-item" onclick="scrollApp(0)">
                <span class="icon">📈</span> Metrics
            </button>
            <button class="nav-item" onclick="scrollApp(1)">
                <span class="icon">📋</span> Transactions
            </button>
            <button class="nav-item" onclick="scrollApp(2)">
                <span class="icon">📊</span> Stocks
            </button>
        </div>
        
        <script>
            function scrollApp(index) {
                try {
                    const mainSection = window.parent.document.querySelector('section.stMain');
                    const expanders = window.parent.document.querySelectorAll('[data-testid="stExpander"]');
                    if (expanders && expanders.length > index) {
                        const target = expanders[index];
                        const rect = target.getBoundingClientRect();
                        const scrollTop = mainSection.scrollTop + rect.top - 100; // 100px 여백으로 타이틀바 확보
                        
                        mainSection.scrollTo({
                            top: Math.max(0, scrollTop),
                            behavior: 'smooth'
                        });
                    }
                } catch (e) { console.error(e); }
            }
        </script>
        
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@500&display=swap');
            #nav-menu { display: flex; flex-direction: column; gap: 8px; font-family: 'Outfit', sans-serif; }
            .nav-item {
                display: flex; align-items: center; padding: 12px 16px; width: 100%;
                background: rgba(79, 70, 229, 0.03); border: 1px solid transparent;
                border-radius: 12px; color: #1E293B; cursor: pointer; font-size: 14px;
                font-weight: 500; transition: all 0.2s; text-align: left;
            }
            .nav-item:hover {
                background: rgba(79, 70, 229, 0.08); color: #4F46E5;
                border: 1px solid rgba(79, 70, 229, 0.1); transform: translateX(4px);
            }
            .icon { margin-right: 12px; font-size: 16px; }
        </style>
        """, height=220)
        
        st.markdown('<div style="margin: 1rem 0; border-bottom: 1px solid rgba(0,0,0,0.05);"></div>', unsafe_allow_html=True)
        
        st.info("실시간 데이터 분석 시스템 v2.0")
    
    # 통계 계산
    stats = calculate_statistics(df)
    
    # 주요 지표 (접힘/펼침)
    metrics_container = st.container()
    with metrics_container:
        with st.expander("📈 주요 지표", expanded=True):
            # 연도별/월별/일별 통계 표시
            if not df.empty and '날짜' in df.columns and '실현손익' in df.columns:
                # 기간 및 네비게이션 행 (통합 - 수직 정렬 최적화)
                p_col1, p_col2 = st.columns([7, 3], vertical_alignment="center")
                with p_col1:
                    start_date = df['날짜'].min().strftime('%Y-%m-%d')
                    end_date = df['날짜'].max().strftime('%Y-%m-%d')
                    st.markdown(f'<p style="margin: 0; padding: 0; font-size: 0.9rem; color: var(--text-dim); font-weight: 500;">📅 기간: {start_date} ~ {end_date}</p>', unsafe_allow_html=True)
                
                with p_col2:
                    if st.session_state.selected_month is not None:
                        if st.button("← 월별 보기", key="back_to_month", use_container_width=True):
                            st.session_state.selected_month = None
                            st.rerun()
                    elif st.session_state.selected_year is not None:
                        if st.button("← 연도별 보기", key="back_to_year", use_container_width=True):
                            st.session_state.selected_year = None
                            st.session_state.selected_month = None
                            st.rerun()
                
                # 정보 텍스트 (더 컴팩트하게)
                if st.session_state.selected_month is not None:
                    st.markdown(f'<p style="font-weight: 700; font-size: 1.3rem; margin: 0.5rem 0 0 0;">{st.session_state.selected_year}년 {st.session_state.selected_month}월 일별 통계</p>', unsafe_allow_html=True)
                elif st.session_state.selected_year is not None:
                    st.markdown(f'<p style="font-weight: 700; font-size: 1.3rem; margin: 0.5rem 0 0 0;">{st.session_state.selected_year}년 월별 통계</p>', unsafe_allow_html=True)
                
                # 연도별 뷰
                if st.session_state.selected_year is None:
                    df_with_year = df.copy()
                    df_with_year['연도'] = df_with_year['날짜'].dt.year
                    
                    # 연도별 그룹화
                    yearly_stats = df_with_year.groupby('연도').agg({
                        '실현손익': 'sum',
                        '종목명': 'count'
                    }).reset_index()
                    yearly_stats.columns = ['연도', '실현손익', '거래건수']
                    
                    # 첫 거래 연도부터 현재 연도까지 모든 연도 생성
                    first_year = int(df['날짜'].min().year)
                    current_year = int(pd.Timestamp.now().year)
                    all_years = pd.DataFrame({'연도': range(first_year, current_year + 1)})
                    
                    # 모든 연도와 병합
                    yearly_stats = all_years.merge(yearly_stats, on='연도', how='left').fillna(0)
                    
                    # 연도 버튼들을 먼저 표시 (컴팩트 로우 적용)
                    st.markdown('<p style="font-size: 0.9rem; margin-top: 0.5rem; margin-bottom: 0.6rem;">연도를 클릭하면 월별 통계를 볼 수 있습니다</p>', unsafe_allow_html=True)
                    cols = st.columns(len(yearly_stats))
                    for idx, (col, (_, row)) in enumerate(zip(cols, yearly_stats.iterrows())):
                        year = int(row['연도'])
                        with col:
                            if st.button(f"{year}", key=f"year_{year}", use_container_width=True):
                                st.session_state.selected_year = year
                                st.rerun()
                    
                    # HTML 테이블 생성
                    metrics_html = """<table class="metric-table">
<tr>
<th>년도</th>
<th>실현손익</th>
<th>거래건수</th>
</tr>
"""
                    
                    for _, row in yearly_stats.iterrows():
                        year = int(row['연도'])
                        profit = row['실현손익']
                        count = int(row['거래건수'])
                        profit_class = 'positive' if profit >= 0 else 'negative'
                        
                        metrics_html += f"""<tr>
<td>{year}</td>
<td class="metric-value {profit_class}">{profit:,.0f}원</td>
<td class="metric-value">{count:,}건</td>
</tr>
"""
                    
                    # 합계 행 추가
                    total_profit = yearly_stats['실현손익'].sum()
                    total_count = int(yearly_stats['거래건수'].sum())
                    total_class = 'positive' if total_profit >= 0 else 'negative'
                    
                    metrics_html += f"""<tr class="total-row">
<td>합계</td>
<td class="metric-value {total_class}">{total_profit:,.0f}원</td>
<td class="metric-value">{total_count:,}건</td>
</tr>
</table>
"""
                    
                    st.markdown(metrics_html, unsafe_allow_html=True)
                    
                    # 연도별 차트 추가
                    fig_yearly = plot_performance_chart(df_with_year, view_type='연도별', title='연도별 실현손익 현황')
                    if fig_yearly:
                        st.plotly_chart(fig_yearly, use_container_width=True)
                
                # 월별 또는 일별 뷰
                else:
                    selected_year = st.session_state.selected_year
                    
                    if st.session_state.selected_month is None:
                        # --- 월별 뷰 ---
                        # 선택된 연도의 데이터만 필터링
                        year_df = df[df['날짜'].dt.year == selected_year].copy()
                        year_df['월'] = year_df['날짜'].dt.month
                        
                        # 월별 그룹화
                        monthly_stats = year_df.groupby('월').agg({
                            '실현손익': 'sum',
                            '종목명': 'count'
                        }).reset_index()
                        monthly_stats.columns = ['월', '실현손익', '거래건수']
                        
                        # 1월부터 12월까지 (또는 현재월까지) 모든 월 생성
                        current_year = pd.Timestamp.now().year
                        current_month = pd.Timestamp.now().month
                        
                        if selected_year == current_year:
                            max_month = current_month
                        else:
                            max_month = 12
                        
                        all_months = pd.DataFrame({'월': range(1, max_month + 1)})
                        monthly_stats = all_months.merge(monthly_stats, on='월', how='left').fillna(0)
                        
                        # 실현손익이 0인 달은 제외
                        monthly_filtered = monthly_stats[monthly_stats['실현손익'] != 0].copy()
                        
                        # 월 선택 버튼들 표시
                        if not monthly_filtered.empty:
                            st.markdown('<p style="font-size: 0.9rem; margin-top: 0.5rem; margin-bottom: 0.6rem;">월을 클릭하면 일별 통계를 볼 수 있습니다</p>', unsafe_allow_html=True)
                            
                            # 6개씩 2줄로 배치 (그리드 레이아웃)
                            months_data = monthly_filtered.reset_index()
                            chunk_size = 6
                            for i in range(0, len(months_data), chunk_size):
                                chunk = months_data.iloc[i : i + chunk_size]
                                cols = st.columns(chunk_size)
                                for (_, row), col in zip(chunk.iterrows(), cols):
                                    m_val = int(row['월'])
                                    with col:
                                        if st.button(
                                            f"{m_val}월", 
                                            key=f"month_{m_val}", 
                                            use_container_width=True
                                        ):
                                            st.session_state.selected_month = m_val
                                            st.rerun()
                        
                        # HTML 테이블 생성
                        metrics_html = """<table class="metric-table">
<tr>
<th>월</th>
<th>실현손익</th>
<th>거래건수</th>
</tr>
"""
                        
                        for _, row in monthly_filtered.iterrows():
                            month = int(row['월'])
                            profit = row['실현손익']
                            count = int(row['거래건수'])
                            profit_class = 'positive' if profit >= 0 else 'negative'
                            
                            metrics_html += f"""<tr>
<td>{month}월</td>
<td class="metric-value {profit_class}">{profit:,.0f}원</td>
<td class="metric-value">{count:,}건</td>
</tr>
"""
                        
                        # 합계 행 추가
                        total_profit = monthly_stats['실현손익'].sum()
                        total_count = int(monthly_stats['거래건수'].sum())
                        total_class = 'positive' if total_profit >= 0 else 'negative'
                        
                        metrics_html += f"""<tr class="total-row">
<td>합계</td>
<td class="metric-value {total_class}">{total_profit:,.0f}원</td>
<td class="metric-value">{total_count:,}건</td>
</tr>
</table>
"""
                        st.markdown(metrics_html, unsafe_allow_html=True)
                        
                        # 월별 차트 추가
                        fig_monthly = plot_performance_chart(year_df, view_type='월별', title=f'{selected_year}년 월별 실현손익 현황')
                        if fig_monthly:
                            st.plotly_chart(fig_monthly, use_container_width=True)
                    
                    else:
                        # --- 일별 뷰 ---
                        selected_month = st.session_state.selected_month
                        
                        # 해당 연도/월 데이터 필터링
                        month_df = df[(df['날짜'].dt.year == selected_year) & (df['날짜'].dt.month == selected_month)].copy()
                        month_df['일'] = month_df['날짜'].dt.day
                        
                        # 일별 그룹화
                        daily_stats = month_df.groupby('일').agg({
                            '실현손익': 'sum',
                            '종목명': 'count'
                        }).reset_index().sort_values('일')
                        daily_stats.columns = ['일', '실현손익', '거래건수']
                        
                        # HTML 테이블 생성
                        metrics_html = """<table class="metric-table">
<tr>
<th>날짜</th>
<th>실현손익</th>
<th>거래건수</th>
</tr>
"""
                        
                        for _, row in daily_stats.iterrows():
                            day = int(row['일'])
                            profit = row['실현손익']
                            count = int(row['거래건수'])
                            profit_class = 'positive' if profit >= 0 else 'negative'
                            
                            metrics_html += f"""<tr>
<td>{day}일</td>
<td class="metric-value {profit_class}">{profit:,.0f}원</td>
<td class="metric-value">{count:,}건</td>
</tr>
"""
                        
                        # 합계 행 추가
                        total_profit = daily_stats['실현손익'].sum()
                        total_count = int(daily_stats['거래건수'].sum())
                        total_class = 'positive' if total_profit >= 0 else 'negative'
                        
                        metrics_html += f"""<tr class="total-row">
<td>합계</td>
<td class="metric-value {total_class}">{total_profit:,.0f}원</td>
<td class="metric-value">{total_count:,}건</td>
</tr>
</table>
"""
                        st.markdown(metrics_html, unsafe_allow_html=True)
                        
                        # 일별 차트 추가
                        fig_daily = plot_performance_chart(month_df, view_type='일별', title=f'{selected_year}년 {selected_month}월 일별 실현손익 현황')
                        if fig_daily:
                            st.plotly_chart(fig_daily, use_container_width=True)
            else:
                st.info("데이터가 없습니다.")



    # 종목별 수익 (접힘/펼침)
    transactions_container = st.container()
    with transactions_container:
        with st.expander("📋 거래 내역", expanded=True):
            # 날짜 범위 선택 (한 줄로 표시)
            period = st.radio(
                "기간 선택",
                options=["오늘", "이번주", "이번달", "올해", "전체", "사용자화"],
                index=0,  # 기본값: 오늘
                horizontal=True
            )
            
            # 날짜 범위 계산
            if period != "사용자화":
                start_date, end_date = get_date_range(period, df)
            else:
                if '날짜' in df.columns:
                    min_date = df['날짜'].min().date()
                    max_date = df['날짜'].max().date()
                    
                    date_range = st.date_input(
                        "날짜 범위",
                        value=(min_date, max_date),
                        min_value=min_date,
                        max_value=max_date
                    )
                    
                    if len(date_range) == 2:
                        start_date, end_date = date_range
                    else:
                        start_date, end_date = min_date, max_date
            
            # 날짜 필터 적용
            filtered_df = df.copy()
            if '날짜' in df.columns and start_date and end_date:
                filtered_df = filtered_df[
                    (filtered_df['날짜'].dt.date >= start_date) &
                    (filtered_df['날짜'].dt.date <= end_date)
                ]
            
            # 종목 필터 (날짜 범위에 해당하는 종목만 표시)
            if '종목명' in filtered_df.columns:
                stocks_in_range = ['전체'] + sorted(filtered_df['종목명'].unique().tolist())
                selected_stock = st.selectbox("종목 선택", stocks_in_range)
                
                if selected_stock != '전체':
                    filtered_df = filtered_df[filtered_df['종목명'] == selected_stock]
            
            # 날짜 컬럼에서 시간 제거 (날짜만 표시)
            display_df = filtered_df.copy()
            if '날짜' in display_df.columns:
                display_df['날짜'] = display_df['날짜'].dt.date
            
            # 컬럼 순서 재배치: 날짜, 종목명, 종목코드, 수익률, 실현손익, 체결가, 체결량
            desired_columns = ['날짜', '종목명', '종목코드', '수익률', '실현손익', '체결가', '체결량']
            existing_columns = [col for col in desired_columns if col in display_df.columns]
            other_columns = [col for col in display_df.columns if col not in desired_columns]
            display_df = display_df[existing_columns + other_columns]
            
            # 테이블 표시 (실현손익 내림차순 정렬)
            # 정렬을 위해 원본 수치 값 사용
            if '실현손익' in filtered_df.columns:
                sorted_indices = filtered_df.sort_values('실현손익', ascending=False).index
                display_df = display_df.loc[sorted_indices]
            
            # 컬럼 설정 (숫자 컬럼은 NumberColumn으로 설정하여 오른쪽 정렬 및 천단위 콤마 자동 적용)
            column_config = {}
            if '수익률' in display_df.columns:
                column_config['수익률'] = st.column_config.NumberColumn(
                    '수익률',
                    help='수익률 (%)',
                    format="%.2f"
                )
            if '실현손익' in display_df.columns:
                column_config['실현손익'] = st.column_config.NumberColumn(
                    '실현손익',
                    help='실현손익 (원)',
                    format="%d"
                )
            if '체결가' in display_df.columns:
                column_config['체결가'] = st.column_config.NumberColumn(
                    '체결가',
                    help='체결가 (원)',
                    format="%d"
                )
            if '체결량' in display_df.columns:
                column_config['체결량'] = st.column_config.NumberColumn(
                    '체결량',
                    help='체결량 (주)',
                    format="%d"
                )
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                height=400,
                column_config=column_config
            )
            
            # 필터링된 통계
            if not filtered_df.empty:
                filtered_stats = calculate_statistics(filtered_df)
                st.caption(f"필터링된 데이터: {filtered_stats['총_거래건수']}건 | 총 실현손익: {filtered_stats['총_실현손익']:,.0f}원")
    
    
    # 종목별 수익 (접힘/펼침)
    stocks_container = st.container()
    with stocks_container:
        with st.expander("📊 종목별 실현손익", expanded=True):
            # Top 10 종목 고정 표시
            fig_stock = plot_stock_performance(df, top_n=10)
            if fig_stock:
                st.plotly_chart(fig_stock, use_container_width=True)
    
    # 푸터
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
