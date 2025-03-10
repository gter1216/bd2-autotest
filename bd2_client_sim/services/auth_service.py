"""
Description: This module handles authentication functionalities.

Changelog:
- 2025-03-07: Initial creation.
"""

from pathlib import Path
import json
from cryptography.fernet import Fernet
from ..core.base_service import BaseService
from ..core.endpoint_manager import EndpointManager
import logging
import os
import socket
from config.config import CONFIG

class AuthService(BaseService):
    """Handles login authentication"""

    # 项目级配置文件（所有用户共享）
    PROJECT_CONFIG_FILE = "auth.enc"
    PROJECT_KEY_FILE = "auth.key"
    
    # 用户级配置文件（按主机名区分）
    USER_CONFIG_FILE = "auth.enc"
    USER_KEY_FILE = "auth.key"

    def __init__(self, base_url):
        super().__init__(base_url)
        self.logger = self._get_logger()
        self._init_crypto()

    def _init_crypto(self):
        """初始化加密相关的设置"""
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        var_dir = Path(project_root) / "var"
        credentials_dir = var_dir / "credentials"
        
        # 项目配置文件路径（直接在 credentials 目录下）
        self.project_config_path = credentials_dir / self.PROJECT_CONFIG_FILE
        self.project_key_path = credentials_dir / self.PROJECT_KEY_FILE
        
        # 用户个人配置文件路径（在 var/credentials/hosts/hostname 目录下）
        hostname = socket.gethostname()
        user_config_dir = credentials_dir / "hosts" / hostname
        user_config_dir.mkdir(parents=True, exist_ok=True)
        self.user_config_path = user_config_dir / self.USER_CONFIG_FILE
        self.user_key_path = user_config_dir / self.USER_KEY_FILE
        
        # 记录主机名，用于日志显示
        self.hostname = hostname

    def _get_fernet(self, key_path):
        """获取指定密钥的Fernet实例"""
        if key_path.exists():
            return Fernet(key_path.read_bytes())
        return None

    def save_project_credentials(self, vm_username, vm_password, sso_username, sso_password):
        """
        保存项目级凭据（通常是公共账号）
        保存位置：项目目录/config/auth.enc
        """
        # 确保配置目录存在
        self.project_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成新密钥
        key = Fernet.generate_key()
        self.project_key_path.write_bytes(key)
        fernet = Fernet(key)
        
        # 加密保存凭据
        data = {
            "type": "project",  # 标记凭据类型
            "vm_username": vm_username,
            "vm_password": vm_password,
            "sso_username": sso_username,
            "sso_password": sso_password
        }
        encrypted = fernet.encrypt(json.dumps(data).encode())
        self.project_config_path.write_bytes(encrypted)
        self.logger.info(f"项目凭据已加密保存到: {self.project_config_path}")

    def save_user_credentials(self, vm_username, vm_password, sso_username, sso_password):
        """
        保存用户个人凭据
        保存位置：~/.bd2/auth.enc
        """
        # 确保用户配置目录存在
        self.user_config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 生成新密钥
        key = Fernet.generate_key()
        self.user_key_path.write_bytes(key)
        fernet = Fernet(key)
        
        # 加密保存凭据
        data = {
            "type": "personal",  # 标记凭据类型
            "vm_username": vm_username,
            "vm_password": vm_password,
            "sso_username": sso_username,
            "sso_password": sso_password
        }
        encrypted = fernet.encrypt(json.dumps(data).encode())
        self.user_config_path.write_bytes(encrypted)
        self.logger.info(f"个人凭据已加密保存到: {self.user_config_path}")

    def _load_credentials(self):
        """
        按优先级加载凭据：
        1. 用户个人加密凭据（~/.bd2/auth.enc）
        2. 项目级加密凭据（项目目录/config/auth.enc）
        3. config.yaml 中的明文配置
        """
        # 1. 尝试加载用户个人凭据
        if self.user_config_path.exists() and self.user_key_path.exists():
            try:
                fernet = self._get_fernet(self.user_key_path)
                encrypted = self.user_config_path.read_bytes()
                data = json.loads(fernet.decrypt(encrypted))
                if data.get("type") == "personal":
                    self.logger.debug(f"使用个人凭据（来自：{self.user_config_path}）")
                    return data
            except Exception as e:
                self.logger.error(f"读取个人凭据失败: {str(e)}")

        # 2. 尝试加载项目凭据
        if self.project_config_path.exists() and self.project_key_path.exists():
            try:
                fernet = self._get_fernet(self.project_key_path)
                encrypted = self.project_config_path.read_bytes()
                data = json.loads(fernet.decrypt(encrypted))
                if data.get("type") == "project":
                    self.logger.debug(f"使用项目凭据（来自：{self.project_config_path}）")
                    return data
            except Exception as e:
                self.logger.error(f"读取项目凭据失败: {str(e)}")

        # 3. 尝试从 config.yaml 加载明文配置
        try:
            vm_username = CONFIG.get("basic.vm_username")
            vm_password = CONFIG.get("basic.vm_password")
            sso_username = CONFIG.get("basic.sso_username")
            sso_password = CONFIG.get("basic.sso_password")
            
            if all([vm_username, vm_password, sso_username, sso_password]):
                self.logger.warning("使用 config.yaml 中的明文密码（不推荐）")
                return {
                    "type": "plain",
                    "vm_username": vm_username,
                    "vm_password": vm_password,
                    "sso_username": sso_username,
                    "sso_password": sso_password
                }
        except Exception as e:
            self.logger.error(f"读取配置文件失败: {str(e)}")

        return None

    def get_current_credentials_info(self):
        """获取当前使用的凭据信息"""
        creds = self._load_credentials()
        if not creds:
            return "未找到任何可用的凭据"
        
        cred_type = creds.get("type", "unknown")
        if cred_type == "personal":
            return f"使用个人凭据 (主机: {self.hostname}, 用户: {creds['vm_username']}, 位置: {self.user_config_path})"
        elif cred_type == "project":
            return f"使用项目凭据 (用户: {creds['vm_username']}, 位置: {self.project_config_path})"
        else:
            return f"使用明文配置 (用户: {creds['vm_username']}, 位置: config.yaml)"

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
            creds = self._load_credentials()
            if creds:
                vm_username = vm_username or creds.get("vm_username")
                vm_password = vm_password or creds.get("vm_password")
                sso_username = sso_username or creds.get("sso_username")
                sso_password = sso_password or creds.get("sso_password")
                self.logger.info(self.get_current_credentials_info())
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
            self.save_user_credentials(vm_username, vm_password, sso_username, sso_password)
        
        self.logger.info("登录流程完成")
        return sso_response

    def logout(self):
        """User logout"""
        self.logger.info("开始执行登出操作")
        url = EndpointManager.get_endpoint("auth_logout")
        response = self.post(url)
        
        if response:
            self.logger.info("登出成功")
            # 只删除用户个人凭据，保留项目凭据
            if self.user_config_path.exists():
                self.user_config_path.unlink()
                if self.user_key_path.exists():
                    self.user_key_path.unlink()
                self.logger.debug("已删除个人凭据")
        else:
            self.logger.error("登出失败")
            
        return response
