import yfinance as yf
import numpy as np
import pandas as pd

def load_brazil_stocks(ticker_x, ticker_y, period="5y", interval="1d"):
    X = yf.download(ticker_x, period=period, interval=interval)
    Y = yf.download(ticker_y, period=period, interval=interval)

    if X.empty:
        raise ValueError(f"Sem dados para {ticker_x}")
    if Y.empty:
        raise ValueError(f"Sem dados para {ticker_y}")

    # garante vetor 1D
    px = X["Close"].to_numpy(dtype=float).reshape(-1)
    py = Y["Close"].to_numpy(dtype=float).reshape(-1)

    T = min(len(px), len(py))
    return px[:T], py[:T]