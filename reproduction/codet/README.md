# CodeT Context

Implementação simplificada e experimentos do método **CodeT** (Code-Test Dual Agreement).

## Método

CodeT usa **dual agreement** entre soluções e testes gerados:
1. Gera múltiplas soluções de código
2. Gera múltiplos testes
3. Executa matriz: soluções × testes
4. Seleciona solução que passa no maior número de testes (consenso)

## Estrutura

```
codet/
├── simplified/
│   └── simple_codet.py          # Implementação simplificada
├── tests/
│   ├── test_codet.py            # Testes principais
│   ├── test_codet_execution.py  # Testes de execução
│   └── test_codet_serialization.py
├── cache/
│   ├── codet_output/            # Cache gpt-5-nano
│   ├── codet_output_gpt4o_mini/ # Cache GPT-4o mini
│   └── codet_test_output/       # Cache de testes
├── results/
│   └── simple_codet_results_*.json
└── scripts/
    └── inspect_codet.py         # Inspeção de resultados
```

## Uso

```bash
cd simplified

# Com cache padrão (gpt-5-nano)
python simple_codet.py

# Com cache específico
python simple_codet.py --input_dir ../cache/codet_output_gpt4o_mini
```

## Resultados

- **gpt-5-nano**: 100% acurácia (10/10 tarefas)
- **GPT-4o mini**: 90% acurácia (9/10 tarefas)

## Arquivos de Entrada

- `cache/codet_output/solutions.jsonl` - Soluções geradas
- `cache/codet_output/tests.jsonl` - Testes gerados
- `../../../datasets/mbpp/sanitized-mbpp.json` - Ground truth

## Arquivos de Saída

- `results/simple_codet_results_*.json` - Resultados detalhados por tarefa

## Dependências

- `shared/utils/execution.py` - Execução segura de código
- `tqdm` - Barra de progresso
- Ground truth MBPP

## Próximos Passos

1. Experimente com diferentes caches
2. Compare com TiCoder: `cd ../ticoder/simplified`
3. Veja análise completa: `../docs/comparison.md`
