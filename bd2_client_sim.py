from config.config import CONFIG
from bd2_client_sim.services.auth_service import AuthService
# from bd2_client_sim.services.diag_service import DiagService
from bd2_client_sim.services.cert_service import CertService
from utils.cli_parser import CLIParser
from utils.logger_manager import LoggerManager
from bd2_client_sim.core.sse_manager import SSEManager
import time

class BD2ClientSim:
    """BD2 客户端模拟器"""
    _args = None  # 存储解析后的命令行参数
    _sse_manager = None  # SSE 管理器实例

    def __init__(self):
        # 确保命令行参数已经解析
        if BD2ClientSim._args is None:
            BD2ClientSim._args = CLIParser.parse_args()
            if BD2ClientSim._args is None:  # 参数解析失败
                return
            
        # 设置日志级别（按优先级：命令行参数 > config file）
        if BD2ClientSim._args.log_level:
            LoggerManager.set_log_level(BD2ClientSim._args.log_level)
            
        # 获取logger实例
        self.logger = LoggerManager.get_logger(__file__)
        self.logger.debug("初始化BD2ClientSim")
        self.base_url = CONFIG.get("basic.base_url")
        self.logger.info(f"使用基础URL: {self.base_url}")
        
        # 初始化服务
        self.auth = AuthService(self.base_url)
        # self.diagnosis = DiagService(self.base_url)
        self.cert = CertService(self.base_url)
        
        # 初始化 SSE 管理器
        if BD2ClientSim._sse_manager is None:
            BD2ClientSim._sse_manager = SSEManager(self.base_url)

    def run_task(self, task_type, action, **kwargs):
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
                    # 让 AuthService 处理凭据获取
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
                elif action == "get_login_status":
                    self.logger.info("开始检查登录状态")
                    result = self.auth.get_login_status()
                    if not result.success:
                        self.logger.error("未登录或登录已过期")
                    else:
                        self.logger.info("登录状态正常")
                    return result.to_dict()
                elif action == "get_vehicle_status":
                    self.logger.info("开始检查车辆状态")
                    result = self.auth.get_vehicle_status()
                    if not result.success:
                        self.logger.error(f"车辆状态异常: {result.error}")
                    else:
                        self.logger.info("车辆状态正常")
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

            elif task_type == "diag":
                if action == "run":
                    self.logger.info(f"运行诊断: {kwargs['code']}")
                    return self.diagnosis.run_diagnosis(kwargs["code"])

            self.logger.error(f"未知的任务或操作: {task_type} {action}")
            return {"error": "未知的任务或操作"}

        except KeyError as e:
            self.logger.error(f"缺少必要参数: {str(e)}")
            return {"error": f"缺少必要参数: {str(e)}"}
        except Exception as e:
            self.logger.error(f"任务执行失败: {str(e)}")
            return {"error": str(e)}

    def execute(self):
        """
        从 CLI 解析参数，并执行任务
        """
        if BD2ClientSim._args is None:
            BD2ClientSim._args = CLIParser.parse_args()
            if BD2ClientSim._args is None:  # 参数解析失败
                return
        
        self.logger.debug("开始解析命令行参数")
        
        args_dict = vars(BD2ClientSim._args)
        task_type = args_dict.pop('task_type')
        action = args_dict.pop('action')
        # 移除日志相关参数，因为它们不是任务参数
        args_dict.pop('log_level', None)
        
        try:
            # 启动 SSE 日志记录，使用 LoggerManager 的会话目录
            session_dir = LoggerManager.get_session_dir()
            if not session_dir:  # 如果会话目录还未创建
                session_dir = LoggerManager.create_session_dir()
            
            # 启动SSE监听并等待连接就绪
            if not BD2ClientSim._sse_manager.start_sse_logging(task_type, action, session_dir):
                self.logger.error("一个或多个SSE连接启动失败")
            
            # 等待所有SSE连接就绪
            if not BD2ClientSim._sse_manager.wait_for_ready(timeout=10):
                self.logger.warning("等待SSE连接就绪超时，继续执行任务")
            
            # 执行任务
            self.logger.debug(f"解析到任务类型: {task_type}, 操作: {action}")
            result = self.run_task(task_type, action, **args_dict)
            self.logger.info(f"任务执行结果: {result}")
            
            # 任务完成后等待一小段时间，确保SSE日志能够完整记录
            time.sleep(0.5)
            
        finally:
            # 停止所有 SSE 处理器
            if BD2ClientSim._sse_manager:
                BD2ClientSim._sse_manager.stop_all()

if __name__ == "__main__":
    client_sim = BD2ClientSim()
    client_sim.execute()
