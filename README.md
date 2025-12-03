
# PROJETO: TiCoder-SLM (Reprodução de Paper)

## Objetivo
Replicar a lógica do paper "LLM-Based Test-Driven Interactive Code Generation", mas substituindo o Test Manager (gerador de testes) por um SLM (Small Language Model) com In-Context Learning.

## Restrições (Core Team - 2 Dias)
1. Sem Interface Gráfica (CLI apenas).
2. Dataset: HumanEval (usar apenas 20 problemas para teste rápido).
3. Stack: Python 3.10+, API Groq (ou Mock para dev), JSON para armazenamento.

## Arquitetura Simplificada
1. **Generation (Cache):** Script gera 5 variantes de código para cada problema e salva em JSON.
2. **Oracle (Simulador):** Script executa um input na "Canonical Solution" do dataset para saber a resposta correta.
3. **TiCoder Loop (Variante TICODER-OUTPUT):**
   - SLM analisa os 5 códigos.
   - SLM gera um input de teste (Few-Shot Prompting).
   - Oracle roda input -> Define Gabarito ($o'$).
   - Script elimina códigos que divergem do Gabarito ($c(i) \neq o'$).
   - **Nota:** Implementamos a variante *Assistant 3* do paper, onde o oráculo fornece o valor de saída exato, permitindo poda mais agressiva do que apenas PASS/FAIL.

## Reprodução e Comparação: TiCoder vs CodeT

Para validar a eficácia do TiCoder e compará-lo com o CodeT, realizamos experimentos controlados utilizando um subconjunto fixo do dataset MBPP.

### Metodologia



1.  **Dataset Controlado**: Selecionamos aleatoriamente 20 problemas do MBPP (`reproduction/subset_20.jsonl`) para garantir que ambos os métodos fossem avaliados nos mesmos desafios.
2.  **Cache Compartilhado**: Geramos 5 candidatos de código para cada problema usando o modelo `gpt-3.5-turbo`. Este cache foi usado tanto pelo TiCoder quanto pelo CodeT para eliminar a variabilidade da geração de código.
3.  **Parâmetros**:
    - `limit=20`: Número de problemas avaliados.
    - `tests=8`: Número de testes gerados pelo TiCoder para validar cada candidato.
    - `max_tokens=150`: Limite de tokens para geração de código e testes.

### Resultados

| Métrica | Descrição | Resultado |
| :--- | :--- | :--- |
| **Baseline (Pass@1)** | Probabilidade esperada de selecionar um candidato correto aleatoriamente do conjunto gerado (`c/n`). | **70.33%** |
| **TiCoder (Pass-Fail)** | **Oráculo Booleano**: O Oráculo (Referência) valida se o par entrada/saída do teste gerado é consistente com o gabarito (Pass/Fail), sem fornecer explicitamente o valor correto ao gerador se falhar. | **~71.0%** |
| **TiCoder (Output)** | **Oráculo Explícito**: O Oráculo fornece a saída exata esperada para uma dada entrada. O sistema poda qualquer candidato que não corresponda estritamente a este valor de saída. | **72.25%** |
| **CodeT (Consenso)** | Seleciona o candidato que pertence ao maior cluster de "consenso" (saída mais comum). | **75.83%** |

### Hipóteses finais

- **Amostragem pequena**: 20 exemplos são insuficientes para convergir
- **TiCoder cru**: mplementação específica dos autores era muito mais complexa do que o framework proposto, gerando resultados melhores 