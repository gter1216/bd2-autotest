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

    def login(self, vm_username=None, vm_password=None, sso_username=None, sso_password=None, save_as_user=False):
        """
        完整的登录流程：VM登录 + SSO登录

        参数:
            vm_username: VM用户名，如果为None则使用保存的凭据
            vm_password: VM密码，如果为None则使用保存的凭据
            sso_username: SSO用户名，如果为None则使用保存的凭据
            sso_password: SSO密码，如果为None则使用保存的凭据
            save_as_user: 是否将凭据保存为个人凭据
        """
        self.logger.info("开始执行登录流程")
        
        # 如果没有提供完整凭据，尝试加载保存的凭据
        if not all([vm_username, vm_password, sso_username, sso_password]):
            creds = self.credential_manager.get_current_credentials()
            if creds:
                vm_username = vm_username or creds.get("vm_username")
                vm_password = vm_password or creds.get("vm_password")
                sso_username = sso_username or creds.get("sso_username")
                sso_password = sso_password or creds.get("sso_password")
                self.logger.info(self.credential_manager.get_current_credentials_info())
            else:
                return {"error": "未找到可用的凭据"}
        
        # 1. 执行VM登录
        vm_url = EndpointManager.get_endpoint("vm_login")
        self.logger.debug(f"开始VM登录: {vm_url}")
        vm_response = self.post(vm_url, {"username": vm_username, "password": vm_password}, ignore_401=True)
        if not vm_response:
            self.logger.error("VM登录失败")
            return {"error": "VM登录失败"}
        self.logger.debug("VM登录步骤完成")
        
        # 2. 执行SSO登录
        sso_url = EndpointManager.get_endpoint("sso_login")
        self.logger.debug(f"开始SSO登录: {sso_url}")
        sso_response = self.post(sso_url, {"username": sso_username, "password": sso_password})
        if not sso_response:
            self.logger.error("SSO登录失败")
            return {"error": "SSO登录失败"}
        
        # 如果需要，保存为个人凭据
        if save_as_user:
            self.credential_manager.save_user_credentials(vm_username, vm_password, sso_username, sso_password)
        
        self.logger.info("登录流程完成")
        return sso_response

    def logout(self):
        """User logout"""
        self.logger.info("开始执行登出操作")
        url = EndpointManager.get_endpoint("auth_logout")
        response = self.post(url)
        
        if response:
            self.logger.info("登出成功")
            # 删除用户个人凭据
            self.credential_manager.remove_user_credentials()
        else:
            self.logger.error("登出失败")
            
        return response
