import click
import sys
from typing import Optional, Tuple, Dict, Any
from enum import Enum

class TestType(str, Enum):
    AUTH = "auth"
    CERT = "cert"
    DIAG = "diag"

class TestAction(str, Enum):
    RUN = "run"
    STOP = "stop"
    STATUS = "status"

class CLIParser:
    """BD2 功能测试参数解析器"""
    
    def __init__(self):
        self.parser = click.Group()
        self._add_arguments()
    
    def _add_arguments(self):
        """添加命令行参数"""
        @self.parser.command()
        @click.option('--type', '-t', type=click.Choice([t.value for t in TestType]),
                     help='测试类型 (auth/cert/diag)')
        @click.option('--action', '-a', type=click.Choice([a.value for a in TestAction]),
                     help='测试动作 (run/stop/status)')
        @click.option('--uds', is_flag=True, help='启用 UDS 日志')
        @click.option('--cs', is_flag=True, help='启用 CS 日志')
        @click.option('--level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
                     help='日志级别')
        def test(type: str, action: str, uds: bool, cs: bool, level: Optional[str]):
            """BD2 功能测试"""
            pass
    
    def parse_args(self) -> Dict[str, Any]:
        """解析命令行参数"""
        try:
            ctx = self.parser.parse_args(sys.argv[1:])
            return {
                'type': ctx.params.get('type'),
                'action': ctx.params.get('action'),
                'uds': ctx.params.get('uds', False),
                'cs': ctx.params.get('cs', False),
                'level': ctx.params.get('level'),
            }
        except click.exceptions.ClickException as e:
            print(f"Error: {e}")
            sys.exit(1)
