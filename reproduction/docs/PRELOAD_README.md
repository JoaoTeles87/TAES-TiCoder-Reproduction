# Pre-loader de Amostras Aleatórias

## Visão Geral

Foi adicionado o método `preload_random_samples` à classe `DataParser` para carregar N amostras aleatórias de forma determinística usando uma seed.

## Método Adicionado

```python
@staticmethod
def preload_random_samples(file_path, n, seed=None):
    """
    Carrega dataset e retorna N amostras aleatórias de forma determinística por seed.

    Args:
        file_path (str): Caminho para arquivo .json ou .jsonl
        n (int): Número de amostras a retornar. Se n >= tamanho do dataset, retorna tudo.
        seed (int ou None): Seed para amostragem determinística. Recomenda-se usar int.

    Returns:
        tuple: (samples_list, indices_list) onde samples_list é a lista de itens selecionados
               e indices_list são os índices inteiros (no dataset original) escolhidos.
    """
```

## Características

- **Determinístico**: Usando a mesma seed, sempre retorna as mesmas amostras
- **Reproduzível**: Ideal para experimentos que precisam de consistência
- **Eficiente**: Usa `random.sample()` sem reposição
- **Flexível**: Se N >= tamanho do dataset, retorna todas as amostras

## Uso

### Exemplo Básico

```python
from data_parser import DataParser

# Carrega 5 amostras com seed=43
samples, indices = DataParser.preload_random_samples(
    "datasets/mbpp/mbpp.jsonl",
    n=5,
    seed=43
)

print(f"Índices selecionados: {indices}")
# Output: Índices selecionados: [39, 292, 712, 458, 120]
```

### Exemplo com Processamento

```python
from data_parser import DataParser

# Carrega amostras
samples, indices = DataParser.preload_random_samples(
    "datasets/mbpp/mbpp.jsonl",
    n=10,
    seed=42
)

# Processa cada amostra
for sample, idx in zip(samples, indices):
    prog_data = DataParser.parse_mbpp_data(sample)
    print(f"[{idx}] {prog_data.func_name}")
```

## Scripts de Demonstração

### `demo_preload.py`

Demonstra o comportamento determinístico do método com vários testes:

```bash
python3 demo_preload.py
```

### `example_usage.py`

Mostra um exemplo prático de uso integrando com o pipeline de processamento:

```bash
python3 example_usage.py
```

## Garantias

1. **Mesma seed → Mesmas amostras**: Executar com a mesma seed sempre retorna os mesmos índices
2. **Seeds diferentes → Amostras diferentes**: Seeds diferentes geram seleções diferentes
3. **N maior que dataset**: Retorna todas as amostras disponíveis
4. **Rastreabilidade**: Retorna tanto as amostras quanto seus índices originais

## Casos de Uso

- **Experimentos reproduzíveis**: Use uma seed fixa para garantir que todos os experimentos usem as mesmas amostras
- **Desenvolvimento rápido**: Teste com subconjuntos pequenos do dataset (ex: n=10, seed=42)
- **Validação cruzada**: Use seeds diferentes para criar diferentes folds
- **Debugging**: Sempre trabalhe com o mesmo subconjunto durante o debug

## Exemplo de Fluxo Completo

```python
# 1. Definir seed para reprodutibilidade
SEED = 43
N_SAMPLES = 50

# 2. Carregar amostras
samples, indices = DataParser.preload_random_samples(
    "datasets/mbpp/mbpp.jsonl",
    n=N_SAMPLES,
    seed=SEED
)

# 3. Processar amostras
results = []
for sample, idx in zip(samples, indices):
    prog_data = DataParser.parse_mbpp_data(sample)
    # ... seu processamento aqui ...
    results.append((idx, prog_data))

# 4. Salvar resultados com índices para rastreabilidade
print(f"Processados {len(results)} amostras")
print(f"Índices: {indices}")
```
