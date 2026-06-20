# 📱 CATALYST FILTER™ 설치 가이드 (완전 초보자용)

이 문서는 프로그래밍을 전혀 모르는 분도 따라 할 수 있도록,
화면에 무엇이 보이는지까지 적었습니다. 순서대로만 따라오세요.

**전체 소요 시간: 약 40분 (한 번만 하면 끝)**

---

## 🗺️ 먼저 전체 그림 이해하기

이 시스템은 4개의 무료 서비스를 연결해서 만듭니다.

| 서비스 | 역할 | 비유 |
|---|---|---|
| 한국투자증권 | 실제 주가 데이터를 줌 | 정보를 캐는 광산 |
| GitHub | 코드를 올려두고 매일 자동으로 실행시켜줌 | 자동으로 일하는 일꾼 |
| 텔레그램 | 결과를 메시지로 받음 | 우편함 |
| (이 zip 파일) | 위 셋을 연결하는 코드 | 배관 |

준비물은 **이메일 주소 하나**와 **휴대폰(텔레그램 앱)**뿐입니다.

---

## STEP 1. 한국투자증권 계좌 만들기 (이미 있으면 건너뛰기)

1. 휴대폰에서 **"한국투자증권"** 앱 설치
2. 앱 실행 → **계좌개설** → 비대면 계좌개설 진행 (신분증 촬영, 본인인증)
3. 완료되면 **HTS ID(아이디)**가 생깁니다 — 나중에 필요하니 기억해두세요

> 이미 계좌가 있다면 이 단계는 건너뛰세요.

---

## STEP 2. 한국투자증권 API 키 발급받기

이게 "주가 데이터를 가져와도 된다"는 허가증입니다.

1. 컴퓨터 브라우저에서 **https://apiportal.koreainvestment.com** 접속
2. 오른쪽 위 **로그인** 클릭 → 한투증권 계좌로 로그인
3. 로그인 후 상단 메뉴에서 **"API신청"** 클릭
4. **"KIS Developers 서비스 신청하기"** 버튼 클릭
5. 화면에 보이는 본인 계좌번호를 선택하고 **신청** 클릭
6. 본인인증 팝업이 뜨면 인증 완료
7. 신청이 끝나면 화면에 두 개의 긴 문자열이 보입니다:
   - **App Key** (영문+숫자 조합, 매우 긺)
   - **App Secret** (마찬가지로 매우 긺)

📌 **이 두 값을 메모장에 복사해서 저장해두세요.** (예시처럼 따옴표 없이 순수 문자열만)

```
App Key: PSxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
App Secret: V9xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ 이 값은 비밀번호와 같습니다. 절대 다른 사람에게 보여주거나 카톡/문자로 보내지 마세요.

---

## STEP 3. 텔레그램 봇 만들기

텔레그램 봇은 "나에게 자동으로 메시지를 보내는 가상의 친구"라고 생각하면 됩니다.

1. 휴대폰에서 **텔레그램 앱** 실행 (없으면 앱스토어에서 설치)
2. 검색창에 **`BotFather`** 입력 → 파란 체크마크 있는 공식 계정 선택
3. 대화창 열고 **`/newbot`** 입력 후 전송
4. BotFather가 "봇 이름을 정해주세요"라고 물어봄
   - 예: `내 주식 브리핑 봇` 입력 (한글 가능, 아무 이름이나 OK)
5. 이어서 "봇 아이디(username)를 정해주세요"라고 물어봄
   - 반드시 영문으로 끝에 **`bot`**이 들어가야 함
   - 예: `my_stock_briefing_bot` 입력
   - 이미 사용 중이면 다른 이름으로 재시도
6. 성공하면 이런 메시지가 옵니다:

```
Done! Congratulations on your new bot...
Use this token to access the HTTP API:
7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

📌 **이 긴 숫자+문자 조합(토큰)을 메모장에 복사해두세요.**

```
텔레그램 봇 토큰: 7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

7. 이제 검색창에서 방금 만든 봇 이름(`my_stock_briefing_bot`)을 검색해서 들어가기
8. 대화창 하단의 **시작(Start)** 버튼 클릭, 또는 **`/start`** 입력해서 전송
   - (이 과정이 꼭 필요합니다 — 봇이 나에게 먼저 말 걸 권한을 얻는 단계예요)

---

## STEP 4. 내 텔레그램 Chat ID 알아내기

봇이 "나"에게 메시지를 보내려면, "나"가 누구인지 알아야 합니다. 그 고유 번호가 Chat ID예요.

1. 컴퓨터 브라우저 주소창에 아래 주소를 입력하되, `여기에봇토큰` 부분만 STEP 3에서 받은 토큰으로 바꿔서 입력:

```
https://api.telegram.org/bot여기에봇토큰/getUpdates
```

   실제 예시 (토큰이 `7123456789:AAFxxx...`라면):
```
https://api.telegram.org/bot7123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/getUpdates
```

2. 엔터를 누르면 화면에 복잡한 글자들이 쭉 나옵니다. 그중에서 아래처럼 생긴 부분을 찾으세요:

```
"chat":{"id":987654321,"first_name":"홍길동",...
```

3. `"id":` 바로 뒤에 있는 숫자(`987654321`)가 내 Chat ID입니다.

📌 **이 숫자도 메모장에 저장해두세요.**

```
텔레그램 Chat ID: 987654321
```

> 만약 화면에 `{"ok":true,"result":[]}` 처럼 빈 결과만 나오면, STEP 3의 8번(봇에게 /start 보내기)을 다시 하고 30초 후 새로고침 해보세요.

---

## STEP 5. GitHub 계정 만들기

GitHub는 "코드를 보관하고, 정해진 시간에 자동으로 실행해주는 창고"입니다.

1. 브라우저에서 **https://github.com** 접속
2. 오른쪽 위 **Sign up** 클릭
3. 이메일, 비밀번호, 사용자 이름(Username) 입력해서 계정 생성
   - Username은 나중에 인터넷 주소에 들어가니 영문으로 간단하게 (예: `hong-gildong`)
4. 이메일 인증까지 완료

---

## STEP 6. 압축 파일을 GitHub에 올리기

여기가 조금 낯설 수 있는데, 천천히 따라오면 됩니다. 클릭만으로 가능한 방법을 안내해요.

### 6-1. 새 저장소(repository) 만들기

1. GitHub 로그인 후 오른쪽 위 **`+`** 아이콘 클릭 → **New repository** 클릭
2. **Repository name**에 `catalyst-filter` 입력
3. **Public** 선택되어 있는지 확인 (기본값)
4. 아래 체크박스들은 전부 **체크하지 않은 상태**로 둡니다
5. 초록색 **Create repository** 버튼 클릭

### 6-2. 압축 파일 풀어서 업로드하기

1. 받은 `catalyst-filter.zip` 파일을 컴퓨터에서 더블클릭해서 압축 풀기
   - 폴더 안에 `src`, `docs`, `.github` 등의 폴더가 보이면 정상입니다
2. 방금 만든 GitHub 저장소 페이지로 돌아가기
3. 페이지 중간에 있는 **"uploading an existing file"** 파란 글씨 링크 클릭
   - (안 보이면 페이지 상단의 **Add file** → **Upload files** 클릭)
4. 압축 푼 폴더 안의 **모든 파일과 폴더**를 마우스로 전체 선택해서, 브라우저 화면 안으로 드래그 앤 드롭
   - ⚠️ `catalyst-filter` 폴더 자체가 아니라, **그 안에 있는 내용물**(`.github`, `src`, `docs`, `README.md` 등)을 끌어다 놓아야 합니다
5. 화면 아래로 스크롤 → **Commit changes** 초록 버튼 클릭

업로드가 끝나면 저장소 페이지에 `src`, `docs`, `.github` 폴더와 `README.md` 파일이 보입니다.

---

## STEP 7. 비밀 정보 등록하기 (Secrets)

지금까지 메모장에 모아둔 4가지 값을 GitHub에 안전하게 등록합니다.
이 값들은 등록 후 아무도(나 자신도) 다시 볼 수 없게 암호화되니 안심하세요.

1. 저장소 페이지 상단 메뉴에서 **Settings** 클릭 (톱니바퀴 아이콘)
2. 왼쪽 메뉴에서 **Secrets and variables** 클릭 → **Actions** 클릭
3. 초록색 **New repository secret** 버튼 클릭
4. 아래 표를 보면서, **총 4번 반복**해서 등록합니다:

| Name (이름)에 입력 | Secret (값)에 입력 |
|---|---|
| `KIS_APP_KEY` | STEP 2에서 받은 App Key |
| `KIS_APP_SECRET` | STEP 2에서 받은 App Secret |
| `TELEGRAM_BOT_TOKEN` | STEP 3에서 받은 봇 토큰 |
| `TELEGRAM_CHAT_ID` | STEP 4에서 받은 Chat ID 숫자 |

각각 Name과 Secret을 입력한 후 **Add secret** 버튼을 누르고, 다시 **New repository secret**을 눌러서 다음 것을 등록 — 이렇게 4번 반복합니다.

다 끝나면 목록에 이렇게 4개가 보여야 합니다:
```
KIS_APP_KEY        ✓ Updated now
KIS_APP_SECRET      ✓ Updated now
TELEGRAM_BOT_TOKEN   ✓ Updated now
TELEGRAM_CHAT_ID    ✓ Updated now
```

---

## STEP 8. 화면(대시보드) 켜기 — GitHub Pages

1. 같은 **Settings** 페이지에서 왼쪽 메뉴 맨 아래쪽 **Pages** 클릭
2. **Source** 드롭다운에서 **Deploy from a branch** 선택되어 있는지 확인
3. 바로 아래 **Branch** 드롭다운에서 **main** 선택
4. 그 옆 폴더 선택에서 **`/docs`** 선택
5. **Save** 버튼 클릭

1~2분 기다린 후, 같은 페이지 상단에 초록색 글씨로 사이트 주소가 뜹니다:
```
Your site is live at https://본인아이디.github.io/catalyst-filter/
```

이 주소가 내 대시보드 주소예요. 즐겨찾기 해두세요.

---

## STEP 9. 지금 바로 한 번 실행해서 테스트하기

매일 저녁 7시까지 안 기다리고, 지금 바로 작동하는지 확인해볼게요.

1. 저장소 페이지 상단 메뉴에서 **Actions** 클릭
2. 왼쪽 목록에서 **Daily Market Briefing** 클릭
3. 오른쪽의 **Run workflow** 버튼 클릭 → 다시 한번 초록색 **Run workflow** 버튼 클릭
4. 페이지를 새로고침(F5)하면 노란 점(진행 중) → 초록 체크(성공) 또는 빨간 X(실패)가 보입니다
   - 노란 점이 도는 동안은 30초~1분 정도 기다리면 됩니다

### ✅ 성공하면
텔레그램 앱을 열어보세요. 봇이 보낸 주가 브리핑 메시지가 와 있을 거예요!

### ❌ 빨간 X(실패)가 뜨면
1. 빨간 X 옆의 **Daily Market Briefing** 글자를 클릭
2. **briefing** 칸 클릭하면 무엇이 잘못됐는지 영어로 나옵니다
3. 대부분의 원인은:
   - STEP 7에서 Secret 이름을 잘못 입력함 (대소문자까지 정확히 같아야 함)
   - STEP 2의 App Key/Secret을 복사할 때 앞뒤 공백이 같이 복사됨
4. Settings → Secrets and variables → Actions로 가서 해당 값을 다시 확인하고, 연필 아이콘으로 수정 가능

---

## STEP 10. 매일 저절로 작동하는지 확인하기

별도로 할 일은 없습니다! 평일 저녁 7시가 되면 자동으로:
1. 텔레그램으로 그날 주가 브리핑이 옵니다
2. 대시보드(STEP 8 주소)가 최신 정보로 업데이트됩니다

---

## 🎮 봇 사용법 (텔레그램에서)

만든 봇과의 채팅창에서 이렇게 메시지를 보내보세요:

| 보낼 메시지 | 봇의 반응 |
|---|---|
| `/status` | "지금 작동 중이에요" 같은 현재 상태 알려줌 |
| `/pause` | 자동 브리핑을 잠시 멈춤 (여행 갈 때 등) |
| `/resume` | 다시 작동 시작 |

명령을 보내고 **최대 10분 정도** 기다리면 봇이 응답합니다 (즉시 답장이 아닐 수 있어요, 정상입니다).

---

## 🔧 관심 종목 바꾸고 싶을 때

기본으로 설정된 10개 종목(삼성전자, SK하이닉스 등) 대신 원하는 종목으로 바꾸려면:

1. GitHub 저장소에서 `src` 폴더 클릭 → `fetch_market_data.py` 파일 클릭
2. 오른쪽 위 연필(✏️) 아이콘 클릭 (편집 모드)
3. `WATCHLIST = [` 로 시작하는 부분을 찾아서, 원하는 종목코드로 수정
   - 종목코드는 네이버 증권에서 검색하면 6자리 숫자로 나와요 (예: 삼성전자 005930)
4. 수정 후 오른쪽 위 초록색 **Commit changes** 클릭

다음 실행부터 바뀐 종목으로 분석합니다.

---

## ❓ 자주 묻는 질문

**Q. 비용이 드나요?**
A. 전부 무료입니다. GitHub Actions, 텔레그램, GitHub Pages 모두 개인 사용 범위에서 무료예요.

**Q. 컴퓨터를 꺼놔도 작동하나요?**
A. 네! GitHub가 자체 서버에서 실행하기 때문에 내 컴퓨터나 휴대폰은 꺼져 있어도 상관없습니다.

**Q. 실수로 App Key를 다른 사람에게 보여줬어요.**
A. apiportal.koreainvestment.com에 다시 로그인해서 키를 재발급(폐기 후 재신청)하고, GitHub Secrets도 새 값으로 교체하세요.

**Q. 시간을 저녁 7시가 아니라 다른 시간으로 바꾸고 싶어요.**
A. `.github/workflows/daily_briefing.yml` 파일을 열어서 `cron` 부분의 숫자를 바꾸면 됩니다. (한국시간 = UTC + 9시간이라는 점만 기억하면 돼요. 어려우면 이 채팅에 다시 요청하세요.)

---

막히는 단계가 있으면 **몇 번째 STEP에서 어떤 화면이 보이는지** 그대로 알려주세요. 같이 해결해드릴게요.
