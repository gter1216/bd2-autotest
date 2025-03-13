import click
import sys
from typing import Optional, Tuple, Dict, Any
from enum import Enum

class TaskType(str, Enum):
    AUTH = "auth"
    CERT = "cert"
    DIAG = "diag"

class AuthAction(str, Enum):
    LOGIN = "login"
    GET_LOGIN_ST = "get_login_st"
    GET_VEHICLE_ST = "get_vehicle_st"

class CertAction(str, Enum):
    INIT = "init"
    DEPLOY = "deploy"
    REVOKE = "revoke"
    GET_CERT_ST = "get_cert_st"

class DiagAction(str, Enum):
    RUN = "run"

class EcuType(str, Enum):
    ADF = "adf"
    CDF = "cdf"
    SAF = "saf"
    VDF_MCORE = "vdf_mcore"
    VDF = "vdf"
    ZONE_FTM = "zone_ftm"
    ZONE_FTE = "zone_fte"
    ZONE_REM = "zone_rem"
    ZONE_REE = "zone_ree"
    ALL = "all"

class CLIParser:
    """BD2 Client Simulator CLI Parser"""

    @staticmethod
    def parse_args() -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """
        解析命令行参数
        返回: (task_type, action, args) 或 None（如果解析失败）
        """
        try:
            # 确保至少有一个参数（程序名）
            if len(sys.argv) < 2:
                CLIParser._show_help()
                sys.exit(0)  # 正常退出，不返回 None

            # 获取任务类型
            task_type = sys.argv[1]
            if task_type in ['-h', '--help']:
                CLIParser._show_help()
                sys.exit(0)  # 正常退出，不返回 None

            if task_type not in [t.value for t in TaskType]:
                click.echo(f"错误: 无效的任务类型 '{task_type}'")
                click.echo("可用的任务类型: " + ", ".join(t.value for t in TaskType))
                sys.exit(1)  # 错误退出

            # 获取动作
            if len(sys.argv) < 3:
                click.echo(f"错误: 缺少动作参数")
                click.echo(f"用法: bd2_client_sim.py {task_type} <action> [<args>] [--uds-log] [--cs-log] [--log-level]")
                sys.exit(1)  # 错误退出

            action = sys.argv[2]
            if action in ['-h', '--help']:
                CLIParser._show_task_help(task_type)
                sys.exit(0)  # 正常退出，不返回 None

            # 验证动作是否有效
            valid_actions = {
                TaskType.AUTH: [a.value for a in AuthAction],
                TaskType.CERT: [a.value for a in CertAction],
                TaskType.DIAG: [a.value for a in DiagAction]
            }
            if action not in valid_actions[TaskType(task_type)]:
                click.echo(f"错误: 无效的动作 '{action}'")
                click.echo(f"可用的动作: " + ", ".join(valid_actions[TaskType(task_type)]))
                sys.exit(1)  # 错误退出

            # 解析其他参数
            args = {}
            i = 3
            while i < len(sys.argv):
                arg = sys.argv[i]
                
                # 处理可选参数
                if arg in ['--uds-log', '--cs-log']:
                    if i + 1 >= len(sys.argv):
                        click.echo(f"错误: {arg} 需要一个值 (on/off)")
                        sys.exit(1)
                    value = sys.argv[i + 1].lower()
                    if value not in ['on', 'off']:
                        click.echo(f"错误: {arg} 的值必须是 on 或 off")
                        sys.exit(1)
                    args[arg[2:].replace('-', '_')] = (value == 'on')
                    i += 2
                elif arg == '--log-level':
                    if i + 1 >= len(sys.argv):
                        click.echo("错误: --log-level 需要一个值")
                        sys.exit(1)  # 错误退出
                    value = sys.argv[i + 1]
                    if value not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                        click.echo("错误: --log-level 的值必须是 DEBUG, INFO, WARNING, ERROR, 或 CRITICAL")
                        sys.exit(1)  # 错误退出
                    args['log_level'] = value
                    i += 2
                # 处理必选参数
                elif arg == '-ecu':
                    if i + 1 >= len(sys.argv):
                        click.echo("错误: -ecu 需要一个值")
                        sys.exit(1)  # 错误退出
                    value = sys.argv[i + 1]
                    if task_type == TaskType.CERT.value:
                        if action == CertAction.DEPLOY.value:
                            if value not in [e.value for e in EcuType]:
                                click.echo(f"错误: -ecu 的值必须是 {', '.join(e.value for e in EcuType)}")
                                sys.exit(1)  # 错误退出
                        elif action == CertAction.REVOKE.value:
                            if value not in [e.value for e in EcuType if e != EcuType.ALL]:
                                click.echo(f"错误: -ecu 的值必须是 {', '.join(e.value for e in EcuType if e != EcuType.ALL)}")
                                sys.exit(1)  # 错误退出
                        elif action == CertAction.GET_CERT_ST.value:
                            if value not in [e.value for e in EcuType if e != EcuType.ALL]:
                                click.echo(f"错误: -ecu 的值必须是 {', '.join(e.value for e in EcuType if e != EcuType.ALL)}")
                                sys.exit(1)  # 错误退出
                    args['ecu'] = value
                    i += 2
                elif arg in ['-h', '--help']:
                    CLIParser._show_action_help(task_type, action)
                    sys.exit(0)  # 正常退出，不返回 None
                else:
                    click.echo(f"错误: 未知的参数 '{arg}'")
                    sys.exit(1)  # 错误退出

            # 验证必选参数
            if task_type == TaskType.CERT.value:
                if action in [CertAction.DEPLOY.value, CertAction.REVOKE.value]:
                    if 'ecu' not in args:
                        click.echo(f"错误: {action} 操作需要 -ecu 参数")
                        sys.exit(1)  # 错误退出
                    if action == CertAction.DEPLOY.value:
                        if args['ecu'] not in [e.value for e in EcuType]:
                            click.echo(f"错误: -ecu 的值必须是 {', '.join(e.value for e in EcuType)}")
                            sys.exit(1)  # 错误退出
                    elif action == CertAction.REVOKE.value:
                        if args['ecu'] not in [e.value for e in EcuType if e != EcuType.ALL]:
                            click.echo(f"错误: -ecu 的值必须是 {', '.join(e.value for e in EcuType if e != EcuType.ALL)}")
                            sys.exit(1)  # 错误退出

            return task_type, action, args

        except Exception as e:
            click.echo(f"错误: {str(e)}")
            sys.exit(1)  # 错误退出

    @staticmethod
    def _show_help():
        """显示主帮助信息"""
        click.echo("""
用法: bd2_client_sim.py <task_type> <action> [<args>] [--uds-log] [--cs-log] [--log-level]

BD2 Client Simulator CLI

必选参数:
  <task_type>    任务类型 (auth, cert, diag)
  <action>      具体操作（使用 -h 查看每个任务类型的可用操作）

可选参数:
  -h, --help    显示帮助信息
  --uds-log     UDS 日志开关 (on/off)
  --cs-log      CS 日志开关 (on/off)
  --log-level   设置日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)

示例:
    bd2_client_sim.py auth login --uds-log on              # 执行登录操作并启用UDS日志
    bd2_client_sim.py cert deploy -ecu ccc --cs-log on     # 部署证书到CCC并启用CS日志
    bd2_client_sim.py diag run                             # 运行诊断
""")

    @staticmethod
    def _show_task_help(task_type: str):
        """显示特定任务类型的帮助信息"""
        task_helps = {
            TaskType.AUTH.value: """
用法: bd2_client_sim.py auth <action> [<args>] [--uds-log] [--cs-log] [--log-level]

可用的认证操作:
  login          用户登录
  get_login_st   检查登录状态
  get_vehicle_st 获取车辆状态

示例:
    bd2_client_sim.py auth login --uds-log on              # 执行登录操作并启用UDS日志
    bd2_client_sim.py auth get_login_st                    # 检查登录状态
""",
            TaskType.CERT.value: """
用法: bd2_client_sim.py cert <action> [<args>] [--uds-log] [--cs-log] [--log-level]

可用的证书操作:
  init           初始化证书功能
  deploy         部署证书（需要 -ecu 参数）
  revoke         撤销证书（需要 -ecu 参数）
  get_cert_st    获取证书状态

示例:
    bd2_client_sim.py cert init                           # 初始化证书功能
    bd2_client_sim.py cert deploy -ecu vdf_mcore --cs-log on    # 部署证书到VDF_MCORE并启用CS日志
    bd2_client_sim.py cert revoke -ecu zone_fte         # 撤销ZONE_FTE证书
    bd2_client_sim.py cert get_cert_st -ecu saf         # 获取SAF的证书状态
""",
            TaskType.DIAG.value: """
用法: bd2_client_sim.py diag <action> [<args>] [--uds-log] [--cs-log] [--log-level]

可用的诊断操作:
  run            运行诊断任务

示例:
    bd2_client_sim.py diag run --uds-log on              # 运行诊断并启用UDS日志
"""
        }
        click.echo(task_helps.get(task_type, "未知的任务类型"))

    @staticmethod
    def _show_action_help(task_type: str, action: str):
        """显示特定动作的帮助信息"""
        action_helps = {
            (TaskType.AUTH.value, AuthAction.LOGIN.value): """
用法: bd2_client_sim.py auth login [<args>] [--uds-log] [--cs-log] [--log-level]

执行用户登录操作

示例:
    bd2_client_sim.py auth login                          # 使用默认配置登录
    bd2_client_sim.py auth login --uds-log on --cs-log on # 启用所有日志
""",
            (TaskType.AUTH.value, AuthAction.GET_LOGIN_ST.value): """
用法: bd2_client_sim.py auth get_login_st [<args>] [--uds-log] [--cs-log] [--log-level]

检查当前用户的登录状态

示例:
    bd2_client_sim.py auth get_login_st                   # 检查登录状态
""",
            (TaskType.AUTH.value, AuthAction.GET_VEHICLE_ST.value): """
用法: bd2_client_sim.py auth get_vehicle_st [<args>] [--uds-log] [--cs-log] [--log-level]

获取车辆的状态信息

示例:
    bd2_client_sim.py auth get_vehicle_st                 # 获取车辆状态
""",
            (TaskType.CERT.value, CertAction.INIT.value): """
用法: bd2_client_sim.py cert init [<args>] [--uds-log] [--cs-log] [--log-level]

初始化证书功能

示例:
    bd2_client_sim.py cert init                          # 初始化证书功能
""",
            (TaskType.CERT.value, CertAction.DEPLOY.value): """
用法: bd2_client_sim.py cert deploy -ecu <type> [<args>] [--uds-log] [--cs-log] [--log-level]

部署证书到指定 ECU

必选参数:
  -ecu <type>    ECU 类型 (adf, cdf, saf, vdf_mcore, vdf, zone_ftm, zone_fte, zone_rem, zone_ree, all)

示例:
    bd2_client_sim.py cert deploy -ecu ccc               # 部署到 CCC
    bd2_client_sim.py cert deploy -ecu all --cs-log on   # 部署到所有 ECU 并启用CS日志
""",
            (TaskType.CERT.value, CertAction.REVOKE.value): """
用法: bd2_client_sim.py cert revoke -ecu <type> [<args>] [--uds-log] [--cs-log] [--log-level]

撤销指定 ECU 的证书

必选参数:
  -ecu <type>    ECU 类型 (adf, cdf, saf, vdf_mcore, vdf, zone_ftm, zone_fte, zone_rem, zone_ree)

示例:
    bd2_client_sim.py cert revoke -ecu vdf_mcore        # 撤销 VDF_MCORE 证书
    bd2_client_sim.py cert revoke -ecu zone_fte         # 撤销 ZONE_FTE 证书
""",
            (TaskType.CERT.value, CertAction.GET_CERT_ST.value): """
用法: bd2_client_sim.py cert get_cert_st [-ecu <type>] [--uds-log] [--cs-log] [--log-level]

获取证书状态信息

可选参数:
  -ecu <type>    ECU 类型 (adf, cdf, saf, vdf_mcore, vdf, zone_ftm, zone_fte, zone_rem, zone_ree)
                 如果不指定，将显示所有 ECU 的状态

示例:
    bd2_client_sim.py cert get_cert_st                  # 获取所有 ECU 的证书状态
    bd2_client_sim.py cert get_cert_st -ecu saf         # 获取 SAF 的证书状态
    bd2_client_sim.py cert get_cert_st -ecu vdf_mcore   # 获取 VDF_MCORE 的证书状态
""",
            (TaskType.DIAG.value, DiagAction.RUN.value): """
用法: bd2_client_sim.py diag run [<args>] [--uds-log] [--cs-log] [--log-level]

运行诊断任务

示例:
    bd2_client_sim.py diag run                          # 运行诊断
    bd2_client_sim.py diag run --uds-log on            # 运行诊断并启用UDS日志
"""
        }
        help_text = action_helps.get((task_type, action))
        if help_text:
            click.echo(help_text)
        else:
            click.echo(f"未知的操作: {task_type} {action}")
