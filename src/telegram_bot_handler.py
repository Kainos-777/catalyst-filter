"""
텔레그램 봇 명령 처리기.
/pause   → 자동 브리핑 일시정지
/resume  → 자동 브리핑 재개
/status  → 현재 상태 + 다음 실행 예정 안내

GitHub Actions의 polling 워크플로우(telegram_listener.yml)가
주기적으로 이 스크립트를 실행해서 새 명령이 있는지 확인합니다.

설계 노트(보안/안정성):
- last_update_id는 control.json과 분리된 offset.json에 저장합니다.
  이유: control.json은 사용자 상태(paused 등)를 담고 있어 손상 가능성이
  상대적으로 높은데, 만약 두 값이 한 파일에 있으면 control.json 손상 시
  offset까지 0으로 리셋되어 텔레그램이 과거 메시지를 전부 재전송 →
  /pause, /resume 명령이 중복 재실행되는 심각한 부작용이 생깁니다.
  파일을 분리하면 한쪽이 깨져도 다른 쪽은 영향받지 않습니다.
- getUpdates 호출 시마다 처리 완료된 offset을 다음 호출의 offset으로
  넘겨 텔레그램 서버 측에서도 해당 메시지를 큐에서 제거하도록 합니다
  (텔레그램 공식 권장 방식).
"""
import json
import os
import sys
import requests
from datetime import datetime

BASE_DIR = os.path.dirname(__file__)
CONTROL_FILE = os.path.join(BASE_DIR, "..", "docs", "control.json")
OFFSET_FILE = os.path.join(BASE_DIR, "..", "docs", "telegram_offset.json")


def get_env(name):
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"환경변수 {name} 가 설정되지 않았습니다.")
    return val


def load_json_safe(path, default):
    """JSON 파일을 읽되, 없거나 손상되었으면 기본값을 반환 (절대 예외를 던지지 않음)"""
    if not os.path.exists(path):
        return dict(default)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return dict(default)
        for k, v in default.items():
            data.setdefault(k, v)
        return data
    except (json.JSONDecodeError, OSError):
        print(f"⚠️ {path} 파일이 손상되어 기본값으로 복구합니다.")
        return dict(default)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_control():
    return load_json_safe(CONTROL_FILE, {"paused": False, "updated_at": None, "updated_by": "init"})


def load_offset():
    return load_json_safe(OFFSET_FILE, {"last_update_id": 0})


def mask_secrets(text, *secrets):
    """로그 출력 전 방어적 시크릿 마스킹 (notify_telegram.py와 동일 정책)"""
    for secret in secrets:
        if secret and len(secret) >= 8:
            text = text.replace(secret, "***MASKED***")
    return text


def send_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    res = requests.post(url, data=payload, timeout=10)
    if not res.ok:
        safe_body = mask_secrets(res.text, bot_token)
        print(f"⚠️ 응답 메시지 발송 실패: {res.status_code} {safe_body}")


def get_updates(bot_token, offset):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates"
    params = {"offset": offset, "timeout": 5}
    res = requests.get(url, params=params, timeout=15)
    res.raise_for_status()
    return res.json().get("result", [])


def status_text(control):
    state = "⏸ 일시정지됨" if control.get("paused") else "▶️ 정상 작동 중"
    updated = control.get("updated_at") or "—"
    return (
        f"📊 <b>CATALYST FILTER™ 봇 상태</b>\n\n"
        f"현재 상태: {state}\n"
        f"마지막 변경: {updated}\n\n"
        f"⏰ 자동 브리핑 시각: 매일 평일 오후 7:00 (KST)\n\n"
        f"명령어:\n"
        f"/pause  — 자동 브리핑 멈추기\n"
        f"/resume — 자동 브리핑 재개하기\n"
        f"/status — 현재 상태 확인"
    )


def main():
    bot_token = get_env("TELEGRAM_BOT_TOKEN")
    allowed_chat_id = get_env("TELEGRAM_CHAT_ID")

    control = load_control()
    offset_state = load_offset()
    last_update_id = offset_state.get("last_update_id", 0)

    try:
        updates = get_updates(bot_token, last_update_id + 1 if last_update_id else 0)
    except requests.RequestException as e:
        print(f"⚠️ 텔레그램 폴링 실패: {e}")
        sys.exit(0)  # 폴링 실패는 워크플로우 실패로 취급하지 않음 (다음 주기에 재시도)

    if not updates:
        print("새로운 명령 없음.")
        return

    control_changed = False
    max_update_id = last_update_id

    for update in updates:
        max_update_id = max(max_update_id, update["update_id"])

        message = update.get("message", {})
        text = (message.get("text") or "").strip().lower()
        chat = message.get("chat", {})
        chat_id = str(chat.get("id", ""))

        # 보안: 등록된 chat_id가 아니면 무시 (다른 사람이 봇에 명령 못 보내게)
        if chat_id != str(allowed_chat_id):
            print(f"⚠️ 미등록 chat_id({chat_id})로부터의 메시지 무시")
            continue

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if text == "/pause":
            control["paused"] = True
            control["updated_at"] = now
            control["updated_by"] = "telegram"
            control_changed = True
            send_message(bot_token, chat_id, "⏸ 자동 브리핑을 <b>일시정지</b>했습니다.\n/resume 으로 다시 켤 수 있어요.")

        elif text == "/resume":
            control["paused"] = False
            control["updated_at"] = now
            control["updated_by"] = "telegram"
            control_changed = True
            send_message(bot_token, chat_id, "▶️ 자동 브리핑을 <b>재개</b>했습니다.\n매일 오후 7시에 다시 발송됩니다.")

        elif text in ("/status", "/start"):
            send_message(bot_token, chat_id, status_text(control))

        elif text:
            send_message(
                bot_token, chat_id,
                "❓ 알 수 없는 명령입니다.\n\n/pause /resume /status 중 하나를 입력해주세요."
            )

    # offset은 처리 성공 여부와 무관하게 항상 갱신 (텔레그램 메시지 중복 수신 방지)
    save_json(OFFSET_FILE, {"last_update_id": max_update_id})

    if control_changed:
        save_json(CONTROL_FILE, control)
        print(f"✅ 상태 변경됨: paused={control['paused']}")
    else:
        print("ℹ️ 명령 처리 완료 (상태 변경 없음)")


if __name__ == "__main__":
    main()
