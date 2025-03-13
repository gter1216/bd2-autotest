#!/usr/bin/env python3
"""
BD2 功能测试工具
支持命令行调用和类调用接口
"""

import os
import sys
import pytest
import datetime
from typing import Optional, Dict, Any, List
from utils.cli.bd2_func_test.cli_parser import CLIParser
from config.config import CONFIG
from config.config import CONFIG
from utils.logger_manager import LoggerManager

# class BD2FuncTest:
#     """BD2 功能测试类"""
    
#     def __init__(self, test: Optional[str] = None, group: Optional[str] = None,
#                  run_all: bool = False, uds_log: bool = False, cs_log: bool = False,
#                  log_level: Optional[str] = None, console_log: bool = False):
#         """
#         初始化功能测试
#         :param test: 单个测试用例
#         :param group: 功能组
#         :param run_all: 是否运行所有测试
#         :param uds_log: 是否启用 UDS 日志
#         :param cs_log: 是否启用 CS 日志
#         :param log_level: 日志级别
#         :param console_log: 是否输出日志到控制台
#         """
#         self.test = test
#         self.group = group
#         self.run_all = run_all
#         self.uds_log = uds_log
#         self.cs_log = cs_log
#         self.log_level = log_level
#         self.console_log = console_log
        
#         # 设置环境变量
#         if console_log:
#             os.environ['BD2_LOG_TO_CONSOLE'] = 'true'
        
#         # 设置脚本名称
#         os.environ['BD2_SCRIPT_NAME'] = 'bd2_func_test'
        
#         # # 设置日志目录
#         # log_dir = os.path.join(os.path.dirname(__file__), 'logs', 'bd2_func_test')
#         # os.makedirs(log_dir, exist_ok=True)
#         # CONFIG.set("log.base_log_dir", log_dir)
    
#     def _get_pytest_args(self) -> List[str]:
#         """获取 pytest 命令行参数"""
#         args = []
        
#         # 添加测试文件路径
#         test_dir = os.path.join(os.path.dirname(__file__), 'bd2_func_test')
#         args.append(test_dir)
        
#         # 添加测试路径
#         if self.test:
#             args.extend(['-k', self.test])
#         elif self.group:
#             args.extend(['-k', f'^{self.group}'])
        
#         # 添加日志相关参数
#         if self.uds_log:
#             args.append('--uds-log')
#         if self.cs_log:
#             args.append('--cs-log')
#         if self.log_level:
#             args.extend(['--log-level', self.log_level])
            
#         # 创建日志目录
#         log_dir = LoggerManager.create_session_dir()
        
#         # 设置 pytest 日志文件路径
#         pytest_log_file = os.path.join(log_dir, 'pytest.log')
#         args.extend(['--log-file', pytest_log_file])
        
#         return args
    
#     def run(self) -> int:
#         """
#         运行测试
#         :return: 测试结果（0 表示成功，非 0 表示失败）
#         """
#         pytest_args = self._get_pytest_args()
#         return pytest.main(pytest_args)

def main():
    """主函数"""
    try:
        # 设置脚本名称环境变量
        os.environ['BD2_SCRIPT_NAME'] = 'bd2_func_test'
        
        # 解析命令行参数
        bd2_args, pytest_args = CLIParser.parse_args()
        
        # 设置日志配置
        if bd2_args['uds_log']:
            os.environ['BD2_UDS_LOG'] = 'true'
        if bd2_args['cs_log']:
            os.environ['BD2_CS_LOG'] = 'true'
        if bd2_args['console_log']:
            os.environ['BD2_CONSOLE_LOG'] = 'true'
        if bd2_args['log_level']:
            os.environ['BD2_LOG_LEVEL'] = bd2_args['log_level']
        
        # 创建日志目录
        log_dir = LoggerManager.create_session_dir()
        
        # 设置 pytest 日志文件路径
        pytest_log_file = os.path.join(os.path.abspath(log_dir), 'pytest.log')
        os.environ['PYTEST_LOG_FILE'] = pytest_log_file
        pytest_args.extend(['--log-file', pytest_log_file])
        
        # 运行测试
        sys.exit(pytest.main(pytest_args))
        
    except Exception as e:
        print(f"错误: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
