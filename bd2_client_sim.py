from config.config import CONFIG
from bd2_client_sim.services.auth_service import AuthService
# from bd2_client_sim.services.diag_service import DiagService
from bd2_client_sim.services.cert_service import CertService
from utils.cli_parser import CLIParser
from utils.logger_manager import LoggerManager
from bd2_client_sim.core.base_service import BaseService
from typing import Optional, Dict, Any
import time
import sys
import subprocess

class BD2ClientSim:
    """BD2 客户端模拟器"""
    
    def __init__(self, task_type: Optional[str] = None, 
                 action: Optional[str] = None, 
                 uds_log: bool = False,
                 cs_log: bool = False,
                 log_level: Optional[str] = None,
                 **kwargs):
        """
        初始化 BD2 客户端模拟器
        :param task_type: 任务类型 (auth, cert, diag)
        :param action: 具体操作
        :param uds_log: 是否启用 UDS 日志
        :param cs_log: 是否启用 CS 日志
        :param log_level: 日志级别
        :param kwargs: 其他参数，如 ecu 等
        """
        # 设置参数
        self.task_type = task_type
        self.action = action
        self.uds_log = uds_log
        self.cs_log = cs_log
        self.extra_args = kwargs
        
        # 设置日志级别
        if log_level:
            LoggerManager.set_log_level(log_level)
            
        # 获取logger实例
        self.logger = LoggerManager.get_logger(__file__)
        
        # 创建会话目录并记录命令
        try:
            # 启动 SSE 日志记录，使用 LoggerManager 的会话目录
            session_dir = LoggerManager.get_session_dir()
            if not session_dir:  # 如果会话目录还未创建
                session_dir = LoggerManager.create_session_dir()
                
            # 记录执行命令（如果是通过命令行调用）
            if len(sys.argv) > 1:
                cmd = subprocess.list2cmdline(sys.argv)
                self.logger.info(f"执行命令: {cmd}")
        except Exception as e:
            self.logger.warning(f"无法获取执行命令: {e}")
            
        self.logger.debug("初始化BD2ClientSim")
        self.base_url = CONFIG.get("basic.base_url")
        self.logger.info(f"使用基础URL: {self.base_url}")
        
        # 初始化服务
        self.auth = AuthService(self.base_url)
        # self.diagnosis = DiagService(self.base_url)
        self.cert = CertService(self.base_url)
        
        # 初始化 SSE 管理器
        self.sse_manager = BaseService.get_sse_manager()
        if self.sse_manager:
            self._setup_sse_listeners()

    def _setup_sse_listeners(self):
        """根据配置设置 SSE 监听器"""
        # 获取命令行参数或配置文件中的 SSE 设置
        sse_configs = {
            "basic_vehicle_service_log": CONFIG.get("basic.basic_vehicle_service_log", "off"),
            "uds_log": "on" if self.uds_log else "off",
            "cs_log": "on" if self.cs_log else "off"
        }
        
        # 启动需要的 SSE 监听器
        for sse_type, status in sse_configs.items():
            if status == "on":
                self.logger.info(f"启动 {sse_type} SSE 监听")
                self.sse_manager.start_sse(sse_type)
            else:
                self.logger.debug(f"{sse_type} SSE 监听未启用")

    def run_task(self, task_type: str, action: str, **kwargs) -> Dict[str, Any]:
        """
        执行 BD2 任务
        :param task_type: 任务类型 (auth, cert, diag)
        :param action: 具体操作
        :param kwargs: 任务所需的额外参数
        :return: API 响应
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
                        # time.sleep(10)
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

    def execute(self) -> Dict[str, Any]:
        """
        执行任务
        :return: 任务执行结果
        """
        if not self.task_type or not self.action:
            self.logger.error("缺少必要的任务类型或动作参数")
            return {"error": "缺少必要的任务类型或动作参数"}
            
        try:
            # 执行任务
            self.logger.debug(f"解析到任务类型: {self.task_type}, 操作: {self.action}")
            result = self.run_task(self.task_type, self.action, **self.extra_args)
            self.logger.info(f"任务执行结果: {result}")
            
            # 任务完成后等待一小段时间，确保SSE日志能够完整记录
            time.sleep(0.5)
            
            return result
            
        finally:
            pass

    def cleanup(self):
        """清理资源"""
        if self.sse_manager:
            self.sse_manager.stop_all()

    @classmethod
    def from_cli_args(cls) -> 'BD2ClientSim':
        """
        从命令行参数创建实例
        :return: BD2ClientSim实例
        """
        result = CLIParser.parse_args()
        if result is None:
            sys.exit(1)
            
        task_type, action, args = result
        return cls(
            task_type=task_type,
            action=action,
            uds_log=args.get('uds_log', False),
            cs_log=args.get('cs_log', False),
            log_level=args.get('log_level'),
            **{k: v for k, v in args.items() if k not in ['uds_log', 'cs_log', 'log_level']}
        )

if __name__ == "__main__":
    client_sim = BD2ClientSim.from_cli_args()
    try:
        result = client_sim.execute()
        if result.get('error'):
            sys.exit(1)
    finally:
        client_sim.cleanup()
