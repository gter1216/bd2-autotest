"""
Description: This module handles authentication functionalities.

Changelog:
- 2025-03-07: Initial creation.
"""

from ..core.base_service import BaseService
from ..core.endpoint_manager import EndpointManager

class AuthService(BaseService):
    """Handles login authentication"""

    def login(self, vm_username, vm_password, sso_username, sso_password):
        """
        完整的登录流程：VM登录 + SSO登录
        """
        # 1. 首先进行VM登录
        vm_url = EndpointManager.get_endpoint("vm_login")
        vm_response = self.post(vm_url, {"username": vm_username, "password": vm_password})
        if not vm_response or "token" not in vm_response:
            # self.logger.log_error("VM Login failed!")
            return {"error": "VM登录失败"}
        
        # 保存VM登录的token
        self.set_auth_token(vm_response["token"])
        
        # 2. 然后进行SSO登录
        sso_url = EndpointManager.get_endpoint("sso_login")
        sso_response = self.post(sso_url, {"username": sso_username, "password": sso_password})
        if not sso_response or "token" not in sso_response:
            # self.logger.log_error("SSO Login failed!")
            return {"error": "SSO登录失败"}
            
        # 更新为SSO登录后的token
        self.set_auth_token(sso_response["token"])
        # self.logger.log_info("Login successful!")
        return sso_response

    def logout(self):
        """User logout"""
        url = EndpointManager.get_endpoint("auth_logout")
        response = self.post(url)
        if response:
            self.set_auth_token(None)
            # self.logger.log_info("Logout successful!")
        return response
