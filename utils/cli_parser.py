import argparse
import logging
import sys
from argparse import ArgumentParser, Namespace
from io import StringIO
import contextlib

class CustomArgumentParser(ArgumentParser):
    """自定义的参数解析器，重写错误处理方法"""
    
    def error(self, message):
        """重写错误处理方法，只显示错误信息"""
        # 获取当前命令的上下文
        task_type = None
        action = None
        if len(sys.argv) > 1:
            task_type = sys.argv[1]
        if len(sys.argv) > 2:
            action = sys.argv[2]

        # 只显示错误信息和简单的用法提示
        if not task_type:
            print(f"\n错误: {message}")
            print("\n用法: %(prog)s <task_type> <action> [<args>]" % {"prog": self.prog})
            print("\n可用的任务类型: auth, cert, diag")
            print("使用 -h 或 --help 查看详细帮助信息")
        elif task_type in ["auth", "cert", "diag"]:
            if not action:
                print(f"\n错误: {message}")
                print(f"\n用法: %(prog)s {task_type} <action> [<args>]" % {"prog": self.prog})
                print("\n使用 -h 或 --help 查看详细帮助信息")
            else:
                print(f"\n错误: {message}")
                print(f"\n使用 -h 或 --help 查看详细帮助信息")
        else:
            print(f"\n错误: {message}")
            print("\n用法: %(prog)s <task_type> <action> [<args>]" % {"prog": self.prog})
            print("\n可用的任务类型: auth, cert, diag")
            print("使用 -h 或 --help 查看详细帮助信息")

        if sys.gettrace() is not None:  # 调试模式
            return
        else:
            sys.exit(2)

class CLIParser:
    """BD2 客户端模拟器的命令行解析器"""

    @staticmethod
    def _show_command_help(parser: ArgumentParser, command_type: str = None, action: str = None):
        """显示指定命令的帮助信息"""
        if command_type == "auth":
            if action == "login":
                print("\n登录命令示例:")
                print("  python bd2_client_sim.py auth login --log-level DEBUG")
            elif action == "logout":
                print("\n登出命令示例:")
                print("  python bd2_client_sim.py auth logout --log-level DEBUG")
            else:
                print("\n认证命令示例:")
                print("  python bd2_client_sim.py auth login --log-level DEBUG")
                print("  python bd2_client_sim.py auth logout")
        elif command_type == "cert":
            if action == "deploy":
                print("\n证书部署命令示例:")
                print("  python bd2_client_sim.py cert deploy -e vdf")
                print("  python bd2_client_sim.py cert deploy -e all --log-level DEBUG")
            elif action == "revoke":
                print("\n证书撤销命令示例:")
                print("  python bd2_client_sim.py cert revoke -i cert123")
            elif action == "refresh":
                print("\n证书刷新命令示例:")
                print("  python bd2_client_sim.py cert refresh -i cert123 -d newdata")
            else:
                print("\n证书管理命令示例:")
                print("  python bd2_client_sim.py cert deploy -e vdf")
                print("  python bd2_client_sim.py cert revoke -i cert123")
                print("  python bd2_client_sim.py cert refresh -i cert123 -d newdata")
        elif command_type == "diag":
            if action == "run":
                print("\n诊断运行命令示例:")
                print("  python bd2_client_sim.py diag run -c 0x1234")
            else:
                print("\n诊断命令示例:")
                print("  python bd2_client_sim.py diag run -c 0x1234")
        else:
            print("\n常用命令示例:")
            print("  python bd2_client_sim.py auth login --log-level DEBUG")
            print("  python bd2_client_sim.py cert deploy -e vdf")
            print("  python bd2_client_sim.py diag run -c 0x1234")
        print()

    @staticmethod
    def _show_error_and_help(parser: ArgumentParser, error_msg: str = None):
        """显示错误信息和帮助信息"""
        # 清除屏幕上的重复信息
        if error_msg:
            print(f"\n错误: {error_msg}")
        
        # 获取当前命令的上下文
        task_type = None
        action = None
        if len(sys.argv) > 1:
            task_type = sys.argv[1]
        if len(sys.argv) > 2:
            action = sys.argv[2]

        # 根据命令上下文显示相应的帮助信息
        if not task_type:
            parser.print_help()
        elif task_type in ["auth", "cert", "diag"]:
            # 获取对应的子解析器
            subparser = next((p for p in parser._subparsers._group_actions[0].choices.values() 
                            if p.prog.split()[-1] == task_type), None)
            if subparser:
                if not action:
                    subparser.print_help()
                else:
                    # 获取操作的子解析器
                    action_parser = next((p for p in subparser._subparsers._group_actions[0].choices.values()
                                       if p.prog.split()[-1] == action), None)
                    if action_parser:
                        action_parser.print_help()
                    else:
                        subparser.print_help()
            else:
                parser.print_help()
        else:
            parser.print_help()

    @staticmethod
    def parse_args():
        # 创建主解析器，使用自定义的 ArgumentParser
        parser = CustomArgumentParser(
            description="BD2 Client Simulator CLI",
            usage="%(prog)s [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}] <task_type> <action> [<args>]",
            formatter_class=argparse.RawDescriptionHelpFormatter  # 使用 RawDescriptionHelpFormatter
        )
        
        # 添加日志相关选项
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="设置日志级别（优先级高于配置文件）"
        )
        
        # 创建子命令解析器
        subparsers = parser.add_subparsers(dest="task_type", required=True, help="任务类型 (auth, cert, diag)")

        # 认证任务 auth
        auth_parser = subparsers.add_parser("auth", 
            help="认证任务",
            description="认证相关的操作，包括登录和登出",
            usage="%(prog)s <action> [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        auth_subparsers = auth_parser.add_subparsers(dest="action", required=True, help="认证任务操作")

        # 登录命令现在执行完整的登录流程（VM + SSO）
        login_parser = auth_subparsers.add_parser("login", 
            help="用户登录（VM + SSO）",
            description="执行完整的用户登录流程，包括VM和SSO认证",
            usage="%(prog)s [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        login_parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="设置日志级别（优先级高于配置文件）"
        )

        logout_parser = auth_subparsers.add_parser("logout", 
            help="用户登出",
            description="执行用户登出操作",
            usage="%(prog)s [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        logout_parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="设置日志级别（优先级高于配置文件）"
        )

        # 证书任务 cert
        cert_parser = subparsers.add_parser("cert", 
            help="证书管理",
            description="证书管理相关的操作，包括部署、撤销和刷新证书",
            usage="%(prog)s <action> [<args>] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        cert_subparsers = cert_parser.add_subparsers(dest="action", required=True, help="证书管理操作")

        deploy_parser = cert_subparsers.add_parser("deploy", 
            help="部署证书",
            description="部署证书到指定的ECU组件",
            usage="%(prog)s -e/--ecu {vdf,adf,cdf,zone,ccc,all} [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        deploy_parser.add_argument("-e", "--ecu", 
            choices=["vdf", "adf", "cdf", "zone", "ccc", "all"], 
            required=True, 
            help="目标 ECU 组件"
        )
        deploy_parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="设置日志级别（优先级高于配置文件）"
        )

        revoke_parser = cert_subparsers.add_parser("revoke", 
            help="撤销证书",
            description="撤销指定ID的证书",
            usage="%(prog)s -i/--cert_id CERT_ID [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        revoke_parser.add_argument("-i", "--cert_id", required=True, help="证书 ID")
        revoke_parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="设置日志级别（优先级高于配置文件）"
        )

        refresh_parser = cert_subparsers.add_parser("refresh", 
            help="刷新证书",
            description="使用新的证书数据刷新指定ID的证书",
            usage="%(prog)s -i/--cert_id CERT_ID -d/--cert_data CERT_DATA [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        refresh_parser.add_argument("-i", "--cert_id", required=True, help="证书 ID")
        refresh_parser.add_argument("-d", "--cert_data", required=True, help="新的证书数据")
        refresh_parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="设置日志级别（优先级高于配置文件）"
        )

        # 诊断任务 diag
        diag_parser = subparsers.add_parser("diag", 
            help="诊断任务",
            description="诊断相关的操作",
            usage="%(prog)s <action> [<args>] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        diag_subparsers = diag_parser.add_subparsers(dest="action", required=True, help="诊断任务操作")

        run_diag_parser = diag_subparsers.add_parser("run", 
            help="运行诊断",
            description="运行指定代码的诊断任务",
            usage="%(prog)s -c/--code CODE [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        run_diag_parser.add_argument("-c", "--code", required=True, help="诊断代码")
        run_diag_parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            help="设置日志级别（优先级高于配置文件）"
        )

        # 添加示例到每个解析器的 epilog
        parser.epilog = """
示例:
    bd2_client_sim.py auth login --log-level DEBUG          # 执行登录操作
    bd2_client_sim.py cert deploy -e vdf                    # 部署证书到VDF
    bd2_client_sim.py diag run -c 0x1234                    # 运行诊断
"""

        auth_parser.epilog = """
示例:
    bd2_client_sim.py auth login                            # 使用默认日志级别登录
    bd2_client_sim.py auth login --log-level DEBUG          # 使用DEBUG级别登录
"""

        login_parser.epilog = """
示例:
    bd2_client_sim.py auth login                            # 使用默认日志级别登录
    bd2_client_sim.py auth login --log-level DEBUG          # 使用DEBUG级别登录
"""

        logout_parser.epilog = """
示例:
    bd2_client_sim.py auth logout                           # 执行登出操作
    bd2_client_sim.py auth logout --log-level DEBUG         # 使用DEBUG级别登出
"""

        cert_parser.epilog = """
示例:
    bd2_client_sim.py cert deploy -e vdf                    # 部署证书到VDF
    bd2_client_sim.py cert revoke -i cert123                # 撤销指定证书
    bd2_client_sim.py cert refresh -i cert123 -d data       # 刷新证书数据
"""

        deploy_parser.epilog = """
示例:
    bd2_client_sim.py cert deploy -e vdf                    # 部署到VDF
    bd2_client_sim.py cert deploy -e all                    # 部署到所有组件
    bd2_client_sim.py cert deploy -e ccc --log-level DEBUG  # 使用DEBUG级别部署到CCC
"""

        revoke_parser.epilog = """
示例:
    bd2_client_sim.py cert revoke -i cert123                # 撤销指定证书
    bd2_client_sim.py cert revoke -i cert123 --log-level DEBUG  # 使用DEBUG级别撤销证书
"""

        refresh_parser.epilog = """
示例:
    bd2_client_sim.py cert refresh -i cert123 -d newdata    # 刷新证书数据
    bd2_client_sim.py cert refresh -i cert123 -d newdata --log-level DEBUG  # 使用DEBUG级别刷新证书
"""

        diag_parser.epilog = """
示例:
    bd2_client_sim.py diag run -c 0x1234                   # 运行诊断
    bd2_client_sim.py diag run -c 0x1234 --log-level DEBUG # 使用DEBUG级别运行诊断
"""

        run_diag_parser.epilog = """
示例:
    bd2_client_sim.py diag run -c 0x1234                   # 运行指定诊断代码
    bd2_client_sim.py diag run -c 0x1234 --log-level DEBUG # 使用DEBUG级别运行诊断
"""

        try:
            args = parser.parse_args()
            return args
        except SystemExit as e:
            # 在调试模式下，不直接退出
            if sys.gettrace() is not None:
                return None
            else:
                sys.exit(e.code)
        except Exception as e:
            print(f"\n错误: {str(e)}\n")
            parser.print_help()
            if sys.gettrace() is not None:
                return None
            else:
                sys.exit(1)
