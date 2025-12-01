import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path


class CacheParser:
    """
    Classe para gerenciar cache de respostas de modelos de linguagem.

    Compatível com os formatos usados por CodeT e TiCoder.
    Suporta concatenação de múltiplas respostas e exportação em JSON e JSONL.
    """

    def __init__(self, cache_file: Optional[str] = None):
        """
        Inicializa o CacheParser.

        Args:
            cache_file: Caminho opcional para arquivo de cache existente (JSON ou JSONL).
                       Se fornecido, carrega os dados existentes.
        """
        self.cache: Dict[str, Any] = {}
        self.entries: List[Dict[str, Any]] = []

        if cache_file and Path(cache_file).exists():
            self._load_from_file(cache_file)

    def _load_from_file(self, file_path: str):
        """Carrega cache existente de um arquivo JSON ou JSONL."""
        with open(file_path, 'r', encoding='utf-8') as f:
            if file_path.endswith('.jsonl'):
                # Formato JSONL: uma entrada por linha
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        self.entries.append(entry)
                        # Adiciona também ao dicionário de cache
                        if 'key' in entry:
                            self.cache[str(entry['key'])] = entry
            else:
                # Formato JSON: um único objeto ou lista
                data = json.load(f)
                if isinstance(data, list):
                    self.entries = data
                    for entry in data:
                        if 'key' in entry:
                            self.cache[str(entry['key'])] = entry
                elif isinstance(data, dict):
                    self.cache = data
                    # Converte dicionário em lista de entradas
                    for key, value in data.items():
                        if isinstance(value, tuple) and len(value) >= 2:
                            # Formato do TiCoder: (key, response, timestamp)
                            self.entries.append({
                                'key': value[0],
                                'response': value[1],
                                'timestamp': value[2] if len(value) > 2 else None
                            })
                        else:
                            self.entries.append({'key': key, 'value': value})

    def add_response(self,
                     prompt: Any,
                     response: Any,
                     model: str = "gpt-4o-mini",
                     max_tokens: int = 512,
                     temperature: float = 0.8,
                     n: int = 1,
                     metadata: Optional[Dict] = None):
        """
        Adiciona uma nova resposta ao cache.

        Args:
            prompt: O prompt usado (pode ser string ou lista de mensagens)
            response: A resposta do modelo (objeto choice ou lista)
            model: Nome do modelo usado
            max_tokens: Número máximo de tokens
            temperature: Temperatura usada na geração
            n: Número de completions geradas
            metadata: Metadados adicionais opcionais
        """
        # Cria uma chave única baseada nos parâmetros
        # Formato compatível com TiCoder/CodeT
        key = (prompt, n, temperature, False, max_tokens, model, n)

        # Extrai o conteúdo da resposta
        if hasattr(response, '__iter__') and not isinstance(response, str):
            # Lista de choices
            content = []
            for choice in response:
                if hasattr(choice, 'message'):
                    content.append({
                        'content': choice.message.content,
                        'role': choice.message.role,
                        'finish_reason': choice.finish_reason if hasattr(choice, 'finish_reason') else None
                    })
                else:
                    content.append(str(choice))
        else:
            content = str(response)

        # Cria a entrada
        entry = {
            'key': {
                'prompt': prompt if isinstance(prompt, (str, list)) else str(prompt),
                'model': model,
                'max_tokens': max_tokens,
                'temperature': temperature,
                'n': n
            },
            'response': content,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'metadata': metadata or {}
        }

        # Adiciona ao cache e à lista de entradas
        key_str = str(key)
        self.cache[key_str] = entry
        self.entries.append(entry)

        return entry

    def to_json(self, output_file: str, mode: str = 'cache'):
        """
        Salva o cache em formato JSON.

        Args:
            output_file: Caminho do arquivo de saída
            mode: 'cache' para formato de dicionário (compatível com TiCoder),
                  'entries' para lista de entradas
        """
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            if mode == 'cache':
                # Formato de dicionário (compatível com TiCoder)
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
            else:
                # Formato de lista
                json.dump(self.entries, f, indent=2, ensure_ascii=False)

        print(f"Cache salvo em {output_file} ({len(self.entries)} entradas)")

    def to_jsonl(self, output_file: str):
        """
        Salva o cache em formato JSONL (uma entrada por linha).

        Args:
            output_file: Caminho do arquivo de saída
        """
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in self.entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        print(f"Cache salvo em {output_file} ({len(self.entries)} entradas)")

    def append_to_json(self, output_file: str, mode: str = 'cache'):
        """
        Adiciona novas entradas a um arquivo JSON existente.

        Args:
            output_file: Caminho do arquivo de saída
            mode: 'cache' ou 'entries'
        """
        existing_data = {}
        existing_entries = []

        # Carrega dados existentes se o arquivo existir
        if Path(output_file).exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    existing_data = data
                else:
                    existing_entries = data

        # Merge com os novos dados
        if mode == 'cache':
            existing_data.update(self.cache)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
        else:
            existing_entries.extend(self.entries)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(existing_entries, f, indent=2, ensure_ascii=False)

        total_entries = len(existing_data) if mode == 'cache' else len(existing_entries)
        print(f"Cache atualizado em {output_file} ({total_entries} entradas totais)")

    def append_to_jsonl(self, output_file: str):
        """
        Adiciona novas entradas a um arquivo JSONL existente.

        Args:
            output_file: Caminho do arquivo de saída
        """
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        # Append mode para JSONL
        with open(output_file, 'a', encoding='utf-8') as f:
            for entry in self.entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        print(f"Adicionadas {len(self.entries)} entradas em {output_file}")

    def clear(self):
        """Limpa o cache atual (mantém apenas dados já salvos)."""
        self.cache.clear()
        self.entries.clear()

    def get_entry_count(self) -> int:
        """Retorna o número de entradas no cache."""
        return len(self.entries)

    def __len__(self):
        """Retorna o número de entradas no cache."""
        return len(self.entries)

    def __repr__(self):
        """Representação string do cache."""
        return f"CacheParser({len(self.entries)} entries)"


# Funções auxiliares para compatibilidade com o formato do TiCoder
def create_cache_entry_from_choices(prompt: Any, choices: List, model: str = "gpt-4o-mini",
                                    max_tokens: int = 512, temperature: float = 0.8):
    """
    Função auxiliar para criar uma entrada de cache a partir de choices da OpenAI.

    Args:
        prompt: O prompt usado
        choices: Lista de choices retornadas pela API
        model: Nome do modelo
        max_tokens: Tokens máximos
        temperature: Temperatura usada

    Returns:
        Dicionário com a entrada formatada
    """
    parser = CacheParser()
    return parser.add_response(
        prompt=prompt,
        response=choices,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        n=len(choices)
    )
