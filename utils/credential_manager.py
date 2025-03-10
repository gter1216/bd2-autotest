"""
Description: This module handles credential management.

Changelog:
- 2025-03-07: Initial creation.
- 2025-03-10: Updated to use default log environment.
"""

from pathlib import Path
import json
from cryptography.fernet import Fernet
import os
import socket
from utils.logger_manager import LoggerManager

class CredentialManager:
    """Handles credential management and storage"""

    # 项目级配置文件（所有用户共享）
    PROJECT_CONFIG_FILE = "auth.enc"
    PROJECT_KEY_FILE = "auth.key"
    
    # 用户级配置文件（按主机名区分）
    USER_CONFIG_FILE = "auth.enc"
    USER_KEY_FILE = "auth.key"

    def __init__(self):
        self.logger = LoggerManager.get_logger(__file__)  # 使用默认环境
        self._init_crypto()

    def _init_crypto(self):
        """初始化加密相关的设置"""
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
        保存位置：var/credentials/auth.enc
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
        保存位置：var/credentials/hosts/<hostname>/auth.enc
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

    def remove_project_credentials(self):
        """删除项目级凭据"""
        try:
            if self.project_config_path.exists():
                self.project_config_path.unlink()
            if self.project_key_path.exists():
                self.project_key_path.unlink()
            self.logger.info("项目凭据已删除")
        except Exception as e:
            self.logger.error(f"删除项目凭据失败: {str(e)}")
            raise

    def remove_user_credentials(self):
        """删除用户个人凭据"""
        try:
            if self.user_config_path.exists():
                self.user_config_path.unlink()
            if self.user_key_path.exists():
                self.user_key_path.unlink()
            self.logger.info("个人凭据已删除")
        except Exception as e:
            self.logger.error(f"删除个人凭据失败: {str(e)}")
            raise

    def get_current_credentials(self):
        """
        按优先级加载凭据：
        1. 用户个人加密凭据
        2. 项目级加密凭据
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
            from config.config import CONFIG
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
        creds = self.get_current_credentials()
        if not creds:
            return "未找到任何可用的凭据"
        
        cred_type = creds.get("type", "unknown")
        if cred_type == "personal":
            return f"使用个人凭据 (主机: {self.hostname}, 用户: {creds['vm_username']}, 位置: {self.user_config_path})"
        elif cred_type == "project":
            return f"使用项目凭据 (用户: {creds['vm_username']}, 位置: {self.project_config_path})"
        else:
            return f"使用明文配置 (用户: {creds['vm_username']}, 位置: config.yaml)" 