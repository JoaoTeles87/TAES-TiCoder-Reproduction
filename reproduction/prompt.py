import sys
import os

# Add src to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import models
import cache_parser
from data_parser import ProgramData, DataParser
import config

def code_prompt(program_data: ProgramData) -> list[dict]:
    """
    Gera um prompt de geração de código para o modelo de linguagem baseado nos dados do programa.
    
    Args:
        program_data (ProgramData): Dados estruturados do programa
    
    Returns:
        str: Prompt formatado para o modelo de linguagem
    """


    prompt_text = f"Complete the following Python function:\n\n{program_data.sig}\n\n"
    prompt_text += "Do not explain the function, just complete the function.\n"
    prompt_text += "Do not surround the code with any markdown formatting.\n"
    prompt = [
        {
            "role": "system",
            "content": "Suppose you are a code completion engine. You are asked to complete the following Python function. " +
            "The function signature is given below. The context of the function is also provided. Complete the function. "
        },
        {
            "role": "user",
            "content": prompt_text
        }
    ]
    return prompt

def test_prompt(program_data: ProgramData) -> list[dict]:
    """
    Gera um prompt de geração de testes para o modelo de linguagem baseado nos dados do programa.
    
    Args:
        program_data (ProgramData): Dados estruturados do programa
    
    Returns:
        str: Prompt formatado para o modelo de linguagem
    """
    prompt = [
        {
            "role": "system",
            "content": "Suppose you are a code completion engine. You are asked to generate tests for test driven development of a Python function. \n" +
            "You will be given a function which contains the description. \n" +
            "You need to generate tests for the function. "
        }
    ]
    prompt_text = (f"Context of the function is :\n\n{program_data.ctxt}\n\n" +
    f"The functions is defined as follows:\n\n{program_data.sig}\n\n" +
    f"Generate a test code for the function containing assersions. \n" +
    f"Start the test code with: \n\ndef {config.TEST_PREFIX}{program_data.func_name}():\n\tassert {program_data.func_name} (\n\n\n" +
    f"Do not explain the test code, just generate it. Do not call the test code.\n" +
    f"Do not write any standalone asserts.\n" +
    "The test code should contain only one assertion for the function. \n")

    prompt.append(
        {
            "role": "user",
            "content": prompt_text
        }
    )
    return prompt

mbpp_sanitized_file = os.path.join(os.path.dirname(__file__), "../datasets/mbpp/sanitized-mbpp.json")
data = DataParser.read_json_or_jsonl_to_list(mbpp_sanitized_file)[:1]
prog_data: ProgramData = DataParser.parse_sanitized_mbpp_data(data[0])

if __name__ == "__main__":

    model = models.GPT5Nano()
    cache = cache_parser.CacheParser()

    # json e jsonl de acordo com como o TiCoder e  o CodeT querem a cache. (olhar repo do CodeT)
    
    try:
        choices = model.create_completion(
            messages=test_prompt(prog_data),
            n = 3,
            max_tokens=4000,
            reasoning_effort="low"
        )

        for i, choice in enumerate(choices):
            print("=" * 30, f"Generated Code {i+1}", "=" * 30 + "\n\n")
            print(choice.message.content, end = "\n\n")

        cache.add_response(choices)
        cache.append_to_json("mika.json")
        cache.append_to_jsonl("mika.jsonl")
        # cache.to_json("mika.json") #cria o json e caso exista, limpa todo o json e adiciona os dados
        # cache.to_jsonl("mika.jsonl") #cria o jsonl e caso exista, limpa todo o json e adiciona os dados

    except Exception as e:
        print(f"Error: {e}")


