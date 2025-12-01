import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path


class CacheParser:
    """
    Classe para processar respostas do método create_completion e converter para JSON/JSONL.

    Recebe diretamente a lista de choices retornada por Model.create_completion()
    e gerencia a conversão para diferentes formatos de saída.
    """

    def __init__(self, cache_file: Optional[str] = None):
        """
        Inicializa o CacheParser.

        Args:
            cache_file: Caminho opcional para arquivo de cache existente (JSON ou JSONL).
                       Se fornecido, carrega os dados existentes.
        """
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
            else:
                # Formato JSON: assume que é uma lista de entradas
                data = json.load(f)
                if isinstance(data, list):
                    self.entries = data
                else:
                    # Se for um dict único, adiciona como entrada
                    self.entries.append(data)

    def add_response(self, choices: List, metadata: Optional[Dict] = None):
        """
        Processa e adiciona a resposta do método create_completion.

        Args:
            choices: Lista de choices retornada por Model.create_completion()
            metadata: Metadados adicionais opcionais (ex: prompt, model, etc.)

        Returns:
            A entrada criada
        """
        # Extrai o conteúdo das choices
        responses = []
        for choice in choices:
            if hasattr(choice, 'message'):
                responses.append({
                    'content': choice.message.content,
                    'role': choice.message.role,
                    'finish_reason': getattr(choice, 'finish_reason', None)
                })
            else:
                # Fallback caso não seja o formato esperado
                responses.append({'content': str(choice)})

        # Cria a entrada
        entry = {
            'responses': responses,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'metadata': metadata or {}
        }

        # Adiciona à lista de entradas
        self.entries.append(entry)

        return entry

    def to_json(self, output_file: str):
        """
        Salva as respostas processadas em formato JSON.

        Args:
            output_file: Caminho do arquivo de saída
        """
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.entries, f, indent=2, ensure_ascii=False)

        print(f"Respostas salvas em {output_file} ({len(self.entries)} entradas)")

    def to_jsonl(self, output_file: str):
        """
        Salva as respostas processadas em formato JSONL (uma entrada por linha).

        Args:
            output_file: Caminho do arquivo de saída
        """
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in self.entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

        print(f"Respostas salvas em {output_file} ({len(self.entries)} entradas)")

    def append_to_json(self, output_file: str):
        """
        Adiciona novas entradas a um arquivo JSON existente.

        Args:
            output_file: Caminho do arquivo de saída
        """
        existing_entries = []

        # Carrega dados existentes se o arquivo existir
        if Path(output_file).exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_entries = data

        # Merge com os novos dados
        existing_entries.extend(self.entries)

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(existing_entries, f, indent=2, ensure_ascii=False)

        print(f"Respostas atualizadas em {output_file} ({len(existing_entries)} entradas totais)")

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
        """Limpa as entradas atuais."""
        self.entries.clear()

    def get_entry_count(self) -> int:
        """Retorna o número de entradas no cache."""
        return len(self.entries)

    def __len__(self):
        """Retorna o número de entradas no cache."""
        return len(self.entries)

    def __repr__(self):
        """Representação string do cache."""
        return f"CacheParser({len(self.entries)} entradas)"
