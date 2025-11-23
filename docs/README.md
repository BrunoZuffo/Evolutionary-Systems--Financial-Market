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

### Fenótipo

É uma estratégia de trading aplicada ao histórico de PETR4 e VALE3.

# Operadores Evolutivos

## Seleção: Torneio (pressiona melhores indivíduos sem perder diversidade)

## Crossover: recombinação uniforme (mistura genética de pais)

#### Mutação: perturbação pequena nos genes (evita convergência prematura)

#### Elitismo: melhor indivíduo passa direto para próxima geração

### Fitness

Três componentes:

# Retorno total

# Penalização por drawdown

# Penalização por número excessivo de trades

O objetivo final é maximizar retorno ajustado ao risco.