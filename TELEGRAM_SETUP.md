# 텔레그램 알림 설정 가이드 (Telegram Setup)

이 프로젝트는 데이터 수집 완료 또는 실패 시 텔레그램으로 알림을 보낼 수 있습니다.
설정을 위해 **Bot Token**과 **Chat ID**가 필요합니다.

## 1. 봇 생성 및 토큰 발급 (`Bot Token`)

1. 텔레그램 앱에서 **`@BotFather`** 검색
2. 봇파더와의 채팅방에서 **`/newbot`** 입력 및 전송
3. 봇의 **이름(Name)** 입력 (예: `MyProfitBot`)
4. 봇의 **아이디(Username)** 입력 (반드시 `bot`으로 끝나야 함, 예: `my_profit_alarm_bot`)
5. 생성이 완료되면 **`HTTP API:`** 다음에 나오는 긴 문자열이 토큰입니다.
    - 예: `123456789:ABCdefGHIjkl...`
    - 이 값을 복사해두세요.

## 2. 내 채팅 ID 알아내기 (`Chat ID`)

1. 방금 만든 봇을 검색해서 채팅방에 들어간 뒤 **`/start`**를 누르거나 아무 메시지나 하나 보냅니다. (이 과정 필수!)
2. 웹 브라우저를 켜고 아래 주소에 접속합니다. (토큰 값을 본인의 것으로 바꿔주세요)
    - `https://api.telegram.org/bot[여기에_토큰_입력]/getUpdates`
    - 예: `https://api.telegram.org/bot123456789:ABC.../getUpdates`
3. 화면에 나온 JSON 결과에서 `"from": {"id": 12345678, ...}` 부분의 숫자(`12345678`)가 본인의 Chat ID입니다.

## 3. 설정 파일 적용

`config.py` 파일을 열고 아래와 같이 입력합니다.

```python
# 텔레그램 알림 설정
TELEGRAM_BOT_TOKEN = "123456789:ABCdefGHIjkl..."
TELEGRAM_CHAT_ID = "12345678"
```

이제 `run_daily.bat`을 실행하면 작업 완료 시 스마트폰으로 알림이 옵니다! 🎉
