import sys
from utils.cli.bd2_client_sim.cli_parser import CLIParser as ClientSimCLIParser
from utils.cli.bd2_func_test.cli_parser import CLIParser as FuncTestCLIParser
from utils.cli.factory import CLIParserFactory

class CLIParser:
    @staticmethod
    def parse_args():
        # 根据脚本名称自动选择正确的解析器
        script_name = sys.argv[0].split('/')[-1]
        parser = CLIParserFactory.get_parser(script_name)
        return parser.parse_args()

# 导出与原来相同的接口
__all__ = ['CLIParser'] 