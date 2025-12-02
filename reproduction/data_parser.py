import json
import re
import random
import sys
sys.path.insert(0, '../src')

import config
from config import debug_print


class ProgramData:
    """
    Classe que representa os dados de um programa/função.
    
    Atributos:
        ctxt (str): Contexto ou código anterior à função
        sig (str): Assinatura da função (def nome(...):)
        func_name (str): Nome da função
        val_tests (list): Lista de testes de validação
        oracle (str): Código correto da função (implementação de referência)
    """
    
    def __init__(self, ctxt="", sig="", func_name="", val_tests=None, oracle=""):
        """
        Inicializa um objeto ProgramData.
        
        Args:
            ctxt (str): Contexto do programa. Padrão: ""
            sig (str): Assinatura da função. Padrão: ""
            func_name (str): Nome da função. Padrão: ""
            val_tests (list): Testes de validação. Padrão: None
            oracle (str): Implementação correta. Padrão: ""
        """
        self.ctxt = ctxt
        self.sig = sig
        self.func_name = func_name
        self.val_tests = val_tests if val_tests is not None else []
        self.oracle = oracle
    
    def to_dict(self):
        """
        Converte o objeto ProgramData para dicionário.
        
        Returns:
            dict: Dicionário contendo todos os atributos do objeto
        """
        return {
            "ctxt": self.ctxt,
            "sig": self.sig,
            "func_name": self.func_name,
            "val_tests": self.val_tests,
            "oracle": self.oracle
        }
    
    def __repr__(self):
        """
        Representação em string do objeto ProgramData.
        
        Returns:
            str: String representando o objeto
        """
        return (f"ProgramData(func_name='{self.func_name}', "
                f"ctxt_len={len(self.ctxt)}, "
                f"tests={len(self.val_tests)})")


class DataParser:
    """
    Classe responsável por fazer parsing de dados de diferentes formatos
    de datasets (HumanEval, MBPP, etc).
    """
    
    @staticmethod
    def create_validation_tests(test_bodies, func_name):
        """
        Cria testes de validação formatados com prefixo de teste.
        
        Args:
            test_bodies (list): Lista com os corpos dos testes
            func_name (str): Nome da função a ser testada
        
        Returns:
            list: Lista de testes formatados com função test_<func_name>
        """
        return [
            "def " + config.TEST_PREFIX + func_name + "():\n\t" + test_body
            for test_body in test_bodies
        ]
    
    @staticmethod
    def read_json_or_jsonl_to_list(file_path):
        """
        Lê um arquivo JSON ou JSONL e retorna como lista de dicionários.
        
        Args:
            file_path (str): Caminho do arquivo (.json ou .jsonl)
        
        Returns:
            list: Lista de dicionários contendo os dados do arquivo
        """
        if file_path.endswith(".jsonl"):
            with open(file_path, "r", encoding="utf-8-sig") as f:
                return [json.loads(line) for line in f if line.strip()]
        else:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                return json.load(f)
    
    @staticmethod
    def preload_random_samples(file_path, n, seed=None):
        """
        Carrega dataset e retorna N amostras aleatórias de forma determinística por seed.
        
        Args:
            file_path (str): Caminho para arquivo .json ou .jsonl
            n (int): Número de amostras a retornar. Se n >= tamanho do dataset, retorna tudo.
            seed (int ou None): Seed para amostragem determinística. Recomenda-se usar int.
        
        Returns:
            tuple: (samples_list, indices_list) onde samples_list é a lista de itens selecionados
                   e indices_list são os índices inteiros (no dataset original) escolhidos.
        """
        data = DataParser.read_json_or_jsonl_to_list(file_path)
        total = len(data)
        if n >= total:
            return data, list(range(total))
        
        rng = random.Random(seed)
        # Amostragem de índices sem reposição de forma determinística para o seed dado
        indices = rng.sample(range(total), n)
        samples = [data[i] for i in indices]
        return samples, indices
    
    @staticmethod
    def parse_func_code(data):
        """
        Extrai o nome e assinatura da função a partir do código.
        
        Args:
            data (dict): Dicionário contendo a chave 'code' com código-fonte
        
        Returns:
            tuple: (func_name, func_sig) - Nome da função e sua assinatura
        
        Raises:
            AssertionError: Se houver múltiplas funções sob teste
        """
        # Encontra todas as declarações 'def' e seus nomes
        def_stmts = re.findall(r".*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", data["code"])
        def_stmts = dict.fromkeys(def_stmts)
        num = len(def_stmts)
        func_name = None
        
        # Se houver lista de testes, usa para identificar a função principal
        if "test_list" in data:
            test_functions = str(data["test_list"])
            for stmt in def_stmts.keys():
                if test_functions.find(stmt) != -1:
                    if func_name is None:
                        func_name = stmt
                    else:
                        assert (
                            False
                        ), f"Multiple functions under test: {func_name} and {stmt}"
        else:
            # Caso contrário, assume a última função definida
            func_name = def_stmts[num - 1]
        
        # Extrai a assinatura da função (argumentos e parênteses)
        args = re.findall(r".*def\s+" + func_name + r"(\s*\(.*\)\s*):", data["code"])
        func_sig = args[0] if len(args) > 0 else ""
        return func_name, func_sig
    
    @staticmethod
    def get_func_details(data):
        """
        Obtém detalhes da função (nome, assinatura, corpo/oracle).
        
        Se os dados contêm as chaves code_func, code_sig e code_body,
        usa-as diretamente. Caso contrário, faz parsing do código.
        
        Args:
            data (dict): Dicionário com informações da função
        
        Returns:
            tuple: (func_name, func_sig, oracle) - Nome, assinatura e código correto
        """
        # Verifica se data possui estrutura pré-processada
        if "code_func" in data:
            func_name = data["code_func"]
            func_sig = data["code_sig"]
            oracle_body = data["code_body"]
            oracle = "def " + func_name + func_sig + ":" + oracle_body
        else:
            # Faz parsing direto do código
            func_name, func_sig = DataParser.parse_func_code(data)
            oracle = data["code"]
            #print(f"func_name = {func_name}, func_sig = {func_sig}")
        
        return func_name, func_sig, oracle
    
    @staticmethod
    def parse_human_eval_data(data) -> ProgramData:
        """
        Faz parsing de dados do dataset HumanEval.
        
        Args:
            data (dict): Dicionário com dados do HumanEval
                Esperado: 'prompt', 'entry_point', 'test', 'canonical_solution'
        
        Returns:
            ProgramData: Objeto contendo dados estruturados do programa
        """
        sig = data["prompt"]
        
        return ProgramData(
            ctxt="",
            sig=sig,
            func_name=data["entry_point"],
            val_tests=[data["test"]],
            oracle=sig + data["canonical_solution"]
        )
    
    @staticmethod
    def parse_mbpp_data(data) -> ProgramData:
        """
        Faz parsing de dados do dataset MBPP.
        
        Args:
            data (dict): Dicionário com dados do MBPP
                Esperado: 'text', 'code', 'code_func', 'code_sig', 'code_body', 'test_list'
        
        Returns:
            ProgramData: Objeto contendo dados estruturados do programa
        
        Raises:
            AssertionError: Se não encontrar a função no código
        """
        func_docstring = data["text"]
        func_name, func_sig, oracle = DataParser.get_func_details(data)
        debug_print(f'"""{func_docstring}"""')
        assert len(data["code"].split("def " + func_name + func_sig + ":")) > 1
        
        ctxt = data["code"].split("def " + func_name + func_sig + ":")[0]
        sig = (
            "def " + func_name + func_sig + ':\n\t"""' + func_docstring + '"""'
        )
        val_tests = DataParser.create_validation_tests(data["test_list"], func_name)
        
        return ProgramData(
            ctxt=ctxt,
            sig=sig,
            func_name=func_name,
            val_tests=val_tests,
            oracle=oracle
        )
    
    @staticmethod
    def parse_sanitized_mbpp_data(data) -> ProgramData:
        """
        Faz parsing de dados do dataset MBPP sanitizado.
        
        Args:
            data (dict): Dicionário com dados do MBPP sanitizado
                Esperado: 'prompt', 'code', 'code_func', 'code_sig', 'code_body', 'test_list'
        
        Returns:
            ProgramData: Objeto contendo dados estruturados do programa
        
        Raises:
            AssertionError: Se não encontrar a função no código
        """
        func_docstring = data["prompt"]
        func_name, func_sig, oracle = DataParser.get_func_details(data)
        debug_print(f'"""{func_docstring}"""')
        assert len(data["code"].split("def " + func_name + func_sig + ":")) > 1
        
        ctxt = data["code"].split("def " + func_name + func_sig + ":")[0]
        sig = (
            "def " + func_name + func_sig + ':\n\t"""' + func_docstring + '"""'
        )
        val_tests = DataParser.create_validation_tests(data["test_list"], func_name)
        
        return ProgramData(
            ctxt=ctxt,
            sig=sig,
            func_name=func_name,
            val_tests=val_tests,
            oracle=oracle
        )
