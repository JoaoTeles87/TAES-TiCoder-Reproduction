import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class CacheParser:
    """
    Processa respostas do metodo create_completion e salva no formato de cache usado pelo TiCoder.

    O formato final do JSON segue o que o TiCoder persiste em config.codex_query_response_log:
      { str(k): [k, response, timestamp] }
    onde k e um tuple com informacoes da chamada e response contem a estrutura da ChatCompletion.
    """

    def __init__(self, cache_file: Optional[str] = None):
        self.entries: Dict[str, List[Any]] = {}

        if cache_file and Path(cache_file).exists():
            self._load_from_file(cache_file)

    def _load_from_file(self, file_path: str):
        """Carrega cache existente de um arquivo JSON ou JSONL."""
        loaded: Any = None
        with open(file_path, "r", encoding="utf-8") as f:
            if file_path.endswith(".jsonl"):
                tmp: Dict[str, List[Any]] = {}
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    if isinstance(record, dict) and "key" in record and "value" in record:
                        tmp[str(record["key"])] = self._normalize_entry(record["value"])
                loaded = tmp
            else:
                loaded = json.load(f)

        if isinstance(loaded, dict):
            self.entries = {str(k): self._normalize_entry(v) for k, v in loaded.items()}
        elif isinstance(loaded, list):
            normalized: Dict[str, List[Any]] = {}
            for idx, entry in enumerate(loaded):
                normalized[str(idx)] = self._normalize_entry(entry)
            self.entries = normalized
        else:
            self.entries = {}

    def _normalize_entry(self, entry: Any) -> List[Any]:
        """Garante que uma entrada siga [k, response, timestamp] com response serializavel."""
        if isinstance(entry, list) and len(entry) == 3:
            key_part, response_part, ts_part = entry
            return [key_part, self._normalize_response(response_part), ts_part]
        return [None, self._normalize_response(entry), datetime.now().strftime("%Y-%m-%d %H:%M:%S")]

    def _normalize_response(self, response: Any) -> Dict[str, Any]:
        """
        Converte uma resposta (objeto OpenAI, dict ou lista de choices) para dict serializavel
        com os campos usados pelo TiCoder.
        """
        if isinstance(response, dict):
            choices = response.get("choices", response.get("responses"))
            if choices is not None:
                response["choices"] = [self._serialize_choice(ch, idx) for idx, ch in enumerate(choices)]
            response.setdefault("usage", {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
            return response

        if isinstance(response, list):
            choices = [self._serialize_choice(ch, idx) for idx, ch in enumerate(response)]
            return {
                "id": None,
                "object": "chat.completion",
                "created": int(time.time()),
                "model": None,
                "choices": choices,
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }

        return {
            "id": None,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": None,
            "choices": [self._serialize_choice(response, 0)],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    def _serialize_choice(self, choice: Any, idx: int) -> Dict[str, Any]:
        """Serializa um objeto Choice do OpenAI em um dict simples."""
        if isinstance(choice, dict):
            finish_reason = choice.get("finish_reason")
            message = choice.get("message", {})
            role = message.get("role")
            content = message.get("content")
        else:
            finish_reason = getattr(choice, "finish_reason", None)
            message = getattr(choice, "message", None)
            role = getattr(message, "role", None) if message else None
            content = getattr(message, "content", None) if message else str(choice)

        return {
            "index": getattr(choice, "index", idx),
            "finish_reason": finish_reason,
            "message": {
                "role": role,
                "content": content,
            },
        }

    def _stringify_prompt(self, prompt: Any) -> str:
        """Transforma o prompt (list[dict], str, etc.) em string para exportacao CodeT."""
        if isinstance(prompt, list):
            parts: List[str] = []
            for item in prompt:
                if isinstance(item, dict):
                    content = item.get("content")
                    if content is not None:
                        parts.append(str(content))
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        if prompt is None:
            return ""
        return str(prompt)

    def _extract_choice_content(self, choice: Any) -> str:
        """Extrai apenas o texto de um choice para exportacao CodeT."""
        if isinstance(choice, dict):
            message = choice.get("message") or {}
            if "content" in message and message["content"] is not None:
                return str(message["content"])
            if "content" in choice and choice["content"] is not None:
                return str(choice["content"])
            return str(choice)

        message = getattr(choice, "message", None)
        if message and getattr(message, "content", None) is not None:
            return str(message.content)
        if hasattr(choice, "content") and getattr(choice, "content") is not None:
            return str(getattr(choice, "content"))
        return str(choice)

    def _build_codet_record(self, choices: List[Any], prompt: Any) -> Dict[str, Any]:
        """Gera um registro no formato esperado pelo CodeT."""
        return {
            "prompt": self._stringify_prompt(prompt),
            "samples": [self._extract_choice_content(ch) for ch in choices],
        }

    def add_response(
        self,
        choices: List[Any],
        prompt: Optional[Any] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        echo: bool = False,
        usage: Optional[Dict[str, int]] = None,
        metadata: Optional[Dict] = None,
    ) -> List[Any]:
        """
        Processa e adiciona a resposta no formato de cache do TiCoder.

        Args:
            choices: Lista de choices retornada por Model.create_completion()
            prompt: Prompt usado na chamada (list[dict] ou str) para compor a chave do cache
            max_tokens: Limite de tokens usado na geracao
            temperature: Temperatura usada na geracao
            model: Nome do modelo usado na geracao
            echo: Flag echo usada na geracao (default False)
            usage: Dicionario opcional de uso de tokens
            metadata: Metadados adicionais opcionais

        Returns:
            A entrada criada no formato [k, response, timestamp]
        """
        max_suggestions = len(choices)
        key_tuple: Tuple[Any, ...] = (
            prompt,
            max_suggestions,
            temperature,
            echo,
            max_tokens,
            model,
            max_suggestions,
        )
        response_dict = {
            "id": None,
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [self._serialize_choice(ch, idx) for idx, ch in enumerate(choices)],
            "usage": usage or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "metadata": metadata or {},
        }

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = [list(key_tuple), response_dict, timestamp]

        self.entries[str(key_tuple)] = entry
        return entry

    def _read_existing_json(self, output_file: str) -> Dict[str, List[Any]]:
        """Le um JSON existente e o normaliza para o formato interno de entries."""
        if not Path(output_file).exists():
            return {}

        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return {str(k): self._normalize_entry(v) for k, v in data.items()}
        if isinstance(data, list):
            return {str(idx): self._normalize_entry(v) for idx, v in enumerate(data)}
        return {}

    def to_json(self, output_file: str):
        """
        Salva as respostas processadas em formato JSON (um dict de entradas).
        Se o arquivo existir, ele sera sobrescrito.
        """
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, indent=2, ensure_ascii=False)

        print(f"Respostas salvas em {output_file} ({len(self.entries)} entradas)")

    def to_jsonl(self, output_file: str):
        """
        Salva as respostas processadas em formato JSONL (uma entrada por linha).
        Cada linha contem {\"key\": str(k), \"value\": [k, response, timestamp]}.
        """
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            for key, value in self.entries.items():
                f.write(json.dumps({"key": key, "value": value}, ensure_ascii=False) + "\n")

        print(f"Respostas salvas em {output_file} ({len(self.entries)} entradas)")

    def append_to_json(self, output_file: str):
        """
        Adiciona novas entradas a um arquivo JSON existente, preservando o formato do TiCoder.
        """
        existing_entries = self._read_existing_json(output_file)
        existing_entries.update(self.entries)

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(existing_entries, f, indent=2, ensure_ascii=False)

        print(f"Respostas atualizadas em {output_file} ({len(existing_entries)} entradas totais)")

    def append_to_jsonl(self, output_file: str):
        """
        Adiciona novas entradas a um arquivo JSONL existente.
        """
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "a", encoding="utf-8") as f:
            for key, value in self.entries.items():
                f.write(json.dumps({"key": key, "value": value}, ensure_ascii=False) + "\n")

        print(f"Adicionadas {len(self.entries)} entradas em {output_file}")

    def save_codet_jsonl(self, choices: List[Any], prompt: Any, output_file: str):
        """Salva choices no formato CodeT (prompt + samples) em JSONL."""
        record = self._build_codet_record(choices, prompt)
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        print(f"Resposta CodeT adicionada em {output_file}")

    def save_codet_json(self, choices: List[Any], prompt: Any, output_file: str):
        """Salva choices no formato CodeT (prompt + samples) em JSON."""
        record = self._build_codet_record(choices, prompt)
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        existing: List[Dict[str, Any]] = []
        if Path(output_file).exists():
            try:
                with open(output_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    existing = data
                elif isinstance(data, dict):
                    existing = [data]
            except Exception:
                existing = []

        existing.append(record)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)

        print(f"Respostas CodeT salvas em {output_file} ({len(existing)} entradas)")

    def clear(self):
        """Limpa as entradas atuais."""
        self.entries.clear()

    def get_entry_count(self) -> int:
        """Retorna o numero de entradas no cache."""
        return len(self.entries)

    def __len__(self):
        """Retorna o numero de entradas no cache."""
        return len(self.entries)

    def __repr__(self):
        """Representacao string do cache."""
        return f"CacheParser({len(self.entries)} entradas)"
