# realtime_bot.py
"""
Robô diário "quase em tempo real" usando o best_genome.json.

Fluxo:
- Lê best_genome.json (gerado pelo main_walkforward.py).
- Baixa histórico recente de PETR4.SA (X) e VALE3.SA (Y).
- Roda o backtest_lead_lag com o genoma atual até o último dia disponível.
- Imprime um resumo no terminal (equity final, retorno, nº de trades).
- Salva TODAS as trades simuladas em trades_log.csv (sobrescreve a cada execução).

Observação importante:
- Isto ainda é um "paper bot": ele recalcula o histórico inteiro até hoje,
  não mantém estado incremental entre dias. Para os próximos ~10 dias de teste,
  isso é excelente pra validar o comportamento real da estratégia.
"""

import json
import csv
import os
from datetime import datetime

import numpy as np
import yfinance as yf

from core.leadlag import backtest_lead_lag


def load_best_genome(path="best_genome.json"):
    with open(path, "r") as f:
        genome = json.load(f)
    return genome


def load_prices_with_dates(ticker, period="10y", interval="1d"):
    """
    Baixa preços e retorna (prices, dates).
    Funciona tanto com colunas simples quanto com MultiIndex (Price x Ticker),
    que é o formato que você está recebendo no df.head().
    """

    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=False,  # evita surpresas com colunas
        progress=False,
    )

    if df is None or df.empty:
        raise RuntimeError(
            f"ERRO: Yahoo Finance retornou DataFrame vazio para {ticker}."
        )

    # Se as colunas forem MultiIndex (como no seu caso):
    #   nível 0: tipo de preço (Close, High, Low, Open, Volume)
    #   nível 1: ticker (PETR4.SA, VALE3.SA)
    cols = df.columns

    import pandas as pd

    # Caso MultiIndex
    if isinstance(cols, pd.MultiIndex):
        level0 = cols.get_level_values(0)

        series = None

        # tenta pegar 'Close' primeiro
        if "Close" in level0:
            close_df = df["Close"]  # isso vira um DataFrame com 1 coluna (ticker)
            # pega a primeira coluna (ex.: PETR4.SA)
            if isinstance(close_df, pd.DataFrame):
                series = close_df.iloc[:, 0]
            else:
                series = close_df

        # se não achar, tenta 'Adj Close'
        elif "Adj Close" in level0:
            adj_df = df["Adj Close"]
            if isinstance(adj_df, pd.DataFrame):
                series = adj_df.iloc[:, 0]
            else:
                series = adj_df

        if series is None:
            raise RuntimeError(
                f"ERRO: Nenhuma coluna 'Close' ou 'Adj Close' encontrada num MultiIndex para {ticker}.\n"
                f"Colunas disponíveis: {cols}"
            )

    # Caso colunas simples (não MultiIndex)
    else:
        if "Close" in cols:
            series = df["Close"]
        elif "Adj Close" in cols:
            series = df["Adj Close"]
        else:
            raise RuntimeError(
                f"ERRO: Nenhuma coluna de preço ('Close' ou 'Adj Close') encontrada para {ticker}.\n"
                f"Colunas disponíveis: {cols.tolist()}"
            )

    # limpa NaN e transforma em vetor 1D
    series = series.dropna()
    prices = series.to_numpy(dtype=float).reshape(-1)
    dates = series.index.to_pydatetime()

    if len(prices) == 0:
        raise RuntimeError(f"ERRO: Após dropna, {ticker} não tem preços válidos.")

    return prices, dates




def save_trades_csv(
    filepath,
    trades,
    dates,
    initial_cash,
    final_equity,
):
    """
    Salva todas as trades em CSV.
    Cada linha = uma trade fechada.
    Sobrescreve o arquivo inteiro a cada execução.
    """
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Cabeçalho
        writer.writerow([
            "entry_date",
            "exit_date",
            "entry_t",
            "exit_t",
            "entry_price",
            "exit_price",
            "size",
            "fee_entry",
            "fee_exit",
            "pnl",
            "pnl_pct",
            "exit_reason",
            "equity_after_trade",
        ])

        equity = initial_cash

        for tr in trades:
            entry_t = tr["entry_t"]
            exit_t = tr.get("exit_t", None)

            entry_date = dates[entry_t].strftime("%Y-%m-%d") if entry_t is not None else ""
            exit_date = dates[exit_t].strftime("%Y-%m-%d") if exit_t is not None else ""

            entry_price = tr["entry_price"]
            exit_price = tr.get("exit_price", np.nan)
            size = tr["size"]
            fee_entry = tr.get("fee_entry", 0.0)
            fee_exit = tr.get("fee_exit", 0.0)
            pnl = tr.get("pnl", 0.0)
            exit_reason = tr.get("exit_reason", "")

            equity += pnl
            cost = entry_price * size if entry_price and size else 0.0
            pnl_pct = (pnl / cost * 100.0) if cost > 0 else 0.0

            writer.writerow([
                entry_date,
                exit_date,
                entry_t,
                exit_t,
                f"{entry_price:.4f}",
                f"{exit_price:.4f}" if not np.isnan(exit_price) else "",
                f"{size:.6f}",
                f"{fee_entry:.4f}",
                f"{fee_exit:.4f}",
                f"{pnl:.4f}",
                f"{pnl_pct:.4f}",
                exit_reason,
                f"{equity:.4f}",
            ])


def main():
    print("=== REALTIME BOT: PETR4.SA (X) x VALE3.SA (Y) ===")

    # 1) Carrega genoma otimizado
    genome = load_best_genome("best_genome.json")
    threshold = float(genome["threshold"])
    tp = float(genome["tp"])
    sl = float(genome["sl"])
    lag = int(genome["lag"])
    max_hold = int(genome["max_hold"])

    print("\nGenoma usado:")
    print(genome)

    # 2) Baixa histórico (por padrão, 10 anos diários)
    Px, dates_x = load_prices_with_dates("PETR4.SA", period="10y", interval="1d")
    Py, dates_y = load_prices_with_dates("VALE3.SA", period="10y", interval="1d")

    # Garante que têm o mesmo tamanho (alinha pela cauda)
    n = min(len(Px), len(Py))
    Px = Px[-n:]
    Py = Py[-n:]
    dates = dates_x[-n:]  # assumindo calendário compatível

    # 3) Roda backtest com o genoma atual
    fee = 0.0005  # mesma taxa usada no GA
    result = backtest_lead_lag(
        Px,
        Py,
        threshold=threshold,
        lag=lag,
        tp=tp,
        sl=sl,
        max_hold=max_hold,
        fee=fee,
    )

    initial_cash = result["initial_cash"]
    final_equity = result["final_equity"]
    total_return_pct = result["total_return_pct"]
    trades = result["trades"]
    equity_curve = result["equity_curve"]

    print("\n=== RESUMO DO BACKTEST ATÉ HOJE ===")
    print(f"Data de hoje (aprox.): {datetime.now().date()}")
    print(f"Capital inicial: {initial_cash:.2f}")
    print(f"Capital final  : {final_equity:.2f}")
    print(f"Retorno total (%): {total_return_pct:.2f}%")
    print(f"Número de trades: {len(trades)}")

    if len(equity_curve) > 0:
        print(f"Equity mais recente (último dia): {float(equity_curve[-1]):.2f}")

    # Mostra últimas 3 trades
    print("\nÚltimas trades (até 3):")
    for tr in trades[-3:]:
        entry_t = tr["entry_t"]
        exit_t = tr.get("exit_t", None)
        entry_date = dates[entry_t].strftime("%Y-%m-%d") if entry_t is not None else "?"
        exit_date = dates[exit_t].strftime("%Y-%m-%d") if exit_t is not None else "?"

        print({
            "entry_date": entry_date,
            "exit_date": exit_date,
            "entry_price": tr["entry_price"],
            "exit_price": tr.get("exit_price", None),
            "pnl": tr.get("pnl", 0.0),
            "exit_reason": tr.get("exit_reason", ""),
        })

    # 4) Salva TODAS as trades no CSV
    trades_csv_path = "trades_log.csv"
    save_trades_csv(
        trades_csv_path,
        trades,
        dates,
        initial_cash,
        final_equity,
    )

    print(f"\n[INFO] Trades salvas em {trades_csv_path}.")
    print("      Cada execução sobrescreve o arquivo com o histórico completo até o dia atual.")
    print("      Use isso para analisar PnL por trade, equity por trade, etc.")


if __name__ == "__main__":
    main()
