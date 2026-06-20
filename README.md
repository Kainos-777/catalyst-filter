# CATALYST FILTER™ — 자동 주식 브리핑 시스템

매일 장마감 후 **오후 7시(KST)**에 자동으로:
1. 한국투자증권(KIS) Open API로 실시간 시세·RSI·수급 데이터 수집
2. 5가지 기준으로 매수/관망/매도 신호 분석
3. GitHub Pages 대시보드 자동 업데이트
4. 텔레그램으로 브리핑 발송

텔레그램에서 `/pause` `/resume` `/status` 명령으로 봇을 직접 켜고 끌 수 있습니다.

---

## 🚀 설치 가이드 (10분)

### 1단계. 이 저장소를 GitHub에 올리기

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/{내깃헙아이디}/catalyst-filter.git
git push -u origin main
```

### 2단계. GitHub Secrets 등록

저장소 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

다음 4개를 등록하세요:

| Secret 이름 | 값 | 발급처 |
|---|---|---|
| `KIS_APP_KEY` | 한투증권 App Key | apiportal.koreainvestment.com |
| `KIS_APP_SECRET` | 한투증권 App Secret | apiportal.koreainvestment.com |
| `TELEGRAM_BOT_TOKEN` | 봇 토큰 | @BotFather 에서 발급 |
| `TELEGRAM_CHAT_ID` | 내 채팅 ID | 아래 "Chat ID 확인법" 참고 |

### 3단계. 텔레그램 Chat ID 확인법

1. 만든 봇과 텔레그램에서 대화 시작 (아무 메시지나 전송, 예: `/start`)
2. 브라우저에서 아래 URL 접속 (본인 봇 토큰으로 교체):
   ```
   https://api.telegram.org/bot{여기에봇토큰}/getUpdates
   ```
3. 응답 JSON에서 `"chat":{"id": 123456789, ...}` 의 숫자가 Chat ID

### 4단계. GitHub Pages 활성화

저장소 → **Settings** → **Pages** → Source를 **Deploy from a branch** → Branch: `main`, 폴더: `/docs` 선택 → Save

배포 후 다음 주소에서 대시보드 확인 가능:
```
https://{내깃헙아이디}.github.io/catalyst-filter/
```

### 5단계. 수동 테스트 실행

저장소 → **Actions** 탭 → **Daily Market Briefing** 선택 → **Run workflow** 버튼으로 즉시 테스트 가능

---

## 🤖 텔레그램 봇 명령어

봇에게 다음 메시지를 보내면 즉시 응답합니다 (최대 10분 이내 — polling 주기):

| 명령어 | 동작 |
|---|---|
| `/status` | 현재 작동 상태와 다음 실행 시각 확인 |
| `/pause` | 자동 브리핑 일시정지 (오후 7시가 되어도 발송 안 함) |
| `/resume` | 일시정지 해제, 자동 발송 재개 |

> 본인의 `TELEGRAM_CHAT_ID`로 등록되지 않은 사람이 명령을 보내면 무시됩니다(보안).

---

## ⏰ 자동 실행 시간

매일(월~금) 한국시간 **오후 7시**에 자동 실행됩니다.

```yaml
# .github/workflows/daily_briefing.yml
- cron: "0 10 * * 1-5"  # UTC 10:00 = KST 19:00
```

시간을 바꾸려면 cron 표현식의 `10`(UTC 시) 부분을 `KST - 9`로 계산해서 수정하세요.

---

## 📂 폴더 구조

```
catalyst-filter/
├── .github/workflows/
│   ├── daily_briefing.yml       # 매일 19시 자동 브리핑
│   ├── telegram_listener.yml    # 10분마다 /pause /resume /status 명령 확인
│   └── security_scan.yml        # 주간 의존성 취약점 자동 스캔
├── src/
│   ├── kis_auth.py              # 한투 API 인증
│   ├── fetch_market_data.py     # 시세·RSI·수급 수집
│   ├── analyze.py               # 5기준 스크리닝 분석
│   ├── notify_telegram.py       # 텔레그램 발송
│   ├── check_pause.py           # 일시정지 상태 확인
│   ├── telegram_bot_handler.py  # /pause /resume /status 명령 처리
│   └── main.py                   # 전체 실행 진입점
├── docs/
│   ├── index.html                # GitHub Pages 대시보드
│   ├── data.json                 # 자동 생성되는 결과 데이터
│   ├── control.json              # 일시정지 상태 저장
│   └── telegram_offset.json      # 텔레그램 메시지 중복 처리 방지용 offset
└── requirements.txt
```

---

## 🔧 관심종목 수정

`src/fetch_market_data.py` 의 `WATCHLIST` 리스트에서 종목코드·이름·섹터를 자유롭게 추가/삭제하세요.

```python
WATCHLIST = [
    {"code": "000660", "name": "SK하이닉스", "sector": "반도체"},
    # 원하는 종목 추가...
]
```

---

## 🔒 보안 및 안정성 설계 노트

이 프로젝트는 풀스택 아키텍처, 백엔드 개발, 보안, 금융 도메인 4가지 관점에서
교차검증을 거쳤습니다. 발견되어 수정된 주요 사항:

- **동시성**: 두 워크플로우(브리핑/봇 리스너)가 동시에 git push할 때
  충돌하지 않도록 `pull --rebase` + 재시도 로직 적용
- **상태 파일 손상 내성**: `control.json`(일시정지 여부)과
  `telegram_offset.json`(중복 메시지 방지)을 분리 저장해, 한쪽이
  손상되어도 다른 쪽(특히 텔레그램 메시지 중복 폭주 방지)에 영향 없음
- **메시지 분할 안전성**: 긴 브리핑이 4096자를 넘을 때 HTML 태그가
  중간에 잘려 텔레그램이 메시지를 거부하지 않도록 줄 단위로만 분할
- **의존성 취약점**: `requests` 라이브러리의 실제 CVE 2건을 pip-audit으로
  발견해 패치 완료. 매주 자동 재스캔
- **RSI 계산 정확성**: KIS API의 일봉 데이터 정렬 순서를 가정하지 않고
  실제 영업일자(`stck_bsop_date`) 기준으로 명시 정렬 — 정렬 가정이
  틀릴 경우 RSI가 정반대로 계산되는 위험 제거
- **RSI 엣지케이스**: 가격이 전혀 변동하지 않는 구간(거래정지 등)에서
  RSI가 기계적으로 100(과매수)이 되어 잘못된 매도 신호를 내지 않도록,
  이 경우 "판단 불가"로 처리
- **장애 가시성**: 지수 조회나 개별 종목 조회가 실패해도 워크플로우가
  죽지 않을 뿐 아니라, 실패 사실을 브리핑 메시지에 명시적으로 표시
  (조용히 데이터가 누락되는 것을 방지)

---

## ⚠️ 주의사항

- 한투증권 API는 모의투자/실전투자 도메인이 다릅니다. 기본값은 실전(`openapi.koreainvestment.com:9443`)으로 설정되어 있어요. 모의투자로 테스트하려면 `kis_auth.py`의 `KIS_BASE_URL`을 `https://openapivts.koreainvestment.com:29443`으로 변경하세요.
- API 호출 제한(초당 호출 수)이 있으니 종목 수를 너무 늘리지 마세요.
- 이 도구는 투자 참고용이며, 투자 손실의 책임은 투자자 본인에게 있습니다.

