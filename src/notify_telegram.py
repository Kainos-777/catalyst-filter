"""
텔레그램 봇으로 분석 결과를 발송합니다.
"""
import os
import requests
from datetime import datetime


def get_env(name):
    val = os.environ.get(name)
    if not val:
        raise RuntimeError(f"환경변수 {name} 가 설정되지 않았습니다. GitHub Secrets를 확인하세요.")
    return val


def split_message_safely(text, max_len=3500):
    """
    텔레그램 메시지 길이 제한(4096자) 대응.
    단순 문자 슬라이싱은 <b>...</b> 같은 HTML 태그를 중간에서 잘라
    parse_mode=HTML 요청이 400 Bad Request로 거부될 수 있으므로,
    반드시 줄바꿈(\n) 단위로만 분할한다.
    한 줄 자체가 max_len을 넘는 비정상적인 경우에도 태그 손상을
    피하기 위해 그 줄은 통째로 다음 청크로 보낸다(드물게 청크가
    max_len을 살짝 초과할 수 있으나, 4096자 한도에는 여유가 있다).
    """
    lines = text.split("\n")
    chunks = []
    current = []
    current_len = 0

    for line in lines:
        line_len = len(line) + 1  # 줄바꿈 문자 포함
        if current and current_len + line_len > max_len:
            chunks.append("\n".join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len

    if current:
        chunks.append("\n".join(current))

    return chunks


def mask_secrets(text, *secrets):
    """
    로그 출력 전, 혹시라도 응답 본문에 시크릿 값이 포함되어 있을 경우를 대비한
    방어적 마스킹. GitHub Actions가 env로 등록된 secrets를 자동 마스킹하지만,
    다층 방어(defense in depth) 차원에서 한 번 더 가립니다.
    """
    for secret in secrets:
        if secret and len(secret) >= 8:
            text = text.replace(secret, "***MASKED***")
    return text


def send_telegram_message(text, parse_mode="HTML"):
    """텔레그램으로 메시지 발송 (4096자 제한을 줄 단위로 안전하게 분할)"""
    bot_token = get_env("TELEGRAM_BOT_TOKEN")
    chat_id = get_env("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    chunks = split_message_safely(text)

    for chunk in chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        res = requests.post(url, data=payload, timeout=10)
        if not res.ok:
            safe_body = mask_secrets(res.text, bot_token)
            print(f"⚠️ 텔레그램 발송 실패: {res.status_code} {safe_body}")
        res.raise_for_status()


def fmt_num(val):
    try:
        return f"{float(val):,.0f}"
    except (ValueError, TypeError):
        return str(val)


def fmt_change(val):
    try:
        v = float(val)
        sign = "🔺" if v > 0 else ("🔻" if v < 0 else "➖")
        return f"{sign} {v:+,.2f}"
    except (ValueError, TypeError):
        return str(val)


def build_briefing_message(analyzed):
    today = datetime.now().strftime("%Y년 %m월 %d일 %H:%M")

    kospi = analyzed.get("kospi") or {}
    kosdaq = analyzed.get("kosdaq") or {}

    lines = []
    lines.append(f"📊 <b>CATALYST FILTER™ 장마감 브리핑</b>")
    lines.append(f"🕐 {today}")
    lines.append("━━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("💹 <b>지수 현황</b>")

    if "error" in kospi:
        lines.append(f"⚠️ KOSPI 데이터 조회 실패 ({kospi['error']})")
    else:
        lines.append(f"KOSPI  {fmt_num(kospi.get('price'))}  ({fmt_change(kospi.get('change_rate'))}%)")

    if "error" in kosdaq:
        lines.append(f"⚠️ KOSDAQ 데이터 조회 실패 ({kosdaq['error']})")
    else:
        lines.append(f"KOSDAQ {fmt_num(kosdaq.get('price'))}  ({fmt_change(kosdaq.get('change_rate'))}%)")
    lines.append("")

    buy_list = analyzed.get("buy_list", [])
    if buy_list:
        lines.append(f"📈 <b>매수 신호 ({len(buy_list)}종목)</b>")
        for s in buy_list:
            rsi_txt = f"RSI {s['rsi']}" if s.get("rsi") is not None else "RSI -"
            lines.append(
                f"• <b>{s['name']}</b> ({s['sector']}) {fmt_num(s.get('price'))}원 "
                f"{fmt_change(s.get('change_rate'))}% | {rsi_txt} | {s.get('pass_count')}/5"
            )
        lines.append("")

    hold_list = analyzed.get("hold_list", [])
    if hold_list:
        lines.append(f"⏸ <b>관망 ({len(hold_list)}종목)</b>")
        for s in hold_list:
            rsi_txt = f"RSI {s['rsi']}" if s.get("rsi") is not None else "RSI -"
            lines.append(
                f"• {s['name']} {fmt_num(s.get('price'))}원 {fmt_change(s.get('change_rate'))}% | {rsi_txt}"
            )
        lines.append("")

    sell_list = analyzed.get("sell_list", [])
    if sell_list:
        lines.append(f"📉 <b>매도 신호 ({len(sell_list)}종목)</b>")
        for s in sell_list:
            rsi_txt = f"RSI {s['rsi']}" if s.get("rsi") is not None else "RSI -"
            lines.append(
                f"• {s['name']} {fmt_num(s.get('price'))}원 {fmt_change(s.get('change_rate'))}% | {rsi_txt}"
            )
        lines.append("")

    # 조회 자체가 실패한 종목은 buy/hold/sell 어디에도 속하지 않으므로
    # 별도로 명시해 "조용히 누락"되는 일이 없게 한다.
    error_list = [s for s in analyzed.get("all_stocks", []) if s.get("signal") == "오류"]
    if error_list:
        lines.append(f"⚠️ <b>조회 실패 ({len(error_list)}종목)</b>")
        for s in error_list:
            err = (s.get("reasons") or ["알 수 없는 오류"])[0]
            lines.append(f"• {s['name']}: {err}")
        lines.append("")

    lines.append("━━━━━━━━━━━━━━━━━")
    lines.append("⚠️ 투자 참고용 자료입니다. 투자 손실의 책임은 투자자 본인에게 있습니다.")
    lines.append(f"🔗 상세 대시보드: {get_pages_url()}")

    return "\n".join(lines)


def get_pages_url():
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if "/" in repo:
        owner, name = repo.split("/", 1)
        return f"https://{owner}.github.io/{name}/"
    return "(GitHub Pages URL)"
