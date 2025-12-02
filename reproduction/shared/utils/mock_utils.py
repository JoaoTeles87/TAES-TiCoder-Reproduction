from unittest.mock import MagicMock

# --- TiCoder Style Mocks (OpenAI Object Mocks) ---

def create_mock_openai_response(content):
    """Creates a mock ChatCompletion object similar to what the OpenAI API returns."""
    from openai.types.chat import ChatCompletion, ChatCompletionMessage
    from openai.types.chat.chat_completion import Choice, CompletionUsage
    
    msg = ChatCompletionMessage(content=content, role="assistant")
    choice = Choice(finish_reason="stop", index=0, message=msg)
    usage = CompletionUsage(completion_tokens=10, prompt_tokens=10, total_tokens=20)
    response = ChatCompletion(id="chatcmpl-mock", choices=[choice], created=1234567890, model="gpt-4", object="chat.completion", usage=usage)
    return response

# --- CodeT Style Mocks (Custom Model Wrapper Mocks) ---

class MockChoice:
    def __init__(self, content, index=0):
        self.message = MagicMock()
        self.message.content = content
        self.finish_reason = "stop"
        self.index = index

class MockResponse:
    def __init__(self, choices):
        self.choices = choices

class MockModel:
    def __init__(self, model_name="gpt-5-nano"):
        self.model_name = model_name

    def create_completion(self, **kwargs):
        n = kwargs.get('n', 1)
        choices = []
        for i in range(n):
            choices.append(MockChoice(f"def solution():\n    return 'solution_{i}'", index=i))
        return choices
