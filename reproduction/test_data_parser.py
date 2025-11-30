from data_parser import DataParser, ProgramData

def test_mbpp_parsing():
    """
    Função de teste para fazer parsing de algumas linhas do dataset MBPP.
    
    Lê as primeiras 5 linhas do arquivo mbpp.jsonl e faz o parsing,
    exibindo as informações extraídas de cada programa.
    """
    mbpp_file = "../datasets/mbpp/mbpp.jsonl"
    
    print("=" * 80)
    print("TESTE DE PARSING DO MBPP")
    print("=" * 80)
    
    try:
        # Lê os dados do arquivo MBPP
        mbpp_data = DataParser.read_json_or_jsonl_to_list(mbpp_file)
        
        # Processa apenas as primeiras 5 entradas
        for i, data in enumerate(mbpp_data[:5]):
            print(f"\n--- Programa {i+1} ---")
            print(f"Task ID: {data.get('task_id', 'N/A')}")
            print(f"Descrição: {data.get('text', 'N/A')[:100]}...")
            print(f"Número de testes: {len(data.get('test_list', []))}")
            
            # Faz o parsing
            try:
                program = DataParser.parse_mbpp_data(data)
                print(f"\n✓ Parse bem-sucedido!")
                print(f"  - Nome da função: {program.func_name}")
                print(f"  - Assinatura:\n{program.sig}")
                print(f"\n  - Contexto:\n{program.ctxt if program.ctxt else '(vazio)'}")
                print(f"\n  - Primeiro teste:\n{program.val_tests[0] if program.val_tests else 'N/A'}")
                print(f"\n  - Oracle (primeiros 300 chars):\n{program.oracle[:300]}...")
                
            except Exception as e:
                print(f"\n✗ Erro ao fazer parse: {str(e)}")
        
        print("\n" + "=" * 80)
        print("TESTE FINALIZADO")
        print("=" * 80)
        
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {mbpp_file}")
    except Exception as e:
        print(f"Erro ao ler arquivo: {str(e)}")

def test_sanitized_mbpp_parsing():
    """
    Função de teste para fazer parsing de algumas linhas do dataset MBPP sanitizado.
    
    Lê as primeiras 5 linhas do arquivo sanitized-mbpp.json e faz o parsing,
    exibindo as informações extraídas de cada programa.
    """
    mbpp_sanitized_file = "../datasets/mbpp/sanitized-mbpp.json"

    print("=" * 80)
    print("TESTE DE PARSING DO MBPP SANITIZADO")
    print("=" * 80)

    try:
        # Lê os dados do arquivo MBPP sanitizado
        mbpp_sanitized_data = DataParser.read_json_or_jsonl_to_list(mbpp_sanitized_file)

        # Processa apenas as primeiras 5 entradas
        for i, data in enumerate(mbpp_sanitized_data[:5]):
            print(f"\n--- Programa {i+1} ---")
            print(f"Descrição: {data.get('prompt', 'N/A')[:100]}...")
            print(f"Número de testes: {len(data.get('test_list', []))}")
            
            # Faz o parsing
            try:
                program = DataParser.parse_sanitized_mbpp_data(data)
                print(f"\n✓ Parse bem-sucedido!")
                print(f"  - Nome da função: {program.func_name}")
                print(f"  - Assinatura:\n{program.sig}")
                print(f"\n  - Contexto:\n{program.ctxt if program.ctxt else '(vazio)'}")
                print(f"\n  - Primeiro teste:\n{program.val_tests[0] if program.val_tests else 'N/A'}")
                print(f"\n  - Oracle (primeiros 300 chars):\n{program.oracle[:300]}...")
                
            except Exception as e:
                print(f"\n✗ Erro ao fazer parse: {str(e)}")
        
        print("\n" + "=" * 80)
        print("TESTE FINALIZADO")
        print("=" * 80)
        
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em {mbpp_sanitized_file}")
    except Exception as e:
        print(f"Erro ao ler arquivo: {str(e)}")


if __name__ == "__main__":
    test_mbpp_parsing()
    print("\n\n")
    test_sanitized_mbpp_parsing()