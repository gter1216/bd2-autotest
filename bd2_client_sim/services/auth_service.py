"""
Description: This module handles authentication functionalities.

Changelog:
- 2025-03-07: Initial creation.
"""

from ..core.base_service import BaseService
from ..core.endpoint_manager import EndpointManager

class AuthService(BaseService):
    """Handles login authentication"""

    def login(self, username, password):
        """User login"""
        url = EndpointManager.get_endpoint("auth_login")
        response = self.post(url, {"username": username, "password": password})
        if response and "token" in response:
            self.set_auth_token(response["token"])
            # self.logger.log_info("Login successful!")
        else:
            # self.logger.log_error("Login failed!")
            pass
        return response

    def logout(self):
        """User logout"""
        url = EndpointManager.get_endpoint("auth_logout")
        response = self.post(url)
        if response:
            self.set_auth_token(None)
            # self.logger.log_info("Logout successful!")
        return response
