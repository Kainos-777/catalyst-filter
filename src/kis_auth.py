"""
한국투자증권 KIS Open API 인증 모듈
GitHub Secrets에서 APP_KEY, APP_SECRET, ACCOUNT_NO를 읽어 토큰을 발급받습니다.
"""
import os
import json
import requests
import time

KIS_BASE_URL = "https://openapi.koreainvestment.com:9443"  # 실전투자 도메인
TOKEN_CACHE_FILE = "/tmp/kis_token.json"


def get_env(name):
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"환경변수 {name} 가 설정되지 않았습니다. GitHub Secrets를 확인하세요.")
    return val


def get_access_token():
    """접근 토큰 발급 (1일 1회만 발급 가능 — 캐시 사용)"""
    app_key = get_env("KIS_APP_KEY")
    app_secret = get_env("KIS_APP_SECRET")

    # 캐시된 토큰이 있고 유효하면 재사용
    if os.path.exists(TOKEN_CACHE_FILE):
        try:
            with open(TOKEN_CACHE_FILE, "r") as f:
                cached = json.load(f)
            if cached.get("expires_at", 0) > time.time() + 600:
                return cached["access_token"]
        except Exception:
            pass

    url = f"{KIS_BASE_URL}/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {
        "grant_type": "client_credentials",
        "appkey": app_key,
        "appsecret": app_secret,
    }
    res = requests.post(url, headers=headers, data=json.dumps(body), timeout=10)
    res.raise_for_status()
    data = res.json()

    token = data["access_token"]
    expires_in = int(data.get("expires_in", 86400))

    with open(TOKEN_CACHE_FILE, "w") as f:
        json.dump({"access_token": token, "expires_at": time.time() + expires_in}, f)
    # 방어적 보안: 액세스 토큰이 담긴 파일은 소유자만 읽기/쓰기 가능하도록 제한
    # (GitHub Actions의 /tmp는 작업별로 격리되지만, 다층 방어 원칙을 따름)
    try:
        os.chmod(TOKEN_CACHE_FILE, 0o600)
    except OSError:
        pass  # 일부 환경에서 chmod가 제한될 수 있으나 치명적이지 않음

    return token


def get_headers(tr_id, extra=None):
    """
    공통 API 호출 헤더 생성.
    KIS 공식 샘플 코드(Python/JS 다수)에서 일관되게 소문자 appkey/appsecret을
    사용하므로 이를 따른다. HTTP 헤더 이름은 RFC 7230에 따라 대소문자를
    구분하지 않지만, 검증된 공식 예제 표기를 그대로 사용해 불확실성을 없앤다.
    """
    token = get_access_token()
    headers = {
        "content-type": "application/json; charset=utf-8",
        "authorization": f"Bearer {token}",
        "appkey": get_env("KIS_APP_KEY"),
        "appsecret": get_env("KIS_APP_SECRET"),
        "tr_id": tr_id,
        "custtype": "P",
    }
    if extra:
        headers.update(extra)
    return headers
