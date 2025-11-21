# realtime_signal.py
#
# Gera um sinal em "tempo real" (fim de dia) para PETR4.SA (X) e VALE3.SA (Y),
# usando o melhor genoma salvo em best_genome.json.
#
# Lógica de BUY melhorada:
#   - X caiu mais do que o threshold do genoma
#   - magnitude da queda >= 0.75 * desvio padrão dos últimos 20 dias (volatilidade recente)
#   - tendência de 60 dias de Y não é muito negativa (retorno >= -5%)
#
# Se todas as condições forem satisfeitas: BUY_Y
# Caso contrário: FLAT
#
# Loga tudo em signals_log.csv

import os
import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf


# ----------------- Helpers de preço ----------------- #

def load_price_series(ticker: str, period: str = "180d", interval: str = "1d") -> pd.Series:
    """
    Baixa uma série de preços (Close ou Adj Close) de um ticker.
    Já trata o MultiIndex Price x Ticker que o yfinance está retornando pra você.
    """
    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
    )

    if df is None or df.empty:
        raise RuntimeError(f"ERRO: yfinance retornou DataFrame vazio para {ticker}.")

    cols = df.columns

    if isinstance(cols, pd.MultiIndex):
        level0 = cols.get_level_values(0)
        series = None

        if "Close" in level0:
            close_df = df["Close"]
            if isinstance(close_df, pd.DataFrame):
                series = close_df.iloc[:, 0]
            else:
                series = close_df
        elif "Adj Close" in level0:
            adj_df = df["Adj Close"]
            if isinstance(adj_df, pd.DataFrame):
                series = adj_df.iloc[:, 0]
            else:
                series = adj_df

        if series is None:
            raise RuntimeError(
                f"ERRO: Nenhuma coluna 'Close' ou 'Adj Close' encontrada em MultiIndex para {ticker}.\n"
                f"Colunas: {cols}"
            )
    else:
        if "Close" in cols:
            series = df["Close"]
        elif "Adj Close" in cols:
            series = df["Adj Close"]
        else:
            raise RuntimeError(
                f"ERRO: Nenhuma coluna 'Close' ou 'Adj Close' encontrada para {ticker}.\n"
                f"Colunas: {list(cols)}"
            )

    series = series.dropna()
    if series.empty:
        raise RuntimeError(f"ERRO: Série de preços vazia para {ticker} após dropna.")

    return series


def compute_returns(prices: pd.Series) -> np.ndarray:
    """Retorno simples diário, alinhado com a série (primeiro retorno = 0)."""
    arr = prices.to_numpy(dtype=float).reshape(-1)
    rets = (arr[1:] - arr[:-1]) / (arr[:-1] + 1e-12)
    return np.concatenate([[0.0], rets])


# ----------------- Log em CSV ----------------- #

def log_signal(
    date_str,
    ticker_x,
    ticker_y,
    last_price_x,
    last_price_y,
    last_ret_x,
    threshold,
    tp,
    sl,
    lag,
    max_hold,
    signal,
    reason,
    filename="signals_log.csv",
):
    """
    Acrescenta uma linha no CSV de sinais.
    Se o arquivo não existir, cria com cabeçalho.
    """
    import csv

    file_exists = os.path.exists(filename)
    mode = "a" if file_exists else "w"

    with open(filename, mode, newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "date",
                "ticker_x",
                "ticker_y",
                "last_price_x",
                "last_price_y",
                "last_ret_x",
                "threshold",
                "tp",
                "sl",
                "lag",
                "max_hold",
                "signal",
                "reason",
            ])

        writer.writerow([
            date_str,
            ticker_x,
            ticker_y,
            f"{last_price_x:.4f}",
            f"{last_price_y:.4f}",
            f"{last_ret_x:.6f}",
            f"{threshold:.6f}",
            f"{tp:.6f}",
            f"{sl:.6f}",
            lag,
            max_hold,
            signal,
            reason,
        ])


# ----------------- Genoma ----------------- #

def load_best_genome(path="best_genome.json"):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} não encontrado. Rode main_walkforward.py ou main_ga.py "
            "para gerar um best_genome.json."
        )
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # arquivo pode guardar {"genome": {...}} ou já o dict diretamente
    if "genome" in data:
        return data["genome"]
    return data


# ----------------- Main ----------------- #

def main():
    ticker_x = "PETR4.SA"
    ticker_y = "VALE3.SA"

    print(f"=== SINAL EM TEMPO REAL: {ticker_x} (X) x {ticker_y} (Y) ===\n")

    genome = load_best_genome("best_genome.json")
    threshold = float(genome["threshold"])
    tp = float(genome["tp"])
    sl = float(genome["sl"])
    lag = int(genome["lag"])
    max_hold = int(genome["max_hold"])

    print("Genoma carregado:")
    print(genome)

    # Carrega últimos 180 dias de X e Y
    Px = load_price_series(ticker_x, period="180d", interval="1d")
    Py = load_price_series(ticker_y, period="180d", interval="1d")

    # Garantir alinhamento por data (interseção)
    df = pd.DataFrame({"Px": Px, "Py": Py}).dropna()
    Px = df["Px"]
    Py = df["Py"]

    rx = compute_returns(Px)

    last_price_x = float(Px.iloc[-1])
    last_price_y = float(Py.iloc[-1])
    last_ret_x = float(rx[-1])

    # Volatilidade de 20 dias de X
    if len(rx) >= 21:
        vol20 = float(rx[-20:].std())
    else:
        vol20 = float(rx.std())

    # Tendência de 60 dias de Y (retorno acumulado)
    if len(Py) >= 61:
        price_60 = float(Py.iloc[-61])
        trend60_y = (last_price_y / (price_60 + 1e-12) - 1.0)
    else:
        trend60_y = 0.0

    today = datetime.utcnow().date()
    date_str = today.isoformat()

    print("\n=== CONTEXTO DO DIA ===")
    print(f"Data (aprox.): {date_str}")
    print(f"{ticker_x} preço mais recente: {last_price_x:.2f}")
    print(f"{ticker_y} preço mais recente: {last_price_y:.2f}")
    print(f"Retorno diário de {ticker_x} (último candle): {last_ret_x * 100:.2f}%")
    print(f"Threshold do genoma: {threshold * 100:.2f}%")
    print(f"Volatilidade 20 dias de {ticker_x}: {vol20 * 100:.2f}%")
    print(f"Tendência 60 dias de {ticker_y}: {trend60_y * 100:.2f}%")
    print(f"TP: {tp * 100:.2f}%, SL: {sl * 100:.2f}%, lag: {lag}, max_hold: {max_hold} dias\n")

    # ----------------- Lógica de BUY melhorada ----------------- #

    cond1 = last_ret_x <= threshold
    cond2 = abs(last_ret_x) >= 0.75 * vol20 if vol20 > 0 else False
    cond3 = trend60_y >= -0.05  # não operar se Y estiver despencando forte

    reasons = []
    if not cond1:
        reasons.append("queda de X menor que o threshold")
    if not cond2:
        reasons.append("queda de X não é grande o bastante vs volatilidade")
    if not cond3:
        reasons.append("tendência de 60d de Y muito negativa")

    if cond1 and cond2 and cond3:
        signal = "BUY_Y"
        reason = "X caiu forte (abaixo do threshold) com movimento relevante e Y não está em forte baixa"
        print(">>> SINAL: COMPRAR VALE3.SA (Y) NA PRÓXIMA ABERTURA <<<")
        print(f"Motivo: {reason}")
    else:
        signal = "FLAT"
        if not reasons:
            reason = "condições não atendidas (sem motivo específico)"
        else:
            reason = "; ".join(reasons)
        print(">>> SINAL: FICAR FORA / MANTER FLAT <<<")
        print(f"Motivo: {reason}")

    # Loga o sinal
    log_signal(
        date_str=date_str,
        ticker_x=ticker_x,
        ticker_y=ticker_y,
        last_price_x=last_price_x,
        last_price_y=last_price_y,
        last_ret_x=last_ret_x,
        threshold=threshold,
        tp=tp,
        sl=sl,
        lag=lag,
        max_hold=max_hold,
        signal=signal,
        reason=reason,
    )

    print("\n[INFO] Sinal registrado em signals_log.csv.")
    print("\nObs.: o script supõe que você está FLAT.")
    print("      Ele responde: 'se eu estivesse sem posição hoje, entro amanhã ou não?'.")


if __name__ == "__main__":
    main()
