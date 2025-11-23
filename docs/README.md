# Algoritmo Evolutivo para Otimização de Estratégias de Trading entre PETR4 e VALE3

Este projeto implementa um **Algoritmo Genético (AG)** para evoluir **estratégias de trading** baseadas na relação entre duas ações brasileiras: **PETR4.SA** e **VALE3.SA**.  
O objetivo é otimizar parâmetros que geram sinais de compra/venda para o próximo candle, usando dados reais da B3 via Yahoo Finance.

O trabalho foi desenvolvido para a disciplina:

**SSC0713 – Sistemas Evolutivos Aplicados à Robótica  
ICMC – USP São Carlos  
Professor: Eduardo do Valle Simões**

---

## 🧬 1. Visão Geral

O algoritmo evolutivo busca encontrar o melhor conjunto de parâmetros para uma regra simples, porém não trivial, que decide:

- **Quando comprar VALE3**
- **Quando ficar fora do mercado**
- Baseado na **variação percentual de PETR4** nos últimos candles

O AG evolui os seguintes parâmetros:

| Gene | Descrição |
|------|-----------|
| `threshold` | queda mínima de PETR4 para ativar sinal |
| `tp` | take profit (%) |
| `sl` | stop loss (%) |
| `lag` | atraso usado entre sinais |
| `max_hold` | dias máximos mantendo o trade |

Um indivíduo representa **uma estratégia completa** (genótipo).  
Essa estratégia gera sinais (fenótipo), que são avaliados via backtesting para obter o fitness.

---

## 🔍 2. Estrutura Evolutiva

### Representação (Genótipo)
Cada indivíduo é um dicionário contendo:

```python
{
  "threshold": float,
  "tp": float,
  "sl": float,
  "lag": int,
  "max_hold": int
}

Fenótipo
É uma estratégia de trading aplicada ao histórico de PETR4 e VALE3.
Operadores Evolutivos
Seleção: Torneio (pressiona melhores indivíduos sem perder diversidade)


Crossover: recombinação uniforme (mistura genética de pais)


Mutação: perturbação pequena nos genes (evita convergência prematura)


Elitismo: melhor indivíduo passa direto para próxima geração


Fitness
Três componentes:
Retorno total


Penalização por drawdown


Penalização por número excessivo de trades


O objetivo final é maximizar retorno ajustado ao risco.

📊 3. Dados Financeiros
Fonte: Yahoo Finance (yfinance)


Timeframe: Diário


Ações: PETR4.SA e VALE3.SA


Período total: ~10 anos



🧪 4. Módulos do Projeto
1️⃣ main_ga.py
Treina o AG e salva:
best_genome.json

2️⃣ main_walkforward.py
Executa treinamento rolando no tempo (walk-forward).
 Gera avaliações out-of-sample.
3️⃣ realtime_signal.py
Gera sinais em tempo real, com logging em:
signals_log.csv

4️⃣ realtime_bot.py
Simula trades reais com base nos sinais.
 Gera:
trades_log.csv

5️⃣ analyze_signals.py
Avalia a validade dos sinais (ex.: BUY_Y → lucro do dia seguinte).
6️⃣ analyze_results.py
📌 Será usado para comparar o desempenho da estratégia com o Buy & Hold.
 (Métricas: retorno, drawdown, sharpe, nº de trades)

⚙️ 5. Instalação
Criar o ambiente virtual:
python -m venv .venv

Ativar:
Windows
.\.venv\Scripts\activate

Instalar dependências:
pip install -r requirements.txt


▶️ 6. Como Rodar o Projeto
Treinar o Algoritmo Genético
python main_ga.py

Executar o Walk-Forward
python main_walkforward.py

Gerar sinais com o modelo treinado
python realtime_signal.py

Gerar trades simulados
python realtime_bot.py

Analisar qualidade dos sinais
python analyze_signals.py

Analisar resultados finais
python analyze_results.py


📈 7. Exemplo de Saída (sinais e trades)
signals_log.csv:
 Todos os sinais emitidos pelo modelo.


trades_log.csv:
 Cada operação simulada com:


retorno,


retorno em %,


take-profit/stop,


motivo de saída,


equity após o trade.



🎥 8. Vídeo Explicativo (Obrigatório)
👉 Link do vídeo será colocado aqui após gravação.

📚 9. Referências
Material da disciplina SSC0713


“Algorithms for Optimization” — Kochenderfer


B3


Yahoo Finance API (yfinance)



👨‍💻 Autor
Bruno Zuffo
 ICMC — USP São Carlos
 Curso: Engenharia de Computação
 Disciplina: SSC0713 – Sistemas Evolutivos