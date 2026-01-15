# Algoritmo Evolutivo para Otimização de Estratégias de Trading entre PETR4 e VALE3

Este projeto implementa um **Algoritmo Genético (AG)** para evoluir **estratégias de trading** baseadas na relação entre duas ações brasileiras: **PETR4.SA** e **VALE3.SA**.  
O objetivo é otimizar parâmetros que geram sinais de compra/venda para o próximo candle, usando dados reais da B3 via Yahoo Finance.

Trabalho desenvolvido para a disciplina:

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

### **Genótipo**
```python
{
  "threshold": float,
  "tp": float,
  "sl": float,
  "lag": int,
  "max_hold": int
}
```

### **Fenótipo**
- Estratégia de trading derivada desses parâmetros  
- Geração de sinais BUY_Y ou FLAT  
- Avaliada em dados históricos

### **Operadores Evolutivos**
- **Seleção:** Torneio (pressiona melhores indivíduos sem perder diversidade)  
- **Crossover:** recombinação uniforme  
- **Mutação:** perturbação gaussiana nos genes  
- **Elitismo:** melhor indivíduo passa direto para a próxima geração  

### **Fitness**
Três componentes:
- **Retorno total**  
- **Penalização por drawdown**  
- **Penalização por número excessivo de trades**

---

## 📊 3. Dados Financeiros

- Fonte: Yahoo Finance (`yfinance`)  
- Timeframe: Diário  
- Ações: **PETR4.SA** e **VALE3.SA**  
- Período total: ~10 anos  

---

## 🧪 4. Módulos do Projeto

### **1️⃣ main_ga.py**
Treina o AG e salva:
- `best_genome.json`

### **2️⃣ main_walkforward.py**
Executa treinamento rolando no tempo (walk-forward):
- Avaliação **out-of-sample**

### **3️⃣ realtime_signal.py**
Gera sinais com o melhor genoma:
- Salva em `signals_log.csv`

### **4️⃣ realtime_bot.py**
Simula trades reais baseado nos sinais:
- Salva em `trades_log.csv`

### **5️⃣ analyze_signals.py**
Analisa qualidade de cada **BUY_Y**:
- Verifica retorno do dia seguinte

### **6️⃣ analyze_results.py**
Comparará resultados com:
- **Buy & Hold**
- **Random baseline**
- **Estratégia evoluída**
- (Inclui métricas como retorno, drawdown, sharpe, nº trades)

---

## ⚙️ 5. Instalação

### **Criar ambiente virtual**
```bash
python -m venv .venv
```

### **Ativar**
Windows:
```bash
.\.venv\Scripts\Activate.ps1
```
Se der erro de política:
```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```
### **Instalar dependências**
```bash
pip install -r requirements.txt
```

---

## ▶️ 6. Como Rodar o Projeto

### **Treinar o Algoritmo Genético**
```bash
python main_ga.py
```

### **Executar o Walk-Forward**
```bash
python main_walkforward.py
```

### **Gerar sinais com o modelo treinado**
```bash
python realtime_signal.py
```

### **Gerar operações simuladas**
```bash
python realtime_bot.py
```

### **Analisar qualidade dos sinais**
```bash
python analyze_signals.py
```

### **Analisar performance da estratégia**
```bash
python analyze_results.py
```

---

## 📈 7. Exemplo de Saída

### **signals_log.csv**
Lista de todos os sinais gerados:
- Data
- Retorno de PETR4
- Parâmetros aplicados
- Sinal (BUY_Y / FLAT)

### **trades_log.csv**
Cada trade inclui:
- Preço de entrada
- Preço de saída
- Retorno
- Motivo da saída
- Capital acumulado

---

## 🎥 8. Vídeo Explicativo (Obrigatório)
📌 Link será inserido aqui após gravação.

---

## 📚 9. Referências

- Material da disciplina SSC0713  
- “Algorithms for Optimization” — Kochenderfer  
- Yahoo Finance API (`yfinance`)  
- B3  

---

## 👨‍💻 Autor
**Bruno Zuffo**  
Engenharia de Computação — ICMC/USP  
Disciplina: SSC0713 — Sistemas Evolutivos
