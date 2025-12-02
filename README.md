# TAES-TiCoder-Reproduction

Reprodução e análise comparativa dos métodos **CodeT** e **TiCoder** para geração de código assistida por testes.

## Estrutura do Projeto

```
TAES-TiCoder-Reproduction/
├── codet/                    # Implementação original CodeT
├── ticode/                   # Implementação original TiCoder  
├── datasets/                 # Datasets MBPP compartilhados
└── reproduction/             # Experimentos de reprodução
    ├── codet/                # Contexto CodeT
    ├── ticoder/              # Contexto TiCoder
    ├── shared/               # Recursos compartilhados
    └── docs/                 # Documentação
```

## Início Rápido

### CodeT
```bash
cd reproduction/codet/simplified
python simple_codet.py
```

### TiCoder
```bash
cd reproduction/ticoder/simplified
python simple_ticoder.py
```

## Resultados

| Método | Abordagem | Acurácia (MBPP 10 tarefas) |
|--------|-----------|----------------------------|
| **CodeT** | Dual Agreement | 100% (gpt-5-nano) |
| **TiCoder** | Test-based Pruning | 80% (gpt-5-nano) |

## Documentação

- [Reprodução](reproduction/README.md) - Guia completo dos experimentos
- [CodeT](reproduction/codet/README.md) - Documentação específica CodeT
- [TiCoder](reproduction/ticoder/README.md) - Documentação específica TiCoder
- [Comparação](reproduction/docs/comparison.md) - Análise comparativa detalhada

## Licença

Reprodução para fins acadêmicos. Consulte licenças originais do CodeT e TiCoder.
