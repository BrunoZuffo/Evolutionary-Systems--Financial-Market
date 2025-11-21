import numpy as np

def compute_returns(prices):
    prices = np.array(prices, dtype=float)
    rets = (prices[1:] - prices[:-1]) / (prices[:-1] + 1e-12)
    return np.concatenate([[0.0], rets])  # alinha tamanho (0 no primeiro)


def backtest_lead_lag(
    Px, Py,
    threshold=-0.01,
    lag=1,
    tp=0.02,
    sl=-0.01,
    max_hold=10,
    fee=0.0005
):
    Px = np.array(Px, dtype=float)
    Py = np.array(Py, dtype=float)

    rx = compute_returns(Px)
    ry = compute_returns(Py)

    cash = 1000.0
    position = 0.0
    entry_price = None
    equity_curve = []
    trades = []

    for t in range(len(Px)):
        price_y = Py[t]
        equity = cash + position * price_y
        equity_curve.append(equity)

        if t == 0:
            continue

        if position == 0.0:
            if rx[t-1] <= threshold:
                if t + lag < len(Py):
                    entry_idx = t + lag
                    entry_price = Py[entry_idx]

                    # calcula o tamanho da posição já considerando a taxa
                    size = cash / (entry_price * (1.0 + fee))
                    cost = size * entry_price
                    fee_paid = cost * fee

                    if size > 0:
                        cash -= cost + fee_paid
                        position = size
                        trades.append({
                            "entry_t": entry_idx,
                            "entry_price": entry_price,
                            "size": size,
                            "fee_entry": fee_paid
                    })

        else:
            trade = trades[-1]
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
                trades[-1]["pnl"] = (price_y - entry_price) * position - (trades[-1]["fee_entry"] + fee_paid)
                trades[-1]["exit_reason"] = exit_reason
                position = 0.0
                entry_price = None

    final_equity = cash + position * Py[-1]
    equity_curve = np.array(equity_curve)
    total_return = (final_equity / 1000.0 - 1.0) * 100

    return {
        "initial_cash": 1000.0,
        "final_equity": final_equity,
        "total_return_pct": total_return,
        "equity_curve": equity_curve,
        "trades": trades
    }
