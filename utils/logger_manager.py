"""
Description: This module provides a logger manager for handling logging configurations
             and ensuring a single logger instance.

Changelog:
- 2025-03-07: Initial Creation.
"""

import logging
import sys
import os
from config.config import CONFIG
from datetime import datetime


class LoggerManager:
    _instance = None  # Singleton pattern to ensure only one LoggerManager instance globally
    _logger = None  # Shared logger object
    _log_env = None  # Log environment (WebClient / pytest)
    _log_level = None  # Specified log level

    def __new__(cls, env="webclient"):
        """
        Singleton pattern: Ensure only one instance of LoggerManager and decide log storage
        location based on environment
        """
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance._log_env = env
            cls._instance._initialize_logger()
        return cls._instance

    @classmethod
    def determine_log_level(cls):
        """
        确定日志级别的优先级策略：
        1. 如果指定了 log_level，使用指定的级别
        2. 使用配置文件中的级别
        3. 如果以上都没有，默认使用 INFO 级别
        """
        if cls._log_level:
            return cls._log_level
        return CONFIG.get("log.level", "INFO")

    def _initialize_logger(self):
        """Initialize Logger"""
        if LoggerManager._logger is None:
            LoggerManager._logger = logging.getLogger("UnifiedLogger")
        
        # 移除所有现有的handlers
        if LoggerManager._logger.handlers:
            LoggerManager._logger.handlers.clear()
            
        # 根据优先级策略设置日志级别
        log_level = self.determine_log_level()
        LoggerManager._logger.setLevel(getattr(logging, log_level))

        # 使用基本的日志格式，精确到毫秒，文件名不带后缀
        log_format = "[%(asctime)s.%(msecs)03d] [%(filename)s] %(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        
        class NoExtFormatter(logging.Formatter):
            def format(self, record):
                # 移除文件名中的.py后缀
                record.filename = record.filename.replace('.py', '')
                return super().format(record)
        
        formatter = NoExtFormatter(log_format, date_format)

        # Console log
        if CONFIG.get("log.log_to_console", True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_level))
            console_handler.setFormatter(formatter)
            LoggerManager._logger.addHandler(console_handler)

        # File log
        if CONFIG.get("log.log_to_file", True):
            # 获取当前时间
            now = datetime.now()
            
            # 构建日志目录路径
            base_log_dir = CONFIG.get("log.base_log_dir", "logs")
            env_dir = os.path.basename(sys.argv[0]).replace('.py', '')  # 使用脚本名作为环境名
            date_dir = now.strftime("%Y-%m-%d")  # 日期目录
            log_dir = os.path.join(base_log_dir, env_dir, date_dir)
            
            # 创建日志目录
            os.makedirs(log_dir, exist_ok=True)
            
            # 生成日志文件名（精确到毫秒）
            log_file = os.path.join(
                log_dir,
                now.strftime("%Y%m%d_%H%M%S_%f")[:-3] + ".log"  # 去掉最后3位毫秒，保留精确到毫秒
            )
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)  # 文件日志始终使用 DEBUG 级别
            file_handler.setFormatter(formatter)
            LoggerManager._logger.addHandler(file_handler)

        # 禁用日志传播到父logger
        LoggerManager._logger.propagate = False

    @classmethod
    def set_log_level(cls, log_level):
        """设置指定的日志级别"""
        cls._log_level = log_level
        # 如果logger已经初始化，重新初始化以应用新的日志级别
        if cls._instance and cls._logger:
            cls._instance._initialize_logger()

    @classmethod
    def get_logger(cls, file_path, env="webclient"):
        """
        Get Logger and use `filename` as log prefix
        - file_path: Pass `__file__` to automatically extract filename
        - env: Running environment ("webclient" or "pytest")
        """
        instance = cls(env)  # Ensure LoggerManager is initialized according to environment
        filename = os.path.basename(file_path).replace(".py", "")  # Extract filename (remove .py)
        logger = logging.getLogger(filename)
        
        # 确保子logger继承UnifiedLogger的设置
        logger.handlers = []  # 清除现有handlers
        logger.parent = LoggerManager._logger
        logger.propagate = True
        
        return logger
