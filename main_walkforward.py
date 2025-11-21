# main_walkforward.py
import numpy as np
import matplotlib.pyplot as plt
import json

from data.loaders import load_brazil_stocks
from evolution.ga import run_ga, evaluate_genome


def walkforward_deslizante(
    Px,
    Py,
    train_years=6,
    test_years=1,
    population_size=120,
    generations=40,
    fee=0.0005,
    seed_base=42,
):
    """
    Walk-forward deslizante:
    - Janela de treino: train_years
    - Janela de teste:  test_years
    - Anda para frente pelo tamanho da janela de teste.

    Retorna:
        wf_results (lista de dicts com treino/teste por janela)
    """
    n = len(Px)
    dias_por_ano = 252  # aproximado

    train_len = train_years * dias_por_ano
    test_len = test_years * dias_por_ano

    wf_results = []
    wf_idx = 0

    start_train = 0
    while True:
        end_train = start_train + train_len
        end_test = end_train + test_len

        if end_test > n:
            break  # acabou o histórico para outra janela completa

        wf_idx += 1
        print(f"\n=== WF #{wf_idx} | treino [{start_train}:{end_train}] teste [{end_train}:{end_test}] ===")

        Px_train = Px[start_train:end_train]
        Py_train = Py[start_train:end_train]

        Px_test = Px[end_train:end_test]
        Py_test = Py[end_train:end_test]

        # --- GA no TREINO ---
        best_train, history_train = run_ga(
            Px_train,
            Py_train,
            population_size=population_size,
            generations=generations,
            fee=fee,
            seed=seed_base + wf_idx,
        )

        print("\n> Melhor indivíduo no TREINO:")
        print("Genoma:", best_train["genome"])
        print("Fitness treino:", best_train["fitness"])
        print("Retorno treino (%):", best_train["total_return_pct"])
        print("MDD treino (%):", best_train["mdd_pct"])
        print("Calmar treino:", best_train["calmar"])
        print("Sortino treino:", best_train["sortino"])
        print("N trades treino:", best_train["n_trades"])

        # --- Aplica mesmo genoma no TESTE ---
        eval_test = evaluate_genome(best_train["genome"], Px_test, Py_test, fee=fee)

        print("\n> Desempenho no TESTE (sem reotimizar):")
        print("Retorno teste (%):", eval_test["total_return_pct"])
        print("MDD teste (%):", eval_test["mdd_pct"])
        print("Calmar teste:", eval_test["calmar"])
        print("Sortino teste:", eval_test["sortino"])
        print("N trades teste:", eval_test["n_trades"])
        print("Retornos por janela teste:", eval_test["window_returns"])

        wf_results.append({
            "wf_idx": wf_idx,
            "start_train": start_train,
            "end_train": end_train,
            "end_test": end_test,
            "best_train": best_train,
            "history_train": history_train,
            "eval_test": eval_test,
        })

        # anda a janela pelo tamanho do bloco de teste
        start_train += test_len

    return wf_results


if __name__ == "__main__":
    np.random.seed(42)

    # 1) Carrega 10 anos de PETR4 x VALE3 (diário)
    Px, Py = load_brazil_stocks(
        "PETR4.SA",
        "VALE3.SA",
        period="10y",
        interval="1d",
    )

    Px = np.asarray(Px, dtype=float).reshape(-1)
    Py = np.asarray(Py, dtype=float).reshape(-1)
    n = min(len(Px), len(Py))
    Px = Px[:n]
    Py = Py[:n]

    # 2) Executa WF
    wf_results = walkforward_deslizante(
        Px,
        Py,
        train_years=6,
        test_years=1,
        population_size=120,
        generations=40,
        fee=0.0005,
        seed_base=100,
    )

    if not wf_results:
        print("Nenhuma janela WF gerada (histórico insuficiente).")
        raise SystemExit()

    # 3) Gráfico de retorno por janela (treino x teste)
    wf_ids = [r["wf_idx"] for r in wf_results]
    ret_train = [r["best_train"]["total_return_pct"] for r in wf_results]
    ret_test = [r["eval_test"]["total_return_pct"] for r in wf_results]

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

    # 4) Última janela WF – plots detalhados + salvar best_genome.json
    last = wf_results[-1]
    last_wf_idx = last["wf_idx"]
    history_train = last["history_train"]
    best_train = last["best_train"]
    eval_test = last["eval_test"]

    # 4.1 Fitness por geração (última WF)
    plt.figure(figsize=(10, 4))
    plt.plot(history_train, marker="o")
    plt.title(f"Última janela WF #{last_wf_idx} - Fitness por geração")
    plt.xlabel("Geração")
    plt.ylabel("Fitness")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    # 4.2 Equity treino x teste (última WF)
    eq_train = best_train["result"]["equity_curve"]
    eq_test = eval_test["result"]["equity_curve"]

    plt.figure(figsize=(10, 5))
    plt.plot(eq_train, label="Treino")
    offset = len(eq_train)
    plt.plot(np.arange(offset, offset + len(eq_test)), eq_test, label="Teste")
    plt.title(f"Última janela WF #{last_wf_idx} - Equity treino x teste")
    plt.xlabel("Tempo (candles)")
    plt.ylabel("Equity")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # 4.3 Salva best_genome.json com o genoma da ÚLTIMA janela de treino
    best_genome = best_train["genome"]
    with open("best_genome.json", "w") as f:
        json.dump(best_genome, f, indent=2)
    print("\n[INFO] best_genome.json salvo com o melhor genoma da última janela WF:")
    print(best_genome)
