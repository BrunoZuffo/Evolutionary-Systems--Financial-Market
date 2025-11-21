# evolution/genome.py

import random
import copy

# Faixas "realistas" para swing trade diário em ações brasileiras
GENOME_BOUNDS = {
    # queda mínima de X (líder) para disparar entrada em Y (seguidor)
    "threshold": (-0.03, -0.005),   # -3% a -0.5%

    # take profit (alvo de lucro relativo)
    "tp": (0.01, 0.04),             # +1% a +4%

    # stop loss (perda máxima relativa)
    "sl": (-0.06, -0.02),           # -6% a -2%

    # atraso entre sinal em X e entrada em Y
    "lag": (0, 3),                  # 0 a 3 dias

    # tempo máximo segurando a posição
    "max_hold": (3, 15),            # 3 a 15 dias
}


def _clamp(value, low, high):
    return max(low, min(high, value))


def _fix_constraints(g):
    """
    Garante:
    - limites dentro de GENOME_BOUNDS
    - |sl| >= tp  (stop nunca mais apertado que o alvo)
    - lag, max_hold inteiros
    """
    # clamp básicos
    for key, (lo, hi) in GENOME_BOUNDS.items():
        g[key] = _clamp(g[key], lo, hi)

    # força |sl| >= tp
    if abs(g["sl"]) < g["tp"]:
        g["sl"] = -g["tp"]  # mantém sinal negativo
        lo, hi = GENOME_BOUNDS["sl"]
        g["sl"] = _clamp(g["sl"], lo, hi)

    # lag e max_hold inteiros
    g["lag"] = int(round(g["lag"]))
    g["max_hold"] = int(round(g["max_hold"]))

    # garante de novo dentro da faixa
    for key, (lo, hi) in GENOME_BOUNDS.items():
        g[key] = _clamp(g[key], lo, hi)

    return g


def random_genome():
    """
    Cria um genoma aleatório dentro dos limites e respeitando as constraints.
    """
    g = {
        "threshold": random.uniform(*GENOME_BOUNDS["threshold"]),
        "tp":        random.uniform(*GENOME_BOUNDS["tp"]),
        "sl":        random.uniform(*GENOME_BOUNDS["sl"]),
        "lag":       random.randint(*GENOME_BOUNDS["lag"]),
        "max_hold":  random.randint(*GENOME_BOUNDS["max_hold"]),
    }
    return _fix_constraints(g)


def crossover(g1, g2):
    """
    Crossover simples:
    - média para parâmetros contínuos
    - escolha aleatória para inteiros
    """
    child = {}

    # contínuos
    child["threshold"] = 0.5 * (g1["threshold"] + g2["threshold"])
    child["tp"]        = 0.5 * (g1["tp"]        + g2["tp"])
    child["sl"]        = 0.5 * (g1["sl"]        + g2["sl"])

    # inteiros
    child["lag"]       = random.choice([g1["lag"], g2["lag"]])
    child["max_hold"]  = random.choice([g1["max_hold"], g2["max_hold"]])

    return _fix_constraints(child)


def mutate(genome, mutation_rate=0.3):
    """
    Mutação gaussiana nos contínuos + pequenos passos nos inteiros.
    mutation_rate = probabilidade de mutar cada gene.
    """
    g = copy.deepcopy(genome)

    thr_lo, thr_hi = GENOME_BOUNDS["threshold"]
    tp_lo, tp_hi   = GENOME_BOUNDS["tp"]
    sl_lo, sl_hi   = GENOME_BOUNDS["sl"]

    thr_range = thr_hi - thr_lo
    tp_range  = tp_hi  - tp_lo
    sl_range  = sl_hi  - sl_lo

    # threshold
    if random.random() < mutation_rate:
        g["threshold"] += random.gauss(0.0, 0.15 * thr_range)

    # tp
    if random.random() < mutation_rate:
        g["tp"] += random.gauss(0.0, 0.15 * tp_range)

    # sl
    if random.random() < mutation_rate:
        g["sl"] += random.gauss(0.0, 0.15 * sl_range)

    # lag
    if random.random() < mutation_rate:
        g["lag"] += random.choice([-1, 0, 1])

    # max_hold
    if random.random() < mutation_rate:
        g["max_hold"] += random.choice([-2, -1, 0, 1, 2])

    return _fix_constraints(g)
