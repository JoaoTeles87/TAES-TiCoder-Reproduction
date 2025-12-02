# TiCoder Context

Implementação simplificada e experimentos do método **TiCoder** (Test-Informed Code Generation).

## Método

TiCoder usa **test-based pruning** para filtrar soluções:
1. Gera múltiplas soluções de código
2. Gera múltiplos testes
3. Filtra códigos que não passam nos testes gerados
4. Seleciona melhor código entre os que restaram (ordenados por consenso)

## Estrutura

```
ticoder/
├── simplified/
│   └── simple_ticoder.py        # Implementação simplificada
├── tests/
│   ├── test_ticoder.py          # Testes principais
│   └── test_ticoder_serialization.py
├── cache/
│   ├── ticoder_cache.json       # Cache gpt-5-nano
│   └── ticoder_cache_gpt4o_mini.json
└── results/
    ├── ticoder_results.json
    ├── simple_ticoder_results_ticoder_cache.json
    └── simple_ticoder_results_ticoder_cache_gpt4o_mini.json
```

## Uso

```bash
cd simplified

# Com cache padrão (gpt-5-nano)
python simple_ticoder.py

# Com cache específico
python simple_ticoder.py --cache_file ../cache/ticoder_cache_gpt4o_mini.json
```

## Resultados

- **gpt-5-nano**: 80% acurácia (8/10 tarefas)
- **GPT-4o mini**: 60% acurácia (6/10 tarefas)

## Arquivos de Entrada

- `cache/ticoder_cache.json` - Cache unificado (código + testes)
- `../../../datasets/mbpp/sanitized-mbpp.json` - Ground truth

## Arquivos de Saída

- `results/simple_ticoder_results_*.json` - Resultados detalhados por tarefa

## Diferenças vs CodeT

| Aspecto | TiCoder | CodeT |
|---------|---------|-------|
| **Entrada** | Cache JSON unificado | JSONL separados |
| **Filtro** | Remove códigos ruins | Seleciona por consenso |
| **Acurácia** | 80% | 100% |
| **Complexidade** | Maior | Menor |

## Dependências

- `shared/utils/execution.py` - Execução segura de código
- `tqdm` - Barra de progresso
- Ground truth MBPP

## Próximos Passos

1. Experimente com diferentes caches
2. Compare com CodeT: `cd ../codet/simplified`
3. Veja análise completa: `../docs/comparison.md`
