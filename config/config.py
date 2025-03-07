import os
import yaml
from datetime import datetime
from threading import Lock

class ConfigLoader:
    """Singleton Configuration Loader for BD2 Client Simulator"""

    _instance = None
    _lock = Lock()  # 线程安全锁

    def __new__(cls):
        """Ensure singleton instance"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                base_path = os.path.dirname(os.path.abspath(__file__))
                config_file = os.path.join(base_path, "config.yaml")
                cls._instance._init_config(config_file)
        return cls._instance

    def _init_config(self, config_file):
        """Initialize configuration"""
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self):
        """Load YAML configuration file."""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")

        with open(self.config_file, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)

    def __getattr__(self, key):
        """
        Enable direct attribute access, e.g., CONFIG.log_level
        If the attribute does not exist, fallback to get_value() method.
        """
        return self.get(key)

    def get(self, key, default=None):
        """
        Get a value from config.yaml.

        :param key: The key to retrieve (e.g., "log.level")
        :param default: Default value if key is not found
        :return: The value from config.yaml or default
        """
        keys = key.split(".")  # 处理嵌套 key，如 log.level
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default  # key 不存在，返回默认值
        return value


# 重新创建全局 CONFIG 实例
CONFIG = ConfigLoader()
