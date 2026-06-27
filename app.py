import streamlit as st
import yfinance as yf
import feedparser

st.set_page_config(
    page_title="StockPilot AI",
    layout="wide"
)

st.title("📈 StockPilot AI")
st.caption("투자 의사결정 지원 AI Agent")

st.info(
    "📌 본 서비스는 투자 권유가 아닌 투자 판단을 보조하기 위한 AI Agent입니다."
)

st.markdown(
    "<div style='text-align:right; color:gray; font-size:13px;'>Developed by <b>JaeWon Lee</b></div>",
    unsafe_allow_html=True
)


# =====================
# 종목 데이터
# =====================

stock_map = {

    # 삼성
    "삼성전자": "005930.KS",
    "삼성전기": "009150.KS",
    "삼성SDI": "006400.KS",
    "삼성바이오로직스": "207940.KS",
    "삼성물산": "028260.KS",

    # SK
    "SK하이닉스": "000660.KS",
    "SK텔레콤": "017670.KS",
    "SK이노베이션": "096770.KS",
    "SK스퀘어": "402340.KS",

    # 국내
    "NAVER": "035420.KS",
    "카카오": "035720.KS",

    # 미국
    "Apple": "AAPL",
    "Tesla": "TSLA",
    "NVIDIA": "NVDA",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Google": "GOOGL"
}

# =====================
# 별칭
# =====================

alias_map = {

    "하이닉스": "SK하이닉스",
    "sk하이닉스": "SK하이닉스",

    "애플": "Apple",
    "apple": "Apple",
    "APPLE": "Apple",

    "엔비디아": "NVIDIA",
    "nvidia": "NVIDIA",

    "테슬라": "Tesla",
    "tesla": "Tesla",

    "구글": "Google",
    "google": "Google"
}

# =====================
# 함수
# =====================

def calculate_rsi(data, period=14):

    delta = data["Close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss

    rsi = 100 - (100 / (1 + rs))

    return round(rsi.iloc[-1], 2)


def format_price(price, currency):

    if currency == "KRW":
        return f"{price:,.0f} 원"

    elif currency == "USD":
        return f"${price:,.2f}"

    else:
        return f"{price:,.2f} {currency}"


def format_market_cap(value):

    if value is None:
        return "N/A"

    if value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.1f}조"

    elif value >= 1_000_000:
        return f"{value / 1_000_000:.0f}백만"

    else:
        return f"{value:,}"

# =====================
# 검색
# =====================

query = st.text_input(
    "종목명 입력",
    placeholder="예: SK, 삼성, 애플, 테슬라, 엔비디아"
)
selected_stock = None

if query:

    query = query.strip()

    candidates = []

    if query in alias_map:
        candidates.append(alias_map[query])

    for stock_name in stock_map.keys():

        if query.lower() in stock_name.lower():
            candidates.append(stock_name)

    candidates = list(dict.fromkeys(candidates))

    if len(candidates) == 0:

        st.error("검색 결과가 없습니다.")
        st.stop()

    selected_stock = st.selectbox(
        "검색 결과",
        candidates
    )

# =====================
# 분석
# =====================

if selected_stock:

    try:

        ticker = stock_map[selected_stock]

        stock = yf.Ticker(ticker)

        info = stock.info

        hist = stock.history(period="1y")

        if hist.empty:
            st.error("주가 데이터를 가져오지 못했습니다.")
            st.stop()

        current_price = round(
            hist["Close"].iloc[-1],
            2
        )

        currency = info.get("currency", "")

        year_high = round(
            hist["High"].max(),
            2
        )

        year_low = round(
            hist["Low"].min(),
            2
        )

        pe = info.get("trailingPE")

        roe = info.get("returnOnEquity")

        market_cap = info.get("marketCap")

        if roe:
            roe = round(roe * 100, 2)

        rsi = calculate_rsi(hist)

        ma20 = hist["Close"].rolling(20).mean().iloc[-1]

        # =====================
        # 투자 매력도
        # =====================

        score = 50

        if pe and pe < 25:
            score += 15

        if roe and roe > 10:
            score += 15

        if 40 <= rsi <= 70:
            score += 20

        if current_price > ma20:
            score += 10

        score = min(score, 100)

        confidence = min(
            95,
            round(score * 0.9)
        )

        # =====================
        # 투자기간
        # =====================

        if score >= 85:

            invest_period = "장기 (1년 이상)"
            grade = "🟢 매우 우수"

        elif score >= 70:

            invest_period = "중장기 (3개월 ~ 1년)"
            grade = "🟡 양호"

        else:

            invest_period = "단기 (1주 ~ 3개월)"
            grade = "🔴 관망"

        # =====================
        # 출력
        # =====================

        st.markdown("---")

        st.header(selected_stock)

        st.subheader("📈 최근 1년 주가 추이")
        st.line_chart(hist["Close"])

        st.markdown("---")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "현재가",
                format_price(current_price, currency)
            )

        with col2:
            st.metric(
                "연중 최고가",
                format_price(year_high, currency)
            )

        with col3:
            st.metric(
                "연중 최저가",
                format_price(year_low, currency)
            )

        with col4:
            st.metric(
                "PER",
                f"{round(pe,2)}배" if pe else "N/A"
            )

        st.markdown("---")

        col5, col6, col7, col8, col9 = st.columns(5)

        with col5:
            st.metric(
                "ROE",
                f"{roe}%" if roe else "N/A"
            )

        with col6:
            st.metric(
                "RSI",
                rsi
            )

        with col7:
            st.metric(
                "투자 매력도",
                f"{score}점"
            )

        with col8:
            st.metric(
                "AI 신뢰도",
                f"{confidence}%"
            )

        with col9:
            st.metric(
                "시가총액",
                format_market_cap(market_cap)
            )

        st.success(
            f"추천 투자기간 : {invest_period}"
        )

        st.info(
            f"투자 등급 : {grade}"
        )

        # =====================
        # AI 의견
        # =====================

        st.markdown("---")

        st.subheader("🤖 AI 종합 의견")

        opinion = []

        opinion.append(
            f"현재 RSI는 {rsi} 수준입니다."
        )

        opinion.append(
            f"투자 매력도는 {score}점입니다."
        )

        opinion.append(
            f"AI 신뢰도는 {confidence}% 수준입니다."
        )

        if rsi > 70:
            opinion.append(
                "단기적으로 과열 가능성이 있습니다."
            )

        elif rsi < 30:
            opinion.append(
                "과매도 구간으로 해석될 수 있습니다."
            )

        else:
            opinion.append(
                "기술적 지표상 과열 상태는 아닙니다."
            )

        if roe and roe > 10:
            opinion.append(
                "ROE가 양호하여 수익성이 우수합니다."
            )

        if pe and pe < 25:
            opinion.append(
                "PER 기준 과도한 고평가 상태는 아닙니다."
            )

        for item in opinion:
            st.write("•", item)

        # =====================
        # 뉴스
        # =====================

        st.markdown("---")

        st.subheader("📰 최신 뉴스")

        rss_url = (
            f"https://news.google.com/rss/search?q={selected_stock}"
        )

        feed = feedparser.parse(rss_url)

        if len(feed.entries) == 0:

            st.write(
                "관련 뉴스를 찾지 못했습니다."
            )

        else:

            for article in feed.entries[:5]:

                st.markdown(
                    f"- [{article.title}]({article.link})"
                )

    except Exception as e:

        st.error(
            f"오류 발생 : {e}"
        )
