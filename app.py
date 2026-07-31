import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime

st.set_page_config(page_title="GARUDA V2", layout="wide")

st.title("GARUDA V2 - Live F&O Scanner")

st.write("Market Time:", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))

FO_STOCKS = [
    "RELIANCE.NS",
    "SBIN.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS"
]

rows = []

for symbol in FO_STOCKS:
    try:
        df = yf.download(symbol, period="1d", interval="5m", progress=False)

        if df.empty:
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = float(df["Close"].iloc[-1])
        high = float(df["High"].max())
        low = float(df["Low"].min())
        volume = int(df["Volume"].iloc[-1])

        signal = "BUY" if close > (high + low) / 2 else "NO TRADE"

        rows.append({
            "Stock": symbol.replace(".NS", ""),
            "Close": round(close, 2),
            "High": round(high, 2),
            "Low": round(low, 2),
            "Volume": volume,
            "Signal": signal
        })

    except Exception:
        pass

df_result = pd.DataFrame(rows)

st.subheader("Live Signals")

if not df_result.empty:
    st.dataframe(df_result, use_container_width=True)
else:
    st.warning("No data available.")
