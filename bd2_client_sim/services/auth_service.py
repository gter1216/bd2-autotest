"""
Description: This module handles authentication functionalities.

Changelog:
- 2025-03-07: Initial creation.
"""

from ..core.base_service import BaseService
from ..core.endpoint_manager import EndpointManager
from utils.credential_manager import CredentialManager

class AuthService(BaseService):
    """Handles login authentication"""

    def __init__(self, base_url):
        super().__init__(base_url)
        self.logger = self._get_logger()
        self.credential_manager = CredentialManager()

    def login(self):
        """登录系统
        
        登录流程：
        1. 先进行 VM 登录
           - 如果状态码是 200 或 401，继续执行 SSO 登录
           - 如果状态码是其他值，直接返回登录失败
        2. 然后进行 SSO 登录（仅在 VM 登录状态码为 200 或 401 时执行）
           - 如果状态码是 200 且有响应数据，则登录成功
           - 否则登录失败
           
        Returns:
            dict: 包含登录结果的信息
                - 成功时返回 {"status": "success"}
                - 失败时返回 {"error": "错误信息"}
        """
        self.logger.info("开始登录")
        
        # 获取登录凭证
        creds = self.credential_manager.get_current_credentials()
        if not creds:
            self.logger.error("未找到可用的登录凭证")
            return {"error": "未找到可用的登录凭证"}
            
        username = creds.get("username")
        password = creds.get("password")
        self.logger.info("使用保存的凭证登录")
        
        # 第一步：VM 登录
        vm_status_code, vm_response = self.post("/api/v1/login", {
            "username": username,
            "password": password,
            "type": "vm"
        })
        
        # 检查 VM 登录结果
        if vm_status_code not in [200, 401]:
            self.logger.error(f"VM登录失败，状态码: {vm_status_code}")
            return {"error": f"VM登录失败，状态码: {vm_status_code}"}
            
        self.logger.info("VM登录完成，继续执行 SSO 登录")
            
        # 第二步：SSO 登录
        sso_status_code, sso_response = self.post("/api/v1/login", {
            "username": username,
            "password": password,
            "type": "sso"
        })
        
        if sso_status_code == 200 and sso_response:
            self.logger.info("SSO登录成功")
            # 保存凭证
            self.credential_manager.save_user_credentials(username, password)
            return {"status": "success"}
            
        return {"error": "SSO登录失败"}

    def logout(self):
        """登出系统
        
        Returns:
            dict: 包含登出结果的信息
                - 成功时返回 {"status": "success"}
                - 失败时返回 {"error": "错误信息"}
        """
        self.logger.info("开始登出")
        status_code, response = self.post("/api/v1/logout")
        if status_code == 200:
            self.logger.info("登出成功")
            # 清除凭证
            self.credential_manager.remove_user_credentials()
            return {"status": "success"}
        return {"error": "登出失败"}

    def get_login_status(self):
        """检查登录状态
        
        Returns:
            dict: 包含登录状态的信息
                - 成功时返回 {"status": "success"}
                - 失败时返回 {"error": "错误信息"}
        """
        self.logger.info("检查登录状态")
        status_code, response = self.get("/api/v1/login")
        if status_code == 200:
            return {"status": "success"}
        return {"error": "登录状态: NOK"}
