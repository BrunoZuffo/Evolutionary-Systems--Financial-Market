import random

# Faixas válidas para cada parâmetro da estratégia
PARAM_RANGES = {
    # queda mínima em X para gerar sinal (negativo)
    "threshold": (-0.03, -0.001),   # de -3% a -0.1%

    # take profit de Y (positivo)
    "tp": (0.002, 0.05),            # de 0.2% a 5%

    # stop loss de Y (negativo)
    "sl": (-0.05, -0.002),          # de -5% a -0.2%

    # atraso entre sinal de X e entrada em Y (em candles)
    "lag": (0, 5),                  # de 0 a 5 candles

    # tempo máximo segurando o trade
    "max_hold": (3, 40),            # entre 3 e 40 candles
}


def random_float(low, high):
    """Sorteia um float uniforme entre low e high."""
    return low + (high - low) * random.random()


def random_int(low, high):
    """Sorteia um inteiro entre low e high (inclusive)."""
    return random.randint(low, high)


def clamp(value, low, high):
    """Garante que o value fica dentro de [low, high]."""
    return max(low, min(high, value))


def random_genome():
    """
    Cria um indivíduo aleatório.
    Cada indivíduo é só um dicionário com os parâmetros da estratégia.
    """
    g = {
        "threshold": random_float(*PARAM_RANGES["threshold"]),
        "tp":        random_float(*PARAM_RANGES["tp"]),
        "sl":        random_float(*PARAM_RANGES["sl"]),
        "lag":       random_int(*PARAM_RANGES["lag"]),
        "max_hold":  random_int(*PARAM_RANGES["max_hold"]),
    }
    return g


def mutate(genome, mutation_rate=0.3):
    """
    Aplica pequenas perturbações aleatórias nos parâmetros.
    mutation_rate = probabilidade de mutar cada gene.
    """
    new_g = genome.copy()

    # threshold (float negativo)
    if random.random() < mutation_rate:
        low, high = PARAM_RANGES["threshold"]
        delta = (high - low) * 0.1   # 10% do range
        new_g["threshold"] += random.uniform(-delta, delta)
        new_g["threshold"] = clamp(new_g["threshold"], low, high)

    # tp (float positivo)
    if random.random() < mutation_rate:
        low, high = PARAM_RANGES["tp"]
        delta = (high - low) * 0.1
        new_g["tp"] += random.uniform(-delta, delta)
        new_g["tp"] = clamp(new_g["tp"], low, high)

    # sl (float negativo)
    if random.random() < mutation_rate:
        low, high = PARAM_RANGES["sl"]
        delta = (high - low) * 0.1
        new_g["sl"] += random.uniform(-delta, delta)
        new_g["sl"] = clamp(new_g["sl"], low, high)

    # lag (inteiro)
    if random.random() < mutation_rate:
        low, high = PARAM_RANGES["lag"]
        delta = random.randint(-1, 1)
        new_g["lag"] = clamp(new_g["lag"] + delta, low, high)

    # max_hold (inteiro)
    if random.random() < mutation_rate:
        low, high = PARAM_RANGES["max_hold"]
        delta = random.randint(-3, 3)
        new_g["max_hold"] = clamp(new_g["max_hold"] + delta, low, high)

    return new_g


def crossover(parent1, parent2):
    """
    Crossover simples: para cada gene, escolhe de um dos pais.
    """
    child = {}
    for key in parent1.keys():
        if random.random() < 0.5:
            child[key] = parent1[key]
        else:
            child[key] = parent2[key]
    return child
