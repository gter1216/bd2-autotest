from config.config import CONFIG
from bd2_client_sim.services.auth_service import AuthService
# from bd2_client_sim.services.diag_service import DiagService
# from bd2_client_sim.services.cert_service import CertService
from utils.cli_parser import CLIParser
from utils.logger_manager import LoggerManager

class BD2ClientSim:
    """BD2 客户端模拟器"""
    _args = None  # 存储解析后的命令行参数

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
        self.auth = AuthService(self.base_url)
        # self.diagnosis = DiagService(self.base_url)
        # self.cert = CertService(self.base_url)

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
                    if "error" in result:
                        self.logger.error(f"登录失败: {result['error']}")
                    else:
                        self.logger.info("登录成功")
                    return result
                elif action == "logout":
                    self.logger.info("开始登出流程")
                    result = self.auth.logout()
                    if result:
                        self.logger.info("登出成功")
                    else:
                        self.logger.error("登出失败")
                    return result

            elif task_type == "cert":
                if action == "deploy":
                    self.logger.info(f"部署证书到ECU: {kwargs['ecu']}")
                    return self.cert.deploy_certificate(kwargs["ecu"])
                elif action == "revoke":
                    self.logger.info(f"撤销证书: {kwargs['cert_id']}")
                    return self.cert.revoke_certificate(kwargs["cert_id"])
                elif action == "refresh":
                    self.logger.info(f"刷新证书: {kwargs['cert_id']}")
                    return self.cert.refresh_certificate(kwargs["cert_id"], kwargs["cert_data"])

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
        
        self.logger.debug(f"解析到任务类型: {task_type}, 操作: {action}")
        result = self.run_task(task_type, action, **args_dict)
        print(result)

if __name__ == "__main__":
    client_sim = BD2ClientSim()
    client_sim.execute()
