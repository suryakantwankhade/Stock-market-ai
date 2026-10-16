import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="A-STOCK AI ENGINE",
    page_icon="📈",
    layout="wide"
)

st.title("📈 A-STOCK AI ENGINE v1.0")
st.caption("AI-Powered Stock Market Analysis")

ticker = st.text_input(
    "Enter Stock Symbol",
    value="RELIANCE.NS"
).strip().upper()

period = st.selectbox(
    "Analysis Period",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3
)

if st.button("🔍 Analyze Stock"):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty:
            st.error("Stock data not available. Check the symbol.")
            st.stop()

        df = df.dropna().copy()

        df["SMA20"] = df["Close"].rolling(20).mean()
        df["SMA50"] = df["Close"].rolling(50).mean()

        delta = df["Close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(
            alpha=1/14, min_periods=14, adjust=False
        ).mean()

        avg_loss = loss.ewm(
            alpha=1/14, min_periods=14, adjust=False
        ).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        df["RSI"] = 100 - (100 / (1 + rs))

        df["EMA12"] = df["Close"].ewm(
            span=12, adjust=False
        ).mean()

        df["EMA26"] = df["Close"].ewm(
            span=26, adjust=False
        ).mean()

        df["MACD"] = df["EMA12"] - df["EMA26"]
        df["Signal"] = df["MACD"].ewm(
            span=9, adjust=False
        ).mean()

        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest

        st.subheader(f"📊 Analysis: {ticker}")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Latest Close",
            f"₹{latest['Close']:.2f}"
        )

        change = latest["Close"] - previous["Close"]
        col2.metric(
            "Price Change",
            f"₹{change:.2f}",
            f"{change / previous['Close'] * 100:.2f}%"
            if previous["Close"] else None
        )

        col3.metric(
            "RSI (14)",
            f"{latest['RSI']:.2f}"
            if pd.notna(latest["RSI"]) else "N/A"
        )

        col4.metric(
            "SMA 20",
            f"₹{latest['SMA20']:.2f}"
            if pd.notna(latest["SMA20"]) else "N/A"
        )

        st.subheader("📈 Price Chart")

        chart_data = df[["Close", "SMA20", "SMA50"]]
        st.line_chart(chart_data)

        st.subheader("🧠 Technical Analysis")

        score = 0

        if latest["Close"] > latest["SMA20"]:
            score += 1
        else:
            score -= 1

        if latest["SMA20"] > latest["SMA50"]:
            score += 1
        else:
            score -= 1

        if latest["MACD"] > latest["Signal"]:
            score += 1
        else:
            score -= 1

        if latest["RSI"] < 30:
            st.info("RSI: Oversold zone")
        elif latest["RSI"] > 70:
            st.warning("RSI: Overbought zone")
        else:
            st.info("RSI: Between 30 and 70")

        if score >= 2:
            st.success("Positive technical signals")
        elif score <= -2:
            st.error("Negative technical signals")
        else:
            st.warning("Mixed technical signals")

        st.write("Technical Score:", score, "/ 3")
        st.caption(
            "These are rule-based indicators, not a guaranteed "
            "prediction or personalized investment advice."
        )

        st.subheader("🏢 Fundamental Data")

        try:
            info = stock.info

            fields = {
                "Company": "longName",
                "Sector": "sector",
                "P/E Ratio": "trailingPE",
                "ROE": "returnOnEquity",
                "Profit Margin": "profitMargins",
                "Debt/Equity": "debtToEquity",
                "Market Cap": "marketCap",
                "Revenue Growth": "revenueGrowth"
            }

            rows = []

            for label, key in fields.items():
                value = info.get(key)

                if value is None:
                    value = "Not available"
                elif key in [
                    "returnOnEquity",
                    "profitMargins",
                    "revenueGrowth"
                ]:
                    value = f"{value * 100:.2f}%"
                elif key == "marketCap":
                    value = f"₹{value:,.0f}"
                elif isinstance(value, (int, float)):
                    value = round(value, 2)

                rows.append({
                    "Metric": label,
                    "Value": value
                })

            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True
            )

        except Exception:
            st.warning("Fundamental data is currently unavailable.")

        st.subheader("📋 Recent Market Data")
        st.dataframe(
            df.tail(10).round(2),
            use_container_width=True
        )

    except Exception as e:
        st.error(f"Analysis failed: {e}")

st.divider()
st.caption("A-STOCK AI ENGINE | Educational analysis tool")
