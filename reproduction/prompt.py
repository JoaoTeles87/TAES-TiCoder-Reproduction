import models
from data_parser import ProgramData, DataParser

def code_prompt(program_data: ProgramData) -> list[dict]:
    """
    Gera um prompt para o modelo de linguagem baseado nos dados do programa.
    
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

mbpp_sanitized_file = "../datasets/mbpp/sanitized-mbpp.json"
data = DataParser.read_json_or_jsonl_to_list(mbpp_sanitized_file)[:1]
prog_data: ProgramData = DataParser.parse_sanitized_mbpp_data(data[0])

if __name__ == "__main__":

    model = models.GPT5Nano()


    # json e jsonl de acordo com como o TiCoder e  o CodeT querem a cache. (olhar repo do CodeT)
    
    
    try:
        choices = model.create_completion(
            messages=code_prompt(prog_data),
            n = 5
        )

        for i, choice in enumerate(choices):
            print("=" * 10, f"Generated Code {i+1}", "=" * 10 + "\n\n")
            print(choice.message.content, end = "\n\n")
    except Exception as e:
        print(f"Error: {e}")


