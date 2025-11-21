import numpy as np

def compute_returns(prices):
    # garante vetor 1D
    prices = np.asarray(prices, dtype=float).reshape(-1)

    if len(prices) < 2:
        return np.zeros_like(prices, dtype=float)

    rets = (prices[1:] - prices[:-1]) / (prices[:-1] + 1e-12)
    # primeiro retorno = 0 para alinhar tamanhos
    return np.concatenate(([0.0], rets))


def backtest_lead_lag(
    Px, Py,
    threshold=-0.01,
    lag=1,
    tp=0.02,
    sl=-0.01,
    max_hold=10,
    fee=0.0005
):
    # converte para numpy 1D
    Px = np.asarray(Px, dtype=float).reshape(-1)
    Py = np.asarray(Py, dtype=float).reshape(-1)

    # garante mesmo comprimento
    T = min(len(Px), len(Py))
    Px = Px[:T]
    Py = Py[:T]

    rx = compute_returns(Px)
    ry = compute_returns(Py)  # ainda não usamos, mas deixei aqui

    cash = 1000.0
    position = 0.0
    entry_price = None
    equity_curve = []
    trades = []

    # para lidar com o lag sem olhar o futuro
    planned_entry_t = None  # candle onde queremos entrar (por causa do lag)

    for t in range(T):
        price_y = Py[t]
        equity = cash + position * price_y
        equity_curve.append(equity)

        # não há retorno definido em t=0 (rx[-1] não faz sentido)
        if t == 0:
            continue

        # =====================================================
        # 1) Se NÃO temos posição aberta
        # =====================================================
        if position == 0.0:

            # 1a) Verifica se chegou a hora de executar uma entrada planejada
            if planned_entry_t is not None and t >= planned_entry_t:
                # executa entrada pelo preço atual (sem olhar o futuro)
                entry_price = price_y
                size = cash / (entry_price * (1.0 + fee))
                cost = size * entry_price
                fee_paid = cost * fee

                if size > 0 and cash >= cost + fee_paid:
                    cash -= cost + fee_paid
                    position = size
                    trades.append({
                        "signal_t": planned_entry_t - lag,  # quando o sinal aconteceu
                        "entry_t": t,                        # quando entrou de fato
                        "entry_price": entry_price,
                        "size": size,
                        "fee_entry": fee_paid
                    })

                # limpa o plano de entrada, mesmo que não tenha conseguido entrar
                planned_entry_t = None

            # 1b) Se ainda estamos sem posição e sem entrada planejada,
            #     podemos gerar um novo sinal
            if position == 0.0 and planned_entry_t is None:
                # sinal baseado apenas em informações PASSADAS (rx[t-1])
                if rx[t-1] <= threshold:
                    if lag == 0:
                        # entra IMEDIATAMENTE no candle atual
                        entry_price = price_y
                        size = cash / (entry_price * (1.0 + fee))
                        cost = size * entry_price
                        fee_paid = cost * fee

                        if size > 0 and cash >= cost + fee_paid:
                            cash -= cost + fee_paid
                            position = size
                            trades.append({
                                "signal_t": t,
                                "entry_t": t,
                                "entry_price": entry_price,
                                "size": size,
                                "fee_entry": fee_paid
                            })
                    else:
                        # agenda uma entrada futura em t + lag (sem olhar o preço futuro)
                        target_t = t + lag
                        if target_t < T:
                            planned_entry_t = target_t

        # =====================================================
        # 2) Se JÁ temos posição aberta -> checar saída
        # =====================================================
        else:
            trade = trades[-1]  # trade mais recente
            hold_time = t - trade["entry_t"]
            entry_price = trade["entry_price"]
            ret_trade = (price_y - entry_price) / (entry_price + 1e-12)

            exit_reason = None
            if ret_trade >= tp:
                exit_reason = "TP"
            elif ret_trade <= sl:
                exit_reason = "SL"
            elif hold_time >= max_hold:
                exit_reason = "TIME"

            if exit_reason is not None:
                revenue = position * price_y
                fee_paid = revenue * fee
                cash += revenue - fee_paid

                trades[-1]["exit_t"] = t
                trades[-1]["exit_price"] = price_y
                trades[-1]["fee_exit"] = fee_paid
                trades[-1]["pnl"] = (
                    (price_y - entry_price) * position
                    - (trades[-1]["fee_entry"] + fee_paid)
                )
                trades[-1]["exit_reason"] = exit_reason

                position = 0.0
                entry_price = None
                planned_entry_t = None  # não deve haver plano de entrada ativo com posição aberta

    # fim do loop principal

    # se terminar ainda com posição aberta, fecha no último preço
    if position != 0.0:
        price_y = Py[-1]
        revenue = position * price_y
        fee_paid = revenue * fee
        cash += revenue - fee_paid

        trades[-1]["exit_t"] = T - 1
        trades[-1]["exit_price"] = price_y
        trades[-1]["fee_exit"] = fee_paid
        trades[-1]["pnl"] = (
            (price_y - trades[-1]["entry_price"]) * position
            - (trades[-1]["fee_entry"] + fee_paid)
        )
        trades[-1]["exit_reason"] = "EOD"  # end of data
        position = 0.0

        # atualiza equity final
        equity_curve[-1] = cash

    final_equity = cash
    equity_curve = np.array(equity_curve)
    total_return = (final_equity / 1000.0 - 1.0) * 100.0

    return {
        "initial_cash": 1000.0,
        "final_equity": final_equity,
        "total_return_pct": total_return,
        "equity_curve": equity_curve,
        "trades": trades
    }
