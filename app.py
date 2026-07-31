import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

st.set_page_config(page_title="GARUDA V2 Pro", layout="wide")

st_autorefresh(interval=15 * 1000, key="garuda_refresh")

IST = pytz.timezone("Asia/Kolkata")

FNO_STOCKS = [
    "RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK","SBIN","LT","AXISBANK","KOTAKBANK","ITC",
    "HINDUNILVR","BAJFINANCE","BAJAJFINSV","MARUTI","M&M","TATAMOTORS","SUNPHARMA","DRREDDY",
    "CIPLA","DIVISLAB","APOLLOHOSP","ADANIENT","ADANIPORTS","POWERGRID","NTPC","ONGC","COALINDIA",
    "ULTRACEMCO","GRASIM","SHREECEM","JSWSTEEL","TATASTEEL","HINDALCO","VEDL","SAIL","JINDALSTEL",
    "BHARTIARTL","WIPRO","HCLTECH","TECHM","PERSISTENT","LTIM","NAUKRI","OFSS","DIXON","TRENT",
    "ASIANPAINT","NESTLEIND","BRITANNIA","TATACONSUM","DABUR","GODREJCP","COLPAL","UBL","MCDOWELL-N",
    "PIDILITIND","AMBUJACEM","ACC","INDIGO","SIEMENS","ABB","BHEL","CGPOWER","CUMMINSIND","BEL",
    "HAL","RVNL","IRCTC","PNB","BANKBARODA","CANBK","UNIONBANK","INDUSINDBK","AUBANK","FEDERALBNK",
    "IDFCFIRSTB","YESBANK","RBLBANK","BANDHANBNK","LICHSGFIN","PFC","RECLTD","SBICARD","CHOLAFIN",
    "SHRIRAMFIN","MUTHOOTFIN","MANAPPURAM","PAGEIND","DMART","LODHA","DLF","OBEROIRLTY","GODREJPROP",
    "PHOENIXLTD","TORNTPHARM","LUPIN","AUROPHARMA","ZYDUSLIFE","ALKEM","BIOCON","GLENMARK",
    "MOTHERSON","BOSCHLTD","ASHOKLEY","EICHERMOT","HEROMOTOCO","TVSMOTOR","BHARATFORG","ESCORTS",
    "EXIDEIND","BALKRISIND","MRF","APOLLOTYRE","JKCEMENT","RAMCOCEM","INDUSTOWER","TATAPOWER",
    "ADANIGREEN","ADANIPOWER","GAIL","IOC","BPCL","HINDPETRO","PETRONET","ATGL","IGL","MGL",
    "NHPC","SJVN","TORNTPOWER","SUPREMEIND","POLYCAB","KEI","HAVELLS","VOLTAS","WHIRLPOOL","BLUESTARCO",
    "CONCOR","DELHIVERY","ZOMATO","PAYTM","NYKAA","INDIAMART","IRFC","NMDC","HINDZINC","NATIONALUM",
    "ABCAPITAL","ABFRL","ADANIENSOL","AARTIIND","ALKYLAMINE","ANGELONE","ASTRAL","BATAINDIA","BERGEPAINT",
    "CANFINHOME","COROMANDEL","DEEPAKNTR","GMRINFRA","GNFC","GUJGASLTD","IDBI","INDHOTEL","JSWENERGY",
    "LAURUSLABS","LICI","LINDEINDIA","LTTS","MAXHEALTH","MCX","MPHASIS","NAVINFLUOR","PIIND","SRF",
    "TATACHEM","TATACOMM","UPL","VEDANTA","VBL","ZEEL","SONACOMS","KPITTECH","COFORGE","PEL"
]

SECTOR_MAP = {
    "NIFTY BANK":["HDFCBANK","ICICIBANK","SBIN","AXISBANK","KOTAKBANK","INDUSINDBK","BANKBARODA","PNB","CANBK"],
    "NIFTY IT":["TCS","INFY","HCLTECH","WIPRO","TECHM","LTIM","PERSISTENT","COFORGE","MPHASIS"],
    "NIFTY AUTO":["MARUTI","M&M","TATAMOTORS","EICHERMOT","HEROMOTOCO","TVSMOTOR","ASHOKLEY"],
    "NIFTY PHARMA":["SUNPHARMA","DRREDDY","CIPLA","DIVISLAB","LUPIN","TORNTPHARM","ZYDUSLIFE"],
    "NIFTY METAL":["TATASTEEL","JSWSTEEL","HINDALCO","VEDL","SAIL","NMDC","NATIONALUM"],
    "NIFTY FMCG":["ITC","HINDUNILVR","NESTLEIND","BRITANNIA","TATACONSUM","DABUR","COLPAL","VBL"],
    "NIFTY REALTY":["DLF","LODHA","OBEROIRLTY","GODREJPROP","PHOENIXLTD"],
    "NIFTY ENERGY":["RELIANCE","ONGC","NTPC","POWERGRID","GAIL","IOC","BPCL","HINDPETRO"],
    "NIFTY INFRA":["LT","ADANIPORTS","RVNL","IRFC","CONCOR","GMRINFRA"]
}

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=30)
def fetch(symbol):
    try:
        df = yf.download(symbol + ".NS", period="5d", interval="5m", progress=False, auto_adjust=True)
        if df.empty:
            return None
        c = df["Close"].squeeze()
        v = df["Volume"].squeeze()
        h = df["High"].squeeze()
        l = df["Low"].squeeze()
        tp = (h + l + c) / 3
        vwap = (tp * v).cumsum() / v.cumsum()
        vsma = v.rolling(20).mean()
        spike = v / vsma
        out = {
            "Symbol": symbol,
            "Price": float(c.iloc[-1]),
            "VWAP": float(vwap.iloc[-1]),
            "RSI": float(rsi(c).iloc[-1]),
            "Volume Spike": float(spike.iloc[-1]) if pd.notna(spike.iloc[-1]) else 0,
            "Day High": float(h.max()),
            "Day Low": float(l.min()),
            "Change %": float((c.iloc[-1] / c.iloc[0] - 1) * 100)
        }
        if out["Price"] > out["VWAP"] and out["RSI"] > 60 and out["Volume Spike"] >= 1.5:
            out["Signal"] = "BUY"
        elif out["Price"] < out["VWAP"] and out["RSI"] < 40 and out["Volume Spike"] >= 1.5:
            out["Signal"] = "SELL"
        else:
            out["Signal"] = "NO TRADE"
        out["BTST/STBT"] = "BTST" if out["Signal"] == "BUY" else ("STBT" if out["Signal"] == "SELL" else "")
        return out
    except Exception:
        return None

st.title("GARUDA V2 Pro")

results = []
with ThreadPoolExecutor(max_workers=20) as ex:
    futures = [ex.submit(fetch, s) for s in FNO_STOCKS]
    for f in as_completed(futures):
        r = f.result()
        if r:
            results.append(r)

df = pd.DataFrame(results)

now = datetime.now(IST)
buy = df[df["Signal"]=="BUY"] if not df.empty else pd.DataFrame()
sell = df[df["Signal"]=="SELL"] if not df.empty else pd.DataFrame()

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Market Time", now.strftime("%H:%M:%S"))
c2.metric("Last Refresh", now.strftime("%H:%M:%S"))
c3.metric("Scanned", len(df))
c4.metric("BUY", len(buy))
c5.metric("SELL", len(sell))

st.subheader("Live BUY Signals")
st.dataframe(buy, use_container_width=True)

st.subheader("Live SELL Signals")
st.dataframe(sell, use_container_width=True)

st.subheader("BTST / STBT Candidates")
st.dataframe(df[df["BTST/STBT"]!=""], use_container_width=True)

st.subheader("Sector Strength")
sector_rows = []
for sec, syms in SECTOR_MAP.items():
    d = df[df["Symbol"].isin(syms)]
    if len(d):
        sector_rows.append({"Sector":sec,"Avg Change %":round(d["Change %"].mean(),2),"BUY":int((d["Signal"]=="BUY").sum()),"SELL":int((d["Signal"]=="SELL").sum())})
st.dataframe(pd.DataFrame(sector_rows).sort_values("Avg Change %", ascending=False), use_container_width=True)

st.subheader("All Scanned Stocks")
st.dataframe(df.sort_values(["Signal","Volume Spike"], ascending=[True,False]), use_container_width=True)
