import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import timedelta

SIGNALS_CSV = "signals_log.csv"


def main():
    # === 1) Carregar sinais ===
    df = pd.read_csv(SIGNALS_CSV)
    print("Colunas em signals_log.csv:", list(df.columns))

    if df.empty:
        print("Nenhum sinal encontrado em signals_log.csv.")
        return

    # Converter datas
    df["date"] = pd.to_datetime(df["date"])

    # Descobrir o ticker Y (deve ser sempre o mesmo)
    ticker_y = df["ticker_y"].iloc[0]

    # === 2) Buscar histórico de preços de Y (VALE3.SA) ===
    start_date = df["date"].min()
    # pegamos uns dias a mais no final para garantir o próximo candle
    end_date = df["date"].max() + timedelta(days=10)

    print(f"\nBaixando histórico de {ticker_y} de {start_date.date()} até {end_date.date()}...")
    data_y = yf.download(ticker_y, start=start_date, end=end_date)

    if data_y.empty:
        print("Falha ao baixar dados de Y para análise de sinais.")
        return

    # Índice por data (somente a coluna 'Close')
    # Mantém só a coluna Close
    data_y = data_y[["Close"]].copy()
    data_y.index = data_y.index.tz_localize(None)  # tira timezone se vier

    # Garante série 1D, mesmo que venha como (N,1)
    price_map = pd.Series(
        data_y["Close"].to_numpy().reshape(-1),  # força 1D
        index=data_y.index
    )

    # Usa o mapa data -> preço
    df["next_date"] = df["date"] + pd.Timedelta(days=1)
    df["next_price_y"] = df["next_date"].map(price_map)

    # Alguns dias podem não ter próximo preço (feriado/fim de semana)
    valid_mask = df["next_price_y"].notna()
    df_valid = df[valid_mask].copy()

    if df_valid.empty:
        print("Nenhum sinal com próximo dia disponível para análise.")
        return

    df_valid["ret_pct"] = (df_valid["next_price_y"] / df_valid["last_price_y"] - 1.0) * 100.0

    # === 4) Filtrar apenas BUY_Y ===
    buys = df_valid[df_valid["signal"] == "BUY_Y"].copy()

    print("\n==== TRADES BUY_Y (saindo no próximo dia logado) ====")
    if buys.empty:
        print("Nenhum BUY_Y válido encontrado.")
    else:
        print(buys[["date", "last_price_y", "next_price_y", "ret_pct"]])

        print("\nN trades:", len(buys))
        print("Retorno médio por trade (%):", buys["ret_pct"].mean())
        print("Retorno mediano por trade (%):", buys["ret_pct"].median())
        print("Retorno mínimo (%):", buys["ret_pct"].min())
        print("Retorno máximo (%):", buys["ret_pct"].max())
        print("% trades positivos:", 100.0 * (buys["ret_pct"] > 0).mean(), "%")

    # === 5) GRÁFICO: preço de Y + pontos de BUY ===
    plt.figure(figsize=(12, 6))

    # Série de preços completa de Y
    plt.plot(data_y.index, data_y["Close"], label=f"Preço {ticker_y}", alpha=0.7)

    # Pontos onde o bot mandou BUY_Y
    if not buys.empty:
        plt.scatter(
            buys["date"],
            buys["last_price_y"],
            marker="^",
            s=80,
            label="Sinal BUY_Y (último preço)",
        )

        # Opcional: marcar o próximo dia (resultado)
        plt.scatter(
            buys["next_date"],
            buys["next_price_y"],
            marker="o",
            s=60,
            label="Preço no dia seguinte",
        )

    plt.title(f"Sinais BUY_Y vs Preço de {ticker_y}")
    plt.xlabel("Data")
    plt.ylabel("Preço de fechamento")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    # Salvar figura
    out_file = "signals_vs_price.png"
    plt.savefig(out_file, dpi=150)
    print(f"\n[INFO] Gráfico salvo em {out_file}")

    # Mostrar na tela
    plt.show()


if __name__ == "__main__":
    main()
