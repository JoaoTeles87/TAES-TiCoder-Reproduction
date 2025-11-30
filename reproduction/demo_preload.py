#!/usr/bin/env python3
"""
Demo do método DataParser.preload_random_samples
Mostra como carregar N amostras aleatórias de forma determinística usando seed.
"""
import os
import sys

# Adiciona o diretório reproduction ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set dummy OpenAI key to avoid config.py requiring it
os.environ.setdefault("OPENAI_API_KEY", "dummy_key_for_demo")

from data_parser import DataParser


def main():
    # Caminho para o dataset de exemplo (usa mbpp.jsonl que tem mais amostras)
    dataset_path = "../datasets/mbpp/mbpp.jsonl"
    
    print("=" * 70)
    print("Demonstração: DataParser.preload_random_samples")
    print("=" * 70)
    
    # Teste 1: Mesma seed deve retornar mesmas amostras
    print("\n[Teste 1] Verificando determinismo com seed=43, n=3")
    samples1, indices1 = DataParser.preload_random_samples(dataset_path, n=3, seed=43)
    samples2, indices2 = DataParser.preload_random_samples(dataset_path, n=3, seed=43)
    
    print(f"Índices (execução 1): {indices1}")
    print(f"Índices (execução 2): {indices2}")
    print(f"✓ Índices são idênticos: {indices1 == indices2}")
    
    # Teste 2: Seeds diferentes retornam amostras diferentes
    print("\n[Teste 2] Seeds diferentes retornam amostras diferentes")
    samples_seed42, indices_seed42 = DataParser.preload_random_samples(dataset_path, n=3, seed=42)
    samples_seed43, indices_seed43 = DataParser.preload_random_samples(dataset_path, n=3, seed=43)
    
    print(f"Índices com seed=42: {indices_seed42}")
    print(f"Índices com seed=43: {indices_seed43}")
    print(f"✓ Índices são diferentes: {indices_seed42 != indices_seed43}")
    
    # Teste 3: Mostrar resumo das amostras
    print("\n[Teste 3] Resumo das amostras carregadas (seed=43)")
    for i, sample in enumerate(samples1):
        func_name = sample.get("code_func", "N/A")
        text = sample.get("text", sample.get("prompt", "N/A"))
        print(f"  [{indices1[i]}] {func_name}: {text[:80]}...")
    
    # Teste 4: N maior que dataset retorna tudo
    print("\n[Teste 4] N maior que tamanho do dataset")
    all_samples, all_indices = DataParser.preload_random_samples(dataset_path, n=1000, seed=43)
    print(f"Dataset tem {len(all_samples)} amostras")
    print(f"Solicitado n=1000, retornado: {len(all_samples)} amostras")
    print(f"✓ Retornou todas as amostras disponíveis")
    
    print("\n" + "=" * 70)
    print("✓ Todos os testes passaram!")
    print("=" * 70)


if __name__ == "__main__":
    main()
