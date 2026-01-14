import random
import numpy as np

from core.leadlag import backtest_lead_lag
from evolution.genome import random_genome, mutate, crossover


def max_drawdown(equity_curve):
    """
    Máximo drawdown (em %) de uma curva de patrimônio.
    """
    equity = np.array(equity_curve, dtype=float)
    peaks = np.maximum.accumulate(equity)
    drawdowns = (equity - peaks) / (peaks + 1e-12)  # <= 0
    mdd = drawdowns.min()
    return mdd * 100.0  # ex: -25.0


def equity_returns(equity_curve):
    """
    Converte a curva de patrimônio em retornos passo a passo.
    r_t = (E_t - E_{t-1}) / E_{t-1}
    """
    equity = np.array(equity_curve, dtype=float)
    rets = (equity[1:] - equity[:-1]) / (equity[:-1] + 1e-12)
    return rets


def annualized_return(total_return_pct, n_periods, periods_per_year=252):
    """
    Retorno anualizado aproximado a partir do retorno total (%) e do nº de períodos.
    """
    if n_periods <= 1:
        return total_return_pct

    total_return = total_return_pct / 100.0
    years = n_periods / periods_per_year
    if years <= 0:
        return total_return_pct

    ann = (1.0 + total_return) ** (1.0 / years) - 1.0
    return ann * 100.0


def sortino_ratio(equity_curve):
    """
    Sortino Ratio aproximado a partir da curva de patrimônio.
    Sortino = retorno_médio / desvio dos retornos negativos.
    """
    rets = equity_returns(equity_curve)
    if len(rets) < 2:
        return 0.0

    mean_ret = np.mean(rets)
    neg_rets = rets[rets < 0]

    if len(neg_rets) == 0:
        # nunca teve retorno negativo -> bom demais; limita pra não explodir
        return 5.0

    downside_std = np.std(neg_rets)
    if downside_std < 1e-12:
        return 0.0

    return mean_ret / downside_std


def calmar_ratio(total_return_pct, mdd_pct, n_periods, periods_per_year=252):
    """
    Calmar = retorno_anualizado / |MDD|
    """
    if mdd_pct >= 0:
        return 0.0

    ann_ret = annualized_return(total_return_pct, n_periods, periods_per_year)
    if ann_ret <= 0:
        return 0.0

    return ann_ret / abs(mdd_pct)


def windowed_consistency(equity_curve, n_windows=3):
    """
    Divide a curva em 'n_windows' blocos e mede o retorno em cada.
    Penaliza se alguma janela for muito pior que a média.
    """
    equity = np.array(equity_curve, dtype=float)
    n = len(equity)
    if n < n_windows + 1:
        return [], 0.0

    window_size = n // n_windows
    window_returns = []

    for i in range(n_windows):
        start = i * window_size
        end = (i + 1) * window_size if i < n_windows - 1 else n

        if end - start < 2:
            continue

        eq_start = equity[start]
        eq_end = equity[end - 1]
        ret = (eq_end / (eq_start + 1e-12) - 1.0) * 100.0
        window_returns.append(ret)

    if not window_returns:
        return [], 0.0

    avg_ret = np.mean(window_returns)
    penalty = 0.0
    for r in window_returns:
        diff = avg_ret - r
        if diff > 30.0:
            penalty += (diff - 30.0) * 0.2

    return window_returns, penalty


def evaluate_genome(genome, Px, Py, fee=0.0005):
    """
    Avalia um indivíduo de forma mais "profissional".
    """
    res = backtest_lead_lag(
        Px, Py,
        threshold=genome["threshold"],
        lag=genome["lag"],
        tp=genome["tp"],
        sl=genome["sl"],
        max_hold=genome["max_hold"],
        fee=fee
    )

    total_ret = res["total_return_pct"]          # %
    equity_curve = res["equity_curve"]
    n_periods = len(equity_curve)
    mdd = max_drawdown(equity_curve)             # %
    calmar = calmar_ratio(total_ret, mdd, n_periods)
    sortino = sortino_ratio(equity_curve)
    n_trades = len(res["trades"])

    # Penalidade por nº de trades ruim
    MIN_TRADES = 15
    MAX_TRADES = 400
    trade_penalty = 0.0
    if n_trades < MIN_TRADES:
        trade_penalty += (MIN_TRADES - n_trades) * 0.5
    if n_trades > MAX_TRADES:
        trade_penalty += (n_trades - MAX_TRADES) * 0.1

    # Consistência por janelas
    window_returns, cons_penalty = windowed_consistency(equity_curve, n_windows=3)

    # Combinação do fitness
    fitness = (
        #2.0 * calmar +      # Calmar pesa mais
        #1.5 * sortino +     # Sortino também
        1 * total_ret     # retorno total com peso menor
        #- trade_penalty
        #- cons_penalty
    )

    return {
        "fitness": fitness,
        "total_return_pct": total_ret,
        "mdd_pct": mdd,
        "calmar": calmar,
        "sortino": sortino,
        "n_trades": n_trades,
        "window_returns": window_returns,
        "trade_penalty": trade_penalty,
        "cons_penalty": cons_penalty,
        "result": res,
    }


def tournament_selection(population, k=3):
    """
    Seleção por torneio: sorteia k e pega o de maior fitness.
    """
    competitors = random.sample(population, k)
    competitors.sort(key=lambda ind: ind["fitness"], reverse=True)
    return competitors[0]


def run_ga(
    Px, Py,
    population_size=150,
    generations=60,
    elite_frac=0.2,
    mutation_rate=1,
    tournament_size=3,
    fee=0.0005,
    seed=42
):
    """
    Roda o Algoritmo Genético para otimizar os parâmetros.
    Retorna:
      - best_individual
      - history (melhor fitness por geração)
    """
    random.seed(seed)
    np.random.seed(seed)

    # 1) População inicial
    population = []
    for _ in range(population_size):
        g = random_genome()
        eval_res = evaluate_genome(g, Px, Py, fee)
        population.append({
            "genome": g,
            **eval_res,
        })

    history = []

<<<<<<< HEAD


    DELTA = 1e-6
    count_stagnation = 0
    best_prev = None 
    mutation_rate_original = mutation_rate
    MUT_MAX = 0.8



=======
>>>>>>> cbdfd3fb8f64e02ff5dccaf1f863c57cad5e1708
    for gen in range(generations):
        # 2) Ordena por fitness -> ELITISMO
        population.sort(key=lambda ind: ind["fitness"], reverse=True)
        best = population[0]
        history.append(best["fitness"]) #cópia dos melhores

<<<<<<< HEAD
        best_now=best["fitness"]
        
        if best_prev is not None:
            improv= best_now-best_prev
            if improv<=DELTA:
                count_stagnation=count_stagnation+1
            else:
                count_stagnation=0
                mutation_rate=mutation_rate_original
        else:
            improv = None
            count_stagnation=0
        if count_stagnation>10:
            print(f"   Δfit={improv_str} | stagn={count_stagnation} | mut={mutation_rate:.4f}")
            mutation_rate=min(MUT_MAX,mutation_rate*10)
            count_stagnation=0
        best_prev=best_now

=======
>>>>>>> cbdfd3fb8f64e02ff5dccaf1f863c57cad5e1708
        print(
            f"Geração {gen+1}/{generations} | "
            f"Fit: {best['fitness']:.2f} | "
            f"Ret: {best['total_return_pct']:.2f}% | "
            f"MDD: {best['mdd_pct']:.2f}% | "
            f"Calmar: {best['calmar']:.2f} | "
            f"Sortino: {best['sortino']:.2f} | "
            f"Trades: {best['n_trades']}"
        )

<<<<<<< HEAD
        if improv is None:
            improv_str = "None"
        else:
            improv_str = f"{improv:.6g}"
        print(f"   Δfit={improv_str} | stagn={count_stagnation} | mut={mutation_rate:.4f}")


=======
>>>>>>> cbdfd3fb8f64e02ff5dccaf1f863c57cad5e1708
        # 3) Elitismo
        elite_count = max(1, int(elite_frac * population_size))
        new_population = population[:elite_count]

        # 4) Geração de filhos
        while len(new_population) < population_size: #seleção por torneio
            parent1 = tournament_selection(population, k=tournament_size)
            parent2 = tournament_selection(population, k=tournament_size)
            child_genome = crossover(parent1["genome"], parent2["genome"]) #crossover
            child_genome = mutate(child_genome, mutation_rate=mutation_rate) #mutação

            eval_res = evaluate_genome(child_genome, Px, Py, fee)
            new_population.append({
                "genome": child_genome,
                **eval_res,
            })

        population = new_population

    population.sort(key=lambda ind: ind["fitness"], reverse=True)
    best = population[0]
    return best, history
