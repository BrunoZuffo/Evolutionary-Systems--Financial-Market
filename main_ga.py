#SEMPRE:
#./.venv/Scripts/Activate.ps1
#pip install -requirements.txt -> só quando mudar os requirements.txt

#DIA D:
#    python realtime_signal.py -> após fechamento do mercado ( gera o sinal se deve comprar ou fazer nada )

#DIA D+1:
#    python realtime_bot.py -> testa com toda a série da b3 pra rodar o backtest com o best 
#    python analyze_signals.py -> analisa os sinais gerados pelo realtime_signal.py e ve se ele foi condizente com as expectativas ou não

# main_ga.py
import numpy as np
import matplotlib.pyplot as plt

from data.loaders import load_brazil_stocks
from evolution.ga import run_ga

if __name__ == "__main__":
    np.random.seed(42)

    # ==========================
    # 1) Carrega 10 anos diários
    # ==========================
    Px, Py = load_brazil_stocks(
        "PETR4.SA",
        "VALE3.SA",
        period="10y",   # 10 anos
        interval="1d",  # candles diários
    )

    # ==========================
    # 2) Roda GA UMA vez (sem walk-forward)
    # ==========================
    best, history = run_ga(
        Px, Py,
        population_size=150,
        generations=60,
        fee=0.0005,
        seed=42,
    )

    print("\n=== MELHOR INDIVÍDUO (10 anos inteiros) ===")
    print("Genoma:", best["genome"])
    print("Fitness:", best["fitness"])
    print("Retorno total (%):", best["total_return_pct"])
    print("Max Drawdown (%):", best["mdd_pct"])
    print("Calmar:", best["calmar"])  # RETORNO ANUALIZADO
    print("Sortino:", best["sortino"]) # retorno ajustado pelas perdas ruins
    print("N trades:", best["n_trades"])
    print("Retornos por janela (%):", best["window_returns"])

    # ==========================
    # 3) Gráfico – fitness por geração
    # ==========================
    plt.figure(figsize=(10, 4))
    plt.plot(history, marker="o", linewidth=1)
    plt.title("Melhor fitness por geração - PETR4.SA x VALE3.SA")
    plt.xlabel("Geração")
    plt.ylabel("Fitness")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # ==========================
    # 4) Gráfico – equity do melhor indivíduo
    # ==========================
    equity = best["result"]["equity_curve"]

    plt.figure(figsize=(10, 4))
    plt.plot(equity, linewidth=1)
    plt.title("Equity - Melhor indivíduo (10 anos)")
    plt.xlabel("Tempo (candles) - dias")
    plt.ylabel("Equity")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
