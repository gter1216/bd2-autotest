import argparse

class CLIParser:
    """BD2 客户端模拟器的命令行解析器"""

    @staticmethod
    def parse_args():
        parser = argparse.ArgumentParser(description="BD2 Client Simulator CLI")
        subparsers = parser.add_subparsers(dest="task_type", required=True, help="任务类型 (auth, cert, diag)")

        # 认证任务 auth
        auth_parser = subparsers.add_parser("auth", help="认证任务")
        auth_subparsers = auth_parser.add_subparsers(dest="action", required=True, help="认证任务操作")

        login_parser = auth_subparsers.add_parser("login", help="用户登录")
        login_parser.add_argument("-u", "--username", required=True, help="用户名")
        login_parser.add_argument("-p", "--password", required=True, help="密码")

        logout_parser = auth_subparsers.add_parser("logout", help="用户登出")

        # 证书任务 cert
        cert_parser = subparsers.add_parser("cert", help="证书管理")
        cert_subparsers = cert_parser.add_subparsers(dest="action", required=True, help="证书管理操作")

        deploy_parser = cert_subparsers.add_parser("deploy", help="部署证书")
        deploy_parser.add_argument("-e", "--ecu", choices=["vdf", "adf", "cdf", "zone", "ccc", "all"], required=True, help="目标 ECU 组件")

        revoke_parser = cert_subparsers.add_parser("revoke", help="撤销证书")
        revoke_parser.add_argument("-i", "--cert_id", required=True, help="证书 ID")

        refresh_parser = cert_subparsers.add_parser("refresh", help="刷新证书")
        refresh_parser.add_argument("-i", "--cert_id", required=True, help="证书 ID")
        refresh_parser.add_argument("-d", "--cert_data", required=True, help="新的证书数据")

        # 诊断任务 diag
        diag_parser = subparsers.add_parser("diag", help="诊断任务")
        diag_subparsers = diag_parser.add_subparsers(dest="action", required=True, help="诊断任务操作")

        run_diag_parser = diag_subparsers.add_parser("run", help="运行诊断")
        run_diag_parser.add_argument("-c", "--code", required=True, help="诊断代码")

        return parser.parse_args()
