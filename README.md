# PROJETO: TiCoder-SLM (Reprodução de Paper)

## Objetivo
[cite_start]Replicar a lógica do paper "LLM-Based Test-Driven Interactive Code Generation" [cite: 36][cite_start], mas substituindo o Test Manager (gerador de testes) por um SLM (Small Language Model) com In-Context Learning[cite: 606].

## Restrições (Core Team - 2 Dias)
1. Sem Interface Gráfica (CLI apenas).
# PROJETO: TiCoder-SLM (Reprodução de Paper)

## Objetivo
[cite_start]Replicar a lógica do paper "LLM-Based Test-Driven Interactive Code Generation" [cite: 36][cite_start], mas substituindo o Test Manager (gerador de testes) por um SLM (Small Language Model) com In-Context Learning[cite: 606].

## Restrições (Core Team - 2 Dias)
1. Sem Interface Gráfica (CLI apenas).
2. Dataset: HumanEval (usar apenas 20 problemas para teste rápido).
3. Stack: Python 3.10+, API Groq (ou Mock para dev), JSON para armazenamento.

## Arquitetura Simplificada
1. [cite_start]**Generation (Cache):** Script gera 5 variantes de código para cada problema e salva em JSON[cite: 543].
2. [cite_start]**Oracle (Simulador):** Script executa um input na "Canonical Solution" do dataset para saber a resposta correta.
3. **TiCoder Loop (Variante TICODER-OUTPUT):**
   - SLM analisa os 5 códigos.
   - SLM gera um input de teste (Few-Shot Prompting).
   - Oracle roda input -> Define Gabarito ($o'$).
   - [cite_start]Script elimina códigos que divergem do Gabarito ($c(i) \neq o'$)[cite: 285].
   - **Nota:** Implementamos a variante *Assistant 3* do paper, onde o oráculo fornece o valor de saída exato, permitindo poda mais agressiva do que apenas PASS/FAIL.