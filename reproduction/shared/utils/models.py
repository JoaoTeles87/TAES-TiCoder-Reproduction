from openai import OpenAI
from dotenv import load_dotenv
from typing import Optional, List, Any

load_dotenv()

class Model:
	"""Instancia sempre um cliente OpenAI sem receber api_key ou client por argumento."""
	def __init__(self, model_name: str = "gpt-4o-mini"):
		self.client = OpenAI()
		self.model_name = model_name

	def create_completion(self, **kwargs):
		"""
		Chamada genérica para criar uma completion via chat.completions.create.
		Kwargs são repassados para a chamada do client.
		Retorna response.choices como antes.
		"""
		# extrair valores com prioridade: explicit max_tokens ou max_completion_tokens
		max_tokens = kwargs.pop("max_tokens", kwargs.pop("max_completion_tokens", 512))
        
		print(f"DEBUG: Calling OpenAI with model={self.model_name}, max_completion_tokens={max_tokens}, kwargs={kwargs.keys()}")

		# mapear para o nome esperado pelo SDK usado historicamente no projeto
		response = self.client.chat.completions.create(
			model=self.model_name,
			max_completion_tokens=max_tokens,
			**kwargs,
		)
		return response.choices


class GPT5Nano(Model):
	"""Força uso do modelo gpt-5-nano e instancia o cliente via super."""
	def __init__(self):
		super().__init__(model_name="gpt-5-nano")

	def create_completion(self, **kwargs):
		"""
		OBS:
		GPT-5 Nano não aceita 'temperature' — esse parâmetro é ignorado.
		"""
		# garantir que temperature não seja passado
		kwargs.pop("temperature", None)
		
		# Set default reasoning_effort to 'low' (minimal) if not provided
		# User requested "none" or "minimal". "low" is the standard minimal value for o1.
		if "reasoning_effort" not in kwargs:
			kwargs["reasoning_effort"] = "minimal"

		# repassar demais kwargs ao comportamento genérico
		return super().create_completion(**kwargs)


class GPT4oMini(Model):
	"""Força uso do modelo gpt-4o-mini e instancia o cliente via super."""
	def __init__(self):
		super().__init__(model_name="gpt-4o-mini")
