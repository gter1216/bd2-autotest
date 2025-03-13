import click
import sys
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

class TestType(str, Enum):
    """测试类型"""
    AUTH = "auth"         # 认证相关
    CERT = "cert"         # 证书相关
    DIAG = "diag"         # 诊断相关

class TestCase(str, Enum):
    """具体测试用例"""
    # Auth 测试用例
    AUTH_LOGIN = "auth.login"
    AUTH_STATUS = "auth.status"
    
    # Cert 测试用例
    CERT_INIT = "cert.init"
    CERT_DEPLOY = "cert.deploy"
    CERT_REVOKE = "cert.revoke"
    CERT_STATUS = "cert.status"
    
    # Diag 测试用例
    DIAG_RUN = "diag.run"

class CLIParser:
    """BD2 功能测试参数解析器"""
    
    # BD2 特有的参数
    BD2_ARGS = {
        '--uds-log': True,      # 需要值的参数
        '--cs-log': True,       # 需要值的参数
        '--console-log': True,  # 需要值的参数
        '--log-level': True,    # 需要值的参数
        '-h': False,            # 不需要值的参数
        '--help': False         # 不需要值的参数
    }
    
    @staticmethod
    def parse_args() -> Tuple[Dict[str, Any], List[str]]:
        """解析命令行参数
        
        Returns:
            Tuple[Dict[str, Any], List[str]]: (BD2参数, pytest参数)
        """
        try:
            # 确保至少有一个参数（程序名）
            if len(sys.argv) < 2:
                CLIParser._show_help()
                sys.exit(0)

            # 初始化参数字典
            bd2_args = {
                'uds_log': False,       # UDS日志
                'cs_log': False,        # CS日志
                'console_log': False,   # 控制台日志
                'log_level': None       # 日志级别
            }
            
            # 收集 pytest 参数
            pytest_args = []

            # 解析参数
            i = 1
            while i < len(sys.argv):
                arg = sys.argv[i]
                
                # 处理帮助信息
                if arg in ['-h', '--help']:
                    CLIParser._show_help()
                    sys.exit(0)
                
                # 处理 BD2 特有参数
                if arg in CLIParser.BD2_ARGS:
                    # 检查是否需要值
                    if CLIParser.BD2_ARGS[arg]:
                        if i + 1 >= len(sys.argv):
                            click.echo(f"错误: {arg} 需要一个值")
                            sys.exit(1)
                        value = sys.argv[i + 1]

                        # 处理日志级别
                        if arg == '--log-level':
                            if value not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                                click.echo("错误: --log-level 的值必须是 DEBUG, INFO, WARNING, ERROR, 或 CRITICAL")
                                sys.exit(1)
                            bd2_args['log_level'] = value
                        # 处理需要 on/off 值的参数
                        elif arg in ['--uds-log', '--cs-log', '--console-log']:
                            if value not in ['on', 'off']:
                                click.echo(f"错误: {arg} 的值必须是 on 或 off")
                                sys.exit(1)
                            # 移除前缀并转换为字典键
                            key = arg[2:].replace('-', '_')
                            bd2_args[key] = (value == 'on')
                        
                        i += 2
                    else:
                        i += 1
                
                # 其他参数都传递给 pytest
                else:
                    pytest_args.append(arg)
                    i += 1

            return bd2_args, pytest_args

        except Exception as e:
            click.echo(f"错误: {str(e)}")
            sys.exit(1)

    @staticmethod
    def _show_help():
        """显示帮助信息"""
        click.echo("""
用法: bd2_func_test.py [BD2参数] [pytest参数]

BD2 功能测试工具

BD2 参数:
  --uds-log on|off      启用/禁用 UDS 日志
  --cs-log on|off       启用/禁用 CS 日志
  --console-log on|off  启用/禁用控制台日志
  --log-level LEVEL     设置日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  -h, --help            显示帮助信息

pytest 参数:
  支持所有 pytest 参数，例如：
  -v, --verbose          详细输出
  -s, --capture=no      不捕获输出
  -k <表达式>           按测试名称过滤
  -m <标记>             按标记过滤
  -x, --exitfirst      首次失败时停止
  --maxfail=num        失败次数达到指定值时停止
  --pdb                失败时进入调试器
  --test-path <path>   测试文件或目录路径
  -t, --type <type>    测试类型
  -c, --case <case>    测试用例
  等等...

示例:
    # 运行所有测试
    bd2_func_test.py
    
    # 运行特定测试文件，使用 BD2 参数
    bd2_func_test.py tests/test_auth.py --uds-log on --cs-log off --log-level DEBUG
    
    # 运行特定测试用例，使用 pytest 过滤
    bd2_func_test.py tests/test_auth.py -k "test_login"
    
    # 运行特定类型的测试，使用 pytest 标记
    bd2_func_test.py -m "auth"
    
    # 组合使用
    bd2_func_test.py tests/test_cert.py --uds-log on --cs-log on --log-level DEBUG -v -s --maxfail=2
""")
