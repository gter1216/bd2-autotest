#!/usr/bin/env python3
"""
BD2 负载测试命令行参数解析器
"""

import os
import sys
import click
from typing import Dict, Any


class CLIParser:
    """BD2 负载测试参数解析器"""
    
    @staticmethod
    def parse_args() -> Dict[str, Any]:
        """解析命令行参数
        
        Returns:
            Dict[str, Any]: 解析后的参数字典
        """
        try:
            # 确保至少有一个参数（程序名）
            if len(sys.argv) < 2:
                CLIParser._show_help()
                sys.exit(0)

            # 初始化参数字典
            args = {
                'test_cases_file': None,  # 测试用例文件
                'duration': None,         # 测试持续时间（秒）
                'uds_log': False,         # UDS日志
                'ccs_log': False,         # CCS日志
                'log_level': None         # 日志级别
            }
            
            # 处理第一个参数：必须是测试用例文件
            if sys.argv[1] in ['-h', '--help']:
                CLIParser._show_help()
                sys.exit(0)
            elif sys.argv[1].startswith('-'):
                click.echo("错误: 第一个参数必须是测试用例文件")
                sys.exit(1)
                
            # 获取工程根目录下的 bd2_load_test 文件夹
            script_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            yaml_dir = os.path.join(script_dir, 'bd2_load_test')
            yaml_file = os.path.join(yaml_dir, sys.argv[1])
            
            # 检查文件是否存在
            if not os.path.isfile(yaml_file):
                click.echo(f"错误: 测试用例文件不存在: {yaml_file}")
                sys.exit(1)
                
            args['test_cases_file'] = yaml_file
            
            # 解析可选参数
            i = 2
            while i < len(sys.argv):
                arg = sys.argv[i]
                
                # 处理帮助信息
                if arg in ['-h', '--help']:
                    CLIParser._show_help()
                    sys.exit(0)
                
                # 处理其他参数
                if arg in ['-t', '--time']:
                    if i + 1 >= len(sys.argv):
                        click.echo("错误: -t/--time 需要一个值")
                        sys.exit(1)
                    try:
                        minutes = int(sys.argv[i + 1])
                        if minutes <= 0:
                            raise ValueError()
                        args['duration'] = minutes * 60  # 转换为秒
                    except ValueError:
                        click.echo("错误: -t/--time 必须是正整数（分钟）")
                        sys.exit(1)
                    i += 2
                    
                elif arg == '--uds-log':
                    if i + 1 >= len(sys.argv):
                        click.echo("错误: --uds-log 需要一个值 (on/off)")
                        sys.exit(1)
                    value = sys.argv[i + 1]
                    if value not in ['on', 'off']:
                        click.echo("错误: --uds-log 的值必须是 on 或 off")
                        sys.exit(1)
                    args['uds_log'] = (value == 'on')
                    i += 2
                    
                elif arg == '--ccs-log':
                    if i + 1 >= len(sys.argv):
                        click.echo("错误: --ccs-log 需要一个值 (on/off)")
                        sys.exit(1)
                    value = sys.argv[i + 1]
                    if value not in ['on', 'off']:
                        click.echo("错误: --ccs-log 的值必须是 on 或 off")
                        sys.exit(1)
                    args['ccs_log'] = (value == 'on')
                    i += 2
                    
                elif arg == '--log-level':
                    if i + 1 >= len(sys.argv):
                        click.echo("错误: --log-level 需要一个值")
                        sys.exit(1)
                    value = sys.argv[i + 1]
                    if value not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                        click.echo("错误: --log-level 的值必须是 DEBUG, INFO, WARNING, ERROR, 或 CRITICAL")
                        sys.exit(1)
                    args['log_level'] = value
                    i += 2
                    
                else:
                    click.echo(f"错误: 未知的参数 '{arg}'")
                    sys.exit(1)

            return args

        except Exception as e:
            click.echo(f"错误: {str(e)}")
            sys.exit(1)

    @staticmethod
    def _show_help():
        """显示帮助信息"""
        click.echo("""
用法: bd2_load_test.py <测试用例文件> [选项]

BD2 负载测试工具

参数:
  测试用例文件            YAML格式的测试用例文件（必需）

选项:
  -t, --time <分钟>     测试持续时间（分钟）
  --uds-log on|off      启用/禁用 UDS 日志
  --ccs-log on|off      启用/禁用 CCS 日志
  --log-level LEVEL     设置日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  -h, --help            显示帮助信息

示例:
  # 基本用法（必需参数）
  bd2_load_test.py load_test_cases_001.yaml

  # 设置测试时间（例如运行 60 分钟）
  bd2_load_test.py load_test_cases_001.yaml -t 60

  # 启用 UDS 日志和 CCS 日志
  bd2_load_test.py load_test_cases_001.yaml --uds-log on --ccs-log on

  # 设置日志级别
  bd2_load_test.py load_test_cases_001.yaml --log-level DEBUG

  # 组合使用
  bd2_load_test.py load_test_cases_001.yaml -t 60 --uds-log on --ccs-log on --log-level DEBUG
""")
