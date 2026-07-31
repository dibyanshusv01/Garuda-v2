import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="GARUDA V2", layout="wide")

st.title("🚀 GARUDA V2 - Live F&O Scanner")

st.write("Market Time:", datetime.now().strftime("%d-%m-%Y %H:%M:%S"))

stocks = [
    "RELIANCE.NS",
    "SBIN.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS"
]

results = []

for ticker in stocks:
    try:
        df = yf.download(ticker, period="1d", interval="5m", progress=False)

        if df.empty:
            continue

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        close = round(df["Close"].iloc[-1], 2)
        high = round(df["High"].max(), 2)
        low = round(df["Low"].min(), 2)
        volume = int(df["Volume"].iloc[-1])

        signal = "BUY" if close > (high + low) / 2 else "NO TRADE"

        results.append({
            "Stock": ticker.replace(".NS", ""),
            "Close": close,
            "High": high,
            "Low": low,
            "Volume": volume,
            "Signal": signal,
        })

    except Exception:
        pass

df_result = pd.DataFrame(results)

st.subheader("📊 Live Signals")

if not df_result.empty:
    st.dataframe(df_result, use_container_width=True)
else:
    st.warning("No data available.")
