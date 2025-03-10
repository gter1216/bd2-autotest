"""
Description: This module handles authentication functionalities.

Changelog:
- 2025-03-07: Initial creation.
"""

from ..core.base_service import BaseService
from ..core.endpoint_manager import EndpointManager
import logging

class AuthService(BaseService):
    """Handles login authentication"""

    def __init__(self, base_url):
        super().__init__(base_url)
        self.logger = self._get_logger()

    def login(self, vm_username, vm_password, sso_username, sso_password):
        """
        完整的登录流程：VM登录 + SSO登录
        """
        self.logger.info("开始执行登录流程")
        self.logger.debug(f"VM用户名: {vm_username}")
        
        # 1. 首先进行VM登录
        vm_url = EndpointManager.get_endpoint("vm_login")
        self.logger.debug(f"开始VM登录: {vm_url}")
        # 第一步登录返回401是正常的，所以设置ignore_401=True
        vm_response = self.post(vm_url, {"username": vm_username, "password": vm_password}, ignore_401=True)
        if not vm_response:
            self.logger.error("VM登录失败")
            return {"error": "VM登录失败"}
        self.logger.debug("VM登录步骤完成")
        
        # 2. 然后进行SSO登录
        sso_url = EndpointManager.get_endpoint("sso_login")
        self.logger.debug(f"开始SSO登录: {sso_url}")
        sso_response = self.post(sso_url, {"username": sso_username, "password": sso_password})
        if not sso_response:
            self.logger.error("SSO登录失败")
            return {"error": "SSO登录失败"}
        
        self.logger.info("登录流程完成")
        return sso_response

    def logout(self):
        """User logout"""
        self.logger.info("开始执行登出操作")
        url = EndpointManager.get_endpoint("auth_logout")
        response = self.post(url)
        
        if response:
            self.logger.info("登出成功")
        else:
            self.logger.error("登出失败")
            
        return response
