# analyze_signals.py
#
# Analisa a sequência de sinais em signals_log.csv
# e mede o desempenho de BUY_Y com saída no próximo dia logado.

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

CSV_PATH = "signals_log.csv"


def main():
    # 1) Carrega CSV
    df = pd.read_csv(CSV_PATH)
    print("Colunas em signals_log.csv:", list(df.columns))

    # Checagem básica
    required = ["date", "signal", "last_price_y"]
    for col in required:
        if col not in df.columns:
            print(f"[ERRO] Coluna obrigatória '{col}' não encontrada.")
            return

    # Garante ordenação temporal
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # 2) Cria coluna com o "próximo preço" Y
    # *** IMPORTANTE: shift feito no DF COMPLETO, não só nos BUY_Y ***
    df["next_price_y"] = df["last_price_y"].shift(-1)

    # 3) Filtra apenas as entradas de compra
    buys = df[df["signal"] == "BUY_Y"].copy()

    if buys.empty:
        print("\n[INFO] Nenhum sinal BUY_Y encontrado ainda.")
        print("Rode o realtime_signal.py em mais dias até gerar alguns BUYs.")
        return

    # Remove BUYs que não têm próxima linha no CSV (sem como medir retorno)
    buys = buys[buys["next_price_y"].notna()].copy()
    if buys.empty:
        print(
            "\n[INFO] Há BUY_Y, mas nenhum tem linha seguinte no CSV "
            "para estimar retorno. Logue pelo menos mais um dia."
        )
        return

    # 4) Retorno simples: entra em last_price_y, sai em next_price_y
    buys["ret_pct"] = (
        (buys["next_price_y"] - buys["last_price_y"])
        / buys["last_price_y"]
        * 100.0
    )

    print("\n==== TRADES BUY_Y (saindo no próximo dia logado) ====")
    print(
        buys[["date", "last_price_y", "next_price_y", "ret_pct"]]
        .to_string(index=False)
    )

    # 5) Estatísticas básicas
    n_trades = len(buys)
    mean_ret = buys["ret_pct"].mean()
    median_ret = buys["ret_pct"].median()
    min_ret = buys["ret_pct"].min()
    max_ret = buys["ret_pct"].max()
    pos_pct = (buys["ret_pct"] > 0).mean() * 100.0

    print(f"\nN trades: {n_trades}")
    print(f"Retorno médio por trade (%): {mean_ret:.2f}")
    print(f"Retorno mediano por trade (%): {median_ret:.2f}")
    print(f"Retorno mínimo (%): {min_ret:.2f}")
    print(f"Retorno máximo (%): {max_ret:.2f}")
    print(f"% trades positivos: {pos_pct:.1f}%")

    # 6) Curva de equity (capital normalizado)
    equity = (1.0 + buys["ret_pct"] / 100.0).cumprod()

    plt.figure(figsize=(8, 4))
    plt.plot(range(1, len(equity) + 1), equity, marker="o")
    plt.title("Equity (capital normalizado) - sequência de BUY_Y")
    plt.xlabel("Trade #")
    plt.ylabel("Equity (1.0 = capital inicial)")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # 7) Histograma de retornos
    plt.figure(figsize=(8, 4))
    plt.hist(buys["ret_pct"], bins=20, edgecolor="black")
    plt.title("Histograma de retornos por trade (BUY_Y)")
    plt.xlabel("Retorno (%)")
    plt.ylabel("Frequência")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
