# Reproduction Experiments

Experimentos de reprodução organizados por contexto: **CodeT**, **TiCoder** e recursos **Compartilhados**.

## Estrutura

### 📂 codet/
Tudo relacionado ao método CodeT.
- `simplified/` - Implementação simplificada
- `tests/` - Testes específicos
- `cache/` - Caches de modelos
- `results/` - Resultados de experimentos
- `scripts/` - Scripts auxiliares

[Ver documentação completa →](codet/README.md)

### 📂 ticoder/
Tudo relacionado ao método TiCoder.
- `simplified/` - Implementação simplificada
- `tests/` - Testes específicos
- `cache/` - Caches de modelos
- `results/` - Resultados de experimentos

[Ver documentação completa →](ticoder/README.md)

### 📂 shared/
Recursos compartilhados entre CodeT e TiCoder.
- `utils/` - Utilitários comuns (execution, data_parser, cache_parser, etc.)
- `tests/` - Testes de infraestrutura
- `scripts/` - Scripts de geração e experimentos
- `debug/` - Ferramentas de debug

### 📂 docs/
Documentação geral e análises.
- `EXPERIMENT_REPORT_MBPP_10.md` - Relatório de experimentos
- `PRELOAD_README.md` - Guia de cache pré-carregado
- `comparison.md` - Comparação CodeT vs TiCoder

## Uso Rápido

```bash
# CodeT
cd codet/simplified && python simple_codet.py

# TiCoder
cd ticoder/simplified && python simple_ticoder.py
```

## Comparação

| Aspecto | CodeT | TiCoder |
|---------|-------|---------|
| **Método** | Dual Agreement | Test-based Pruning |
| **Acurácia** | 100% | 80% |
| **Complexidade** | Simples | Moderada |
| **Entrada** | Solutions + Tests (JSONL) | Cache unificado (JSON) |

Para análise detalhada, veja [docs/comparison.md](docs/comparison.md).
