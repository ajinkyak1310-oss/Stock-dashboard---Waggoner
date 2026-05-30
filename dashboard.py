import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Portfolio Dashboard", layout="wide", page_icon="📈")

PORTFOLIO = [
    {"ticker": "FCNCA", "sector": "Financials",               "class": "ERN"},
    {"ticker": "MELI",  "sector": "Consumer Discretionary",   "class": "ERN"},
    {"ticker": "ONON",  "sector": "Consumer Discretionary",   "class": "FCF"},
    {"ticker": "DECK",  "sector": "Consumer Discretionary",   "class": "ERN"},
    {"ticker": "OMAB",  "sector": "Industrials",              "class": "DIV"},
    {"ticker": "NTES",  "sector": "Information Technology",   "class": "DIV"},
    {"ticker": "KDP",   "sector": "Consumer Staples",         "class": "DIV"},
    {"ticker": "AXON",  "sector": "Industrials",              "class": "REV"},
    {"ticker": "CAVA",  "sector": "Consumer Discretionary",   "class": "REV"},
    {"ticker": "TTWO",  "sector": "Communication Services",   "class": "REV"},
    {"ticker": "JPM",   "sector": "Financials",               "class": "DIV"},
    {"ticker": "MS",    "sector": "Financials",               "class": "DIV"},
    {"ticker": "PGR",   "sector": "Financials",               "class": "ERN"},
    {"ticker": "IBKR",  "sector": "Financials",               "class": "ERN"},
    {"ticker": "FSLR",  "sector": "Information Technology",   "class": "ERN"},
    {"ticker": "CME",   "sector": "Financials",               "class": "DIV"},
    {"ticker": "BK",    "sector": "Financials",               "class": "DIV"},
    {"ticker": "XZO",   "sector": "Information Technology",   "class": "REV"},
    {"ticker": "CVNA",  "sector": "Consumer Discretionary",   "class": "FCF"},
    {"ticker": "SOFI",  "sector": "Financials",               "class": "FCF"},
    {"ticker": "OZK",   "sector": "Financials",               "class": "DIV"},
    {"ticker": "CRWV",  "sector": "Information Technology",   "class": "REV"},
    {"ticker": "ALAB",  "sector": "Information Technology",   "class": "REV"},
    {"ticker": "ANET",  "sector": "Information Technology",   "class": "ERN"},
]

CLASS_COLORS = {"ERN": "🟡", "FCF": "🟢", "DIV": "🔵", "REV": "🟠"}

@st.cache_data(ttl=300)
def fetch_stock_data(tickers):
    rows = []
    for item in tickers:
        t = item["ticker"]
        try:
            info = yf.Ticker(t).info
            price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice")
            prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
            change_pct = ((price - prev_close) / prev_close * 100) if price and prev_close else None
            rows.append({
                "Ticker": t,
                "Name": info.get("shortName") or info.get("longName") or t,
                "Sector": item["sector"],
                "Class": item["class"],
                "Price": price,
                "Chg %": change_pct,
                "Volume": info.get("regularMarketVolume"),
                "Mkt Cap": info.get("marketCap"),
                "P/E": info.get("trailingPE"),
                "52W High": info.get("fiftyTwoWeekHigh"),
                "52W Low": info.get("fiftyTwoWeekLow"),
                "EPS": info.get("trailingEps"),
                "Div Yield": info.get("dividendYield"),
            })
        except Exception:
            rows.append({"Ticker": t, "Name": t, "Sector": item["sector"], "Class": item["class"],
                         "Price": None, "Chg %": None, "Volume": None, "Mkt Cap": None,
                         "P/E": None, "52W High": None, "52W Low": None, "EPS": None, "Div Yield": None})
    return pd.DataFrame(rows)

@st.cache_data(ttl=600)
def fetch_news(tickers):
    all_news = []
    for item in tickers:
        t = item["ticker"]
        try:
            news = yf.Ticker(t).news
            for n in (news or [])[:3]:
                content = n.get("content", {})
                title = content.get("title", n.get("title", ""))
                pub = content.get("pubDate", n.get("providerPublishTime", ""))
                link = ""
                click_url = content.get("clickThroughUrl", {})
                if isinstance(click_url, dict):
                    link = click_url.get("url", "")
                if not link:
                    link = n.get("link", "")
                if title:
                    all_news.append({"Ticker": t, "Headline": title, "Published": pub, "URL": link})
        except Exception:
            pass
    return all_news

def fmt_price(v):
    return f"${v:,.2f}" if v else "—"

def fmt_pct(v):
    if v is None:
        return "—"
    arrow = "▲" if v >= 0 else "▼"
    return f"{arrow} {abs(v):.2f}%"

def fmt_large(v):
    if not v:
        return "—"
    if v >= 1e12:
        return f"${v/1e12:.2f}T"
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.2f}M"
    return f"${v:,.0f}"

def fmt_vol(v):
    if not v:
        return "—"
    if v >= 1e6:
        return f"{v/1e6:.2f}M"
    if v >= 1e3:
        return f"{v/1e3:.1f}K"
    return str(v)

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("🗂 Filters")
sectors = ["All"] + sorted(set(p["sector"] for p in PORTFOLIO))
classes = ["All"] + sorted(set(p["class"] for p in PORTFOLIO))
sel_sector = st.sidebar.selectbox("Sector", sectors)
sel_class  = st.sidebar.selectbox("Class",  classes)

# Pre-filter by sector/class to build name options
pre_filtered = [p for p in PORTFOLIO
                if (sel_sector == "All" or p["sector"] == sel_sector)
                and (sel_class == "All" or p["class"] == sel_class)]

ticker_options = ["All"] + [p["ticker"] for p in pre_filtered]
sel_stock = st.sidebar.selectbox("Stock", ticker_options)

sel_tickers = [p["ticker"] for p in pre_filtered
               if sel_stock == "All" or p["ticker"] == sel_stock]

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()

st.sidebar.markdown("---")
st.sidebar.markdown("**Class Legend**")
for k, v in CLASS_COLORS.items():
    st.sidebar.markdown(f"{v} **{k}**")

# ── Header ───────────────────────────────────────────────────────────────────
st.title("📈 Portfolio Dashboard")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  Data delayed ~15 min")

filtered_portfolio = [p for p in PORTFOLIO if p["ticker"] in sel_tickers]
df = fetch_stock_data(filtered_portfolio)

# Build ticker → name map for dropdowns
ticker_name_map = {row["Ticker"]: row["Name"] for _, row in df.iterrows()}
ticker_labels = [f"{t} — {ticker_name_map.get(t, t)}" for t in sel_tickers]
label_to_ticker = {f"{t} — {ticker_name_map.get(t, t)}": t for t in sel_tickers}

# ── Top KPI Cards ─────────────────────────────────────────────────────────────
gainers = df[df["Chg %"] > 0].shape[0]
losers  = df[df["Chg %"] < 0].shape[0]
avg_chg = df["Chg %"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Stocks Tracked", len(df))
c2.metric("Gainers", gainers)
c3.metric("Losers", losers)
c4.metric("Avg Change", f"{avg_chg:+.2f}%" if pd.notna(avg_chg) else "—")

st.markdown("---")

# ── Price Table ───────────────────────────────────────────────────────────────
st.subheader("Stock Overview")

display_df = df.copy()
display_df["Class"] = display_df["Class"].apply(lambda x: f"{CLASS_COLORS.get(x,'')} {x}")
display_df["Price"]     = display_df["Price"].apply(fmt_price)
display_df["Chg %"]     = display_df["Chg %"].apply(fmt_pct)
display_df["Volume"]    = display_df["Volume"].apply(fmt_vol)
display_df["Mkt Cap"]   = display_df["Mkt Cap"].apply(fmt_large)
display_df["P/E"]       = display_df["P/E"].apply(lambda x: f"{x:.1f}" if x else "—")
display_df["EPS"]       = display_df["EPS"].apply(lambda x: f"${x:.2f}" if x else "—")
display_df["52W High"]  = display_df["52W High"].apply(fmt_price)
display_df["52W Low"]   = display_df["52W Low"].apply(fmt_price)
display_df["Div Yield"] = display_df["Div Yield"].apply(lambda x: f"{x*100:.2f}%" if x else "—")

st.dataframe(
    display_df[["Ticker", "Name", "Sector", "Class", "Price", "Chg %", "Volume",
                "Mkt Cap", "P/E", "EPS", "52W High", "52W Low", "Div Yield"]],
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")

# ── Price Chart ───────────────────────────────────────────────────────────────
st.subheader("Price Chart (30 Days)")
chart_label = st.selectbox("Select stock to chart", ticker_labels)
chart_ticker = label_to_ticker[chart_label]

@st.cache_data(ttl=300)
def get_history(ticker):
    return yf.Ticker(ticker).history(period="1mo")

hist = get_history(chart_ticker)
if not hist.empty:
    st.line_chart(hist["Close"], use_container_width=True)
else:
    st.info("No chart data available.")

st.markdown("---")

# ── News Feed ─────────────────────────────────────────────────────────────────
st.subheader("Latest News")
news = fetch_news(filtered_portfolio)

if news:
    news_label = st.selectbox("Filter news by stock", ["All"] + ticker_labels, key="news_filter")
    news_ticker = None if news_label == "All" else label_to_ticker[news_label]
    shown = [n for n in news if news_ticker is None or n["Ticker"] == news_ticker]
    for n in shown[:20]:
        pub = n["Published"]
        if isinstance(pub, (int, float)):
            pub = datetime.utcfromtimestamp(pub).strftime("%Y-%m-%d %H:%M")
        if n["URL"]:
            st.markdown(f"**{n['Ticker']}** — [{n['Headline']}]({n['URL']}) <span style='color:gray;font-size:12px'>{pub}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"**{n['Ticker']}** — {n['Headline']} <span style='color:gray;font-size:12px'>{pub}</span>", unsafe_allow_html=True)
else:
    st.info("No news found.")
