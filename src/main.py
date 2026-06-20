"""
메인 실행 스크립트
1. KIS API로 시장 데이터 수집
2. 5가지 기준으로 분석
3. JSON으로 저장 (GitHub Pages용)
4. 텔레그램으로 발송
"""
import json
import sys
from datetime import datetime

from fetch_market_data import fetch_all_market_data
from analyze import analyze_market
from notify_telegram import send_telegram_message, build_briefing_message


def main():
    print("1️⃣ 시장 데이터 수집 중...")
    raw_data = fetch_all_market_data()

    print("2️⃣ 데이터 분석 중...")
    analyzed = analyze_market(raw_data)

    print("3️⃣ 결과 JSON 저장 중...")
    output = {
        "generated_at": datetime.now().isoformat(),
        "data": analyzed,
    }
    with open("../docs/data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("   → docs/data.json 저장 완료")

    print("4️⃣ 텔레그램 발송 중...")
    message = build_briefing_message(analyzed)
    try:
        send_telegram_message(message)
        print("   → 텔레그램 발송 완료")
    except Exception as e:
        print(f"   ⚠️ 텔레그램 발송 실패: {e}")
        sys.exit(1)

    print("✅ 전체 프로세스 완료")


if __name__ == "__main__":
    main()
