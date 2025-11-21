import numpy as np
import matplotlib.pyplot as plt

from evolution.ga import run_ga


if __name__ == "__main__":
    np.random.seed(42)

    T = 1000

    # Séries simuladas. Pode mudar a média para mais/menos tendência.
    Px = 100 + np.cumsum(np.random.normal(0.01, 0.2, size=T))
    Py = 50 + 0.5 * (Px - 100) + np.random.normal(0, 0.5, size=T)

    best, history = run_ga(
        Px, Py,
        population_size=30,
        generations=25,
        elite_frac=0.2,
        mutation_rate=0.3,
        tournament_size=3,
        fee=0.0005,
        seed=42
    )

    print("\n=== MELHOR INDIVÍDUO ===")
    print("Genoma:", best["genome"])
    print("Fitness:", best["fitness"])
    print("Retorno total (%):", best["total_return_pct"])
    print("Max Drawdown (%):", best["mdd_pct"])
    print("Calmar:", best["calmar"])
    print("Sortino:", best["sortino"])
    print("N trades:", best["n_trades"])
    print("Retornos por janela (%):", best["window_returns"])

    # Fitness por geração
    plt.figure(figsize=(10, 5))
    plt.plot(history)
    plt.title("Melhor fitness por geração")
    plt.xlabel("Geração")
    plt.ylabel("Fitness")
    plt.grid(True)
    plt.show()

    # Curva de patrimônio do melhor
    equity = best["result"]["equity_curve"]

    plt.figure(figsize=(10, 5))
    plt.plot(equity)
    plt.title("Evolução do Patrimônio - Melhor Indivíduo")
    plt.xlabel("Tempo (candles)")
    plt.ylabel("Equity")
    plt.grid(True)
    plt.show()
