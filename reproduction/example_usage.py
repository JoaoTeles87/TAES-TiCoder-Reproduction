#!/usr/bin/env python3
"""
Exemplo de uso prático: Processar N amostras aleatórias do dataset
usando DataParser.preload_random_samples e parse_mbpp_data
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("OPENAI_API_KEY", "dummy_key_for_demo")

from data_parser import DataParser


def process_random_samples(dataset_path, n_samples, seed):
    """
    Carrega e processa N amostras aleatórias do dataset.
    
    Args:
        dataset_path: Caminho para o arquivo .jsonl
        n_samples: Número de amostras a processar
        seed: Seed para reprodutibilidade
    
    Returns:
        Lista de objetos ProgramData processados
    """
    # Carrega N amostras aleatórias usando o método novo
    samples, indices = DataParser.preload_random_samples(
        dataset_path, 
        n=n_samples, 
        seed=seed
    )
    
    print(f"Carregadas {len(samples)} amostras do dataset")
    print(f"Índices selecionados: {indices}")
    print()
    
    # Processa cada amostra
    processed = []
    for i, (sample, original_idx) in enumerate(zip(samples, indices)):
        print(f"[{i+1}/{len(samples)}] Processando índice {original_idx}...")
        
        # Usa o parser apropriado (MBPP neste caso)
        prog_data = DataParser.parse_mbpp_data(sample)
        processed.append(prog_data)
        
        # Mostra resumo
        print(f"  Função: {prog_data.func_name}")
        print(f"  Testes: {len(prog_data.val_tests)}")
        print()
    
    return processed


def main():
    dataset_path = "../datasets/mbpp/mbpp.jsonl"
    
    print("=" * 70)
    print("Exemplo: Processamento de amostras aleatórias com seed")
    print("=" * 70)
    print()
    
    # Processa 5 amostras com seed=42
    print("### Processando 5 amostras com seed=42")
    processed = process_random_samples(dataset_path, n_samples=5, seed=42)
    
    print("=" * 70)
    print(f"✓ Total processado: {len(processed)} programas")
    print("=" * 70)
    print()
    
    # Demonstra que executar novamente com o mesmo seed retorna as mesmas amostras
    print("### Executando novamente com seed=42 (deve retornar as mesmas amostras)")
    processed2 = process_random_samples(dataset_path, n_samples=5, seed=42)
    
    # Verifica se são as mesmas funções
    same_functions = [p1.func_name == p2.func_name 
                      for p1, p2 in zip(processed, processed2)]
    
    print("✓ Mesmas funções processadas:", all(same_functions))
    print("  Funções:", [p.func_name for p in processed])


if __name__ == "__main__":
    main()
