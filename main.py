import numpy as np
import matplotlib.pyplot as plt
from core.leadlag import backtest_lead_lag

if __name__ == "__main__":
    np.random.seed(42)

    T = 1000

    Px = 100 + np.cumsum(np.random.normal(0, 0.2, size=T))
    Py = 50 + 0.5*(Px - 100) + np.random.normal(0, 0.5, size=T)

    result = backtest_lead_lag(
        Px, Py,
        threshold=-0.01,
        lag=1,
        tp=0.02,
        sl=-0.01,
        max_hold=10,
        fee=0.0005
    )

    print("\n=== RESULTADOS ===")
    print("Capital inicial:", result["initial_cash"])
    print("Capital final  :", result["final_equity"])
    print("Retorno total (%):", result["total_return_pct"])
    print("N trades:", len(result["trades"]))
    print()

    for tr in result["trades"][:5]:
        print(tr)
        
equity = result["equity_curve"]

plt.figure(figsize=(10,5))
plt.plot(equity)
plt.title("Evolução do Patrimônio")
plt.xlabel("Tempo (candles)")
plt.ylabel("Equity")
plt.grid(True)
plt.show()

fig, ax1 = plt.subplots(figsize=(10,5))

ax1.plot(Px, label="X (leader)", alpha=0.7)
ax1.plot(Py, label="Y (follower)", alpha=0.7)
ax1.set_xlabel("Tempo (candles)")
ax1.set_ylabel("Preço")
ax1.legend()
ax1.grid(True)

plt.show()