# analyze_signals.py
#
# Analisa o desempenho REAL dos sinais gravados em signals_log.csv.
# Considera apenas sinais BUY_Y e simula:
#   - entrada na próxima abertura (próximo pregão >= data+1)
#   - saída depois de max_hold dias de pregão
#
# Calcula retorno por trade, equity curve, drawdown, CAGR e plota gráficos.

import os
from datetime import timedelta

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt


def load_price_series(ticker: str, start_date, end_date) -> pd.Series:
    """
    Baixa preços diários de 'ticker' entre start_date e end_date (inclusive),
    e retorna um pandas.Series com Close/AdjClose, já lidando com MultiIndex.
    """
    df = yf.download(
        ticker,
        start=start_date,
        end=end_date + timedelta(days=1),
        interval="1d",
        auto_adjust=False,
        progress=False,
    )

    if df is None or df.empty:
        raise RuntimeError(f"ERRO: yfinance retornou DataFrame vazio para {ticker}.")

    cols = df.columns
    if isinstance(cols, pd.MultiIndex):
        level0 = cols.get_level_values(0)
        series = None
        if "Close" in level0:
            close_df = df["Close"]
            if isinstance(close_df, pd.DataFrame):
                series = close_df.iloc[:, 0]
            else:
                series = close_df
        elif "Adj Close" in level0:
            adj_df = df["Adj Close"]
            if isinstance(adj_df, pd.DataFrame):
                series = adj_df.iloc[:, 0]
            else:
                series = adj_df
        if series is None:
            raise RuntimeError(
                f"ERRO: Nenhuma coluna 'Close' ou 'Adj Close' em MultiIndex para {ticker}.\n"
                f"Colunas: {cols}"
            )
    else:
        if "Close" in cols:
            series = df["Close"]
        elif "Adj Close" in cols:
            series = df["Adj Close"]
        else:
            raise RuntimeError(
                f"ERRO: Nenhuma coluna 'Close' ou 'Adj Close' encontrada para {ticker}.\n"
                f"Colunas: {list(cols)}"
            )

    series = series.dropna()
    if series.empty:
        raise RuntimeError(f"ERRO: Série de preços vazia para {ticker} após dropna.")

    return series


def next_trading_index(price_series: pd.Series, date):
    idx = price_series.index
    pos = idx.searchsorted(pd.to_datetime(date))
    if pos >= len(idx):
        return None
    return pos


def main():
    log_path = "signals_log.csv"
    if not os.path.exists(log_path):
        print(f"[ERRO] Arquivo {log_path} não encontrado. Rode primeiro realtime_signal.py.")
        return

    df = pd.read_csv(log_path)
    print("Colunas em signals_log.csv:", list(df.columns))

    required_cols = [
        "date", "ticker_y", "max_hold", "signal"
    ]
    for c in required_cols:
        if c not in df.columns:
            print(f"[ERRO] Coluna obrigatória '{c}' não encontrada em signals_log.csv.")
            return

    df["date"] = pd.to_datetime(df["date"])
    df["signal"] = df["signal"].astype(str).str.upper().str.strip()

    # Considera apenas BUY_Y
    df_buy = df[df["signal"] == "BUY_Y"].copy()

    if df_buy.empty:
        print("\n[INFO] Nenhum sinal BUY_Y encontrado ainda.")
        print("Rode o realtime_signal.py em mais dias até gerar alguns BUYs.")
        return

    tickers_y = df_buy["ticker_y"].unique()
    if len(tickers_y) != 1:
        print("[AVISO] Há mais de um ticker_y. Vou usar só o primeiro.")
    ticker_y = tickers_y[0]

    print(f"\nAnalisando retornos reais para BUY_Y em {ticker_y}.")

    min_date = df_buy["date"].min()
    max_date = df_buy["date"].max()
    max_hold_max = int(df_buy["max_hold"].max())

    start_prices = min_date - timedelta(days=5)
    end_prices = max_date + timedelta(days=max_hold_max + 5)

    print(f"Baixando preços de {ticker_y} de {start_prices.date()} até {end_prices.date()}...")
    price_series = load_price_series(ticker_y, start_prices, end_prices)

    results = []

    for _, row in df_buy.iterrows():
        signal_date = row["date"]
        max_hold = int(row["max_hold"])

        entry_search_date = signal_date + timedelta(days=1)
        entry_pos = next_trading_index(price_series, entry_search_date)
        if entry_pos is None:
            continue

        exit_pos = min(entry_pos + max_hold, len(price_series) - 1)

        entry_date = price_series.index[entry_pos]
        exit_date = price_series.index[exit_pos]
        entry_price = float(price_series.iloc[entry_pos])
        exit_price = float(price_series.iloc[exit_pos])
        ret_pct = (exit_price / entry_price - 1.0) * 100.0

        results.append({
            "signal_date": signal_date.date().isoformat(),
            "entry_date": entry_date.date().isoformat(),
            "exit_date": exit_date.date().isoformat(),
            "entry_price": entry_price,
            "exit_price": exit_price,
            "max_hold_days": max_hold,
            "realized_return_pct": ret_pct,
        })

    if not results:
        print("[INFO] Nenhum sinal pôde ser avaliado (sem dados suficientes de preço).")
        return

    res_df = pd.DataFrame(results)

    # ---------- Estatísticas ----------
    n_trades = len(res_df)
    avg_ret = res_df["realized_return_pct"].mean()
    med_ret = res_df["realized_return_pct"].median()
    win_rate = (res_df["realized_return_pct"] > 0).mean() * 100.0
    best = res_df["realized_return_pct"].max()
    worst = res_df["realized_return_pct"].min()

    # Equity curve: capital inicial 1.0, 100% por trade em sequência
    equity = [1.0]
    for r in res_df["realized_return_pct"]:
        equity.append(equity[-1] * (1.0 + r / 100.0))
    equity = np.array(equity[1:])  # tira o primeiro dummy

    # Drawdown
    peaks = np.maximum.accumulate(equity)
    drawdowns = (equity / peaks - 1.0) * 100.0
    max_dd = drawdowns.min()

    # CAGR aproximado
    first_entry = pd.to_datetime(res_df["entry_date"].iloc[0])
    last_exit = pd.to_datetime(res_df["exit_date"].iloc[-1])
    total_years = (last_exit - first_entry).days / 365.0
    if total_years > 0:
        cagr = (equity[-1]) ** (1.0 / total_years) - 1.0
    else:
        cagr = np.nan

    print("\n===== ANÁLISE DOS SINAIS BUY_Y =====")
    print(f"Nº de trades avaliados: {n_trades}")
    print(f"Retorno médio por trade: {avg_ret:.2f}%")
    print(f"Retorno mediano por trade: {med_ret:.2f}%")
    print(f"Win rate: {win_rate:.1f}%")
    print(f"Melhor trade: {best:.2f}%")
    print(f"Pior trade: {worst:.2f}%")
    print(f"Max Drawdown (equity): {max_dd:.2f}%")
    if not np.isnan(cagr):
        print(f"CAGR aproximado: {cagr*100:.2f}% ao ano")
    else:
        print("CAGR aproximado: N/A (período muito curto)")

    print("\nPrimeiros 10 trades:")
    print(res_df.head(10).to_string(index=False))

    out_path = "signals_realized.csv"
    res_df.to_csv(out_path, index=False)
    print(f"\n[INFO] Resultados detalhados salvos em {out_path}.")

    # ---------- Gráficos ----------
    plt.figure(figsize=(10, 4))
    plt.plot(equity, marker="o")
    plt.title("Equity (capital normalizado) - sequência de BUY_Y")
    plt.xlabel("Trade #")
    plt.ylabel("Equity (1.0 = capital inicial)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(8, 4))
    plt.hist(res_df["realized_return_pct"], bins=20, edgecolor="black")
    plt.title("Histograma de retornos por trade (BUY_Y)")
    plt.xlabel("Retorno (%)")
    plt.ylabel("Frequência")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
