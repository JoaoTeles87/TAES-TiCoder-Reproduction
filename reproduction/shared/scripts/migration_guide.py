"""
MIGRAÇÃO: Como usar preload_random_samples no lugar de read_json_or_jsonl_to_list

Este arquivo mostra exemplos de como migrar código existente para usar o novo
método preload_random_samples quando você precisa de amostragem determinística.
"""

import os
os.environ.setdefault("OPENAI_API_KEY", "dummy")

from data_parser import DataParser, ProgramData

# ==============================================================================
# ANTES: Carregando todo o dataset e pegando primeira amostra
# ==============================================================================

def old_way():
    mbpp_sanitized_file = "../datasets/mbpp/sanitized-mbpp.json"
    
    # Carrega todo o dataset e pega só a primeira
    data = DataParser.read_json_or_jsonl_to_list(mbpp_sanitized_file)[:1]
    prog_data = DataParser.parse_sanitized_mbpp_data(data[0])
    
    return prog_data


# ==============================================================================
# DEPOIS: Usando preload_random_samples com seed
# ==============================================================================

def new_way_single_sample():
    """Carrega UMA amostra específica usando seed"""
    mbpp_sanitized_file = "../datasets/mbpp/sanitized-mbpp.json"
    
    # Carrega 1 amostra com seed=42 (sempre a mesma amostra)
    samples, indices = DataParser.preload_random_samples(
        mbpp_sanitized_file, 
        n=1, 
        seed=42
    )
    prog_data = DataParser.parse_sanitized_mbpp_data(samples[0])
    
    print(f"Amostra selecionada: índice {indices[0]}")
    return prog_data


def new_way_multiple_samples():
    """Carrega MÚLTIPLAS amostras usando seed"""
    mbpp_sanitized_file = "../datasets/mbpp/sanitized-mbpp.json"
    
    # Carrega 5 amostras com seed=42 (sempre as mesmas 5)
    samples, indices = DataParser.preload_random_samples(
        mbpp_sanitized_file, 
        n=5, 
        seed=42
    )
    
    # Processa todas
    prog_data_list = []
    for sample, idx in zip(samples, indices):
        prog_data = DataParser.parse_sanitized_mbpp_data(sample)
        prog_data_list.append(prog_data)
        print(f"[{idx}] {prog_data.func_name}")
    
    return prog_data_list


def new_way_first_n_samples():
    """Se você realmente quer as PRIMEIRAS N amostras (sem aleatoriedade)"""
    mbpp_sanitized_file = "../datasets/mbpp/sanitized-mbpp.json"
    
    # Use read_json_or_jsonl_to_list normalmente
    data = DataParser.read_json_or_jsonl_to_list(mbpp_sanitized_file)[:5]
    
    prog_data_list = []
    for sample in data:
        prog_data = DataParser.parse_sanitized_mbpp_data(sample)
        prog_data_list.append(prog_data)
    
    return prog_data_list


# ==============================================================================
# EXEMPLO: Migração do prompt.py
# ==============================================================================

def exemplo_prompt_py_migrado():
    """
    Versão migrada do código em prompt.py
    Agora usa seed para garantir reprodutibilidade
    """
    mbpp_sanitized_file = "../datasets/mbpp/sanitized-mbpp.json"
    
    # ANTES: data = DataParser.read_json_or_jsonl_to_list(mbpp_sanitized_file)[:1]
    # DEPOIS: Usa seed para garantir sempre a mesma amostra
    SEED = 42  # Defina uma seed fixa para reprodutibilidade
    samples, indices = DataParser.preload_random_samples(
        mbpp_sanitized_file, 
        n=1, 
        seed=SEED
    )
    
    prog_data = DataParser.parse_sanitized_mbpp_data(samples[0])
    
    print(f"Usando amostra do índice {indices[0]} com seed={SEED}")
    print(f"Função: {prog_data.func_name}")
    
    # Resto do código continua igual...
    # prompt = code_prompt(prog_data)
    # choices = model.create_completion(messages=prompt, n=5)
    # etc...
    
    return prog_data


# ==============================================================================
# QUANDO USAR CADA ABORDAGEM
# ==============================================================================

def guidelines():
    """
    Diretrizes de quando usar cada método:
    
    1. Use read_json_or_jsonl_to_list + slicing [:N] quando:
       - Você quer SEMPRE as primeiras N amostras (ordem fixa)
       - Não precisa de aleatoriedade
       - Exemplo: Testes unitários com dados fixos
    
    2. Use preload_random_samples quando:
       - Você quer N amostras ALEATÓRIAS mas REPRODUZÍVEIS
       - Precisa de seed para experimentos científicos
       - Quer variar as amostras mas manter consistência (mesma seed)
       - Exemplo: Experimentos, desenvolvimento, debugging com subsets
    
    3. Use preload_random_samples sem seed quando:
       - Você quer N amostras VERDADEIRAMENTE aleatórias
       - Cada execução deve ter amostras diferentes
       - Exemplo: Data augmentation, testes de robustez
    """
    pass


if __name__ == "__main__":
    print("=" * 70)
    print("Exemplos de Migração")
    print("=" * 70)
    print()
    
    print("### 1. Uma amostra com seed")
    prog = new_way_single_sample()
    print(f"Função: {prog.func_name}\n")
    
    print("### 2. Múltiplas amostras com seed")
    progs = new_way_multiple_samples()
    print(f"Total: {len(progs)} funções\n")
    
    print("### 3. Exemplo do prompt.py migrado")
    prog = exemplo_prompt_py_migrado()
    print()
