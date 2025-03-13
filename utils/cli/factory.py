from typing import Dict, Type
from .base import BaseCLIParser
from .bd2_client_sim.cli_parser import CLIParser as ClientSimCLIParser
from .bd2_func_test.cli_parser import CLIParser as FuncTestCLIParser

class CLIParserFactory:
    _parsers: Dict[str, Type[BaseCLIParser]] = {
        'bd2_client_sim.py': ClientSimCLIParser,
        'bd2_func_test.py': FuncTestCLIParser,
    }

    @classmethod
    def get_parser(cls, script_name: str) -> BaseCLIParser:
        parser_class = cls._parsers.get(script_name)
        if not parser_class:
            raise ValueError(f"No parser found for script: {script_name}")
        return parser_class() 