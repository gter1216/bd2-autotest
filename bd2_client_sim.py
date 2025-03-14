from config.config import CONFIG
from bd2_client_sim.services.auth_service import AuthService
# from bd2_client_sim.services.diag_service import DiagService
from bd2_client_sim.services.cert_service import CertService
from utils.cli.bd2_client_sim.cli_parser import CLIParser
from utils.logger_manager import LoggerManager
from bd2_client_sim.core.base_service import BaseService
from typing import Optional, Dict, Any
import time
import sys
import subprocess
import os
import logging
import json

class BD2ClientSim:
    """BD2 客户端模拟器类"""
    
    def __init__(self, uds_log: bool = False, cs_log: bool = False, 
                 log_level: str = None):
        """
        初始化客户端模拟器
        :param uds_log: 是否启用 UDS 日志
        :param cs_log: 是否启用 CS 日志
        :param log_level: 日志级别
        """
        # 设置日志
        if uds_log:
            os.environ['BD2_UDS_LOG'] = 'true'
        if cs_log:
            os.environ['BD2_CS_LOG'] = 'true'
        if log_level:
            os.environ['BD2_LOG_LEVEL'] = log_level
        
        # 设置脚本名称
        os.environ['BD2_SCRIPT_NAME'] = 'bd2_client_sim'
        
        # 初始化日志
        self.logger = logging.getLogger('bd2_client_sim')
        
        # 获取会话目录
        session_dir = os.environ.get('BD2_SESSION_DIR')
        if not session_dir:
            session_dir = LoggerManager.get_session_dir()
            if not session_dir:  # 如果会话目录还未创建
                session_dir = LoggerManager.create_session_dir()
                
        # 初始化基础 URL
        self.base_url = CONFIG.get("basic.base_url")
        self.logger.info(f"使用基础URL: {self.base_url}")
        
        # 初始化服务
        self.auth = AuthService(self.base_url)
        self.cert = CertService(self.base_url, cs_log=cs_log)
        
    def run_task(self, task_type: str, action: str, **kwargs) -> Dict[str, Any]:
        """
        执行任务
        :param task_type: 任务类型 (auth, cert, diag)
        :param action: 具体操作
        :param kwargs: 任务所需的额外参数
        :return: 任务执行结果
        """
        self.logger.info(f"执行任务: {task_type} {action}")
        self.logger.debug(f"任务参数: {kwargs}")

        try:
            if task_type == "auth":
                if action == "login":
                    self.logger.info("开始登录流程")
                    result = self.auth.login()
                    if not result.success:
                        self.logger.error(f"登录失败: {result.error}")
                    else:
                        self.logger.info("登录成功")
                    return result.to_dict()
                elif action == "logout":
                    self.logger.info("开始登出流程")
                    result = self.auth.logout()
                    if not result.success:
                        self.logger.error(f"登出失败: {result.error}")
                    else:
                        self.logger.info("登出成功")
                    return result.to_dict()
                elif action == "get_login_st":
                    self.logger.info("开始检查登录状态")
                    result = self.auth.get_login_status()
                    if not result.success:
                        self.logger.error("未登录或登录已过期")
                    else:
                        self.logger.info("登录状态正常")
                    return result.to_dict()
                elif action == "get_vehicle_st":
                    self.logger.info("开始检查车辆状态")
                    result = self.auth.get_vehicle_status()
                    if not result.success:
                        self.logger.error(f"车辆状态异常: {result.error}")
                    else:
                        self.logger.info("车辆状态正常")
                        time.sleep(10)
                    return result.to_dict()

            elif task_type == "cert":
                if action == "init":
                    self.logger.info("开始初始化证书功能")
                    result = self.cert.init_cert()
                    if not result.success:
                        self.logger.warning(f"证书功能初始化失败: {result.error}")
                    else:
                        self.logger.info("证书功能初始化成功")
                    return result.to_dict()
                elif action == "get_cert_st":
                    self.logger.info("开始获取证书状态")
                    result = self.cert.get_cert_st(kwargs.get('ecu'))
                    if not result.success:
                        self.logger.warning(f"获取证书状态失败: {result.error}")
                    else:
                        self.logger.info("获取证书状态成功")
                    return result.to_dict()
                elif action in ["deploy", "revoke"]:
                    if "ecu" not in kwargs:
                        raise KeyError("ecu")
                    if action == "deploy":
                        result = self.cert.deploy_cert(kwargs["ecu"])
                    else:  # revoke
                        result = self.cert.revoke_cert(kwargs["ecu"])
                    return result.to_dict()

            elif task_type == "diag":
                if action == "run":
                    self.logger.info(f"运行诊断: {kwargs.get('code', '')}")
                    return self.diagnosis.run_diagnosis(kwargs.get("code"))

            self.logger.error(f"未知的任务或操作: {task_type} {action}")
            return {"error": "未知的任务或操作"}

        except KeyError as e:
            self.logger.error(f"缺少必要参数: {str(e)}")
            return {"error": f"缺少必要参数: {str(e)}"}
        except Exception as e:
            self.logger.error(f"任务执行失败: {str(e)}")
            return {"error": str(e)}

    @classmethod
    def from_cli_args(cls) -> 'BD2ClientSim':
        """
        从命令行参数创建实例
        :return: BD2ClientSim实例
        """
        # 解析命令行参数
        task_type, action, args = CLIParser.parse_args()
        
        # 创建实例
        client = cls(
            uds_log=args.get('uds_log', False),
            cs_log=args.get('cs_log', False),
            log_level=args.get('log_level')
        )
        
        # 执行任务
        result = client.run_task(task_type, action, **args)
        
        # 输出结果
        if result.get('error'):
            print(f"错误: {result['error']}", file=sys.stderr)
            sys.exit(1)
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            sys.exit(0)

def main():
    """主函数"""
    try:
        # 从命令行参数创建实例并执行
        BD2ClientSim.from_cli_args()
    except Exception as e:
        print(f"错误: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
