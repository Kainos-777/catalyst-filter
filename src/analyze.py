"""
수집된 데이터를 기반으로 5가지 기준 스크리닝 + 매수/매도 신호 생성
"""


def signal_from_rsi(rsi):
    if rsi is None:
        return "관망"
    if rsi < 40:
        return "매수"
    if rsi > 65:
        return "매도"
    return "관망"


def score_stock(stock):
    """
    5가지 기준으로 종목 채점:
    1. 수급 (외국인/기관 순매수)
    2. RSI 적정 구간 (30~55)
    3. 거래량 활발 여부
    4. 52주 위치
    5. 등락률 방향성
    """
    pass_count = 0
    reasons = []

    # 1. 수급
    try:
        foreign_net = float(stock.get("foreign_net", 0) or 0)
        inst_net = float(stock.get("inst_net", 0) or 0)
        if foreign_net > 0 or inst_net > 0:
            pass_count += 1
            reasons.append(f"수급 양호 (외인 {foreign_net:+,.0f}주, 기관 {inst_net:+,.0f}주)")
        else:
            reasons.append(f"수급 약세 (외인 {foreign_net:+,.0f}주, 기관 {inst_net:+,.0f}주)")
    except (ValueError, TypeError):
        reasons.append("수급 데이터 확인 불가")

    # 2. RSI
    rsi = stock.get("rsi")
    if rsi is not None:
        if 30 <= rsi <= 55:
            pass_count += 1
            reasons.append(f"RSI {rsi} — 매수 적정 구간")
        elif rsi < 30:
            reasons.append(f"RSI {rsi} — 과매도 (반등 주시)")
        else:
            reasons.append(f"RSI {rsi} — 과매수 (조정 주의)")

    # 3. 거래량
    try:
        volume = float(stock.get("volume", 0) or 0)
        if volume > 0:
            pass_count += 1
    except (ValueError, TypeError):
        pass

    # 4. 52주 위치
    try:
        price = float(stock.get("price", 0) or 0)
        high_52w = float(stock.get("high_52w", 0) or 0)
        low_52w = float(stock.get("low_52w", 0) or 0)
        if high_52w > low_52w:
            position = (price - low_52w) / (high_52w - low_52w) * 100
            if 20 <= position <= 80:
                pass_count += 1
            reasons.append(f"52주 위치 {position:.0f}%")
    except (ValueError, TypeError, ZeroDivisionError):
        pass

    # 5. 등락률 방향
    try:
        change_rate = float(stock.get("change_rate", 0) or 0)
        if -3 <= change_rate <= 5:
            pass_count += 1
            reasons.append(f"등락률 {change_rate:+.2f}% — 안정적 변동성")
        else:
            reasons.append(f"등락률 {change_rate:+.2f}% — 변동성 확대")
    except (ValueError, TypeError):
        pass

    signal = signal_from_rsi(rsi)
    if pass_count >= 4:
        signal = "매수"
    elif pass_count <= 2:
        signal = "관망"

    return {
        "pass_count": pass_count,
        "signal": signal,
        "reasons": reasons,
    }


def analyze_market(raw_data):
    """전체 시장 데이터를 분석해서 최종 리포트 생성"""
    analyzed_stocks = []

    for stock in raw_data.get("stocks", []):
        if "error" in stock:
            analyzed_stocks.append({**stock, "signal": "오류", "pass_count": 0, "reasons": [stock["error"]]})
            continue
        analysis = score_stock(stock)
        analyzed_stocks.append({**stock, **analysis})

    analyzed_stocks.sort(key=lambda x: x.get("pass_count", 0), reverse=True)

    buy_list = [s for s in analyzed_stocks if s.get("signal") == "매수"]
    hold_list = [s for s in analyzed_stocks if s.get("signal") == "관망"]
    sell_list = [s for s in analyzed_stocks if s.get("signal") == "매도"]

    return {
        "kospi": raw_data.get("kospi"),
        "kosdaq": raw_data.get("kosdaq"),
        "all_stocks": analyzed_stocks,
        "buy_list": buy_list,
        "hold_list": hold_list,
        "sell_list": sell_list,
    }
