"""
Description: This module provides a logger manager for handling logging configurations
             and ensuring a single logger instance.

Changelog:
- 2025-03-07: Initial Creation.
- 2025-03-10: Updated to use script names as log environments.
- 2025-03-10: Added password masking in log messages.
- 2025-03-11: Added session directory support for SSE logging.
"""

import logging
import sys
import os
import re
from config.config import CONFIG
from datetime import datetime


class LoggerManager:
    _instance = None  # Singleton pattern to ensure only one LoggerManager instance globally
    _logger = None  # Shared logger object
    _log_env = None  # Log environment (script name)
    _log_level = None  # Specified log level
    _session_dir = None  # Current session directory

    # 定义需要记录文件日志的脚本
    FILE_LOG_SCRIPTS = {
        'bd2_client_sim',
        'bd2_func_test',
        'bd2_load_test'
    }

    # 需要隐藏密码的字段
    PASSWORD_FIELDS = {
        'password',
        'pwd',
        'sso_password',
        'vm_password'
    }

    @classmethod
    def get_current_script_env(cls):
        """
        获取当前运行脚本的日志环境
        - 如果脚本在 FILE_LOG_SCRIPTS 中，返回脚本名
        - 否则返回 None，表示不记录文件日志
        """
        current_script = os.path.basename(sys.argv[0]).replace('.py', '')
        return current_script if current_script in cls.FILE_LOG_SCRIPTS else None

    @classmethod
    def get_session_dir(cls):
        """获取当前会话目录
        
        Returns:
            str: 当前会话目录的路径，如果未创建则返回None
        """
        return cls._session_dir

    @classmethod
    def create_session_dir(cls, script_name=None):
        """创建新的会话目录
        
        Args:
            script_name: 脚本名称，如果为None则自动获取
            
        Returns:
            str: 会话目录的路径
        """
        if script_name is None:
            script_name = cls.get_current_script_env()
            
        # 获取当前时间
        now = datetime.now()
        
        # 构建日志目录路径
        base_log_dir = CONFIG.get("log.base_log_dir", "logs")
        script_dir = script_name  # 脚本名称作为一级目录
        date_dir = now.strftime("%Y-%m-%d")  # 日期作为二级目录
        session_dir = now.strftime("%H%M%S_%f")[:-3]  # 时间作为三级目录（精确到毫秒）
        
        # 完整的日志目录路径
        log_dir = os.path.join(base_log_dir, script_dir, date_dir, session_dir)
        
        # 创建目录
        os.makedirs(log_dir, exist_ok=True)
        
        # 保存会话目录
        cls._session_dir = log_dir
        
        # 打印会话目录的绝对路径
        abs_path = os.path.abspath(log_dir)
        print(f"\n日志目录: {abs_path}\n")
        
        return log_dir

    def __new__(cls, env=None):
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

    @classmethod
    def mask_passwords(cls, message):
        """
        隐藏消息中的密码
        """
        if not isinstance(message, str):
            return message

        # 处理 JSON 格式的消息
        try:
            import json
            data = json.loads(message)
            if isinstance(data, dict):
                for key in cls.PASSWORD_FIELDS:
                    if key in data:
                        data[key] = "*******"
                return json.dumps(data)
        except:
            pass

        # 处理普通文本消息
        # 1. 处理 key=value 格式
        for field in cls.PASSWORD_FIELDS:
            message = re.sub(
                fr'{field}=["\']?[^"\'\s]+["\']?',
                f'{field}=*******',
                message,
                flags=re.IGNORECASE
            )
            # 2. 处理 "key": "value" 格式
            message = re.sub(
                fr'"{field}":\s*["\']?[^"\'\s]+["\']?',
                f'"{field}": "*******"',
                message,
                flags=re.IGNORECASE
            )

        return message

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

        # 使用统一的日志格式：[时间] [线程名] [模块名] 日志级别 - 日志信息
        log_format = "[%(asctime)s.%(msecs)03d][%(threadName)s][%(name)s]%(levelname)s - %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        
        class SecureFormatter(logging.Formatter):
            def format(self, record):
                # 移除文件名中的.py后缀
                record.filename = record.filename.replace('.py', '')
                # 如果是主线程，显示为main
                if record.threadName == "MainThread":
                    record.threadName = "main"
                # # 隐藏密码
                # if hasattr(record, 'msg'):
                #     record.msg = LoggerManager.mask_passwords(record.msg)
                return super().format(record)
        
        formatter = SecureFormatter(log_format, date_format)

        # Console log
        if CONFIG.get("log.log_to_console", True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_level))
            console_handler.setFormatter(formatter)
            LoggerManager._logger.addHandler(console_handler)

        # File log - 只在指定脚本时创建
        if (CONFIG.get("log.log_to_file", True) and 
            self._log_env and 
            self._log_env in self.FILE_LOG_SCRIPTS):
            
            # 创建会话目录（如果还没有创建）
            if not LoggerManager._session_dir:
                LoggerManager._session_dir = self.create_session_dir(self._log_env)
            
            # 生成日志文件名
            log_file = os.path.join(LoggerManager._session_dir, "script.log")
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(getattr(logging, log_level))
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
    def get_logger(cls, file_path, env=None):
        """
        Get Logger and use `filename` as log prefix
        - file_path: Pass `__file__` to automatically extract filename
        - env: Running environment (script name). If None, use current script's environment.
        """
        if env is None:
            env = cls.get_current_script_env()
        instance = cls(env)  # Ensure LoggerManager is initialized according to environment
        filename = os.path.basename(file_path).replace(".py", "")  # Extract filename (remove .py)
        logger = logging.getLogger(filename)
        
        # 确保子logger继承UnifiedLogger的设置
        logger.handlers = []  # 清除现有handlers
        logger.parent = LoggerManager._logger
        logger.propagate = True
        
        return logger

    @classmethod
    def get_console_logger(cls, file_path):
        """
        获取只输出到控制台的日志记录器
        - file_path: Pass `__file__` to automatically extract filename
        """
        return cls.get_logger(file_path, env=None)
