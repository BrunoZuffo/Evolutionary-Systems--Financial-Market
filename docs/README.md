# Evolutionary-Systems–Financial-Market

Projeto da disciplina **Sistemas Evolutivos**: uso de um **Algoritmo Genético (GA)** para
evoluir uma estratégia de trading em ações brasileiras, baseada na relação entre duas ações
(PETR4.SA e VALE3.SA por padrão).

O foco principal **não** é “bater o mercado”, e sim:
- Modelar claramente **genótipo → fenótipo**;
- Implementar operadores evolutivos (seleção, crossover, mutação);
- Definir e justificar uma **função de fitness** aplicada a um problema real;
- Avaliar o sistema com **backtest**, **walk-forward** e comparação com um **baseline** simples.

---

## 1. Estrutura do projeto

```text
core/
  leadlag.py          # Backtest da estratégia (lead/lag entre X e Y)
data/
  loaders.py          # Carrega dados da B3 via yfinance
evolution/
  ga.py               # Algoritmo Genético (representação, seleção, crossover, mutação)
  genome.py           # Funções auxiliares para o genoma
tests/
  ...                 # (opcional) testes
main.py               # Exemplo simples
main_ga.py            # GA rodando em 10 anos contínuos (uma janela)
main_walkforward.py   # GA em esquema walk-forward (várias janelas)
realtime_signal.py    # Gera o sinal diário “se eu estivesse FLAT, o que eu faria amanhã?”
realtime_bot.py       # Simula o robô ao longo de todo o histórico, gera trades_log.csv
analyze_signals.py    # Análise simples dos sinais do dia (signals_log.csv)
analyze_results.py    # ANÁLISE AVANÇADA: estratégia x buy&hold, Sharpe, DD, histograma etc.
best_genome.json      # Melhor genoma encontrado pelo treino (para uso em tempo real)
signals_log.csv       # Log de sinais diários do realtime_signal.py
trades_log.csv        # Log de trades simuladas pelo realtime_bot.py
requirements.txt      # Dependências do projeto (pandas, numpy, matplotlib, yfinance, etc.)
