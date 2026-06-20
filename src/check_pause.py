"""
docs/control.json 의 일시정지 플래그를 읽어
GitHub Actions의 step output(steps.pause_check.outputs.paused)으로 전달합니다.

control.json 형식:
{
  "paused": false,
  "updated_at": "2026-06-20T10:00:00",
  "updated_by": "telegram"
}

파일이 없거나 손상된 경우, 안전을 위해 "정상 작동(일시정지 아님)"으로
간주합니다. 일시정지 플래그 손상으로 인해 브리핑이 영구히 멈추는 것보다는,
의도치 않게 한 번 더 발송되는 쪽이 훨씬 안전하기 때문입니다.
"""
import json
import os

CONTROL_FILE = os.path.join(os.path.dirname(__file__), "..", "docs", "control.json")
GITHUB_OUTPUT = os.environ.get("GITHUB_OUTPUT")


def is_paused():
    if not os.path.exists(CONTROL_FILE):
        return False
    try:
        with open(CONTROL_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return False
        return bool(data.get("paused", False))
    except (json.JSONDecodeError, OSError):
        # 파일이 깨져 있으면 안전하게 "정상 작동"으로 간주 (브리핑을 막지 않음)
        return False


def main():
    paused = is_paused()
    print(f"일시정지 상태: {paused}")

    if GITHUB_OUTPUT:
        with open(GITHUB_OUTPUT, "a", encoding="utf-8") as f:
            f.write(f"paused={'true' if paused else 'false'}\n")

    if paused:
        print("⏸ 봇이 일시정지 상태입니다. 브리핑을 건너뜁니다.")
    else:
        print("▶️ 봇이 정상 작동 중입니다. 브리핑을 진행합니다.")


if __name__ == "__main__":
    main()
