# 구현 계획 - Kiwoom API ka10170 전환

`kiwoom_collector.py`를 업데이트하여 `ka10073` 대신 `ka10170` API ID를 사용하도록 변경합니다. 이 API는 `tot_pl_amt`(총손익금액)을 포함한 "당일매매일지" 데이터를 제공합니다.

## 사용자 검토 필요 사항
> [!IMPORTANT]
> 제공해주신 이미지를 바탕으로 요청 파라미터를 구성했습니다. `ottks_tp`(단주구분)는 '1'(당일매수에 대한 당일매도), `ch_crd_tp`(현금신용구분)는 '0'(전체)으로 설정할 예정입니다. 이 설정이 의도와 다르다면 알려주세요.

## 변경 제안

### Kiwoom Collector (`kiwoom_collector.py`)
- `get_realized_profit` 함수는 단일 날짜(`base_date`) 조회로 변경되었습니다 (완료).
- `_clean_dataframe` 매핑 업데이트 완료.

### Run Pipeline (`run_pipeline.py`)
- **반복 조회 로직 추가**:
    - `start_date`와 `end_date`를 인자로 받아, 해당 기간 동안 반복문을 돌며 `kiwoom_collector.get_realized_profit(base_date=...)`를 호출합니다.
    - 조회된 일별 DataFrame을 하나로 합칩니다 (`pd.concat`).
    - 합쳐진 전체 데이터를 `GoogleSheetManager`를 통해 구글 시트에 업데이트합니다.
- **기존 호환성**:
    - `run_pipeline.py`의 인자는 `start-date`, `end-date`를 그대로 유지하여 사용자가 기간을 지정할 수 있게 합니다.

### [MODIFY] [run_pipeline.py](file:///Users/20eung/Project/Kiwoom-Profit-Visualizer/run_pipeline.py)
- `KiwoomRestCollector` 호출부를 반복문으로 변경.
- 조회된 데이터를 리스트에 모아 `concat`.
- `upsert_data` 호출.

### [MODIFY] [streamlit_app.py](file:///Users/20eung/Project/Kiwoom-Profit-Visualizer/streamlit_app.py)
- **증분 동기화 로직 구현**:
    - `sync_with_kiwoom` 함수 수정.
    - 현재 로드된 데이터의 마지막 날짜(`df['날짜'].max()`)를 확인.
    - 시작일: `마지막 날짜 + 1일` (데이터가 없으면 2024.01.01).
    - 종료일: `오늘`.
    - 해당 기간 동안 반복문으로 `get_realized_profit(base_date=...)` 호출.
    - 수집된 데이터를 구글 시트에 `upsert`.
- **호환성 수정**: `get_realized_profit` 인자 변경 대응.

## 데이터 저장 스키마
`ka10170` API를 사용하면 다음과 같은 정보가 저장됩니다:
- **기존 컬럼 유지**: `날짜`, `종목명`, `종목코드`, `실현손익`, `수익률`
- **변경/추가 컬럼**:
    - `체결가` -> `매도평균가`, `매수평균가`
    - `체결량` -> `매도수량`, `매수수량`
    - `매도금액`, `매수금액`, `수수료_제세금`
> **참고**: 사용자가 "일자별 손익현황만 필요하다"고 했지만, 기존 `streamlit_app`의 "종목별 수익 현황" 차트를 유지하기 위해 **상세 내역(Transaction)** 형태로 저장하는 것이 유리합니다. 일자별 합계는 이 데이터를 기반으로 시각화 단계에서 계산됩니다. API 응답에 날짜가 없을 경우 `base_date`를 `날짜` 컬럼으로 강제 주입합니다.

## 검증 계획

### 자동화 테스트
- `python kiwoom_collector.py`를 실행하여 로그 출력을 확인합니다.
- `tot_pl_amt` 값이 정상적으로 출력되고 CSV에 저장되는지 확인합니다.
