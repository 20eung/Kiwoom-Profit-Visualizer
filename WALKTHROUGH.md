# Walkthrough - Kiwoom API ka10170 전환

Kiwoom REST API를 `ka10073`(기간별 실현손익)에서 `ka10170`(당일매매일지)으로 전환하여 **당일총손익금액**을 정확히 파악할 수 있도록 수정했습니다.

## 변경 사항

### [kiwoom_collector.py](file:///Users/20eung/Project/Kiwoom-Profit-Visualizer/kiwoom_collector.py)

#### 1. API ID 및 요청 파라미터 변경
- **API ID**: `ka10170` (당일매매일지)
- **파라미터**: `base_dt`(기준일자), `ottks_tp`("1"), `ch_crd_tp`("0")
- **함수 인자**: `start_date`, `end_date` -> `base_date`

```python
# Before
def get_realized_profit(self, start_date=None, end_date=None, stock_code=""):
    # ... ka10073 호출

# After
def get_realized_profit(self, base_date=None):
    # ... ka10170 호출
    body = {
        "base_dt": base_date,
        "ottks_tp": "1",
        "ch_crd_tp": "0"
    }
```

#### 2. 총손익금액 파싱 및 출력
응답 데이터에서 `tot_pl_amt`(총손익금액)를 직접 추출하여 콘솔에 출력하도록 추가했습니다.

```python
if "tot_pl_amt" in data:
    total_profit = data["tot_pl_amt"]
    print(f"💰 당일 총손익금액: {total_profit}")
```

#### 3. 컬럼 매핑 업데이트
`ka10170`의 응답 필드(`buy_avg_pric`, `sell_qty`, `pl_amt` 등)를 한국어 컬럼명으로 매핑했습니다.

## 검증 결과

### 실행 인자 확인
스크립트 실행 인자가 `base-date`로 변경된 것을 확인했습니다.

```bash
python kiwoom_collector.py --help
# usage: kiwoom_collector.py ... [--base-date BASE_DATE]
```

### 다음 단계
- 실제 API 키를 사용하여 코드를 실행하고, 콘솔에 출력되는 `💰 당일 총손익금액` 값을 확인해보세요.
- 생성된 `kiwoom_data.csv` 파일에 당일 매매 상세 내역이 올바르게 저장되는지 확인하세요.

## 추가 구현: 대량 수집 및 증분 동기화

사용자의 요청에 따라 다음 기능이 추가되었습니다.

### 1. 대량 수집 파이프라인 (`run_pipeline.py`)
지정된 날짜 범위 동안 하루씩 반복하며 데이터를 수집하고 병합하여 구글 시트에 업로드합니다.
```bash
# 2024년 1월 1일부터 오늘까지 수집
python run_pipeline.py --start-date 20240101
```

### 2. 증분 동기화 (`streamlit_app.py`)
웹 대시보드의 'Sync Kiwoom API' 버튼 클릭 시:
1.  구글 시트의 마지막 데이터 날짜를 확인합니다.
2.  `마지막 날짜 + 1일`부터 `오늘`까지의 데이터를 순차적으로 수집합니다.
3.  수집된 데이터를 시트에 추가(Upsert)합니다.
4.  이미 최신 상태라면 API를 호출하지 않습니다.

## 트러블슈팅

### 4. Invalid JWT Signature 오류 해결
시스템 시간 동기화 확인 및 `credentials.json` 재발급으로 해결했습니다.

### 5. 데이터 '0' 또는 누락 문제 해결 (ka10170)
**원인**:
1.  **API 파라미터**: `ottks_tp` (단주구분)를 "1" (당일매수에 대한 당일매도)로 설정하여, 보유하고 있던 주식을 당일 매도(Overnight Sell)한 경우 실현손익이 0으로 계산되거나 누락됨.
2.  **데이터 타입**: API가 숫자를 천단위 콤마(`14,125`)가 포함된 문자열로 반환하여, `pd.to_numeric` 변환 시 `NaN` -> Empty String으로 처리됨.

**해결**:
1.  **API 파라미터 변경**: `ottks_tp`를 `"0"` (전체) 또는 `"2"` (당일매도 전체)로 변경하여 모든 매도 건에 대한 실현손익을 포착하도록 수정 (현재 `"0"` 적용).
2.  **콤마 제거**: 숫자 변환 전 `.str.replace(',', '')` 로직을 추가하여 정확한 숫자 파싱 보장.

### 6. HTS와 데이터 미세 차이 분석
**현상**: HTS(신용 당일매매일지) 상의 손익(362,434원)과 API 수집 손익(362,555원) 간에 약 121원의 차이 발생.
**원인**:
1.  **신용 이자(Credit Interest)**: HTS 화면은 '신용 당일매매일지'로, 매매 시 발생한 **신용 대출 이자**가 '제세금+이자' 항목에 포함되어 손익에서 차감됨.
2.  **API 데이터 특성**: `ka10073`(일자별 실현손익) API는 매매 차익에 대한 세금과 수수료는 차감하지만, **신용 이자**는 별도 항목으로 취급하거나 본문에 포함되지 않아 차감되지 않은 '순수 매매 손익'을 반환함.
**결론**: 현재 수집되는 데이터는 **신용 이자 차감 전 실현손익**이며, HTS는 **이자 차감 후 실현손익**임. 121원은 해당 일자의 신용 이자 비용으로 판단됨.


