# analyze_results.py
"""
Análise de resultados das trades reais (trades_log.csv).

Lê o arquivo gerado pelo realtime_bot.py e calcula:
- Retorno total (%)
- Sharpe "por trade"
- Max drawdown (%)
- Winrate
- Nº de trades
- Distribuição por motivo de saída (TP / SL / TIME / EOD)
- Retornos por ano
- Comparação com um baseline muito simples de buy-and-hold

Gera:
- Gráfico de equity
- Gráfico de drawdown
- Histograma de retornos por trade
- Atualiza (ou cria) um arquivo RESULTS.md com um resumo em Markdown
"""

import os
import datetime as dt

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


TRADES_FILE = "trades_log.csv"
RESULTS_MD = "RESULTS.md"


def load_trades(path: str = TRADES_FILE) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"[ERRO] Arquivo {path} não encontrado.")

    df = pd.read_csv(
        path,
        parse_dates=["entry_date", "exit_date"],
        dayfirst=False,  # datas estão no formato ISO yyyy-mm-dd
    )

    required_cols = [
        "entry_date", "exit_date",
        "entry_price", "exit_price",
        "pnl", "pnl_pct",
        "exit_reason", "equity_after_trade",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"[ERRO] Colunas faltando em {path}: {missing}")

    # Ordena por exit_date pra garantir ordem temporal
    df = df.sort_values("exit_date").reset_index(drop=True)
    return df


def infer_initial_equity(df: pd.DataFrame) -> float:
    """
    Recupera o capital inicial usando a 1ª trade:
    equity_after_trade_0 = equity_0 + pnl_0 - fees_0
    Aqui ignoramos fees (que já estão embutidas em pnl), então:
    equity_0 ~ equity_after_0 - pnl_0
    """
    equity0 = df.loc[0, "equity_after_trade"] - df.loc[0, "pnl"]
    return float(equity0)


def compute_equity_metrics(df: pd.DataFrame):
    equity0 = infer_initial_equity(df)
    equity = df["equity_after_trade"].astype(float)

    final_equity = equity.iloc[-1]
    total_return_pct = (final_equity / equity0 - 1.0) * 100.0

    # Max Drawdown
    running_max = equity.cummax()
    drawdown = (equity / running_max - 1.0) * 100.0
    max_dd_pct = float(drawdown.min())

    return {
        "equity0": equity0,
        "final_equity": final_equity,
        "total_return_pct": total_return_pct,
        "max_dd_pct": max_dd_pct,
        "drawdown_series": drawdown,
        "equity_series": equity,
    }


def compute_trade_stats(df: pd.DataFrame):
    n_trades = len(df)
    pnl_pct = df["pnl_pct"].astype(float) / 100.0  # em fração

    mean_ret = pnl_pct.mean()
    std_ret = pnl_pct.std(ddof=1)

    if std_ret > 0:
        sharpe_per_trade = (mean_ret / std_ret) * np.sqrt(n_trades)
    else:
        sharpe_per_trade = np.nan

    winrate = (df["pnl"] > 0).mean() * 100.0
    lossrate = (df["pnl"] < 0).mean() * 100.0
    flat_rate = (df["pnl"] == 0).mean() * 100.0

    # Stats por motivo de saída
    by_reason = (
        df.groupby("exit_reason")["pnl_pct"]
        .agg(["count", "mean", "median", "min", "max"])
        .sort_index()
    )

    # Stats por ano (com base na exit_date)
    df["year"] = df["exit_date"].dt.year
    by_year = (
        df.groupby("year")["pnl_pct"]
        .agg(["count", "mean", "sum"])
        .rename(columns={"count": "n_trades", "mean": "ret_medio_pct", "sum": "ret_total_pct"})
    )

    return {
        "n_trades": n_trades,
        "mean_ret_pct": mean_ret * 100.0,
        "std_ret_pct": std_ret * 100.0,
        "sharpe_per_trade": sharpe_per_trade,
        "winrate": winrate,
        "lossrate": lossrate,
        "flat_rate": flat_rate,
        "by_reason": by_reason,
        "by_year": by_year,
    }


def compute_buy_and_hold_baseline(df: pd.DataFrame, equity0: float):
    """
    Baseline bem simples:
    - Compra 1x a VALE3.SA no entry_price da PRIMEIRA trade
    - Segura até o exit_price da ÚLTIMA trade
    - Retorno = (preço_final / preço_inicial - 1)
    É uma aproximação grosseira, mas serve de baseline didático.
    """
    first_price = float(df.loc[0, "entry_price"])
    last_price = float(df.loc[len(df) - 1, "exit_price"])

    bh_ret = (last_price / first_price - 1.0) * 100.0
    bh_final_equity = equity0 * (1.0 + bh_ret / 100.0)

    return {
        "bh_ret_pct": bh_ret,
        "bh_final_equity": bh_final_equity,
    }


def plot_equity_vs_baseline(equity: pd.Series, equity0: float, bh_final_equity: float):
    n = len(equity)
    # linha "reta" do buy and hold entre equity0 e bh_final_equity
    bh_curve = np.linspace(equity0, bh_final_equity, n)

    plt.figure(figsize=(10, 5))
    plt.plot(equity.values, label="Estratégia GA")
    plt.plot(bh_curve, linestyle="--", label="Buy & Hold (aprox.)")
    plt.title("Equity da estratégia vs Buy & Hold")
    plt.xlabel("Trade #")
    plt.ylabel("Equity")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_drawdown(drawdown: pd.Series):
    plt.figure(figsize=(10, 4))
    plt.plot(drawdown.values)
    plt.title("Drawdown (%) ao longo das trades")
    plt.xlabel("Trade #")
    plt.ylabel("Drawdown (%)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def plot_return_hist(df: pd.DataFrame):
    pnl_pct = df["pnl_pct"].astype(float)

    plt.figure(figsize=(8, 4))
    plt.hist(pnl_pct, bins=30, edgecolor="black")
    plt.title("Histograma de retornos por trade")
    plt.xlabel("Retorno por trade (%)")
    plt.ylabel("Frequência")
    plt.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.show()


def write_results_md(equity_stats, trade_stats, bh_stats, df: pd.DataFrame, path: str = RESULTS_MD):
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append(f"# Resultados da Estratégia Evolutiva\n")
    lines.append(f"_Última atualização: {now}_\n")
    lines.append("---\n")

    lines.append("## Resumo geral\n")
    lines.append(f"- Capital inicial estimado: **R$ {equity_stats['equity0']:.2f}**")
    lines.append(f"- Capital final: **R$ {equity_stats['final_equity']:.2f}**")
    lines.append(f"- Retorno total: **{equity_stats['total_return_pct']:.2f}%**")
    lines.append(f"- Max Drawdown: **{equity_stats['max_dd_pct']:.2f}%**")
    lines.append("")

    lines.append("## Métricas por trade\n")
    lines.append(f"- Nº de trades: **{trade_stats['n_trades']}**")
    lines.append(f"- Retorno médio por trade: **{trade_stats['mean_ret_pct']:.3f}%**")
    lines.append(f"- Volatilidade dos retornos (desvio padrão): **{trade_stats['std_ret_pct']:.3f}%**")
    lines.append(f"- Sharpe (por trade): **{trade_stats['sharpe_per_trade']:.3f}**")
    lines.append(f"- Winrate: **{trade_stats['winrate']:.2f}%**")
    lines.append(f"- Lossrate: **{trade_stats['lossrate']:.2f}%**")
    lines.append(f"- Trades ~0 (flat): **{trade_stats['flat_rate']:.2f}%**")
    lines.append("")

    lines.append("## Baseline: Buy & Hold aproximado de Y\n")
    lines.append(f"- Retorno Buy & Hold (aprox.): **{bh_stats['bh_ret_pct']:.2f}%**")
    lines.append(f"- Equity final Buy & Hold (aprox.): **R$ {bh_stats['bh_final_equity']:.2f}**")
    lines.append("")

    lines.append("## Estatísticas por motivo de saída\n")
    lines.append("```")
    lines.append(trade_stats["by_reason"].to_string())
    lines.append("```")
    lines.append("")

    lines.append("## Estatísticas por ano (baseado em exit_date)\n")
    lines.append("```")
    lines.append(trade_stats["by_year"].to_string())
    lines.append("```")
    lines.append("")

    # Escreve (sobrescrevendo) o RESULTS.md
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[INFO] RESULTADOS salvos em {path}")


def main():
    print(f"Lendo trades de {TRADES_FILE} ...")
    df = load_trades(TRADES_FILE)

    if df.empty:
        print("[ERRO] trades_log.csv está vazio.")
        return

    equity_stats = compute_equity_metrics(df)
    trade_stats = compute_trade_stats(df)
    bh_stats = compute_buy_and_hold_baseline(df, equity_stats["equity0"])

    # Prints no console
    print("\n=== RESUMO GERAL ===")
    print(f"Capital inicial estimado: R$ {equity_stats['equity0']:.2f}")
    print(f"Capital final:            R$ {equity_stats['final_equity']:.2f}")
    print(f"Retorno total:           {equity_stats['total_return_pct']:.2f}%")
    print(f"Max Drawdown:            {equity_stats['max_dd_pct']:.2f}%")

    print("\n=== MÉTRICAS POR TRADE ===")
    print(f"Nº trades:                      {trade_stats['n_trades']}")
    print(f"Retorno médio por trade:       {trade_stats['mean_ret_pct']:.3f}%")
    print(f"Volatilidade (desvio padrão):  {trade_stats['std_ret_pct']:.3f}%")
    print(f"Sharpe (por trade):            {trade_stats['sharpe_per_trade']:.3f}")
    print(f"Winrate:                       {trade_stats['winrate']:.2f}%")
    print(f"Lossrate:                      {trade_stats['lossrate']:.2f}%")
    print(f"Trades ~0:                     {trade_stats['flat_rate']:.2f}%")

    print("\n=== BASELINE: BUY & HOLD DE Y (APROX.) ===")
    print(f"Retorno Buy & Hold (aprox.):   {bh_stats['bh_ret_pct']:.2f}%")
    print(f"Equity final Buy & Hold (apx): R$ {bh_stats['bh_final_equity']:.2f}")

    print("\n=== POR MOTIVO DE SAÍDA ===")
    print(trade_stats["by_reason"])

    print("\n=== POR ANO (exit_date) ===")
    print(trade_stats["by_year"])

    # Gráficos
    plot_equity_vs_baseline(
        equity_stats["equity_series"],
        equity_stats["equity0"],
        bh_stats["bh_final_equity"],
    )
    plot_drawdown(equity_stats["drawdown_series"])
    plot_return_hist(df)

    # RESULTS.md
    write_results_md(equity_stats, trade_stats, bh_stats, df, RESULTS_MD)


if __name__ == "__main__":
    main()
