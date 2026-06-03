import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

try:
    from curl_cffi import requests as curl_requests
    @st.cache_resource
    def get_session():
        return curl_requests.Session(impersonate="chrome110")
except ImportError:
    get_session = lambda: None

st.set_page_config(page_title="Portfolio Dashboard", layout="wide", page_icon="📈")

st.markdown("""
<style>
/* ── Global background ───────────────────────────────────────────────── */
.stApp {
    background: linear-gradient(160deg, #0d1117 0%, #0d1b2a 50%, #0d1117 100%);
}

/* ── Sidebar ─────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%);
    border-right: 1px solid rgba(99,102,241,0.25);
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stMarkdown {
    color: #94a3b8 !important;
}

/* ── Metric cards ────────────────────────────────────────────────────── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #161b22, #1c2333);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4), 0 0 0 1px rgba(99,102,241,0.1);
    transition: transform 0.2s, box-shadow 0.2s;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 30px rgba(99,102,241,0.2);
}
[data-testid="stMetricLabel"] {
    color: #7c8db0 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
[data-testid="stMetricValue"] {
    color: #e6edf3 !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] {
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}

/* ── Tabs ────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: #161b22;
    border-radius: 12px;
    padding: 4px;
    gap: 4px;
    border: 1px solid rgba(99,102,241,0.2);
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #7c8db0;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    padding: 8px 16px;
    border: none;
    transition: all 0.2s;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(99,102,241,0.15);
    color: #a5b4fc;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    box-shadow: 0 2px 10px rgba(99,102,241,0.4);
}

/* ── Buttons ─────────────────────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    padding: 8px 20px;
    box-shadow: 0 2px 10px rgba(99,102,241,0.3);
    transition: all 0.2s;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(99,102,241,0.5);
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
}

/* ── Sliders ─────────────────────────────────────────────────────────── */
[data-testid="stSlider"] [data-testid="stThumbValue"] {
    background: #6366f1;
}
.stSlider .st-bo { background: #6366f1 !important; }

/* ── Selectbox / dropdowns ───────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div {
    background: #161b22;
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 8px;
}

/* ── Dataframe ───────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 10px;
    overflow: hidden;
}

/* ── Section dividers ────────────────────────────────────────────────── */
hr {
    border-color: rgba(99,102,241,0.2) !important;
}

/* ── Subheaders ──────────────────────────────────────────────────────── */
h2, h3 {
    background: linear-gradient(90deg, #a5b4fc, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700 !important;
}

/* ── Info / warning boxes ────────────────────────────────────────────── */
[data-testid="stInfo"] {
    background: rgba(99,102,241,0.1);
    border-left: 3px solid #6366f1;
    border-radius: 8px;
}
[data-testid="stWarning"] {
    background: rgba(245,158,11,0.1);
    border-left: 3px solid #f59e0b;
    border-radius: 8px;
}

/* ── Progress bar (52W range) ────────────────────────────────────────── */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg, #6366f1, #8b5cf6);
    border-radius: 99px;
}
[data-testid="stProgressBar"] > div {
    background: rgba(99,102,241,0.15);
    border-radius: 99px;
}

/* ── Caption text ────────────────────────────────────────────────────── */
[data-testid="stCaptionContainer"] p {
    color: #7c8db0 !important;
}
</style>
""", unsafe_allow_html=True)

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

# ── Data Fetching ─────────────────────────────────────────────────────────────

def yticker(symbol):
    """Create a yfinance Ticker with curl_cffi session when available."""
    session = get_session()
    if session is not None:
        return yf.Ticker(symbol, session=session)
    return yf.Ticker(symbol)

@st.cache_data(ttl=300)
def fetch_stock_data(tickers):
    rows = []
    errors = []
    for item in tickers:
        t = item["ticker"]
        try:
            ticker_obj = yticker(t)
            info = ticker_obj.info

            # info dict sometimes returns empty on cloud — fallback to fast_info
            price = (info.get("currentPrice") or info.get("regularMarketPrice")
                     or info.get("navPrice"))
            prev_close = (info.get("previousClose")
                          or info.get("regularMarketPreviousClose"))

            # Fallback: use fast_info if info didn't return price
            if not price:
                try:
                    fi = ticker_obj.fast_info
                    price      = getattr(fi, "last_price", None)
                    prev_close = getattr(fi, "previous_close", None)
                except Exception:
                    pass

            change_pct = ((price - prev_close) / prev_close * 100) if price and prev_close else None

            rows.append({
                "Ticker":   t,
                "Name":     info.get("shortName") or info.get("longName") or t,
                "Sector":   item["sector"],
                "Class":    item["class"],
                "Price":    price,
                "Chg %":    change_pct,
                "Volume":   info.get("regularMarketVolume"),
                "Mkt Cap":  info.get("marketCap"),
                "P/E":      info.get("trailingPE"),
                "52W High": info.get("fiftyTwoWeekHigh"),
                "52W Low":  info.get("fiftyTwoWeekLow"),
                "EPS":      info.get("trailingEps"),
                "Div Yield":info.get("dividendYield"),
            })
        except Exception as e:
            errors.append(f"{t}: {e}")
            rows.append({"Ticker": t, "Name": t, "Sector": item["sector"], "Class": item["class"],
                         "Price": None, "Chg %": None, "Volume": None, "Mkt Cap": None,
                         "P/E": None, "52W High": None, "52W Low": None, "EPS": None, "Div Yield": None})

    df = pd.DataFrame(rows)
    if errors:
        df.attrs["errors"] = errors
    return df

@st.cache_data(ttl=600)
def fetch_news(tickers):
    all_news = []
    for item in tickers:
        t = item["ticker"]
        try:
            news = yticker(t).news
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

@st.cache_data(ttl=600)
def fetch_detail(ticker):
    try:
        t = yticker(ticker)
        return {
            "info": t.info,
            "quarterly_financials": t.quarterly_financials,
            "financials": t.financials,
            "balance_sheet": t.balance_sheet,
            "cashflow": t.cashflow,
        }
    except Exception:
        return {"info": {}, "quarterly_financials": None,
                "financials": None, "balance_sheet": None, "cashflow": None}

@st.cache_data(ttl=300)
def get_history(ticker, period):
    try:
        return yticker(ticker).history(period=period)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def fetch_industry_peers(industry_key, exclude_ticker, max_peers=12):
    """Fetch top companies in the same industry from yfinance, then get their multiples."""
    try:
        top = yf.Industry(industry_key).top_companies
        peer_symbols = [s for s in top.index.tolist() if s != exclude_ticker][:max_peers]
    except Exception:
        return pd.DataFrame()

    rows = []
    for sym in peer_symbols:
        try:
            inf = yticker(sym).info
            price = inf.get("currentPrice") or inf.get("regularMarketPrice")
            rev   = inf.get("totalRevenue")
            mcap  = inf.get("marketCap")
            rows.append({
                "Ticker":    sym,
                "Name":      inf.get("shortName") or sym,
                "Price":     price,
                "Mkt Cap":   mcap,
                "P/E":       inf.get("trailingPE"),
                "P/B":       inf.get("priceToBook"),
                "EV/EBITDA": inf.get("enterpriseToEbitda"),
                "P/S":       (mcap / rev) if mcap and rev and rev > 0 else None,
                "Revenue":   rev,
                "Net Margin":inf.get("profitMargins"),
                "EPS":       inf.get("trailingEps"),
                "Book Value":inf.get("bookValue"),
                "EBITDA":    inf.get("ebitda"),
                "EV":        inf.get("enterpriseValue"),
                "Shares":    inf.get("sharesOutstanding"),
            })
        except Exception:
            pass
    return pd.DataFrame(rows)

@st.cache_data(ttl=600)
def fetch_peers_data(peer_tickers):
    rows = []
    for t in peer_tickers:
        try:
            info = yticker(t).info
            price     = info.get("currentPrice") or info.get("regularMarketPrice")
            prev      = info.get("previousClose") or info.get("regularMarketPreviousClose")
            chg       = ((price - prev) / prev * 100) if price and prev else None
            rows.append({
                "Ticker":    t,
                "Name":      info.get("shortName") or t,
                "Price":     price,
                "Chg %":     chg,
                "Mkt Cap":   info.get("marketCap"),
                "P/E":       info.get("trailingPE"),
                "P/B":       info.get("priceToBook"),
                "EV/EBITDA": info.get("enterpriseToEbitda"),
                "Revenue":   info.get("totalRevenue"),
                "Net Income":info.get("netIncomeToCommon"),
                "Net Margin":info.get("profitMargins"),
                "Div Yield": info.get("dividendYield"),
                "52W High":  info.get("fiftyTwoWeekHigh"),
                "52W Low":   info.get("fiftyTwoWeekLow"),
                "ROE":       info.get("returnOnEquity"),
            })
        except Exception:
            rows.append({"Ticker": t, "Name": t})
    return pd.DataFrame(rows)

# ── Formatters ────────────────────────────────────────────────────────────────

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

def _detect_scale(df_raw, key_rows):
    """Return (divisor, label) based on the magnitude of revenue/top-line values."""
    for row in key_rows:
        if row in df_raw.index:
            vals = df_raw.loc[row].dropna()
            if not vals.empty:
                mx = vals.abs().max()
                if mx >= 1e9:
                    return 1e9, "B"
                return 1e6, "M"
    return 1e6, "M"

def _fmt_scaled(v, div):
    if pd.isna(v) or v is None:
        return "—"
    return f"${v / div:,.2f}"

def _fmt_pct_val(v):
    if pd.isna(v) or v is None:
        return "—"
    return f"{v * 100:.1f}%"

def _fmt_growth(v):
    if pd.isna(v) or v is None:
        return "—"
    sign = "+" if v >= 0 else ""
    return f"{sign}{v:.1f}%"

def render_income_table(df_raw):
    """Render a rich P&L table with expenses, margins, and YoY growth — uniform unit."""
    if df_raw is None or df_raw.empty:
        st.info("No data available.")
        return

    div, unit = _detect_scale(df_raw, ["Total Revenue"])
    cols = list(df_raw.columns[:8])  # up to 8 periods
    col_labels = [c.strftime("%b '%y") if hasattr(c, "strftime") else str(c) for c in cols]

    def get(row):
        """Return a plain list of numeric values for `row`, length = len(cols)."""
        if row in df_raw.index:
            vals = pd.to_numeric(df_raw.loc[row, cols], errors="coerce")
            return list(vals)
        return [None] * len(cols)

    def get_first(*rows):
        """Return the first row that exists in df_raw."""
        for row in rows:
            if row in df_raw.index:
                return get(row)
        return [None] * len(cols)

    rev   = get("Total Revenue")
    cogs  = get("Cost Of Revenue")
    gp    = get("Gross Profit")
    rd    = get("Research And Development")
    sga   = get("Selling General And Administration")
    op    = get("Operating Income")
    ebit  = get("EBITDA")
    ie    = get_first("Interest Expense Non Operating", "Interest Expense", "Net Non Operating Interest Income Expense")
    pbt   = get("Pretax Income")
    tax   = get("Tax Provision")
    ni    = get("Net Income")
    eps_b = get("Basic EPS")
    eps_d = get("Diluted EPS")

    def add_lists(a, b):
        result = []
        for x, y in zip(a, b):
            if x is None and y is None:
                result.append(None)
            else:
                result.append((x or 0) + (y or 0))
        return result

    def margin(num, denom):
        return [
            (n / d) if (n is not None and d and not pd.isna(n) and not pd.isna(d)) else None
            for n, d in zip(num, denom)
        ]

    def yoy_growth(lst):
        growth = [None] * len(lst)
        for i in range(len(lst) - 1):
            cur, prev = lst[i], lst[i + 1]
            if cur is not None and prev is not None and not pd.isna(cur) and not pd.isna(prev) and prev != 0:
                growth[i] = (cur - prev) / abs(prev) * 100
        return growth

    opex = add_lists(rd, sga)

    def fs(v):   return _fmt_scaled(v, div)
    def fp(v):   return _fmt_pct_val(v)
    def fg(v):   return _fmt_growth(v)
    def feps(v): return f"${v:.2f}" if v is not None and not pd.isna(v) else "—"

    rows_data = {
        f"Revenue ({unit})":          [fs(v) for v in rev],
        "Revenue Growth (YoY)":        [fg(v) for v in yoy_growth(rev)],
        f"Cost of Revenue ({unit})":   [fs(v) for v in cogs],
        f"Gross Profit ({unit})":      [fs(v) for v in gp],
        "Gross Margin":                [fp(v) for v in margin(gp, rev)],
        f"R&D Expense ({unit})":       [fs(v) for v in rd],
        f"SG&A Expense ({unit})":      [fs(v) for v in sga],
        f"Total OpEx ({unit})":        [fs(v) for v in opex],
        f"Operating Income ({unit})":  [fs(v) for v in op],
        "Operating Margin":            [fp(v) for v in margin(op, rev)],
        f"EBITDA ({unit})":            [fs(v) for v in ebit],
        "EBITDA Margin":               [fp(v) for v in margin(ebit, rev)],
        f"Interest Expense ({unit})":  [fs(v) for v in ie],
        f"Pretax Income ({unit})":     [fs(v) for v in pbt],
        f"Tax ({unit})":               [fs(v) for v in tax],
        f"Net Income ({unit})":        [fs(v) for v in ni],
        "Net Income Growth (YoY)":     [fg(v) for v in yoy_growth(ni)],
        "Net Margin":                  [fp(v) for v in margin(ni, rev)],
        "EPS (Basic)":                 [feps(v) for v in eps_b],
        "EPS (Diluted)":               [feps(v) for v in eps_d],
    }

    out = pd.DataFrame(rows_data, index=col_labels).T
    out.index.name = f"(All $ in {unit})"

    COLORED_ROWS = {
        "Revenue Growth (YoY)", "Net Income Growth (YoY)",
        "Gross Margin", "Operating Margin", "EBITDA Margin", "Net Margin",
    }

    def _cell_style(val, row_label):
        if row_label not in COLORED_ROWS or val == "—":
            return ""
        try:
            num = float(val.replace("%", "").replace("+", "").strip())
            if num > 0:
                return "color: #16a34a; font-weight: 700; background-color: rgba(22,163,74,0.12)"
            elif num < 0:
                return "color: #dc2626; font-weight: 700; background-color: rgba(220,38,38,0.12)"
        except ValueError:
            pass
        return ""

    def style_income(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        for row_label in df.index:
            if row_label in COLORED_ROWS:
                for col in df.columns:
                    styles.loc[row_label, col] = _cell_style(df.loc[row_label, col], row_label)
        return styles

    st.dataframe(out.style.apply(style_income, axis=None), use_container_width=True)

def render_fin_table(df_raw, rows_to_show):
    """Generic table for balance sheet / cash flow with uniform unit."""
    if df_raw is None or df_raw.empty:
        st.info("No data available.")
        return
    available = [r for r in rows_to_show if r in df_raw.index]
    if not available:
        st.info("No data available.")
        return
    div, unit = _detect_scale(df_raw, rows_to_show)
    df = df_raw.loc[available].copy()
    df.columns = [c.strftime("%b '%y") if hasattr(c, "strftime") else str(c) for c in df.columns]
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.map(lambda v: _fmt_scaled(v, div))
    df.index.name = f"(All $ in {unit})"
    st.dataframe(df, use_container_width=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("🗂 Filters")
sectors = ["All"] + sorted(set(p["sector"] for p in PORTFOLIO))
classes = ["All"] + sorted(set(p["class"] for p in PORTFOLIO))
sel_sector = st.sidebar.selectbox("Sector", sectors)
sel_class  = st.sidebar.selectbox("Class",  classes)

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

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown(f"""
<div style="
    background: linear-gradient(135deg, #1c1f2e 0%, #1a1f35 100%);
    border: 1px solid rgba(99,102,241,0.3);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.4);
">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h1 style="
                margin:0; font-size:2rem; font-weight:800;
                background: linear-gradient(90deg, #818cf8, #c084fc, #38bdf8);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            ">📈 Portfolio Dashboard</h1>
            <p style="margin:6px 0 0; color:#7c8db0; font-size:0.85rem;">
                Live market data · Refreshed {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · Prices delayed ~15 min
            </p>
        </div>
        <div style="text-align:right;">
            <span style="
                background: rgba(99,102,241,0.15); color:#a5b4fc;
                padding:6px 14px; border-radius:99px; font-size:0.8rem; font-weight:600;
                border: 1px solid rgba(99,102,241,0.3);
            ">⚡ Live</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

filtered_portfolio = [p for p in PORTFOLIO if p["ticker"] in sel_tickers]
df = fetch_stock_data(filtered_portfolio)

if df.attrs.get("errors"):
    with st.expander("⚠️ Data fetch warnings (click to expand)"):
        for err in df.attrs["errors"]:
            st.caption(err)

null_prices = df["Price"].isna().sum()
if null_prices == len(df):
    st.error("❌ Could not fetch any market data. Yahoo Finance may be rate-limiting this server. Try refreshing in a minute.")
    st.stop()

ticker_name_map = {row["Ticker"]: row["Name"] for _, row in df.iterrows()}
ticker_labels = [f"{t} — {ticker_name_map.get(t, t)}" for t in sel_tickers]
label_to_ticker = {f"{t} — {ticker_name_map.get(t, t)}": t for t in sel_tickers}

# ── Top KPI Cards ─────────────────────────────────────────────────────────────

gainers = df[df["Chg %"] > 0].shape[0]
losers  = df[df["Chg %"] < 0].shape[0]
avg_chg = df["Chg %"].mean()

avg_chg_str  = f"{avg_chg:+.2f}%" if pd.notna(avg_chg) else "—"
avg_chg_color = "#10b981" if pd.notna(avg_chg) and avg_chg >= 0 else "#ef4444"

kpi_html = f"""
<div style="display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:8px;">
    <div style="background:linear-gradient(135deg,#1c1f2e,#1a2744);border:1px solid rgba(99,102,241,0.3);
                border-radius:14px;padding:20px;box-shadow:0 4px 20px rgba(0,0,0,0.3);">
        <div style="color:#7c8db0;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;">Stocks Tracked</div>
        <div style="color:#e6edf3;font-size:2rem;font-weight:800;margin-top:6px;">{len(df)}</div>
        <div style="color:#6366f1;font-size:0.78rem;margin-top:4px;">In your portfolio</div>
    </div>
    <div style="background:linear-gradient(135deg,#0d2818,#0d1f14);border:1px solid rgba(16,185,129,0.35);
                border-radius:14px;padding:20px;box-shadow:0 4px 20px rgba(0,0,0,0.3);">
        <div style="color:#7c8db0;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;">Gainers</div>
        <div style="color:#10b981;font-size:2rem;font-weight:800;margin-top:6px;">{gainers}</div>
        <div style="color:#10b981;font-size:0.78rem;margin-top:4px;">▲ Up today</div>
    </div>
    <div style="background:linear-gradient(135deg,#2a0d0d,#1f0d0d);border:1px solid rgba(239,68,68,0.35);
                border-radius:14px;padding:20px;box-shadow:0 4px 20px rgba(0,0,0,0.3);">
        <div style="color:#7c8db0;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;">Losers</div>
        <div style="color:#ef4444;font-size:2rem;font-weight:800;margin-top:6px;">{losers}</div>
        <div style="color:#ef4444;font-size:0.78rem;margin-top:4px;">▼ Down today</div>
    </div>
    <div style="background:linear-gradient(135deg,#1c1f2e,#1a1f35);border:1px solid rgba(99,102,241,0.3);
                border-radius:14px;padding:20px;box-shadow:0 4px 20px rgba(0,0,0,0.3);">
        <div style="color:#7c8db0;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;">Avg Change</div>
        <div style="color:{avg_chg_color};font-size:2rem;font-weight:800;margin-top:6px;">{avg_chg_str}</div>
        <div style="color:#7c8db0;font-size:0.78rem;margin-top:4px;">Portfolio average</div>
    </div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)

st.markdown("---")

# ── Price Table ───────────────────────────────────────────────────────────────

st.subheader("Stock Overview")
st.caption("Click any row to open detailed analysis below.")

display_df = df.copy()
display_df["Class"]     = display_df["Class"].apply(lambda x: f"{CLASS_COLORS.get(x,'')} {x}")
display_df["Price"]     = display_df["Price"].apply(fmt_price)
display_df["Chg %"]     = display_df["Chg %"].apply(fmt_pct)
display_df["Volume"]    = display_df["Volume"].apply(fmt_vol)
display_df["Mkt Cap"]   = display_df["Mkt Cap"].apply(fmt_large)
display_df["P/E"]       = display_df["P/E"].apply(lambda x: f"{x:.1f}" if x else "—")
display_df["EPS"]       = display_df["EPS"].apply(lambda x: f"${x:.2f}" if x else "—")
display_df["52W High"]  = display_df["52W High"].apply(fmt_price)
display_df["52W Low"]   = display_df["52W Low"].apply(fmt_price)
display_df["Div Yield"] = display_df["Div Yield"].apply(lambda x: f"{x*100:.2f}%" if x else "—")

_raw_chg = df["Chg %"].reset_index(drop=True)

def _style_overview(frame):
    styles = pd.DataFrame("", index=frame.index, columns=frame.columns)
    for i in frame.index:
        chg = _raw_chg.iloc[i] if i < len(_raw_chg) else None
        if chg is None or pd.isna(chg):
            continue
        if chg > 0:
            styles.loc[i, "Chg %"] = "color: #16a34a; font-weight: 700"
        else:
            styles.loc[i, "Chg %"] = "color: #dc2626; font-weight: 700"
    return styles

_overview_cols = ["Ticker", "Name", "Sector", "Class", "Price", "Chg %", "Volume",
                  "Mkt Cap", "P/E", "EPS", "52W High", "52W Low", "Div Yield"]
_styled_overview = display_df[_overview_cols].style.apply(_style_overview, axis=None)

event = st.dataframe(
    _styled_overview,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
)

st.markdown("---")

# ── Stock Detail Section ──────────────────────────────────────────────────────

selected_rows = event.selection.get("rows", []) if event and event.selection else []

if selected_rows:
    row_idx   = selected_rows[0]
    selected  = df.iloc[row_idx]
    ticker    = selected["Ticker"]
    name      = selected["Name"]
    chg       = selected["Chg %"]
    chg_color = "green" if (chg or 0) >= 0 else "red"
    chg_arrow = "▲" if (chg or 0) >= 0 else "▼"

    # Stock header
    h1, h2, h3 = st.columns([2, 1, 2])
    h1.markdown(f"## {name} &nbsp; `{ticker}`", unsafe_allow_html=True)
    h2.markdown(f"### {fmt_price(selected['Price'])}")
    h3.markdown(
        f"<span style='color:{chg_color};font-size:22px;font-weight:600'>"
        f"{chg_arrow} {abs(chg):.2f}%</span>" if chg else "—",
        unsafe_allow_html=True,
    )
    st.caption(f"{selected['Sector']}  ·  {CLASS_COLORS.get(selected['Class'], '')} {selected['Class']}")

    detail = fetch_detail(ticker)
    info   = detail["info"]

    roe             = info.get("returnOnEquity")
    book            = info.get("bookValue")
    beta            = info.get("beta")
    fwd_pe          = info.get("forwardPE")
    revenue_growth  = info.get("revenueGrowth")
    earnings_growth = info.get("earningsGrowth")
    profit_margin   = info.get("profitMargins")
    target_price    = info.get("targetMeanPrice")

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab_summary, tab_chart, tab_fin, tab_peers, tab_dcf, tab_comps, tab_news = st.tabs(["📊 Summary", "📈 Chart", "📋 Financials", "👥 Peers", "💰 DCF", "⚖️ Comps", "📰 News"])

    # ── Summary ───────────────────────────────────────────────────────────────
    with tab_summary:
        st.markdown("#### Key Metrics")

        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        r1c1.metric("Market Cap",  fmt_large(selected["Mkt Cap"]))
        r1c2.metric("P/E (TTM)",   f"{selected['P/E']:.1f}" if selected["P/E"] else "—")
        r1c3.metric("Fwd P/E",     f"{fwd_pe:.1f}" if fwd_pe else "—")
        r1c4.metric("EPS (TTM)",   f"${selected['EPS']:.2f}" if selected["EPS"] else "—")

        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        r2c1.metric("Book Value",  f"${book:.2f}" if book else "—")
        r2c2.metric("ROE",         f"{roe*100:.1f}%" if roe else "—")
        r2c3.metric("Div Yield",   f"{selected['Div Yield']*100:.2f}%" if selected["Div Yield"] else "—")
        r2c4.metric("Beta",        f"{beta:.2f}" if beta else "—")

        r3c1, r3c2, r3c3, r3c4 = st.columns(4)
        r3c1.metric("Profit Margin",   f"{profit_margin*100:.1f}%" if profit_margin else "—")
        r3c2.metric("Revenue Growth",  f"{revenue_growth*100:.1f}%" if revenue_growth else "—")
        r3c3.metric("Earnings Growth", f"{earnings_growth*100:.1f}%" if earnings_growth else "—")
        r3c4.metric("Analyst Target",  fmt_price(target_price))

        st.markdown("#### 52-Week Range")
        lo, hi, px = selected["52W Low"], selected["52W High"], selected["Price"]
        if lo and hi and px:
            pct_pos = (px - lo) / (hi - lo) * 100
            cl, cb, ch = st.columns([1, 5, 1])
            cl.caption(fmt_price(lo))
            cb.progress(min(max(pct_pos / 100, 0.0), 1.0))
            ch.caption(fmt_price(hi))
            st.caption(f"Current price is **{pct_pos:.1f}%** above 52-week low")

        st.markdown("#### Insights")
        insights = []
        if chg and chg > 2:
            insights.append(("✅", f"Strong day — up {chg:.2f}% today"))
        if chg and chg < -2:
            insights.append(("⚠️", f"Down {abs(chg):.2f}% today — watch for momentum shift"))
        if roe and roe > 0.15:
            insights.append(("✅", f"Healthy ROE of {roe*100:.1f}%"))
        elif roe and roe < 0.05:
            insights.append(("⚠️", f"Low ROE of {roe*100:.1f}% — capital efficiency concern"))
        if profit_margin and profit_margin > 0.20:
            insights.append(("✅", f"Strong profit margin of {profit_margin*100:.1f}%"))
        if lo and hi and px:
            if px / hi > 0.95:
                insights.append(("📌", "Trading near 52-week high"))
            elif px / hi < 0.70:
                insights.append(("📌", "Well below 52-week high — potential value or weakness"))
        if selected["Div Yield"]:
            insights.append(("💰", f"Dividend yield of {selected['Div Yield']*100:.2f}%"))
        if target_price and px and target_price > px:
            upside = (target_price - px) / px * 100
            insights.append(("🎯", f"Analyst target {fmt_price(target_price)} — {upside:.1f}% upside"))
        if not insights:
            insights.append(("ℹ️", "No notable signals at this time."))
        for icon, msg in insights:
            st.markdown(f"{icon} {msg}")

    # ── Chart ─────────────────────────────────────────────────────────────────
    with tab_chart:
        period_map = {
            "1 Week": "5d", "1 Month": "1mo", "3 Months": "3mo",
            "6 Months": "6mo", "1 Year": "1y", "2 Years": "2y",
        }
        period_label = st.radio("Period", list(period_map.keys()), index=2, horizontal=True)
        hist = get_history(ticker, period_map[period_label])

        if not hist.empty:
            st.line_chart(hist["Close"], use_container_width=True)
            mc1, mc2, mc3, mc4 = st.columns(4)
            mc1.metric("Period High",  fmt_price(hist["Close"].max()))
            mc2.metric("Period Low",   fmt_price(hist["Close"].min()))
            mc3.metric("Period Open",  fmt_price(hist["Close"].iloc[0]))
            mc4.metric("Period Close", fmt_price(hist["Close"].iloc[-1]))
        else:
            st.info("No chart data available.")

    # ── Financials ────────────────────────────────────────────────────────────
    with tab_fin:
        balance_rows = [
            "Total Assets", "Total Liabilities Net Minority Interest",
            "Stockholders Equity", "Cash And Cash Equivalents",
            "Total Debt", "Net Debt",
        ]
        cashflow_rows = [
            "Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow",
            "Free Cash Flow", "Capital Expenditure",
        ]

        ft1, ft2, ft3, ft4 = st.tabs(["Quarterly P&L", "Annual P&L", "Balance Sheet", "Cash Flow"])

        with ft1:
            st.markdown("**Quarterly Income Statement**")
            render_income_table(detail["quarterly_financials"])

        with ft2:
            st.markdown("**Annual Income Statement**")
            render_income_table(detail["financials"])

        with ft3:
            st.markdown("**Annual Balance Sheet**")
            render_fin_table(detail["balance_sheet"], balance_rows)

        with ft4:
            st.markdown("**Annual Cash Flow**")
            render_fin_table(detail["cashflow"], cashflow_rows)

    # ── News ─────────────────────────────────────────────────────────────────
    # ── Peers ─────────────────────────────────────────────────────────────────
    with tab_peers:
        sector = selected["Sector"]
        peer_list = [p["ticker"] for p in PORTFOLIO if p["sector"] == sector]

        st.markdown(f"**Sector peers — {sector}** ({len(peer_list)} stocks in portfolio)")

        with st.spinner("Loading peer data..."):
            peers_df = fetch_peers_data(peer_list)

        if not peers_df.empty:
            # Build display with color styling
            pdisplay = peers_df.copy()
            raw_chg_peers  = pdisplay["Chg %"].copy()
            raw_pe_peers   = pdisplay["P/E"].copy()

            pdisplay["Price"]      = pdisplay["Price"].apply(fmt_price)
            pdisplay["Chg %"]      = pdisplay["Chg %"].apply(fmt_pct)
            pdisplay["Mkt Cap"]    = pdisplay["Mkt Cap"].apply(fmt_large)
            pdisplay["Revenue"]    = pdisplay["Revenue"].apply(fmt_large)
            pdisplay["Net Income"] = pdisplay["Net Income"].apply(fmt_large)
            pdisplay["P/E"]        = pdisplay["P/E"].apply(lambda x: f"{x:.1f}" if pd.notna(x) and x else "—")
            pdisplay["P/B"]        = pdisplay["P/B"].apply(lambda x: f"{x:.1f}" if pd.notna(x) and x else "—")
            pdisplay["EV/EBITDA"]  = pdisplay["EV/EBITDA"].apply(lambda x: f"{x:.1f}" if pd.notna(x) and x else "—")
            pdisplay["Net Margin"] = pdisplay["Net Margin"].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) and x else "—")
            pdisplay["Div Yield"]  = pdisplay["Div Yield"].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) and x else "—")
            pdisplay["52W High"]   = pdisplay["52W High"].apply(fmt_price)
            pdisplay["52W Low"]    = pdisplay["52W Low"].apply(fmt_price)
            pdisplay["ROE"]        = pdisplay["ROE"].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) and x else "—")

            peer_cols = ["Ticker", "Name", "Price", "Chg %", "Mkt Cap",
                         "P/E", "P/B", "EV/EBITDA", "Revenue", "Net Income",
                         "Net Margin", "ROE", "Div Yield", "52W High", "52W Low"]
            sub = pdisplay[peer_cols].reset_index(drop=True)

            def _style_peers(frame):
                styles = pd.DataFrame("", index=frame.index, columns=frame.columns)
                # Highlight selected stock row
                for i, row in frame.iterrows():
                    if row["Ticker"] == ticker:
                        for col in frame.columns:
                            styles.loc[i, col] = "background-color: rgba(59,130,246,0.18); font-weight: 700"
                # Color Chg % column
                for i in frame.index:
                    chg_val = raw_chg_peers.iloc[i] if i < len(raw_chg_peers) else None
                    if chg_val is not None and pd.notna(chg_val):
                        base = "background-color: rgba(59,130,246,0.18); " if frame.loc[i, "Ticker"] == ticker else ""
                        if chg_val > 0:
                            styles.loc[i, "Chg %"] = base + "color: #16a34a; font-weight: 700"
                        else:
                            styles.loc[i, "Chg %"] = base + "color: #dc2626; font-weight: 700"
                return styles

            st.dataframe(
                sub.style.apply(_style_peers, axis=None),
                use_container_width=True,
                hide_index=True,
            )

            # Quick KPI comparison bar charts
            st.markdown("#### P/E Comparison")
            pe_data = peers_df[["Ticker", "P/E"]].dropna().set_index("Ticker")
            if not pe_data.empty:
                st.bar_chart(pe_data)

            st.markdown("#### Market Cap Comparison")
            mc_data = peers_df[["Ticker", "Mkt Cap"]].dropna().set_index("Ticker")
            if not mc_data.empty:
                st.bar_chart(mc_data)
        else:
            st.info("No peer data available.")

    # ── DCF Valuation ──────────────────────────────────────────────────────────
    with tab_dcf:
        cf = detail["cashflow"]
        fins = detail["financials"]
        shares = info.get("sharesOutstanding")
        total_cash = info.get("totalCash")
        total_debt = info.get("totalDebt")
        current_price = selected["Price"]

        # Extract FCF history
        fcf_history = []
        if cf is not None and not cf.empty and "Free Cash Flow" in cf.index:
            raw_fcf = pd.to_numeric(cf.loc["Free Cash Flow"], errors="coerce").dropna()
            fcf_history = list(raw_fcf.values)

        # Estimate historical FCF growth (CAGR over available years)
        def calc_cagr(values):
            vals = [v for v in values if v and not pd.isna(v) and v > 0]
            if len(vals) >= 2:
                return ((vals[0] / vals[-1]) ** (1 / (len(vals) - 1)) - 1) * 100
            return 10.0

        hist_growth = calc_cagr(fcf_history)

        # Estimate WACC from beta
        beta_val = info.get("beta") or 1.0
        rf = 4.5       # risk-free rate %
        erp = 5.5      # equity risk premium %
        cost_of_equity = rf + beta_val * erp
        default_wacc = round(min(max(cost_of_equity, 7.0), 20.0), 1)

        base_fcf = fcf_history[0] if fcf_history else None

        if base_fcf is None or base_fcf <= 0 or not shares:
            st.warning("Insufficient free cash flow data for DCF. This stock may have negative FCF.")
            if fcf_history:
                st.caption(f"Available FCF history: {[fmt_large(v) for v in fcf_history]}")
        else:
            net_cash = (total_cash or 0) - (total_debt or 0)

            st.markdown("#### Assumptions")
            st.caption("Adjust the inputs below and the DCF recalculates instantly.")

            col_a, col_b = st.columns(2)
            with col_a:
                growth_rate = st.slider(
                    "FCF Growth Rate (Years 1–10) %",
                    min_value=0.0, max_value=40.0,
                    value=round(min(max(hist_growth, 0.0), 30.0), 1),
                    step=0.5, key=f"dcf_growth_{ticker}",
                    help="Annual growth rate applied to Free Cash Flow for the projection period."
                )
                terminal_growth = st.slider(
                    "Terminal Growth Rate %",
                    min_value=0.0, max_value=5.0,
                    value=2.5, step=0.1, key=f"dcf_tgr_{ticker}",
                    help="Long-term perpetual growth rate after projection period. Typically ~2–3% (GDP growth)."
                )
            with col_b:
                discount_rate = st.slider(
                    "Discount Rate / WACC %",
                    min_value=5.0, max_value=25.0,
                    value=default_wacc,
                    step=0.5, key=f"dcf_wacc_{ticker}",
                    help="Weighted Average Cost of Capital. Pre-filled using CAPM: Rf + Beta × ERP."
                )
                projection_years = st.slider(
                    "Projection Period (Years)",
                    min_value=5, max_value=15,
                    value=10, step=1, key=f"dcf_years_{ticker}",
                    help="Number of years to project FCF before applying terminal value."
                )

            st.markdown("---")

            # ── Run DCF ──────────────────────────────────────────────────────
            g  = growth_rate    / 100
            r  = discount_rate  / 100
            tg = terminal_growth / 100

            projected_fcfs, pv_fcfs = [], []
            fcf = base_fcf
            for yr in range(1, projection_years + 1):
                fcf = fcf * (1 + g)
                pv  = fcf / (1 + r) ** yr
                projected_fcfs.append(fcf)
                pv_fcfs.append(pv)

            terminal_fcf   = projected_fcfs[-1] * (1 + tg)
            terminal_value = terminal_fcf / (r - tg) if r > tg else 0
            pv_terminal    = terminal_value / (1 + r) ** projection_years

            sum_pv_fcf   = sum(pv_fcfs)
            enterprise_v = sum_pv_fcf + pv_terminal
            equity_value = enterprise_v + net_cash
            intrinsic    = equity_value / shares

            upside = (intrinsic - current_price) / current_price * 100 if current_price else 0
            upside_color = "#16a34a" if upside >= 0 else "#dc2626"
            verdict = "UNDERVALUED" if upside >= 10 else ("OVERVALUED" if upside <= -10 else "FAIRLY VALUED")

            # Result cards
            st.markdown("#### DCF Result")
            r1, r2, r3, r4 = st.columns(4)
            r1.metric("Intrinsic Value",  fmt_price(intrinsic))
            r2.metric("Current Price",    fmt_price(current_price))
            r3.metric("Upside / Downside", f"{upside:+.1f}%")
            r4.markdown(
                f"<div style='padding:12px;border-radius:8px;background:rgba({"22,163,74" if upside>=10 else ("220,38,38" if upside<=-10 else "100,116,139")},0.15);text-align:center'>"
                f"<span style='font-size:18px;font-weight:700;color:{upside_color}'>{verdict}</span></div>",
                unsafe_allow_html=True,
            )

            st.markdown("---")

            # Assumptions summary
            st.markdown("#### Assumptions Used")
            a1, a2, a3, a4, a5 = st.columns(5)
            a1.metric("Base FCF",         fmt_large(base_fcf))
            a2.metric("FCF Growth",       f"{growth_rate:.1f}%")
            a3.metric("Discount Rate",    f"{discount_rate:.1f}%")
            a4.metric("Terminal Growth",  f"{terminal_growth:.1f}%")
            a5.metric("Net Cash / Debt",  fmt_large(net_cash))

            st.caption(
                f"WACC estimated via CAPM: Rf {rf}% + Beta {beta_val:.2f} × ERP {erp}% = {cost_of_equity:.1f}%. "
                f"Historical FCF CAGR: {hist_growth:.1f}%. "
                f"Terminal value accounts for {pv_terminal/enterprise_v*100:.0f}% of enterprise value."
            )

            st.markdown("---")

            # Projection table
            st.markdown("#### FCF Projection Table")
            col_years  = [f"Year {i}" for i in range(1, projection_years + 1)] + ["Terminal Value"]
            col_fcf    = [fmt_large(v) for v in projected_fcfs] + [fmt_large(terminal_value)]
            col_pv     = [fmt_large(v) for v in pv_fcfs]        + [fmt_large(pv_terminal)]
            col_cum_pv = []
            running = 0
            for v in pv_fcfs:
                running += v
                col_cum_pv.append(fmt_large(running))
            col_cum_pv.append(fmt_large(running + pv_terminal))

            proj_df = pd.DataFrame({
                "Period":           col_years,
                "Projected FCF":    col_fcf,
                "Present Value":    col_pv,
                "Cumulative PV":    col_cum_pv,
            })

            def style_proj(frame):
                styles = pd.DataFrame("", index=frame.index, columns=frame.columns)
                last = len(frame) - 1
                for col in frame.columns:
                    styles.loc[last, col] = "background-color: rgba(59,130,246,0.15); font-weight:700"
                return styles

            st.dataframe(
                proj_df.style.apply(style_proj, axis=None),
                use_container_width=True,
                hide_index=True,
            )

    # ── Comparable Valuation ───────────────────────────────────────────────────
    with tab_comps:
        industry_key = info.get("industryKey")
        industry_name = info.get("industry", "Unknown Industry")
        price    = selected["Price"]
        eps      = selected["EPS"]
        shares   = info.get("sharesOutstanding")
        book_val = info.get("bookValue")
        rev_total  = info.get("totalRevenue")
        ebitda_val = info.get("ebitda")

        rev_ps    = (rev_total  / shares) if rev_total  and shares else None
        ebitda_ps = (ebitda_val / shares) if ebitda_val and shares else None
        net_debt_ps = (((info.get("totalDebt") or 0) - (info.get("totalCash") or 0)) / shares) if shares else 0

        if not industry_key:
            st.warning("Industry data not available for this stock.")
        else:
            with st.spinner(f"Loading {industry_name} industry peers from market..."):
                comps_df = fetch_industry_peers(industry_key, ticker)

            if comps_df.empty:
                st.warning("Could not load industry peers.")
            else:
                st.markdown(f"#### Industry Peers — {industry_name}")
                st.caption(f"{len(comps_df)} peers fetched from market · Average multiples used for implied valuation")

                # ── Peer multiples table ──────────────────────────────────────
                md = comps_df[["Ticker", "Name", "Price", "Mkt Cap", "P/E", "P/B", "P/S", "EV/EBITDA", "Net Margin"]].copy()
                md["Price"]      = md["Price"].apply(fmt_price)
                md["Mkt Cap"]    = md["Mkt Cap"].apply(fmt_large)
                md["P/E"]        = md["P/E"].apply(lambda x: f"{x:.1f}x" if pd.notna(x) and x else "—")
                md["P/B"]        = md["P/B"].apply(lambda x: f"{x:.1f}x" if pd.notna(x) and x else "—")
                md["P/S"]        = md["P/S"].apply(lambda x: f"{x:.1f}x" if pd.notna(x) and x else "—")
                md["EV/EBITDA"]  = md["EV/EBITDA"].apply(lambda x: f"{x:.1f}x" if pd.notna(x) and x else "—")
                md["Net Margin"] = md["Net Margin"].apply(lambda x: f"{x*100:.1f}%" if pd.notna(x) and x else "—")

                # Add average row
                avg_row = {
                    "Ticker": "— AVG —", "Name": "Industry Average",
                    "Price":  "—",
                    "Mkt Cap": "—",
                    "P/E":    f"{comps_df['P/E'].dropna().mean():.1f}x",
                    "P/B":    f"{comps_df['P/B'].dropna().mean():.1f}x",
                    "P/S":    f"{comps_df['P/S'].dropna().mean():.1f}x",
                    "EV/EBITDA": f"{comps_df['EV/EBITDA'].dropna().mean():.1f}x",
                    "Net Margin": f"{comps_df['Net Margin'].dropna().mean()*100:.1f}%",
                }
                md_with_avg = pd.concat([md, pd.DataFrame([avg_row])], ignore_index=True)

                def _style_comps_mkt(frame):
                    styles = pd.DataFrame("", index=frame.index, columns=frame.columns)
                    last = len(frame) - 1
                    for col in frame.columns:
                        styles.loc[last, col] = "background-color: rgba(234,179,8,0.18); font-weight:700"
                    return styles

                st.dataframe(
                    md_with_avg.style.apply(_style_comps_mkt, axis=None),
                    use_container_width=True, hide_index=True,
                )

                st.markdown("---")

                # ── Average multiples ─────────────────────────────────────────
                avg_pe   = comps_df["P/E"].dropna().mean()
                avg_pb   = comps_df["P/B"].dropna().mean()
                avg_ps   = comps_df["P/S"].dropna().mean()
                avg_eveb = comps_df["EV/EBITDA"].dropna().mean()

                # ── Implied prices ────────────────────────────────────────────
                implied = {}

                if avg_pe and eps and eps > 0:
                    implied["P/E"] = {
                        "multiple": avg_pe,
                        "implied":  avg_pe * eps,
                        "label":    f"Avg industry P/E {avg_pe:.1f}x  ×  EPS ${eps:.2f}",
                    }
                if avg_pb and book_val and book_val > 0:
                    implied["P/B"] = {
                        "multiple": avg_pb,
                        "implied":  avg_pb * book_val,
                        "label":    f"Avg industry P/B {avg_pb:.1f}x  ×  Book Value/Share ${book_val:.2f}",
                    }
                if avg_ps and rev_ps and rev_ps > 0:
                    implied["P/S"] = {
                        "multiple": avg_ps,
                        "implied":  avg_ps * rev_ps,
                        "label":    f"Avg industry P/S {avg_ps:.1f}x  ×  Revenue/Share ${rev_ps:.2f}",
                    }
                if avg_eveb and ebitda_ps and ebitda_ps > 0:
                    implied["EV/EBITDA"] = {
                        "multiple": avg_eveb,
                        "implied":  avg_eveb * ebitda_ps - net_debt_ps,
                        "label":    f"Avg industry EV/EBITDA {avg_eveb:.1f}x  ×  EBITDA/Share ${ebitda_ps:.2f}  −  Net Debt/Share ${net_debt_ps:.2f}",
                    }

                st.markdown("#### Implied Share Price")
                st.caption("Average industry multiple × this stock's per-share metric")

                if not implied:
                    st.warning("Not enough data to compute implied prices.")
                else:
                    # KPI cards
                    card_cols = st.columns(len(implied) + 1)
                    card_cols[0].metric("Current Price", fmt_price(price))
                    for i, (method, vals) in enumerate(implied.items(), 1):
                        imp   = vals["implied"]
                        delta = (imp - price) / price * 100 if price else 0
                        card_cols[i].metric(
                            f"Implied ({method})",
                            fmt_price(imp),
                            delta=f"{delta:+.1f}%",
                        )

                    # Bar chart
                    st.markdown("#### Visual Comparison")
                    methods    = ["Current"] + list(implied.keys())
                    imp_prices = [price]    + [v["implied"] for v in implied.values()]
                    bar_colors = ["#3b82f6"] + [
                        "#16a34a" if v["implied"] >= price else "#dc2626"
                        for v in implied.values()
                    ]
                    fig_bar = go.Figure(go.Bar(
                        x=methods, y=imp_prices,
                        marker_color=bar_colors,
                        text=[fmt_price(p) for p in imp_prices],
                        textposition="outside",
                    ))
                    fig_bar.add_hline(
                        y=price, line_dash="dash", line_color="#3b82f6",
                        annotation_text="Current Price", annotation_position="top right",
                    )
                    fig_bar.update_layout(
                        yaxis_title="Price (USD)", height=380,
                        margin=dict(t=40, b=10, l=0, r=0),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        yaxis=dict(gridcolor="rgba(128,128,128,0.15)"),
                    )
                    st.plotly_chart(fig_bar, use_container_width=True)

                    # Formula breakdown
                    st.markdown("#### How Each Price Was Calculated")
                    for method, vals in implied.items():
                        st.markdown(f"- **{method}**: {vals['label']}  →  **{fmt_price(vals['implied'])}**")

    with tab_news:
        stock_news = fetch_news([{"ticker": ticker}])
        if stock_news:
            for n in stock_news:
                pub = n["Published"]
                if isinstance(pub, (int, float)):
                    pub = datetime.utcfromtimestamp(pub).strftime("%Y-%m-%d %H:%M")
                if n["URL"]:
                    st.markdown(
                        f"[{n['Headline']}]({n['URL']}) "
                        f"<span style='color:gray;font-size:12px'>{pub}</span>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f"{n['Headline']} "
                        f"<span style='color:gray;font-size:12px'>{pub}</span>",
                        unsafe_allow_html=True,
                    )
                st.markdown("---")
        else:
            st.info("No news found.")

else:
    st.info("👆 Click any row in the table above to open detailed analysis.")

st.markdown("---")

# ── Heatmap Tab ───────────────────────────────────────────────────────────────

st.subheader("📊 Portfolio Heatmap")
st.caption("Block size = Market Cap · Color = % Change today")

hm_df = df.dropna(subset=["Chg %", "Mkt Cap"]).copy()

if not hm_df.empty:
    hm_df["Chg %"] = pd.to_numeric(hm_df["Chg %"], errors="coerce")
    hm_df["Mkt Cap"] = pd.to_numeric(hm_df["Mkt Cap"], errors="coerce")
    hm_df = hm_df.dropna(subset=["Chg %", "Mkt Cap"])

    hm_df["label"] = hm_df.apply(
        lambda r: f"{r['Ticker']}<br>${r['Price']:,.2f}<br>{'+' if r['Chg %'] >= 0 else ''}{r['Chg %']:.2f}%", axis=1
    )

    fig = go.Figure(go.Treemap(
        labels=hm_df["label"],
        parents=[""] * len(hm_df),
        values=hm_df["Mkt Cap"],
        customdata=hm_df[["Ticker", "Chg %", "Price", "Mkt Cap"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Change: %{customdata[1]:.2f}%<br>"
            "Price: $%{customdata[2]:.2f}<br>"
            "Mkt Cap: %{customdata[3]:,.0f}<extra></extra>"
        ),
        marker=dict(
            colors=hm_df["Chg %"],
            colorscale=[
                [0.0,  "#7f1d1d"],
                [0.2,  "#dc2626"],
                [0.4,  "#f87171"],
                [0.5,  "#1e293b"],
                [0.6,  "#4ade80"],
                [0.8,  "#16a34a"],
                [1.0,  "#14532d"],
            ],
            cmid=0,
            showscale=True,
            colorbar=dict(title="Chg %", ticksuffix="%"),
        ),
        textfont=dict(size=14, color="white"),
        tiling=dict(packing="squarify"),
    ))

    fig.update_layout(
        margin=dict(t=10, l=0, r=0, b=0),
        height=500,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Not enough data to render heatmap.")

st.markdown("---")

# ── Portfolio News Feed ───────────────────────────────────────────────────────

st.subheader("Latest News (All Holdings)")
news = fetch_news(filtered_portfolio)

if news:
    news_label  = st.selectbox("Filter by stock", ["All"] + ticker_labels, key="news_filter")
    news_ticker = None if news_label == "All" else label_to_ticker[news_label]
    shown = [n for n in news if news_ticker is None or n["Ticker"] == news_ticker]
    for n in shown[:20]:
        pub = n["Published"]
        if isinstance(pub, (int, float)):
            pub = datetime.utcfromtimestamp(pub).strftime("%Y-%m-%d %H:%M")
        if n["URL"]:
            st.markdown(
                f"**{n['Ticker']}** — [{n['Headline']}]({n['URL']}) "
                f"<span style='color:gray;font-size:12px'>{pub}</span>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"**{n['Ticker']}** — {n['Headline']} "
                f"<span style='color:gray;font-size:12px'>{pub}</span>",
                unsafe_allow_html=True,
            )
else:
    st.info("No news found.")
