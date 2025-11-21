import numpy as np
import matplotlib.pyplot as plt

from data.loaders import load_brazil_stocks
from evolution.ga import run_ga, evaluate_genome


def walkforward_petr_vale(
    test_block_days=250,      # ~ 1 ano de pregão
    population_size=150,
    generations=60,
    fee=0.0005
):
    # ==============================
    # 1) Carregar 10 anos de dados
    # ==============================
    Px, Py = load_brazil_stocks(
        "PETR4.SA",
        "VALE3.SA",
        period="10y",
        interval="1d"
    )

    Px = np.asarray(Px, dtype=float).reshape(-1)
    Py = np.asarray(Py, dtype=float).reshape(-1)
    T = min(len(Px), len(Py))
    Px = Px[:T]
    Py = Py[:T]

    print(f"Total de candles (dias): {T}")

    # ponto inicial do primeiro teste:
    # ~70% do total
    first_train_end = int(0.7 * T)
    print(f"Primeiro treino: 0 .. {first_train_end-1}")
    print(f"Cada bloco de teste: {test_block_days} dias\n")

    wf_results = []  # para guardar métricas por janela

    train_end = first_train_end
    wf_id = 0

    while train_end + test_block_days <= T:
        wf_id += 1
        test_start = train_end
        test_end = train_end + test_block_days

        print("=" * 60)
        print(f"Janela WF #{wf_id}")
        print(f"Treino: 0 .. {train_end-1}  (n={train_end})")
        print(f"Teste : {test_start} .. {test_end-1}  (n={test_block_days})")

        # -------------------------
        # 2) Treino (GA)
        # -------------------------
        train_Px = Px[:train_end]
        train_Py = Py[:train_end]

        best_train, history = run_ga(
            train_Px, train_Py,
            population_size=population_size,
            generations=generations,
            fee=fee,
            seed=42 + wf_id  # muda seed por janela
        )

        genome = best_train["genome"]

        print("\n> Melhor indivíduo no TREINO:")
        print("Genoma:", genome)
        print("Fitness treino:", best_train["fitness"])
        print("Retorno treino (%):", best_train["total_return_pct"])
        print("MDD treino (%):", best_train["mdd_pct"])
        print("Calmar treino:", best_train["calmar"])
        print("Sortino treino:", best_train["sortino"])
        print("N trades treino:", best_train["n_trades"])

        # -------------------------
        # 3) Avaliação no TESTE
        # -------------------------
        test_Px = Px[test_start:test_end]
        test_Py = Py[test_start:test_end]

        eval_test = evaluate_genome(genome, test_Px, test_Py, fee)

        print("\n> Desempenho no TESTE (sem reotimizar):")
        print("Retorno teste (%):", eval_test["total_return_pct"])
        print("MDD teste (%):", eval_test["mdd_pct"])
        print("Calmar teste:", eval_test["calmar"])
        print("Sortino teste:", eval_test["sortino"])
        print("N trades teste:", eval_test["n_trades"])
        print("Retornos por janela teste:", eval_test["window_returns"])

        wf_results.append({
            "wf_id": wf_id,
            "train_start": 0,
            "train_end": train_end,
            "test_start": test_start,
            "test_end": test_end,
            "genome": genome,
            "fitness_train": best_train["fitness"],
            "ret_train": best_train["total_return_pct"],
            "mdd_train": best_train["mdd_pct"],
            "calmar_train": best_train["calmar"],
            "sortino_train": best_train["sortino"],
            "n_trades_train": best_train["n_trades"],
            "ret_test": eval_test["total_return_pct"],
            "mdd_test": eval_test["mdd_pct"],
            "calmar_test": eval_test["calmar"],
            "sortino_test": eval_test["sortino"],
            "n_trades_test": eval_test["n_trades"],
            "history": history,
            "equity_train": best_train["result"]["equity_curve"],
            "equity_test": eval_test["result"]["equity_curve"],
        })

        # avança a janela:
        train_end = test_end  # expanding: treino passa a incluir esse bloco de teste

    return wf_results


if __name__ == "__main__":
    wf_results = walkforward_petr_vale(
        test_block_days=250,   # ~1 ano de teste por bloco
        population_size=150,
        generations=60,
        fee=0.0005
    )

    # =================================
    # 4) Gráficos de resumo do WF
    # =================================
    # Se não tiver nenhuma janela, aborta
    if not wf_results:
        print("Nenhuma janela WF foi gerada (dados insuficientes).")
        raise SystemExit()

    # ---- 4.1. Retorno treino x teste por janela ----
    wf_ids = [r["wf_id"] for r in wf_results]
    ret_train = [r["ret_train"] for r in wf_results]
    ret_test = [r["ret_test"] for r in wf_results]

    plt.figure(figsize=(10, 5))
    plt.plot(wf_ids, ret_train, marker="o", label="Treino")
    plt.plot(wf_ids, ret_test, marker="s", label="Teste")
    plt.title("Walk-forward PETR4 x VALE3 - Retorno por janela")
    plt.xlabel("Janela WF")
    plt.ylabel("Retorno (%)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # ---- 4.2. Fitness por geração da última janela ----
    last = wf_results[-1]
    history = last["history"]

    plt.figure(figsize=(10, 4))
    plt.plot(history, marker="o", linewidth=1)
    plt.title(f"Última janela WF #{last['wf_id']} - Fitness por geração")
    plt.xlabel("Geração")
    plt.ylabel("Fitness")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # ---- 4.3. Equity treino vs teste na última janela ----
    eq_train = last["equity_train"]
    eq_test = last["equity_test"]

    plt.figure(figsize=(10, 5))
    plt.plot(eq_train, label="Treino", linewidth=1)
    plt.plot(
        range(len(eq_train), len(eq_train) + len(eq_test)),
        eq_test,
        label="Teste",
        linewidth=1
    )
    plt.title(f"Última janela WF #{last['wf_id']} - Equity treino x teste")
    plt.xlabel("Tempo (candles)")
    plt.ylabel("Equity")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()
