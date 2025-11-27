# TiCoder-SLM: Otimização de Geração de Código Interativa com SLMs e In-Context Learning

Este repositório contém a implementação do projeto **TiCoder-SLM**, um estudo empírico que visa replicar e otimizar o fluxo de trabalho de geração de código guiada por testes (Test-Driven Interactive Code Generation). O projeto foca na eficiência computacional e na redução de latência ao substituir Grandes Modelos de Linguagem (LLMs) por Pequenos Modelos de Linguagem (SLMs) aprimorados com técnicas de In-Context Learning.

---

## 📄 Contexto e Motivação

O artigo original, **"LLM-Based Test-Driven Interactive Code Generation: User Study and Empirical Evaluation"**[^1], utiliza modelos massivos (GPT-3.5/4, Davinci) tanto para gerar código quanto para gerar testes e poderia ter explorado mais o uso de modelos menores. Pois foi dado prioridade a latência e custo. Além disso, o feedback apontou que o uso de In-Context Learning (ICL) foi limitado e SLMs não foram explorados como fatores de benefício para o workflow.

Além disso, no artigo original, eles usam o mesmo modelo LLM (ex: Davinci) para gerar esses testes e depois um algoritmo matemático para ranquear qual teste divide melhor os candidatos ($S_{discr}$)[^2].

### Contribuição do Projeto

A proposta deste trabalho é substituir essa geração e ranqueamento "brutos" por um **SLM instruído via Prompt Engineering (In-Context Learning)**. O SLM deve olhar os códigos e intuir qual teste desambigua, sem precisar gerar 50 testes e calcular estatísticas como no paper.

---

## 🎯 Objetivos Gerais

1. **Replicação do Workflow TiCoder**: Implementar a lógica de geração de testes discriminativos e poda de código (pruning), simulando a interação do usuário através de um oráculo automatizado baseado na solução de referência[^3].

2. **Integração de SLMs (Small Language Models)**: Demonstrar a viabilidade técnica de utilizar modelos leves (como Llama-3-8B ou Phi-3.5) para atuar como o "Gerenciador de Testes"[^4], reduzindo a dependência de APIs proprietárias de alto custo.

3. **Aplicação de In-Context Learning (ICL)**: Implementar prompts do tipo Few-Shot Chain-of-Thought para capacitar o SLM a identificar divergências lógicas entre candidatos de código e gerar inputs de teste precisos com poucas iterações.

4. **Validação em Cenário Simulado**: Avaliar a acurácia da seleção de código comparando o método proposto com um baseline aleatório, utilizando datasets de programação padrão (ex: HumanEval/MBPP).

---

## 🛠️ Arquitetura da Solução

O projeto adapta a arquitetura original do TiCoder[^5] para um ambiente de execução automatizada, dividida em três componentes principais:

### 1. Code Generator (Camada de Cache)

Responsável por fornecer o espaço de busca inicial.

- Gera $N$ candidatos de código ($C_1...C_5$) para um problema dado a partir de um prompt em linguagem natural[^6].
- Utiliza um LLM robusto (gerado previamente e cacheado) para isolar a variável de "geração" e focar o estudo na "validação".

### 2. Test Manager (SLM + In-Context Learning)

O núcleo inteligente do sistema que substitui o ranqueamento estatístico original.

- **Motor**: Um modelo SLM (Small Language Model) otimizado.
- **Lógica**: Recebe os códigos candidatos e, através de um prompt few-shot, raciocina sobre as diferenças semânticas entre eles.
- **Saída**: Gera um único teste discriminativo (Input) projetado especificamente para expor falhas nos candidatos incorretos, sem a necessidade de gerar múltiplos testes descartáveis[^7].

### 3. Simulated User (Oráculo Automatizado)

Um script que substitui a interação humana manual para permitir validação em escala[^8].

- Executa o teste gerado pelo SLM na **Solução de Referência** ($b_p$) (Ground Truth do dataset).
- Define o output da referência como a "resposta correta".
- Executa o mesmo teste nos códigos candidatos e realiza a poda (pruning) automática de qualquer candidato que não retorne o mesmo resultado da referência[^9].

---

## 📚 Referências

[^1]: Artigo original sobre geração de código interativa baseada em testes com LLMs
[^2]: Métrica de discriminação de testes
[^3]: Metodologia de validação automatizada
[^4]: Componente de gerenciamento de testes
[^5]: Arquitetura base do TiCoder
[^6]: Geração de candidatos de código
[^7]: Estratégia de teste discriminativo
[^8]: Simulação de usuário
[^9]: Processo de poda de candidatos
