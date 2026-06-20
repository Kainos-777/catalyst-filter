"""
한국투자증권 API로 코스피/코스닥 지수와 관심종목 시세를 수집합니다.
"""
import requests
from datetime import datetime, timedelta
from kis_auth import KIS_BASE_URL, get_headers

# 관심 종목 (스크리닝 대상) — 필요시 자유롭게 수정하세요
WATCHLIST = [
    {"code": "000660", "name": "SK하이닉스", "sector": "반도체"},
    {"code": "005930", "name": "삼성전자", "sector": "반도체"},
    {"code": "009150", "name": "삼성전기", "sector": "전기전자"},
    {"code": "012450", "name": "한화에어로스페이스", "sector": "방산"},
    {"code": "402340", "name": "SK스퀘어", "sector": "지주"},
    {"code": "005380", "name": "현대차", "sector": "자동차"},
    {"code": "196170", "name": "알테오젠", "sector": "바이오"},
    {"code": "373220", "name": "LG에너지솔루션", "sector": "2차전지"},
    {"code": "267260", "name": "HD현대일렉트릭", "sector": "전력기기"},
    {"code": "034020", "name": "두산에너빌리티", "sector": "원전"},
]


def get_index_price(index_code):
    """
    코스피(0001) / 코스닥(1001) 지수 현재가 조회
    """
    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-index-price"
    headers = get_headers("FHPUP02100000")
    params = {
        "FID_COND_MRKT_DIV_CODE": "U",
        "FID_INPUT_ISCD": index_code,
    }
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()
    output = data.get("output", {})
    return {
        "price": output.get("bstp_nmix_prpr", "-"),
        "change": output.get("bstp_nmix_prdy_vrss", "-"),
        "change_rate": output.get("bstp_nmix_prdy_ctrt", "-"),
    }


def get_stock_price(stock_code):
    """국내주식 현재가 시세 조회"""
    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = get_headers("FHKST01010100")
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
    }
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()
    output = data.get("output", {})
    return {
        "price": output.get("stck_prpr", "-"),
        "change": output.get("prdy_vrss", "-"),
        "change_rate": output.get("prdy_ctrt", "-"),
        "volume": output.get("acml_vol", "-"),
        "high_52w": output.get("w52_hgpr", "-"),
        "low_52w": output.get("w52_lwpr", "-"),
    }


def get_investor_flow(stock_code):
    """종목별 외국인/기관 순매수 동향 (최근 거래일 기준)"""
    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-investor"
    headers = get_headers("FHKST01010900")
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
    }
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()
    output = data.get("output", [])
    if not output:
        return {"foreign_net": "-", "inst_net": "-"}
    latest = output[0]
    return {
        "foreign_net": latest.get("frgn_ntby_qty", "-"),
        "inst_net": latest.get("orgn_ntby_qty", "-"),
    }


def get_daily_chart(stock_code, period_count=20):
    """
    일봉 데이터 조회 (RSI 계산용)

    주의(중요1): KIS API는 FID_INPUT_DATE_1(조회 시작일), FID_INPUT_DATE_2(조회 종료일)에
    실제 YYYYMMDD 날짜 값을 요구한다. 빈 문자열을 보내면 API가 빈 데이터나 오류를
    반환할 수 있어, RSI 계산이 통째로 실패하는 원인이 된다.
    RSI(14)를 계산하려면 최소 15개의 종가가 필요하므로, 주말·공휴일을 감안해
    넉넉하게 60일 전부터 오늘까지 조회한다.

    주의(중요2): output2는 일반적으로 최신 날짜가 먼저 오는 내림차순으로 알려져
    있으나, 이는 비공식 경험칙이며 API 응답이 항상 이 순서를 보장한다고 가정하면
    위험하다(RSI가 정반대로 계산될 수 있음). 따라서 인덱스 반전(closes[::-1])
    대신, 응답에 포함된 실제 영업일자(stck_bsop_date) 필드 기준으로 명시적
    오름차순 정렬을 수행해 정렬 순서에 대한 가정을 코드에서 제거한다.
    """
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")

    url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
    headers = get_headers("FHKST03010100")
    params = {
        "FID_COND_MRKT_DIV_CODE": "J",
        "FID_INPUT_ISCD": stock_code,
        "FID_INPUT_DATE_1": start_date,
        "FID_INPUT_DATE_2": end_date,
        "FID_PERIOD_DIV_CODE": "D",
        "FID_ORG_ADJ_PRC": "1",
    }
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    data = res.json()
    output = data.get("output2", [])

    # 날짜(stck_bsop_date) 기준 오름차순(과거→현재) 정렬 — API의 암묵적 순서에 의존하지 않음
    rows = [d for d in output if d.get("stck_clpr") and d.get("stck_bsop_date")]
    rows.sort(key=lambda d: d["stck_bsop_date"])

    # 최근 period_count개만 사용 (정렬 후 뒤쪽이 최신)
    rows = rows[-period_count:]
    closes = [float(d["stck_clpr"]) for d in rows]
    return closes


def calc_rsi(closes, period=14):
    """
    RSI(상대강도지수) 계산.
    입력 계약: closes는 과거→현재 순서(오름차순)로 정렬되어 있어야 한다.
    (get_daily_chart()가 stck_bsop_date 기준으로 이미 오름차순 정렬해서 반환함)

    엣지케이스 처리: avg_gain과 avg_loss가 모두 0인 경우(완전히 가격
    변동이 없는 구간 — 거래정지, 데이터 수신 결손 등에서 발생 가능)는
    수학적으로 100을 반환할 수 있으나, 이를 "과매수"로 해석해 매도
    신호를 내는 것은 실거래상 위험한 오판이다. 따라서 이 경우는
    "판단 불가"로 보고 None을 반환해 데이터 부족과 동일하게 다룬다.
    """
    if len(closes) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_gain == 0 and avg_loss == 0:
        # 완전 횡보(가격 변동 전무) — 판단 불가로 처리
        return None
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 1)


def fetch_all_market_data():
    """전체 시장 데이터 한 번에 수집"""
    result = {"kospi": None, "kosdaq": None, "stocks": []}

    try:
        result["kospi"] = get_index_price("0001")
    except Exception as e:
        result["kospi"] = {"error": str(e)}

    try:
        result["kosdaq"] = get_index_price("1001")
    except Exception as e:
        result["kosdaq"] = {"error": str(e)}

    for item in WATCHLIST:
        code = item["code"]
        try:
            price_info = get_stock_price(code)
            flow_info = get_investor_flow(code)
            closes = get_daily_chart(code, period_count=20)
            rsi = calc_rsi(closes)

            result["stocks"].append({
                **item,
                **price_info,
                **flow_info,
                "rsi": rsi,
            })
        except Exception as e:
            result["stocks"].append({**item, "error": str(e)})

    return result


if __name__ == "__main__":
    import json as _json
    data = fetch_all_market_data()
    print(_json.dumps(data, ensure_ascii=False, indent=2))
