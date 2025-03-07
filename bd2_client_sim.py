
from config.config import CONFIG
from bd2_client_sim.services.auth_service import AuthService
# from bd2_client_sim.services.diag_service import DiagService
# from bd2_client_sim.services.cert_service import CertService
from utils.cli_parser import CLIParser

# 设置日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

class BD2ClientSim:
    """BD2 客户端模拟器"""

    def __init__(self):
        # self.base_url = CONFIG.basic["base_url"]
        self.base_url = CONFIG.get("basic.base_url")
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
        try:
            if task_type == "auth":
                if action == "login":
                    return self.auth.login(kwargs["username"], kwargs["password"])
                elif action == "logout":
                    return self.auth.logout()

            elif task_type == "cert":
                if action == "deploy":
                    return self.cert.deploy_certificate(kwargs["ecu"])
                elif action == "revoke":
                    return self.cert.revoke_certificate(kwargs["cert_id"])
                elif action == "refresh":
                    return self.cert.refresh_certificate(kwargs["cert_id"], kwargs["cert_data"])

            elif task_type == "diag":
                if action == "run":
                    return self.diagnosis.run_diagnosis(kwargs["code"])

            # logger.error("未知的任务或操作: %s %s", task_type, action)
            return {"error": "未知的任务或操作"}

        except KeyError as e:
            # logger.error("缺少必要参数: %s", str(e))
            return {"error": f"缺少必要参数: {str(e)}"}
        except Exception as e:
            # logger.error("任务执行失败: %s", str(e))
            return {"error": str(e)}

    def execute(self):
        """
        从 CLI 解析参数，并执行任务
        """
        args = CLIParser.parse_args()
        result = self.run_task(args.task_type, args.action, **vars(args))
        print(result)

if __name__ == "__main__":
    client_sim = BD2ClientSim()
    client_sim.execute()
